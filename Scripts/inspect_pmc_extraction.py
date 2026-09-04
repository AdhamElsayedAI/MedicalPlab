import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
)


def shorten(
    text: str,
    limit: int = 500,
) -> str:
    text = " ".join(
        text.split()
    )

    if len(text) <= limit:
        return text

    return (
        text[:limit]
        + " [...]"
    )


def print_block(
    block: dict[str, Any],
) -> None:
    print(
        f"Block ID      : {block.get('block_id')}"
    )

    print(
        f"Type          : {block.get('block_type')}"
    )

    print(
        f"Section depth : {block.get('section_depth')}"
    )

    print(
        "Section path  : "
        + " > ".join(
            block.get(
                "section_path",
                [],
            )
        )
    )

    print(
        f"Source elem   : "
        f"{block.get('source_element_id')}"
    )

    print(
        f"Text length   : "
        f"{len(block.get('text', ''))}"
    )

    print(
        "Text          : "
        + shorten(
            block.get(
                "text",
                "",
            )
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect normalized PMC JATS "
            "extraction samples."
        )
    )

    parser.add_argument(
        "document_id",
    )

    parser.add_argument(
        "--specialty",
        default="cardiology",
    )

    args = parser.parse_args()

    path = (
        PROCESSED_DIR
        / args.specialty.lower()
        / (
            f"{args.document_id}"
            ".jats.json"
        )
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Extraction not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    blocks = data.get(
        "blocks",
        [],
    )

    sections = data.get(
        "sections",
        [],
    )

    tables = data.get(
        "tables",
        [],
    )

    print(
        "\nMedicalPlab PMC Extraction Audit"
    )

    print("=" * 78)

    print(
        f"Document : {args.document_id}"
    )

    print(
        f"Sections : {len(sections)}"
    )

    print(
        f"Blocks   : {len(blocks)}"
    )

    print(
        f"Tables   : {len(tables)}"
    )

    # --------------------------------------------------------
    # Block distribution
    # --------------------------------------------------------

    block_types = Counter(
        block.get(
            "block_type"
        )
        for block in blocks
    )

    print(
        "\nBlock Type Distribution"
    )

    print("-" * 78)

    for block_type, count in sorted(
        block_types.items()
    ):
        print(
            f"{block_type:<20}: {count}"
        )

    # --------------------------------------------------------
    # Hierarchy
    # --------------------------------------------------------

    print(
        "\nSection Hierarchy"
    )

    print("-" * 78)

    for section in sections:
        depth = int(
            section.get(
                "depth",
                0,
            )
        )

        title = section.get(
            "title",
            "",
        )

        print(
            f"{'  ' * max(depth - 1, 0)}"
            f"- {title}"
        )

    # --------------------------------------------------------
    # Abstract
    # --------------------------------------------------------

    print(
        "\nAbstract Sample"
    )

    print("-" * 78)

    abstracts = [
        block
        for block in blocks
        if block.get(
            "block_type"
        ) == "abstract"
    ]

    if abstracts:
        print_block(
            abstracts[0]
        )
    else:
        print(
            "[NO ABSTRACT BLOCK]"
        )

    # --------------------------------------------------------
    # Paragraph samples
    # --------------------------------------------------------

    print(
        "\nParagraph Samples"
    )

    print("-" * 78)

    target_sections = [
        "Etiology",
        "Diagnostic criteria",
        "Pharmacological management",
        "Diuretics",
        "Monitoring and follow-up",
        "Conclusion",
    ]

    for target in target_sections:
        matches = [
            block
            for block in blocks
            if (
                block.get(
                    "block_type"
                )
                == "paragraph"
                and target
                in block.get(
                    "section_path",
                    [],
                )
            )
        ]

        print(
            f"\n### {target}"
        )

        if not matches:
            print(
                "[NO PARAGRAPH FOUND]"
            )

            continue

        print_block(
            matches[0]
        )

    # --------------------------------------------------------
    # Table 5
    # --------------------------------------------------------

    print(
        "\nTable 5 Audit"
    )

    print("-" * 78)

    table5 = None

    for table in tables:
        label = str(
            table.get(
                "label",
                "",
            )
        )

        if label.lower().startswith(
            "table 5"
        ):
            table5 = table
            break

    if table5 is None:
        print(
            "Table 5 not found ❌"
        )

    else:
        print(
            f"ID      : "
            f"{table5.get('table_id')}"
        )

        print(
            f"Label   : "
            f"{table5.get('label')}"
        )

        print(
            f"Caption : "
            f"{table5.get('caption')}"
        )

        rows = table5.get(
            "rows",
            [],
        )

        print(
            f"Rows    : {len(rows)}"
        )

        print(
            "\nFirst 12 structured rows:"
        )

        for row in rows[:12]:
            cells = row.get(
                "cells",
                [],
            )

            values = [
                str(
                    cell.get(
                        "text",
                        "",
                    )
                )
                for cell in cells
            ]

            print(
                f"\nROW "
                f"{row.get('row_index')}"
                f" | header="
                f"{row.get('is_header')}"
            )

            print(
                " | ".join(
                    values
                )
            )

    # --------------------------------------------------------
    # Table-row retrieval blocks
    # --------------------------------------------------------

    print(
        "\nTable 5 Retrieval Block Samples"
    )

    print("-" * 78)

    table5_blocks = [
        block
        for block in blocks
        if (
            block.get(
                "block_type"
            )
            == "table_row"
            and block.get(
                "metadata",
                {},
            ).get(
                "table_id"
            )
            == "t0005"
        )
    ]

    for block in table5_blocks[:8]:
        print(
            "\n"
            + "-" * 78
        )

        print_block(
            block
        )

    # --------------------------------------------------------
    # Basic text-quality warnings
    # --------------------------------------------------------

    print(
        "\nText Quality Checks"
    )

    print("-" * 78)

    empty_blocks = [
        block
        for block in blocks
        if not str(
            block.get(
                "text",
                "",
            )
        ).strip()
    ]

    duplicate_ids = [
        block_id
        for block_id, count in Counter(
            block.get(
                "block_id"
            )
            for block in blocks
        ).items()
        if count > 1
    ]

    suspicious_short_paragraphs = [
        block
        for block in blocks
        if (
            block.get(
                "block_type"
            )
            == "paragraph"
            and len(
                block.get(
                    "text",
                    "",
                )
            ) < 40
        )
    ]

    print(
        f"Empty blocks             : "
        f"{len(empty_blocks)}"
    )

    print(
        f"Duplicate block IDs      : "
        f"{len(duplicate_ids)}"
    )

    print(
        f"Paragraphs <40 chars     : "
        f"{len(suspicious_short_paragraphs)}"
    )

    if suspicious_short_paragraphs:
        print(
            "\nShort paragraph samples:"
        )

        for block in suspicious_short_paragraphs[
            :10
        ]:
            print(
                f"- "
                f"{block.get('section_path')} "
                f"=> "
                f"{block.get('text')!r}"
            )

    passed = (
        not empty_blocks
        and not duplicate_ids
    )

    print(
        "\n"
        + "=" * 78
    )

    print(
        "Audit result : "
        + (
            "PASS ✅"
            if passed
            else "REVIEW ⚠️"
        )
    )


if __name__ == "__main__":
    main()