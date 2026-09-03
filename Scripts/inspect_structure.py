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
    """Load a cleaned MedicalPlab document."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "Expected document JSON to contain an object."
        )

    return data


def normalize_folder_name(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )


def normalize_text(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text.strip(),
    ).casefold()


def is_numbered_section(line: str) -> bool:
    """
    Detect real numbered section headings.

    Examples accepted:
        1 Introduction
        3.1 Blood pressure threshold...
        4.2 COVID-19 and hypertension

    Examples rejected:
        12.5 mg once a day
        1000 treated people...
        1. thiazide...
    """
    line = line.strip()

    # Hierarchical section such as 3.1 / 4.2 / 5.4
    match = re.match(
        r"^(\d+(?:\.\d+)+)\s+([A-Z][A-Za-z].*)$",
        line,
    )

    if match:
        return True

    # Top-level section such as:
    # 1 Introduction
    # 4 Special settings
    match = re.match(
        r"^(\d+)\s+([A-Z][A-Za-z].*)$",
        line,
    )

    if match:
        return True

    return False


def is_recommendation_heading(line: str) -> bool:
    """
    Detect actual recommendation block headings.
    """
    line = line.strip()

    return bool(
        re.match(
            r"^\d+\.\s+RECOMMENDATIONS?\b",
            line,
        )
    )


def is_block_heading(line: str) -> bool:
    lowered = normalize_text(line)

    return lowered in {
        "implementation remarks:",
        "implementation remarks",
        "evidence and rationale",
        "evidence-to-decision considerations",
    }


def classify_heading(line: str) -> str:
    lowered = normalize_text(line)

    if is_recommendation_heading(line):
        return "recommendation"

    if lowered in {
        "implementation remarks",
        "implementation remarks:",
    }:
        return "implementation_remarks"

    if lowered == "evidence and rationale":
        return "evidence_rationale"

    if lowered == (
        "evidence-to-decision considerations"
    ):
        return "evidence_to_decision"

    if is_numbered_section(line):
        return "numbered_section"

    return "other"


def is_main_body_start(line: str) -> bool:
    """
    Locate the real body instead of contents/summary pages.
    """
    return normalize_text(line) == "1 introduction"


def is_main_body_end(line: str) -> bool:
    """
    References mark the end of the core guideline body.
    """
    return normalize_text(line) == "references"


def is_uppercase_continuation(line: str) -> bool:
    """
    Detect a short uppercase continuation belonging to
    the previous recommendation heading.
    """
    line = line.strip()

    if not line:
        return False

    words = line.split()

    if not 1 <= len(words) <= 12:
        return False

    letters = [
        char
        for char in line
        if char.isalpha()
    ]

    if len(letters) < 5:
        return False

    uppercase_ratio = (
        sum(
            char.isupper()
            for char in letters
        )
        / len(letters)
    )

    return uppercase_ratio >= 0.95


def locate_main_body(
    pages: list[dict[str, Any]],
) -> tuple[
    tuple[int, int],
    tuple[int, int] | None,
]:
    """
    Find the exact page/line range containing core guideline
    content.

    Start: real '1 Introduction'
    End:   'References'
    """
    start_position = None
    end_position = None

    for page_index, page in enumerate(pages):
        text = page.get("text", "")

        if not isinstance(text, str):
            continue

        lines = text.splitlines()

        for line_index, raw_line in enumerate(lines):
            line = raw_line.strip()

            if (
                start_position is None
                and is_main_body_start(line)
            ):
                start_position = (
                    page_index,
                    line_index,
                )
                continue

            if (
                start_position is not None
                and is_main_body_end(line)
            ):
                end_position = (
                    page_index,
                    line_index,
                )

                return (
                    start_position,
                    end_position,
                )

    if start_position is None:
        raise ValueError(
            "Could not locate the start of the main body."
        )

    return (
        start_position,
        end_position,
    )


def position_in_body(
    page_index: int,
    line_index: int,
    start_position: tuple[int, int],
    end_position: tuple[int, int] | None,
) -> bool:
    current = (
        page_index,
        line_index,
    )

    if current < start_position:
        return False

    if (
        end_position is not None
        and current >= end_position
    ):
        return False

    return True


def should_merge_heading_continuation(
    heading: str,
    next_line: str,
) -> bool:
    """
    Decide conservatively whether the next line is a wrapped
    continuation of a numbered section heading.

    Examples:
        "2 Method for developing the"
        + "guideline"

        "3.3 Cardiovascular disease risk assessment as guide to initiation of"
        + "pharmacological treatment"

        "5 Publication, implementation,"
        + "evaluation and research gaps"
    """
    heading = heading.strip()
    next_line = next_line.strip()

    if not heading or not next_line:
        return False

    # Never merge another detected structural heading.
    if is_numbered_section(next_line):
        return False

    if is_recommendation_heading(next_line):
        return False

    if is_block_heading(next_line):
        return False

    # Continuation should remain reasonably short.
    if len(next_line) > 120:
        return False

    words = next_line.split()

    if not words:
        return False

    # Most wrapped heading continuations begin with lowercase text.
    first_alpha = next(
        (
            character
            for character in next_line
            if character.isalpha()
        ),
        None,
    )

    if first_alpha is None:
        return False

    if not first_alpha.islower():
        return False

    lowered_heading = heading.casefold()

    dangling_endings = (
        " the",
        " of",
        " and",
        " for",
        " to",
        " with",
        " in",
        " on",
        ",",
    )

    return lowered_heading.endswith(
        dangling_endings
    )


def collect_heading_candidates(
    pages: list[dict[str, Any]],
    start_position: tuple[int, int],
    end_position: tuple[int, int] | None,
) -> list[dict[str, Any]]:
    """
    Collect high-confidence structural headings from the
    core guideline body and safely merge wrapped headings.
    """
    candidates: list[dict[str, Any]] = []

    for page_index, page in enumerate(pages):
        page_number = page.get(
            "page_number"
        )

        text = page.get(
            "text",
            "",
        )

        if not isinstance(text, str):
            continue

        lines = text.splitlines()

        line_index = 0

        while line_index < len(lines):
            raw_line = lines[line_index]
            line = raw_line.strip()

            if not position_in_body(
                page_index,
                line_index,
                start_position,
                end_position,
            ):
                line_index += 1
                continue

            heading_type = None
            original_line_number = (
                line_index + 1
            )

            if is_recommendation_heading(line):
                heading_type = "recommendation"

                # Merge uppercase recommendation continuation.
                if line_index + 1 < len(lines):
                    next_line = (
                        lines[line_index + 1]
                        .strip()
                    )

                    if is_uppercase_continuation(
                        next_line
                    ):
                        line = (
                            f"{line} {next_line}"
                        )

                        line_index += 1

            elif is_block_heading(line):
                heading_type = classify_heading(
                    line
                )

            elif is_numbered_section(line):
                heading_type = "numbered_section"

                # Merge a wrapped numbered heading
                # when the next line clearly completes it.
                if line_index + 1 < len(lines):
                    next_line = (
                        lines[line_index + 1]
                        .strip()
                    )

                    if should_merge_heading_continuation(
                        line,
                        next_line,
                    ):
                        line = (
                            f"{line} {next_line}"
                        )

                        line_index += 1

            if heading_type:
                candidates.append(
                    {
                        "page_number": page_number,
                        "line_number": original_line_number,
                        "heading_type": heading_type,
                        "text": re.sub(
                            r"\s+",
                            " ",
                            line,
                        ).strip(),
                    }
                )

            line_index += 1

    return candidates

def print_heading_summary(
    candidates: list[dict[str, Any]],
) -> None:
    counter = Counter(
        item["heading_type"]
        for item in candidates
    )

    print("\nHeading Type Summary")
    print("-" * 45)

    for heading_type, count in sorted(
        counter.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    ):
        print(
            f"{heading_type:<28} {count:>4}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Audit high-confidence structure in the "
            "core MedicalPlab document body."
        )
    )

    parser.add_argument(
        "document_id",
        help="Document ID to inspect.",
    )

    parser.add_argument(
        "--specialty",
        default="Cardiology",
    )

    args = parser.parse_args()

    specialty = normalize_folder_name(
        args.specialty
    )

    input_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.cleaned.json"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Cleaned document not found: "
            f"{input_path}"
        )

    document = load_json(
        input_path
    )

    pages = document.get(
        "pages",
        [],
    )

    if not isinstance(pages, list):
        raise ValueError(
            "Document pages must be a list."
        )

    if not pages:
        raise ValueError(
            "Document contains no pages."
        )

    (
        start_position,
        end_position,
    ) = locate_main_body(
        pages
    )

    candidates = (
        collect_heading_candidates(
            pages,
            start_position,
            end_position,
        )
    )

    start_page = pages[
        start_position[0]
    ]["page_number"]

    end_page = (
        pages[end_position[0]][
            "page_number"
        ]
        if end_position
        else None
    )

    print(
        "\nMedicalPlab Structure Audit v3"
    )
    print("=" * 42)

    print(
        f"Document           : "
        f"{args.document_id}"
    )

    print(
        f"Total PDF pages    : "
        f"{len(pages)}"
    )

    print(
        f"Core body starts   : "
        f"Page {start_page}"
    )

    print(
        f"Core body ends     : "
        f"Page {end_page}"
        if end_page
        else "Core body ends     : EOF"
    )

    print(
        f"Heading candidates : "
        f"{len(candidates)}"
    )

    print_heading_summary(
        candidates
    )

    print("\nDetected Core Structure")
    print("-" * 110)

    for item in candidates:
        print(
            f"P{item['page_number']:>2} "
            f"L{item['line_number']:<3} "
            f"[{item['heading_type']:<22}] | "
            f"{item['text']}"
        )


if __name__ == "__main__":
    main()