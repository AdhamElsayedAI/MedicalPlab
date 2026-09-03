import argparse
import hashlib
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


CRITICAL_BLOCK_TYPES = {
    "recommendation",
    "implementation_remarks",
    "evidence_rationale",
    "evidence_to_decision",
}


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON object from disk."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return data


def save_json(
    path: Path,
    data: dict[str, Any],
) -> None:
    """Save JSON using UTF-8."""
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


def normalize_for_comparison(text: str) -> str:
    """
    Normalize only whitespace.

    Medical wording, punctuation, numbers and symbols
    remain unchanged.
    """
    return re.sub(
        r"\s+",
        " ",
        text.strip(),
    )


def sha256_text(text: str) -> str:
    """Generate SHA-256 for normalized UTF-8 text."""
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def extract_core_body(
    pages: list[dict[str, Any]],
) -> str:
    """
    Extract the same core-body range used by the parser.

    Start:
        1 Introduction

    End:
        References
    """
    body_lines: list[str] = []

    started = False
    finished = False

    for page in pages:
        text = page.get(
            "text",
            "",
        )

        if not isinstance(text, str):
            continue

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not started:
                if (
                    line.casefold()
                    == "1 introduction"
                ):
                    started = True
                else:
                    continue

            if (
                started
                and line.casefold()
                == "references"
            ):
                finished = True
                break

            body_lines.append(
                line
            )

        if finished:
            break

    if not started:
        raise ValueError(
            "Could not locate core-body start."
        )

    if not finished:
        raise ValueError(
            "Could not locate core-body end."
        )

    return normalize_for_comparison(
        "\n".join(body_lines)
    )


def reconstruct_from_sections(
    sections: list[dict[str, Any]],
) -> str:
    """
    Reconstruct the parsed body in original block order.

    If parsing was lossless, this normalized text should
    exactly equal the normalized source core body.
    """
    parts: list[str] = []

    for section in sections:
        heading = section.get(
            "heading",
            "",
        )

        text = section.get(
            "text",
            "",
        )

        if heading:
            parts.append(
                str(heading)
            )

        if text:
            parts.append(
                str(text)
            )

    return normalize_for_comparison(
        "\n".join(parts)
    )


def find_first_mismatch(
    source: str,
    reconstructed: str,
) -> int | None:
    """Return first differing character index."""
    limit = min(
        len(source),
        len(reconstructed),
    )

    for index in range(limit):
        if (
            source[index]
            != reconstructed[index]
        ):
            return index

    if len(source) != len(reconstructed):
        return limit

    return None


def build_context(
    text: str,
    position: int,
    radius: int = 100,
) -> str:
    """Return text around a mismatch."""
    start = max(
        0,
        position - radius,
    )

    end = min(
        len(text),
        position + radius,
    )

    return text[
        start:end
    ]


def validate_block_indexes(
    sections: list[dict[str, Any]],
) -> list[str]:
    """Ensure block_index is sequential."""
    errors: list[str] = []

    expected = list(
        range(
            1,
            len(sections) + 1,
        )
    )

    actual = [
        section.get(
            "block_index"
        )
        for section in sections
    ]

    if actual != expected:
        errors.append(
            "block_index values are not sequential."
        )

    return errors


def validate_page_ranges(
    sections: list[dict[str, Any]],
) -> list[str]:
    """Validate provenance page ranges."""
    errors: list[str] = []

    previous_start_page = 0

    for section in sections:
        block_index = section.get(
            "block_index",
            "?",
        )

        start_page = section.get(
            "start_page"
        )

        end_page = section.get(
            "end_page"
        )

        if not isinstance(
            start_page,
            int,
        ):
            errors.append(
                f"Block {block_index}: "
                "invalid start_page."
            )
            continue

        if not isinstance(
            end_page,
            int,
        ):
            errors.append(
                f"Block {block_index}: "
                "invalid end_page."
            )
            continue

        if end_page < start_page:
            errors.append(
                f"Block {block_index}: "
                "end_page is before start_page."
            )

        if start_page < previous_start_page:
            errors.append(
                f"Block {block_index}: "
                "page order is not monotonic."
            )

        previous_start_page = start_page

    return errors


def find_empty_blocks(
    sections: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """
    Separate acceptable structural empties from dangerous
    semantic empties.
    """
    allowed_empty: list[
        dict[str, Any]
    ] = []

    critical_empty: list[
        dict[str, Any]
    ] = []

    for section in sections:
        text = str(
            section.get(
                "text",
                "",
            )
        ).strip()

        if text:
            continue

        block_type = section.get(
            "block_type"
        )

        item = {
            "block_index": section.get(
                "block_index"
            ),
            "block_type": block_type,
            "heading": section.get(
                "heading"
            ),
        }

        if block_type in CRITICAL_BLOCK_TYPES:
            critical_empty.append(
                item
            )
        else:
            allowed_empty.append(
                item
            )

    return (
        allowed_empty,
        critical_empty,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate MedicalPlab section parsing "
            "for loss, duplication and provenance."
        )
    )

    parser.add_argument(
        "document_id",
    )

    parser.add_argument(
        "--specialty",
        default="Cardiology",
    )

    args = parser.parse_args()

    specialty = normalize_folder_name(
        args.specialty
    )

    cleaned_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.cleaned.json"
    )

    sections_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.sections.json"
    )

    if not cleaned_path.exists():
        raise FileNotFoundError(
            f"Missing cleaned document: "
            f"{cleaned_path}"
        )

    if not sections_path.exists():
        raise FileNotFoundError(
            f"Missing section output: "
            f"{sections_path}"
        )

    cleaned_document = load_json(
        cleaned_path
    )

    parsed_document = load_json(
        sections_path
    )

    pages = cleaned_document.get(
        "pages",
        [],
    )

    sections = parsed_document.get(
        "sections",
        [],
    )

    if not isinstance(
        pages,
        list,
    ):
        raise ValueError(
            "Cleaned pages must be a list."
        )

    if not isinstance(
        sections,
        list,
    ):
        raise ValueError(
            "Parsed sections must be a list."
        )

    source_body = extract_core_body(
        pages
    )

    reconstructed_body = (
        reconstruct_from_sections(
            sections
        )
    )

    source_hash = sha256_text(
        source_body
    )

    reconstructed_hash = sha256_text(
        reconstructed_body
    )

    exact_match = (
        source_body
        == reconstructed_body
    )

    mismatch_position = None

    source_context = None
    reconstructed_context = None

    if not exact_match:
        mismatch_position = (
            find_first_mismatch(
                source_body,
                reconstructed_body,
            )
        )

        if mismatch_position is not None:
            source_context = build_context(
                source_body,
                mismatch_position,
            )

            reconstructed_context = (
                build_context(
                    reconstructed_body,
                    mismatch_position,
                )
            )

    validation_errors: list[str] = []

    validation_errors.extend(
        validate_block_indexes(
            sections
        )
    )

    validation_errors.extend(
        validate_page_ranges(
            sections
        )
    )

    (
        allowed_empty,
        critical_empty,
    ) = find_empty_blocks(
        sections
    )

    if critical_empty:
        validation_errors.append(
            "One or more semantic blocks "
            "contain no content."
        )

    if not exact_match:
        validation_errors.append(
            "Parsed content does not exactly "
            "reconstruct the normalized core body."
        )

    passed = (
        not validation_errors
    )

    report = {
        "document_id": args.document_id,
        "validated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "validation_status": (
            "pass"
            if passed
            else "needs_review"
        ),
        "total_blocks": len(
            sections
        ),
        "source_characters": len(
            source_body
        ),
        "reconstructed_characters": len(
            reconstructed_body
        ),
        "exact_content_match": exact_match,
        "source_sha256": source_hash,
        "reconstructed_sha256": (
            reconstructed_hash
        ),
        "allowed_empty_block_count": len(
            allowed_empty
        ),
        "critical_empty_block_count": len(
            critical_empty
        ),
        "allowed_empty_blocks": (
            allowed_empty
        ),
        "critical_empty_blocks": (
            critical_empty
        ),
        "validation_errors": (
            validation_errors
        ),
        "first_mismatch_position": (
            mismatch_position
        ),
        "source_context_at_mismatch": (
            source_context
        ),
        "parsed_context_at_mismatch": (
            reconstructed_context
        ),
    }

    report_path = (
        PROCESSED_DIR
        / specialty
        / (
            f"{args.document_id}"
            ".sections.validation.json"
        )
    )

    save_json(
        report_path,
        report,
    )

    print(
        "\nMedicalPlab Section Integrity Validator"
    )
    print("=" * 44)

    print(
        f"Document               : "
        f"{args.document_id}"
    )

    print(
        f"Parsed blocks          : "
        f"{len(sections)}"
    )

    print(
        f"Source characters      : "
        f"{len(source_body):,}"
    )

    print(
        f"Reconstructed chars    : "
        f"{len(reconstructed_body):,}"
    )

    print(
        f"Exact content match    : "
        f"{'YES ✅' if exact_match else 'NO ❌'}"
    )

    print(
        f"Allowed empty blocks   : "
        f"{len(allowed_empty)}"
    )

    print(
        f"Critical empty blocks  : "
        f"{len(critical_empty)}"
    )

    print(
        f"Validation             : "
        f"{'PASS ✅' if passed else 'NEEDS REVIEW ❌'}"
    )

    if allowed_empty:
        print(
            "\nStructural empty blocks "
            "(allowed):"
        )

        for item in allowed_empty:
            print(
                f"#{item['block_index']:>2} "
                f"[{item['block_type']}] "
                f"{item['heading']}"
            )

    if critical_empty:
        print(
            "\nCRITICAL empty blocks:"
        )

        for item in critical_empty:
            print(
                f"#{item['block_index']:>2} "
                f"[{item['block_type']}] "
                f"{item['heading']}"
            )

    if not exact_match:
        print(
            "\nFirst mismatch:"
        )

        print(
            f"Position: "
            f"{mismatch_position}"
        )

        print(
            "\nSOURCE:"
        )

        print(
            source_context
        )

        print(
            "\nPARSED:"
        )

        print(
            reconstructed_context
        )

    print(
        f"\nReport                 : "
        f"{report_path}"
    )


if __name__ == "__main__":
    main()