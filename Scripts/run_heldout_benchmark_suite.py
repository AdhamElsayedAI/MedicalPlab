"""Comprehensive Retrieval Benchmark Suite on Frozen Held-out Evaluation Set.

Benchmarks 5 configurations on medicalplab-retrieval-multisource-heldout-v1:
1. BM25 only
2. Dense only (Qwen/Qwen3-Embedding-0.6B)
3. BM25 + Dense (Weighted linear combination)
4. Hybrid + Weighted RRF
5. Hybrid + MedicalReranker (multi-factor clinical heuristic)

Tracks:
- Hit@1, Hit@3, Hit@5
- Recall@1, Recall@3, Recall@5, Recall@10
- MRR
- nDCG@10
- Authority-selection accuracy
- Latency, model/device, corpus version, eval version.
"""

import json
import math
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from medicalplab.stage_b.evidence_policy import normalize

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_PATH = PROJECT_ROOT / "evaluation" / "retrieval_eval_multisource_heldout_v1.json"
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"
MANIFEST_PATH = PROJECT_ROOT / "Data" / "metadata" / "document_manifest.json"
SNAPSHOT_PATH = PROJECT_ROOT / "Data" / "metadata" / "corpus_cardiorespiratory_snapshot_v1.json"

MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = (
    "Instruct: Given a medical education query, retrieve the passages "
    "from the available medical sources that most directly support the "
    "requested claim. Respect any source explicitly requested by the "
    "query. Do not assume every query targets a guideline.\nQuery:"
)


def load_corpus(document_ids: list[str]) -> list[dict[str, Any]]:
    chunks = []
    manifest = json.load(open(MANIFEST_PATH, encoding="utf-8"))
    doc_map = {d["document_id"]: d for d in manifest}

    for doc_id in document_ids:
        doc = doc_map.get(doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not in manifest")
        spec = doc.get("medical_specialty", "Cardiology").strip().lower().replace(" ", "_").replace("/", "_")
        chunk_file = PROJECT_ROOT / "Data" / "processed" / spec / f"{doc_id}.chunks.json"
        if not chunk_file.exists():
            raise FileNotFoundError(f"Missing chunk file: {chunk_file}")
        data = json.load(open(chunk_file, encoding="utf-8"))
        c_list = data.get("chunks", []) if isinstance(data, dict) else data
        chunks.extend(c_list)
    return chunks


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


# Metrics
def compute_metrics(
    ranked_blocks: list[str],
    relevant_blocks: set[str],
    relevance_map: dict[str, int],
    preferred_doc: str | None,
) -> dict[str, Any]:
    # Hit@k
    hit1 = 1.0 if any(b in relevant_blocks for b in ranked_blocks[:1]) else 0.0
    hit3 = 1.0 if any(b in relevant_blocks for b in ranked_blocks[:3]) else 0.0
    hit5 = 1.0 if any(b in relevant_blocks for b in ranked_blocks[:5]) else 0.0

    # Recall@k
    n_rel = len(relevant_blocks)
    if n_rel > 0:
        rec1 = len(set(ranked_blocks[:1]) & relevant_blocks) / n_rel
        rec3 = len(set(ranked_blocks[:3]) & relevant_blocks) / n_rel
        rec5 = len(set(ranked_blocks[:5]) & relevant_blocks) / n_rel
        rec10 = len(set(ranked_blocks[:10]) & relevant_blocks) / n_rel
    else:
        rec1 = rec3 = rec5 = rec10 = 0.0

    # MRR
    mrr = 0.0
    for rank, b in enumerate(ranked_blocks, start=1):
        if b in relevant_blocks:
            mrr = 1.0 / rank
            break

    # nDCG@10
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

    # Authority selection accuracy (hit@3 with preferred_doc)
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


def aggregate(metric_dicts: list[dict[str, Any]]) -> dict[str, float]:
    keys = ["hit@1", "hit@3", "hit@5", "recall@1", "recall@3", "recall@5", "recall@10", "mrr", "ndcg@10"]
    agg = {}
    for k in keys:
        vals = [m[k] for m in metric_dicts if k in m]
        agg[k] = round(sum(vals) / len(vals), 4) if vals else 0.0
    
    auth_vals = [m["auth_hit"] for m in metric_dicts if m.get("auth_hit") is not None]
    agg["authority_accuracy"] = round(sum(auth_vals) / len(auth_vals), 4) if auth_vals else 1.0
    return agg


def main():
    eval_data = json.load(open(EVAL_PATH, encoding="utf-8"))
    cases = eval_data["cases"]
    answerable_cases = [c for c in cases if c.get("expected_answerable", True)]
    target_doc_ids = eval_data.get("corpus_document_ids", ["DOC-WHO-CARD-0001", "DOC-PMC-CARD-0002"])

    print("==================================================================")
    print(f"RUNNING RETRIEVAL BENCHMARK SUITE")
    print(f"Eval set: {eval_data.get('eval_set_id')} v{eval_data.get('version')}")
    print(f"Answerable cases: {len(answerable_cases)} / Total cases: {len(cases)}")
    print(f"Target documents: {target_doc_ids}")
    print("==================================================================")

    # 1. Load corpus chunks
    chunks = load_corpus(target_doc_ids)
    print(f"Loaded {len(chunks)} chunks across {len(target_doc_ids)} documents")

    # 2. Build BM25 index
    bm25 = BM25Index(chunks)

    # 3. Load dense model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {MODEL_NAME} on {device}...")
    t0 = time.perf_counter()
    model = SentenceTransformer(MODEL_NAME, device=device)
    model_load_time = time.perf_counter() - t0

    # 4. Encode corpus
    t0 = time.perf_counter()
    corpus_texts = [format_chunk_text(c) for c in chunks]
    corpus_embs = model.encode(corpus_texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    corpus_encode_time = time.perf_counter() - t0

    # Pre-map chunk indices to block keys
    chunk_keys = [block_key(c) for c in chunks]

    # Evaluate all 5 strategies
    results_by_strategy: dict[str, list[dict[str, Any]]] = {
        "bm25_only": [],
        "dense_only": [],
        "bm25_dense_blend": [],
        "hybrid_weighted_rrf": [],
        "hybrid_medical_reranker": [],
    }
    latencies: dict[str, list[float]] = defaultdict(list)

    # Load Stage-R MedicalReranker for Strategy 5
    from medicalplab.stage_r.reranker import MedicalReranker
    from medicalplab.stage_r.models import EvidenceCandidate, ScoreBreakdown
    from medicalplab.stage_r.query_expansion import expand_query
    reranker = MedicalReranker()

    for case in answerable_cases:
        query_text = case["query"]
        relevant_blocks = {f"{r['document_id']}:B{int(r['block_index']):04d}" for r in case.get("relevant_blocks", [])}
        relevance_map = {f"{r['document_id']}:B{int(r['block_index']):04d}": int(r.get("relevance", 3)) for r in case.get("relevant_blocks", [])}
        preferred_doc = case.get("preferred_document_id")

        # --- 1. BM25 only ---
        t_start = time.perf_counter()
        bm25_scores = bm25.score_query(query_text)
        max_bm25 = np.max(bm25_scores) if np.max(bm25_scores) > 0 else 1.0
        norm_bm25 = bm25_scores / max_bm25

        # Aggregate chunk scores to unique block keys
        best_bm25_by_block = defaultdict(lambda: float("-inf"))
        for k, s in zip(chunk_keys, norm_bm25):
            if s > best_bm25_by_block[k]:
                best_bm25_by_block[k] = float(s)
        ranked_bm25 = [k for k, _ in sorted(best_bm25_by_block.items(), key=lambda x: x[1], reverse=True)]
        latencies["bm25_only"].append(time.perf_counter() - t_start)
        results_by_strategy["bm25_only"].append(compute_metrics(ranked_bm25, relevant_blocks, relevance_map, preferred_doc))

        # --- 2. Dense only ---
        t_start = time.perf_counter()
        formatted_q = f"{QUERY_INSTRUCTION}\n{query_text.strip()}"
        q_emb = model.encode([formatted_q], normalize_embeddings=True, show_progress_bar=False)[0]
        dense_sims = np.dot(corpus_embs, q_emb)

        best_dense_by_block = defaultdict(lambda: float("-inf"))
        for k, s in zip(chunk_keys, dense_sims):
            if s > best_dense_by_block[k]:
                best_dense_by_block[k] = float(s)
        ranked_dense = [k for k, _ in sorted(best_dense_by_block.items(), key=lambda x: x[1], reverse=True)]
        latencies["dense_only"].append(time.perf_counter() - t_start)
        results_by_strategy["dense_only"].append(compute_metrics(ranked_dense, relevant_blocks, relevance_map, preferred_doc))

        # --- 3. BM25 + Dense blend (alpha=0.6 dense, 0.4 sparse) ---
        t_start = time.perf_counter()
        best_blend_by_block = {}
        all_keys = set(best_bm25_by_block.keys()) | set(best_dense_by_block.keys())
        for k in all_keys:
            d_s = max(0.0, best_dense_by_block.get(k, 0.0))
            b_s = max(0.0, best_bm25_by_block.get(k, 0.0))
            best_blend_by_block[k] = 0.6 * d_s + 0.4 * b_s
        ranked_blend = [k for k, _ in sorted(best_blend_by_block.items(), key=lambda x: x[1], reverse=True)]
        latencies["bm25_dense_blend"].append(time.perf_counter() - t_start)
        results_by_strategy["bm25_dense_blend"].append(compute_metrics(ranked_blend, relevant_blocks, relevance_map, preferred_doc))

        # --- 4. Hybrid + Weighted RRF (k=60, dense_weight=2.0, bm25_weight=1.0) ---
        t_start = time.perf_counter()
        rrf_k = 60
        rrf_scores = defaultdict(float)
        for rank, k in enumerate(ranked_dense[:30], start=1):
            rrf_scores[k] += 2.0 / (rrf_k + rank)
        for rank, k in enumerate(ranked_bm25[:30], start=1):
            rrf_scores[k] += 1.0 / (rrf_k + rank)
        ranked_rrf = [k for k, _ in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)]
        latencies["hybrid_weighted_rrf"].append(time.perf_counter() - t_start)
        results_by_strategy["hybrid_weighted_rrf"].append(compute_metrics(ranked_rrf, relevant_blocks, relevance_map, preferred_doc))

        # --- 5. Hybrid + MedicalReranker ---
        t_start = time.perf_counter()
        retrieval_query = expand_query(query_text)
        # Build candidates from top 20 blend candidates
        block_lookup = {block_key(c): c for c in chunks}
        candidates = []
        for k in ranked_blend[:20]:
            chunk_data = block_lookup[k]
            score = best_blend_by_block[k]
            breakdown = ScoreBreakdown(
                dense_score=best_dense_by_block.get(k, 0.0),
                sparse_score=best_bm25_by_block.get(k, 0.0),
                alpha=0.6,
                hybrid_score=score,
                rerank_score=0.0,
                final_score=score,
            )
            cand = EvidenceCandidate(
                ref=k,
                document_id=chunk_data["document_id"],
                source=chunk_data.get("block_type", "guideline"),
                heading=chunk_data.get("heading", ""),
                section=chunk_data.get("section", ""),
                text=chunk_data.get("text", ""),
                score=score,
                score_breakdown=breakdown,
            )
            candidates.append(cand)
        
        reranked = reranker.rerank(query=retrieval_query, candidates=candidates, top_k=10)
        ranked_reranked = [r.ref for r in reranked]
        # Append remaining candidates to fill out ranking
        for k in ranked_blend:
            if k not in ranked_reranked:
                ranked_reranked.append(k)
        latencies["hybrid_medical_reranker"].append(time.perf_counter() - t_start)
        results_by_strategy["hybrid_medical_reranker"].append(compute_metrics(ranked_reranked, relevant_blocks, relevance_map, preferred_doc))

    # Print Summary Table
    print("\n=========================================================================================")
    print(f"{'Strategy':<26} | {'Hit@1':<6} | {'Hit@3':<6} | {'Rec@3':<6} | {'Rec@10':<6} | {'MRR':<6} | {'nDCG@10':<7} | {'AuthAcc':<7} | {'Latency':<7}")
    print("-----------------------------------------------------------------------------------------")
    
    summary_out = {}
    for strat, metric_list in results_by_strategy.items():
        agg = aggregate(metric_list)
        avg_lat = round(sum(latencies[strat]) / len(latencies[strat]) * 1000, 2)
        print(f"{strat:<26} | {agg['hit@1']:<6.3f} | {agg['hit@3']:<6.3f} | {agg['recall@3']:<6.3f} | {agg['recall@10']:<6.3f} | {agg['mrr']:<6.3f} | {agg['ndcg@10']:<7.3f} | {agg['authority_accuracy']:<7.3f} | {avg_lat:<5.1f}ms")
        summary_out[strat] = {
            **agg,
            "latency_ms": avg_lat,
        }

    output_payload = {
        "benchmark_id": "medicalplab-heldout-retrieval-comparison-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evaluation_set": {
            "eval_set_id": eval_data.get("eval_set_id"),
            "version": eval_data.get("version"),
            "answerable_queries": len(answerable_cases),
        },
        "corpus": {
            "version": "1.0.0",
            "snapshot_id": "medicalplab-cardiorespiratory-corpus-v1",
            "documents_evaluated": target_doc_ids,
            "chunk_count": len(chunks),
        },
        "model": {
            "dense_model": MODEL_NAME,
            "device": device,
            "model_load_seconds": round(model_load_time, 2),
            "corpus_encode_seconds": round(corpus_encode_time, 2),
        },
        "summary_metrics": summary_out,
    }

    out_file = RESULTS_DIR / "heldout_retrieval_comparison_v1.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)
    print(f"\nBenchmark results saved to: {out_file}")


if __name__ == "__main__":
    main()
