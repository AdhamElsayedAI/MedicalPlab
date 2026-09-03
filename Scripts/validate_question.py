import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent

QUESTION_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "question.schema.json"
)

DEFAULT_QUESTION_PATH = (
    PROJECT_ROOT / "examples" / "question.example.json"
)


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file and return its content."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_schema(
    question: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    """Validate a question against the canonical JSON Schema."""
    validator = Draft202012Validator(schema)

    errors = []

    for error in sorted(
        validator.iter_errors(question),
        key=lambda item: list(item.path),
    ):
        location = ".".join(str(part) for part in error.path)

        if location:
            errors.append(f"{location}: {error.message}")
        else:
            errors.append(error.message)

    return errors


def validate_business_rules(
    question: dict[str, Any],
) -> list[str]:
    """
    Validate rules that JSON Schema alone cannot reliably enforce.
    """
    errors = []

    choices = question.get("choices", [])

    choice_ids = [
        choice.get("id")
        for choice in choices
        if isinstance(choice, dict)
    ]

    choice_texts = [
        choice.get("text", "").strip().casefold()
        for choice in choices
        if isinstance(choice, dict)
    ]

    correct_answer = question.get("correct_answer")

    # Correct answer must point to an existing choice.
    if correct_answer not in choice_ids:
        errors.append(
            "correct_answer must match one of the choice IDs."
        )

    # Choice IDs must be unique.
    if len(choice_ids) != len(set(choice_ids)):
        errors.append(
            "Choice IDs must be unique."
        )

    # Choice text must not be duplicated.
    non_empty_texts = [
        text for text in choice_texts if text
    ]

    if len(non_empty_texts) != len(set(non_empty_texts)):
        errors.append(
            "Choice texts must be unique."
        )

    # AI-generated questions must identify the model/version.
    generation = question.get("generation", {})

    if generation.get("generated_by_ai") is True:
        if not generation.get("model"):
            errors.append(
                "AI-generated questions must include generation.model."
            )

        if not generation.get("generation_version"):
            errors.append(
                "AI-generated questions must include "
                "generation.generation_version."
            )

    return errors


def validate_question(
    question_path: Path,
) -> tuple[bool, list[str]]:
    """Run all MedicalPlab validation checks."""
    schema = load_json(QUESTION_SCHEMA_PATH)
    question = load_json(question_path)

    errors = []

    errors.extend(
        validate_schema(question, schema)
    )

    errors.extend(
        validate_business_rules(question)
    )

    return len(errors) == 0, errors


def main() -> None:
    is_valid, errors = validate_question(
        DEFAULT_QUESTION_PATH
    )

    print("\nMedicalPlab Question Validator")
    print("=" * 32)

    if is_valid:
        print("VALID ✅")
        print(
            f"File: {DEFAULT_QUESTION_PATH.name}"
        )
        return

    print("INVALID ❌")

    for index, error in enumerate(errors, start=1):
        print(f"{index}. {error}")


if __name__ == "__main__":
    main()