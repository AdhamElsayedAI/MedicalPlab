import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHUNKS_PATH = (
    PROJECT_ROOT
    / "Data"
    / "processed"
    / "cardiology"
    / "DOC-WHO-CARD-0001.chunks.json"
)

EVAL_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "retrieval_eval_v1.json"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "evaluation"
    / "results"
)

MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"

TOP_K_VALUES = (1, 3, 5, 10)

QUERY_INSTRUCTION = (
    "Instruct: Given a medical education query, retrieve authoritative "
    "clinical guideline passages that directly answer the question. "
    "Prioritize recommendations, implementation remarks, and supporting "
    "evidence.\nQuery:"
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return data


def build_retrieval_text(
    chunk: dict[str, Any],
) -> str:
    section_path = chunk.get(
        "section_path",
        [],
    )

    if isinstance(section_path, list):
        section_text = " > ".join(
            str(item)
            for item in section_path
        )
    else:
        section_text = str(
            section_path
        )

    topics = chunk.get(
        "topics",
        [],
    )

    if isinstance(topics, list):
        topic_text = ", ".join(
            str(item)
            for item in topics
        )
    else:
        topic_text = str(
            topics
        )

    parts = [
        f"Medical specialty: {chunk.get('medical_specialty', '')}",
        f"Topics: {topic_text}",
        f"Section: {section_text}",
        f"Heading: {chunk.get('heading', '')}",
        f"Evidence type: {chunk.get('block_type', '')}",
        f"Content: {chunk.get('text', '')}",
    ]

    return "\n".join(
        part
        for part in parts
        if part.strip()
    )


def rank_unique_blocks(
    chunks: list[dict[str, Any]],
    scores: np.ndarray,
) -> list[int]:
    best_score_by_block: dict[
        int,
        float,
    ] = defaultdict(
        lambda: float("-inf")
    )

    for chunk, score in zip(
        chunks,
        scores,
    ):
        block_index = int(
            chunk["source_block_index"]
        )

        score_value = float(
            score
        )

        if (
            score_value
            > best_score_by_block[
                block_index
            ]
        ):
            best_score_by_block[
                block_index
            ] = score_value

    ranked = sorted(
        best_score_by_block.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return [
        block_index
        for block_index, _
        in ranked
    ]


def reciprocal_rank(
    ranked_blocks: list[int],
    relevant_blocks: set[int],
) -> float:
    for rank, block_index in enumerate(
        ranked_blocks,
        start=1,
    ):
        if block_index in relevant_blocks:
            return 1.0 / rank

    return 0.0


def hit_at_k(
    ranked_blocks: list[int],
    relevant_blocks: set[int],
    k: int,
) -> float:
    return float(
        any(
            block in relevant_blocks
            for block in ranked_blocks[:k]
        )
    )


def recall_at_k(
    ranked_blocks: list[int],
    relevant_blocks: set[int],
    k: int,
) -> float:
    if not relevant_blocks:
        return 0.0

    retrieved = set(
        ranked_blocks[:k]
    )

    return (
        len(
            retrieved & relevant_blocks
        )
        / len(
            relevant_blocks
        )
    )


def dcg_at_k(
    ranked_blocks: list[int],
    relevance_map: dict[int, int],
    k: int,
) -> float:
    score = 0.0

    for rank, block_index in enumerate(
        ranked_blocks[:k],
        start=1,
    ):
        relevance = relevance_map.get(
            block_index,
            0,
        )

        if relevance <= 0:
            continue

        gain = (
            (2 ** relevance)
            - 1
        )

        discount = math.log2(
            rank + 1
        )

        score += (
            gain
            / discount
        )

    return score


def ndcg_at_k(
    ranked_blocks: list[int],
    relevance_map: dict[int, int],
    k: int,
) -> float:
    actual = dcg_at_k(
        ranked_blocks,
        relevance_map,
        k,
    )

    ideal_relevances = sorted(
        relevance_map.values(),
        reverse=True,
    )

    ideal = 0.0

    for rank, relevance in enumerate(
        ideal_relevances[:k],
        start=1,
    ):
        gain = (
            (2 ** relevance)
            - 1
        )

        discount = math.log2(
            rank + 1
        )

        ideal += (
            gain
            / discount
        )

    if ideal == 0.0:
        return 0.0

    return actual / ideal


def mean(values: list[float]) -> float:
    if not values:
        return 0.0

    return (
        sum(values)
        / len(values)
    )


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

    if not isinstance(chunks, list):
        raise ValueError(
            "chunks must be a list."
        )

    if not isinstance(cases, list):
        raise ValueError(
            "cases must be a list."
        )

    answerable_cases = [
        case
        for case in cases
        if case.get(
            "expected_answerable"
        )
    ]

    documents = [
        build_retrieval_text(
            chunk
        )
        for chunk in chunks
    ]

    print(
        "\nMedicalPlab Qwen3 Dense Retrieval Benchmark"
    )
    print("=" * 64)

    print(
        f"Model                : {MODEL_NAME}"
    )

    print(
        f"GPU                  : "
        f"{torch.cuda.get_device_name(0)}"
    )

    print(
        f"Chunks               : {len(chunks)}"
    )

    print(
        f"Answerable queries   : "
        f"{len(answerable_cases)}"
    )

    print(
        "Loading model..."
    )

    load_start = time.perf_counter()

    model = SentenceTransformer(
        MODEL_NAME,
        device="cuda",
        model_kwargs={
            "torch_dtype": torch.float16,
        },
        tokenizer_kwargs={
            "padding_side": "left",
        },
    )

    # More than enough for our current validated chunks
    # while keeping GPU memory conservative.
    model.max_seq_length = 2048

    load_seconds = (
        time.perf_counter()
        - load_start
    )

    print(
        f"Model loaded         : "
        f"{load_seconds:.2f}s"
    )

    print(
        "\nEncoding corpus..."
    )

    corpus_start = time.perf_counter()

    document_embeddings = model.encode(
        documents,
        batch_size=4,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    corpus_seconds = (
        time.perf_counter()
        - corpus_start
    )

    print(
        f"Corpus encoded       : "
        f"{corpus_seconds:.2f}s"
    )

    print(
        f"Embedding dimension  : "
        f"{document_embeddings.shape[1]}"
    )

    queries = [
        case["query"]
        for case in answerable_cases
    ]

    print(
        "\nEncoding queries..."
    )

    query_start = time.perf_counter()

    query_embeddings = model.encode(
        queries,
        prompt=QUERY_INSTRUCTION,
        batch_size=4,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    query_seconds = (
        time.perf_counter()
        - query_start
    )

    print(
        f"Queries encoded      : "
        f"{query_seconds:.2f}s"
    )

    # Because embeddings are normalized,
    # dot product == cosine similarity.
    similarity_matrix = (
        query_embeddings
        @ document_embeddings.T
    )

    hits = {
        k: []
        for k in TOP_K_VALUES
    }

    recalls = {
        k: []
        for k in TOP_K_VALUES
    }

    reciprocal_ranks: list[float] = []
    ndcg_scores: list[float] = []

    per_query_results = []

    print(
        "\nPer-query results"
    )
    print("-" * 110)

    for query_index, case in enumerate(
        answerable_cases
    ):
        scores = similarity_matrix[
            query_index
        ]

        ranked_blocks = rank_unique_blocks(
            chunks,
            scores,
        )

        relevance_map = {
            item["block_index"]: item["relevance"]
            for item in case[
                "relevant_blocks"
            ]
        }

        relevant_blocks = set(
            relevance_map
        )

        rr = reciprocal_rank(
            ranked_blocks,
            relevant_blocks,
        )

        ndcg = ndcg_at_k(
            ranked_blocks,
            relevance_map,
            10,
        )

        reciprocal_ranks.append(
            rr
        )

        ndcg_scores.append(
            ndcg
        )

        query_metrics: dict[
            str,
            float,
        ] = {}

        for k in TOP_K_VALUES:
            hit = hit_at_k(
                ranked_blocks,
                relevant_blocks,
                k,
            )

            recall = recall_at_k(
                ranked_blocks,
                relevant_blocks,
                k,
            )

            hits[k].append(
                hit
            )

            recalls[k].append(
                recall
            )

            query_metrics[
                f"hit_at_{k}"
            ] = hit

            query_metrics[
                f"recall_at_{k}"
            ] = recall

        top5 = ranked_blocks[:5]

        print(
            f"{case['query_id']:<9} | "
            f"{case['language']:<5} | "
            f"RR={rr:.3f} | "
            f"nDCG@10={ndcg:.3f} | "
            f"Top5={top5}"
        )

        per_query_results.append(
            {
                "query_id": case[
                    "query_id"
                ],
                "language": case[
                    "language"
                ],
                "query_type": case[
                    "query_type"
                ],
                "query": case[
                    "query"
                ],
                "top_10_blocks": (
                    ranked_blocks[:10]
                ),
                "reciprocal_rank": rr,
                "ndcg_at_10": ndcg,
                **query_metrics,
            }
        )

    aggregate = {}

    print(
        "\nAggregate metrics"
    )
    print("-" * 64)

    for k in TOP_K_VALUES:
        mean_hit = mean(
            hits[k]
        )

        mean_recall = mean(
            recalls[k]
        )

        aggregate[
            f"hit_at_{k}"
        ] = mean_hit

        aggregate[
            f"recall_at_{k}"
        ] = mean_recall

        print(
            f"Hit@{k:<2}       : "
            f"{mean_hit:.4f}"
        )

        print(
            f"Recall@{k:<2}    : "
            f"{mean_recall:.4f}"
        )

    mean_rr = mean(
        reciprocal_ranks
    )

    mean_ndcg = mean(
        ndcg_scores
    )

    aggregate[
        "mrr"
    ] = mean_rr

    aggregate[
        "ndcg_at_10"
    ] = mean_ndcg

    print(
        f"MRR          : "
        f"{mean_rr:.4f}"
    )

    print(
        f"nDCG@10      : "
        f"{mean_ndcg:.4f}"
    )

    print(
        "\nBM25 baseline"
    )
    print("-" * 64)

    print(
        "Hit@1        : 0.6364"
    )

    print(
        "Recall@5     : 0.6742"
    )

    print(
        "Recall@10    : 0.8485"
    )

    print(
        "MRR          : 0.7400"
    )

    print(
        "nDCG@10      : 0.6831"
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_path = (
        RESULTS_DIR
        / "qwen3_embedding_0.6b_v1.json"
    )

    results = {
        "model": MODEL_NAME,
        "dtype": "float16",
        "device": "cuda",
        "embedding_dimension": int(
            document_embeddings.shape[1]
        ),
        "query_instruction": (
            QUERY_INSTRUCTION
        ),
        "corpus_chunks": len(
            chunks
        ),
        "answerable_queries": len(
            answerable_cases
        ),
        "aggregate_metrics": aggregate,
        "per_query": per_query_results,
    }

    with results_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    peak_vram = (
        torch.cuda.max_memory_allocated()
        / 1024**3
    )

    print(
        f"\nPeak CUDA memory : "
        f"{peak_vram:.2f} GB"
    )

    print(
        f"Results saved    : "
        f"{results_path}"
    )


if __name__ == "__main__":
    main()