"""Comparative Evaluation of True Neural Cross-Encoder vs Heuristic MedicalReranker vs Non-Reranked Hybrid.

Evaluates on the frozen held-out benchmark:
- evaluation/retrieval_eval_multisource_heldout_v1.json (20 answerable cases)
- 227 frozen corpus chunks (DOC-WHO-CARD-0001, DOC-PMC-CARD-0002)

Compares:
1. Non-reranked Hybrid (Weighted RRF)
2. Heuristic MedicalReranker (rule/keyword based)
3. Neural Cross-Encoder (cross-encoder/ms-marco-MiniLM-L-6-v2)

Tracks:
- Hit@1, Hit@3, Hit@5
- Recall@1, Recall@3, Recall@5, Recall@10
- MRR
- nDCG@10
- Authority-selection accuracy
- Latency (mean, p50, p95)
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
EVAL_PATH = PROJECT_ROOT / "evaluation" / "retrieval_eval_multisource_heldout_v1.json"
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
MANIFEST_PATH = PROJECT_ROOT / "Data" / "metadata" / "document_manifest.json"

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


def aggregate(metric_dicts: list[dict[str, Any]], latencies: list[float]) -> dict[str, Any]:
    keys = ["hit@1", "hit@3", "hit@5", "recall@1", "recall@3", "recall@5", "recall@10", "mrr", "ndcg@10"]
    agg = {}
    for k in keys:
        vals = [m[k] for m in metric_dicts if k in m]
        agg[k] = round(sum(vals) / len(vals), 4) if vals else 0.0
    
    auth_vals = [m["auth_hit"] for m in metric_dicts if m.get("auth_hit") is not None]
    agg["authority_accuracy"] = round(sum(auth_vals) / len(auth_vals), 4) if auth_vals else 1.0
    
    lat_ms = np.array(latencies) * 1000
    agg["latency_mean_ms"] = round(float(np.mean(lat_ms)), 2)
    agg["latency_p50_ms"] = round(float(np.percentile(lat_ms, 50)), 2)
    agg["latency_p95_ms"] = round(float(np.percentile(lat_ms, 95)), 2)
    return agg


def main():
    eval_data = json.load(open(EVAL_PATH, encoding="utf-8"))
    cases = [c for c in eval_data["cases"] if c.get("expected_answerable", True)]
    target_docs = eval_data.get("corpus_document_ids", ["DOC-WHO-CARD-0001", "DOC-PMC-CARD-0002"])

    # Load corpus
    chunks = []
    for doc_id in target_docs:
        spec = "cardiology"
        c_path = PROJECT_ROOT / "Data" / "processed" / spec / f"{doc_id}.chunks.json"
        data = json.load(open(c_path, encoding="utf-8"))
        chunks.extend(data.get("chunks", []))
    
    chunk_keys = [block_key(c) for c in chunks]
    block_lookup = {block_key(c): c for c in chunks}
    unique_blocks = list(dict.fromkeys(chunk_keys))

    # Pre-build BM25
    bm25 = BM25Index(chunks)

    # Load Dense
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading dense model {DENSE_MODEL_NAME} on {device}...")
    dense_model = SentenceTransformer(DENSE_MODEL_NAME, device=device)
    corpus_texts = [format_chunk_text(c) for c in chunks]
    corpus_embs = dense_model.encode(corpus_texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)

    # Load Neural Cross-Encoder
    print(f"Loading cross-encoder {CROSS_ENCODER_NAME} on {device}...")
    cross_encoder = CrossEncoder(CROSS_ENCODER_NAME, device=device)

    # Heuristic reranker
    heuristic_reranker = MedicalReranker()

    # Evaluation containers
    results_non_reranked = []
    results_heuristic = []
    results_neural = []

    lats_non_reranked = []
    lats_heuristic = []
    lats_neural = []

    print("\nEvaluating 20 heldout queries across 3 reranker options...")

    for case in cases:
        q = case["query"]
        rel_blocks = {f"{r['document_id']}:B{int(r['block_index']):04d}" for r in case.get("relevant_blocks", [])}
        rel_map = {f"{r['document_id']}:B{int(r['block_index']):04d}": int(r.get("relevance", 3)) for r in case.get("relevant_blocks", [])}
        pref_doc = case.get("preferred_document_id")

        # 1. Base Hybrid Retrieval (Weighted RRF)
        t0 = time.perf_counter()
        q_emb = dense_model.encode([f"{QUERY_INSTRUCTION}\n{q.strip()}"], normalize_embeddings=True, show_progress_bar=False)[0]
        d_sims = np.dot(corpus_embs, q_emb)
        b_sims = bm25.score_query(q)
        max_b = np.max(b_sims) if np.max(b_sims) > 0 else 1.0
        b_sims = b_sims / max_b

        dense_best = defaultdict(lambda: float("-inf"))
        bm25_best = defaultdict(lambda: float("-inf"))
        for k, d_s, b_s in zip(chunk_keys, d_sims, b_sims):
            if d_s > dense_best[k]:
                dense_best[k] = float(d_s)
            if b_s > bm25_best[k]:
                bm25_best[k] = float(b_s)

        ranked_dense = sorted(dense_best.keys(), key=lambda k: dense_best[k], reverse=True)
        ranked_bm25 = sorted(bm25_best.keys(), key=lambda k: bm25_best[k], reverse=True)

        rrf_scores = defaultdict(float)
        for rank, k in enumerate(ranked_dense[:30], start=1):
            rrf_scores[k] += 2.0 / (60 + rank)
        for rank, k in enumerate(ranked_bm25[:30], start=1):
            rrf_scores[k] += 1.0 / (60 + rank)
        
        ranked_hybrid = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)
        t_base = time.perf_counter() - t0
        lats_non_reranked.append(t_base)
        results_non_reranked.append(compute_metrics(ranked_hybrid, rel_blocks, rel_map, pref_doc))

        # Top 15 candidates for reranking
        top_candidates = ranked_hybrid[:15]

        # 2. Heuristic MedicalReranker
        t0 = time.perf_counter()
        retrieval_query = expand_query(q)
        candidates_obj = []
        for k in top_candidates:
            c_data = block_lookup[k]
            score = rrf_scores[k]
            bd = ScoreBreakdown(
                dense_score=dense_best[k],
                sparse_score=bm25_best[k],
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
        for k in ranked_hybrid:
            if k not in ranked_h:
                ranked_h.append(k)
        lats_heuristic.append(t_base + (time.perf_counter() - t0))
        results_heuristic.append(compute_metrics(ranked_h, rel_blocks, rel_map, pref_doc))

        # 3. Neural Cross-Encoder Reranker
        t0 = time.perf_counter()
        pairs = [(q, format_chunk_text(block_lookup[k])) for k in top_candidates]
        ce_scores = cross_encoder.predict(pairs)
        ranked_pairs = sorted(zip(top_candidates, ce_scores), key=lambda x: x[1], reverse=True)
        ranked_neural = [k for k, _ in ranked_pairs]
        for k in ranked_hybrid:
            if k not in ranked_neural:
                ranked_neural.append(k)
        lats_neural.append(t_base + (time.perf_counter() - t0))
        results_neural.append(compute_metrics(ranked_neural, rel_blocks, rel_map, pref_doc))

    # Aggregate
    agg_non_reranked = aggregate(results_non_reranked, lats_non_reranked)
    agg_heuristic = aggregate(results_heuristic, lats_heuristic)
    agg_neural = aggregate(results_neural, lats_neural)

    print("\n==========================================================================================================================")
    print(f"{'Reranker Strategy':<35} | {'Hit@1':<6} | {'Hit@3':<6} | {'Rec@3':<6} | {'Rec@10':<6} | {'MRR':<6} | {'nDCG@10':<7} | {'AuthAcc':<7} | {'p50 Lat':<8} | {'p95 Lat':<8}")
    print("--------------------------------------------------------------------------------------------------------------------------")
    for name, agg in [
        ("1. Non-Reranked Hybrid (RRF)", agg_non_reranked),
        ("2. Heuristic MedicalReranker", agg_heuristic),
        ("3. Neural Cross-Encoder (MiniLM-L6)", agg_neural),
    ]:
        print(f"{name:<35} | {agg['hit@1']:<6.3f} | {agg['hit@3']:<6.3f} | {agg['recall@3']:<6.3f} | {agg['recall@10']:<6.3f} | {agg['mrr']:<6.3f} | {agg['ndcg@10']:<7.3f} | {agg['authority_accuracy']:<7.3f} | {agg['latency_p50_ms']:<6.1f}ms | {agg['latency_p95_ms']:<6.1f}ms")

    out_payload = {
        "benchmark_id": "medicalplab-reranker-decision-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evaluation_set": {
            "eval_set_id": eval_data.get("eval_set_id"),
            "version": eval_data.get("version"),
            "answerable_queries": len(cases),
        },
        "corpus": {
            "snapshot_id": "medicalplab-cardiorespiratory-corpus-v1",
            "document_count": len(target_docs),
            "chunk_count": len(chunks),
        },
        "models": {
            "dense_retriever": DENSE_MODEL_NAME,
            "neural_reranker": CROSS_ENCODER_NAME,
            "device": device,
        },
        "metrics": {
            "non_reranked_hybrid_rrf": agg_non_reranked,
            "heuristic_medical_reranker": agg_heuristic,
            "neural_cross_encoder": agg_neural,
        },
    }

    out_file = RESULTS_DIR / "neural_reranker_comparison_v1.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"\nReranker comparative results saved to: {out_file}")


if __name__ == "__main__":
    main()
