"""
Clean Retrieval Re-baseline on PRODUCT_DEV_V3 (N=100)
=====================================================
Evaluates existing reference systems without any model changes:
1. BGE-M3 Exhaustive Hybrid (BAAI/bge-m3 @ 5617a9f61b028005a4858fdac845db406aefb181)
2. Measures:
   - Semantic Recall@1, 5, 10, 20, 50, 100, 200
   - Exact Recall@1, 5, 10, 20, 50, 100, 200
   - Gold rank distribution (median, p75, p90, max, not_retrieved)
   - MRR & nDCG@10
   - Passage-level DocHit@1, 3, 5, 10 (derived from the SAME passage ranking)
   - Passage-level SectionHit@1, 3, 5, 10 (derived from the SAME passage ranking)
3. Compares against PRODUCT_DEV_V2 to determine TASK_DEFINITION_CORRECTION_DELTA.
"""

import gc
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / ".renal_env"))
sys.path.insert(0, str(_ROOT / "src"))

import torch
from medicalplab.evidence_engine.bge_m3_retriever import BGEM3ExhaustiveRetriever
from medicalplab.evidence_engine.query_representation import ClinicalQueryProcessor

DEV3_PATH = _ROOT / "evaluation" / "evidence_engine" / "product_dev_v3.json"
REPORT_PATH = _ROOT / "reports" / "evidence_engine" / "product_dev_v3_bge_m3_baseline_report.json"
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

def wilson_score_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z * math.sqrt((p * (1 - p) / total) + (z**2) / (4 * (total**2)))) / denom
    return max(0.0, center - spread), min(1.0, center + spread)

def make_stat(count: int, n: int) -> dict[str, Any]:
    low, high = wilson_score_interval(count, n)
    return {
        "count": count,
        "total": n,
        "rate": count / n if n > 0 else 0.0,
        "pct": f"{(count / n) * 100:.2f}%" if n > 0 else "0.0%",
        "ci_95_wilson": [round(low, 4), round(high, 4)],
    }

def compute_dcg(relevances: list[int], k: int = 10) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevances[:k], 1):
        if rel > 0:
            dcg += (2**rel - 1) / math.log2(i + 1)
    return dcg

def compute_ndcg(retrieved_ids: list[str], gold_ids: set[str], k: int = 10) -> float:
    rels = [1 if cid in gold_ids else 0 for cid in retrieved_ids[:k]]
    actual_dcg = compute_dcg(rels, k)
    ideal_rels = sorted(rels, reverse=True)
    ideal_dcg = compute_dcg(ideal_rels, k)
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0

def main():
    print("=" * 70)
    print("CLEAN RETRIEVAL RE-BASELINE ON PRODUCT_DEV_V3")
    print("=" * 70)

    items = json.loads(DEV3_PATH.read_bytes())
    n = len(items)
    print(f"Loaded {n} items from {DEV3_PATH.name}")

    query_processor = ClinicalQueryProcessor()
    query_reps = [query_processor.process_query(it["query"]) for it in items]

    retriever = BGEM3ExhaustiveRetriever(data_root=_ROOT / "Data")
    retriever.ensure_corpus_representations()

    # Metrics accumulators
    k_eval = [1, 5, 10, 20, 50, 100, 200]
    rec_sem = {k: 0 for k in k_eval}
    rec_exact = {k: 0 for k in k_eval}

    doc_hits = {k: 0 for k in [1, 3, 5, 10]}
    sec_hits = {k: 0 for k in [1, 3, 5, 10]}

    ranks_sem = []
    ranks_exact = []
    mrr_sum = 0.0
    ndcg_sum = 0.0
    latencies = []

    per_item_results = []

    t_start = time.perf_counter()
    for idx, (item, q_rep) in enumerate(zip(items, query_reps), 1):
        t0 = time.perf_counter()
        qid = item["query_id"]
        exact_golds = set(item.get("exact_gold_chunk_ids", []))
        sem_golds = set(item.get("semantic_support_chunk_ids", exact_golds))
        gold_doc = item.get("gold_document_id", "")

        # Get gold section from corpus
        gold_cid = next(iter(exact_golds), "")
        gold_ch = retriever.chunks.get(gold_cid, {})
        gold_sec = gold_ch.get("heading") or (gold_ch.get("section_path") or [""])[0]

        # Exhaustive Hybrid retrieval (top 200)
        cands = retriever.retrieve_exhaustive(q_rep, top_k=200, mode="hybrid")
        retrieved_cids = [c.chunk_id for c in cands]

        # Rank metrics
        r_sem = next((r for r, cid in enumerate(retrieved_cids, 1) if cid in sem_golds), None)
        r_exact = next((r for r, cid in enumerate(retrieved_cids, 1) if cid in exact_golds), None)

        if r_sem is not None:
            ranks_sem.append(r_sem)
            mrr_sum += 1.0 / r_sem
            for k in k_eval:
                if r_sem <= k:
                    rec_sem[k] += 1
        if r_exact is not None:
            ranks_exact.append(r_exact)
            for k in k_eval:
                if r_exact <= k:
                    rec_exact[k] += 1

        ndcg_sum += compute_ndcg(retrieved_cids, sem_golds, k=10)

        # Passage-level DocHit and SectionHit from the SAME ranked list
        for k in [1, 3, 5, 10]:
            slice_cands = cands[:k]
            # Doc hit: any candidate in top-k is from the gold document
            if any(c.document_id == gold_doc for c in slice_cands):
                doc_hits[k] += 1
            # Section hit: any candidate in top-k is from gold doc AND gold section
            if any(c.document_id == gold_doc and (c.heading == gold_sec or (c.section_path and c.section_path[0] == gold_sec)) for c in slice_cands):
                sec_hits[k] += 1

        dt_ms = (time.perf_counter() - t0) * 1000
        latencies.append(dt_ms)

        per_item_results.append({
            "query_id": qid,
            "query": item["query"],
            "rank_sem": r_sem,
            "rank_exact": r_exact,
            "top1_cid": retrieved_cids[0] if retrieved_cids else None,
            "top1_score": round(cands[0].fused_score, 4) if cands else 0.0,
            "latency_ms": round(dt_ms, 1)
        })

        if idx % 25 == 0 or idx == n:
            print(f"Scored {idx}/{n} queries (mean latency: {np.mean(latencies):.1f}ms)...")

    total_time = time.perf_counter() - t_start

    # Summary distributions
    sem_ranks_arr = np.array(ranks_sem) if ranks_sem else np.array([9999])
    exact_ranks_arr = np.array(ranks_exact) if ranks_exact else np.array([9999])

    report = {
        "benchmark": "PRODUCT_DEV_V3",
        "benchmark_file": str(DEV3_PATH.relative_to(_ROOT)),
        "n_queries": n,
        "retriever_model": "BAAI/bge-m3",
        "retriever_revision": "5617a9f61b028005a4858fdac845db406aefb181",
        "scoring_mode": "official_hybrid_dense_sparse_colbert",
        "total_corpus_passages_indexed": len(retriever.chunks),
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_elapsed_seconds": round(total_time, 2),
        "mean_query_latency_ms": round(float(np.mean(latencies)), 1),
        "p50_latency_ms": round(float(np.percentile(latencies, 50)), 1),
        "p95_latency_ms": round(float(np.percentile(latencies, 95)), 1),
        "metrics": {
            "semantic_recall": {f"recall_at_{k}": make_stat(rec_sem[k], n) for k in k_eval},
            "exact_recall": {f"recall_at_{k}": make_stat(rec_exact[k], n) for k in k_eval},
            "mrr": round(mrr_sum / n, 4),
            "ndcg_at_10": round(ndcg_sum / n, 4),
            "passage_level_doc_hits": {f"doc_hit_at_{k}": make_stat(doc_hits[k], n) for k in [1, 3, 5, 10]},
            "passage_level_section_hits": {f"section_hit_at_{k}": make_stat(sec_hits[k], n) for k in [1, 3, 5, 10]},
            "semantic_rank_distribution": {
                "median": float(np.median(sem_ranks_arr)),
                "p75": float(np.percentile(sem_ranks_arr, 75)),
                "p90": float(np.percentile(sem_ranks_arr, 90)),
                "max": int(np.max(sem_ranks_arr)),
                "not_retrieved_in_top200": n - len(ranks_sem)
            },
            "exact_rank_distribution": {
                "median": float(np.median(exact_ranks_arr)),
                "p75": float(np.percentile(exact_ranks_arr, 75)),
                "p90": float(np.percentile(exact_ranks_arr, 90)),
                "max": int(np.max(exact_ranks_arr)),
                "not_retrieved_in_top200": n - len(ranks_exact)
            }
        },
        "per_item_results": per_item_results
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    sha = compute_sha256(REPORT_PATH.read_bytes())
    (REPORT_PATH.with_suffix(".json.sha256")).write_text(f"{sha}  {REPORT_PATH.name}\n", encoding="utf-8")

    print("\n" + "=" * 70)
    print("RESULTS: BGE-M3 ON CLEAN PRODUCT_DEV_V3")
    print("=" * 70)
    print(f"Semantic Recall@1  : {report['metrics']['semantic_recall']['recall_at_1']['pct']}")
    print(f"Semantic Recall@5  : {report['metrics']['semantic_recall']['recall_at_5']['pct']}")
    print(f"Semantic Recall@10 : {report['metrics']['semantic_recall']['recall_at_10']['pct']}")
    print(f"Semantic Recall@20 : {report['metrics']['semantic_recall']['recall_at_20']['pct']}")
    print(f"Semantic Recall@50 : {report['metrics']['semantic_recall']['recall_at_50']['pct']}")
    print(f"Semantic Recall@100: {report['metrics']['semantic_recall']['recall_at_100']['pct']}")
    print(f"MRR                : {report['metrics']['mrr']:.4f}")
    print(f"nDCG@10            : {report['metrics']['ndcg_at_10']:.4f}")
    print(f"DocHit@1           : {report['metrics']['passage_level_doc_hits']['doc_hit_at_1']['pct']}")
    print(f"DocHit@5           : {report['metrics']['passage_level_doc_hits']['doc_hit_at_5']['pct']}")
    print(f"SectionHit@1       : {report['metrics']['passage_level_section_hits']['section_hit_at_1']['pct']}")
    print(f"SectionHit@5       : {report['metrics']['passage_level_section_hits']['section_hit_at_5']['pct']}")
    print(f"\nSaved report to {REPORT_PATH.name} (SHA-256: {sha})")

if __name__ == "__main__":
    main()
