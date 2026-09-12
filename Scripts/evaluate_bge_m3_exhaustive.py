"""
MedicalPlab Shared Evidence Engine V2 — Exhaustive BGE-M3 Retrieval Evaluation
==============================================================================
Evaluates BAAI/bge-m3 across all 2,691 passages exhaustively on PRODUCT_DEV_V2 (N=120).
Zero early candidate pruning, zero document gates, zero section gates.

Computes:
1. Mode A: ColBERT multi-vector late-interaction alone
2. Mode B: Official hybrid (0.4 * dense + 0.2 * sparse + 0.4 * colbert)
3. Semantic & Exact-Gold Recall@1, 5, 10, 20, 50, 100, 200
4. Gold rank distribution: median, p75, p90, max rank, not retrieved
5. Miss classification:
   - CORPUS_COVERAGE_FAILURE
   - QREL_OR_QUERY_CONSTRUCTION_FAILURE
   - MODEL_SEMANTIC_FAILURE
"""

import gc
import hashlib
import json
import logging
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

from medicalplab.evidence_engine.bge_m3_retriever import BGEM3ExhaustiveRetriever
from medicalplab.evidence_engine.query_representation import ClinicalQueryProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("bge_m3_eval")

DEV_PATH = _ROOT / "evaluation" / "evidence_engine" / "product_dev_v2.json"
REPORT_PATH = _ROOT / "reports" / "evidence_engine" / "bge_m3_exhaustive_acquisition_report.json"
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def wilson_score_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z * math.sqrt((p * (1 - p) / total) + (z**2) / (4 * (total**2)))) / denom
    return max(0.0, center - spread), min(1.0, center + spread)


def make_stat(count: int, n: int):
    low, high = wilson_score_interval(count, n)
    return {
        "count": count,
        "total": n,
        "rate": count / n if n > 0 else 0.0,
        "pct": f"{(count / n) * 100:.2f}%" if n > 0 else "0.0%",
        "ci_95_wilson": [round(low, 4), round(high, 4)],
    }


def evaluate_mode(retriever: BGEM3ExhaustiveRetriever, items: list[dict], query_reps: list, mode: str):
    n = len(items)
    cutoff_ks = [1, 5, 10, 20, 50, 100, 200]
    rec_sem = {k: 0 for k in cutoff_ks}
    rec_exact = {k: 0 for k in cutoff_ks}

    gold_ranks_sem = []
    gold_ranks_exact = []
    per_item = []

    t0 = time.perf_counter()
    for idx, (item, q_rep) in enumerate(zip(items, query_reps), 1):
        qid = item["query_id"]
        exact_golds = set(item.get("exact_gold_chunk_ids", []))
        sem_golds = set(item.get("semantic_support_chunk_ids", exact_golds))

        # Exhaustive retrieval of all 2691 passages
        cands = retriever.retrieve_exhaustive(q_rep, top_k=2691, mode=mode)
        cand_cids = [c.chunk_id for c in cands]

        # Find first rank of semantic and exact gold
        r_sem = None
        r_exact = None
        for r, cid in enumerate(cand_cids, 1):
            if r_sem is None and cid in sem_golds:
                r_sem = r
            if r_exact is None and cid in exact_golds:
                r_exact = r
            if r_sem is not None and r_exact is not None:
                break

        if r_sem is not None:
            gold_ranks_sem.append(r_sem)
            for k in cutoff_ks:
                if r_sem <= k:
                    rec_sem[k] += 1

        if r_exact is not None:
            gold_ranks_exact.append(r_exact)
            for k in cutoff_ks:
                if r_exact <= k:
                    rec_exact[k] += 1

        per_item.append({
            "query_id": qid,
            "query": item["query"],
            "first_semantic_rank": r_sem,
            "first_exact_rank": r_exact,
            "top1_chunk_id": cand_cids[0] if cand_cids else None,
            "top1_score": cands[0].fused_score if cands else None,
        })

        if idx % 20 == 0 or idx == n:
            logger.info(f"[{mode.upper()}] Processed {idx}/{n} queries ({time.perf_counter() - t0:.1f}s)...")

    elapsed = time.perf_counter() - t0

    # Rank distributions
    sem_ranks_arr = np.array(gold_ranks_sem) if gold_ranks_sem else np.array([2691])
    exact_ranks_arr = np.array(gold_ranks_exact) if gold_ranks_exact else np.array([2691])

    dist_sem = {
        "median": float(np.median(sem_ranks_arr)),
        "p75": float(np.percentile(sem_ranks_arr, 75)),
        "p90": float(np.percentile(sem_ranks_arr, 90)),
        "max": int(np.max(sem_ranks_arr)),
        "not_retrieved": n - len(gold_ranks_sem),
    }

    dist_exact = {
        "median": float(np.median(exact_ranks_arr)),
        "p75": float(np.percentile(exact_ranks_arr, 75)),
        "p90": float(np.percentile(exact_ranks_arr, 90)),
        "max": int(np.max(exact_ranks_arr)),
        "not_retrieved": n - len(gold_ranks_exact),
    }

    metrics = {
        "semantic_recall": {f"recall_at_{k}": make_stat(rec_sem[k], n) for k in cutoff_ks},
        "exact_recall": {f"recall_at_{k}": make_stat(rec_exact[k], n) for k in cutoff_ks},
        "semantic_rank_distribution": dist_sem,
        "exact_rank_distribution": dist_exact,
        "elapsed_seconds": round(elapsed, 2),
        "mean_query_ms": round((elapsed / n) * 1000, 1),
    }

    return metrics, per_item


def classify_misses(items: list[dict], per_item_results: list[dict], retriever: BGEM3ExhaustiveRetriever) -> dict[str, Any]:
    """Classify every miss at Recall@100 into standard failure taxonomy."""
    classification = {
        "CORPUS_COVERAGE_FAILURE": 0,
        "QREL_OR_QUERY_CONSTRUCTION_FAILURE": 0,
        "MODEL_SEMANTIC_FAILURE": 0,
        "misses_detail": [],
    }

    item_by_id = {it["query_id"]: it for it in items}

    for res in per_item_results:
        r = res["first_semantic_rank"]
        if r is None or r > 100:
            qid = res["query_id"]
            raw_item = item_by_id[qid]
            claim = raw_item.get("canonical_claim", "")
            exact_golds = raw_item.get("exact_gold_chunk_ids", [])
            query = raw_item.get("query", "")

            # Check if gold chunk text actually contains the claim facts
            gold_cid = exact_golds[0] if exact_golds else None
            gold_text = retriever.chunks.get(gold_cid, {}).get("text", "") if gold_cid else ""

            # Check overlap of claim keywords with chunk
            claim_words = [w.lower() for w in claim.split() if len(w) > 4]
            overlap = sum(1 for w in claim_words if w in gold_text.lower())
            ratio = overlap / max(1, len(claim_words))

            if len(gold_text) < 150 or ratio < 0.30:
                cat = "CORPUS_COVERAGE_FAILURE"
                reason = "Target medical proposition absent or insufficiently detailed in the indexed chunk."
            elif "in ." in query or "guide Table" in query or "Renal Topic?" in query:
                cat = "QREL_OR_QUERY_CONSTRUCTION_FAILURE"
                reason = "Benchmark query contains synthetic artifact or malformed section placeholder."
            else:
                cat = "MODEL_SEMANTIC_FAILURE"
                reason = "Evidence is present in chunk but BGE-M3 multi-vector representation failed to rank within top 100."

            classification[cat] += 1
            classification["misses_detail"].append({
                "query_id": qid,
                "query": query,
                "gold_chunk_id": gold_cid,
                "category": cat,
                "reason": reason,
                "actual_rank": r,
            })

    return classification


def main():
    logger.info("================================================================")
    logger.info("BGE-M3 EXHAUSTIVE RETRIEVAL EVALUATION ON PRODUCT_DEV_V2")
    logger.info("================================================================")

    items = json.loads(DEV_PATH.read_bytes())
    n = len(items)
    logger.info(f"Loaded {n} items from {DEV_PATH.name}")

    query_processor = ClinicalQueryProcessor()
    query_reps = [query_processor.process_query(it["query"]) for it in items]

    retriever = BGEM3ExhaustiveRetriever(data_root=_ROOT / "Data")
    retriever.ensure_corpus_representations(batch_size=16)

    # 1. Evaluate Mode A: ColBERT multi-vector alone
    logger.info("\n--- Evaluating Mode A: BGE-M3 ColBERT Multi-Vector Alone ---")
    metrics_colbert, per_item_colbert = evaluate_mode(retriever, items, query_reps, mode="colbert")
    logger.info(f"ColBERT Semantic Recall@20: {metrics_colbert['semantic_recall']['recall_at_20']['pct']}")
    logger.info(f"ColBERT Semantic Recall@50: {metrics_colbert['semantic_recall']['recall_at_50']['pct']}")
    logger.info(f"ColBERT Semantic Recall@100: {metrics_colbert['semantic_recall']['recall_at_100']['pct']}")

    # 2. Evaluate Mode B: Official BGE-M3 Hybrid (0.4 Dense + 0.2 Sparse + 0.4 ColBERT)
    logger.info("\n--- Evaluating Mode B: Official BGE-M3 Hybrid (Dense + Sparse + ColBERT) ---")
    metrics_hybrid, per_item_hybrid = evaluate_mode(retriever, items, query_reps, mode="hybrid")
    logger.info(f"Hybrid Semantic Recall@20: {metrics_hybrid['semantic_recall']['recall_at_20']['pct']}")
    logger.info(f"Hybrid Semantic Recall@50: {metrics_hybrid['semantic_recall']['recall_at_50']['pct']}")
    logger.info(f"Hybrid Semantic Recall@100: {metrics_hybrid['semantic_recall']['recall_at_100']['pct']}")

    # Select winning mode on PRODUCT_DEV_V2
    colbert_r50 = metrics_colbert['semantic_recall']['recall_at_50']['rate']
    hybrid_r50 = metrics_hybrid['semantic_recall']['recall_at_50']['rate']
    winning_mode = "hybrid" if hybrid_r50 >= colbert_r50 else "colbert"
    winning_metrics = metrics_hybrid if winning_mode == "hybrid" else metrics_colbert
    winning_per_item = per_item_hybrid if winning_mode == "hybrid" else per_item_colbert

    logger.info(f"\nWinning Exhaustive Mode: {winning_mode.upper()} (Recall@50: {winning_metrics['semantic_recall']['recall_at_50']['pct']})")

    # 3. Classify all misses at Recall@100
    miss_analysis = classify_misses(items, winning_per_item, retriever)
    logger.info(f"\n--- Miss Classification at Recall@100 ---")
    logger.info(f"CORPUS_COVERAGE_FAILURE: {miss_analysis['CORPUS_COVERAGE_FAILURE']}")
    logger.info(f"QREL_OR_QUERY_CONSTRUCTION_FAILURE: {miss_analysis['QREL_OR_QUERY_CONSTRUCTION_FAILURE']}")
    logger.info(f"MODEL_SEMANTIC_FAILURE: {miss_analysis['MODEL_SEMANTIC_FAILURE']}")

    summary = {
        "benchmark": "PRODUCT_DEV_V2",
        "benchmark_file": str(DEV_PATH.relative_to(_ROOT)),
        "n_queries": n,
        "retriever_model": retriever.model_id,
        "retriever_revision": retriever.revision,
        "total_corpus_passages_indexed": len(retriever.ordered_chunk_ids),
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "winning_mode": winning_mode,
        "mode_comparison": {
            "mode_a_colbert_alone": metrics_colbert,
            "mode_b_official_hybrid": metrics_hybrid,
        },
        "gates": {
            "ACQUISITION_GATE_RECALL_AT_20": {
                "target": 0.95,
                "actual": winning_metrics['semantic_recall']['recall_at_20']['rate'],
                "passed": winning_metrics['semantic_recall']['recall_at_20']['rate'] >= 0.95,
            },
            "ACQUISITION_GATE_RECALL_AT_50": {
                "target": 0.98,
                "actual": winning_metrics['semantic_recall']['recall_at_50']['rate'],
                "passed": winning_metrics['semantic_recall']['recall_at_50']['rate'] >= 0.98,
            },
        },
        "miss_classification": miss_analysis,
        "per_item_results": winning_per_item,
    }

    raw_json = json.dumps(summary, indent=2, ensure_ascii=False)
    REPORT_PATH.write_text(raw_json, encoding="utf-8")
    sha = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
    (REPORT_PATH.with_suffix(".json.sha256")).write_text(f"{sha}  {REPORT_PATH.name}\n", encoding="utf-8")

    logger.info(f"\nWrote full report to {REPORT_PATH.name} (SHA-256: {sha})")
    logger.info("================================================================")


if __name__ == "__main__":
    main()
