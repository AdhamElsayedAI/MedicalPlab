import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
)


# High-confidence extraction artifacts only.
#
# IMPORTANT:
# Do not add normal medical headings here simply because
# they repeat across several pages.
CONFIRMED_EDGE_ARTIFACTS = {
    "guideline for the pharmacological treatment of hypertension in adults",
    "snoitadnemmocer",
    "sexenna",
    "secnerefer",
}


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON data from a file."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object in: {path}"
        )

    return data


def save_json(
    path: Path,
    data: dict[str, Any],
) -> None:
    """Save JSON data using UTF-8."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def normalize_folder_name(value: str) -> str:
    """Normalize specialty name for filesystem use."""
    return (
        value.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )


def normalize_edge_line(line: str) -> str:
    """
    Normalize edge text for safe artifact comparison.

    Example:
    '48 GUIDELINE FOR THE PHARMACOLOGICAL...'
    becomes:
    'guideline for the pharmacological...'
    """
    line = line.strip()

    # Remove a leading page number.
    line = re.sub(
        r"^\s*\d+\s+",
        "",
        line,
    )

    # Remove a trailing page number.
    line = re.sub(
        r"\s+\d+\s*$",
        "",
        line,
    )

    # Normalize whitespace.
    line = re.sub(
        r"\s+",
        " ",
        line,
    )

    return line.casefold().strip()


def clean_general_text(text: str) -> str:
    """
    Apply conservative formatting cleanup.

    This function does not rewrite or summarize
    medical content.
    """
    text = text.replace(
        "\u00a0",
        " ",
    )

    # Remove trailing spaces on lines.
    lines = [
        line.rstrip()
        for line in text.splitlines()
    ]

    text = "\n".join(lines)

    # Collapse excessive spaces, but preserve line structure.
    text = re.sub(
        r"[ \t]{2,}",
        " ",
        text,
    )

    # Avoid excessive blank lines.
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def clean_page(
    text: str,
) -> tuple[str, list[str]]:
    """
    Remove only confirmed artifacts occurring at page edges.

    Returns:
        cleaned_text
        removed_lines
    """
    if not text:
        return "", []

    lines = text.splitlines()

    if not lines:
        return "", []

    removed_lines: list[str] = []

    non_empty_indexes = [
        index
        for index, line in enumerate(lines)
        if line.strip()
    ]

    if not non_empty_indexes:
        return "", []

    # Only inspect first/last 5 non-empty lines.
    edge_indexes = set(
        non_empty_indexes[:5]
        + non_empty_indexes[-5:]
    )

    cleaned_lines: list[str] = []

    for index, original_line in enumerate(lines):
        stripped = original_line.strip()

        if (
            stripped
            and index in edge_indexes
        ):
            normalized = normalize_edge_line(
                stripped
            )

            if normalized in CONFIRMED_EDGE_ARTIFACTS:
                removed_lines.append(
                    stripped
                )
                continue

        cleaned_lines.append(
            original_line
        )

    cleaned_text = "\n".join(
        cleaned_lines
    )

    cleaned_text = clean_general_text(
        cleaned_text
    )

    return cleaned_text, removed_lines


def build_cleaning_report(
    document_id: str,
    original_pages: list[dict[str, Any]],
    cleaned_pages: list[dict[str, Any]],
    removed_artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build measurable cleaning statistics."""
    original_characters = sum(
        len(page.get("text", ""))
        for page in original_pages
    )

    cleaned_characters = sum(
        len(page.get("text", ""))
        for page in cleaned_pages
    )

    characters_removed = (
        original_characters
        - cleaned_characters
    )

    removal_ratio = (
        characters_removed
        / original_characters
        if original_characters
        else 0.0
    )

    pages_modified = len(
        {
            item["page_number"]
            for item in removed_artifacts
        }
    )

    # Conservative safety check:
    # cleaning should remove only a small proportion
    # of source text.
    safe_removal = (
        removal_ratio <= 0.05
    )

    return {
        "document_id": document_id,
        "cleaning_status": (
            "pass"
            if safe_removal
            else "needs_review"
        ),
        "original_characters": original_characters,
        "cleaned_characters": cleaned_characters,
        "characters_removed": characters_removed,
        "removal_ratio": round(
            removal_ratio,
            6,
        ),
        "pages_modified": pages_modified,
        "artifacts_removed": len(
            removed_artifacts
        ),
        "removed_artifacts": removed_artifacts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Safely clean extracted MedicalPlab "
            "document text."
        )
    )

    parser.add_argument(
        "document_id",
        help="Document ID to clean.",
    )

    parser.add_argument(
        "--specialty",
        default="Cardiology",
        help="Medical specialty. Default: Cardiology",
    )

    args = parser.parse_args()

    specialty = normalize_folder_name(
        args.specialty
    )

    input_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.json"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Extracted document not found: "
            f"{input_path}"
        )

    document = load_json(
        input_path
    )

    original_pages = document.get(
        "pages",
        [],
    )

    if not isinstance(
        original_pages,
        list,
    ):
        raise ValueError(
            "Document pages must be a list."
        )

    cleaned_pages: list[dict[str, Any]] = []

    removed_artifacts: list[dict[str, Any]] = []

    print("\nMedicalPlab Safe Cleaning")
    print("=" * 32)
    print(
        f"Document : {args.document_id}"
    )
    print(
        f"Pages    : {len(original_pages)}"
    )
    print(
        "Cleaning : confirmed artifacts only..."
    )

    for page in original_pages:
        page_number = page.get(
            "page_number"
        )

        original_text = page.get(
            "text",
            "",
        )

        cleaned_text, removed_lines = clean_page(
            original_text
        )

        for removed_line in removed_lines:
            removed_artifacts.append(
                {
                    "page_number": page_number,
                    "text": removed_line,
                }
            )

        cleaned_pages.append(
            {
                "page_number": page_number,
                "text": cleaned_text,
                "character_count": len(
                    cleaned_text
                ),
                "has_text": bool(
                    cleaned_text
                ),
            }
        )

    report = build_cleaning_report(
        args.document_id,
        original_pages,
        cleaned_pages,
        removed_artifacts,
    )

    cleaned_at = datetime.now(
        timezone.utc
    ).isoformat()

    cleaned_document = {
        **{
            key: value
            for key, value in document.items()
            if key != "pages"
        },
        "cleaning": {
            "pipeline_version": "v1",
            "strategy": (
                "conservative_edge_artifact_removal"
            ),
            "cleaned_at": cleaned_at,
        },
        "pages": cleaned_pages,
    }

    cleaned_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.cleaned.json"
    )

    report_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.cleaning.json"
    )

    save_json(
        cleaned_path,
        cleaned_document,
    )

    save_json(
        report_path,
        report,
    )

    print("\nCLEANING COMPLETE ✅")
    print(
        f"Original chars : "
        f"{report['original_characters']:,}"
    )
    print(
        f"Cleaned chars  : "
        f"{report['cleaned_characters']:,}"
    )
    print(
        f"Chars removed  : "
        f"{report['characters_removed']:,}"
    )
    print(
        f"Removal ratio  : "
        f"{report['removal_ratio']:.2%}"
    )
    print(
        f"Pages modified : "
        f"{report['pages_modified']}"
    )
    print(
        f"Artifacts      : "
        f"{report['artifacts_removed']}"
    )
    print(
        f"Quality        : "
        f"{report['cleaning_status'].upper()}"
    )
    print(
        f"Cleaned output : "
        f"{cleaned_path}"
    )
    print(
        f"Audit report   : "
        f"{report_path}"
    )

    if removed_artifacts:
        print(
            "\nRemoved artifact samples:"
        )

        for item in removed_artifacts[:15]:
            print(
                f"Page {item['page_number']}: "
                f"{item['text']}"
            )


if __name__ == "__main__":
    main()