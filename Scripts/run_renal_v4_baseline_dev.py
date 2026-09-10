"""
MedicalPlab Renal V4 — Phase 5: Frozen V3 Baseline on Fresh RETRIEVAL_DEV_V4
============================================================================
Evaluates the frozen V3 retrieval architecture on the fresh, unspent RETRIEVAL_DEV_V4 dataset:
- Embedding: Qwen/Qwen3-Embedding-0.6B (revision: 97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3)
- Chunking: B_400_overlap
- Representation: content_only
- Soft document prior: alpha = 0.18
- Reranker: Qwen/Qwen3-Reranker-0.6B on Top-20 candidates
- Exact vector search (dot product)

Tracks both CandidateCoverage@50 (superset) and RerankerInputHit@20 (actual reranker input).
Persists detailed per-query rankings and failure classifications for Phase 6 failure taxonomy.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import sys
import time
from pathlib import Path
import numpy as np
import torch

# UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from sentence_transformers import CrossEncoder
from transformers import AutoModel, AutoTokenizer

ROOT = _ROOT
DEV_PATH = ROOT / "evaluation" / "renal" / "v4" / "renal-retrieval-dev-v4.json"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
REPORTS_DIR = ROOT / "reports" / "renal_v4"
OUTPUT_REPORT_PATH = REPORTS_DIR / "renal_v4_dev_baseline_v3.json"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode_texts(texts: list[str], tokenizer, model, device: torch.device, batch_size: int = 16) -> np.ndarray:
    all_embeddings = []
    with torch.inference_mode():
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            encoded = tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
            outputs = model(**encoded)
            mask = encoded["attention_mask"].unsqueeze(-1)
            emb = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            emb = torch.nn.functional.normalize(emb, p=2, dim=1)
            all_embeddings.append(emb.cpu().numpy())
    return np.vstack(all_embeddings).astype(np.float32)


def compute_dcg_at_k(relevance: list[int], k: int = 10) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevance[:k]):
        if rel > 0:
            dcg += (2**rel - 1) / math.log2(i + 2)
    return dcg


def compute_ndcg_at_k(relevance: list[int], k: int = 10) -> float:
    actual_dcg = compute_dcg_at_k(relevance, k)
    ideal_relevance = sorted(relevance, reverse=True)
    ideal_dcg = compute_dcg_at_k(ideal_relevance, k)
    if ideal_dcg == 0.0:
        return 0.0
    return actual_dcg / ideal_dcg


def is_chunk_relevant(ch: dict, q: dict) -> bool:
    cid = ch.get("chunk_id")
    if cid in q.get("gold_child_chunk_ids", []):
        return True
    return False


def is_section_relevant(ch: dict, q: dict) -> bool:
    pid = ch.get("parent_section_id")
    if pid and pid in q.get("gold_parent_section_ids", []):
        return True
    return False


def is_doc_relevant(ch: dict, q: dict) -> bool:
    did = ch.get("document_id")
    if did and did in q.get("gold_document_ids", []):
        return True
    return False


def main():
    print("=" * 75)
    print("PHASE 5: FROZEN V3 RETRIEVAL BASELINE ON FRESH RETRIEVAL_DEV_V4")
    print("=" * 75)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Device check
    assert torch.cuda.is_available(), "FATAL: CUDA GPU required!"
    device = torch.device("cuda:0")
    print(f"Device: {torch.cuda.get_device_name(device)}")
    print(f"PyTorch Version: {torch.__version__}, CUDA: {torch.version.cuda}")

    # 2. Verify dataset
    assert DEV_PATH.exists(), f"Dev dataset missing: {DEV_PATH}"
    dev_sha = sha256_file(DEV_PATH)
    sidecar_sha = DEV_PATH.with_suffix(".json.sha256").read_text(encoding="utf-8").split()[0]
    assert dev_sha == sidecar_sha, f"Dataset SHA mismatch! {dev_sha} != {sidecar_sha}"
    print(f"Verified RETRIEVAL_DEV_V4 SHA256: {dev_sha}")

    dev_data = json.loads(DEV_PATH.read_text(encoding="utf-8"))
    queries = dev_data["queries"]
    ans_queries = [q for q in queries if q["answerable"]]
    n_ans = len(ans_queries)
    print(f"Loaded {len(queries)} queries ({n_ans} answerable evaluation queries)")

    # 3. Load Registry and Chunks
    reg_data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    chunks: list[dict] = []
    chunk_id_to_idx: dict[str, int] = {}
    doc_to_chunks: dict[str, list[int]] = {}

    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_text(encoding="utf-8"))
        for ch in payload.get("chunks", []):
            idx = len(chunks)
            chunks.append(ch)
            cid = ch.get("chunk_id")
            if cid:
                chunk_id_to_idx[cid] = idx
            did = ch.get("document_id")
            if did:
                doc_to_chunks.setdefault(did, []).append(idx)

    print(f"Loaded {len(chunks)} chunks across {len(doc_to_chunks)} documents.")

    # 4. Load models and representations
    embed_tok = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
    embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device)
    embed_model.eval()

    doc_ids_sorted = sorted(list(doc_to_chunks.keys()))
    doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}

    doc_cache_path = CACHE_DIR / "all23_doc_embeddings.npy"
    assert doc_cache_path.exists(), f"Doc cache missing: {doc_cache_path}"
    doc_emb = np.load(doc_cache_path)

    corpus_cache_path = CACHE_DIR / "all23_corpus_embeddings.npy"
    assert corpus_cache_path.exists(), f"Corpus cache missing: {corpus_cache_path}"
    corpus_arr = np.load(corpus_cache_path)

    print(f"Corpus shape: {corpus_arr.shape}, Doc prior shape: {doc_emb.shape}")

    # Load CrossEncoder Reranker
    reranker = CrossEncoder(RERANK_MODEL_ID, trust_remote_code=True, device="cuda:0")

    # 5. Query Encoding
    q_texts = [q["query"] for q in ans_queries]
    q_instruct = [QUERY_INSTRUCTION + q for q in q_texts]

    # Warmup
    _ = encode_texts(q_instruct[:2], embed_tok, embed_model, device)

    t0_enc = time.perf_counter()
    q_embs = encode_texts(q_instruct, embed_tok, embed_model, device)
    t1_enc = time.perf_counter()
    per_query_enc_ms = ((t1_enc - t0_enc) / n_ans) * 1000.0
    print(f"Encoded {n_ans} queries in {(t1_enc - t0_enc):.2f}s ({per_query_enc_ms:.2f} ms/query)")

    # 6. Evaluation Loop
    alpha = 0.18
    p_sims = np.dot(q_embs, corpus_arr.T)
    d_sims = np.dot(q_embs, doc_emb.T)

    doc_hit_1, doc_hit_3, doc_hit_5, doc_hit_10 = 0, 0, 0, 0
    sec_hit_1, sec_hit_3, sec_hit_5, sec_hit_10 = 0, 0, 0, 0
    pass_hit_1, pass_hit_3, pass_hit_5, pass_hit_10 = 0, 0, 0, 0

    cand_cov_20, cand_cov_50, cand_cov_100 = 0, 0, 0
    reranker_input_hit_20 = 0

    mrr_sum = 0.0
    ndcg_sum = 0.0

    latencies_s1 = []
    latencies_s2 = []
    latencies_total = []

    per_query_results = []

    for q_idx, q in enumerate(ans_queries):
        qid = q["query_id"]
        q_text = q["query"]

        # Stage 1: Dense + Doc Prior
        t0_s1 = time.perf_counter()
        p_scores = p_sims[q_idx]
        d_scores = d_sims[q_idx]

        combined = np.zeros_like(p_scores)
        for i, ch in enumerate(chunks):
            did = ch["document_id"]
            combined[i] = p_scores[i] + alpha * d_scores[doc_id_to_idx[did]]

        stage1_sorted_idx = np.argsort(combined)[::-1]
        top20_idx = stage1_sorted_idx[:20]
        cands_top20 = [chunks[i] for i in top20_idx]
        t1_s1 = time.perf_counter()
        s1_ms = (t1_s1 - t0_s1) * 1000.0

        # Candidate coverage in stage 1
        c_cov_20 = any(is_chunk_relevant(chunks[i], q) for i in stage1_sorted_idx[:20])
        c_cov_50 = any(is_chunk_relevant(chunks[i], q) for i in stage1_sorted_idx[:50])
        c_cov_100 = any(is_chunk_relevant(chunks[i], q) for i in stage1_sorted_idx[:100])

        cand_cov_20 += int(c_cov_20)
        cand_cov_50 += int(c_cov_50)
        cand_cov_100 += int(c_cov_100)

        # In baseline frozen V3, reranker input is exactly stage1_sorted_idx[:20]
        r_input_hit = c_cov_20
        reranker_input_hit_20 += int(r_input_hit)

        # Stage 2: CrossEncoder Reranker on Top-20
        t0_s2 = time.perf_counter()
        pairs = [[q_text, c.get("text", "")] for c in cands_top20]
        with torch.inference_mode():
            raw_r = reranker.predict(pairs, batch_size=8, show_progress_bar=False)
        r_scores = np.asarray(raw_r, dtype=np.float32).reshape(-1)
        r_order = np.argsort(r_scores)[::-1]
        t1_s2 = time.perf_counter()
        s2_ms = (t1_s2 - t0_s2) * 1000.0

        tot_ms = per_query_enc_ms + s1_ms + s2_ms
        latencies_s1.append(s1_ms)
        latencies_s2.append(s2_ms)
        latencies_total.append(tot_ms)

        # Full ranked list: reranked top 20, then remaining stage 1 (ranks 21..100)
        reranked_top20 = [cands_top20[int(i)] for i in r_order]
        remaining = [chunks[i] for i in stage1_sorted_idx[20:100]]
        full_ranked = reranked_top20 + remaining

        # Hits
        d_h1 = any(is_doc_relevant(ch, q) for ch in full_ranked[:1])
        d_h3 = any(is_doc_relevant(ch, q) for ch in full_ranked[:3])
        d_h5 = any(is_doc_relevant(ch, q) for ch in full_ranked[:5])
        d_h10 = any(is_doc_relevant(ch, q) for ch in full_ranked[:10])

        s_h1 = any(is_section_relevant(ch, q) for ch in full_ranked[:1])
        s_h3 = any(is_section_relevant(ch, q) for ch in full_ranked[:3])
        s_h5 = any(is_section_relevant(ch, q) for ch in full_ranked[:5])
        s_h10 = any(is_section_relevant(ch, q) for ch in full_ranked[:10])

        p_h1 = any(is_chunk_relevant(ch, q) for ch in full_ranked[:1])
        p_h3 = any(is_chunk_relevant(ch, q) for ch in full_ranked[:3])
        p_h5 = any(is_chunk_relevant(ch, q) for ch in full_ranked[:5])
        p_h10 = any(is_chunk_relevant(ch, q) for ch in full_ranked[:10])

        doc_hit_1 += int(d_h1)
        doc_hit_3 += int(d_h3)
        doc_hit_5 += int(d_h5)
        doc_hit_10 += int(d_h10)

        sec_hit_1 += int(s_h1)
        sec_hit_3 += int(s_h3)
        sec_hit_5 += int(s_h5)
        sec_hit_10 += int(s_h10)

        pass_hit_1 += int(p_h1)
        pass_hit_3 += int(p_h3)
        pass_hit_5 += int(p_h5)
        pass_hit_10 += int(p_h10)

        # RR & NDCG
        rr = 0.0
        rel_10 = []
        for r_idx, ch in enumerate(full_ranked[:10]):
            is_rel = int(is_chunk_relevant(ch, q))
            rel_10.append(is_rel)
            if is_rel and rr == 0.0:
                rr = 1.0 / (r_idx + 1)

        if rr == 0.0:
            for r_idx, ch in enumerate(full_ranked):
                if is_chunk_relevant(ch, q):
                    rr = 1.0 / (r_idx + 1)
                    break

        ndcg = compute_ndcg_at_k(rel_10, 10)
        mrr_sum += rr
        ndcg_sum += ndcg

        # Failure Taxonomy Categorization
        # Taxonomy categories:
        # DOCUMENT_ROUTING_FAILURE: Top-1 doc is wrong and gold doc not in top 3
        # RIGHT_DOCUMENT_WRONG_SECTION: Top-1 doc is correct, but section is wrong
        # RIGHT_SECTION_WRONG_PASSAGE: Top-1 section is correct, but passage is wrong
        # CANDIDATE_SUPERSET_MISS: Gold chunk not in stage1 top-50
        # RERANKER_INPUT_SELECTION_MISS: Gold chunk in top-50 superset but NOT in top-20 reranker input
        # RERANKING_FAILURE: Gold chunk WAS in top-20 reranker input, but reranker failed to place it at rank 1
        # FULL_SUCCESS: PassageHit@1 == True
        fail_cat = "FULL_SUCCESS"
        if not p_h1:
            if not d_h1:
                fail_cat = "DOCUMENT_ROUTING_FAILURE"
            elif not s_h1:
                fail_cat = "RIGHT_DOCUMENT_WRONG_SECTION"
            else:
                # doc and section were hit at rank 1, but chunk wasn't
                fail_cat = "RIGHT_SECTION_WRONG_PASSAGE"

            # Check if it was a selection or reranking issue
            if not c_cov_50:
                fail_cat = f"{fail_cat}+CANDIDATE_SUPERSET_MISS"
            elif not r_input_hit:
                fail_cat = f"{fail_cat}+RERANKER_INPUT_SELECTION_MISS"
            else:
                fail_cat = f"{fail_cat}+RERANKING_FAILURE"

        per_query_results.append({
            "query_id": qid,
            "query": q_text,
            "topic": q["topic"],
            "pass_hit_1": p_h1,
            "pass_hit_5": p_h5,
            "doc_hit_1": d_h1,
            "sec_hit_1": s_h1,
            "cand_cov_20": c_cov_20,
            "cand_cov_50": c_cov_50,
            "cand_cov_100": c_cov_100,
            "reranker_input_hit_20": r_input_hit,
            "reciprocal_rank": rr,
            "ndcg_10": ndcg,
            "failure_category": fail_cat,
            "top1_chunk_id": full_ranked[0]["chunk_id"],
            "top1_doc_id": full_ranked[0]["document_id"],
            "gold_chunk_ids": q["gold_child_chunk_ids"],
            "gold_doc_ids": q["gold_document_ids"],
        })

    metrics = {
        "dataset_name": "RETRIEVAL_DEV_V4",
        "dataset_sha256": dev_sha,
        "n_answerable": n_ans,
        "DocumentHit@1": f"{doc_hit_1}/{n_ans} ({doc_hit_1 / n_ans:.4f})",
        "DocumentHit@3": f"{doc_hit_3}/{n_ans} ({doc_hit_3 / n_ans:.4f})",
        "DocumentHit@5": f"{doc_hit_5}/{n_ans} ({doc_hit_5 / n_ans:.4f})",
        "DocumentHit@10": f"{doc_hit_10}/{n_ans} ({doc_hit_10 / n_ans:.4f})",
        "ParentSectionHit@1": f"{sec_hit_1}/{n_ans} ({sec_hit_1 / n_ans:.4f})",
        "ParentSectionHit@3": f"{sec_hit_3}/{n_ans} ({sec_hit_3 / n_ans:.4f})",
        "ParentSectionHit@5": f"{sec_hit_5}/{n_ans} ({sec_hit_5 / n_ans:.4f})",
        "ParentSectionHit@10": f"{sec_hit_10}/{n_ans} ({sec_hit_10 / n_ans:.4f})",
        "PassageHit@1": f"{pass_hit_1}/{n_ans} ({pass_hit_1 / n_ans:.4f})",
        "PassageHit@3": f"{pass_hit_3}/{n_ans} ({pass_hit_3 / n_ans:.4f})",
        "PassageHit@5": f"{pass_hit_5}/{n_ans} ({pass_hit_5 / n_ans:.4f})",
        "PassageHit@10": f"{pass_hit_10}/{n_ans} ({pass_hit_10 / n_ans:.4f})",
        "CandidateCoverage@20": f"{cand_cov_20}/{n_ans} ({cand_cov_20 / n_ans:.4f})",
        "CandidateCoverage@50": f"{cand_cov_50}/{n_ans} ({cand_cov_50 / n_ans:.4f})",
        "CandidateCoverage@100": f"{cand_cov_100}/{n_ans} ({cand_cov_100 / n_ans:.4f})",
        "RerankerInputHit@20": f"{reranker_input_hit_20}/{n_ans} ({reranker_input_hit_20 / n_ans:.4f})",
        "MRR": f"{mrr_sum / n_ans:.4f}",
        "nDCG@10": f"{ndcg_sum / n_ans:.4f}",
        "latency_ms": {
            "encode_per_query_ms": round(per_query_enc_ms, 2),
            "stage1_p50_ms": round(float(np.percentile(latencies_s1, 50)), 2),
            "stage1_p95_ms": round(float(np.percentile(latencies_s1, 95)), 2),
            "stage2_p50_ms": round(float(np.percentile(latencies_s2, 50)), 2),
            "stage2_p95_ms": round(float(np.percentile(latencies_s2, 95)), 2),
            "total_p50_ms": round(float(np.percentile(latencies_total, 50)), 2),
            "total_p95_ms": round(float(np.percentile(latencies_total, 95)), 2),
        }
    }

    print("\n" + "=" * 75)
    print("FRESH RETRIEVAL_DEV_V4 BASELINE METRICS (FROZEN V3 PIPELINE)")
    print("=" * 75)
    for k, v in metrics.items():
        if k != "latency_ms":
            print(f"  {k:25s}: {v}")
    print("\nLatency Profiling (ms):")
    for k, v in metrics["latency_ms"].items():
        print(f"  {k:25s}: {v} ms")

    # Failure Taxonomy Summary
    fail_counts = {}
    for r in per_query_results:
        cat = r["failure_category"]
        fail_counts[cat] = fail_counts.get(cat, 0) + 1

    print("\n" + "=" * 75)
    print("PHASE 6: FRESH FAILURE TAXONOMY BREAKDOWN ON V4 DEV")
    print("=" * 75)
    for cat, cnt in sorted(fail_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat:55s}: {cnt}/{n_ans} ({cnt/n_ans*100:.1f}%)")

    payload = {
        "mission": "MEDICALPLAB RENAL V4",
        "stage": "Phase 5 & 6 Frozen V3 Baseline on Fresh V4 DEV",
        "dataset_sha256": dev_sha,
        "metrics": metrics,
        "failure_taxonomy": fail_counts,
        "queries": per_query_results
    }

    OUTPUT_REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    rep_sha = sha256_file(OUTPUT_REPORT_PATH)
    OUTPUT_REPORT_PATH.with_suffix(".json.sha256").write_text(f"{rep_sha}  {OUTPUT_REPORT_PATH.name}\n", encoding="utf-8")
    print(f"\nPersisted baseline report: {OUTPUT_REPORT_PATH}")
    print(f"Report SHA256: {rep_sha}")


if __name__ == "__main__":
    main()
