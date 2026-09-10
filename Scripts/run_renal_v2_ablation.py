"""Run resumable Renal V2 DEV retrieval ablations on the frozen matrix inputs."""

from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np
import torch
from sentence_transformers import CrossEncoder, SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Scripts"))

import run_renal_v2_matrix as matrix
from medicalplab.learn.renal_bm25 import RenalBM25Index
from medicalplab.learn.renal_normalization import normalize_renal_query

OUT = ROOT / "reports" / "renal_v2_ablation.json"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
PROMPTS = {
    "instruction_a": matrix.QUERY_INSTRUCTION,
    "instruction_b": (
        "Instruct: Given a medical student's renal/urinary learning question, retrieve "
        "the most directly supporting textbook-like or clinical evidence passage.\nQuery: "
    ),
    "instruction_c": (
        "Instruct: Retrieve the renal evidence needed to accurately teach the following "
        "undergraduate medical question.\nQuery: "
    ),
}


def score_value(metrics: dict[str, Any]) -> tuple[float, float, float, float]:
    return (
        metrics["hit_at_1"]["value"],
        metrics["mrr"],
        metrics["ndcg_at_10"],
        metrics["hit_at_5"]["value"],
    )


def ids_and_scores(scores: np.ndarray, count: int) -> list[int]:
    count = min(count, len(scores))
    if count == 0:
        return []
    selected = np.argpartition(scores, -count)[-count:]
    return [int(index) for index in selected[np.argsort(scores[selected])[::-1]]]


def ranked_chunks(all_indices: list[list[int]], chunks: list[dict[str, Any]], top_k: int = 10) -> list[list[dict[str, Any]]]:
    return [[chunks[index] for index in indices[:top_k]] for indices in all_indices]


def evaluate(indices: list[list[int]], chunks: list[dict[str, Any]], queries: list[dict[str, Any]]) -> dict[str, Any]:
    return matrix.compute_metrics(ranked_chunks(indices, chunks), queries, chunks)


def parent_deduplicate(indices: list[int], chunks: list[dict[str, Any]], top_k: int) -> list[int]:
    output: list[int] = []
    seen: set[str] = set()
    for index in indices:
        key = matrix.parent_id(chunks[index]) or matrix.chunk_id(chunks[index])
        if key in seen:
            continue
        seen.add(key)
        output.append(index)
        if len(output) == top_k:
            break
    return output


def role_adjusted_scores(scores: np.ndarray, chunks: list[dict[str, Any]]) -> np.ndarray:
    adjusted = scores.copy()
    for index, chunk in enumerate(chunks):
        role = chunk.get("retrieval_role", "SUPPORTING")
        if role == "EXCLUDED_FROM_SEARCH":
            adjusted[index] = -np.inf
        elif role == "LOW_PRIORITY":
            adjusted[index] -= 0.03
    return adjusted


def cache_query_embeddings(
    model: SentenceTransformer,
    revision: str,
    queries: list[dict[str, Any]],
    prompt_name: str,
    prompt: str,
    normalized: bool,
) -> np.ndarray:
    traces = [normalize_renal_query(query["query"]) for query in queries]
    bodies = [trace.normalized_query if normalized else trace.original_query for trace in traces]
    texts = [prompt + body for body in bodies]
    ids = [query["query_id"] for query in queries]
    corpus_sha = matrix.canonical_sha(list(zip(ids, texts)))
    representation = f"{prompt_name}-{'normalized' if normalized else 'raw'}"
    key = matrix.embedding_cache_key("queries", revision, "queries", representation, corpus_sha)
    cached = matrix.load_embedding_cache(key, ids)
    if cached is not None:
        print(f"QUERY_CACHE=HIT {representation} {key}", flush=True)
        return cached
    print(f"QUERY_CACHE=MISS {representation} {key}", flush=True)
    encoded, batch_size = matrix.encode_gpu(model, texts, f"QUERIES {representation}")
    matrix.save_embedding_cache(
        key,
        ids,
        encoded,
        {
            "kind": "queries",
            "dataset_sha256": matrix.verified_dataset_sha(matrix.DEV_PATH),
            "prompt_name": prompt_name,
            "normalized": normalized,
            "batch_size": batch_size,
        },
    )
    return encoded


def corpus_embeddings(chunks: list[dict[str, Any]]) -> tuple[np.ndarray, dict[str, Any]]:
    report = json.loads(matrix.OUT_REPORT.read_text(encoding="utf-8"))
    entry = next(
        item
        for item in report["results"]
        if item["chunking"] == "B_400_overlap" and item["representation"] == "content_only"
    )
    embeddings = matrix.load_embedding_cache(entry["embedding_cache_key"], [matrix.chunk_id(chunk) for chunk in chunks])
    if embeddings is None:
        raise RuntimeError("Best matrix embedding cache is absent or failed hash verification")
    return embeddings, entry


def bm25_rankings(index: RenalBM25Index, queries: list[str], top_k: int) -> tuple[list[list[int]], list[list[tuple[int, float]]]]:
    rankings: list[list[int]] = []
    scored: list[list[tuple[int, float]]] = []
    for query in queries:
        hits = index.search(query, top_k=top_k)
        rankings.append([hit.index for hit in hits])
        scored.append([(hit.index, hit.score) for hit in hits])
    return rankings, scored


def rrf_rankings(
    dense: list[list[int]],
    sparse: list[list[int]],
    depth: int,
    rrf_k: int,
    chunks: list[dict[str, Any]],
    deduplicate_parents: bool,
    top_k: int,
) -> tuple[list[list[int]], list[list[tuple[int, float]]]]:
    all_rankings: list[list[int]] = []
    all_scores: list[list[tuple[int, float]]] = []
    for dense_indices, sparse_indices in zip(dense, sparse):
        fused: dict[int, float] = {}
        for rank, index in enumerate(dense_indices[:depth], 1):
            fused[index] = fused.get(index, 0.0) + 1.0 / (rrf_k + rank)
        for rank, index in enumerate(sparse_indices[:depth], 1):
            fused[index] = fused.get(index, 0.0) + 1.0 / (rrf_k + rank)
        ordered = sorted(fused, key=lambda index: (-fused[index], matrix.chunk_id(chunks[index])))
        if deduplicate_parents:
            ordered = parent_deduplicate(ordered, chunks, top_k)
        else:
            ordered = ordered[:top_k]
        all_rankings.append(ordered)
        all_scores.append([(index, fused[index]) for index in ordered])
    return all_rankings, all_scores


def failures(indices: list[list[int]], chunks: list[dict[str, Any]], queries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for query, ranked in zip(queries, indices):
        first = next((rank for rank, index in enumerate(ranked[:10], 1) if matrix.is_relevant(chunks[index], query)), None)
        if first is not None:
            continue
        gold_docs = set(query.get("gold_document_ids", []))
        top = [chunks[index] for index in ranked[:10]]
        same_doc = [chunk for chunk in top if chunk.get("document_id") in gold_docs]
        category = "RIGHT_DOCUMENT_WRONG_SECTION" if same_doc else "WRONG_DOCUMENT"
        if any(
            any(term in " ".join(chunk.get("section_path", [])).casefold() for term in ("method", "statistical", "result"))
            for chunk in same_doc
        ):
            category = "METHODS_RESULTS_NOISE"
        output.append(
            {
                "query_id": query["query_id"],
                "query": query["query"],
                "topic": query["topic"],
                "gold_document_ids": query.get("gold_document_ids", []),
                "gold_parent_section_ids": query.get("gold_parent_section_ids", []),
                "top_10": [
                    {
                        "rank": rank,
                        "chunk_id": matrix.chunk_id(chunk),
                        "document_id": chunk.get("document_id"),
                        "parent_section_id": matrix.parent_id(chunk),
                        "section_path": chunk.get("section_path", []),
                    }
                    for rank, chunk in enumerate(top, 1)
                ],
                "failure_category": category,
            }
        )
    return output


def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required; CPU fallback is prohibited")
    print(f"PYTHON={sys.executable} TORCH={torch.__version__} CUDA={torch.version.cuda}", flush=True)
    print(f"DEVICE={torch.cuda.get_device_name(0)}", flush=True)
    queries = matrix.load_queries()
    chunks = matrix.load_chunks("B_400_overlap")
    registry = matrix.load_registry()
    embeddings, matrix_entry = corpus_embeddings(chunks)
    print(f"CORPUS_CACHE=HIT HASH_VERIFIED=true PASSAGES={len(chunks)}", flush=True)
    model = SentenceTransformer(matrix.MODEL_ID, device="cuda", local_files_only=True)
    model.max_seq_length = matrix.MAX_SEQUENCE_LENGTH
    model.eval()
    revision = matrix.model_revision(model)
    stages: list[dict[str, Any]] = []

    # Prompt selection is small and DEV-only.
    prompt_trials: list[dict[str, Any]] = []
    raw_embeddings_by_prompt: dict[str, np.ndarray] = {}
    for name, prompt in PROMPTS.items():
        query_embeddings = cache_query_embeddings(model, revision, queries, name, prompt, normalized=False)
        raw_embeddings_by_prompt[name] = query_embeddings
        similarities = embeddings @ query_embeddings.T
        ranked = [ids_and_scores(similarities[:, q_index], 10) for q_index in range(len(queries))]
        metrics = evaluate(ranked, chunks, queries)
        prompt_trials.append({"prompt": name, "text": prompt, "metrics": metrics})
    selected_prompt = max(prompt_trials, key=lambda item: score_value(item["metrics"]))["prompt"]
    print(f"SELECTED_PROMPT={selected_prompt}", flush=True)
    raw_queries = raw_embeddings_by_prompt[selected_prompt]
    raw_similarities = embeddings @ raw_queries.T
    raw_ranked = [ids_and_scores(raw_similarities[:, q_index], 50) for q_index in range(len(queries))]
    stages.append({"stage": "best_dense_matrix", "metrics": evaluate(raw_ranked, chunks, queries)})

    normalized_embeddings = cache_query_embeddings(
        model, revision, queries, selected_prompt, PROMPTS[selected_prompt], normalized=True
    )
    normalized_similarities = embeddings @ normalized_embeddings.T
    normalized_ranked = [ids_and_scores(normalized_similarities[:, q_index], 50) for q_index in range(len(queries))]
    stages.append({"stage": "plus_query_normalization", "metrics": evaluate(normalized_ranked, chunks, queries)})

    filtered_scores = [role_adjusted_scores(normalized_similarities[:, q_index], chunks) for q_index in range(len(queries))]
    filtered_ranked = [ids_and_scores(scores, 50) for scores in filtered_scores]
    stages.append({"stage": "plus_section_role_filtering", "metrics": evaluate(filtered_ranked, chunks, queries)})

    parent_ranked = [parent_deduplicate(indices, chunks, 50) for indices in filtered_ranked]
    stages.append({"stage": "plus_parent_child_deduplication", "metrics": evaluate(parent_ranked, chunks, queries)})

    normalized_texts = [normalize_renal_query(query["query"]).normalized_query for query in queries]
    active_indices = [index for index, chunk in enumerate(chunks) if chunk.get("retrieval_role") != "EXCLUDED_FROM_SEARCH"]
    active_chunks = [chunks[index] for index in active_indices]
    bm25 = RenalBM25Index(active_chunks, [str(chunk.get("text", "")) for chunk in active_chunks])
    active_bm25_ranked, active_bm25_scored = bm25_rankings(bm25, normalized_texts, 50)
    sparse_ranked = [[active_indices[index] for index in ranking] for ranking in active_bm25_ranked]
    sparse_scored = [[(active_indices[index], score) for index, score in scored] for scored in active_bm25_scored]
    stages.append({"stage": "bm25_only", "metrics": evaluate(sparse_ranked, chunks, queries)})

    rrf_trials: list[dict[str, Any]] = []
    for depth in (30, 50):
        for rrf_k in (20, 60):
            ranked, scored = rrf_rankings(parent_ranked, sparse_ranked, depth, rrf_k, chunks, True, 50)
            rrf_trials.append(
                {"depth": depth, "rrf_k": rrf_k, "metrics": evaluate(ranked, chunks, queries), "ranked": ranked, "scored": scored}
            )
    best_rrf = max(rrf_trials, key=lambda item: score_value(item["metrics"]))
    hybrid_ranked = best_rrf.pop("ranked")
    hybrid_scored = best_rrf.pop("scored")
    stages.append({"stage": "plus_hybrid_rrf", "metrics": best_rrf["metrics"]})
    print(f"SELECTED_RRF depth={best_rrf['depth']} k={best_rrf['rrf_k']}", flush=True)

    reranker = CrossEncoder(RERANK_MODEL_ID, device="cuda", local_files_only=True, trust_remote_code=True)
    reranker_trials: list[dict[str, Any]] = []
    reranker_score_sets: dict[str, list[list[tuple[int, float]]]] = {}
    rerank_seconds = 0.0
    candidate_generators = {
        "best_dense_raw": raw_ranked,
        "normalized_filtered_parent": parent_ranked,
        "hybrid_rrf": hybrid_ranked,
    }
    for generator_name, generator_rankings in candidate_generators.items():
        candidates = [ranking[:30] for ranking in generator_rankings]
        query_bodies = [query["query"] for query in queries] if generator_name == "best_dense_raw" else normalized_texts
        pairs = [
            (query_bodies[query_index], str(chunks[index].get("text", "")))
            for query_index, ranking in enumerate(candidates)
            for index in ranking
        ]
        offsets = [0]
        for ranking in candidates:
            offsets.append(offsets[-1] + len(ranking))
        rerank_started = time.perf_counter()
        with torch.inference_mode():
            pair_scores = np.asarray(
                reranker.predict(pairs, batch_size=8, show_progress_bar=True), dtype=np.float32
            ).reshape(-1)
        elapsed = time.perf_counter() - rerank_started
        rerank_seconds += elapsed
        reranked: list[list[int]] = []
        scored_rankings: list[list[tuple[int, float]]] = []
        for query_index, ranking in enumerate(candidates):
            scores = pair_scores[offsets[query_index] : offsets[query_index + 1]]
            order = np.argsort(scores)[::-1]
            ordered = [ranking[int(position)] for position in order]
            reranked.append(ordered)
            scored_rankings.append(
                [(ranking[int(position)], float(scores[int(position)])) for position in order]
            )
        trial_metrics = evaluate(reranked, chunks, queries)
        reranker_trials.append(
            {
                "candidate_generator": generator_name,
                "elapsed_seconds": elapsed,
                "metrics": trial_metrics,
                "ranked": reranked,
            }
        )
        reranker_score_sets[generator_name] = scored_rankings
    best_reranker = max(reranker_trials, key=lambda item: score_value(item["metrics"]))
    selected_reranker_generator = best_reranker["candidate_generator"]
    reranked = best_reranker.pop("ranked")
    reranker_scores = reranker_score_sets[selected_reranker_generator]
    stages.append(
        {
            "stage": "plus_qwen3_reranker",
            "candidate_generator": selected_reranker_generator,
            "metrics": best_reranker["metrics"],
        }
    )

    # A bounded educational-source prior trial; keep it only if it improves the primary tuple.
    prior_trials: list[dict[str, Any]] = []
    for weight in (0.0, 0.025, 0.05):
        ranked: list[list[int]] = []
        for scores in reranker_scores:
            adjusted = []
            for index, score in scores:
                role = registry.get(str(chunks[index].get("document_id")), {}).get("educational_classification", "SUPPORTING")
                bonus = weight if role == "CORE_EDUCATIONAL" else (weight * 0.5 if role == "SUPPORTING" else 0.0)
                adjusted.append((index, score + bonus))
            ranked.append([index for index, _ in sorted(adjusted, key=lambda item: item[1], reverse=True)])
        prior_trials.append({"weight": weight, "metrics": evaluate(ranked, chunks, queries), "ranked": ranked})
    best_prior = max(prior_trials, key=lambda item: score_value(item["metrics"]))
    final_ranked = best_prior.pop("ranked")
    if best_prior["weight"] > 0.0:
        stages.append({"stage": "plus_educational_source_prior", "metrics": best_prior["metrics"]})
    final_failures = failures(final_ranked, chunks, queries)
    breakdown = Counter(item["failure_category"] for item in final_failures)

    payload = {
        "report_id": "RENAL-V2-RETRIEVAL-ABLATION",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset": "RENAL-DEV-v2",
        "dataset_sha256": matrix.verified_dataset_sha(matrix.DEV_PATH),
        "n_answerable": len(queries),
        "model_id": matrix.MODEL_ID,
        "model_revision": revision,
        "matrix_selection": matrix_entry,
        "prompt_trials": prompt_trials,
        "selected_prompt": selected_prompt,
        "normalization_version": "renal-normalization-v1",
        "role_filter": {"excluded": "removed", "low_priority_dense_penalty": 0.03},
        "bm25": {"k1": 1.5, "b": 0.75},
        "rrf_trials": rrf_trials,
        "selected_rrf": {"depth": best_rrf["depth"], "rrf_k": best_rrf["rrf_k"]},
        "reranker": {
            "model_id": RERANK_MODEL_ID,
            "candidate_count": 30,
            "batch_size": 8,
            "selected_candidate_generator": selected_reranker_generator,
            "total_trial_elapsed_seconds": rerank_seconds,
        },
        "reranker_trials": reranker_trials,
        "source_prior_trials": prior_trials,
        "selected_source_prior": best_prior["weight"],
        "stages": stages,
        "final_failure_breakdown": dict(breakdown),
        "final_failures": final_failures,
    }
    matrix.atomic_json(OUT, payload)
    print(f"ABLATION_COMPLETE={OUT}", flush=True)
    for stage in stages:
        print(f"{stage['stage']}: {matrix.metric_summary(stage['metrics'])}", flush=True)


if __name__ == "__main__":
    main()
