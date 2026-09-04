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


# Maximum percentage of source text that the cleaning
# stage is allowed to remove automatically.
MAX_REMOVAL_RATIO = 0.05


# ---------------------------------------------------------------------
# Confirmed PDF layout artifacts
#
# IMPORTANT:
# These values were confirmed manually from the current WHO
# hypertension guideline.
#
# They are NOT removed globally from medical text.
# They are removed only when they occur at a page edge.
#
# This is especially important for values such as "DNA",
# which could be legitimate medical content elsewhere.
# ---------------------------------------------------------------------

CONFIRMED_EDGE_ARTIFACTS = {
    # Repeated document footer
    "guideline for the pharmacological treatment of hypertension in adults",

    # Reversed vertical page labels
    "snoitadnemmocer",
    "sexenna",
    "secnerefer",

    # Front matter
    "stnemegdelwonkca",
    "snoitaiverbba",
    "dna",
    "smynorca",
    "yrammus",
    "evitucexe",

    # Introduction
    "noitcudortni",

    # Method / guideline vertical labels
    "enilediug",
    "eht",
    "gnipoleved",
    "rof",
    "dohtem",

    # Special settings
    "sgnittes",
    "laiceps",

    # Publication / implementation / research gaps
    "spag",
    "hcraeser",
    "noitaulave",
    ",noitatnemelpmi",
    ",noitacilbup",

    # Implementation tools
    "sloot",
    "noitatnemelpmi",
}


def load_json(path: Path) -> dict[str, Any]:
    """
    Load a JSON object from disk.
    """
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
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
    """
    Save JSON using UTF-8.
    """
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


def normalize_folder_name(
    value: str,
) -> str:
    """
    Convert a specialty name into a safe folder name.
    """
    return (
        value.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )


def normalize_edge_line(
    line: str,
) -> str:
    """
    Normalize a possible page-edge artifact.

    Examples:

        "2 GUIDELINE FOR ..."
            ->
        "guideline for ..."

        "iv GUIDELINE FOR ..."
            ->
        "guideline for ..."

        "GUIDELINE FOR ... 2"
            ->
        "guideline for ..."

    This function is used only for artifact comparison.
    It does not rewrite source medical content.
    """
    value = line.strip()

    if not value:
        return ""

    # Remove a leading printed page number or Roman numeral.
    value = re.sub(
        r"^(?:\d{1,3}|[ivxlcdm]{1,8})\s+",
        "",
        value,
        flags=re.IGNORECASE,
    )

    # Remove a trailing printed page number or Roman numeral.
    value = re.sub(
        r"\s+(?:\d{1,3}|[ivxlcdm]{1,8})$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\s+",
        " ",
        value.strip(),
    )

    return value.casefold()


def is_terminal_page_number(
    line: str,
) -> bool:
    """
    Detect a standalone printed page marker.

    Examples:
        1
        25
        iv
        vii

    IMPORTANT:
    This function alone never causes removal.

    A page number is removed only when it is directly
    attached to a confirmed artifact cluster at a page edge.
    """
    value = line.strip().casefold()

    if not value:
        return False

    return bool(
        re.fullmatch(
            r"(?:\d{1,3}|[ivxlcdm]{1,8})",
            value,
        )
    )


def get_non_empty_indexes(
    lines: list[str],
    removed_indexes: set[int],
) -> list[int]:
    """
    Return indexes of currently active non-empty lines.
    """
    return [
        index
        for index, line in enumerate(lines)
        if (
            index not in removed_indexes
            and line.strip()
        )
    ]


def clean_page(
    text: str,
) -> tuple[
    str,
    list[str],
]:
    """
    Safely clean one extracted PDF page.

    Strategy:
        1. Preserve all original medical text.
        2. Peel only confirmed artifacts from page edges.
        3. Remove a standalone printed page number only
           when it is attached directly to an artifact cluster.
        4. Never rewrite medical wording.
        5. Never perform LLM-based cleaning.

    Returns:
        cleaned_text
        removed_lines
    """
    if not isinstance(text, str):
        return "", []

    if not text:
        return "", []

    lines = text.splitlines()

    removed_indexes: set[int] = set()

    # -------------------------------------------------------------
    # BOTTOM EDGE PEELING
    #
    # Example:
    #
    # ENILEDIUG
    # EHT
    # GNIPOLEVED
    # ROF
    # DOHTEM
    # 3
    #
    # We first remove "3" only because the line directly above
    # is a confirmed artifact.
    #
    # Then the confirmed artifacts are peeled one at a time.
    # -------------------------------------------------------------

    while True:
        indexes = get_non_empty_indexes(
            lines,
            removed_indexes,
        )

        if not indexes:
            break

        last_index = indexes[-1]

        last_line = (
            lines[last_index]
            .strip()
        )

        normalized_last = normalize_edge_line(
            last_line
        )

        # Confirmed artifact itself.
        if (
            normalized_last
            in CONFIRMED_EDGE_ARTIFACTS
        ):
            removed_indexes.add(
                last_index
            )
            continue

        # Standalone page number below an artifact cluster.
        if is_terminal_page_number(
            last_line
        ):
            if len(indexes) >= 2:
                previous_index = (
                    indexes[-2]
                )

                previous_line = (
                    lines[
                        previous_index
                    ]
                    .strip()
                )

                normalized_previous = (
                    normalize_edge_line(
                        previous_line
                    )
                )

                if (
                    normalized_previous
                    in CONFIRMED_EDGE_ARTIFACTS
                ):
                    removed_indexes.add(
                        last_index
                    )
                    continue

            # Standalone number without confirmed artifact
            # directly above it: preserve it.
            break

        break

    # -------------------------------------------------------------
    # TOP EDGE PEELING
    #
    # Same conservative logic for artifacts appearing at
    # the start of a PDF page.
    # -------------------------------------------------------------

    while True:
        indexes = get_non_empty_indexes(
            lines,
            removed_indexes,
        )

        if not indexes:
            break

        first_index = indexes[0]

        first_line = (
            lines[first_index]
            .strip()
        )

        normalized_first = normalize_edge_line(
            first_line
        )

        if (
            normalized_first
            in CONFIRMED_EDGE_ARTIFACTS
        ):
            removed_indexes.add(
                first_index
            )
            continue

        # Standalone page number above an artifact cluster.
        if is_terminal_page_number(
            first_line
        ):
            if len(indexes) >= 2:
                next_index = (
                    indexes[1]
                )

                next_line = (
                    lines[
                        next_index
                    ]
                    .strip()
                )

                normalized_next = (
                    normalize_edge_line(
                        next_line
                    )
                )

                if (
                    normalized_next
                    in CONFIRMED_EDGE_ARTIFACTS
                ):
                    removed_indexes.add(
                        first_index
                    )
                    continue

            break

        break

    # Preserve the exact order of all remaining lines.
    cleaned_lines = [
        line
        for index, line in enumerate(lines)
        if index not in removed_indexes
    ]

    cleaned_text = "\n".join(
        cleaned_lines
    ).strip()

    removed_lines = [
        lines[index].strip()
        for index in sorted(
            removed_indexes
        )
        if lines[index].strip()
    ]

    return (
        cleaned_text,
        removed_lines,
    )


def calculate_document_characters(
    pages: list[dict[str, Any]],
) -> int:
    """
    Calculate total characters in document page text.
    """
    total = 0

    for page in pages:
        text = page.get(
            "text",
            "",
        )

        if isinstance(text, str):
            total += len(text)

    return total


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Safely remove confirmed PDF layout "
            "artifacts from an extracted MedicalPlab document."
        )
    )

    parser.add_argument(
        "document_id",
        help=(
            "Document ID, for example "
            "DOC-WHO-CARD-0001"
        ),
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

    input_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.json"
    )

    output_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.cleaned.json"
    )

    report_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.cleaning.json"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Extracted document not found: "
            f"{input_path}"
        )

    document = load_json(
        input_path
    )

    pages = document.get(
        "pages",
        [],
    )

    if not isinstance(
        pages,
        list,
    ):
        raise ValueError(
            "Document 'pages' field must be a list."
        )

    if not pages:
        raise ValueError(
            "Document contains no extracted pages."
        )

    original_characters = (
        calculate_document_characters(
            pages
        )
    )

    if original_characters <= 0:
        raise ValueError(
            "Document contains no extractable text."
        )

    cleaned_pages: list[
        dict[str, Any]
    ] = []

    removed_artifacts: list[
        dict[str, Any]
    ] = []

    pages_modified = 0

    print(
        "\nMedicalPlab Safe Cleaning"
    )
    print("=" * 32)

    print(
        f"Document : "
        f"{args.document_id}"
    )

    print(
        f"Pages    : "
        f"{len(pages)}"
    )

    print(
        "Cleaning : confirmed artifacts only..."
    )

    for page_position, page in enumerate(
        pages,
        start=1,
    ):
        if not isinstance(
            page,
            dict,
        ):
            raise ValueError(
                f"Page #{page_position} "
                "must be a JSON object."
            )

        original_text = page.get(
            "text",
            "",
        )

        if not isinstance(
            original_text,
            str,
        ):
            original_text = ""

        (
            cleaned_text,
            removed_lines,
        ) = clean_page(
            original_text
        )

        if (
            cleaned_text
            != original_text.strip()
        ):
            pages_modified += 1

        page_number = page.get(
            "page_number",
            page_position,
        )

        for removed_line in removed_lines:
            removed_artifacts.append(
                {
                    "page_number": (
                        page_number
                    ),
                    "text": (
                        removed_line
                    ),
                }
            )

        cleaned_page = dict(
            page
        )

        cleaned_page[
            "text"
        ] = cleaned_text

        cleaned_page[
            "character_count"
        ] = len(
            cleaned_text
        )

        cleaned_page[
            "has_text"
        ] = bool(
            cleaned_text.strip()
        )

        cleaned_pages.append(
            cleaned_page
        )

    cleaned_characters = (
        calculate_document_characters(
            cleaned_pages
        )
    )

    removed_characters = (
        original_characters
        - cleaned_characters
    )

    removal_ratio = (
        removed_characters
        / original_characters
    )

    quality_errors: list[str] = []

    if cleaned_characters <= 0:
        quality_errors.append(
            "Cleaning removed all document text."
        )

    if removal_ratio < 0:
        quality_errors.append(
            "Cleaned document is larger than source "
            "in an unexpected way."
        )

    if removal_ratio > MAX_REMOVAL_RATIO:
        quality_errors.append(
            "Automatic cleaning removed more than "
            f"{MAX_REMOVAL_RATIO:.0%} of source text."
        )

    if len(cleaned_pages) != len(pages):
        quality_errors.append(
            "Page count changed during cleaning."
        )

    quality_status = (
        "pass"
        if not quality_errors
        else "needs_review"
    )

    cleaned_document = {
        key: value
        for key, value
        in document.items()
        if key != "pages"
    }

    cleaned_document[
        "cleaning"
    ] = {
        "pipeline_version": "v2",
        "strategy": (
            "confirmed_edge_artifact_peeling"
        ),
        "cleaned_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "maximum_removal_ratio": (
            MAX_REMOVAL_RATIO
        ),
        "artifact_policy": (
            "document_confirmed_page_edge_only"
        ),
    }

    cleaned_document[
        "pages"
    ] = cleaned_pages

    cleaning_report = {
        "document_id": (
            args.document_id
        ),
        "status": (
            quality_status
        ),
        "page_count": (
            len(pages)
        ),
        "original_characters": (
            original_characters
        ),
        "cleaned_characters": (
            cleaned_characters
        ),
        "removed_characters": (
            removed_characters
        ),
        "removal_ratio": round(
            removal_ratio,
            6,
        ),
        "pages_modified": (
            pages_modified
        ),
        "removed_artifact_count": (
            len(
                removed_artifacts
            )
        ),
        "removed_artifacts": (
            removed_artifacts
        ),
        "quality_errors": (
            quality_errors
        ),
    }

    save_json(
        output_path,
        cleaned_document,
    )

    save_json(
        report_path,
        cleaning_report,
    )

    print(
        "\nCLEANING COMPLETE ✅"
        if quality_status == "pass"
        else "\nCLEANING NEEDS REVIEW ❌"
    )

    print(
        f"Original chars : "
        f"{original_characters:,}"
    )

    print(
        f"Cleaned chars  : "
        f"{cleaned_characters:,}"
    )

    print(
        f"Chars removed  : "
        f"{removed_characters:,}"
    )

    print(
        f"Removal ratio  : "
        f"{removal_ratio:.2%}"
    )

    print(
        f"Pages modified : "
        f"{pages_modified}"
    )

    print(
        f"Artifacts      : "
        f"{len(removed_artifacts)}"
    )

    print(
        f"Quality        : "
        f"{'PASS' if quality_status == 'pass' else 'NEEDS REVIEW'}"
    )

    print(
        f"Cleaned output : "
        f"{output_path}"
    )

    print(
        f"Audit report   : "
        f"{report_path}"
    )

    if removed_artifacts:
        print(
            "\nRemoved artifact samples:"
        )

        for item in removed_artifacts[
            :15
        ]:
            print(
                f"Page "
                f"{item['page_number']}: "
                f"{item['text']}"
            )

    if quality_errors:
        print(
            "\nQuality errors:"
        )

        for error in quality_errors:
            print(
                f"- {error}"
            )

        raise SystemExit(1)


if __name__ == "__main__":
    main()