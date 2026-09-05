from __future__ import annotations

import hashlib
import json
import math
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

import numpy as np
import torch
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CALIBRATION_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "evidence_sufficiency_calibration_v1.json"
)

CHUNKS_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
    / "cardiology"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "evaluation"
    / "results"
)

RESULTS_PATH = (
    RESULTS_DIR
    / "evidence_sufficiency_retrieval_only_baseline_v1.json"
)

EXPECTED_CALIBRATION_SHA256 = (
    "4ece4e35de1f46888f75f4dcae624e34b8e8f2696959f162a5f434615b021ad5"
)

MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"

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

RUNTIME_FEATURES_HIGHER_IS_MORE_SUPPORTED = (
    "top1_score",
    "top2_score",
    "top1_top2_margin",
    "top3_mean",
    "top5_mean",
    "top1_minus_top5_mean",
    "requested_source_present_at_1",
    "requested_source_present_at_5",
)

DIAGNOSTIC_ONLY_FEATURES = (
    "top5_std",
    "distinct_documents_in_top5",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return data


def block_key(
    chunk: dict[str, Any],
) -> str:
    return (
        f"{chunk['document_id']}"
        f":B{int(chunk['source_block_index']):04d}"
    )


def document_id_from_key(
    key: str,
) -> str:
    return key.split(
        ":B",
        1,
    )[0]


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

    if isinstance(
        section_path,
        list,
    ):
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

    if isinstance(
        topics,
        list,
    ):
        topic_text = ", ".join(
            str(item)
            for item in topics
        )
    else:
        topic_text = str(
            topics
        )

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

    parts = [
        (
            "Source document: "
            f"{source_label}"
        ),
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
        key = block_key(
            chunk
        )
        value = float(
            score
        )

        if (
            value
            > best_score_by_block[key]
        ):
            best_score_by_block[
                key
            ] = value

    return sorted(
        best_score_by_block.items(),
        key=lambda item: item[1],
        reverse=True,
    )


def binary_target(
    support_label: str,
) -> int:
    return int(
        support_label
        == "supported"
    )


def finite_feature_pairs(
    rows: list[dict[str, Any]],
    feature: str,
) -> tuple[list[float], list[int]]:
    scores: list[float] = []
    labels: list[int] = []

    for row in rows:
        value = row.get(
            feature
        )

        if value is None:
            continue

        value_float = float(
            value
        )

        if not math.isfinite(
            value_float
        ):
            continue

        scores.append(
            value_float
        )
        labels.append(
            int(
                row[
                    "binary_full_support_target"
                ]
            )
        )

    return (
        scores,
        labels,
    )


def auroc_pairwise(
    scores: list[float],
    labels: list[int],
) -> float | None:
    positives = [
        score
        for score, label in zip(
            scores,
            labels,
        )
        if label == 1
    ]

    negatives = [
        score
        for score, label in zip(
            scores,
            labels,
        )
        if label == 0
    ]

    if (
        not positives
        or not negatives
    ):
        return None

    wins = 0.0
    total = 0

    for positive in positives:
        for negative in negatives:
            total += 1

            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5

    return (
        wins
        / total
    )


def average_precision(
    scores: list[float],
    labels: list[int],
) -> float | None:
    positives = sum(
        labels
    )

    if positives == 0:
        return None

    thresholds = sorted(
        set(scores),
        reverse=True,
    )

    previous_recall = 0.0
    ap = 0.0

    for threshold in thresholds:
        tp = 0
        fp = 0

        for score, label in zip(
            scores,
            labels,
        ):
            if score >= threshold:
                if label == 1:
                    tp += 1
                else:
                    fp += 1

        if tp == 0:
            continue

        precision = (
            tp
            / (tp + fp)
        )

        recall = (
            tp
            / positives
        )

        ap += (
            recall
            - previous_recall
        ) * precision

        previous_recall = recall

    return ap


def summarize_values(
    values: list[float],
) -> dict[str, float] | None:
    if not values:
        return None

    return {
        "count": float(
            len(values)
        ),
        "min": float(
            min(values)
        ),
        "max": float(
            max(values)
        ),
        "mean": float(
            mean(values)
        ),
        "median": float(
            median(values)
        ),
    }


def feature_distributions(
    rows: list[dict[str, Any]],
    feature: str,
) -> dict[str, Any]:
    output: dict[
        str,
        Any,
    ] = {}

    for label in (
        "supported",
        "partial",
        "unsupported",
    ):
        values = []

        for row in rows:
            if (
                row[
                    "support_label"
                ]
                != label
            ):
                continue

            value = row.get(
                feature
            )

            if value is None:
                continue

            value_float = float(
                value
            )

            if math.isfinite(
                value_float
            ):
                values.append(
                    value_float
                )

        output[
            label
        ] = summarize_values(
            values
        )

    return output


def threshold_metrics(
    rows: list[dict[str, Any]],
    threshold: float,
) -> dict[str, Any]:
    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for row in rows:
        accepted = (
            float(
                row[
                    "top1_score"
                ]
            )
            >= threshold
        )

        target = int(
            row[
                "binary_full_support_target"
            ]
        )

        if accepted and target == 1:
            tp += 1
        elif accepted and target == 0:
            fp += 1
        elif (
            not accepted
            and target == 0
        ):
            tn += 1
        else:
            fn += 1

    total = len(
        rows
    )

    positives = (
        tp
        + fn
    )

    negatives = (
        tn
        + fp
    )

    accepted_count = (
        tp
        + fp
    )

    supported_accept_precision = (
        tp
        / accepted_count
        if accepted_count
        else None
    )

    coverage = (
        accepted_count
        / total
        if total
        else 0.0
    )

    unsafe_accept_rate = (
        fp
        / negatives
        if negatives
        else None
    )

    false_refusal_rate = (
        fn
        / positives
        if positives
        else None
    )

    supported_recall = (
        tp
        / positives
        if positives
        else None
    )

    return {
        "threshold": (
            threshold
        ),
        "accepted": (
            accepted_count
        ),
        "coverage": (
            coverage
        ),
        "tp_supported_accept": (
            tp
        ),
        "fp_non_supported_accept": (
            fp
        ),
        "tn_non_supported_reject": (
            tn
        ),
        "fn_supported_reject": (
            fn
        ),
        "supported_accept_precision": (
            supported_accept_precision
        ),
        "supported_recall": (
            supported_recall
        ),
        "unsafe_accept_rate": (
            unsafe_accept_rate
        ),
        "false_refusal_rate": (
            false_refusal_rate
        ),
    }


def risk_coverage_curve(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    thresholds = sorted(
        {
            float(
                row[
                    "top1_score"
                ]
            )
            for row in rows
        },
        reverse=True,
    )

    curve = []

    for threshold in thresholds:
        accepted = [
            row
            for row in rows
            if float(
                row[
                    "top1_score"
                ]
            )
            >= threshold
        ]

        accepted_count = len(
            accepted
        )

        false_accepts = sum(
            1
            for row in accepted
            if int(
                row[
                    "binary_full_support_target"
                ]
            )
            == 0
        )

        risk = (
            false_accepts
            / accepted_count
        )

        coverage = (
            accepted_count
            / len(rows)
        )

        curve.append(
            {
                "accepted": (
                    accepted_count
                ),
                "coverage": (
                    coverage
                ),
                "risk_non_supported_among_accepted": (
                    risk
                ),
                "threshold_at_boundary": (
                    threshold
                ),
            }
        )

    return curve


def contrastive_top1_diagnostics(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    groups: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(
        list
    )

    for row in rows:
        group_id = row.get(
            "contrast_group_id"
        )

        if not group_id:
            continue

        groups[
            str(group_id)
        ].append(
            row
        )

    pair_count = 0
    violations = 0
    details = []

    for group_id, group_rows in sorted(
        groups.items()
    ):
        supported_rows = [
            row
            for row in group_rows
            if row[
                "support_label"
            ]
            == "supported"
        ]

        negative_rows = [
            row
            for row in group_rows
            if row[
                "support_label"
            ]
            != "supported"
        ]

        for supported in supported_rows:
            for negative in negative_rows:
                pair_count += 1

                supported_score = float(
                    supported[
                        "top1_score"
                    ]
                )

                negative_score = float(
                    negative[
                        "top1_score"
                    ]
                )

                violation = (
                    negative_score
                    >= supported_score
                )

                violations += int(
                    violation
                )

                details.append(
                    {
                        "contrast_group_id": (
                            group_id
                        ),
                        "supported_case_id": (
                            supported[
                                "case_id"
                            ]
                        ),
                        "negative_case_id": (
                            negative[
                                "case_id"
                            ]
                        ),
                        "supported_top1_score": (
                            supported_score
                        ),
                        "negative_top1_score": (
                            negative_score
                        ),
                        "negative_ge_supported": (
                            violation
                        ),
                    }
                )

    return {
        "pair_count": (
            pair_count
        ),
        "violations": (
            violations
        ),
        "violation_rate": (
            violations
            / pair_count
            if pair_count
            else None
        ),
        "details": (
            details
        ),
    }


def main() -> None:
    print(
        "\nMedicalPlab Retrieval-Only "
        "Evidence Sufficiency Baseline v1"
    )
    print(
        "=" * 76
    )

    if not CALIBRATION_PATH.exists():
        raise FileNotFoundError(
            f"Missing calibration file: "
            f"{CALIBRATION_PATH}"
        )

    actual_calibration_sha = (
        sha256_file(
            CALIBRATION_PATH
        )
    )

    if (
        actual_calibration_sha
        != EXPECTED_CALIBRATION_SHA256
    ):
        raise RuntimeError(
            "Calibration SHA-256 mismatch.\n"
            f"Expected: "
            f"{EXPECTED_CALIBRATION_SHA256}\n"
            f"Actual:   "
            f"{actual_calibration_sha}"
        )

    calibration = load_json(
        CALIBRATION_PATH
    )

    cases = calibration.get(
        "cases",
        [],
    )

    if (
        not isinstance(
            cases,
            list,
        )
        or len(cases)
        != 48
    ):
        raise RuntimeError(
            "Expected exactly 48 "
            "calibration cases."
        )

    label_counts = {
        label: sum(
            1
            for case in cases
            if case.get(
                "support_label"
            )
            == label
        )
        for label in (
            "supported",
            "partial",
            "unsupported",
        )
    }

    if label_counts != {
        "supported": 20,
        "partial": 12,
        "unsupported": 16,
    }:
        raise RuntimeError(
            "Unexpected calibration label "
            f"distribution: {label_counts}"
        )

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is required to match "
            "the selected retrieval baseline."
        )

    chunks: list[
        dict[str, Any]
    ] = []

    document_ids = calibration.get(
        "corpus_document_ids",
        [],
    )

    for document_id in document_ids:
        chunks_path = (
            CHUNKS_DIR
            / f"{document_id}.chunks.json"
        )

        if not chunks_path.exists():
            raise FileNotFoundError(
                f"Missing chunks file: "
                f"{chunks_path}"
            )

        chunk_document = load_json(
            chunks_path
        )

        document_chunks = (
            chunk_document.get(
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
                f"for {document_id}"
            )

        for chunk in document_chunks:
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

    if len(chunks) != 227:
        raise RuntimeError(
            "Expected 227 chunks in the "
            f"current corpus, found {len(chunks)}."
        )

    unique_block_count = len(
        {
            block_key(
                chunk
            )
            for chunk in chunks
        }
    )

    if unique_block_count != 192:
        raise RuntimeError(
            "Expected 192 unique source blocks, "
            f"found {unique_block_count}."
        )

    print(
        f"Calibration SHA   : "
        f"{actual_calibration_sha}"
    )
    print(
        f"Cases             : "
        f"{len(cases)}"
    )
    print(
        "Labels            : "
        "supported=20, partial=12, "
        "unsupported=16"
    )
    print(
        f"Corpus            : "
        f"{len(chunks)} chunks / "
        f"{unique_block_count} blocks"
    )
    print(
        f"Model             : "
        f"{MODEL_NAME}"
    )
    print(
        f"GPU               : "
        f"{torch.cuda.get_device_name(0)}"
    )
    print(
        "Representation    : "
        "source-aware"
    )
    print(
        "Binary target     : "
        "supported=full-accept; "
        "partial+unsupported=do-not-full-accept"
    )

    documents = [
        build_retrieval_text(
            chunk
        )
        for chunk in chunks
    ]

    queries = [
        str(
            case[
                "query"
            ]
        )
        for case in cases
    ]

    print(
        "\nLoading embedding model..."
    )

    load_start = (
        time.perf_counter()
    )

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

    print(
        "Model loaded      : "
        f"{time.perf_counter() - load_start:.2f}s"
    )

    print(
        "\nEncoding corpus..."
    )

    document_embeddings = model.encode(
        documents,
        batch_size=4,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    print(
        "\nEncoding calibration queries..."
    )

    query_embeddings = model.encode(
        queries,
        prompt=QUERY_INSTRUCTION,
        batch_size=4,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    similarity_matrix = (
        query_embeddings
        @ document_embeddings.T
    )

    rows: list[
        dict[str, Any]
    ] = []

    print(
        "\nPer-case retrieval confidence"
    )
    print(
        "-" * 126
    )

    for index, case in enumerate(
        cases
    ):
        ranked_pairs = (
            rank_unique_blocks(
                chunks,
                similarity_matrix[
                    index
                ],
            )
        )

        if len(ranked_pairs) < 5:
            raise RuntimeError(
                "Need at least five unique "
                "ranked blocks per case."
            )

        top5 = ranked_pairs[
            :5
        ]

        top_scores = [
            float(
                score
            )
            for _, score
            in top5
        ]

        top1_score = (
            top_scores[0]
        )

        top2_score = (
            top_scores[1]
        )

        top3_scores = (
            top_scores[:3]
        )

        top5_mean = float(
            np.mean(
                top_scores
            )
        )

        top5_std = float(
            np.std(
                top_scores,
                ddof=0,
            )
        )

        top_blocks = [
            key
            for key, _
            in ranked_pairs[:10]
        ]

        required_document_id = (
            case.get(
                "required_document_id"
            )
        )

        if (
            isinstance(
                required_document_id,
                str,
            )
            and required_document_id
        ):
            requested_source_present_at_1 = int(
                document_id_from_key(
                    top_blocks[0]
                )
                == required_document_id
            )

            requested_source_present_at_5 = int(
                any(
                    document_id_from_key(
                        key
                    )
                    == required_document_id
                    for key
                    in top_blocks[:5]
                )
            )
        else:
            requested_source_present_at_1 = None
            requested_source_present_at_5 = None

        distinct_documents_in_top5 = len(
            {
                document_id_from_key(
                    key
                )
                for key
                in top_blocks[:5]
            }
        )

        row = {
            "case_id": (
                case[
                    "case_id"
                ]
            ),
            "query": (
                case[
                    "query"
                ]
            ),
            "language": (
                case[
                    "language"
                ]
            ),
            "difficulty": (
                case[
                    "difficulty"
                ]
            ),
            "claim_type": (
                case[
                    "claim_type"
                ]
            ),
            "support_label": (
                case[
                    "support_label"
                ]
            ),
            "expected_action": (
                case[
                    "expected_action"
                ]
            ),
            "negative_type": (
                case.get(
                    "negative_type"
                )
            ),
            "hard_negative": (
                case.get(
                    "hard_negative"
                )
            ),
            "contrast_group_id": (
                case.get(
                    "contrast_group_id"
                )
            ),
            "required_document_id": (
                required_document_id
            ),
            "binary_full_support_target": (
                binary_target(
                    str(
                        case[
                            "support_label"
                        ]
                    )
                )
            ),
            "top1_score": (
                top1_score
            ),
            "top2_score": (
                top2_score
            ),
            "top1_top2_margin": (
                top1_score
                - top2_score
            ),
            "top3_mean": float(
                np.mean(
                    top3_scores
                )
            ),
            "top5_mean": (
                top5_mean
            ),
            "top5_std": (
                top5_std
            ),
            "top1_minus_top5_mean": (
                top1_score
                - top5_mean
            ),
            "requested_source_present_at_1": (
                requested_source_present_at_1
            ),
            "requested_source_present_at_5": (
                requested_source_present_at_5
            ),
            "distinct_documents_in_top5": (
                distinct_documents_in_top5
            ),
            "top_10_blocks": (
                top_blocks
            ),
            "top_10_scores": [
                float(
                    score
                )
                for _, score
                in ranked_pairs[:10]
            ],
        }

        rows.append(
            row
        )

        print(
            f"{row['case_id']:<12} | "
            f"{row['support_label']:<11} | "
            f"top1={row['top1_score']:.6f} | "
            f"margin={row['top1_top2_margin']:.6f} | "
            f"top5mean={row['top5_mean']:.6f} | "
            f"top1={row['top_10_blocks'][0]}"
        )

    univariate = {}

    for feature in (
        RUNTIME_FEATURES_HIGHER_IS_MORE_SUPPORTED
    ):
        scores, labels = (
            finite_feature_pairs(
                rows,
                feature,
            )
        )

        univariate[
            feature
        ] = {
            "n": (
                len(scores)
            ),
            "direction": (
                "higher_is_more_supported"
            ),
            "auroc": (
                auroc_pairwise(
                    scores,
                    labels,
                )
            ),
            "auprc_average_precision": (
                average_precision(
                    scores,
                    labels,
                )
            ),
            "distributions": (
                feature_distributions(
                    rows,
                    feature,
                )
            ),
        }

    diagnostics = {}

    for feature in (
        DIAGNOSTIC_ONLY_FEATURES
    ):
        diagnostics[
            feature
        ] = {
            "direction": (
                "diagnostic_only_no_assumed_monotonic_direction"
            ),
            "distributions": (
                feature_distributions(
                    rows,
                    feature,
                )
            ),
        }

    unique_top1_scores = sorted(
        {
            float(
                row[
                    "top1_score"
                ]
            )
            for row in rows
        },
        reverse=True,
    )

    max_top1_score = max(
        unique_top1_scores
    )

    min_top1_score = min(
        unique_top1_scores
    )

    accept_none_threshold = math.nextafter(
        max_top1_score,
        math.inf,
    )

    accept_all_threshold = math.nextafter(
        min_top1_score,
        -math.inf,
    )

    threshold_rows = [
        threshold_metrics(
            rows,
            accept_none_threshold,
        )
    ]

    threshold_rows.extend(
        threshold_metrics(
            rows,
            threshold,
        )
        for threshold
        in unique_top1_scores
    )

    threshold_rows.append(
        threshold_metrics(
            rows,
            accept_all_threshold,
        )
    )

    zero_observed_unsafe_candidates = [
        row
        for row in threshold_rows
        if (
            row[
                "accepted"
            ]
            > 0
            and row[
                "fp_non_supported_accept"
            ]
            == 0
        )
    ]

    best_zero_observed_unsafe = (
        max(
            zero_observed_unsafe_candidates,
            key=lambda row: (
                row[
                    "coverage"
                ]
            ),
        )
        if zero_observed_unsafe_candidates
        else None
    )

    top1_scores, binary_labels = (
        finite_feature_pairs(
            rows,
            "top1_score",
        )
    )

    contrastive = (
        contrastive_top1_diagnostics(
            rows
        )
    )

    results = {
        "baseline_id": (
            "medicalplab-evidence-sufficiency-"
            "retrieval-only-baseline-v1"
        ),
        "version": (
            "1.0.0"
        ),
        "generated_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "status": (
            "calibration_experiment_not_final_test"
        ),
        "calibration": {
            "file": (
                "evaluation/"
                "evidence_sufficiency_"
                "calibration_v1.json"
            ),
            "sha256": (
                actual_calibration_sha
            ),
            "cases": (
                len(cases)
            ),
            "labels": (
                label_counts
            ),
            "binary_policy": (
                "supported is positive/full-accept; "
                "partial and unsupported are negative/"
                "do-not-full-accept"
            ),
        },
        "retrieval": {
            "model": (
                MODEL_NAME
            ),
            "device": (
                "cuda"
            ),
            "dtype": (
                "float16"
            ),
            "max_seq_length": (
                2048
            ),
            "normalize_embeddings": (
                True
            ),
            "source_aware": (
                True
            ),
            "query_instruction": (
                QUERY_INSTRUCTION
            ),
            "corpus_document_ids": (
                document_ids
            ),
            "chunk_count": (
                len(chunks)
            ),
            "unique_block_count": (
                unique_block_count
            ),
        },
        "primary_retrieval_only_signal": {
            "feature": (
                "top1_score"
            ),
            "auroc": (
                auroc_pairwise(
                    top1_scores,
                    binary_labels,
                )
            ),
            "auprc_average_precision": (
                average_precision(
                    top1_scores,
                    binary_labels,
                )
            ),
            "best_zero_observed_unsafe_accept_point": (
                best_zero_observed_unsafe
            ),
            "note": (
                "This is calibration-set behavior only. "
                "Zero observed unsafe accepts on 48 "
                "calibration cases must not be treated "
                "as a general safety guarantee."
            ),
        },
        "univariate_runtime_features": (
            univariate
        ),
        "diagnostic_features": (
            diagnostics
        ),
        "contrastive_top1_diagnostics": (
            contrastive
        ),
        "top1_threshold_sweep": (
            threshold_rows
        ),
        "top1_risk_coverage_curve": (
            risk_coverage_curve(
                rows
            )
        ),
        "cases": (
            rows
        ),
        "interpretation_guardrails": [
            (
                "This is evidence-support calibration, "
                "not clinical accuracy."
            ),
            (
                "The calibration set is not an "
                "independent frozen test set."
            ),
            (
                "Partial and unsupported cases are "
                "both treated as do-not-fully-accept "
                "for the binary retrieval-only baseline."
            ),
            (
                "A weak retrieval-only separation is "
                "evidence for adding a claim-support "
                "verification stage, not for tuning on "
                "the frozen retrieval held-out set."
            ),
        ],
    }

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULTS_PATH.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print()
    print(
        "Primary top1-score baseline"
    )
    print(
        "-" * 76
    )
    print(
        "AUROC             : "
        f"{results['primary_retrieval_only_signal']['auroc']:.4f}"
    )
    print(
        "AUPRC             : "
        f"{results['primary_retrieval_only_signal']['auprc_average_precision']:.4f}"
    )

    print(
        "Contrast violations: "
        f"{contrastive['violations']}/"
        f"{contrastive['pair_count']}"
    )

    if best_zero_observed_unsafe:
        print(
            "Max coverage with 0 observed "
            "non-supported full accepts:"
        )
        print(
            "  Threshold       : "
            f"{best_zero_observed_unsafe['threshold']:.6f}"
        )
        print(
            "  Coverage        : "
            f"{best_zero_observed_unsafe['coverage']:.4f}"
        )
        print(
            "  False refusal   : "
            f"{best_zero_observed_unsafe['false_refusal_rate']:.4f}"
        )
    else:
        print(
            "No non-empty threshold achieved "
            "0 observed non-supported full accepts."
        )

    print()
    print(
        "Created:"
    )
    print(
        "  evaluation\\results\\"
        "evidence_sufficiency_"
        "retrieval_only_baseline_v1.json"
    )
    print()
    print(
        "Retrieval-only baseline: PASS"
    )
    print(
        "Do not select a production threshold "
        "or make final safety claims from this "
        "calibration run."
    )


if __name__ == "__main__":
    main()
