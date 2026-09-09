"""Comprehensive Full-Corpus Retrieval Benchmark Suite (817 Chunks, 13 Documents).

Evaluates 6 configurations against the complete frozen production candidate corpus:
- Corpus: Data/metadata/corpus_cardiorespiratory_snapshot_v1.json (13 documents, 817 chunks)
- Eval Set: evaluation/retrieval_eval_multisource_heldout_v1.json (24 cases: 20 answerable, 4 unsupported)

Configurations:
1. BM25 only
2. Qwen3 Dense only (Qwen/Qwen3-Embedding-0.6B)
3. BM25 + Dense blend (alpha=0.6)
4. BM25 + Dense weighted RRF (k=60, weights 2:1)
5. Best Hybrid + Heuristic MedicalReranker
6. Best Hybrid + Neural Cross-Encoder (cross-encoder/ms-marco-MiniLM-L-6-v2)

Tracks TRUE end-to-end latency (mean, p50, p95) and all retrieval quality metrics.
"""

import json
import math
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sentence_transformers import CrossEncoder, SentenceTransformer

from medicalplab.stage_b.evidence_policy import normalize
from medicalplab.stage_r.models import EvidenceCandidate, ScoreBreakdown
from medicalplab.stage_r.query_expansion import expand_query
from medicalplab.stage_r.reranker import MedicalReranker

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = PROJECT_ROOT / "Data" / "metadata" / "corpus_cardiorespiratory_snapshot_v1.json"
EVAL_PATH = PROJECT_ROOT / "evaluation" / "retrieval_eval_multisource_heldout_v1.json"
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"

DENSE_MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
CROSS_ENCODER_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

QUERY_INSTRUCTION = (
    "Instruct: Given a medical education query, retrieve the passages "
    "from the available medical sources that most directly support the "
    "requested claim. Respect any source explicitly requested by the "
    "query. Do not assume every query targets a guideline.\nQuery:"
)


def block_key(chunk: dict[str, Any]) -> str:
    return f"{chunk['document_id']}:B{int(chunk['source_block_index']):04d}"


def doc_id_from_key(key: str) -> str:
    return key.split(":B", 1)[0]


def tokenize(text: str) -> list[str]:
    return [w for w in normalize(text).split() if len(w) >= 2]


class BM25Index:
    def __init__(self, chunks: list[dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.doc_tokens = [tokenize(f"{c.get('heading', '')} {c.get('section', '')} {c.get('text', '')}") for c in chunks]
        self.doc_lens = [len(t) for t in self.doc_tokens]
        self.avgdl = sum(self.doc_lens) / max(1, len(chunks))
        self.df = Counter()
        for t_set in (set(t) for t in self.doc_tokens):
            for term in t_set:
                self.df[term] += 1
        self.n_docs = len(chunks)

    def score_query(self, query_text: str) -> np.ndarray:
        q_tokens = tokenize(query_text)
        scores = np.zeros(self.n_docs, dtype=float)
        for t in q_tokens:
            df = self.df.get(t, 0)
            if df == 0:
                continue
            idf = math.log(1.0 + (self.n_docs - df + 0.5) / (df + 0.5))
            for i, tokens in enumerate(self.doc_tokens):
                tf = tokens.count(t)
                if tf > 0:
                    num = tf * (self.k1 + 1.0)
                    den = tf + self.k1 * (1.0 - self.b + self.b * (self.doc_lens[i] / self.avgdl))
                    scores[i] += idf * (num / den)
        return scores


def format_chunk_text(chunk: dict[str, Any]) -> str:
    parts = []
    if chunk.get("heading"):
        parts.append(f"Heading: {chunk['heading']}")
    if chunk.get("section"):
        parts.append(f"Section: {chunk['section']}")
    parts.append(f"Content: {chunk.get('text', '')}")
    return "\n".join(parts)


def compute_metrics(
    ranked_blocks: list[str],
    relevant_blocks: set[str],
    relevance_map: dict[str, int],
    preferred_doc: str | None,
) -> dict[str, Any]:
    hit1 = 1.0 if any(b in relevant_blocks for b in ranked_blocks[:1]) else 0.0
    hit3 = 1.0 if any(b in relevant_blocks for b in ranked_blocks[:3]) else 0.0
    hit5 = 1.0 if any(b in relevant_blocks for b in ranked_blocks[:5]) else 0.0

    n_rel = len(relevant_blocks)
    if n_rel > 0:
        rec1 = len(set(ranked_blocks[:1]) & relevant_blocks) / n_rel
        rec3 = len(set(ranked_blocks[:3]) & relevant_blocks) / n_rel
        rec5 = len(set(ranked_blocks[:5]) & relevant_blocks) / n_rel
        rec10 = len(set(ranked_blocks[:10]) & relevant_blocks) / n_rel
    else:
        rec1 = rec3 = rec5 = rec10 = 0.0

    mrr = 0.0
    for rank, b in enumerate(ranked_blocks, start=1):
        if b in relevant_blocks:
            mrr = 1.0 / rank
            break

    dcg = 0.0
    for rank, b in enumerate(ranked_blocks[:10], start=1):
        rel = relevance_map.get(b, 0)
        if rel > 0:
            dcg += ((2 ** rel) - 1) / math.log2(rank + 1)
    
    ideal_relevances = sorted(relevance_map.values(), reverse=True)
    idcg = 0.0
    for rank, rel in enumerate(ideal_relevances[:10], start=1):
        idcg += ((2 ** rel) - 1) / math.log2(rank + 1)
    ndcg = (dcg / idcg) if idcg > 0 else 0.0

    auth_hit = None
    if preferred_doc:
        auth_hit = 1.0 if any(b in relevant_blocks and doc_id_from_key(b) == preferred_doc for b in ranked_blocks[:3]) else 0.0

    return {
        "hit@1": hit1,
        "hit@3": hit3,
        "hit@5": hit5,
        "recall@1": rec1,
        "recall@3": rec3,
        "recall@5": rec5,
        "recall@10": rec10,
        "mrr": mrr,
        "ndcg@10": ndcg,
        "auth_hit": auth_hit,
    }


def aggregate_stats(
    metrics_list: list[dict[str, Any]],
    latencies_sec: list[float],
    fusion_latencies_sec: list[float] | None = None,
) -> dict[str, Any]:
    keys = ["hit@1", "hit@3", "hit@5", "recall@1", "recall@3", "recall@5", "recall@10", "mrr", "ndcg@10"]
    agg = {}
    for k in keys:
        vals = [m[k] for m in metrics_list if k in m]
        agg[k] = round(sum(vals) / len(vals), 4) if vals else 0.0
    
    auth_vals = [m["auth_hit"] for m in metrics_list if m.get("auth_hit") is not None]
    agg["authority_accuracy"] = round(sum(auth_vals) / len(auth_vals), 4) if auth_vals else 1.0

    lat_ms = np.array(latencies_sec) * 1000
    agg["latency_mean_ms"] = round(float(np.mean(lat_ms)), 2)
    agg["latency_p50_ms"] = round(float(np.percentile(lat_ms, 50)), 2)
    agg["latency_p95_ms"] = round(float(np.percentile(lat_ms, 95)), 2)

    if fusion_latencies_sec and len(fusion_latencies_sec) > 0:
        f_ms = np.array(fusion_latencies_sec) * 1000
        agg["fusion_mean_ms"] = round(float(np.mean(f_ms)), 2)
        agg["fusion_p50_ms"] = round(float(np.percentile(f_ms, 50)), 2)
        agg["fusion_p95_ms"] = round(float(np.percentile(f_ms, 95)), 2)
    return agg


def main():
    # 1. Load complete snapshot
    snapshot = json.load(open(SNAPSHOT_PATH, encoding="utf-8"))
    corpus_version = snapshot["version"]
    doc_count = snapshot["document_count"]
    total_chunk_count = snapshot["total_chunks"]

    chunks = []
    for d in snapshot["documents"]:
        c_path = PROJECT_ROOT / d["chunks_file"]
        c_data = json.load(open(c_path, encoding="utf-8"))
        c_list = c_data.get("chunks", []) if isinstance(c_data, dict) else c_data
        chunks.extend(c_list)

    print("=========================================================================================")
    print("FULL CORPUS RETRIEVAL BENCHMARK SUITE (817 CHUNKS)")
    print(f"Corpus: {snapshot['corpus_id']} v{corpus_version}")
    print(f"Verified Documents: {doc_count} | Total Chunks: {len(chunks)} (expected {total_chunk_count})")
    print("=========================================================================================")

    # 2. Load Evaluation Set
    eval_data = json.load(open(EVAL_PATH, encoding="utf-8"))
    total_cases = len(eval_data["cases"])
    answerable_cases = [c for c in eval_data["cases"] if c.get("expected_answerable", True)]
    unsupported_cases = [c for c in eval_data["cases"] if not c.get("expected_answerable", True)]
    print(f"Eval Set: {eval_data.get('eval_set_id')} v{eval_data.get('version')}")
    print(f"Total Cases: {total_cases} | Answerable: {len(answerable_cases)} | Unsupported: {len(unsupported_cases)}")

    # 3. Index BM25 over ALL 817 chunks
    t0 = time.perf_counter()
    bm25 = BM25Index(chunks)
    bm25_build_time = time.perf_counter() - t0
    print(f"Built BM25 index over {len(chunks)} chunks in {bm25_build_time:.2f}s")

    # 4. Load Models
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading dense model {DENSE_MODEL_NAME} on {device}...")
    t0 = time.perf_counter()
    dense_model = SentenceTransformer(DENSE_MODEL_NAME, device=device)
    dense_load_time = time.perf_counter() - t0

    # 5. Encode ALL 817 chunks (or load cached)
    emb_cache_path = PROJECT_ROOT / "Data" / "metadata" / "corpus_817_qwen3_embeddings.npy"
    if emb_cache_path.exists():
        print(f"Loading cached embeddings from {emb_cache_path}...")
        corpus_embs = np.load(emb_cache_path)
        corpus_encode_time = 0.0
        print(f"Loaded {corpus_embs.shape[0]} embeddings from cache.")
    else:
        print(f"Encoding all {len(chunks)} chunks on {device}...")
        t0 = time.perf_counter()
        corpus_texts = [format_chunk_text(c) for c in chunks]
        corpus_embs = dense_model.encode(corpus_texts, batch_size=32, normalize_embeddings=True, show_progress_bar=True)
        corpus_encode_time = time.perf_counter() - t0
        print(f"Encoded {len(chunks)} chunks in {corpus_encode_time:.2f}s")
        np.save(emb_cache_path, corpus_embs)
        print(f"Saved embedding cache to {emb_cache_path}")

    # 6. Load Rerankers
    print(f"Loading cross-encoder {CROSS_ENCODER_NAME} on {device}...")
    cross_encoder = CrossEncoder(CROSS_ENCODER_NAME, device=device)
    heuristic_reranker = MedicalReranker()

    chunk_keys = [block_key(c) for c in chunks]
    block_lookup = {block_key(c): c for c in chunks}

    # Tracking
    configs = [
        "bm25_only",
        "dense_only",
        "bm25_dense_blend",
        "hybrid_weighted_rrf",
        "hybrid_heuristic_reranker",
        "hybrid_neural_reranker",
    ]
    results_by_config = {c: [] for c in configs}
    e2e_latencies = {c: [] for c in configs}
    fusion_latencies = {c: [] for c in configs}

    print("\nExecuting evaluation across all 20 answerable queries with true end-to-end latency profiling...")

    for case in answerable_cases:
        query_text = case["query"]
        rel_blocks = {f"{r['document_id']}:B{int(r['block_index']):04d}" for r in case.get("relevant_blocks", [])}
        rel_map = {f"{r['document_id']}:B{int(r['block_index']):04d}": int(r.get("relevance", 3)) for r in case.get("relevant_blocks", [])}
        pref_doc = case.get("preferred_document_id")

        # -------------------------------------------------------------
        # 1. BM25 Only (True End-to-End)
        # -------------------------------------------------------------
        t_start = time.perf_counter()
        bm25_scores = bm25.score_query(query_text)
        max_b = np.max(bm25_scores) if np.max(bm25_scores) > 0 else 1.0
        norm_b = bm25_scores / max_b

        bm25_best = defaultdict(lambda: float("-inf"))
        for k, s in zip(chunk_keys, norm_b):
            if s > bm25_best[k]:
                bm25_best[k] = float(s)
        ranked_bm25 = sorted(bm25_best.keys(), key=lambda k: bm25_best[k], reverse=True)
        e2e_latencies["bm25_only"].append(time.perf_counter() - t_start)
        results_by_config["bm25_only"].append(compute_metrics(ranked_bm25, rel_blocks, rel_map, pref_doc))

        # -------------------------------------------------------------
        # 2. Dense Only (True End-to-End)
        # -------------------------------------------------------------
        t_start = time.perf_counter()
        formatted_q = f"{QUERY_INSTRUCTION}\n{query_text.strip()}"
        q_emb = dense_model.encode([formatted_q], normalize_embeddings=True, show_progress_bar=False)[0]
        dense_sims = np.dot(corpus_embs, q_emb)

        dense_best = defaultdict(lambda: float("-inf"))
        for k, s in zip(chunk_keys, dense_sims):
            if s > dense_best[k]:
                dense_best[k] = float(s)
        ranked_dense = sorted(dense_best.keys(), key=lambda k: dense_best[k], reverse=True)
        dense_e2e_time = time.perf_counter() - t_start
        e2e_latencies["dense_only"].append(dense_e2e_time)
        results_by_config["dense_only"].append(compute_metrics(ranked_dense, rel_blocks, rel_map, pref_doc))

        # -------------------------------------------------------------
        # 3. BM25 + Dense Blend (alpha=0.6) (True End-to-End)
        # -------------------------------------------------------------
        t_start = time.perf_counter()
        # End-to-end includes query BM25 + query Dense + score combination
        t_fusion_start = time.perf_counter()
        blend_scores = {}
        all_keys = set(bm25_best.keys()) | set(dense_best.keys())
        for k in all_keys:
            d_s = max(0.0, dense_best.get(k, 0.0))
            b_s = max(0.0, bm25_best.get(k, 0.0))
            blend_scores[k] = 0.6 * d_s + 0.4 * b_s
        ranked_blend = sorted(blend_scores.keys(), key=lambda k: blend_scores[k], reverse=True)
        t_fusion_elapsed = time.perf_counter() - t_fusion_start
        # Total e2e time = bm25 time + dense time + fusion overhead
        blend_e2e = (e2e_latencies["bm25_only"][-1] + e2e_latencies["dense_only"][-1] + t_fusion_elapsed)
        e2e_latencies["bm25_dense_blend"].append(blend_e2e)
        fusion_latencies["bm25_dense_blend"].append(t_fusion_elapsed)
        results_by_config["bm25_dense_blend"].append(compute_metrics(ranked_blend, rel_blocks, rel_map, pref_doc))

        # -------------------------------------------------------------
        # 4. Hybrid Weighted RRF (True End-to-End)
        # -------------------------------------------------------------
        t_fusion_start = time.perf_counter()
        rrf_k = 60
        rrf_scores = defaultdict(float)
        for rank, k in enumerate(ranked_dense[:30], start=1):
            rrf_scores[k] += 2.0 / (rrf_k + rank)
        for rank, k in enumerate(ranked_bm25[:30], start=1):
            rrf_scores[k] += 1.0 / (rrf_k + rank)
        ranked_rrf = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)
        t_fusion_elapsed = time.perf_counter() - t_fusion_start
        rrf_e2e = (e2e_latencies["bm25_only"][-1] + e2e_latencies["dense_only"][-1] + t_fusion_elapsed)
        e2e_latencies["hybrid_weighted_rrf"].append(rrf_e2e)
        fusion_latencies["hybrid_weighted_rrf"].append(t_fusion_elapsed)
        results_by_config["hybrid_weighted_rrf"].append(compute_metrics(ranked_rrf, rel_blocks, rel_map, pref_doc))

        # Top 15 candidates for reranking
        top_candidates = ranked_rrf[:15]

        # -------------------------------------------------------------
        # 5. Hybrid + Heuristic MedicalReranker (True End-to-End)
        # -------------------------------------------------------------
        t_rerank_start = time.perf_counter()
        retrieval_query = expand_query(query_text)
        candidates_obj = []
        for k in top_candidates:
            c_data = block_lookup[k]
            score = rrf_scores[k]
            bd = ScoreBreakdown(
                dense_score=dense_best.get(k, 0.0),
                sparse_score=bm25_best.get(k, 0.0),
                alpha=0.6,
                hybrid_score=score,
                rerank_score=0.0,
                final_score=score,
            )
            cand = EvidenceCandidate(
                ref=k,
                document_id=c_data["document_id"],
                source=c_data.get("block_type", "guideline"),
                heading=c_data.get("heading", ""),
                section=c_data.get("section", ""),
                text=c_data.get("text", ""),
                score=score,
                score_breakdown=bd,
            )
            candidates_obj.append(cand)
        
        reranked_heuristic = heuristic_reranker.rerank(query=retrieval_query, candidates=candidates_obj, top_k=10)
        ranked_h = [r.ref for r in reranked_heuristic]
        for k in ranked_rrf:
            if k not in ranked_h:
                ranked_h.append(k)
        t_rerank_elapsed = time.perf_counter() - t_rerank_start
        heuristic_e2e = rrf_e2e + t_rerank_elapsed
        e2e_latencies["hybrid_heuristic_reranker"].append(heuristic_e2e)
        fusion_latencies["hybrid_heuristic_reranker"].append(t_rerank_elapsed)
        results_by_config["hybrid_heuristic_reranker"].append(compute_metrics(ranked_h, rel_blocks, rel_map, pref_doc))

        # -------------------------------------------------------------
        # 6. Hybrid + Neural Cross-Encoder (True End-to-End)
        # -------------------------------------------------------------
        t_ce_start = time.perf_counter()
        pairs = [(query_text, format_chunk_text(block_lookup[k])) for k in top_candidates]
        ce_scores = cross_encoder.predict(pairs)
        ranked_pairs = sorted(zip(top_candidates, ce_scores), key=lambda x: x[1], reverse=True)
        ranked_ce = [k for k, _ in ranked_pairs]
        for k in ranked_rrf:
            if k not in ranked_ce:
                ranked_ce.append(k)
        t_ce_elapsed = time.perf_counter() - t_ce_start
        ce_e2e = rrf_e2e + t_ce_elapsed
        e2e_latencies["hybrid_neural_reranker"].append(ce_e2e)
        fusion_latencies["hybrid_neural_reranker"].append(t_ce_elapsed)
        results_by_config["hybrid_neural_reranker"].append(compute_metrics(ranked_ce, rel_blocks, rel_map, pref_doc))

    # Aggregation
    summary = {}
    print("\n==============================================================================================================================================")
    print(f"{'Configuration':<32} | {'Hit@1':<6} | {'Hit@3':<6} | {'Hit@5':<6} | {'Rec@1':<6} | {'Rec@3':<6} | {'Rec@5':<6} | {'Rec@10':<6} | {'MRR':<6} | {'nDCG@10':<7} | {'AuthAcc':<7} | {'p50 e2e':<9} | {'p95 e2e':<9} | {'mean e2e':<9}")
    print("----------------------------------------------------------------------------------------------------------------------------------------------")

    for cfg in configs:
        stats = aggregate_stats(results_by_config[cfg], e2e_latencies[cfg], fusion_latencies[cfg])
        summary[cfg] = stats
        print(f"{cfg:<32} | {stats['hit@1']:<6.3f} | {stats['hit@3']:<6.3f} | {stats['hit@5']:<6.3f} | {stats['recall@1']:<6.3f} | {stats['recall@3']:<6.3f} | {stats['recall@5']:<6.3f} | {stats['recall@10']:<6.3f} | {stats['mrr']:<6.3f} | {stats['ndcg@10']:<7.3f} | {stats['authority_accuracy']:<7.3f} | {stats['latency_p50_ms']:<7.1f}ms | {stats['latency_p95_ms']:<7.1f}ms | {stats['latency_mean_ms']:<7.1f}ms")

    # Output JSON
    output_payload = {
        "benchmark_id": "medicalplab-full-corpus-817-retrieval-comparison-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "corpus": {
            "version": corpus_version,
            "snapshot_id": snapshot["corpus_id"],
            "document_count": doc_count,
            "chunk_count": len(chunks),
        },
        "evaluation_set": {
            "eval_set_id": eval_data.get("eval_set_id"),
            "version": eval_data.get("version"),
            "total_case_count": total_cases,
            "answerable_case_count": len(answerable_cases),
            "unsupported_case_count": len(unsupported_cases),
        },
        "models": {
            "dense_retriever": DENSE_MODEL_NAME,
            "neural_reranker": CROSS_ENCODER_NAME,
            "device": device,
        },
        "runtime": {
            "bm25_index_seconds": round(bm25_build_time, 3),
            "dense_model_load_seconds": round(dense_load_time, 3),
            "corpus_encode_seconds": round(corpus_encode_time, 3),
        },
        "summary_metrics": summary,
    }

    out_file = RESULTS_DIR / "full_corpus_817_retrieval_comparison_v1.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)
    print(f"\nSaved full corpus benchmark results to {out_file}")


if __name__ == "__main__":
    main()
