import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCUMENT_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "document.schema.json"
)

SOURCE_REGISTRY_PATH = (
    PROJECT_ROOT / "examples" / "source_registry.example.json"
)

DOCUMENT_MANIFEST_PATH = (
    PROJECT_ROOT / "examples" / "document_manifest.example.json"
)


def load_json(path: Path) -> Any:
    """Load JSON data from a file."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_document_schema(
    document: dict[str, Any],
    schema: dict[str, Any],
    index: int,
) -> list[str]:
    """Validate one document against the canonical JSON Schema."""
    validator = Draft202012Validator(schema)

    errors = []

    for error in sorted(
        validator.iter_errors(document),
        key=lambda item: list(item.path),
    ):
        location = ".".join(str(part) for part in error.path)

        prefix = f"Document #{index}"

        if location:
            errors.append(
                f"{prefix} [{location}]: {error.message}"
            )
        else:
            errors.append(
                f"{prefix}: {error.message}"
            )

    return errors


def build_source_index(
    registry: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Index registered sources by source_id."""
    return {
        source["source_id"]: source
        for source in registry
        if isinstance(source, dict)
        and source.get("source_id")
    }


def validate_business_rules(
    document: dict[str, Any],
    source_index: dict[str, dict[str, Any]],
) -> list[str]:
    """Apply MedicalPlab document-governance rules."""
    errors = []

    document_id = document.get(
        "document_id",
        "UNKNOWN",
    )

    source_id = document.get("source_id")

    source = source_index.get(source_id)

    if source is None:
        errors.append(
            f"{document_id}: unknown source_id '{source_id}'."
        )
        return errors

    document_status = document.get(
        "ingestion_status"
    )

    document_license = document.get(
        "license_status"
    )

    source_license = source.get(
        "license_status"
    )

    source_ingestion = source.get(
        "ingestion_status"
    )

    source_ai_status = source.get(
        "ai_use_status"
    )

    source_use_cases = set(
        source.get("use_cases", [])
    )

    rag_allowed = document.get(
        "rag_allowed",
        False,
    )

    question_generation_allowed = document.get(
        "question_generation_allowed",
        False,
    )

    url = document.get("url")
    retrieved_at = document.get(
        "retrieved_at"
    )
    sha256 = document.get("sha256")

    # A document cannot inherit from a blocked source.
    if source_ingestion == "blocked":
        errors.append(
            f"{document_id}: parent source "
            f"'{source_id}' is blocked."
        )

    if source_license == "blocked":
        errors.append(
            f"{document_id}: parent source licence is blocked."
        )

    # Documents used for AI must come from AI-compatible sources.
    ai_compatible_statuses = {
        "allowed",
        "allowed_with_conditions",
    }

    if rag_allowed:
        if "rag" not in source_use_cases:
            errors.append(
                f"{document_id}: parent source is not "
                "registered for RAG."
            )

        if source_ai_status not in ai_compatible_statuses:
            errors.append(
                f"{document_id}: RAG requires an "
                "AI-compatible parent source."
            )

    if question_generation_allowed:
        if "question_generation" not in source_use_cases:
            errors.append(
                f"{document_id}: parent source is not "
                "registered for question generation."
            )

        if source_ai_status not in ai_compatible_statuses:
            errors.append(
                f"{document_id}: question generation requires "
                "an AI-compatible parent source."
            )

    # Documents actively used by AI cannot have blocked licences.
    if (
        rag_allowed
        or question_generation_allowed
    ):
        if document_license == "blocked":
            errors.append(
                f"{document_id}: blocked document licence "
                "cannot be used by AI."
            )

    # Candidate documents may not have a final URL yet.
    # Approved or later documents must be traceable.
    traceable_states = {
        "approved",
        "downloaded",
        "processed",
    }

    if document_status in traceable_states:
        if not url:
            errors.append(
                f"{document_id}: ingestion_status="
                f"'{document_status}' requires url."
            )

    # Downloaded/processed files require provenance metadata.
    downloaded_states = {
        "downloaded",
        "processed",
    }

    if document_status in downloaded_states:
        if not retrieved_at:
            errors.append(
                f"{document_id}: downloaded/processed "
                "documents require retrieved_at."
            )

        if not sha256:
            errors.append(
                f"{document_id}: downloaded/processed "
                "documents require sha256."
            )

    # Validate SHA-256 format when provided.
    if sha256:
        if not re.fullmatch(
            r"[0-9a-fA-F]{64}",
            sha256,
        ):
            errors.append(
                f"{document_id}: sha256 must contain "
                "exactly 64 hexadecimal characters."
            )

    return errors


def validate_manifest(
    manifest_path: Path,
) -> tuple[bool, list[str]]:
    """Validate the complete MedicalPlab document manifest."""
    schema = load_json(
        DOCUMENT_SCHEMA_PATH
    )

    registry = load_json(
        SOURCE_REGISTRY_PATH
    )

    manifest = load_json(
        manifest_path
    )

    errors = []

    if not isinstance(registry, list):
        return False, [
            "Source registry must be a JSON array."
        ]

    if not isinstance(manifest, list):
        return False, [
            "Document manifest must be a JSON array."
        ]

    source_index = build_source_index(
        registry
    )

    document_ids = []

    for index, document in enumerate(
        manifest,
        start=1,
    ):
        if not isinstance(document, dict):
            errors.append(
                f"Document #{index} must be a JSON object."
            )
            continue

        errors.extend(
            validate_document_schema(
                document,
                schema,
                index,
            )
        )

        errors.extend(
            validate_business_rules(
                document,
                source_index,
            )
        )

        document_id = document.get(
            "document_id"
        )

        if document_id:
            document_ids.append(
                document_id
            )

    duplicates = {
        document_id
        for document_id in document_ids
        if document_ids.count(document_id) > 1
    }

    for duplicate in sorted(duplicates):
        errors.append(
            f"Duplicate document_id detected: {duplicate}"
        )

    return len(errors) == 0, errors


def print_manifest_summary(
    manifest: list[dict[str, Any]],
) -> None:
    """Print a compact document summary."""
    print("\nDocument Manifest Summary")
    print("-" * 85)

    for document in manifest:
        document_id = document.get(
            "document_id",
            "UNKNOWN",
        )

        specialty = document.get(
            "medical_specialty",
            "Unknown",
        )

        evidence = document.get(
            "evidence_level",
            "unknown",
        )

        status = document.get(
            "ingestion_status",
            "unknown",
        )

        print(
            f"{document_id:<24} "
            f"{specialty:<18} "
            f"{evidence:<12} "
            f"{status}"
        )


def main() -> None:
    manifest = load_json(
        DOCUMENT_MANIFEST_PATH
    )

    is_valid, errors = validate_manifest(
        DOCUMENT_MANIFEST_PATH
    )

    print("\nMedicalPlab Document Manifest Validator")
    print("=" * 44)

    if is_valid:
        print("VALID ✅")
        print(
            f"Documents registered: {len(manifest)}"
        )

        print_manifest_summary(
            manifest
        )
        return

    print("INVALID ❌")

    for index, error in enumerate(
        errors,
        start=1,
    ):
        print(f"{index}. {error}")


if __name__ == "__main__":
    main()