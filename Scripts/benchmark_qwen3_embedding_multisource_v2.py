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
    / "retrieval_eval_multisource_dev_v2.json"
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
    "Instruct: Given a medical education query, retrieve the passages "
    "from the available medical sources that most directly support the "
    "requested claim. Respect any source explicitly requested by the "
    "query. Do not assume every query targets a guideline.\nQuery:"
)

SOURCE_LABELS = {
    "DOC-WHO-CARD-0001": (
        "World Health Organization (WHO) primary guideline: "
        "Guideline for the pharmacological treatment of "
        "hypertension in adults"
    ),
    "DOC-PMC-CARD-0002": (
        "PMC scientific review article: "
        "Outpatient management of essential hypertension: "
        "a review based on the latest clinical guidelines"
    ),
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return data


def resolve_path(value: str) -> Path:
    path = Path(value)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    return path.resolve()


def block_key(chunk: dict[str, Any]) -> str:
    return (
        f"{chunk['document_id']}"
        f":B{int(chunk['source_block_index']):04d}"
    )


def document_id_from_key(key: str) -> str:
    return key.split(":B", 1)[0]


def build_retrieval_text(
    chunk: dict[str, Any],
    include_source_labels: bool,
) -> str:
    section_path = chunk.get(
        "retrieval_section_path"
    )

    if (
        not isinstance(section_path, list)
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

    parts: list[str] = []

    if include_source_labels:
        document_id = str(
            chunk.get(
                "document_id",
                "",
            )
        )

        source_label = SOURCE_LABELS.get(
            document_id,
            document_id,
        )

        parts.append(
            f"Source document: {source_label}"
        )

    parts.extend(
        [
            (
                "Medical specialty: "
                f"{chunk.get('medical_specialty', '')}"
            ),
            f"Topics: {topic_text}",
            f"Section: {section_text}",
            (
                "Heading: "
                f"{chunk.get('heading', '')}"
            ),
            (
                "Evidence type: "
                f"{chunk.get('block_type', '')}"
            ),
            (
                "Content: "
                f"{chunk.get('text', '')}"
            ),
        ]
    )

    return "\n".join(
        part
        for part in parts
        if part.strip()
    )


def rank_unique_blocks(
    chunks: list[dict[str, Any]],
    scores: np.ndarray,
) -> list[tuple[str, float]]:
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
        key = block_key(chunk)
        score_value = float(score)

        if (
            score_value
            > best_score_by_block[key]
        ):
            best_score_by_block[
                key
            ] = score_value

    return sorted(
        best_score_by_block.items(),
        key=lambda item: item[1],
        reverse=True,
    )


def reciprocal_rank(
    ranked_blocks: list[str],
    relevant_blocks: set[str],
) -> float:
    for rank, key in enumerate(
        ranked_blocks,
        start=1,
    ):
        if key in relevant_blocks:
            return 1.0 / rank

    return 0.0


def hit_at_k(
    ranked_blocks: list[str],
    relevant_blocks: set[str],
    k: int,
) -> float:
    return float(
        any(
            key in relevant_blocks
            for key in ranked_blocks[:k]
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
            retrieved
            & relevant_blocks
        )
        / len(relevant_blocks)
    )


def dcg_at_k(
    ranked_blocks: list[str],
    relevance_map: dict[str, int],
    k: int,
) -> float:
    score = 0.0

    for rank, key in enumerate(
        ranked_blocks[:k],
        start=1,
    ):
        relevance = relevance_map.get(
            key,
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


def gold_source_recall_at_k(
    ranked_blocks: list[str],
    relevant_blocks: set[str],
    target_document_ids: set[str],
    k: int,
) -> float | None:
    if not target_document_ids:
        return None

    represented_documents = {
        document_id_from_key(key)
        for key in ranked_blocks[:k]
        if key in relevant_blocks
    }

    return (
        len(
            represented_documents
            & target_document_ids
        )
        / len(target_document_ids)
    )


def preferred_gold_hit_at_k(
    ranked_blocks: list[str],
    relevant_blocks: set[str],
    preferred_document_id: str | None,
    k: int,
) -> float | None:
    if not preferred_document_id:
        return None

    return float(
        any(
            (
                key in relevant_blocks
                and document_id_from_key(key)
                == preferred_document_id
            )
            for key in ranked_blocks[:k]
        )
    )


def mean(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return sum(values) / len(values)


def aggregate_rows(
    rows: list[dict[str, Any]],
) -> dict[str, float]:
    if not rows:
        return {}

    aggregate: dict[str, float] = {
        "cases": float(len(rows)),
        "mrr": mean(
            [
                float(row["reciprocal_rank"])
                for row in rows
            ]
        ),
        "ndcg_at_10": mean(
            [
                float(row["ndcg_at_10"])
                for row in rows
            ]
        ),
    }

    for k in TOP_K_VALUES:
        aggregate[
            f"hit_at_{k}"
        ] = mean(
            [
                float(row[f"hit_at_{k}"])
                for row in rows
            ]
        )

        aggregate[
            f"recall_at_{k}"
        ] = mean(
            [
                float(
                    row[f"recall_at_{k}"]
                )
                for row in rows
            ]
        )

        source_values = [
            float(
                row[
                    f"gold_source_recall_at_{k}"
                ]
            )
            for row in rows
            if row.get(
                f"gold_source_recall_at_{k}"
            )
            is not None
        ]

        if source_values:
            aggregate[
                f"gold_source_recall_at_{k}"
            ] = mean(source_values)

        preferred_values = [
            float(
                row[
                    f"preferred_gold_hit_at_{k}"
                ]
            )
            for row in rows
            if row.get(
                f"preferred_gold_hit_at_{k}"
            )
            is not None
        ]

        if preferred_values:
            aggregate[
                f"preferred_gold_hit_at_{k}"
            ] = mean(
                preferred_values
            )

    preferred_top1_values = [
        float(
            row[
                "top1_document_is_preferred"
            ]
        )
        for row in rows
        if row.get(
            "top1_document_is_preferred"
        )
        is not None
    ]

    if preferred_top1_values:
        aggregate[
            "top1_document_is_preferred"
        ] = mean(
            preferred_top1_values
        )

    return aggregate


def build_slices(
    rows: list[dict[str, Any]],
    field: str,
) -> dict[str, dict[str, float]]:
    values = sorted(
        {
            str(row[field])
            for row in rows
            if row.get(field) is not None
        }
    )

    return {
        value: aggregate_rows(
            [
                row
                for row in rows
                if str(
                    row.get(field)
                )
                == value
            ]
        )
        for value in values
    }


def print_aggregate(
    title: str,
    aggregate: dict[str, float],
) -> None:
    print(f"\n{title}")
    print("-" * 72)

    if not aggregate:
        print("No cases.")
        return

    print(
        f"Cases      : "
        f"{int(aggregate['cases'])}"
    )

    for k in TOP_K_VALUES:
        print(
            f"Hit@{k:<2}     : "
            f"{aggregate[f'hit_at_{k}']:.4f}"
        )
        print(
            f"Recall@{k:<2}  : "
            f"{aggregate[f'recall_at_{k}']:.4f}"
        )

    print(
        f"MRR        : "
        f"{aggregate['mrr']:.4f}"
    )
    print(
        f"nDCG@10    : "
        f"{aggregate['ndcg_at_10']:.4f}"
    )

    for k in TOP_K_VALUES:
        key = (
            f"gold_source_recall_at_{k}"
        )

        if key in aggregate:
            print(
                f"GoldSourceRecall@{k:<2}: "
                f"{aggregate[key]:.4f}"
            )

    if (
        "top1_document_is_preferred"
        in aggregate
    ):
        print(
            "PreferredDoc@1: "
            f"{aggregate['top1_document_is_preferred']:.4f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Qwen3 0.6B dense "
            "baseline on MedicalPlab Real "
            "Multi-Source Evaluation v2."
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
            "Path to the v2 multi-source "
            "evaluation JSON."
        ),
    )

    parser.add_argument(
        "--results-name",
        default=(
            "qwen3_embedding_0.6b_"
            "multisource_dev_v2_"
            "baseline.json"
        ),
        help=(
            "Output filename under "
            "evaluation/results/."
        ),
    )

    parser.add_argument(
        "--include-source-labels",
        action="store_true",
        help=(
            "Add explicit source-document "
            "descriptions to chunk retrieval "
            "text. Leave OFF for the first "
            "content-only baseline."
        ),
    )

    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available."
        )

    eval_path = resolve_path(
        args.eval_path
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

            actual_document_id = str(
                chunk.get(
                    "document_id",
                    "",
                )
            )

            if (
                actual_document_id
                != document_id
            ):
                raise ValueError(
                    "Chunk document mismatch: "
                    f"expected={document_id}, "
                    f"found={actual_document_id}"
                )

        chunks.extend(
            document_chunks
        )

        loaded_documents.append(
            document_id
        )

    evaluation = load_json(
        eval_path
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

    unsupported_cases = [
        case
        for case in cases
        if not case.get(
            "expected_answerable"
        )
    ]

    documents = [
        build_retrieval_text(
            chunk,
            include_source_labels=(
                args.include_source_labels
            ),
        )
        for chunk in chunks
    ]

    all_query_cases = (
        answerable_cases
        + unsupported_cases
    )

    queries = [
        case["query"]
        for case in all_query_cases
    ]

    print(
        "\nMedicalPlab Qwen3 "
        "Multi-Source Retrieval Benchmark"
    )
    print("=" * 72)

    print(
        f"Model              : "
        f"{MODEL_NAME}"
    )
    print(
        f"GPU                : "
        f"{torch.cuda.get_device_name(0)}"
    )
    print(
        f"Documents          : "
        f"{len(loaded_documents)}"
    )
    print(
        f"Chunks             : "
        f"{len(chunks)}"
    )
    print(
        f"Cases              : "
        f"{len(cases)}"
    )
    print(
        f"Answerable         : "
        f"{len(answerable_cases)}"
    )
    print(
        f"Unsupported        : "
        f"{len(unsupported_cases)}"
    )
    print(
        "Source labels      : "
        f"{args.include_source_labels}"
    )
    print(
        f"Evaluation         : "
        f"{eval_path}"
    )

    print(
        "\nLoading model..."
    )

    load_start = time.perf_counter()

    model = SentenceTransformer(
        MODEL_NAME,
        device="cuda",
        model_kwargs={
            "torch_dtype": (
                torch.float16
            ),
        },
        tokenizer_kwargs={
            "padding_side": "left",
        },
    )

    model.max_seq_length = 2048

    load_seconds = (
        time.perf_counter()
        - load_start
    )

    print(
        f"Model loaded       : "
        f"{load_seconds:.2f}s"
    )

    print(
        "\nEncoding corpus..."
    )

    corpus_start = (
        time.perf_counter()
    )

    document_embeddings = (
        model.encode(
            documents,
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

    print(
        f"Corpus encoded     : "
        f"{corpus_seconds:.2f}s"
    )
    print(
        f"Embedding dimension: "
        f"{document_embeddings.shape[1]}"
    )

    print(
        "\nEncoding queries..."
    )

    query_start = (
        time.perf_counter()
    )

    query_embeddings = (
        model.encode(
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

    print(
        f"Queries encoded    : "
        f"{query_seconds:.2f}s"
    )

    similarity_matrix = (
        query_embeddings
        @ document_embeddings.T
    )

    answerable_rows: list[
        dict[str, Any]
    ] = []

    unsupported_rows: list[
        dict[str, Any]
    ] = []

    print(
        "\nAnswerable per-query results"
    )
    print("-" * 150)

    for query_index, case in enumerate(
        answerable_cases
    ):
        scores = (
            similarity_matrix[
                query_index
            ]
        )

        ranked_pairs = (
            rank_unique_blocks(
                chunks,
                scores,
            )
        )

        ranked_blocks = [
            key
            for key, _
            in ranked_pairs
        ]

        relevance_map = {
            (
                f"{item['document_id']}"
                f":B{int(item['block_index']):04d}"
            ): int(
                item["relevance"]
            )
            for item in case[
                "relevant_blocks"
            ]
        }

        relevant_blocks = set(
            relevance_map
        )

        target_document_ids = {
            str(document_id)
            for document_id
            in case.get(
                "target_document_ids",
                [],
            )
        }

        preferred_document_id = (
            case.get(
                "preferred_document_id"
            )
        )

        if preferred_document_id is not None:
            preferred_document_id = str(
                preferred_document_id
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

        row: dict[str, Any] = {
            "query_id": (
                case["query_id"]
            ),
            "query": (
                case["query"]
            ),
            "language": (
                case["language"]
            ),
            "query_type": (
                case["query_type"]
            ),
            "difficulty": (
                case["difficulty"]
            ),
            "evidence_scope": (
                case.get(
                    "evidence_scope",
                    "unknown",
                )
            ),
            "target_document_ids": (
                sorted(
                    target_document_ids
                )
            ),
            "preferred_document_id": (
                preferred_document_id
            ),
            "reciprocal_rank": rr,
            "ndcg_at_10": ndcg,
            "top_10_blocks": (
                ranked_blocks[:10]
            ),
            "top_10_scores": [
                round(
                    float(score),
                    8,
                )
                for _, score
                in ranked_pairs[:10]
            ],
        }

        for k in TOP_K_VALUES:
            row[
                f"hit_at_{k}"
            ] = hit_at_k(
                ranked_blocks,
                relevant_blocks,
                k,
            )

            row[
                f"recall_at_{k}"
            ] = recall_at_k(
                ranked_blocks,
                relevant_blocks,
                k,
            )

            row[
                f"gold_source_recall_at_{k}"
            ] = (
                gold_source_recall_at_k(
                    ranked_blocks,
                    relevant_blocks,
                    target_document_ids,
                    k,
                )
            )

            row[
                f"preferred_gold_hit_at_{k}"
            ] = (
                preferred_gold_hit_at_k(
                    ranked_blocks,
                    relevant_blocks,
                    preferred_document_id,
                    k,
                )
            )

        if preferred_document_id:
            row[
                "top1_document_is_preferred"
            ] = float(
                document_id_from_key(
                    ranked_blocks[0]
                )
                == preferred_document_id
            )
        else:
            row[
                "top1_document_is_preferred"
            ] = None

        answerable_rows.append(
            row
        )

        print(
            f"{case['query_id']:<10} | "
            f"{case['evidence_scope']:<19} | "
            f"{case['language']:<5} | "
            f"RR={rr:.3f} | "
            f"nDCG@10={ndcg:.3f} | "
            f"Top5={ranked_blocks[:5]}"
        )

    unsupported_offset = len(
        answerable_cases
    )

    print(
        "\nUnsupported-query diagnostics"
    )
    print("-" * 150)

    for offset, case in enumerate(
        unsupported_cases
    ):
        query_index = (
            unsupported_offset
            + offset
        )

        scores = (
            similarity_matrix[
                query_index
            ]
        )

        ranked_pairs = (
            rank_unique_blocks(
                chunks,
                scores,
            )
        )

        top_10 = (
            ranked_pairs[:10]
        )

        top1_score = float(
            top_10[0][1]
        )

        top2_score = (
            float(top_10[1][1])
            if len(top_10) > 1
            else top1_score
        )

        row = {
            "query_id": (
                case["query_id"]
            ),
            "query": (
                case["query"]
            ),
            "language": (
                case["language"]
            ),
            "query_type": (
                case["query_type"]
            ),
            "difficulty": (
                case["difficulty"]
            ),
            "evidence_scope": (
                case.get(
                    "evidence_scope",
                    "unsupported",
                )
            ),
            "top1_score": (
                top1_score
            ),
            "top1_top2_margin": (
                top1_score
                - top2_score
            ),
            "top_10_blocks": [
                key
                for key, _
                in top_10
            ],
            "top_10_scores": [
                round(
                    float(score),
                    8,
                )
                for _, score
                in top_10
            ],
            "classification": (
                "diagnostic_only_no_threshold"
            ),
        }

        unsupported_rows.append(
            row
        )

        print(
            f"{case['query_id']:<10} | "
            f"{case['language']:<5} | "
            f"Top1Score={top1_score:.4f} | "
            f"Margin={row['top1_top2_margin']:.4f} | "
            f"Top5={[key for key, _ in top_10[:5]]}"
        )

    aggregate = aggregate_rows(
        answerable_rows
    )

    by_scope = build_slices(
        answerable_rows,
        "evidence_scope",
    )

    by_language = build_slices(
        answerable_rows,
        "language",
    )

    by_query_type = build_slices(
        answerable_rows,
        "query_type",
    )

    print_aggregate(
        "Overall answerable metrics",
        aggregate,
    )

    for scope, values in (
        by_scope.items()
    ):
        print_aggregate(
            (
                "Evidence-scope slice: "
                f"{scope}"
            ),
            values,
        )

    print(
        "\nImportant note"
    )
    print("-" * 72)
    print(
        "Unsupported cases are NOT scored "
        "as correct/incorrect here because "
        "no evidence-sufficiency threshold "
        "has been calibrated yet."
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        RESULTS_DIR
        / args.results_name
    )

    result = {
        "benchmark_id": (
            "medicalplab-qwen3-embedding-0.6b-"
            + str(
                evaluation.get(
                    "eval_set_id",
                    "unknown-evaluation",
                )
            ).removeprefix(
                "medicalplab-retrieval-"
            )
        ),
        "model": MODEL_NAME,
        "query_instruction": (
            QUERY_INSTRUCTION
        ),
        "include_source_labels": (
            args.include_source_labels
        ),
        "evaluation_set_id": (
            evaluation.get(
                "eval_set_id"
            )
        ),
        "evaluation_path": (
            eval_path.relative_to(
                PROJECT_ROOT
            ).as_posix()
            if eval_path.is_relative_to(
                PROJECT_ROOT
            )
            else str(eval_path)
        ),
        "documents": (
            loaded_documents
        ),
        "chunk_count": (
            len(chunks)
        ),
        "unique_block_count": (
            len(
                {
                    block_key(chunk)
                    for chunk in chunks
                }
            )
        ),
        "case_count": (
            len(cases)
        ),
        "answerable_count": (
            len(answerable_cases)
        ),
        "unsupported_count": (
            len(unsupported_cases)
        ),
        "timing_seconds": {
            "model_load": (
                load_seconds
            ),
            "corpus_encoding": (
                corpus_seconds
            ),
            "query_encoding": (
                query_seconds
            ),
        },
        "aggregate_answerable": (
            aggregate
        ),
        "slices": {
            "evidence_scope": (
                by_scope
            ),
            "language": (
                by_language
            ),
            "query_type": (
                by_query_type
            ),
        },
        "per_query_answerable": (
            answerable_rows
        ),
        "unsupported_diagnostics": (
            unsupported_rows
        ),
        "notes": (
            [
                (
                    "Frozen held-out benchmark; "
                    "do not tune retrieval settings "
                    "or edit gold labels from these results."
                ),
                (
                    "Unsupported cases are diagnostic only "
                    "until a separate evidence-sufficiency "
                    "threshold is calibrated."
                ),
            ]
            if "heldout"
            in str(
                evaluation.get(
                    "eval_set_id",
                    "",
                )
            ).lower()
            else [
                (
                    "Development benchmark only; "
                    "not held-out performance."
                ),
                (
                    "Unsupported cases are diagnostic only "
                    "until a separate evidence-sufficiency "
                    "threshold is calibrated."
                ),
                (
                    "Do not tune on this development set "
                    "and then report it as an independent benchmark."
                ),
            ]
        ),
    }

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    print(
        f"\nSaved results      : "
        f"{output_path}"
    )
    print(
        "Benchmark status   : PASS"
    )


if __name__ == "__main__":
    main()
