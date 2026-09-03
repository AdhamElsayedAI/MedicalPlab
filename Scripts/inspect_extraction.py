import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
)


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON data from a file."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_folder_name(value: str) -> str:
    """Normalize a specialty name for filesystem use."""
    return (
        value.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )


def non_empty_lines(text: str) -> list[str]:
    """Return stripped, non-empty lines."""
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


def normalize_edge_line(line: str) -> str:
    """
    Normalize possible header/footer text before comparison.

    Changing page numbers are removed so the same recurring
    header/footer can be detected across different pages.
    """
    line = line.strip()

    # Remove leading page numbers.
    # Example:
    # "48 GUIDELINE FOR..." -> "GUIDELINE FOR..."
    line = re.sub(
        r"^\s*\d+\s+",
        "",
        line,
    )

    # Remove trailing page numbers.
    # Example:
    # "GUIDELINE FOR... 48" -> "GUIDELINE FOR..."
    line = re.sub(
        r"\s+\d+\s*$",
        "",
        line,
    )

    # Normalize repeated whitespace.
    line = re.sub(
        r"\s+",
        " ",
        line,
    )

    return line.casefold().strip()


def detect_repeated_edge_lines(
    pages: list[dict[str, Any]],
) -> list[tuple[str, int]]:
    """
    Detect recurring text near the beginning or end of pages.

    This function only reports suspected headers/footers.
    It does not remove any document content.
    """
    counter: Counter[str] = Counter()

    examples: dict[str, str] = {}

    for page in pages:
        text = page.get("text", "")

        lines = non_empty_lines(text)

        if not lines:
            continue

        # Inspect the first and last five non-empty lines.
        candidates = (
            lines[:5]
            + lines[-5:]
        )

        # Avoid counting the same normalized line
        # more than once on the same page.
        seen_on_page: set[str] = set()

        for original_line in candidates:
            normalized = normalize_edge_line(
                original_line
            )

            if not normalized:
                continue

            # Ignore tiny fragments.
            if len(normalized) < 3:
                continue

            # Very long lines are unlikely to be
            # headers or footers.
            if len(normalized) > 160:
                continue

            if normalized in seen_on_page:
                continue

            seen_on_page.add(
                normalized
            )

            counter[normalized] += 1

            # Preserve one original form
            # for readable output.
            examples.setdefault(
                normalized,
                original_line.strip(),
            )

    page_count = len(pages)

    # Flag lines appearing on at least ~5% of pages,
    # with a minimum of 3 occurrences.
    threshold = max(
        3,
        round(page_count * 0.05),
    )

    repeated: list[tuple[str, int]] = []

    for normalized, count in counter.items():
        if count >= threshold:
            repeated.append(
                (
                    examples[normalized],
                    count,
                )
            )

    repeated.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return repeated


def find_low_text_pages(
    pages: list[dict[str, Any]],
) -> list[tuple[int, int]]:
    """Return pages containing fewer than 150 characters."""
    results = []

    for page in pages:
        character_count = page.get(
            "character_count",
            0,
        )

        if character_count < 150:
            results.append(
                (
                    page["page_number"],
                    character_count,
                )
            )

    return results


def print_page_sample(
    page: dict[str, Any],
    max_chars: int = 800,
) -> None:
    """Print a short representative sample from one page."""
    text = page.get(
        "text",
        "",
    )

    print(
        f"\n--- PAGE {page['page_number']} ---"
    )

    if not text:
        print("[EMPTY PAGE]")
        return

    print(
        text[:max_chars]
    )

    if len(text) > max_chars:
        print("\n[...]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Audit extracted MedicalPlab text "
            "before cleaning and chunking."
        )
    )

    parser.add_argument(
        "document_id",
        help="Document ID to inspect.",
    )

    parser.add_argument(
        "--specialty",
        default="Cardiology",
        help=(
            "Medical specialty folder. "
            "Default: Cardiology"
        ),
    )

    args = parser.parse_args()

    specialty = normalize_folder_name(
        args.specialty
    )

    document_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.json"
    )

    if not document_path.exists():
        raise FileNotFoundError(
            f"Extracted document not found: "
            f"{document_path}"
        )

    document = load_json(
        document_path
    )

    pages = document.get(
        "pages",
        [],
    )

    if not isinstance(pages, list):
        raise ValueError(
            "Extracted document 'pages' field "
            "must be a list."
        )

    if not pages:
        raise ValueError(
            "Extracted document contains no pages."
        )

    print("\nMedicalPlab Extraction Audit")
    print("=" * 35)

    print(
        f"Document : {args.document_id}"
    )

    print(
        f"Pages    : {len(pages)}"
    )

    total_characters = sum(
        page.get(
            "character_count",
            0,
        )
        for page in pages
    )

    print(
        f"Characters: {total_characters:,}"
    )

    low_text_pages = find_low_text_pages(
        pages
    )

    print(
        f"Low-text pages (<150 chars): "
        f"{len(low_text_pages)}"
    )

    if low_text_pages:
        print(
            "Low-text page numbers:",
            ", ".join(
                f"{page_number}({count})"
                for page_number, count
                in low_text_pages
            ),
        )

    repeated_lines = (
        detect_repeated_edge_lines(
            pages
        )
    )

    print(
        "\nSuspected repeated headers/footers:"
    )

    if not repeated_lines:
        print(
            "None detected."
        )
    else:
        for line, count in repeated_lines[
            :20
        ]:
            print(
                f"[{count:>2} pages] {line}"
            )

    # Representative pages:
    # first, second, middle, penultimate, last.
    sample_indexes = {
        0,
        1,
        len(pages) // 2,
        max(
            len(pages) - 2,
            0,
        ),
        len(pages) - 1,
    }

    print(
        "\nRepresentative Page Samples"
    )
    print("-" * 35)

    for index in sorted(
        sample_indexes
    ):
        if 0 <= index < len(pages):
            print_page_sample(
                pages[index]
            )


if __name__ == "__main__":
    main()