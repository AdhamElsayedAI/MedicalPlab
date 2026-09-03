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


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "Expected document JSON object."
        )

    return data


def save_json(
    path: Path,
    data: dict[str, Any],
) -> None:
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
    )


def is_numbered_section(line: str) -> bool:
    line = line.strip()

    if re.match(
        r"^\d+(?:\.\d+)+\s+[A-Z][A-Za-z]",
        line,
    ):
        return True

    if re.match(
        r"^\d+\s+[A-Z][A-Za-z]",
        line,
    ):
        return True

    return False


def get_section_number(
    line: str,
) -> str | None:
    match = re.match(
        r"^(\d+(?:\.\d+)*)\s+",
        line.strip(),
    )

    if not match:
        return None

    return match.group(1)


def get_section_level(
    section_number: str | None,
) -> int:
    if not section_number:
        return 0

    return len(
        section_number.split(".")
    )


def is_recommendation_heading(line: str) -> bool:
    return bool(
        re.match(
            r"^\d+\.\s+RECOMMENDATIONS?\b",
            line.strip(),
        )
    )


def is_block_heading(line: str) -> bool:
    lowered = line.strip().casefold()

    return lowered in {
        "implementation remarks:",
        "implementation remarks",
        "evidence and rationale",
        "evidence-to-decision considerations",
    }


def classify_block_heading(
    line: str,
) -> str | None:
    lowered = line.strip().casefold()

    if lowered.startswith(
        "implementation remarks"
    ):
        return "implementation_remarks"

    if lowered == "evidence and rationale":
        return "evidence_rationale"

    if lowered == (
        "evidence-to-decision considerations"
    ):
        return "evidence_to_decision"

    if is_recommendation_heading(line):
        return "recommendation"

    return None


def is_uppercase_continuation(line: str) -> bool:
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


def should_merge_heading_continuation(
    heading: str,
    next_line: str,
) -> bool:
    heading = heading.strip()
    next_line = next_line.strip()

    if not heading or not next_line:
        return False

    if is_numbered_section(next_line):
        return False

    if is_recommendation_heading(next_line):
        return False

    if is_block_heading(next_line):
        return False

    if len(next_line) > 120:
        return False

    first_alpha = next(
        (
            char
            for char in next_line
            if char.isalpha()
        ),
        None,
    )

    if first_alpha is None:
        return False

    if not first_alpha.islower():
        return False

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

    return heading.casefold().endswith(
        dangling_endings
    )


def locate_main_body(
    pages: list[dict[str, Any]],
) -> tuple[
    tuple[int, int],
    tuple[int, int],
]:
    start_position = None
    end_position = None

    for page_index, page in enumerate(pages):
        text = page.get(
            "text",
            "",
        )

        if not isinstance(text, str):
            continue

        lines = text.splitlines()

        for line_index, raw_line in enumerate(lines):
            line = raw_line.strip()

            if (
                start_position is None
                and line.casefold()
                == "1 introduction"
            ):
                start_position = (
                    page_index,
                    line_index,
                )

            elif (
                start_position is not None
                and line.casefold()
                == "references"
            ):
                end_position = (
                    page_index,
                    line_index,
                )

                break

        if end_position is not None:
            break

    if start_position is None:
        raise ValueError(
            "Could not locate main-body start."
        )

    if end_position is None:
        raise ValueError(
            "Could not locate main-body end."
        )

    return (
        start_position,
        end_position,
    )


def flatten_body_lines(
    pages: list[dict[str, Any]],
    start_position: tuple[int, int],
    end_position: tuple[int, int],
) -> list[dict[str, Any]]:
    """
    Convert the core body into one ordered line stream while
    preserving page and line provenance.
    """
    output = []

    for page_index, page in enumerate(pages):
        text = page.get(
            "text",
            "",
        )

        if not isinstance(text, str):
            continue

        lines = text.splitlines()

        for line_index, raw_line in enumerate(lines):
            position = (
                page_index,
                line_index,
            )

            if position < start_position:
                continue

            if position >= end_position:
                continue

            output.append(
                {
                    "page_number": page[
                        "page_number"
                    ],
                    "line_number": (
                        line_index + 1
                    ),
                    "text": raw_line.strip(),
                }
            )

    return output


def detect_heading_at(
    lines: list[dict[str, Any]],
    index: int,
) -> tuple[
    str | None,
    str | None,
    int,
]:
    """
    Detect and safely merge a heading.

    Returns:
        heading_type
        heading_text
        number_of_consumed_lines
    """
    line = lines[index][
        "text"
    ].strip()

    if not line:
        return None, None, 1

    if is_recommendation_heading(line):
        heading = line
        consumed = 1

        if index + 1 < len(lines):
            next_line = lines[
                index + 1
            ]["text"].strip()

            # Merge only if the continuation is on
            # the same PDF page.
            same_page = (
                lines[index]["page_number"]
                == lines[index + 1][
                    "page_number"
                ]
            )

            if (
                same_page
                and is_uppercase_continuation(
                    next_line
                )
            ):
                heading = (
                    f"{heading} {next_line}"
                )

                consumed = 2

        return (
            "recommendation",
            normalize_text(heading),
            consumed,
        )

    block_type = classify_block_heading(
        line
    )

    if block_type:
        return (
            block_type,
            normalize_text(line),
            1,
        )

    if is_numbered_section(line):
        heading = line
        consumed = 1

        if index + 1 < len(lines):
            next_line = lines[
                index + 1
            ]["text"].strip()

            same_page = (
                lines[index]["page_number"]
                == lines[index + 1][
                    "page_number"
                ]
            )

            if (
                same_page
                and should_merge_heading_continuation(
                    heading,
                    next_line,
                )
            ):
                heading = (
                    f"{heading} {next_line}"
                )

                consumed = 2

        return (
            "numbered_section",
            normalize_text(heading),
            consumed,
        )

    return None, None, 1


def build_sections(
    body_lines: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build ordered structural blocks.

    Every heading opens a block which consumes text until
    the next detected heading.
    """
    sections: list[dict[str, Any]] = []

    current_section: dict[str, Any] | None = None

    index = 0

    while index < len(body_lines):
        line_record = body_lines[index]

        (
            heading_type,
            heading_text,
            consumed,
        ) = detect_heading_at(
            body_lines,
            index,
        )

        if heading_type:
            if current_section is not None:
                current_section[
                    "text"
                ] = normalize_text(
                    "\n".join(
                        current_section[
                            "_text_lines"
                        ]
                    )
                )

                current_section.pop(
                    "_text_lines",
                    None,
                )

                sections.append(
                    current_section
                )

            section_number = None
            section_level = 0

            if heading_type == "numbered_section":
                section_number = (
                    get_section_number(
                        heading_text
                    )
                )

                section_level = (
                    get_section_level(
                        section_number
                    )
                )

            current_section = {
                "block_index": (
                    len(sections) + 1
                ),
                "block_type": heading_type,
                "section_number": section_number,
                "section_level": section_level,
                "heading": heading_text,
                "start_page": (
                    line_record[
                        "page_number"
                    ]
                ),
                "start_line": (
                    line_record[
                        "line_number"
                    ]
                ),
                "end_page": (
                    line_record[
                        "page_number"
                    ]
                ),
                "_text_lines": [],
            }

            index += consumed
            continue

        if current_section is not None:
            if line_record["text"]:
                current_section[
                    "_text_lines"
                ].append(
                    line_record[
                        "text"
                    ]
                )

            current_section[
                "end_page"
            ] = line_record[
                "page_number"
            ]

        index += 1

    if current_section is not None:
        current_section[
            "text"
        ] = normalize_text(
            "\n".join(
                current_section[
                    "_text_lines"
                ]
            )
        )

        current_section.pop(
            "_text_lines",
            None,
        )

        sections.append(
            current_section
        )

    # Re-number cleanly after finalization.
    for block_index, section in enumerate(
        sections,
        start=1,
    ):
        section[
            "block_index"
        ] = block_index

        section[
            "character_count"
        ] = len(
            section.get(
                "text",
                "",
            )
        )

    return sections


def build_report(
    document_id: str,
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    counts: dict[str, int] = {}

    for section in sections:
        block_type = section[
            "block_type"
        ]

        counts[block_type] = (
            counts.get(
                block_type,
                0,
            )
            + 1
        )

    empty_blocks = [
        section["block_index"]
        for section in sections
        if not section.get(
            "text",
            ""
        )
    ]

    return {
        "document_id": document_id,
        "total_blocks": len(
            sections
        ),
        "block_type_counts": counts,
        "empty_blocks": (
            empty_blocks
        ),
        "empty_block_count": len(
            empty_blocks
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a cleaned MedicalPlab document "
            "into structural blocks."
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

    (
        start_position,
        end_position,
    ) = locate_main_body(
        pages
    )

    body_lines = flatten_body_lines(
        pages,
        start_position,
        end_position,
    )

    sections = build_sections(
        body_lines
    )

    report = build_report(
        args.document_id,
        sections,
    )

    parsed_at = datetime.now(
        timezone.utc
    ).isoformat()

    output = {
        "document_id": document[
            "document_id"
        ],
        "source_id": document[
            "source_id"
        ],
        "title": document[
            "title"
        ],
        "medical_specialty": document[
            "medical_specialty"
        ],
        "topics": document[
            "topics"
        ],
        "source_sha256": document[
            "source_sha256"
        ],
        "parsed_at": parsed_at,
        "parser": {
            "pipeline_version": "v1",
            "strategy": (
                "core_body_structure_aware"
            ),
        },
        "sections": sections,
    }

    output_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.sections.json"
    )

    report_path = (
        PROCESSED_DIR
        / specialty
        / f"{args.document_id}.sections.quality.json"
    )

    save_json(
        output_path,
        output,
    )

    save_json(
        report_path,
        report,
    )

    print("\nMedicalPlab Section Parser")
    print("=" * 36)
    print(
        f"Document      : "
        f"{args.document_id}"
    )
    print(
        f"Body lines    : "
        f"{len(body_lines)}"
    )
    print(
        f"Parsed blocks : "
        f"{len(sections)}"
    )

    print("\nBlock Type Summary")
    print("-" * 40)

    for block_type, count in sorted(
        report[
            "block_type_counts"
        ].items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    ):
        print(
            f"{block_type:<28} "
            f"{count:>4}"
        )

    print(
        f"\nEmpty blocks  : "
        f"{report['empty_block_count']}"
    )

    print("\nParsed Structure Sample")
    print("-" * 100)

    for section in sections[:25]:
        print(
            f"#{section['block_index']:>2} "
            f"[{section['block_type']:<22}] "
            f"P{section['start_page']}"
            f"-P{section['end_page']} | "
            f"{section['heading']}"
        )

        text = section.get(
            "text",
            "",
        )

        if text:
            preview = (
                text[:180]
                .replace(
                    "\n",
                    " ",
                )
            )

            print(
                f"    {preview}"
            )

    print(
        f"\nOutput        : "
        f"{output_path}"
    )

    print(
        f"Quality report: "
        f"{report_path}"
    )


if __name__ == "__main__":
    main()