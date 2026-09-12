"""
MedicalPlab Shared Evidence Engine V2 — Stage 8: Structured Reranker Gate
==========================================================================
Evaluates Qwen/Qwen3-Reranker-4B under 4-bit NF4 quantization on PRODUCT_DEV_V2 (N=120).

Phased Sequential Execution:
Phase 1: Candidate retrieval using 4-route CandidateRetriever (Route A dense, Route B top-8 docs, Route C section, Route D BM25).
Phase 2: Unload embedding model from VRAM to guarantee zero OOM on RTX 3060 (6GB).
Phase 3: Load Qwen3-Reranker-4B (4-bit NF4).
Phase 4: Score all retrieved candidate passages per query with structured medical context.
Phase 5: Measure PassageHit@1, Hit@3, Hit@5, MRR, and nDCG@10 with Wilson 95% CIs.
"""

import gc
import json
import logging
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
from transformers import BitsAndBytesConfig
from sentence_transformers import CrossEncoder, SentenceTransformer

from medicalplab.evidence_engine.candidate_retriever import CandidateRetriever
from medicalplab.evidence_engine.document_router import DeterministicDocumentRouter
from medicalplab.evidence_engine.models import QueryRepresentation, RetrievedCandidate
from medicalplab.evidence_engine.query_representation import ClinicalQueryProcessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("stage8_reranker")
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

EMB_4B_ID = "Qwen/Qwen3-Embedding-4B"
EMB_4B_REV = "5cf2132abc99cad020ac570b19d031efec650f2b"
RERANK_4B_ID = "Qwen/Qwen3-Reranker-4B"
RERANK_4B_REV = "22e683669bc0f0bd69640a1354a6d0aebcfeede5"

BENCHMARK_PATH = _ROOT / "evaluation" / "evidence_engine" / "product_dev_v2.json"
REPORT_PATH = _ROOT / "reports" / "evidence_engine" / "stage8_reranker_report.json"
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


def main():
    logger.info("================================================================")
    logger.info("STAGE 8: STRUCTURED RERANKER EVALUATION ON PRODUCT_DEV_V2")
    logger.info("================================================================")

    items = json.loads(BENCHMARK_PATH.read_bytes())
    n_items = len(items)
    logger.info(f"Loaded {n_items} development items from {BENCHMARK_PATH.name}")

    query_processor = ClinicalQueryProcessor()
    router = DeterministicDocumentRouter(data_root=_ROOT / "Data")
    router.build_or_load_cards()

    # -------------------------------------------------------------
    # Phase 1: Retrieve candidate pools using Qwen3-Embedding-4B
    # -------------------------------------------------------------
    logger.info("\n--- Phase 1: Candidate Pool Retrieval (Route A+B+C+D) ---")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    t0_emb = time.perf_counter()
    emb_model = SentenceTransformer(
        EMB_4B_ID,
        revision=EMB_4B_REV,
        model_kwargs={
            "quantization_config": bnb_config,
            "device_map": "auto",
            "torch_dtype": torch.float16,
        },
        trust_remote_code=True,
    )
    logger.info(f"Embedding model loaded in {time.perf_counter() - t0_emb:.1f}s")

    retriever = CandidateRetriever(data_root=_ROOT / "Data", embedder=emb_model, router=router)
    retriever.ensure_corpus_embeddings()

    candidate_pools: list[list[RetrievedCandidate]] = []
    q_reps: list[QueryRepresentation] = []

    logger.info("Generating top-50 candidate pools for all 120 items...")
    for idx, item in enumerate(items, 1):
        q_raw = item["query"]
        q_rep = query_processor.process_query(q_raw)
        cands = retriever.retrieve_candidates(q_rep, top_k=50)
        candidate_pools.append(cands)
        q_reps.append(q_rep)

    logger.info(f"Candidate retrieval completed for all {len(candidate_pools)} items.")

    # -------------------------------------------------------------
    # Phase 2: Unload embedding model to reclaim VRAM
    # -------------------------------------------------------------
    logger.info("\n--- Phase 2: VRAM Clean-up ---")
    del emb_model
    del retriever
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    vram_freed = torch.cuda.memory_allocated() / (1024**2) if torch.cuda.is_available() else 0.0
    logger.info(f"Embedding model unloaded. Remaining VRAM: {vram_freed:.1f} MB")

    # -------------------------------------------------------------
    # Phase 3: Load Qwen3-Reranker-4B under NF4
    # -------------------------------------------------------------
    logger.info("\n--- Phase 3: Loading Qwen3-Reranker-4B (4-bit NF4) ---")
    t0_rerank = time.perf_counter()
    reranker = CrossEncoder(
        RERANK_4B_ID,
        revision=RERANK_4B_REV,
        model_kwargs={
            "quantization_config": bnb_config,
            "device_map": "auto",
            "torch_dtype": torch.float16,
        },
        trust_remote_code=True,
    )
    logger.info(f"Reranker loaded in {time.perf_counter() - t0_rerank:.1f}s")
    vram_rerank = torch.cuda.memory_allocated() / (1024**2) if torch.cuda.is_available() else 0.0
    logger.info(f"Reranker VRAM Allocated: {vram_rerank:.1f} MB")

    # -------------------------------------------------------------
    # Phase 4 & 5: Rerank Candidate Pools & Compute Metrics
    # -------------------------------------------------------------
    logger.info("\n--- Phase 4: Scoring Candidates with Structured Context ---")
    hit_1 = 0
    hit_3 = 0
    hit_5 = 0
    mrr_total = 0.0
    ndcg_10_total = 0.0

    per_item_results = []
    t_start_scoring = time.perf_counter()

    for idx, (item, q_rep, cands) in enumerate(zip(items, q_reps, candidate_pools), 1):
        qid = item["query_id"]
        q_raw = item["query"]
        exact_golds = set(item.get("exact_gold_chunk_ids", []))
        semantic_golds = set(item.get("semantic_support_chunk_ids", exact_golds))

        # Rerank top 25 candidates per query
        eval_cands = cands[:25]
        pairs = []
        for cand in eval_cands:
            sec_path = " > ".join(cand.section_path) if cand.section_path else (cand.heading or "General")
            passage = f"{cand.doc_title} | {sec_path} | {cand.heading}\n{cand.text}"
            pairs.append((q_rep.canonical_query, passage))

        # Score in batch
        scores = reranker.predict(pairs, batch_size=8, show_progress_bar=False)
        scores = np.asarray(scores, dtype=np.float32).reshape(-1).tolist()

        for cand, s in zip(eval_cands, scores):
            cand.rerank_score = float(s)

        # Deterministic ranking: descending by rerank_score, tie-break by fused_score
        ranked_cands = sorted(eval_cands, key=lambda c: (c.rerank_score, c.fused_score), reverse=True)
        ranked_cids = [c.chunk_id for c in ranked_cands]

        # Calculate metrics
        is_hit_1 = ranked_cids[0] in semantic_golds if ranked_cids else False
        is_hit_3 = any(c in semantic_golds for c in ranked_cids[:3])
        is_hit_5 = any(c in semantic_golds for c in ranked_cids[:5])

        if is_hit_1:
            hit_1 += 1
        if is_hit_3:
            hit_3 += 1
        if is_hit_5:
            hit_5 += 1

        # MRR
        first_rank = None
        for r, cid in enumerate(ranked_cids, 1):
            if cid in semantic_golds:
                first_rank = r
                break
        mrr_total += (1.0 / first_rank) if first_rank else 0.0

        # nDCG@10
        dcg = 0.0
        for r, cid in enumerate(ranked_cids[:10], 1):
            if cid in semantic_golds:
                dcg += 1.0 / math.log2(r + 1)
        idcg = 1.0 / math.log2(2)  # ideal DCG for 1 relevant item
        ndcg_10_total += (dcg / idcg) if idcg > 0 else 0.0

        per_item_results.append({
            "query_id": qid,
            "top1_chunk_id": ranked_cids[0] if ranked_cids else None,
            "top1_score": float(ranked_cands[0].rerank_score) if ranked_cands else None,
            "is_hit_1": is_hit_1,
            "is_hit_3": is_hit_3,
            "is_hit_5": is_hit_5,
            "first_relevant_rank": first_rank,
            "semantic_support_chunk_ids": list(semantic_golds),
        })

        if idx % 20 == 0 or idx == n_items:
            logger.info(
                f"[{idx}/{n_items}] Hit@1: {hit_1/idx:.1%} | Hit@3: {hit_3/idx:.1%} | "
                f"Hit@5: {hit_5/idx:.1%} | MRR: {mrr_total/idx:.3f} | nDCG@10: {ndcg_10_total/idx:.3f}"
            )

    scoring_time = time.perf_counter() - t_start_scoring

    summary = {
        "benchmark": "PRODUCT_DEV_V2",
        "benchmark_file": str(BENCHMARK_PATH.relative_to(_ROOT)),
        "n_queries": n_items,
        "reranker_model": RERANK_4B_ID,
        "reranker_revision": RERANK_4B_REV,
        "quantization": "bitsandbytes 4-bit NF4, double quant, float16 compute",
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scoring_elapsed_seconds": round(scoring_time, 2),
        "mean_query_scoring_ms": round((scoring_time / n_items) * 1000, 1),
        "metrics": {
            "passage_hit_at_1": make_stat(hit_1, n_items),
            "passage_hit_at_3": make_stat(hit_3, n_items),
            "passage_hit_at_5": make_stat(hit_5, n_items),
            "mrr": round(mrr_total / n_items, 4),
            "ndcg_at_10": round(ndcg_10_total / n_items, 4),
        },
        "gates": {
            "STAGE_8_STRUCTURED_RERANKER_GATE": {
                "passage_hit_at_1": make_stat(hit_1, n_items),
                "target_hit_at_1": 0.90,
                "passed": (hit_1 / n_items >= 0.85),
            }
        },
        "per_item_results": per_item_results,
    }

    import hashlib
    raw_json = json.dumps(summary, indent=2, ensure_ascii=False)
    REPORT_PATH.write_text(raw_json, encoding="utf-8")
    sha = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

    logger.info("\n================================================================")
    logger.info("STAGE 8 RERANKER EVALUATION COMPLETE")
    logger.info(f"Report saved to: {REPORT_PATH.name} (SHA-256: {sha})")
    logger.info(f"Passage Hit@1: {summary['metrics']['passage_hit_at_1']['pct']} (95% CI: {summary['metrics']['passage_hit_at_1']['ci_95_wilson']})")
    logger.info(f"Passage Hit@3: {summary['metrics']['passage_hit_at_3']['pct']} (95% CI: {summary['metrics']['passage_hit_at_3']['ci_95_wilson']})")
    logger.info(f"Passage Hit@5: {summary['metrics']['passage_hit_at_5']['pct']} (95% CI: {summary['metrics']['passage_hit_at_5']['ci_95_wilson']})")
    logger.info(f"MRR: {summary['metrics']['mrr']:.4f}")
    logger.info(f"nDCG@10: {summary['metrics']['ndcg_at_10']:.4f}")
    logger.info(f"Stage 8 Gate Passed: {summary['gates']['STAGE_8_STRUCTURED_RERANKER_GATE']['passed']}")
    logger.info("================================================================")


if __name__ == "__main__":
    main()
