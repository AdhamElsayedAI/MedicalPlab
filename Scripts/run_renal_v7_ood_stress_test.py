"""
MedicalPlab Renal V7 — Milestone 9: OOD Section-Anchored Stress Test (N=40)
===========================================================================
Executes the frozen V6 N=40 validation set with ZERO retuning as an OOD stress test.
Benchmarks against V6 historical baseline:
- V6 Raw Dense Coverage@20: 15 / 40 = 37.50%
- V6 Selector OutputCoverage@20: 18 / 40 = 45.00%
- V6 Dense@500 Ceiling: 36 / 40 = 90.00%

Reports:
- V7 Stack A CandidateRecall@20, CandidateRecall@50
- V7 Stack A PassageHit@1, PassageHit@5
- V7 Stack A DocumentHit@1, DocumentHit@5
- MRR, nDCG@10
"""

import hashlib
import json
import math
import sys
import time
from pathlib import Path

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
OOD_PATH = _ROOT / "evaluation" / "renal" / "v7" / "renal-ood-stress-v6.json"


def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    z = 1.95996
    p = k / n
    denom = 1.0 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    spread = z * math.sqrt((p * (1 - p) / n) + ((z**2) / (4 * n**2))) / denom
    low = max(0.0, center - spread)
    high = min(1.0, center + spread)
    return round(low * 100, 2), round(high * 100, 2)


def compute_ndcg_at_k(ranked_chunk_ids: list[str], gold_chunk_ids: set[str], k: int = 10) -> float:
    dcg = 0.0
    for i, cid in enumerate(ranked_chunk_ids[:k]):
        if cid in gold_chunk_ids:
            dcg += 1.0 / math.log2(i + 2)
    return dcg / 1.0


def get_doc_id(chunk_id: str) -> str:
    parts = chunk_id.split("-")
    if len(parts) >= 4:
        return "-".join(parts[:4])
    return chunk_id.split("-C")[0]


def main():
    print(f"Loading OOD stress test benchmark from {OOD_PATH.name}...")
    ood_bytes = OOD_PATH.read_bytes()
    ood_sha = hashlib.sha256(ood_bytes).hexdigest()
    queries = json.loads(ood_bytes)
    n = len(queries)
    print(f"Loaded {n} OOD stress test queries (SHA-256: {ood_sha})")

    print("\nInitializing Frozen RenalV7MultiChannelRetriever (Stack A)...")
    retriever = RenalV7MultiChannelRetriever(_ROOT / "Data", candidate_depth=50)
    retriever.load()

    cand_rec20_cnt = 0
    cand_rec50_cnt = 0
    passage_hit1_cnt = 0
    passage_hit5_cnt = 0
    doc_hit1_cnt = 0
    doc_hit5_cnt = 0

    reciprocal_ranks = []
    ndcg_list = []
    latencies = []

    per_query_results = []

    t0_all = time.perf_counter()

    for idx, item in enumerate(queries):
        q = item["query"]
        gold_cids = set(item["gold_chunk_ids"])
        gold_doc = item.get("source_document_id") or item.get("gold_document_id") or get_doc_id(list(gold_cids)[0])

        t0 = time.perf_counter()

        candidates = retriever.acquire_candidates(q, top_k=50)
        cand_cids = [c.chunk_id for c in candidates]

        if any(c in gold_cids for c in cand_cids[:20]):
            cand_rec20_cnt += 1
        if any(c in gold_cids for c in cand_cids[:50]):
            cand_rec50_cnt += 1

        instruction_query = MEDICAL_RERANKER_INSTRUCTION + q
        pairs = []
        for cand in candidates:
            c_idx = retriever._chunk_id_to_idx[cand.chunk_id]
            pairs.append([instruction_query, retriever._rendered_passages[c_idx]])

        if pairs:
            scores = retriever._reranker.predict(pairs, batch_size=16, show_progress_bar=False)
            r_scores = np.asarray(scores, dtype=np.float32).reshape(-1)
            for i, cand in enumerate(candidates):
                cand.rerank_score = float(r_scores[i])
            reranked = sorted(candidates, key=lambda c: c.rerank_score, reverse=True)
        else:
            reranked = candidates

        t_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(t_ms)

        ranked_cids = [c.chunk_id for c in reranked]
        top1_cid = ranked_cids[0] if ranked_cids else ""
        top1_doc = get_doc_id(top1_cid) if top1_cid else ""

        is_p_hit1 = top1_cid in gold_cids
        is_p_hit5 = any(c in gold_cids for c in ranked_cids[:5])
        is_d_hit1 = top1_doc == gold_doc
        is_d_hit5 = any(get_doc_id(c) == gold_doc for c in ranked_cids[:5])

        if is_p_hit1:
            passage_hit1_cnt += 1
        if is_p_hit5:
            passage_hit5_cnt += 1
        if is_d_hit1:
            doc_hit1_cnt += 1
        if is_d_hit5:
            doc_hit5_cnt += 1

        rr = 0.0
        gold_rank = None
        for r_pos, cid in enumerate(ranked_cids):
            if cid in gold_cids:
                rr = 1.0 / (r_pos + 1)
                gold_rank = r_pos + 1
                break
        reciprocal_ranks.append(rr)
        ndcg_list.append(compute_ndcg_at_k(ranked_cids, gold_cids, k=10))

        per_query_results.append({
            "query_id": item.get("query_id"),
            "query": q,
            "gold_chunk_ids": list(gold_cids),
            "gold_document_id": gold_doc,
            "gold_rank": gold_rank,
            "passage_hit_at_1": is_p_hit1,
            "passage_hit_at_5": is_p_hit5,
            "document_hit_at_1": is_d_hit1,
            "document_hit_at_5": is_d_hit5,
            "top1_chunk_id": top1_cid,
            "latency_ms": round(t_ms, 1)
        })

    t_total = time.perf_counter() - t0_all

    rec20_pct = (cand_rec20_cnt / n) * 100.0
    rec20_ci = wilson_score_interval(cand_rec20_cnt, n)

    rec50_pct = (cand_rec50_cnt / n) * 100.0
    rec50_ci = wilson_score_interval(cand_rec50_cnt, n)

    hit1_pct = (passage_hit1_cnt / n) * 100.0
    hit1_ci = wilson_score_interval(passage_hit1_cnt, n)

    hit5_pct = (passage_hit5_cnt / n) * 100.0
    hit5_ci = wilson_score_interval(passage_hit5_cnt, n)

    doc1_pct = (doc_hit1_cnt / n) * 100.0
    doc1_ci = wilson_score_interval(doc_hit1_cnt, n)

    doc5_pct = (doc_hit5_cnt / n) * 100.0
    doc5_ci = wilson_score_interval(doc_hit5_cnt, n)

    mrr = float(np.mean(reciprocal_ranks))
    ndcg = float(np.mean(ndcg_list))

    print("\n=======================================================")
    print(f"OOD SECTION-ANCHORED STRESS TEST (N={n}) FINAL METRICS:")
    print("=======================================================")
    print(f"CandidateRecall@20: {cand_rec20_cnt}/{n} ({rec20_pct:.2f}%) [95% CI: {rec20_ci[0]}% - {rec20_ci[1]}%]")
    print(f"CandidateRecall@50: {cand_rec50_cnt}/{n} ({rec50_pct:.2f}%) [95% CI: {rec50_ci[0]}% - {rec50_ci[1]}%]")
    print(f"PassageHit@1:       {passage_hit1_cnt}/{n} ({hit1_pct:.2f}%) [95% CI: {hit1_ci[0]}% - {hit1_ci[1]}%]")
    print(f"PassageHit@5:       {passage_hit5_cnt}/{n} ({hit5_pct:.2f}%) [95% CI: {hit5_ci[0]}% - {hit5_ci[1]}%]")
    print(f"DocumentHit@1:      {doc_hit1_cnt}/{n} ({doc1_pct:.2f}%) [95% CI: {doc1_ci[0]}% - {doc1_ci[1]}%]")
    print(f"DocumentHit@5:      {doc_hit5_cnt}/{n} ({doc5_pct:.2f}%) [95% CI: {doc5_ci[0]}% - {doc5_ci[1]}%]")
    print(f"MRR:                {mrr:.4f}")
    print(f"nDCG@10:            {ndcg:.4f}")
    print(f"\nHistorical V6 Comparison:")
    print(f"  V6 Raw Dense Coverage@20:       15/40 (37.50%)")
    print(f"  V6 Selector OutputCoverage@20:  18/40 (45.00%)")
    print(f"  V7 Stack A CandidateRecall@20:  {cand_rec20_cnt}/40 ({rec20_pct:.2f}%)")
    print(f"  V7 Stack A CandidateRecall@50:  {cand_rec50_cnt}/40 ({rec50_pct:.2f}%)")

    report = {
        "benchmark": "renal-ood-stress-v6.json",
        "benchmark_sha256": ood_sha,
        "classification": "OOD_SECTION_ANCHORED_STRESS_TEST",
        "sample_size": n,
        "historical_v6_baselines": {
            "v6_raw_dense_coverage_at_20": "15/40 (37.50%)",
            "v6_selector_output_coverage_at_20": "18/40 (45.00%)",
            "v6_dense_at_500_ceiling": "36/40 (90.00%)"
        },
        "v7_stack_a_metrics": {
            "candidate_recall_at_20": {
                "count": cand_rec20_cnt,
                "total": n,
                "percent": rec20_pct,
                "ci_95": rec20_ci
            },
            "candidate_recall_at_50": {
                "count": cand_rec50_cnt,
                "total": n,
                "percent": rec50_pct,
                "ci_95": rec50_ci
            },
            "passage_hit_at_1": {
                "count": passage_hit1_cnt,
                "total": n,
                "percent": hit1_pct,
                "ci_95": hit1_ci
            },
            "passage_hit_at_5": {
                "count": passage_hit5_cnt,
                "total": n,
                "percent": hit5_pct,
                "ci_95": hit5_ci
            },
            "document_hit_at_1": {
                "count": doc_hit1_cnt,
                "total": n,
                "percent": doc1_pct,
                "ci_95": doc1_ci
            },
            "document_hit_at_5": {
                "count": doc_hit5_cnt,
                "total": n,
                "percent": doc5_pct,
                "ci_95": doc5_ci
            },
            "mrr": round(mrr, 4),
            "ndcg_at_10": round(ndcg, 4),
            "latency_ms": {
                "p50": round(float(np.percentile(latencies, 50)), 1),
                "p95": round(float(np.percentile(latencies, 95)), 1),
                "total_seconds": round(t_total, 1)
            }
        },
        "per_query_results": per_query_results
    }

    out_file = REPORTS_DIR / "renal_v7_ood_stress_test_report.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    out_sha = hashlib.sha256(out_file.read_bytes()).hexdigest()
    (REPORTS_DIR / "renal_v7_ood_stress_test_report.json.sha256").write_text(f"{out_sha}  renal_v7_ood_stress_test_report.json", encoding="utf-8")
    print(f"\nWrote OOD stress test report to {out_file.name} (SHA-256: {out_sha})")


if __name__ == "__main__":
    main()
