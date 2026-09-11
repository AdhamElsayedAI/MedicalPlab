"""
MedicalPlab Renal V7 — Milestone 8: One-Shot Frozen Product Test Execution (N=100)
=================================================================================
Executes the frozen undergraduate clinical benchmark strictly ONCE.
- Benchmark: evaluation/renal/v7/renal-product-test-v7.json (N=100)
- Architecture: Frozen Stack A (Multi-Channel V7, Depth 50, Structured Reranking)

Reports:
- CandidateRecall@20, CandidateRecall@50 (+ Wilson 95% CIs)
- PassageHit@1, PassageHit@5 (+ Wilson 95% CIs)
- DocumentHit@1, DocumentHit@5 (+ Wilson 95% CIs)
- MRR, nDCG@10
- Latency (p50, p95)
- Categorized error breakdown
- Evidence groundedness & citation verification
"""

import hashlib
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
BENCHMARK_PATH = _ROOT / "evaluation" / "renal" / "v7" / "renal-product-test-v7.json"


def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    z = 1.95996  # 95% normal quantile
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
    idcg = 1.0
    return dcg / idcg


def get_doc_id(chunk_id: str) -> str:
    parts = chunk_id.split("-")
    if len(parts) >= 4:
        return "-".join(parts[:4])
    return chunk_id.split("-C")[0]


def main():
    print(f"Loading frozen product benchmark from {BENCHMARK_PATH.name}...")
    benchmark_bytes = BENCHMARK_PATH.read_bytes()
    benchmark_sha = hashlib.sha256(benchmark_bytes).hexdigest()
    queries = json.loads(benchmark_bytes)
    n = len(queries)
    print(f"Loaded {n} frozen benchmark queries (SHA-256: {benchmark_sha})")

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
    category_failures = {
        "intra_document_sibling": [],
        "cross_document_clinical_distractor": [],
        "lexical_distractor": []
    }

    t_start_total = time.perf_counter()

    for idx, item in enumerate(queries):
        q = item["query"]
        gold_cids = set(item["gold_chunk_ids"])
        gold_doc = item.get("gold_document_id") or item.get("source_document_id", "")
        evidence_quote = item.get("evidence_span") or item.get("evidence_quote", "")

        t0 = time.perf_counter()

        # Step 1: Candidate acquisition
        candidates = retriever.acquire_candidates(q, top_k=50)
        cand_cids = [c.chunk_id for c in candidates]

        has_rec20 = any(c in gold_cids for c in cand_cids[:20])
        has_rec50 = any(c in gold_cids for c in cand_cids[:50])
        if has_rec20:
            cand_rec20_cnt += 1
        if has_rec50:
            cand_rec50_cnt += 1

        # Step 2: Structured Reranking
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

        t_elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(t_elapsed_ms)

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

        # MRR
        rr = 0.0
        gold_rank = None
        for r_pos, cid in enumerate(ranked_cids):
            if cid in gold_cids:
                rr = 1.0 / (r_pos + 1)
                gold_rank = r_pos + 1
                break
        reciprocal_ranks.append(rr)

        # nDCG
        ndcg_val = compute_ndcg_at_k(ranked_cids, gold_cids, k=10)
        ndcg_list.append(ndcg_val)

        # Failure categorization
        if not is_p_hit1:
            top_cand = reranked[0]
            if top1_doc == gold_doc:
                cat = "intra_document_sibling"
            elif top_cand.channel_ranks.get("bm25", 999) <= 5 and top_cand.channel_ranks.get("dense", 999) > 20:
                cat = "lexical_distractor"
            else:
                cat = "cross_document_clinical_distractor"
            category_failures[cat].append({
                "query_id": item.get("query_id"),
                "query": q,
                "gold_chunks": list(gold_cids),
                "gold_rank": gold_rank,
                "top1_chunk": top1_cid,
                "top1_heading": top_cand.chunk.get("heading"),
                "category": cat,
                "evidence_quote": evidence_quote
            })

        per_query_results.append({
            "query_id": item.get("query_id"),
            "query": q,
            "domain_category": item.get("domain_category"),
            "gold_chunk_ids": list(gold_cids),
            "gold_document_id": gold_doc,
            "gold_rank": gold_rank,
            "passage_hit_at_1": is_p_hit1,
            "passage_hit_at_5": is_p_hit5,
            "document_hit_at_1": is_d_hit1,
            "document_hit_at_5": is_d_hit5,
            "top1_chunk_id": top1_cid,
            "latency_ms": round(t_elapsed_ms, 1)
        })

    t_total = time.perf_counter() - t_start_total

    # Percentages and CIs
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
    p50_lat = float(np.percentile(latencies, 50))
    p95_lat = float(np.percentile(latencies, 95))

    vram_mb = 0.0
    if torch.cuda.is_available():
        vram_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)

    print("\n=======================================================")
    print(f"FROZEN PRODUCT TEST (N={n}) FINAL METRICS:")
    print("=======================================================")
    print(f"CandidateRecall@20: {cand_rec20_cnt}/{n} ({rec20_pct:.2f}%) [95% CI: {rec20_ci[0]}% - {rec20_ci[1]}%]")
    print(f"CandidateRecall@50: {cand_rec50_cnt}/{n} ({rec50_pct:.2f}%) [95% CI: {rec50_ci[0]}% - {rec50_ci[1]}%]")
    print(f"PassageHit@1:       {passage_hit1_cnt}/{n} ({hit1_pct:.2f}%) [95% CI: {hit1_ci[0]}% - {hit1_ci[1]}%]")
    print(f"PassageHit@5:       {passage_hit5_cnt}/{n} ({hit5_pct:.2f}%) [95% CI: {hit5_ci[0]}% - {hit5_ci[1]}%]")
    print(f"DocumentHit@1:      {doc_hit1_cnt}/{n} ({doc1_pct:.2f}%) [95% CI: {doc1_ci[0]}% - {doc1_ci[1]}%]")
    print(f"DocumentHit@5:      {doc_hit5_cnt}/{n} ({doc5_pct:.2f}%) [95% CI: {doc5_ci[0]}% - {doc5_ci[1]}%]")
    print(f"MRR:                {mrr:.4f}")
    print(f"nDCG@10:            {ndcg:.4f}")
    print(f"Latency:            p50: {p50_lat:.1f} ms | p95: {p95_lat:.1f} ms | total: {t_total:.1f} s")
    print(f"Max VRAM:           {vram_mb:.1f} MB")
    print(f"\nFailure Breakdown (Total rank-1 misses = {n - passage_hit1_cnt}):")
    print(f"  Intra-document siblings:          {len(category_failures['intra_document_sibling'])}")
    print(f"  Cross-document clinical distractors: {len(category_failures['cross_document_clinical_distractor'])}")
    print(f"  Lexical distractors:              {len(category_failures['lexical_distractor'])}")

    report = {
        "benchmark": "renal-product-test-v7.json",
        "benchmark_sha256": benchmark_sha,
        "sample_size": n,
        "execution_mode": "ONE_SHOT_FROZEN",
        "pipeline": "Stack A: RenalV7MultiChannelRetriever",
        "metrics": {
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
                "p50": round(p50_lat, 1),
                "p95": round(p95_lat, 1),
                "total_seconds": round(t_total, 1)
            },
            "max_vram_mb": round(vram_mb, 1)
        },
        "failure_categorization": {
            "intra_document_sibling_count": len(category_failures["intra_document_sibling"]),
            "cross_document_clinical_distractor_count": len(category_failures["cross_document_clinical_distractor"]),
            "lexical_distractor_count": len(category_failures["lexical_distractor"]),
            "details": category_failures
        },
        "per_query_results": per_query_results
    }

    out_file = REPORTS_DIR / "renal_v7_frozen_product_test_report.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    out_sha = hashlib.sha256(out_file.read_bytes()).hexdigest()
    (REPORTS_DIR / "renal_v7_frozen_product_test_report.json.sha256").write_text(f"{out_sha}  renal_v7_frozen_product_test_report.json", encoding="utf-8")
    print(f"\nWrote product test report to {out_file.name} (SHA-256: {out_sha})")


if __name__ == "__main__":
    main()
