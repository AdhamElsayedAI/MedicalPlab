import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_SCHEMA_PATH = (
    PROJECT_ROOT
    / "schemas"
    / "retrieval_eval.schema.json"
)

DEFAULT_EVAL_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "retrieval_eval_v1.json"
)

PROCESSED_DATA_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
)


def load_json(
    path: Path,
) -> Any:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def resolve_path(
    value: str,
) -> Path:
    path = Path(
        value
    )

    if not path.is_absolute():
        path = (
            PROJECT_ROOT
            / path
        )

    return path.resolve()


def find_sections_path(
    document_id: str,
) -> Path:
    filename = (
        f"{document_id}"
        ".sections.enriched.json"
    )

    matches = list(
        PROCESSED_DATA_DIR.rglob(
            filename
        )
    )

    if not matches:
        raise FileNotFoundError(
            f"No canonical sections file found "
            f"for {document_id}: {filename}"
        )

    if len(matches) > 1:
        joined = ", ".join(
            str(path)
            for path in matches
        )

        raise RuntimeError(
            f"Multiple canonical section files "
            f"found for {document_id}: {joined}"
        )

    return matches[0]


def load_document_blocks(
    document_id: str,
) -> dict[int, dict[str, Any]]:
    path = find_sections_path(
        document_id
    )

    document = load_json(
        path
    )

    actual_document_id = str(
        document.get(
            "document_id",
            "",
        )
    )

    if (
        actual_document_id
        != document_id
    ):
        raise ValueError(
            f"Document ID mismatch in {path}: "
            f"expected={document_id}, "
            f"found={actual_document_id}"
        )

    sections = document.get(
        "sections",
        [],
    )

    if not isinstance(
        sections,
        list,
    ):
        raise ValueError(
            f"sections must be a list "
            f"for {document_id}."
        )

    block_map: dict[
        int,
        dict[str, Any],
    ] = {}

    for section in sections:
        if not isinstance(
            section,
            dict,
        ):
            raise ValueError(
                f"Invalid section object "
                f"in {document_id}."
            )

        block_index = int(
            section[
                "block_index"
            ]
        )

        if block_index in block_map:
            raise ValueError(
                f"Duplicate block_index "
                f"{block_index} in "
                f"{document_id}."
            )

        block_map[
            block_index
        ] = section

    return block_map


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a MedicalPlab retrieval "
            "evaluation set against the schema "
            "and canonical document blocks."
        )
    )

    parser.add_argument(
        "--eval-path",
        default=str(
            DEFAULT_EVAL_PATH
        ),
        help=(
            "Path to retrieval evaluation JSON."
        ),
    )

    parser.add_argument(
        "--schema-path",
        default=str(
            DEFAULT_SCHEMA_PATH
        ),
        help=(
            "Path to retrieval evaluation schema."
        ),
    )

    args = parser.parse_args()

    eval_path = resolve_path(
        args.eval_path
    )

    schema_path = resolve_path(
        args.schema_path
    )

    schema = load_json(
        schema_path
    )

    evaluation = load_json(
        eval_path
    )

    Draft202012Validator.check_schema(
        schema
    )

    validator = Draft202012Validator(
        schema
    )

    schema_errors = sorted(
        validator.iter_errors(
            evaluation
        ),
        key=lambda error: list(
            error.path
        ),
    )

    errors: list[str] = []

    for error in schema_errors:
        path = ".".join(
            str(part)
            for part in error.path
        )

        if not path:
            path = "<root>"

        errors.append(
            f"{path}: {error.message}"
        )

    default_document_id = (
        evaluation.get(
            "source_document_id"
        )
    )

    if default_document_id is not None:
        default_document_id = str(
            default_document_id
        )

    corpus_document_ids = (
        evaluation.get(
            "corpus_document_ids",
            [],
        )
    )

    if not isinstance(
        corpus_document_ids,
        list,
    ):
        corpus_document_ids = []

    corpus_document_ids = [
        str(document_id)
        for document_id
        in corpus_document_ids
    ]

    if (
        default_document_id
        and corpus_document_ids
        and default_document_id
        not in corpus_document_ids
    ):
        errors.append(
            "source_document_id must belong "
            "to corpus_document_ids when both "
            "fields are provided."
        )

    cases = evaluation.get(
        "cases",
        [],
    )

    if not isinstance(
        cases,
        list,
    ):
        cases = []

    referenced_document_ids: set[
        str
    ] = set(
        corpus_document_ids
    )

    if default_document_id:
        referenced_document_ids.add(
            default_document_id
        )

    # First pass: resolve all document references.
    for case in cases:
        if not isinstance(
            case,
            dict,
        ):
            continue

        relevant_blocks = case.get(
            "relevant_blocks",
            [],
        )

        if not isinstance(
            relevant_blocks,
            list,
        ):
            continue

        for gold in relevant_blocks:
            if not isinstance(
                gold,
                dict,
            ):
                continue

            document_id = gold.get(
                "document_id"
            )

            if document_id is None:
                document_id = (
                    default_document_id
                )

            if document_id:
                referenced_document_ids.add(
                    str(
                        document_id
                    )
                )

    document_blocks: dict[
        str,
        dict[int, dict[str, Any]],
    ] = {}

    for document_id in sorted(
        referenced_document_ids
    ):
        try:
            document_blocks[
                document_id
            ] = load_document_blocks(
                document_id
            )
        except (
            FileNotFoundError,
            RuntimeError,
            ValueError,
            KeyError,
            TypeError,
        ) as exc:
            errors.append(
                f"{document_id}: {exc}"
            )

    query_ids: set[str] = set()

    for case in cases:
        if not isinstance(
            case,
            dict,
        ):
            continue

        query_id = str(
            case.get(
                "query_id",
                "<missing-query-id>",
            )
        )

        if query_id in query_ids:
            errors.append(
                f"{query_id}: duplicate query_id."
            )

        query_ids.add(
            query_id
        )

        answerable = bool(
            case.get(
                "expected_answerable",
                False,
            )
        )

        relevant_blocks = case.get(
            "relevant_blocks",
            [],
        )

        if not isinstance(
            relevant_blocks,
            list,
        ):
            continue

        if (
            answerable
            and not relevant_blocks
        ):
            errors.append(
                f"{query_id}: answerable query "
                "must have relevant blocks."
            )

        if (
            not answerable
            and relevant_blocks
        ):
            errors.append(
                f"{query_id}: unsupported query "
                "must not contain relevant blocks."
            )

        expected_parent = case.get(
            "expected_parent_section_number"
        )

        seen_blocks: set[
            tuple[str, int]
        ] = set()

        for gold in relevant_blocks:
            if not isinstance(
                gold,
                dict,
            ):
                continue

            document_id = gold.get(
                "document_id"
            )

            if document_id is None:
                document_id = (
                    default_document_id
                )

            if not document_id:
                errors.append(
                    f"{query_id}: gold block "
                    "has no document_id and no "
                    "source_document_id fallback."
                )
                continue

            document_id = str(
                document_id
            )

            if (
                corpus_document_ids
                and document_id
                not in corpus_document_ids
            ):
                errors.append(
                    f"{query_id}: document "
                    f"{document_id} is not listed "
                    "in corpus_document_ids."
                )

            try:
                block_index = int(
                    gold[
                        "block_index"
                    ]
                )
            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                errors.append(
                    f"{query_id}: invalid "
                    "block_index."
                )
                continue

            block_key = (
                document_id,
                block_index,
            )

            if block_key in seen_blocks:
                errors.append(
                    f"{query_id}: duplicate gold "
                    f"{document_id}:"
                    f"B{block_index:04d}."
                )

            seen_blocks.add(
                block_key
            )

            block_map = document_blocks.get(
                document_id
            )

            if block_map is None:
                continue

            if block_index not in block_map:
                errors.append(
                    f"{query_id}: unknown block "
                    f"{document_id}:"
                    f"B{block_index:04d}."
                )
                continue

            section = block_map[
                block_index
            ]

            if expected_parent:
                actual_parent = section.get(
                    "parent_section_number"
                )

                actual_number = section.get(
                    "section_number"
                )

                if (
                    actual_parent
                    != expected_parent
                    and actual_number
                    != expected_parent
                ):
                    errors.append(
                        f"{query_id}: block "
                        f"{document_id}:"
                        f"B{block_index:04d} "
                        "does not belong to "
                        f"expected section "
                        f"{expected_parent}."
                    )

    answerable_count = sum(
        1
        for case in cases
        if isinstance(
            case,
            dict,
        )
        and case.get(
            "expected_answerable",
            False,
        )
    )

    unsupported_count = (
        len(cases)
        - answerable_count
    )

    print(
        "\nMedicalPlab Retrieval "
        "Evaluation Validator"
    )

    print("=" * 58)

    print(
        f"Evaluation set : "
        f"{evaluation.get('eval_set_id')}"
    )

    print(
        f"Evaluation file: "
        f"{eval_path}"
    )

    print(
        f"Cases          : "
        f"{len(cases)}"
    )

    print(
        f"Answerable     : "
        f"{answerable_count}"
    )

    print(
        f"Unsupported    : "
        f"{unsupported_count}"
    )

    print(
        f"Documents      : "
        f"{len(referenced_document_ids)}"
    )

    if referenced_document_ids:
        for document_id in sorted(
            referenced_document_ids
        ):
            print(
                f"  - {document_id}"
            )

    print(
        f"Errors         : "
        f"{len(errors)}"
    )

    if errors:
        print(
            "\nValidation errors"
        )

        print("-" * 58)

        for error in errors:
            print(
                f"- {error}"
            )

        print(
            "\nValidation     : FAIL ❌"
        )

        raise SystemExit(
            1
        )

    print(
        "Validation     : PASS ✅"
    )


if __name__ == "__main__":
    main()