import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sentence_transformers import (
    CrossEncoder,
    SentenceTransformer,
)

from benchmark_hybrid_rrf import (
    BM25,
    BM25_WEIGHT,
    CHUNKS_PATH,
    DENSE_WEIGHT,
    EVAL_PATH,
    MODEL_NAME,
    QUERY_INSTRUCTION,
    RESULTS_DIR,
    RRF_K,
    aggregate_metrics,
    build_bm25_text,
    build_dense_text,
    create_metric_store,
    load_json,
    rank_unique_blocks,
    section_path_to_text,
    tokenize,
    update_metric_store,
    weighted_rrf,
)


# ============================================================
# Configuration
# ============================================================

RERANKER_MODEL = (
    "Qwen/Qwen3-Reranker-0.6B"
)

RERANK_INSTRUCTION = (
    "Given a medical education query, retrieve authoritative "
    "clinical guideline passages that directly answer the query. "
    "Prioritize direct recommendations, implementation remarks, "
    "and supporting evidence."
)

# Keep the existing hybrid benchmark frozen.
HYBRID_CANDIDATES_PER_RETRIEVER = 30

# Realistic candidate pool passed to reranker.
RERANK_CANDIDATES_PER_RETRIEVER = 20

RERANKER_MAX_LENGTH = 2048
RERANKER_BATCH_SIZE = 2


# ============================================================
# Helpers
# ============================================================

def ordered_union(
    *rankings: list[int],
) -> list[int]:
    result: list[int] = []
    seen: set[int] = set()

    for ranking in rankings:
        for block_index in ranking:
            if block_index in seen:
                continue

            seen.add(
                block_index
            )

            result.append(
                block_index
            )

    return result


def build_block_passages(
    chunks: list[dict[str, Any]],
) -> dict[int, str]:
    grouped: dict[
        int,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for chunk in chunks:
        block_index = int(
            chunk[
                "source_block_index"
            ]
        )

        grouped[
            block_index
        ].append(
            chunk
        )

    passages: dict[
        int,
        str,
    ] = {}

    for (
        block_index,
        block_chunks,
    ) in grouped.items():

        block_chunks = sorted(
            block_chunks,
            key=lambda chunk: int(
                chunk[
                    "chunk_index"
                ]
            ),
        )

        first = block_chunks[0]

        reconstructed_text = " ".join(
            str(
                chunk.get(
                    "text",
                    "",
                )
            ).strip()
            for chunk in block_chunks
            if str(
                chunk.get(
                    "text",
                    "",
                )
            ).strip()
        )

        section = section_path_to_text(
            first.get(
                "section_path",
                [],
            )
        )

        heading = str(
            first.get(
                "heading",
                "",
            )
        )

        block_type = str(
            first.get(
                "block_type",
                "",
            )
        )

        specialty = str(
            first.get(
                "medical_specialty",
                "",
            )
        )

        passages[
            block_index
        ] = (
            f"Medical specialty: {specialty}\n"
            f"Section: {section}\n"
            f"Heading: {heading}\n"
            f"Evidence type: {block_type}\n"
            f"Content: {reconstructed_text}"
        )

    return passages


def candidate_recall(
    candidates: list[int],
    relevant_blocks: set[int],
) -> float:
    if not relevant_blocks:
        return 0.0

    return (
        len(
            set(candidates)
            & relevant_blocks
        )
        / len(
            relevant_blocks
        )
    )


def rerank_candidates(
    reranker: CrossEncoder,
    query: str,
    candidate_blocks: list[int],
    block_passages: dict[int, str],
) -> tuple[
    list[int],
    dict[int, float],
]:
    valid_candidates = [
        block_index
        for block_index
        in candidate_blocks
        if block_index
        in block_passages
    ]

    if not valid_candidates:
        return [], {}

    pairs = [
        (
            query,
            block_passages[
                block_index
            ],
        )
        for block_index
        in valid_candidates
    ]

    scores = reranker.predict(
        pairs,
        batch_size=RERANKER_BATCH_SIZE,
        show_progress_bar=False,
    )

    scores_array = np.asarray(
        scores
    ).reshape(-1)

    if (
        len(scores_array)
        != len(valid_candidates)
    ):
        raise RuntimeError(
            "Reranker score count does not match "
            "candidate count."
        )

    score_map = {
        block_index: float(score)
        for block_index, score
        in zip(
            valid_candidates,
            scores_array,
        )
    }

    ranked = sorted(
        valid_candidates,
        key=lambda block_index: (
            -score_map[
                block_index
            ],
            block_index,
        ),
    )

    return (
        ranked,
        score_map,
    )


# ============================================================
# Main
# ============================================================

def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available."
        )

    chunks_document = load_json(
        CHUNKS_PATH
    )

    evaluation = load_json(
        EVAL_PATH
    )

    chunks = chunks_document.get(
        "chunks",
        [],
    )

    cases = evaluation.get(
        "cases",
        [],
    )

    if not isinstance(
        chunks,
        list,
    ):
        raise ValueError(
            "chunks must be a list."
        )

    if not isinstance(
        cases,
        list,
    ):
        raise ValueError(
            "cases must be a list."
        )

    if not chunks:
        raise ValueError(
            "No chunks found."
        )

    answerable_cases = [
        case
        for case in cases
        if case.get(
            "expected_answerable"
        )
    ]

    if not answerable_cases:
        raise ValueError(
            "No answerable evaluation cases found."
        )

    block_passages = (
        build_block_passages(
            chunks
        )
    )

    # ========================================================
    # Header
    # ========================================================

    print(
        "\nMedicalPlab Cross-Encoder Reranker Benchmark"
    )
    print("=" * 84)

    print(
        f"Dense model             : "
        f"{MODEL_NAME}"
    )

    print(
        "Sparse retriever        : BM25"
    )

    print(
        f"Reranker                : "
        f"{RERANKER_MODEL}"
    )

    print(
        f"Candidate retrieval     : "
        f"Dense Top-{RERANK_CANDIDATES_PER_RETRIEVER} "
        f"+ BM25 Top-{RERANK_CANDIDATES_PER_RETRIEVER}"
    )

    print(
        f"Chunks                  : "
        f"{len(chunks)}"
    )

    print(
        f"Source blocks           : "
        f"{len(block_passages)}"
    )

    print(
        f"Answerable queries      : "
        f"{len(answerable_cases)}"
    )

    print(
        f"GPU                     : "
        f"{torch.cuda.get_device_name(0)}"
    )

    # ========================================================
    # BM25
    # ========================================================

    bm25_documents = [
        build_bm25_text(
            chunk
        )
        for chunk in chunks
    ]

    bm25 = BM25(
        [
            tokenize(
                text
            )
            for text
            in bm25_documents
        ]
    )

    # ========================================================
    # Dense retrieval
    # ========================================================

    print(
        "\nLoading dense embedding model..."
    )

    torch.cuda.reset_peak_memory_stats()

    dense_load_start = (
        time.perf_counter()
    )

    dense_model = SentenceTransformer(
        MODEL_NAME,
        device="cuda",
        model_kwargs={
            "torch_dtype": (
                torch.float16
            ),
        },
        processor_kwargs={
            "padding_side": "left",
        },
    )

    dense_model.max_seq_length = 2048

    dense_load_seconds = (
        time.perf_counter()
        - dense_load_start
    )

    print(
        f"Dense model loaded      : "
        f"{dense_load_seconds:.2f}s"
    )

    dense_documents = [
        build_dense_text(
            chunk
        )
        for chunk in chunks
    ]

    print(
        "Encoding corpus..."
    )

    corpus_start = (
        time.perf_counter()
    )

    document_embeddings = (
        dense_model.encode(
            dense_documents,
            batch_size=4,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
    )

    corpus_seconds = (
        time.perf_counter()
        - corpus_start
    )

    queries = [
        case[
            "query"
        ]
        for case
        in answerable_cases
    ]

    query_start = (
        time.perf_counter()
    )

    query_embeddings = (
        dense_model.encode(
            queries,
            prompt=QUERY_INSTRUCTION,
            batch_size=4,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
    )

    query_seconds = (
        time.perf_counter()
        - query_start
    )

    similarity_matrix = (
        query_embeddings
        @ document_embeddings.T
    )

    dense_peak_vram = (
        torch.cuda.max_memory_allocated()
        / 1024**3
    )

    print(
        f"Corpus encoded          : "
        f"{corpus_seconds:.2f}s"
    )

    print(
        f"Queries encoded         : "
        f"{query_seconds:.2f}s"
    )

    print(
        f"Embedding dimension     : "
        f"{document_embeddings.shape[1]}"
    )

    print(
        f"Dense peak VRAM         : "
        f"{dense_peak_vram:.2f} GB"
    )

    # ========================================================
    # Precompute candidate rankings
    # ========================================================

    query_retrieval_data: list[
        dict[str, Any]
    ] = []

    for (
        query_index,
        case,
    ) in enumerate(
        answerable_cases
    ):
        dense_scores = (
            similarity_matrix[
                query_index
            ]
        )

        dense_ranking = (
            rank_unique_blocks(
                chunks,
                dense_scores,
            )
        )

        bm25_scores = (
            bm25.get_scores(
                tokenize(
                    case[
                        "query"
                    ]
                )
            )
        )

        bm25_ranking = (
            rank_unique_blocks(
                chunks,
                bm25_scores,
                positive_only=True,
            )
        )

        # Existing weighted hybrid ranking
        hybrid_ranking, _ = (
            weighted_rrf(
                dense_ranking=(
                    dense_ranking[
                        :HYBRID_CANDIDATES_PER_RETRIEVER
                    ]
                ),
                sparse_ranking=(
                    bm25_ranking[
                        :HYBRID_CANDIDATES_PER_RETRIEVER
                    ]
                ),
                rrf_k=RRF_K,
                dense_weight=(
                    DENSE_WEIGHT
                ),
                sparse_weight=(
                    BM25_WEIGHT
                ),
            )
        )

        # Reranker candidate union.
        candidate_blocks = (
            ordered_union(
                dense_ranking[
                    :RERANK_CANDIDATES_PER_RETRIEVER
                ],
                bm25_ranking[
                    :RERANK_CANDIDATES_PER_RETRIEVER
                ],
            )
        )

        query_retrieval_data.append(
            {
                "case": case,
                "dense_ranking": (
                    dense_ranking
                ),
                "bm25_ranking": (
                    bm25_ranking
                ),
                "hybrid_ranking": (
                    hybrid_ranking
                ),
                "candidates": (
                    candidate_blocks
                ),
            }
        )

    # ========================================================
    # Free embedding model VRAM
    # ========================================================

    del dense_model

    torch.cuda.empty_cache()

    # ========================================================
    # Load reranker
    # ========================================================

    print(
        "\nLoading Qwen3 reranker..."
    )

    torch.cuda.reset_peak_memory_stats()

    reranker_load_start = (
        time.perf_counter()
    )

    reranker = CrossEncoder(
        RERANKER_MODEL,
        device="cuda",
        model_kwargs={
            "torch_dtype": (
                torch.float16
            ),
        },
        prompts={
            "medical": (
                RERANK_INSTRUCTION
            ),
        },
        default_prompt_name="medical",
        max_length=(
            RERANKER_MAX_LENGTH
        ),
    )

    reranker_load_seconds = (
        time.perf_counter()
        - reranker_load_start
    )

    print(
        f"Reranker loaded         : "
        f"{reranker_load_seconds:.2f}s"
    )

    # ========================================================
    # Evaluation
    # ========================================================

    dense_store = (
        create_metric_store()
    )

    hybrid_store = (
        create_metric_store()
    )

    reranker_store = (
        create_metric_store()
    )

    candidate_recalls: list[
        float
    ] = []

    per_query_results: list[
        dict[str, Any]
    ] = []

    total_rerank_start = (
        time.perf_counter()
    )

    print(
        "\nPer-query results"
    )
    print("-" * 145)

    for item in query_retrieval_data:
        case = item[
            "case"
        ]

        dense_ranking = item[
            "dense_ranking"
        ]

        hybrid_ranking = item[
            "hybrid_ranking"
        ]

        candidates = item[
            "candidates"
        ]

        relevance_map = {
            gold[
                "block_index"
            ]: gold[
                "relevance"
            ]
            for gold in case[
                "relevant_blocks"
            ]
        }

        relevant_blocks = set(
            relevance_map
        )

        coverage = candidate_recall(
            candidates,
            relevant_blocks,
        )

        candidate_recalls.append(
            coverage
        )

        reranked, score_map = (
            rerank_candidates(
                reranker=reranker,
                query=case[
                    "query"
                ],
                candidate_blocks=(
                    candidates
                ),
                block_passages=(
                    block_passages
                ),
            )
        )

        dense_metrics = (
            update_metric_store(
                dense_store,
                dense_ranking,
                relevant_blocks,
                relevance_map,
            )
        )

        hybrid_metrics = (
            update_metric_store(
                hybrid_store,
                hybrid_ranking,
                relevant_blocks,
                relevance_map,
            )
        )

        reranker_metrics = (
            update_metric_store(
                reranker_store,
                reranked,
                relevant_blocks,
                relevance_map,
            )
        )

        print(
            f"{case['query_id']:<9} | "
            f"{case['language']:<5} | "
            f"Candidates={len(candidates):<2} | "
            f"GoldCoverage={coverage:.3f} | "
            f"RR={reranker_metrics['reciprocal_rank']:.3f} | "
            f"nDCG@10={reranker_metrics['ndcg_at_10']:.3f} | "
            f"Top5={reranked[:5]}"
        )

        per_query_results.append(
            {
                "query_id": (
                    case[
                        "query_id"
                    ]
                ),
                "language": (
                    case[
                        "language"
                    ]
                ),
                "query_type": (
                    case[
                        "query_type"
                    ]
                ),
                "query": (
                    case[
                        "query"
                    ]
                ),
                "gold_blocks": (
                    sorted(
                        relevant_blocks
                    )
                ),
                "candidate_blocks": (
                    candidates
                ),
                "candidate_recall": (
                    coverage
                ),
                "dense_top_10": (
                    dense_ranking[:10]
                ),
                "hybrid_top_10": (
                    hybrid_ranking[:10]
                ),
                "reranked_top_10": (
                    reranked[:10]
                ),
                "reranker_scores_top_10": {
                    str(
                        block_index
                    ): score_map[
                        block_index
                    ]
                    for block_index
                    in reranked[:10]
                },
                "dense_metrics": (
                    dense_metrics
                ),
                "hybrid_metrics": (
                    hybrid_metrics
                ),
                "reranker_metrics": (
                    reranker_metrics
                ),
            }
        )

    total_rerank_seconds = (
        time.perf_counter()
        - total_rerank_start
    )

    # ========================================================
    # Aggregate
    # ========================================================

    dense_aggregate = (
        aggregate_metrics(
            dense_store
        )
    )

    hybrid_aggregate = (
        aggregate_metrics(
            hybrid_store
        )
    )

    reranker_aggregate = (
        aggregate_metrics(
            reranker_store
        )
    )

    mean_candidate_recall = (
        sum(
            candidate_recalls
        )
        / len(
            candidate_recalls
        )
        if candidate_recalls
        else 0.0
    )

    reranker_peak_vram = (
        torch.cuda.max_memory_allocated()
        / 1024**3
    )

    print(
        "\nCandidate Stage"
    )
    print("-" * 84)

    print(
        f"Mean gold candidate recall : "
        f"{mean_candidate_recall:.4f}"
    )

    print(
        "\nFinal Comparison"
    )
    print("-" * 84)

    print(
        "Metric       Dense      Weighted Hybrid      + Reranker"
    )

    print(
        f"Hit@1        "
        f"{dense_aggregate['hit_at_1']:.4f}     "
        f"{hybrid_aggregate['hit_at_1']:.4f}               "
        f"{reranker_aggregate['hit_at_1']:.4f}"
    )

    print(
        f"Recall@3     "
        f"{dense_aggregate['recall_at_3']:.4f}     "
        f"{hybrid_aggregate['recall_at_3']:.4f}               "
        f"{reranker_aggregate['recall_at_3']:.4f}"
    )

    print(
        f"Recall@5     "
        f"{dense_aggregate['recall_at_5']:.4f}     "
        f"{hybrid_aggregate['recall_at_5']:.4f}               "
        f"{reranker_aggregate['recall_at_5']:.4f}"
    )

    print(
        f"Recall@10    "
        f"{dense_aggregate['recall_at_10']:.4f}     "
        f"{hybrid_aggregate['recall_at_10']:.4f}               "
        f"{reranker_aggregate['recall_at_10']:.4f}"
    )

    print(
        f"MRR          "
        f"{dense_aggregate['mrr']:.4f}     "
        f"{hybrid_aggregate['mrr']:.4f}               "
        f"{reranker_aggregate['mrr']:.4f}"
    )

    print(
        f"nDCG@10      "
        f"{dense_aggregate['ndcg_at_10']:.4f}     "
        f"{hybrid_aggregate['ndcg_at_10']:.4f}               "
        f"{reranker_aggregate['ndcg_at_10']:.4f}"
    )

    print(
        f"\nReranking time          : "
        f"{total_rerank_seconds:.2f}s"
    )

    print(
        f"Reranker peak VRAM      : "
        f"{reranker_peak_vram:.2f} GB"
    )

    # ========================================================
    # Save
    # ========================================================

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_path = (
        RESULTS_DIR
        / "qwen3_reranker_0.6b_v1.json"
    )

    payload = {
        "benchmark": (
            "MedicalPlab Qwen3 reranker v1"
        ),
        "dense_model": (
            MODEL_NAME
        ),
        "sparse_model": "BM25",
        "reranker_model": (
            RERANKER_MODEL
        ),
        "reranker_instruction": (
            RERANK_INSTRUCTION
        ),
        "candidate_generation": {
            "dense_top_k": (
                RERANK_CANDIDATES_PER_RETRIEVER
            ),
            "bm25_top_k": (
                RERANK_CANDIDATES_PER_RETRIEVER
            ),
            "strategy": (
                "ordered_unique_union"
            ),
            "bm25_zero_score_filter": True,
        },
        "reranker_config": {
            "max_length": (
                RERANKER_MAX_LENGTH
            ),
            "batch_size": (
                RERANKER_BATCH_SIZE
            ),
            "dtype": "float16",
            "device": "cuda",
        },
        "candidate_recall": (
            mean_candidate_recall
        ),
        "aggregate_metrics": {
            "dense": (
                dense_aggregate
            ),
            "weighted_hybrid": (
                hybrid_aggregate
            ),
            "reranked": (
                reranker_aggregate
            ),
        },
        "runtime": {
            "dense_load_seconds": (
                dense_load_seconds
            ),
            "corpus_encode_seconds": (
                corpus_seconds
            ),
            "query_encode_seconds": (
                query_seconds
            ),
            "reranker_load_seconds": (
                reranker_load_seconds
            ),
            "reranking_seconds": (
                total_rerank_seconds
            ),
            "dense_peak_vram_gb": (
                dense_peak_vram
            ),
            "reranker_peak_vram_gb": (
                reranker_peak_vram
            ),
        },
        "per_query": (
            per_query_results
        ),
    }

    with results_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"Results saved           : "
        f"{results_path}"
    )


if __name__ == "__main__":
    main()