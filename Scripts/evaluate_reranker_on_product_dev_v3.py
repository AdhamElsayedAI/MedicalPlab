"""
Evaluate Qwen3-Reranker-4B on PRODUCT_DEV_V3 Candidates with Structured Medical Prompt
=====================================================================================
Evaluates Qwen/Qwen3-Reranker-4B (NF4 quantized, revision 22e683669bc0f0bd69640a1354a6d0aebcfeede5).
Takes candidates from the clean BGE-M3 exhaustive baseline (top 50 per query).
Reranks using the verified structured medical relevance prompt:
- Instruction: Medical evidence relevance instruction
- Original Question
- Retrieval Target
- Document Title
- Section Path
- Heading
- Evidence Passage

Computes:
- Semantic Hit@1, Hit@3, Hit@5, Hit@10
- Exact Hit@1, Hit@3, Hit@5
- MRR, nDCG@10
- Rank Movement: improved, unchanged, degraded among eligible positives
- Latency (p50, p95)
"""

import gc
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
from sentence_transformers import CrossEncoder
from transformers import BitsAndBytesConfig

from medicalplab.evidence_engine.bge_m3_retriever import BGEM3ExhaustiveRetriever
from medicalplab.evidence_engine.query_representation import ClinicalQueryProcessor

DEV3_PATH = _ROOT / "evaluation" / "evidence_engine" / "product_dev_v3.json"
REPORT_PATH = _ROOT / "reports" / "evidence_engine" / "product_dev_v3_reranker_report.json"
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

RERANK_4B_ID = "Qwen/Qwen3-Reranker-4B"
RERANK_4B_REV = "22e683669bc0f0bd69640a1354a6d0aebcfeede5"

MEDICAL_INSTRUCTION = (
    "Rank this evidence according to whether it directly supports the exact medical "
    "information requested. Topic similarity alone is insufficient. Penalize "
    "evidence about the same disease when it addresses a different claim, "
    "investigation, treatment goal, population, or numeric threshold."
)

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

def format_evidence_text(cand: Any) -> str:
    doc_title = cand.doc_title or cand.document_id
    sec_str = " > ".join(cand.section_path) if cand.section_path else (cand.heading or "General")
    heading_str = cand.heading or "Clinical Evidence"
    return (
        f"Document:\n{doc_title}\n\n"
        f"Section:\n{sec_str}\n\n"
        f"Heading:\n{heading_str}\n\n"
        f"Evidence:\n{cand.text.strip()}"
    )

def format_query_prompt(orig_q: str, target: str) -> str:
    return (
        f"Instruction:\n{MEDICAL_INSTRUCTION}\n\n"
        f"Original Question:\n{orig_q}\n\n"
        f"Retrieval Target:\n{target}"
    )

def main():
    print("=" * 70)
    print("CORRECTED QWEN3-RERANKER-4B ON PRODUCT_DEV_V3")
    print("=" * 70)

    items = json.loads(DEV3_PATH.read_bytes())
    n = len(items)
    print(f"Loaded {n} items from {DEV3_PATH.name}")

    query_processor = ClinicalQueryProcessor()
    query_reps = [query_processor.process_query(it["query"]) for it in items]

    # Phase 1: Retrieve top-50 candidates using precomputed BGE-M3 representations
    print("\n--- Phase 1: Acquiring Top-50 BGE-M3 Candidates ---")
    t0_bge = time.perf_counter()
    retriever = BGEM3ExhaustiveRetriever(data_root=_ROOT / "Data")
    retriever.ensure_corpus_representations()

    candidate_pools = []
    for idx, q_rep in enumerate(query_reps, 1):
        cands = retriever.retrieve_exhaustive(q_rep, top_k=50, mode="hybrid")
        candidate_pools.append(cands)

    print(f"BGE-M3 candidate acquisition completed in {time.perf_counter() - t0_bge:.1f}s.")

    # Phase 2: Unload BGE-M3 completely to guarantee 0 OOM
    print("\n--- Phase 2: Freeing BGE-M3 VRAM ---")
    del retriever
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("VRAM flushed.")

    # Phase 3: Load Qwen3-Reranker-4B under 4-bit NF4
    print("\n--- Phase 3: Loading Qwen3-Reranker-4B (4-bit NF4) ---")
    t0_load = time.perf_counter()
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    reranker = CrossEncoder(
        RERANK_4B_ID,
        revision=RERANK_4B_REV,
        model_kwargs={"quantization_config": bnb_config, "device_map": "auto"},
        trust_remote_code=True,
        max_length=1024,
    )
    print(f"Loaded Qwen3-Reranker-4B in {time.perf_counter() - t0_load:.1f}s")
    vram_mb = torch.cuda.memory_allocated() / (1024**2) if torch.cuda.is_available() else 0.0
    print(f"VRAM Allocated: {vram_mb:.1f} MB")

    # Phase 4: Rerank candidates
    print("\n--- Phase 4: Scoring Candidates with Medical Relevance Prompt ---")
    hit_sem = {1: 0, 3: 0, 5: 0, 10: 0}
    hit_exact = {1: 0, 3: 0, 5: 0, 10: 0}
    mrr_sum = 0.0
    ndcg_sum = 0.0

    movement_improved = 0
    movement_unchanged = 0
    movement_degraded = 0
    not_in_candidates = 0

    query_latencies = []
    per_item_results = []

    t_rerank_start = time.perf_counter()
    for idx, (item, q_rep, cands) in enumerate(zip(items, query_reps, candidate_pools), 1):
        t_q0 = time.perf_counter()
        qid = item["query_id"]
        exact_golds = set(item.get("exact_gold_chunk_ids", []))
        sem_golds = set(item.get("semantic_support_chunk_ids", exact_golds))

        # Initial rank before reranking
        initial_cids = [c.chunk_id for c in cands]
        r_pre_sem = next((r for r, cid in enumerate(initial_cids, 1) if cid in sem_golds), None)
        r_pre_exact = next((r for r, cid in enumerate(initial_cids, 1) if cid in exact_golds), None)

        # Build pair inputs for reranker
        target_str = q_rep.neutral_target or q_rep.canonical_query or q_rep.original_query
        formatted_query = format_query_prompt(q_rep.original_query, target_str)
        pairs = [(formatted_query, format_evidence_text(c)) for c in cands]

        # Score with Qwen3-Reranker-4B
        scores = reranker.predict(pairs, batch_size=16, show_progress_bar=False)

        # Sort candidates by reranker score descending
        rerank_order = np.argsort(scores)[::-1]
        reranked_cids = [cands[i].chunk_id for i in rerank_order]
        reranked_scores = [float(scores[i]) for i in rerank_order]

        r_post_sem = next((r for r, cid in enumerate(reranked_cids, 1) if cid in sem_golds), None)
        r_post_exact = next((r for r, cid in enumerate(reranked_cids, 1) if cid in exact_golds), None)

        if r_post_sem is not None:
            mrr_sum += 1.0 / r_post_sem
            for k in [1, 3, 5, 10]:
                if r_post_sem <= k:
                    hit_sem[k] += 1
        if r_post_exact is not None:
            for k in [1, 3, 5, 10]:
                if r_post_exact <= k:
                    hit_exact[k] += 1

        ndcg_sum += compute_ndcg(reranked_cids, sem_golds, k=10)

        # Movement classification
        if r_pre_sem is None:
            not_in_candidates += 1
            movement_type = "NOT_IN_CANDIDATES"
        elif r_post_sem < r_pre_sem:
            movement_improved += 1
            movement_type = "IMPROVED"
        elif r_post_sem == r_pre_sem:
            movement_unchanged += 1
            movement_type = "UNCHANGED"
        else:
            movement_degraded += 1
            movement_type = "DEGRADED"

        q_elapsed = (time.perf_counter() - t_q0) * 1000
        query_latencies.append(q_elapsed)

        per_item_results.append({
            "query_id": qid,
            "query": item["query"],
            "pre_rank_sem": r_pre_sem,
            "post_rank_sem": r_post_sem,
            "movement": movement_type,
            "top1_cid": reranked_cids[0] if reranked_cids else None,
            "top1_score": round(reranked_scores[0], 4) if reranked_scores else None,
            "latency_ms": round(q_elapsed, 1),
        })

        if idx % 20 == 0 or idx == n:
            print(f"Reranked {idx}/{n} queries (mean latency: {np.mean(query_latencies):.1f}ms)...")

    rerank_total_time = time.perf_counter() - t_rerank_start
    eligible_positives = movement_improved + movement_unchanged + movement_degraded
    degraded_rate = movement_degraded / eligible_positives if eligible_positives > 0 else 0.0

    report = {
        "benchmark": "PRODUCT_DEV_V3",
        "benchmark_file": str(DEV3_PATH.relative_to(_ROOT)),
        "n_queries": n,
        "reranker_model": RERANK_4B_ID,
        "reranker_revision": RERANK_4B_REV,
        "rerank_depth": 50,
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_elapsed_seconds": round(rerank_total_time, 2),
        "mean_query_latency_ms": round(float(np.mean(query_latencies)), 1),
        "p50_latency_ms": round(float(np.percentile(query_latencies, 50)), 1),
        "p95_latency_ms": round(float(np.percentile(query_latencies, 95)), 1),
        "metrics": {
            "semantic_hit": {f"hit_at_{k}": make_stat(hit_sem[k], n) for k in [1, 3, 5, 10]},
            "exact_hit": {f"hit_at_{k}": make_stat(hit_exact[k], n) for k in [1, 3, 5, 10]},
            "mrr": round(mrr_sum / n, 4),
            "ndcg_at_10": round(ndcg_sum / n, 4),
        },
        "movement_analysis": {
            "eligible_positives": eligible_positives,
            "improved": movement_improved,
            "unchanged": movement_unchanged,
            "degraded": movement_degraded,
            "not_in_candidates": not_in_candidates,
            "degraded_eligible_rate": round(degraded_rate, 4),
            "degraded_eligible_pct": f"{degraded_rate * 100:.2f}%",
            "degraded_gate_passed": degraded_rate < 0.10,
        },
        "per_item_results": per_item_results
    }

    import hashlib
    out_bytes = json.dumps(report, indent=2).encode("utf-8")
    REPORT_PATH.write_bytes(out_bytes)
    sha = hashlib.sha256(out_bytes).hexdigest()
    (REPORT_PATH.with_suffix(".json.sha256")).write_text(f"{sha}  {REPORT_PATH.name}\n", encoding="utf-8")

    print("\n" + "=" * 70)
    print("RESULTS: QWEN3-RERANKER-4B ON CLEAN PRODUCT_DEV_V3")
    print("=" * 70)
    print(f"Semantic Hit@1 : {report['metrics']['semantic_hit']['hit_at_1']['pct']}")
    print(f"Semantic Hit@3 : {report['metrics']['semantic_hit']['hit_at_3']['pct']}")
    print(f"Semantic Hit@5 : {report['metrics']['semantic_hit']['hit_at_5']['pct']}")
    print(f"Semantic Hit@10: {report['metrics']['semantic_hit']['hit_at_10']['pct']}")
    print(f"Exact Hit@1    : {report['metrics']['exact_hit']['hit_at_1']['pct']}")
    print(f"Exact Hit@5    : {report['metrics']['exact_hit']['hit_at_5']['pct']}")
    print(f"MRR            : {report['metrics']['mrr']:.4f}")
    print(f"nDCG@10        : {report['metrics']['ndcg_at_10']:.4f}")
    print(f"Movement       : {movement_improved} improved, {movement_unchanged} unchanged, {movement_degraded} degraded (out of {eligible_positives} eligible)")
    print(f"Degraded Rate  : {report['movement_analysis']['degraded_eligible_pct']}")
    print(f"\nSaved report to {REPORT_PATH.name} (SHA-256: {sha})")

if __name__ == "__main__":
    main()
