"""
MedicalPlab Renal V5 — Cheap First-Stage Gold-Rank Diagnostic
=============================================================
Computes exact first-stage retrieval ranks across the entire 2,691-chunk corpus
and all 23 documents for all 50 DEV-A queries.
Zero cross-encoding required (pure dense dot product + document prior).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import numpy as np
import torch

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from transformers import AutoModel, AutoTokenizer

ROOT = _ROOT
DEV_A_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
REPORTS_DIR = ROOT / "reports" / "renal_v5"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = (
    "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
)
ALPHA_DOC_PRIOR = 0.18


def main():
    print("=" * 70)
    print("MEDICALPLAB RENAL V5 — FIRST-STAGE GOLD-RANK DIAGNOSTIC")
    print("=" * 70)

    # 1. Device check
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # 2. Load DEV-A dataset
    dev_a = json.loads(DEV_A_PATH.read_text(encoding="utf-8"))
    n_queries = len(dev_a)
    print(f"Loaded {n_queries} DEV-A queries.")

    # 3. Load chunks and documents
    chunks = []
    chunk_id_to_idx = {}
    doc_to_chunks = {}
    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_bytes())
        for ch in payload.get("chunks", []):
            idx = len(chunks)
            chunks.append(ch)
            cid = ch["chunk_id"]
            did = ch["document_id"]
            chunk_id_to_idx[cid] = idx
            doc_to_chunks.setdefault(did, []).append(idx)

    n_chunks = len(chunks)
    doc_ids_sorted = sorted(list(doc_to_chunks.keys()))
    doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
    chunk_doc_indices = np.array([doc_id_to_idx[ch["document_id"]] for ch in chunks], dtype=np.int32)
    print(f"Loaded {n_chunks} chunks across {len(doc_ids_sorted)} documents.")

    # 4. Load cached embeddings
    corpus_emb_path = CACHE_DIR / "all23_corpus_embeddings.npy"
    doc_emb_path = CACHE_DIR / "all23_doc_embeddings.npy"
    corpus_embeddings = np.load(corpus_emb_path).astype(np.float32)  # (2691, 1024)
    doc_embeddings = np.load(doc_emb_path).astype(np.float32)        # (23, 1024)
    print(f"Corpus embeddings: {corpus_embeddings.shape}, Doc embeddings: {doc_embeddings.shape}")

    # 5. Encode queries
    print("Encoding DEV-A queries with Qwen3-Embedding-0.6B...")
    tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
    embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device).eval()

    query_texts = [QUERY_INSTRUCTION + item["query"] for item in dev_a]
    with torch.inference_mode():
        encoded = tokenizer(query_texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        outputs = embed_model(**encoded)
        mask = encoded["attention_mask"].unsqueeze(-1)
        q_emb = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        q_emb = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)
    print(f"Query embeddings encoded: {q_emb.shape}")

    # 6. Compute exact first-stage scores across full corpus and all docs
    # p_sims: (50, 2691), d_sims: (50, 23)
    p_sims = q_emb @ corpus_embeddings.T
    d_sims = q_emb @ doc_embeddings.T

    # Combine passage score with alpha * doc_prior
    # For each query, combined score is p_sims[q, :] + ALPHA_DOC_PRIOR * d_sims[q, chunk_doc_indices]
    comb_sims = p_sims + ALPHA_DOC_PRIOR * d_sims[:, chunk_doc_indices]
    print("Exact first-stage scores computed.")

    # 7. Evaluate per-query metrics
    cov_counts = {20: 0, 30: 0, 50: 0, 100: 0, 200: 0, 500: 0}
    per_query_results = []
    
    # Classification buckets
    buckets = {
        "TOP1_FIRST_STAGE": 0,
        "TOP20_PRESENT": 0,
        "SELECTION_CROWDING_21_100": 0,
        "SCORING_REPRESENTATION_101_500": 0,
        "PASSAGE_LOCALIZATION_FAILURE": 0,
        "DOCUMENT_ROUTING_FAILURE": 0,
        "SEVERE_MISS_GT500": 0,
    }

    best_ranks_list = []
    doc_ranks_list = []

    for i, item in enumerate(dev_a):
        qid = item["query_id"]
        gold_cids = item["gold_chunk_ids"]
        gold_did = item["gold_doc_id"]
        gold_c_indices = [chunk_id_to_idx[cid] for cid in gold_cids if cid in chunk_id_to_idx]
        gold_d_idx = doc_id_to_idx.get(gold_did)

        # Full-corpus passage ranking
        q_comb = comb_sims[i]
        ranked_chunk_indices = np.argsort(q_comb)[::-1]
        
        # Rank of best gold chunk (1-indexed)
        # Find where the gold chunks appear in ranked_chunk_indices
        chunk_rank_map = {c_idx: r + 1 for r, c_idx in enumerate(ranked_chunk_indices)}
        gold_chunk_ranks = [chunk_rank_map[c_idx] for c_idx in gold_c_indices]
        best_passage_rank = min(gold_chunk_ranks) if gold_chunk_ranks else None
        best_ranks_list.append(best_passage_rank)

        # Document ranking
        q_doc_scores = d_sims[i]
        ranked_doc_indices = np.argsort(q_doc_scores)[::-1]
        doc_rank_map = {d_idx: r + 1 for r, d_idx in enumerate(ranked_doc_indices)}
        gold_doc_rank = doc_rank_map.get(gold_d_idx)
        doc_ranks_list.append(gold_doc_rank)

        # Candidate coverage
        for k in [20, 30, 50, 100, 200, 500]:
            if best_passage_rank is not None and best_passage_rank <= k:
                cov_counts[k] += 1

        # Failure diagnosis classification
        # Distinguish:
        # 1. evidence ranked 21-100: selection/crowding problem
        # 2. evidence ranked 101-500: first-stage scoring/representation problem
        # 3. evidence extremely low despite correct document: passage localization inside correct document
        # 4. gold document itself ranks poorly: document-routing / semantic retrieval problem
        # 5. evidence mapping is incomplete/incorrect: qrel/evaluation problem
        if best_passage_rank is None:
            diag_cat = "EVAL_MAPPING_EMPTY_GOLD"
        elif best_passage_rank == 1:
            diag_cat = "TOP1_FIRST_STAGE"
        elif best_passage_rank <= 20:
            diag_cat = "TOP20_PRESENT"
        elif 21 <= best_passage_rank <= 100:
            if gold_doc_rank is not None and gold_doc_rank <= 3:
                diag_cat = "SELECTION_CROWDING_21_100"
            else:
                diag_cat = "SELECTION_CROWDING_WEAK_DOC"
        elif 101 <= best_passage_rank <= 500:
            if gold_doc_rank is not None and gold_doc_rank <= 3:
                diag_cat = "PASSAGE_LOCALIZATION_FAILURE"
            else:
                diag_cat = "SCORING_REPRESENTATION_101_500"
        else: # > 500
            if gold_doc_rank is not None and gold_doc_rank <= 3:
                diag_cat = "PASSAGE_LOCALIZATION_FAILURE"
            else:
                diag_cat = "DOCUMENT_ROUTING_FAILURE"

        per_query_results.append({
            "query_id": qid,
            "query": item["query"],
            "curriculum_stratum": item["curriculum_stratum"],
            "query_style": item["query_style"],
            "gold_doc_id": gold_did,
            "gold_chunk_ids": gold_cids,
            "gold_doc_rank": gold_doc_rank,
            "best_passage_first_stage_rank": best_passage_rank,
            "in_top20": (best_passage_rank is not None and best_passage_rank <= 20),
            "in_top30": (best_passage_rank is not None and best_passage_rank <= 30),
            "in_top50": (best_passage_rank is not None and best_passage_rank <= 50),
            "in_top100": (best_passage_rank is not None and best_passage_rank <= 100),
            "in_top200": (best_passage_rank is not None and best_passage_rank <= 200),
            "in_top500": (best_passage_rank is not None and best_passage_rank <= 500),
            "doc_retrieved_strongly": (gold_doc_rank is not None and gold_doc_rank <= 3),
            "diagnosis_category": diag_cat,
        })

    # Summary stats
    print("\n" + "=" * 70)
    print("FIRST-STAGE RETRIEVAL COVERAGE ACROSS DEPTHS (N=50 DEV-A)")
    print("=" * 70)
    for k in [20, 30, 50, 100, 200, 500]:
        c = cov_counts[k]
        pct = c / n_queries * 100
        print(f"CandidateCoverage@{k:3d}: {c:2d} / {n_queries} ({pct:5.1f}%)")

    # Document rank distribution
    doc_hit1 = sum(1 for r in doc_ranks_list if r == 1)
    doc_hit3 = sum(1 for r in doc_ranks_list if r <= 3)
    doc_hit5 = sum(1 for r in doc_ranks_list if r <= 5)
    print(f"\nFirst-Stage Gold Document Retrieval:")
    print(f"  Gold Doc at #1:  {doc_hit1} / {n_queries} ({doc_hit1/n_queries*100:.1f}%)")
    print(f"  Gold Doc in Top 3: {doc_hit3} / {n_queries} ({doc_hit3/n_queries*100:.1f}%)")
    print(f"  Gold Doc in Top 5: {doc_hit5} / {n_queries} ({doc_hit5/n_queries*100:.1f}%)")

    # Diagnosis categories count
    diag_counts = {}
    for r in per_query_results:
        cat = r["diagnosis_category"]
        diag_counts[cat] = diag_counts.get(cat, 0) + 1

    print("\nFailure Diagnosis Distribution:")
    for cat, cnt in sorted(diag_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat:35s}: {cnt:2d} queries ({cnt/n_queries*100:5.1f}%)")

    # Break down the 20 upstream misses (where best rank > 20 or None)
    upstream_misses = [r for r in per_query_results if not r["in_top20"]]
    print(f"\nBreakdown of 20 Upstream Top20 Misses:")
    print(f"  Rank 21–50:   {sum(1 for r in upstream_misses if r['best_passage_first_stage_rank'] is not None and 21 <= r['best_passage_first_stage_rank'] <= 50)} queries")
    print(f"  Rank 51–100:  {sum(1 for r in upstream_misses if r['best_passage_first_stage_rank'] is not None and 51 <= r['best_passage_first_stage_rank'] <= 100)} queries")
    print(f"  Rank 101–200: {sum(1 for r in upstream_misses if r['best_passage_first_stage_rank'] is not None and 101 <= r['best_passage_first_stage_rank'] <= 200)} queries")
    print(f"  Rank 201–500: {sum(1 for r in upstream_misses if r['best_passage_first_stage_rank'] is not None and 201 <= r['best_passage_first_stage_rank'] <= 500)} queries")
    print(f"  Rank > 500:   {sum(1 for r in upstream_misses if r['best_passage_first_stage_rank'] is not None and r['best_passage_first_stage_rank'] > 500)} queries")
    print(f"  Empty Gold:   {sum(1 for r in upstream_misses if r['best_passage_first_stage_rank'] is None)} queries")

    # Check localization vs routing in upstream misses
    loc_failures = [r for r in upstream_misses if r["doc_retrieved_strongly"]]
    routing_failures = [r for r in upstream_misses if not r["doc_retrieved_strongly"]]
    print(f"\nUpstream Miss Mechanism:")
    print(f"  Correct Document Strongly Retrieved (Rank <= 3) but Passage Buried (Passage Localization): {len(loc_failures)} queries ({len(loc_failures)/len(upstream_misses)*100:.1f}%)")
    print(f"  Document Itself Missed/Weak (Rank > 3) (Document Routing / Semantic Miss): {len(routing_failures)} queries ({len(routing_failures)/len(upstream_misses)*100:.1f}%)")

    # Save detailed JSON report
    report = {
        "benchmark": "MEDICALPLAB_RENAL_V5_FIRST_STAGE_GOLD_RANK_DIAGNOSTIC",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_queries": n_queries,
        "candidate_coverage": {
            k: {"numerator": cov_counts[k], "denominator": n_queries, "rate": cov_counts[k] / n_queries}
            for k in [20, 30, 50, 100, 200, 500]
        },
        "document_retrieval": {
            "doc_hit1": {"numerator": doc_hit1, "denominator": n_queries, "rate": doc_hit1 / n_queries},
            "doc_hit3": {"numerator": doc_hit3, "denominator": n_queries, "rate": doc_hit3 / n_queries},
            "doc_hit5": {"numerator": doc_hit5, "denominator": n_queries, "rate": doc_hit5 / n_queries},
        },
        "diagnosis_summary": diag_counts,
        "upstream_miss_breakdown": {
            "total_upstream_misses": len(upstream_misses),
            "passage_localization_failures": len(loc_failures),
            "document_routing_failures": len(routing_failures),
        },
        "detailed_results": per_query_results,
    }

    out_path = REPORTS_DIR / "renal_v5_first_stage_diagnostic.json"
    out_bytes = json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")
    out_path.write_bytes(out_bytes)
    sha = hashlib.sha256(out_bytes).hexdigest()
    (REPORTS_DIR / "renal_v5_first_stage_diagnostic.json.sha256").write_text(f"{sha}  renal_v5_first_stage_diagnostic.json\n", encoding="utf-8")
    print(f"\nSaved report to {out_path.name} (SHA: {sha[:16]}...)")


if __name__ == "__main__":
    main()
