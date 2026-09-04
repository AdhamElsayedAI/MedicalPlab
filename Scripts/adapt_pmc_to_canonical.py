import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MANIFEST_PATH = (
    PROJECT_ROOT
    / "Data"
    / "metadata"
    / "document_manifest.json"
)

PROCESSED_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
)


ALLOWED_BLOCK_TYPES = {
    "abstract",
    "paragraph",
    "table_caption",
    "table_row",
    "table_note",
    "figure_caption",
}


# ============================================================
# Generic helpers
# ============================================================

def load_json(
    path: Path,
) -> Any:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def write_json(
    path: Path,
    data: Any,
) -> None:
    temp_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temp_path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.write(
            "\n"
        )

    temp_path.replace(
        path
    )


def normalize_text(
    value: Any,
) -> str:
    if value is None:
        return ""

    return " ".join(
        str(value).split()
    ).strip()


def sha256_text(
    text: str,
) -> str:
    return hashlib.sha256(
        text.encode(
            "utf-8"
        )
    ).hexdigest()


# ============================================================
# Manifest
# ============================================================

def load_manifest() -> list[dict[str, Any]]:
    data = load_json(
        MANIFEST_PATH
    )

    if isinstance(
        data,
        list,
    ):
        return [
            item
            for item in data
            if isinstance(
                item,
                dict,
            )
        ]

    if isinstance(
        data,
        dict,
    ):
        documents = data.get(
            "documents",
            [],
        )

        if isinstance(
            documents,
            list,
        ):
            return [
                item
                for item in documents
                if isinstance(
                    item,
                    dict,
                )
            ]

    raise ValueError(
        "Unsupported document manifest structure."
    )


def find_document(
    document_id: str,
) -> dict[str, Any]:
    for document in load_manifest():
        if (
            document.get(
                "document_id"
            )
            == document_id
        ):
            return document

    raise ValueError(
        f"Document not found in manifest: "
        f"{document_id}"
    )


# ============================================================
# Table semantic context
# ============================================================

def cell_texts(
    row: dict[str, Any],
) -> list[str]:
    values: list[str] = []

    for cell in row.get(
        "cells",
        [],
    ):
        if isinstance(
            cell,
            dict,
        ):
            value = normalize_text(
                cell.get(
                    "text"
                )
            )
        else:
            value = normalize_text(
                cell
            )

        if value:
            values.append(
                value
            )

    return values


def build_table_context(
    tables: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Precompute:
      - table headers
      - category/group rows
      - group active for each data row

    Example:
      header:
        Name | Starting | Maintenance | Maximum ...

      group:
        Thiazide Diuretics

      data row:
        Chlorthalidone | ...
    """

    context: dict[
        str,
        dict[str, Any]
    ] = {}

    for table in tables:
        table_id = normalize_text(
            table.get(
                "table_id"
            )
        )

        if not table_id:
            continue

        rows = table.get(
            "rows",
            [],
        )

        headers: list[str] = []
        group_by_row: dict[
            int,
            str | None
        ] = {}

        header_rows: set[int] = set()
        group_rows: set[int] = set()

        current_group: str | None = None

        for row in rows:
            if not isinstance(
                row,
                dict,
            ):
                continue

            row_index = int(
                row.get(
                    "row_index",
                    0,
                )
            )

            values = cell_texts(
                row
            )

            is_header = bool(
                row.get(
                    "is_header",
                    False,
                )
            )

            if (
                is_header
                and values
            ):
                header_rows.add(
                    row_index
                )

                if (
                    not headers
                    and len(values) >= 2
                ):
                    headers = values

                continue

            # One-cell rows underneath a multi-column header
            # are usually drug classes / semantic groups.
            if (
                len(values) == 1
                and len(headers) >= 2
            ):
                current_group = (
                    values[0]
                )

                group_rows.add(
                    row_index
                )

                continue

            group_by_row[
                row_index
            ] = current_group

        context[
            table_id
        ] = {
            "headers": headers,
            "group_by_row": group_by_row,
            "header_rows": header_rows,
            "group_rows": group_rows,
            "label": normalize_text(
                table.get(
                    "label"
                )
            ),
            "caption": normalize_text(
                table.get(
                    "caption"
                )
            ),
        }

    return context


def render_table_row(
    block: dict[str, Any],
    table_context: dict[str, dict[str, Any]],
) -> tuple[str | None, str]:
    metadata = block.get(
        "metadata",
        {},
    )

    if not isinstance(
        metadata,
        dict,
    ):
        metadata = {}

    table_id = normalize_text(
        metadata.get(
            "table_id"
        )
    )

    row_index = int(
        metadata.get(
            "row_index",
            0,
        )
    )

    context = table_context.get(
        table_id,
        {},
    )

    header_rows = context.get(
        "header_rows",
        set(),
    )

    group_rows = context.get(
        "group_rows",
        set(),
    )

    if row_index in header_rows:
        return (
            None,
            "table_header",
        )

    if row_index in group_rows:
        return (
            None,
            "table_group",
        )

    cells = [
        normalize_text(
            value
        )
        for value in metadata.get(
            "cells",
            [],
        )
    ]

    cells = [
        value
        for value in cells
        if value
    ]

    if not cells:
        return (
            None,
            "empty_table_row",
        )

    label = normalize_text(
        context.get(
            "label"
        )
        or metadata.get(
            "table_label"
        )
    )

    caption = normalize_text(
        context.get(
            "caption"
        )
    )

    headers = context.get(
        "headers",
        [],
    )

    group = (
        context.get(
            "group_by_row",
            {}
        ).get(
            row_index
        )
    )

    parts: list[str] = []

    table_title = normalize_text(
        " ".join(
            value
            for value in [
                label,
                caption,
            ]
            if value
        )
    )

    if table_title:
        parts.append(
            table_title
        )

    if group:
        parts.append(
            f"Category: {group}"
        )

    labelled_values: list[str] = []

    for index, value in enumerate(
        cells
    ):
        if (
            index < len(headers)
            and headers[index]
        ):
            field_name = headers[
                index
            ]
        else:
            field_name = (
                f"Column {index + 1}"
            )

        labelled_values.append(
            f"{field_name}: {value}"
        )

    if labelled_values:
        parts.append(
            "; ".join(
                labelled_values
            )
        )

    return (
        " — ".join(
            parts
        ),
        "data",
    )


def table_group_for_block(
    block: dict[str, Any],
    table_context: dict[str, dict[str, Any]],
) -> str | None:
    """
    Return the semantic table group associated with a
    concrete data row.

    This does not change the source/JATS hierarchy.
    """

    metadata = block.get(
        "metadata",
        {},
    )

    if not isinstance(
        metadata,
        dict,
    ):
        return None

    table_id = normalize_text(
        metadata.get(
            "table_id"
        )
    )

    row_index = int(
        metadata.get(
            "row_index",
            0,
        )
    )

    context = table_context.get(
        table_id,
        {},
    )

    if not isinstance(
        context,
        dict,
    ):
        return None

    group_by_row = context.get(
        "group_by_row",
        {},
    )

    if not isinstance(
        group_by_row,
        dict,
    ):
        return None

    group = normalize_text(
        group_by_row.get(
            row_index
        )
    )

    return group or None


# ============================================================
# Canonical mapping
# ============================================================

def canonical_heading(
    block: dict[str, Any],
    text: str,
) -> str:
    block_type = normalize_text(
        block.get(
            "block_type"
        )
    )

    section_path = block.get(
        "section_path",
        [],
    )

    if not isinstance(
        section_path,
        list,
    ):
        section_path = []

    section_path = [
        normalize_text(
            value
        )
        for value in section_path
        if normalize_text(
            value
        )
    ]

    metadata = block.get(
        "metadata",
        {},
    )

    if not isinstance(
        metadata,
        dict,
    ):
        metadata = {}

    if block_type == "abstract":
        return "Abstract"

    if block_type in {
        "table_caption",
        "table_row",
        "table_note",
    }:
        label = normalize_text(
            metadata.get(
                "table_label"
            )
        )

        if label:
            return label

    if section_path:
        return section_path[
            -1
        ]

    if block_type == "figure_caption":
        return "Figure"

    return (
        text[:120]
        if text
        else block_type
    )


def adapt_block(
    block: dict[str, Any],
    *,
    block_index: int,
    rendered_text: str | None = None,
    retrieval_group: str | None = None,
) -> dict[str, Any]:
    block_type = normalize_text(
        block.get(
            "block_type"
        )
    )

    if block_type not in ALLOWED_BLOCK_TYPES:
        raise ValueError(
            f"Unsupported block type: "
            f"{block_type}"
        )

    text = normalize_text(
        rendered_text
        if rendered_text is not None
        else block.get(
            "text"
        )
    )

    if not text:
        raise ValueError(
            f"Empty canonical block: "
            f"{block.get('block_id')}"
        )

    section_path = block.get(
        "section_path",
        [],
    )

    if not isinstance(
        section_path,
        list,
    ):
        section_path = []

    section_path = [
        normalize_text(
            value
        )
        for value in section_path
        if normalize_text(
            value
        )
    ]

    retrieval_section_path = list(
        section_path
    )

    normalized_retrieval_group = (
        normalize_text(
            retrieval_group
        )
    )

    if (
        block_type == "table_row"
        and normalized_retrieval_group
    ):
        # The physical location of a broad table in JATS
        # can be narrower than the semantic category of an
        # individual row. Keep section_path source-faithful,
        # but replace its leaf only for retrieval context.
        if section_path:
            retrieval_section_path = [
                *section_path[:-1],
                normalized_retrieval_group,
            ]
        else:
            retrieval_section_path = [
                normalized_retrieval_group
            ]

    section_id_path = block.get(
        "section_id_path",
        [],
    )

    if not isinstance(
        section_id_path,
        list,
    ):
        section_id_path = []

    section_id_path = [
        normalize_text(
            value
        )
        for value in section_id_path
        if normalize_text(
            value
        )
    ]

    section_number = (
        section_id_path[-1]
        if section_id_path
        else None
    )

    parent_section_number = (
        section_id_path[-2]
        if len(
            section_id_path
        ) >= 2
        else None
    )

    parent_section_heading = (
        section_path[-2]
        if len(
            section_path
        ) >= 2
        else None
    )

    source_locator = normalize_text(
        block.get(
            "block_id"
        )
    )

    source_element_id = normalize_text(
        block.get(
            "source_element_id"
        )
    )

    canonical = {
        "block_index": (
            block_index
        ),
        "block_type": (
            block_type
        ),
        "section_number": (
            section_number
        ),
        "section_level": int(
            block.get(
                "section_depth",
                0,
            )
            or 0
        ),
        "heading": canonical_heading(
            block,
            text,
        ),
        "start_page": None,
        "start_line": None,
        "end_page": None,
        "text": text,
        "character_count": len(
            text
        ),
        "parent_section_number": (
            parent_section_number
        ),
        "parent_section_heading": (
            parent_section_heading
        ),
        "section_path": (
            section_path
        ),
        "retrieval_section_path": (
            retrieval_section_path
        ),
        "content_sha256": (
            sha256_text(
                text
            )
        ),
        "provenance_type": (
            "xml_element"
        ),
        "source_locator": (
            source_locator
        ),
        "source_format": (
            "pmc_jats_xml"
        ),
        "source_element_id": (
            source_element_id
            if source_element_id
            else None
        ),
    }

    return canonical


# ============================================================
# Validation
# ============================================================

def validate_canonical_blocks(
    sections: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []

    seen_hashes: set[str] = set()

    for expected_index, block in enumerate(
        sections,
        start=1,
    ):
        if (
            block.get(
                "block_index"
            )
            != expected_index
        ):
            errors.append(
                f"Non-sequential block index at "
                f"{expected_index}."
            )

        block_type = block.get(
            "block_type"
        )

        if block_type not in ALLOWED_BLOCK_TYPES:
            errors.append(
                f"Invalid block type at "
                f"B{expected_index:04d}: "
                f"{block_type}"
            )

        text = normalize_text(
            block.get(
                "text"
            )
        )

        if not text:
            errors.append(
                f"Empty text at "
                f"B{expected_index:04d}."
            )

        expected_hash = (
            sha256_text(
                text
            )
        )

        if (
            block.get(
                "content_sha256"
            )
            != expected_hash
        ):
            errors.append(
                f"Content hash mismatch at "
                f"B{expected_index:04d}."
            )

        if (
            block.get(
                "start_page"
            )
            is not None
        ):
            errors.append(
                f"JATS block has unexpected "
                f"start_page at "
                f"B{expected_index:04d}."
            )

        if (
            block.get(
                "end_page"
            )
            is not None
        ):
            errors.append(
                f"JATS block has unexpected "
                f"end_page at "
                f"B{expected_index:04d}."
            )

        if (
            block.get(
                "provenance_type"
            )
            != "xml_element"
        ):
            errors.append(
                f"Invalid provenance type at "
                f"B{expected_index:04d}."
            )

        content_hash = block.get(
            "content_sha256"
        )

        if content_hash in seen_hashes:
            # Not automatically an error:
            # identical evidence may legitimately occur.
            pass

        seen_hashes.add(
            content_hash
        )

    return errors


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Adapt normalized PMC JATS blocks "
            "to the MedicalPlab canonical "
            "source-block contract."
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

    specialty = (
        args.specialty
        .strip()
        .lower()
    )

    input_path = (
        PROCESSED_DIR
        / specialty
        / (
            f"{args.document_id}"
            ".jats.json"
        )
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"JATS extraction not found: "
            f"{input_path}"
        )

    document = find_document(
        args.document_id
    )

    data = load_json(
        input_path
    )

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "JATS normalized extraction must "
            "be a JSON object."
        )

    blocks = data.get(
        "blocks",
        [],
    )

    tables = data.get(
        "tables",
        [],
    )

    if not isinstance(
        blocks,
        list,
    ):
        raise ValueError(
            "blocks must be a list."
        )

    if not isinstance(
        tables,
        list,
    ):
        raise ValueError(
            "tables must be a list."
        )

    source = data.get(
        "source",
        {},
    )

    if not isinstance(
        source,
        dict,
    ):
        source = {}

    source_sha256 = normalize_text(
        source.get(
            "sha256"
        )
    )

    if len(
        source_sha256
    ) != 64:
        raise ValueError(
            "Missing or invalid JATS "
            "source SHA256."
        )

    print(
        "\nMedicalPlab PMC Canonical Adapter"
    )
    print("=" * 72)

    print(
        f"Document : {args.document_id}"
    )

    print(
        f"Input    : {input_path}"
    )

    print(
        f"Source   : PMC JATS XML"
    )

    print(
        f"SHA256   : {source_sha256}"
    )

    print(
        "Step 1   : building semantic "
        "table context..."
    )

    table_context = (
        build_table_context(
            tables
        )
    )

    print(
        "Step 2   : adapting JATS blocks "
        "to canonical source blocks..."
    )

    canonical_sections: list[
        dict[str, Any]
    ] = []

    skipped_header_rows = 0
    skipped_group_rows = 0
    skipped_empty_rows = 0

    source_type_counts: dict[
        str,
        int
    ] = {}

    canonical_type_counts: dict[
        str,
        int
    ] = {}

    for block in blocks:
        if not isinstance(
            block,
            dict,
        ):
            continue

        block_type = normalize_text(
            block.get(
                "block_type"
            )
        )

        source_type_counts[
            block_type
        ] = (
            source_type_counts.get(
                block_type,
                0,
            )
            + 1
        )

        rendered_text: str | None = None
        retrieval_group: str | None = None

        if block_type == "table_row":
            (
                rendered_text,
                row_kind,
            ) = render_table_row(
                block,
                table_context,
            )

            if row_kind == "table_header":
                skipped_header_rows += 1
                continue

            if row_kind == "table_group":
                skipped_group_rows += 1
                continue

            if row_kind == "empty_table_row":
                skipped_empty_rows += 1
                continue

            retrieval_group = (
                table_group_for_block(
                    block,
                    table_context,
                )
            )

        canonical = adapt_block(
            block,
            block_index=(
                len(
                    canonical_sections
                )
                + 1
            ),
            rendered_text=(
                rendered_text
            ),
            retrieval_group=(
                retrieval_group
            ),
        )

        canonical_sections.append(
            canonical
        )

        canonical_type = (
            canonical[
                "block_type"
            ]
        )

        canonical_type_counts[
            canonical_type
        ] = (
            canonical_type_counts.get(
                canonical_type,
                0,
            )
            + 1
        )

    print(
        "Step 3   : validating canonical "
        "contract..."
    )

    errors = (
        validate_canonical_blocks(
            canonical_sections
        )
    )

    status = (
        "PASS"
        if not errors
        else "REVIEW"
    )

    article = data.get(
        "article",
        {},
    )

    if not isinstance(
        article,
        dict,
    ):
        article = {}

    title = normalize_text(
        document.get(
            "title"
        )
        or article.get(
            "title"
        )
    )

    source_id = normalize_text(
        document.get(
            "source_id"
        )
    )

    medical_specialty = normalize_text(
        document.get(
            "medical_specialty"
        )
    )

    topics = document.get(
        "topics",
        [],
    )

    if not isinstance(
        topics,
        list,
    ):
        topics = []

    topics = [
        normalize_text(
            topic
        )
        for topic in topics
        if normalize_text(
            topic
        )
    ]

    now = datetime.now(
        timezone.utc
    ).isoformat()

    output = {
        "document_id": (
            args.document_id
        ),
        "source_id": (
            source_id
        ),
        "title": (
            title
        ),
        "medical_specialty": (
            medical_specialty
        ),
        "topics": (
            topics
        ),
        "source_sha256": (
            source_sha256
        ),
        "parsed_at": (
            now
        ),
        "parser": {
            "name": (
                "pmc_jats_canonical_adapter"
            ),
            "version": "1.0",
            "source_format": (
                "pmc_jats_xml"
            ),
        },
        "enrichment": {
            "provenance_type": (
                "xml_element"
            ),
            "semantic_table_rows": (
                True
            ),
            "table_header_rows_embedded": (
                True
            ),
            "table_group_rows_embedded": (
                True
            ),
            "references_included": (
                False
            ),
        },
        "sections": (
            canonical_sections
        ),
    }

    quality = {
        "document_id": (
            args.document_id
        ),
        "status": (
            status
        ),
        "source_format": (
            "pmc_jats_xml"
        ),
        "source_sha256": (
            source_sha256
        ),
        "source_block_count": (
            len(
                blocks
            )
        ),
        "canonical_block_count": (
            len(
                canonical_sections
            )
        ),
        "source_block_type_counts": (
            source_type_counts
        ),
        "canonical_block_type_counts": (
            canonical_type_counts
        ),
        "skipped_structural_table_rows": {
            "header_rows": (
                skipped_header_rows
            ),
            "group_rows": (
                skipped_group_rows
            ),
            "empty_rows": (
                skipped_empty_rows
            ),
        },
        "validation_errors": (
            errors
        ),
    }

    output_dir = (
        PROCESSED_DIR
        / specialty
    )

    output_path = (
        output_dir
        / (
            f"{args.document_id}"
            ".sections.enriched.json"
        )
    )

    quality_path = (
        output_dir
        / (
            f"{args.document_id}"
            ".sections.enrichment.json"
        )
    )

    write_json(
        output_path,
        output,
    )

    write_json(
        quality_path,
        quality,
    )

    # ========================================================
    # Report
    # ========================================================

    print(
        "\nCanonical Adapter Summary"
    )

    print("-" * 72)

    print(
        f"Source JATS blocks      : "
        f"{len(blocks)}"
    )

    print(
        f"Canonical blocks        : "
        f"{len(canonical_sections)}"
    )

    print(
        f"Skipped table headers   : "
        f"{skipped_header_rows}"
    )

    print(
        f"Skipped table groups    : "
        f"{skipped_group_rows}"
    )

    print(
        f"Skipped empty rows      : "
        f"{skipped_empty_rows}"
    )

    print(
        "\nCanonical Block Types"
    )

    print("-" * 72)

    for block_type, count in sorted(
        canonical_type_counts.items()
    ):
        print(
            f"{block_type:<20}: "
            f"{count}"
        )

    print(
        "\nProvenance"
    )

    print("-" * 72)

    print(
        "start_page       : null"
    )

    print(
        "end_page         : null"
    )

    print(
        "provenance_type  : xml_element"
    )

    print(
        "source_format    : pmc_jats_xml"
    )

    print(
        "\n"
        + "=" * 72
    )

    print(
        f"Validation      : "
        f"{status}"
        + (
            " ✅"
            if status == "PASS"
            else " ⚠️"
        )
    )

    if errors:
        for error in errors:
            print(
                f"ERROR           : "
                f"{error}"
            )

    print(
        f"Output          : "
        f"{output_path}"
    )

    print(
        f"Quality report  : "
        f"{quality_path}"
    )


if __name__ == "__main__":
    main()