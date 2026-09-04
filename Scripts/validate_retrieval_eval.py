import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_PATH = (
    PROJECT_ROOT
    / "schemas"
    / "retrieval_eval.schema.json"
)

EVAL_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "retrieval_eval_v1.json"
)

SECTIONS_PATH = (
    PROJECT_ROOT
    / "Data"
    / "processed"
    / "cardiology"
    / "DOC-WHO-CARD-0001.sections.enriched.json"
)


def load_json(path: Path) -> Any:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def main() -> None:
    schema = load_json(
        SCHEMA_PATH
    )

    evaluation = load_json(
        EVAL_PATH
    )

    sections_document = load_json(
        SECTIONS_PATH
    )

    Draft202012Validator.check_schema(
        schema
    )

    validator = Draft202012Validator(
        schema
    )

    schema_errors = list(
        validator.iter_errors(
            evaluation
        )
    )

    errors: list[str] = []

    for error in schema_errors:
        path = ".".join(
            str(part)
            for part in error.path
        )

        errors.append(
            f"{path}: {error.message}"
        )

    sections = sections_document.get(
        "sections",
        [],
    )

    block_map = {
        section["block_index"]: section
        for section in sections
    }

    cases = evaluation.get(
        "cases",
        [],
    )

    query_ids: set[str] = set()

    for case in cases:
        query_id = case[
            "query_id"
        ]

        if query_id in query_ids:
            errors.append(
                f"{query_id}: duplicate query_id."
            )

        query_ids.add(
            query_id
        )

        answerable = case[
            "expected_answerable"
        ]

        relevant_blocks = case[
            "relevant_blocks"
        ]

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

        seen_blocks: set[int] = set()

        for gold in relevant_blocks:
            block_index = gold[
                "block_index"
            ]

            if block_index in seen_blocks:
                errors.append(
                    f"{query_id}: duplicate gold "
                    f"block {block_index}."
                )

            seen_blocks.add(
                block_index
            )

            if block_index not in block_map:
                errors.append(
                    f"{query_id}: unknown "
                    f"block {block_index}."
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
                        f"{block_index} does not belong "
                        f"to expected section "
                        f"{expected_parent}."
                    )

    print(
        "\nMedicalPlab Retrieval Evaluation Validator"
    )
    print("=" * 50)

    print(
        f"Evaluation set : "
        f"{evaluation.get('eval_set_id')}"
    )

    print(
        f"Cases          : "
        f"{len(cases)}"
    )

    answerable_count = sum(
        1
        for case in cases
        if case[
            "expected_answerable"
        ]
    )

    unsupported_count = (
        len(cases)
        - answerable_count
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
        f"Errors         : "
        f"{len(errors)}"
    )

    print(
        f"Validation     : "
        f"{'PASS ✅' if not errors else 'FAIL ❌'}"
    )

    if errors:
        print(
            "\nErrors"
        )
        print("-" * 80)

        for error in errors:
            print(
                f"- {error}"
            )

        raise SystemExit(1)


if __name__ == "__main__":
    main()