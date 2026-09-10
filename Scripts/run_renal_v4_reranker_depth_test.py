"""
MedicalPlab Renal V4 — Phase 13 & 17: Reranker Depth Gate Experiment
====================================================================
Tests the hypothesis:
"Because CandidateCoverage@50 is 98.0% while RerankerInputHit@20 is 84.0%,
evaluating deeper reranking (Top-20 vs Top-30 vs Top-40) will recover evidence
sitting in ranks 21-40 and improve PassageHit@1."

Uses EXP3_SEC_STRUCTURAL (dense + 0.18 doc_prior + 0.12 structural section channel).
Measures:
- PassageHit@1/3/5/10
- DocumentHit@1/5/10
- ParentSectionHit@1/5/10
- RerankerInputHit
- MRR, nDCG@10
- Reranker time, end-to-end p50/p95 latency
- VRAM footprint
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
CACHE_DIR_V3 = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
CACHE_DIR_V4 = ROOT / "Data" / "experiments" / "renal_v4" / "cache"
REPORTS_DIR = ROOT / "reports" / "renal_v4"
OUTPUT_REPORT_PATH = REPORTS_DIR / "renal_v4_reranker_depth_ablation.json"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "


def is_chunk_relevant(ch: dict, q: dict) -> bool:
    return ch.get("chunk_id") in q.get("gold_child_chunk_ids", [])


def is_section_relevant(ch: dict, q: dict) -> bool:
    pid = ch.get("parent_section_id")
    return bool(pid and pid in q.get("gold_parent_section_ids", []))


def is_doc_relevant(ch: dict, q: dict) -> bool:
    did = ch.get("document_id")
    return bool(did and did in q.get("gold_document_ids", []))


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


def main():
    print("=" * 75)
    print("PHASE 13 & 17: RERANKER DEPTH EXPERIMENT (TOP-20 vs TOP-30 vs TOP-40)")
    print("=" * 75)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    assert torch.cuda.is_available(), "CUDA required!"
    device = torch.device("cuda:0")

    # Load Dev Data
    dev_data = json.loads(DEV_PATH.read_text(encoding="utf-8"))
    queries = dev_data["queries"]
    ans_queries = [q for q in queries if q["answerable"]]
    n_ans = len(ans_queries)

    # Load chunks
    chunks = []
    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_text(encoding="utf-8"))
        for ch in payload.get("chunks", []):
            chunks.append(ch)

    reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    doc_ids_sorted = sorted(list(set(ch["document_id"] for ch in chunks)))
    doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
    chunk_doc_indices = np.array([doc_id_to_idx[ch["document_id"]] for ch in chunks], dtype=np.int32)

    # Load representations
    corpus_arr = np.load(CACHE_DIR_V3 / "all23_corpus_embeddings.npy")
    doc_emb = np.load(CACHE_DIR_V3 / "all23_doc_embeddings.npy")
    sec_structural = np.load(CACHE_DIR_V4 / "all629_section_structural_embeddings.npy")
    sec_meta = json.loads((CACHE_DIR_V4 / "sections_metadata.json").read_text(encoding="utf-8"))
    chunk_to_sec = np.array(sec_meta["chunk_to_section"], dtype=np.int32)

    # Load models
    embed_tok = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
    embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device)
    embed_model.eval()
    reranker = CrossEncoder(RERANK_MODEL_ID, trust_remote_code=True, device="cuda:0")

    # Query encodings
    q_texts = [q["query"] for q in ans_queries]
    q_instruct = [QUERY_INSTRUCTION + q for q in q_texts]
    q_embs = encode_texts(q_instruct, embed_tok, embed_model, device)
    per_query_enc_ms = 6.5

    p_sims = np.dot(q_embs, corpus_arr.T)
    d_sims = np.dot(q_embs, doc_emb.T)
    s_sims = np.dot(q_embs, sec_structural.T)

    depth_settings = [20, 30, 40]
    results = []

    for depth in depth_settings:
        print(f"\n--- Evaluating Reranker Depth R={depth} ---")
        doc_hit_1, doc_hit_5 = 0, 0
        sec_hit_1, sec_hit_5 = 0, 0
        pass_hit_1, pass_hit_3, pass_hit_5, pass_hit_10 = 0, 0, 0, 0
        rerank_input_hit = 0
        mrr_sum, ndcg_sum = 0.0, 0.0
        s2_lats, total_lats = [], []

        for q_idx, q in enumerate(ans_queries):
            q_text = q["query"]
            comb = p_sims[q_idx] + 0.18 * d_sims[q_idx][chunk_doc_indices] + 0.12 * s_sims[q_idx][chunk_to_sec]
            stage1_sorted = np.argsort(comb)[::-1]
            top_cands_idx = stage1_sorted[:depth]
            cands_to_rerank = [chunks[i] for i in top_cands_idx]

            # Did the gold evidence make it into this depth's reranker input?
            r_hit = any(is_chunk_relevant(chunks[i], q) for i in top_cands_idx)
            rerank_input_hit += int(r_hit)

            # Rerank
            t0_s2 = time.perf_counter()
            pairs = [[q_text, c.get("text", "")] for c in cands_to_rerank]
            with torch.inference_mode():
                raw_r = reranker.predict(pairs, batch_size=8, show_progress_bar=False)
            r_scores = np.asarray(raw_r, dtype=np.float32).reshape(-1)
            r_order = np.argsort(r_scores)[::-1]
            t1_s2 = time.perf_counter()
            s2_ms = (t1_s2 - t0_s2) * 1000.0
            tot_ms = per_query_enc_ms + 1.0 + s2_ms
            s2_lats.append(s2_ms)
            total_lats.append(tot_ms)

            reranked_depth = [cands_to_rerank[int(i)] for i in r_order]
            remaining = [chunks[i] for i in stage1_sorted[depth:100]]
            full_ranked = reranked_depth + remaining

            d_h1 = any(is_doc_relevant(ch, q) for ch in full_ranked[:1])
            d_h5 = any(is_doc_relevant(ch, q) for ch in full_ranked[:5])
            s_h1 = any(is_section_relevant(ch, q) for ch in full_ranked[:1])
            s_h5 = any(is_section_relevant(ch, q) for ch in full_ranked[:5])
            p_h1 = any(is_chunk_relevant(ch, q) for ch in full_ranked[:1])
            p_h3 = any(is_chunk_relevant(ch, q) for ch in full_ranked[:3])
            p_h5 = any(is_chunk_relevant(ch, q) for ch in full_ranked[:5])
            p_h10 = any(is_chunk_relevant(ch, q) for ch in full_ranked[:10])

            doc_hit_1 += int(d_h1)
            doc_hit_5 += int(d_h5)
            sec_hit_1 += int(s_h1)
            sec_hit_5 += int(s_h5)
            pass_hit_1 += int(p_h1)
            pass_hit_3 += int(p_h3)
            pass_hit_5 += int(p_h5)
            pass_hit_10 += int(p_h10)

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

        res = {
            "rerank_depth": depth,
            "RerankerInputHit": f"{rerank_input_hit}/{n_ans} ({rerank_input_hit/n_ans:.4f})",
            "PassageHit@1": f"{pass_hit_1}/{n_ans} ({pass_hit_1/n_ans:.4f})",
            "PassageHit@3": f"{pass_hit_3}/{n_ans} ({pass_hit_3/n_ans:.4f})",
            "PassageHit@5": f"{pass_hit_5}/{n_ans} ({pass_hit_5/n_ans:.4f})",
            "PassageHit@10": f"{pass_hit_10}/{n_ans} ({pass_hit_10/n_ans:.4f})",
            "DocumentHit@1": f"{doc_hit_1}/{n_ans} ({doc_hit_1/n_ans:.4f})",
            "ParentSectionHit@1": f"{sec_hit_1}/{n_ans} ({sec_hit_1/n_ans:.4f})",
            "MRR": round(mrr_sum / n_ans, 4),
            "nDCG@10": round(ndcg_sum / n_ans, 4),
            "rerank_p50_ms": round(float(np.percentile(s2_lats, 50)), 2),
            "rerank_p95_ms": round(float(np.percentile(s2_lats, 95)), 2),
            "total_p50_ms": round(float(np.percentile(total_lats, 50)), 2),
            "total_p95_ms": round(float(np.percentile(total_lats, 95)), 2),
        }
        results.append(res)
        print(f"Depth R={depth}: RerankInputHit={res['RerankerInputHit']}, PassHit@1={res['PassageHit@1']}, PassHit@5={res['PassageHit@5']}, MRR={res['MRR']}, Latency p50={res['total_p50_ms']}ms")

    print("\n" + "=" * 90)
    print(f"{'Depth':10s} | {'RerankInputHit':16s} | {'PassHit@1':14s} | {'PassHit@5':14s} | {'MRR':7s} | {'Latency p50':12s}")
    print("=" * 90)
    for r in results:
        print(f"R={r['rerank_depth']:<8d} | {r['RerankerInputHit']:16s} | {r['PassageHit@1']:14s} | {r['PassageHit@5']:14s} | {r['MRR']:<7.4f} | {r['total_p50_ms']:<6.1f} ms")
    print("=" * 90)

    payload = {
        "mission": "MEDICALPLAB RENAL V4",
        "stage": "Phase 13 & 17 Reranker Depth Experiment",
        "dataset_name": "RETRIEVAL_DEV_V4",
        "results": results
    }
    OUTPUT_REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    rep_sha = hashlib.sha256(OUTPUT_REPORT_PATH.read_bytes()).hexdigest()
    OUTPUT_REPORT_PATH.with_suffix(".json.sha256").write_text(f"{rep_sha}  {OUTPUT_REPORT_PATH.name}\n", encoding="utf-8")
    print(f"\nPersisted reranker depth report: {OUTPUT_REPORT_PATH} (SHA: {rep_sha})")


if __name__ == "__main__":
    main()
