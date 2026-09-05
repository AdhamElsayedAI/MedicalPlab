from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_SET_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "evidence_sufficiency_calibration_v1.json"
)

DEFAULT_SCHEMA_PATH = (
    PROJECT_ROOT
    / "schemas"
    / "evidence_sufficiency_calibration_v1.schema.json"
)

CHUNKS_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
    / "cardiology"
)

DEFAULT_COMPARE_EVALS = [
    PROJECT_ROOT
    / "evaluation"
    / "retrieval_eval_multisource_dev_v2.json",
    PROJECT_ROOT
    / "evaluation"
    / "retrieval_eval_multisource_heldout_v1.json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a MedicalPlab Evidence Sufficiency "
            "Calibration v1 dataset."
        )
    )
    parser.add_argument(
        "--set-path",
        default=str(DEFAULT_SET_PATH),
    )
    parser.add_argument(
        "--schema-path",
        default=str(DEFAULT_SCHEMA_PATH),
    )
    parser.add_argument(
        "--compare-eval",
        action="append",
        default=None,
        help=(
            "Existing retrieval eval JSON used to detect "
            "exact query leakage. May be passed multiple times."
        ),
    )
    return parser.parse_args()


def resolve_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object: {path}"
        )

    return data


def load_corpus_block_keys(
    corpus_document_ids: set[str],
) -> set[tuple[str, int]]:
    keys: set[tuple[str, int]] = set()

    for document_id in sorted(
        corpus_document_ids
    ):
        chunks_path = (
            CHUNKS_DIR
            / f"{document_id}.chunks.json"
        )

        if not chunks_path.exists():
            raise FileNotFoundError(
                "Corpus chunk file not found: "
                f"{chunks_path}"
            )

        document = load_json(
            chunks_path
        )

        chunks = document.get(
            "chunks",
            [],
        )

        if not isinstance(
            chunks,
            list,
        ):
            raise ValueError(
                "chunks must be a list in "
                f"{chunks_path}"
            )

        for chunk in chunks:
            if not isinstance(
                chunk,
                dict,
            ):
                raise ValueError(
                    "Invalid chunk object in "
                    f"{chunks_path}"
                )

            actual_document_id = str(
                chunk.get(
                    "document_id",
                    "",
                )
            )

            block_index = chunk.get(
                "source_block_index"
            )

            if (
                actual_document_id
                != document_id
            ):
                raise ValueError(
                    "Chunk document mismatch in "
                    f"{chunks_path}: expected="
                    f"{document_id}, found="
                    f"{actual_document_id}"
                )

            if not isinstance(
                block_index,
                int,
            ):
                raise ValueError(
                    "Invalid source_block_index in "
                    f"{chunks_path}: "
                    f"{block_index!r}"
                )

            keys.add(
                (
                    document_id,
                    block_index,
                )
            )

    return keys


def normalize_query(value: str) -> str:
    value = value.casefold().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def format_json_path(parts: list[Any]) -> str:
    if not parts:
        return "$"

    text = "$"
    for part in parts:
        if isinstance(part, int):
            text += f"[{part}]"
        else:
            text += f".{part}"
    return text


def main() -> None:
    args = parse_args()

    set_path = resolve_path(args.set_path)
    schema_path = resolve_path(args.schema_path)

    compare_paths = (
        [resolve_path(value) for value in args.compare_eval]
        if args.compare_eval
        else DEFAULT_COMPARE_EVALS
    )

    errors: list[str] = []
    warnings: list[str] = []

    calibration = load_json(set_path)
    schema = load_json(schema_path)

    validator = Draft202012Validator(schema)

    for error in sorted(
        validator.iter_errors(calibration),
        key=lambda item: list(item.absolute_path),
    ):
        path_text = format_json_path(
            list(error.absolute_path)
        )
        errors.append(
            f"{path_text}: {error.message}"
        )

    cases = calibration.get("cases", [])
    corpus_document_ids = set(
        str(value)
        for value in calibration.get(
            "corpus_document_ids",
            [],
        )
    )

    corpus_block_keys: set[
        tuple[str, int]
    ] | None

    try:
        corpus_block_keys = (
            load_corpus_block_keys(
                corpus_document_ids
            )
        )
    except (
        FileNotFoundError,
        ValueError,
    ) as exc:
        corpus_block_keys = None
        errors.append(
            "Corpus block catalog validation "
            f"failed: {exc}"
        )

    seen_case_ids: set[str] = set()
    seen_queries: dict[str, str] = {}
    contrast_groups: dict[
        str,
        list[dict[str, Any]]
    ] = defaultdict(list)

    expected_action = {
        "supported": "answer",
        "partial": "qualified_answer",
        "unsupported": "abstain",
    }

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            continue

        case_id = str(
            case.get(
                "case_id",
                f"index-{index}",
            )
        )

        if case_id in seen_case_ids:
            errors.append(
                f"Duplicate case_id: {case_id}"
            )
        seen_case_ids.add(case_id)

        query = str(case.get("query", ""))
        normalized = normalize_query(query)

        if normalized in seen_queries:
            errors.append(
                "Duplicate normalized query: "
                f"{case_id} duplicates "
                f"{seen_queries[normalized]}"
            )
        else:
            seen_queries[normalized] = case_id

        label = case.get("support_label")
        action = case.get("expected_action")

        if label in expected_action:
            if action != expected_action[label]:
                errors.append(
                    f"{case_id}: support_label={label!r} "
                    f"requires expected_action="
                    f"{expected_action[label]!r}"
                )

        blocks = case.get(
            "supporting_blocks",
            [],
        )
        if not isinstance(blocks, list):
            blocks = []

        block_keys: set[tuple[str, int]] = set()

        for block in blocks:
            if not isinstance(block, dict):
                continue

            document_id = str(
                block.get(
                    "document_id",
                    "",
                )
            )
            block_index = block.get(
                "block_index"
            )

            if (
                document_id
                not in corpus_document_ids
            ):
                errors.append(
                    f"{case_id}: supporting block "
                    f"references document outside corpus: "
                    f"{document_id}"
                )

            if isinstance(block_index, int):
                key = (
                    document_id,
                    block_index,
                )
                if key in block_keys:
                    errors.append(
                        f"{case_id}: duplicate supporting "
                        f"block {document_id}:B"
                        f"{block_index:04d}"
                    )
                block_keys.add(key)

                if (
                    corpus_block_keys
                    is not None
                    and document_id
                    in corpus_document_ids
                    and key
                    not in corpus_block_keys
                ):
                    errors.append(
                        f"{case_id}: supporting block "
                        f"does not exist in corpus: "
                        f"{document_id}:B"
                        f"{block_index:04d}"
                    )

        required_document_id = case.get(
            "required_document_id"
        )
        if (
            required_document_id is not None
            and required_document_id
            not in corpus_document_ids
        ):
            errors.append(
                f"{case_id}: required_document_id "
                f"is outside corpus: "
                f"{required_document_id}"
            )

        negative_type = case.get(
            "negative_type"
        )
        missing_support = case.get(
            "missing_support"
        )
        hard_negative = case.get(
            "hard_negative"
        )

        if label == "supported":
            if not blocks:
                errors.append(
                    f"{case_id}: supported case must "
                    "contain at least one supporting block."
                )
            if negative_type is not None:
                errors.append(
                    f"{case_id}: supported case must "
                    "have negative_type=null."
                )
            if missing_support is not None:
                errors.append(
                    f"{case_id}: supported case must "
                    "have missing_support=null."
                )
            if hard_negative is not False:
                errors.append(
                    f"{case_id}: supported case must "
                    "have hard_negative=false."
                )

        elif label == "partial":
            if not blocks:
                errors.append(
                    f"{case_id}: partial case must "
                    "contain at least one supporting block."
                )
            if negative_type is None:
                errors.append(
                    f"{case_id}: partial case requires "
                    "a negative_type."
                )
            if not isinstance(
                missing_support,
                str,
            ) or not missing_support.strip():
                errors.append(
                    f"{case_id}: partial case requires "
                    "non-empty missing_support."
                )

        elif label == "unsupported":
            if blocks:
                errors.append(
                    f"{case_id}: unsupported case must "
                    "not contain supporting blocks."
                )
            if negative_type is None:
                errors.append(
                    f"{case_id}: unsupported case "
                    "requires a negative_type."
                )
            if not isinstance(
                missing_support,
                str,
            ) or not missing_support.strip():
                errors.append(
                    f"{case_id}: unsupported case "
                    "requires non-empty missing_support."
                )

        contrast_group_id = case.get(
            "contrast_group_id"
        )
        if isinstance(
            contrast_group_id,
            str,
        ):
            contrast_groups[
                contrast_group_id
            ].append(case)

    for group_id, group_cases in sorted(
        contrast_groups.items()
    ):
        if len(group_cases) < 2:
            errors.append(
                f"{group_id}: contrast group must "
                "contain at least two cases."
            )
            continue

        labels = {
            str(case.get("support_label"))
            for case in group_cases
        }

        if "supported" not in labels:
            errors.append(
                f"{group_id}: contrast group must "
                "contain a supported anchor."
            )

        if not (
            {"partial", "unsupported"}
            & labels
        ):
            errors.append(
                f"{group_id}: contrast group must "
                "contain a partial or unsupported "
                "near-miss case."
            )

    existing_queries: dict[
        str,
        tuple[str, str]
    ] = {}

    for compare_path in compare_paths:
        if not compare_path.exists():
            warnings.append(
                f"Compare eval not found: "
                f"{compare_path}"
            )
            continue

        comparison = load_json(
            compare_path
        )

        eval_set_id = str(
            comparison.get(
                "eval_set_id",
                compare_path.name,
            )
        )

        for case in comparison.get(
            "cases",
            [],
        ):
            if not isinstance(case, dict):
                continue

            query = str(
                case.get(
                    "query",
                    "",
                )
            )
            query_id = str(
                case.get(
                    "query_id",
                    "unknown",
                )
            )

            existing_queries[
                normalize_query(query)
            ] = (
                eval_set_id,
                query_id,
            )

    for case in cases:
        if not isinstance(case, dict):
            continue

        query = str(
            case.get(
                "query",
                "",
            )
        )
        normalized = normalize_query(
            query
        )

        if normalized in existing_queries:
            eval_set_id, query_id = (
                existing_queries[
                    normalized
                ]
            )
            errors.append(
                f"{case.get('case_id')}: exact "
                "query leakage from "
                f"{eval_set_id}/{query_id}"
            )

    counts = defaultdict(int)
    language_counts = defaultdict(int)
    negative_counts = defaultdict(int)

    for case in cases:
        if not isinstance(case, dict):
            continue

        counts[
            str(
                case.get(
                    "support_label",
                    "unknown",
                )
            )
        ] += 1

        language_counts[
            str(
                case.get(
                    "language",
                    "unknown",
                )
            )
        ] += 1

        negative_type = case.get(
            "negative_type"
        )
        if negative_type is not None:
            negative_counts[
                str(negative_type)
            ] += 1

    print(
        "\nMedicalPlab Evidence Sufficiency "
        "Calibration Validator"
    )
    print("=" * 72)
    print(
        f"Calibration set : "
        f"{calibration.get('calibration_set_id')}"
    )
    print(
        f"File            : {set_path}"
    )
    print(
        f"Cases           : {len(cases)}"
    )
    print(
        "Labels          : "
        f"supported={counts['supported']}, "
        f"partial={counts['partial']}, "
        f"unsupported={counts['unsupported']}"
    )
    print(
        "Languages       : "
        f"en={language_counts['en']}, "
        f"ar={language_counts['ar']}, "
        f"mixed={language_counts['mixed']}"
    )
    print(
        f"Contrast groups : "
        f"{len(contrast_groups)}"
    )
    print(
        f"Errors          : {len(errors)}"
    )
    print(
        f"Warnings        : {len(warnings)}"
    )

    if negative_counts:
        print(
            "Negative types  :"
        )
        for key, value in sorted(
            negative_counts.items()
        ):
            print(
                f"  - {key}: {value}"
            )

    if warnings:
        print(
            "\nWarnings"
        )
        print("-" * 72)
        for warning in warnings:
            print(
                f"- {warning}"
            )

    if errors:
        print(
            "\nErrors"
        )
        print("-" * 72)
        for error in errors:
            print(
                f"- {error}"
            )

        print(
            "\nValidation     : FAIL"
        )
        sys.exit(1)

    print(
        "\nValidation     : PASS"
    )


if __name__ == "__main__":
    main()
