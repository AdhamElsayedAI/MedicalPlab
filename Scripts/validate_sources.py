import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "source.schema.json"
)

SOURCE_REGISTRY_PATH = (
    PROJECT_ROOT / "examples" / "source_registry.example.json"
)


def load_json(path: Path) -> Any:
    """Load JSON data from a file."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_source_schema(
    source: dict[str, Any],
    schema: dict[str, Any],
    index: int,
) -> list[str]:
    """Validate one source against the canonical source schema."""
    validator = Draft202012Validator(schema)
    errors = []

    for error in sorted(
        validator.iter_errors(source),
        key=lambda item: list(item.path),
    ):
        location = ".".join(str(part) for part in error.path)

        prefix = f"Source #{index}"

        if location:
            errors.append(
                f"{prefix} [{location}]: {error.message}"
            )
        else:
            errors.append(
                f"{prefix}: {error.message}"
            )

    return errors


def validate_business_rules(
    source: dict[str, Any],
) -> list[str]:
    """Apply MedicalPlab source-governance rules."""
    errors = []

    source_id = source.get("source_id", "UNKNOWN")

    license_status = source.get("license_status")
    ai_use_status = source.get("ai_use_status")
    ingestion_status = source.get("ingestion_status")
    license_name = source.get("license_name")
    use_cases = source.get("use_cases", [])

    blocked_ai_states = {
        "permission_required",
        "blocked",
        "unclear",
    }

    # Blocked sources must never be approved for ingestion.
    if license_status == "blocked":
        if ingestion_status != "blocked":
            errors.append(
                f"{source_id}: blocked licence requires "
                "ingestion_status='blocked'."
            )

    # Sources requiring AI permission cannot enter the pipeline.
    if ai_use_status in blocked_ai_states:
        if ingestion_status in {
            "approved",
            "processing",
            "processed",
        }:
            errors.append(
                f"{source_id}: AI use status '{ai_use_status}' "
                "cannot be ingested."
            )

    # Approved/conditional content should have traceable licence info.
    if license_status in {
        "approved",
        "conditional",
    }:
        if not license_name:
            errors.append(
                f"{source_id}: approved or conditional sources "
                "must include license_name."
            )

    # Active RAG or question-generation sources require
    # explicit compatible AI-use permission.
    #
    # Blocked registry entries are allowed to remain documented
    # as long as they cannot enter the ingestion pipeline.
    if ingestion_status != "blocked":
     if any(
        use_case in {"rag", "question_generation"}
        for use_case in use_cases
    ):
        if ai_use_status not in {
            "allowed",
            "allowed_with_conditions",
        }:
            errors.append(
                f"{source_id}: active RAG/question generation "
                "requires explicit compatible AI-use status."
            )

    # Processed sources must have passed governance approval.
    if ingestion_status == "processed":
        if license_status not in {
            "approved",
            "conditional",
        }:
            errors.append(
                f"{source_id}: processed sources require an "
                "approved or conditional licence."
            )

    return errors


def validate_registry(
    registry_path: Path,
) -> tuple[bool, list[str]]:
    """Validate the complete MedicalPlab source registry."""
    schema = load_json(SOURCE_SCHEMA_PATH)
    registry = load_json(registry_path)

    errors = []

    if not isinstance(registry, list):
        return False, [
            "Source registry must be a JSON array."
        ]

    source_ids = []

    for index, source in enumerate(registry, start=1):
        if not isinstance(source, dict):
            errors.append(
                f"Source #{index} must be a JSON object."
            )
            continue

        errors.extend(
            validate_source_schema(
                source,
                schema,
                index,
            )
        )

        errors.extend(
            validate_business_rules(source)
        )

        source_id = source.get("source_id")

        if source_id:
            source_ids.append(source_id)

    # Source IDs must be globally unique.
    duplicates = {
        source_id
        for source_id in source_ids
        if source_ids.count(source_id) > 1
    }

    for duplicate in sorted(duplicates):
        errors.append(
            f"Duplicate source_id detected: {duplicate}"
        )

    return len(errors) == 0, errors


def print_registry_summary(
    registry: list[dict[str, Any]],
) -> None:
    """Print a compact source-governance summary."""
    print("\nSource Registry Summary")
    print("-" * 60)

    for source in registry:
        source_id = source.get("source_id", "UNKNOWN")
        provider = source.get("provider", "Unknown")
        ingestion = source.get(
            "ingestion_status",
            "unknown",
        )
        ai_status = source.get(
            "ai_use_status",
            "unknown",
        )

        print(
            f"{source_id:<20} "
            f"{provider:<30} "
            f"{ingestion:<10} "
            f"{ai_status}"
        )


def main() -> None:
    registry = load_json(SOURCE_REGISTRY_PATH)

    is_valid, errors = validate_registry(
        SOURCE_REGISTRY_PATH
    )

    print("\nMedicalPlab Source Registry Validator")
    print("=" * 40)

    if is_valid:
        print("VALID ✅")
        print(
            f"Sources registered: {len(registry)}"
        )

        print_registry_summary(registry)
        return

    print("INVALID ❌")

    for index, error in enumerate(errors, start=1):
        print(f"{index}. {error}")


if __name__ == "__main__":
    main()