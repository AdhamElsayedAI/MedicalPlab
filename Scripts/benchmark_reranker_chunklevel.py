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

# Keep the frozen hybrid benchmark configuration.
HYBRID_CANDIDATES_PER_RETRIEVER = 30

# Candidate pool passed to reranker.
RERANK_CANDIDATES_PER_RETRIEVER = 20

RERANKER_MAX_LENGTH = 2048
RERANKER_BATCH_SIZE = 2


# ============================================================
# Helpers
# ============================================================

def ordered_union(
    *rankings: list[int],
) -> list[int]:
    """
    Merge rankings while preserving first appearance
    and removing duplicate block indexes.
    """

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


def group_chunks_by_block(
    chunks: list[dict[str, Any]],
) -> dict[
    int,
    list[dict[str, Any]],
]:
    """
    Group retrieval chunks by their source block and
    preserve the original chunk order inside each block.
    """

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

    for block_index in grouped:
        grouped[
            block_index
        ] = sorted(
            grouped[
                block_index
            ],
            key=lambda chunk: int(
                chunk[
                    "chunk_index"
                ]
            ),
        )

    return dict(
        grouped
    )


def build_reranker_chunk_text(
    chunk: dict[str, Any],
) -> str:
    """
    Build one focused passage for one retrieval chunk.

    IMPORTANT:
    We intentionally do NOT reconstruct the entire source
    block here. The reranker scores each chunk independently.
    """

    section = section_path_to_text(
        chunk.get(
            "section_path",
            [],
        )
    )

    specialty = str(
        chunk.get(
            "medical_specialty",
            "",
        )
    )

    heading = str(
        chunk.get(
            "heading",
            "",
        )
    )

    block_type = str(
        chunk.get(
            "block_type",
            "",
        )
    )

    content = str(
        chunk.get(
            "text",
            "",
        )
    ).strip()

    return (
        f"Medical specialty: {specialty}\n"
        f"Section: {section}\n"
        f"Heading: {heading}\n"
        f"Evidence type: {block_type}\n"
        f"Content: {content}"
    )


def candidate_recall(
    candidates: list[int],
    relevant_blocks: set[int],
) -> float:
    """
    Measures whether the high-recall candidate generation
    stage contains the gold source blocks.
    """

    if not relevant_blocks:
        return 0.0

    retrieved = set(
        candidates
    )

    return (
        len(
            retrieved
            & relevant_blocks
        )
        / len(
            relevant_blocks
        )
    )


# ============================================================
# Chunk-level reranking
# ============================================================

def rerank_chunks_and_aggregate_blocks(
    reranker: CrossEncoder,
    query: str,
    candidate_blocks: list[int],
    chunks_by_block: dict[
        int,
        list[dict[str, Any]],
    ],
) -> tuple[
    list[int],
    dict[int, float],
    dict[int, str],
    dict[str, float],
    int,
]:
    """
    Rerank individual chunks.

    Then aggregate chunk scores into a source-block score
    using MAX pooling:

        final block score =
            highest reranker score among its chunks

    Returns:
        ranked_blocks
        block_score_map
        best_chunk_by_block
        chunk_score_map
        total_candidate_chunks
    """

    candidate_chunks: list[
        dict[str, Any]
    ] = []

    # Preserve candidate block ordering for deterministic
    # tie-breaking later.
    candidate_block_rank = {
        block_index: rank
        for rank, block_index in enumerate(
            candidate_blocks,
            start=1,
        )
    }

    for block_index in candidate_blocks:
        block_chunks = chunks_by_block.get(
            block_index,
            [],
        )

        candidate_chunks.extend(
            block_chunks
        )

    if not candidate_chunks:
        return (
            [],
            {},
            {},
            {},
            0,
        )

    pairs = [
        (
            query,
            build_reranker_chunk_text(
                chunk
            ),
        )
        for chunk in candidate_chunks
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
        != len(candidate_chunks)
    ):
        raise RuntimeError(
            "Reranker score count does not match "
            "candidate chunk count."
        )

    block_score_map: dict[
        int,
        float,
    ] = {}

    best_chunk_by_block: dict[
        int,
        str,
    ] = {}

    chunk_score_map: dict[
        str,
        float,
    ] = {}

    for chunk, score in zip(
        candidate_chunks,
        scores_array,
    ):
        score_value = float(
            score
        )

        block_index = int(
            chunk[
                "source_block_index"
            ]
        )

        chunk_id = str(
            chunk[
                "chunk_id"
            ]
        )

        chunk_score_map[
            chunk_id
        ] = score_value

        previous_score = (
            block_score_map.get(
                block_index
            )
        )

        if (
            previous_score is None
            or score_value
            > previous_score
        ):
            block_score_map[
                block_index
            ] = score_value

            best_chunk_by_block[
                block_index
            ] = chunk_id

    ranked_blocks = sorted(
        block_score_map,
        key=lambda block_index: (
            -block_score_map[
                block_index
            ],
            candidate_block_rank.get(
                block_index,
                10**9,
            ),
            block_index,
        ),
    )

    return (
        ranked_blocks,
        block_score_map,
        best_chunk_by_block,
        chunk_score_map,
        len(candidate_chunks),
    )


# ============================================================
# Main
# ============================================================

def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available."
        )

    # ========================================================
    # Load data
    # ========================================================

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

    chunks_by_block = (
        group_chunks_by_block(
            chunks
        )
    )

    # ========================================================
    # Header
    # ========================================================

    print(
        "\nMedicalPlab Chunk-Level Reranker Benchmark v2"
    )

    print("=" * 92)

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
        "Reranking granularity   : Chunk-level"
    )

    print(
        "Block aggregation       : MAX chunk score"
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
        f"{len(chunks_by_block)}"
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

    tokenized_bm25_documents = [
        tokenize(
            text
        )
        for text in bm25_documents
    ]

    bm25 = BM25(
        tokenized_bm25_documents
    )

    # ========================================================
    # Dense model
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

    # ========================================================
    # Corpus embeddings
    # ========================================================

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
        for case in answerable_cases
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
    # Freeze retrieval candidates before loading reranker
    # ========================================================

    retrieval_data: list[
        dict[str, Any]
    ] = []

    for query_index, case in enumerate(
        answerable_cases
    ):
        # ----------------------------------------------------
        # Dense block ranking
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Sparse block ranking
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Frozen weighted-hybrid ranking for comparison
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # SAME candidate generation as reranker v1
        # ----------------------------------------------------

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

        retrieval_data.append(
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
                "candidate_blocks": (
                    candidate_blocks
                ),
            }
        )

    # ========================================================
    # Release embedding model before loading reranker
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
    # Metric stores
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

    candidate_chunk_counts: list[
        int
    ] = []

    per_query_results: list[
        dict[str, Any]
    ] = []

    reranking_start = (
        time.perf_counter()
    )

    # ========================================================
    # Evaluate
    # ========================================================

    print(
        "\nPer-query results"
    )

    print("-" * 155)

    for item in retrieval_data:
        case = item[
            "case"
        ]

        dense_ranking = item[
            "dense_ranking"
        ]

        hybrid_ranking = item[
            "hybrid_ranking"
        ]

        candidate_blocks = item[
            "candidate_blocks"
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
            candidate_blocks,
            relevant_blocks,
        )

        candidate_recalls.append(
            coverage
        )

        (
            reranked_blocks,
            block_score_map,
            best_chunk_by_block,
            chunk_score_map,
            candidate_chunk_count,
        ) = rerank_chunks_and_aggregate_blocks(
            reranker=reranker,
            query=case[
                "query"
            ],
            candidate_blocks=(
                candidate_blocks
            ),
            chunks_by_block=(
                chunks_by_block
            ),
        )

        candidate_chunk_counts.append(
            candidate_chunk_count
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
                reranked_blocks,
                relevant_blocks,
                relevance_map,
            )
        )

        top5_details = [
            (
                block_index,
                best_chunk_by_block.get(
                    block_index,
                    "",
                ),
            )
            for block_index
            in reranked_blocks[:5]
        ]

        print(
            f"{case['query_id']:<9} | "
            f"{case['language']:<5} | "
            f"Blocks={len(candidate_blocks):<2} | "
            f"Chunks={candidate_chunk_count:<2} | "
            f"GoldCoverage={coverage:.3f} | "
            f"RR="
            f"{reranker_metrics['reciprocal_rank']:.3f} | "
            f"nDCG@10="
            f"{reranker_metrics['ndcg_at_10']:.3f} | "
            f"Top5={reranked_blocks[:5]}"
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
                    candidate_blocks
                ),
                "candidate_block_count": (
                    len(
                        candidate_blocks
                    )
                ),
                "candidate_chunk_count": (
                    candidate_chunk_count
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
                    reranked_blocks[:10]
                ),
                "best_chunk_per_top_block": {
                    str(
                        block_index
                    ): best_chunk_by_block.get(
                        block_index
                    )
                    for block_index
                    in reranked_blocks[:10]
                },
                "block_scores_top_10": {
                    str(
                        block_index
                    ): block_score_map[
                        block_index
                    ]
                    for block_index
                    in reranked_blocks[:10]
                },
                "top5_block_chunk_pairs": (
                    top5_details
                ),
                "dense_metrics": (
                    dense_metrics
                ),
                "hybrid_metrics": (
                    hybrid_metrics
                ),
                "reranker_metrics": (
                    reranker_metrics
                ),
                "chunk_scores": (
                    chunk_score_map
                ),
            }
        )

    reranking_seconds = (
        time.perf_counter()
        - reranking_start
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

    mean_candidate_chunks = (
        sum(
            candidate_chunk_counts
        )
        / len(
            candidate_chunk_counts
        )
        if candidate_chunk_counts
        else 0.0
    )

    reranker_peak_vram = (
        torch.cuda.max_memory_allocated()
        / 1024**3
    )

    # ========================================================
    # Results
    # ========================================================

    print(
        "\nCandidate Stage"
    )

    print("-" * 92)

    print(
        f"Mean gold candidate recall : "
        f"{mean_candidate_recall:.4f}"
    )

    print(
        f"Mean candidate chunks      : "
        f"{mean_candidate_chunks:.2f}"
    )

    print(
        "\nFinal Comparison"
    )

    print("-" * 92)

    print(
        "Metric       Dense      Weighted Hybrid      Chunk Reranker v2"
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
        f"{reranking_seconds:.2f}s"
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
        / "qwen3_reranker_chunklevel_0.6b_v2.json"
    )

    payload = {
        "benchmark": (
            "MedicalPlab Qwen3 chunk-level reranker v2"
        ),
        "dense_model": (
            MODEL_NAME
        ),
        "sparse_model": "BM25",
        "reranker_model": (
            RERANKER_MODEL
        ),
        "reranking_strategy": {
            "granularity": "chunk",
            "block_aggregation": (
                "maximum_chunk_score"
            ),
            "reranker_instruction": (
                RERANK_INSTRUCTION
            ),
        },
        "candidate_generation": {
            "dense_top_k": (
                RERANK_CANDIDATES_PER_RETRIEVER
            ),
            "bm25_top_k": (
                RERANK_CANDIDATES_PER_RETRIEVER
            ),
            "strategy": (
                "ordered_unique_block_union"
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
        "mean_candidate_chunks": (
            mean_candidate_chunks
        ),
        "aggregate_metrics": {
            "dense": (
                dense_aggregate
            ),
            "weighted_hybrid": (
                hybrid_aggregate
            ),
            "chunk_reranked": (
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
                reranking_seconds
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