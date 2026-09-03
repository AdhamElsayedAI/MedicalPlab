import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_PATH = (
    PROJECT_ROOT
    / "schemas"
    / "chunk.schema.json"
)

EXAMPLE_PATH = (
    PROJECT_ROOT
    / "examples"
    / "chunk.example.json"
)


def load_json(path: Path) -> Any:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def sha256_text(text: str) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def validate_business_rules(
    chunk: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    text = chunk.get(
        "text",
        "",
    )

    character_count = chunk.get(
        "character_count"
    )

    if isinstance(text, str):
        actual_character_count = len(
            text
        )

        if (
            character_count
            != actual_character_count
        ):
            errors.append(
                "character_count does not "
                f"match text length: "
                f"expected "
                f"{actual_character_count}, "
                f"got {character_count}."
            )

        expected_hash = sha256_text(
            text
        )

        actual_hash = chunk.get(
            "content_sha256"
        )

        if actual_hash != expected_hash:
            errors.append(
                "content_sha256 does not "
                "match chunk text."
            )

    chunk_index = chunk.get(
        "chunk_index"
    )

    chunk_count = chunk.get(
        "chunk_count_in_block"
    )

    if (
        isinstance(chunk_index, int)
        and isinstance(chunk_count, int)
        and chunk_index > chunk_count
    ):
        errors.append(
            "chunk_index cannot exceed "
            "chunk_count_in_block."
        )

    start_page = chunk.get(
        "start_page"
    )

    end_page = chunk.get(
        "end_page"
    )

    if (
        isinstance(start_page, int)
        and isinstance(end_page, int)
        and end_page < start_page
    ):
        errors.append(
            "end_page cannot be before "
            "start_page."
        )

    is_split = chunk.get(
        "is_split"
    )

    if (
        isinstance(chunk_count, int)
        and chunk_count == 1
        and is_split is True
    ):
        errors.append(
            "is_split must be false when "
            "chunk_count_in_block is 1."
        )

    if (
        isinstance(chunk_count, int)
        and chunk_count > 1
        and is_split is False
    ):
        errors.append(
            "is_split must be true when "
            "chunk_count_in_block is "
            "greater than 1."
        )

    return errors


def validate_chunk(
    chunk: dict[str, Any],
    validator: Draft202012Validator,
) -> list[str]:
    errors: list[str] = []

    schema_errors = sorted(
        validator.iter_errors(
            chunk
        ),
        key=lambda error: list(
            error.path
        ),
    )

    for error in schema_errors:
        path = ".".join(
            str(part)
            for part in error.path
        )

        if path:
            errors.append(
                f"{path}: "
                f"{error.message}"
            )
        else:
            errors.append(
                error.message
            )

    if not schema_errors:
        errors.extend(
            validate_business_rules(
                chunk
            )
        )

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate MedicalPlab retrieval "
            "chunks against the canonical "
            "chunk schema and business rules."
        )
    )

    parser.add_argument(
        "--file",
        type=Path,
        default=EXAMPLE_PATH,
        help=(
            "JSON file to validate. "
            "Defaults to "
            "examples/chunk.example.json"
        ),
    )

    args = parser.parse_args()

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Chunk schema not found: "
            f"{SCHEMA_PATH}"
        )

    input_path = args.file

    if not input_path.is_absolute():
        input_path = (
            PROJECT_ROOT
            / input_path
        )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Chunk file not found: "
            f"{input_path}"
        )

    schema = load_json(
        SCHEMA_PATH
    )

    Draft202012Validator.check_schema(
        schema
    )

    validator = Draft202012Validator(
        schema
    )

    data = load_json(
        input_path
    )

    if isinstance(data, dict):
        if "chunks" in data:
            chunks = data["chunks"]

            if not isinstance(
                chunks,
                list,
            ):
                raise ValueError(
                    "'chunks' must be a list."
                )
        else:
            chunks = [data]

    elif isinstance(data, list):
        chunks = data

    else:
        raise ValueError(
            "Chunk input must be a JSON "
            "object or list."
        )

    total_errors = 0

    print(
        "\nMedicalPlab Chunk Validator"
    )
    print("=" * 38)

    print(
        f"Schema : {SCHEMA_PATH}"
    )

    print(
        f"Input  : {input_path}"
    )

    print(
        f"Chunks : {len(chunks)}"
    )

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        if not isinstance(
            chunk,
            dict,
        ):
            print(
                f"\nChunk #{index}: FAIL ❌"
            )

            print(
                "  Chunk must be "
                "a JSON object."
            )

            total_errors += 1
            continue

        errors = validate_chunk(
            chunk,
            validator,
        )

        chunk_id = chunk.get(
            "chunk_id",
            f"#{index}",
        )

        if errors:
            print(
                f"\n{chunk_id}: FAIL ❌"
            )

            for error in errors:
                print(
                    f"  - {error}"
                )

            total_errors += len(
                errors
            )

        else:
            print(
                f"\n{chunk_id}: PASS ✅"
            )

    print("\n" + "-" * 38)

    if total_errors == 0:
        print(
            "Validation: PASS ✅"
        )
    else:
        print(
            "Validation: FAIL ❌"
        )

        print(
            f"Errors    : {total_errors}"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()