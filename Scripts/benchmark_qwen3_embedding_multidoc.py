import argparse
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

CHUNKS_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
    / "cardiology"
)

DEFAULT_EVAL_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "retrieval_eval_multidoc_dev_v1.json"
)

DEFAULT_DOCUMENTS = [
    "DOC-WHO-CARD-0001",
    "DOC-PMC-CARD-0002",
]

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
        "retrieval_section_path"
    )

    if (
        not isinstance(
            section_path,
            list,
        )
        or not section_path
    ):
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


def block_key(
    chunk: dict[str, Any],
) -> str:
    document_id = str(
        chunk[
            "document_id"
        ]
    )

    block_index = int(
        chunk[
            "source_block_index"
        ]
    )

    return (
        f"{document_id}"
        f":B{block_index:04d}"
    )


def rank_unique_blocks(
    chunks: list[dict[str, Any]],
    scores: np.ndarray,
) -> list[str]:
    best_score_by_block: dict[
        str,
        float,
    ] = defaultdict(
        lambda: float("-inf")
    )

    for chunk, score in zip(
        chunks,
        scores,
    ):
        key = block_key(
            chunk
        )

        score_value = float(
            score
        )

        if (
            score_value
            > best_score_by_block[
                key
            ]
        ):
            best_score_by_block[
                key
            ] = score_value

    ranked = sorted(
        best_score_by_block.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return [
        key
        for key, _
        in ranked
    ]


def reciprocal_rank(
    ranked_blocks: list[str],
    relevant_blocks: set[str],
) -> float:
    for rank, block_index in enumerate(
        ranked_blocks,
        start=1,
    ):
        if block_index in relevant_blocks:
            return 1.0 / rank

    return 0.0


def hit_at_k(
    ranked_blocks: list[str],
    relevant_blocks: set[str],
    k: int,
) -> float:
    return float(
        any(
            block in relevant_blocks
            for block in ranked_blocks[:k]
        )
    )


def recall_at_k(
    ranked_blocks: list[str],
    relevant_blocks: set[str],
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
    ranked_blocks: list[str],
    relevance_map: dict[str, int],
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
    ranked_blocks: list[str],
    relevance_map: dict[str, int],
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
    parser = argparse.ArgumentParser(
        description=(
            "Run Qwen3 dense retrieval over "
            "one or more MedicalPlab documents."
        )
    )

    parser.add_argument(
        "--documents",
        nargs="+",
        default=DEFAULT_DOCUMENTS,
        help=(
            "Document IDs whose .chunks.json "
            "files form the retrieval corpus."
        ),
    )

    parser.add_argument(
        "--eval-path",
        default=str(
            DEFAULT_EVAL_PATH
        ),
        help=(
            "Document-aware retrieval "
            "evaluation JSON."
        ),
    )

    parser.add_argument(
        "--results-name",
        default=(
            "qwen3_embedding_0.6b_"
            "multidoc_dev_v1.json"
        ),
    )

    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available."
        )

    chunks: list[
        dict[str, Any]
    ] = []

    loaded_documents: list[str] = []

    for document_id in args.documents:
        chunks_path = (
            CHUNKS_DIR
            / f"{document_id}.chunks.json"
        )

        if not chunks_path.exists():
            raise FileNotFoundError(
                f"Chunk file not found: "
                f"{chunks_path}"
            )

        chunks_document = load_json(
            chunks_path
        )

        document_chunks = (
            chunks_document.get(
                "chunks",
                [],
            )
        )

        if not isinstance(
            document_chunks,
            list,
        ):
            raise ValueError(
                f"chunks must be a list "
                f"for {document_id}."
            )

        for chunk in document_chunks:
            if not isinstance(
                chunk,
                dict,
            ):
                raise ValueError(
                    f"Invalid chunk object "
                    f"in {document_id}."
                )

            chunk_document_id = str(
                chunk.get(
                    "document_id",
                    "",
                )
            )

            if (
                chunk_document_id
                != document_id
            ):
                raise ValueError(
                    f"Chunk document mismatch: "
                    f"expected={document_id}, "
                    f"found={chunk_document_id}"
                )

        chunks.extend(
            document_chunks
        )

        loaded_documents.append(
            document_id
        )

    block_keys = [
        block_key(
            chunk
        )
        for chunk in chunks
    ]

    unique_block_keys = set(
        block_keys
    )

    evaluation = load_json(
        Path(
            args.eval_path
        )
    )

    cases = evaluation.get(
        "cases",
        [],
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
            (
                f"{item['document_id']}"
                f":B{int(item['block_index']):04d}"
            ): item["relevance"]
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
        "\\nLegacy BM25 baseline"
    )

    print("-" * 64)

    print(
        "Skipped: the stored BM25 baseline "
        "is WHO-only and is not directly "
        "comparable to this multi-document corpus."
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_path = (
        RESULTS_DIR
        / args.results_name
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
        "corpus_documents": (
            loaded_documents
        ),
        "corpus_chunks": len(
            chunks
        ),
        "corpus_unique_blocks": len(
            unique_block_keys
        ),
        "evaluation_file": str(
            Path(
                args.eval_path
            )
        ),
        "benchmark_scope": (
            "multi_document_dev_regression"
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
