"""
MedicalPlab Renal V7 — Bounded Model Bake-Off on TRAIN_DEV (N=80)
================================================================
Evaluates retrieval stacks strictly on TRAIN_DEV:
1. Baseline Dense (V3 architecture: single-channel Qwen3 dense, top-20 candidate depth)
2. Pure BM25 (Okapi BM25, candidate depth 50)
3. Dual Hybrid (Qwen3 dense + BM25, RRF, candidate depth 50)
4. Stack A: Full Multi-Channel V7 (Dense + BM25 + Entity Sparse + Structural, RRF, depth 50, structured reranker)
5. Stack A+: Full Multi-Channel V7 (Depth 100)

Reports:
- Recall@20, Recall@50, Recall@100
- Hit@1, Hit@5
- MRR, nDCG@10
- p50 / p95 latency
- VRAM usage
"""

import json
import math
import sys
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / ".renal_env"))
sys.path.insert(0, str(_ROOT / "src"))

import numpy as np
import torch

from medicalplab.learn.renal_v7_retriever import (
    RenalV7MultiChannelRetriever,
    MEDICAL_RERANKER_INSTRUCTION,
)

REPORTS_DIR = _ROOT / "reports" / "renal_v7"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
TRAIN_DEV_PATH = _ROOT / "evaluation" / "renal" / "v7" / "renal-train-dev-v7.json"


def compute_ndcg_at_k(ranked_chunk_ids: list[str], gold_chunk_ids: set[str], k: int = 10) -> float:
    dcg = 0.0
    for i, cid in enumerate(ranked_chunk_ids[:k]):
        if cid in gold_chunk_ids:
            dcg += 1.0 / math.log2(i + 2)
    # Ideal DCG for 1 relevant item is 1.0 / log2(2) = 1.0
    idcg = 1.0
    return dcg / idcg


def evaluate_configuration(name: str, retriever: RenalV7MultiChannelRetriever, queries_data: list[dict], candidate_depth: int = 50, use_channels: list[str] = None):
    print(f"\n=======================================================")
    print(f"Evaluating: {name} (Candidate Depth = {candidate_depth})")
    print(f"=======================================================")

    n_queries = len(queries_data)
    rec20_cnt = 0
    rec50_cnt = 0
    rec100_cnt = 0
    hit1_cnt = 0
    hit5_cnt = 0
    reciprocal_ranks = []
    ndcg_list = []
    latencies = []

    # Backup original weights
    orig_dense_w = retriever.dense_weight
    orig_bm25_w = retriever.bm25_weight
    orig_ent_w = retriever.entity_sparse_weight
    orig_struct_w = retriever.structural_weight

    if use_channels:
        retriever.dense_weight = orig_dense_w if "dense" in use_channels else 0.0
        retriever.bm25_weight = orig_bm25_w if "bm25" in use_channels else 0.0
        retriever.entity_sparse_weight = orig_ent_w if "entity_sparse" in use_channels else 0.0
        retriever.structural_weight = orig_struct_w if "structural" in use_channels else 0.0

    retriever.candidate_depth = candidate_depth

    for q_idx, item in enumerate(queries_data):
        q = item["query"]
        gold_cids = set(item["gold_chunk_ids"])

        t0 = time.perf_counter()
        candidates = retriever.acquire_candidates(q, top_k=candidate_depth)
        t_acq = time.perf_counter() - t0

        cand_cids = [c.chunk_id for c in candidates]

        # Check candidate recall
        if any(c in gold_cids for c in cand_cids[:20]):
            rec20_cnt += 1
        if any(c in gold_cids for c in cand_cids[:50]):
            rec50_cnt += 1
        if any(c in gold_cids for c in cand_cids[:100]):
            rec100_cnt += 1

        # Rerank candidates
        t1 = time.perf_counter()
        instruction_query = MEDICAL_RERANKER_INSTRUCTION + q
        pairs = []
        for cand in candidates:
            idx = retriever._chunk_id_to_idx[cand.chunk_id]
            pairs.append([instruction_query, retriever._rendered_passages[idx]])

        if pairs:
            scores = retriever._reranker.predict(pairs, batch_size=16, show_progress_bar=False)
            r_scores = np.asarray(scores, dtype=np.float32).reshape(-1)
            for i, cand in enumerate(candidates):
                cand.rerank_score = float(r_scores[i])
            reranked = sorted(candidates, key=lambda c: c.rerank_score, reverse=True)
        else:
            reranked = candidates

        t_total = (time.perf_counter() - t0) * 1000.0
        latencies.append(t_total)

        reranked_cids = [c.chunk_id for c in reranked]

        # Top-1 and Top-5 hits
        if reranked_cids and reranked_cids[0] in gold_cids:
            hit1_cnt += 1
        if any(c in gold_cids for c in reranked_cids[:5]):
            hit5_cnt += 1

        # MRR
        rr = 0.0
        for r_pos, cid in enumerate(reranked_cids):
            if cid in gold_cids:
                rr = 1.0 / (r_pos + 1)
                break
        reciprocal_ranks.append(rr)

        # nDCG
        ndcg_list.append(compute_ndcg_at_k(reranked_cids, gold_cids, k=10))

    # Restore weights
    retriever.dense_weight = orig_dense_w
    retriever.bm25_weight = orig_bm25_w
    retriever.entity_sparse_weight = orig_ent_w
    retriever.structural_weight = orig_struct_w

    rec20_pct = (rec20_cnt / n_queries) * 100.0
    rec50_pct = (rec50_cnt / n_queries) * 100.0
    rec100_pct = (rec100_cnt / n_queries) * 100.0
    hit1_pct = (hit1_cnt / n_queries) * 100.0
    hit5_pct = (hit5_cnt / n_queries) * 100.0
    mrr_val = float(np.mean(reciprocal_ranks))
    ndcg_val = float(np.mean(ndcg_list))
    p50_lat = float(np.percentile(latencies, 50))
    p95_lat = float(np.percentile(latencies, 95))

    vram_mb = 0.0
    if torch.cuda.is_available():
        vram_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)

    print(f"Results for {name}:")
    print(f"  Recall@20:  {rec20_cnt}/{n_queries} ({rec20_pct:.2f}%)")
    print(f"  Recall@50:  {rec50_cnt}/{n_queries} ({rec50_pct:.2f}%)")
    print(f"  Recall@100: {rec100_cnt}/{n_queries} ({rec100_pct:.2f}%)")
    print(f"  Hit@1:      {hit1_cnt}/{n_queries} ({hit1_pct:.2f}%)")
    print(f"  Hit@5:      {hit5_cnt}/{n_queries} ({hit5_pct:.2f}%)")
    print(f"  MRR:        {mrr_val:.4f}")
    print(f"  nDCG@10:    {ndcg_val:.4f}")
    print(f"  p50 Latency: {p50_lat:.1f} ms | p95 Latency: {p95_lat:.1f} ms")
    print(f"  Max VRAM:   {vram_mb:.1f} MB")

    return {
        "name": name,
        "candidate_depth": candidate_depth,
        "n_queries": n_queries,
        "recall_at_20": {"count": rec20_cnt, "percent": rec20_pct},
        "recall_at_50": {"count": rec50_cnt, "percent": rec50_pct},
        "recall_at_100": {"count": rec100_cnt, "percent": rec100_pct},
        "hit_at_1": {"count": hit1_cnt, "percent": hit1_pct},
        "hit_at_5": {"count": hit5_cnt, "percent": hit5_pct},
        "mrr": round(mrr_val, 4),
        "ndcg_at_10": round(ndcg_val, 4),
        "p50_latency_ms": round(p50_lat, 1),
        "p95_latency_ms": round(p95_lat, 1),
        "max_vram_mb": round(vram_mb, 1)
    }


def main():
    print("Loading TRAIN_DEV benchmark...")
    queries_data = json.loads(TRAIN_DEV_PATH.read_bytes())
    print(f"Loaded {len(queries_data)} queries from {TRAIN_DEV_PATH.name}")

    print("Initializing RenalV7MultiChannelRetriever...")
    retriever = RenalV7MultiChannelRetriever(_ROOT / "Data")
    retriever.load()

    bakeoff_results = {}

    # 1. Config 1: Baseline Dense (V3 style single-channel, depth 20)
    bakeoff_results["cfg1_dense_baseline_v3"] = evaluate_configuration(
        "Config 1: Single-Channel Dense Baseline (V3 style, depth 20)",
        retriever,
        queries_data,
        candidate_depth=20,
        use_channels=["dense"]
    )

    # 2. Config 2: Pure BM25 (depth 50)
    bakeoff_results["cfg2_pure_bm25"] = evaluate_configuration(
        "Config 2: Pure Okapi BM25 (depth 50)",
        retriever,
        queries_data,
        candidate_depth=50,
        use_channels=["bm25"]
    )

    # 3. Config 3: Dual Hybrid (Dense + BM25, RRF, depth 50)
    bakeoff_results["cfg3_dense_bm25_rrf"] = evaluate_configuration(
        "Config 3: Dual Hybrid Dense + BM25 (RRF, depth 50)",
        retriever,
        queries_data,
        candidate_depth=50,
        use_channels=["dense", "bm25"]
    )

    # 4. Config 4: STACK A (Full Multi-Channel V7, depth 50)
    bakeoff_results["cfg4_stack_a_multichannel_d50"] = evaluate_configuration(
        "Config 4 (STACK A): Full Multi-Channel V7 (Dense+BM25+Entity+Struct, depth 50)",
        retriever,
        queries_data,
        candidate_depth=50,
        use_channels=["dense", "bm25", "entity_sparse", "structural"]
    )

    # 5. Config 5: STACK A+ (Full Multi-Channel V7, depth 100)
    bakeoff_results["cfg5_stack_a_multichannel_d100"] = evaluate_configuration(
        "Config 5 (STACK A+): Full Multi-Channel V7 (Depth 100)",
        retriever,
        queries_data,
        candidate_depth=100,
        use_channels=["dense", "bm25", "entity_sparse", "structural"]
    )

    # Save report
    out_path = REPORTS_DIR / "renal_v7_model_bakeoff_report.json"
    out_path.write_text(json.dumps(bakeoff_results, indent=2), encoding="utf-8")

    import hashlib
    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    (REPORTS_DIR / "renal_v7_model_bakeoff_report.json.sha256").write_text(f"{sha}  renal_v7_model_bakeoff_report.json", encoding="utf-8")
    print(f"\nSaved bake-off report to {out_path.name} (SHA-256: {sha})")

if __name__ == "__main__":
    main()
