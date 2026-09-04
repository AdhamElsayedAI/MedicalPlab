import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = (
    PROJECT_ROOT
    / "Data"
    / "raw"
)

PROCESSED_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
)


# ============================================================
# Basic helpers
# ============================================================

def local_name(
    tag: str,
) -> str:
    if "}" in tag:
        return tag.split("}")[-1]

    return tag


def normalize_text(
    text: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def element_text(
    element: ElementTree.Element | None,
) -> str:
    if element is None:
        return ""

    return normalize_text(
        " ".join(
            part.strip()
            for part in element.itertext()
            if part.strip()
        )
    )


def first_direct_child(
    element: ElementTree.Element,
    name: str,
) -> ElementTree.Element | None:
    for child in element:
        if local_name(
            child.tag
        ) == name:
            return child

    return None


def find_first_descendant(
    element: ElementTree.Element,
    name: str,
) -> ElementTree.Element | None:
    for item in element.iter():
        if local_name(
            item.tag
        ) == name:
            return item

    return None


def descendants_named(
    element: ElementTree.Element | None,
    name: str,
) -> list[ElementTree.Element]:
    if element is None:
        return []

    return [
        item
        for item in element.iter()
        if local_name(
            item.tag
        ) == name
    ]


def find_article(
    root: ElementTree.Element,
) -> ElementTree.Element:
    if local_name(
        root.tag
    ) == "article":
        return root

    for element in root.iter():
        if local_name(
            element.tag
        ) == "article":
            return element

    raise ValueError(
        "No JATS <article> element found."
    )


def sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb",
    ) as file:
        while True:
            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


# ============================================================
# Text extraction excluding structured objects
# ============================================================

EXCLUDED_FROM_PARAGRAPH = {
    "table-wrap",
    "fig",
    "ref-list",
}


def paragraph_text(
    paragraph: ElementTree.Element,
) -> str:
    """
    Extract paragraph text while excluding embedded
    tables, figures and reference lists.

    This prevents table/figure content from being
    duplicated inside the prose block.
    """

    pieces: list[str] = []

    def walk(
        node: ElementTree.Element,
    ) -> None:
        if node.text:
            pieces.append(
                node.text
            )

        for child in node:
            child_name = local_name(
                child.tag
            )

            if child_name not in EXCLUDED_FROM_PARAGRAPH:
                walk(
                    child
                )

            if child.tail:
                pieces.append(
                    child.tail
                )

    walk(
        paragraph
    )

    return normalize_text(
        " ".join(
            pieces
        )
    )


# ============================================================
# Metadata
# ============================================================

def extract_article_ids(
    front: ElementTree.Element | None,
) -> dict[str, str]:
    identifiers: dict[str, str] = {}

    if front is None:
        return identifiers

    for element in descendants_named(
        front,
        "article-id",
    ):
        id_type = (
            element.attrib.get(
                "pub-id-type",
                "unknown",
            )
            .strip()
            .lower()
        )

        value = element_text(
            element
        )

        if value:
            identifiers[
                id_type
            ] = value

    return identifiers


def extract_publication_year(
    front: ElementTree.Element | None,
) -> str | None:
    if front is None:
        return None

    for pub_date in descendants_named(
        front,
        "pub-date",
    ):
        year = find_first_descendant(
            pub_date,
            "year",
        )

        value = element_text(
            year
        )

        if value:
            return value

    return None


# ============================================================
# JATS normalized extractor
# ============================================================

class JATSExtractor:
    def __init__(
        self,
        document_id: str,
    ) -> None:
        self.document_id = (
            document_id
        )

        self.block_counter = 0
        self.section_counter = 0

        self.blocks: list[
            dict[str, Any]
        ] = []

        self.sections: list[
            dict[str, Any]
        ] = []

        self.tables: list[
            dict[str, Any]
        ] = []

        self.figures: list[
            dict[str, Any]
        ] = []

    # --------------------------------------------------------
    # IDs
    # --------------------------------------------------------

    def next_block_id(
        self,
    ) -> str:
        self.block_counter += 1

        return (
            f"{self.document_id}"
            f"-JATS-B"
            f"{self.block_counter:04d}"
        )

    def next_section_id(
        self,
    ) -> str:
        self.section_counter += 1

        return (
            f"{self.document_id}"
            f"-JATS-S"
            f"{self.section_counter:03d}"
        )

    # --------------------------------------------------------
    # Generic block creator
    # --------------------------------------------------------

    def add_block(
        self,
        *,
        block_type: str,
        text: str,
        section_path: list[str],
        section_id_path: list[str],
        section_depth: int,
        source_element_id: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        text = normalize_text(
            text
        )

        if not text:
            return None

        block = {
            "block_id": self.next_block_id(),
            "block_type": block_type,
            "text": text,
            "section_path": list(
                section_path
            ),
            "section_id_path": list(
                section_id_path
            ),
            "section_depth": (
                section_depth
            ),
            "source_element_id": (
                source_element_id
            ),
            "metadata": (
                metadata
                if metadata is not None
                else {}
            ),
        }

        self.blocks.append(
            block
        )

        return block

    # --------------------------------------------------------
    # Abstract
    # --------------------------------------------------------

    def process_abstracts(
        self,
        front: ElementTree.Element | None,
    ) -> None:
        if front is None:
            return

        abstracts = descendants_named(
            front,
            "abstract",
        )

        for index, abstract in enumerate(
            abstracts,
            start=1,
        ):
            text = element_text(
                abstract
            )

            if not text:
                continue

            self.add_block(
                block_type="abstract",
                text=text,
                section_path=[
                    "Abstract",
                ],
                section_id_path=[],
                section_depth=0,
                source_element_id=(
                    abstract.attrib.get(
                        "id"
                    )
                ),
                metadata={
                    "abstract_index": index,
                },
            )

    # --------------------------------------------------------
    # Paragraph
    # --------------------------------------------------------

    def process_paragraph(
        self,
        paragraph: ElementTree.Element,
        section_path: list[str],
        section_id_path: list[str],
        section_depth: int,
    ) -> None:
        text = paragraph_text(
            paragraph
        )

        self.add_block(
            block_type="paragraph",
            text=text,
            section_path=section_path,
            section_id_path=section_id_path,
            section_depth=section_depth,
            source_element_id=(
                paragraph.attrib.get(
                    "id"
                )
            ),
        )

        # Tables or figures may occasionally be nested
        # inside a paragraph in JATS.
        for child in paragraph:
            name = local_name(
                child.tag
            )

            if name == "table-wrap":
                self.process_table(
                    child,
                    section_path,
                    section_id_path,
                    section_depth,
                )

            elif name == "fig":
                self.process_figure(
                    child,
                    section_path,
                    section_id_path,
                    section_depth,
                )

    # --------------------------------------------------------
    # Table
    # --------------------------------------------------------

    def process_table(
        self,
        table_wrap: ElementTree.Element,
        section_path: list[str],
        section_id_path: list[str],
        section_depth: int,
    ) -> None:
        table_id = (
            table_wrap.attrib.get(
                "id"
            )
        )

        label = element_text(
            first_direct_child(
                table_wrap,
                "label",
            )
        )

        caption = element_text(
            first_direct_child(
                table_wrap,
                "caption",
            )
        )

        table_element = (
            find_first_descendant(
                table_wrap,
                "table",
            )
        )

        table_record: dict[
            str,
            Any
        ] = {
            "table_id": table_id,
            "label": label,
            "caption": caption,
            "section_path": list(
                section_path
            ),
            "section_id_path": list(
                section_id_path
            ),
            "rows": [],
        }

        # Caption is useful searchable evidence.
        caption_text = normalize_text(
            " ".join(
                value
                for value in [
                    label,
                    caption,
                ]
                if value
            )
        )

        self.add_block(
            block_type="table_caption",
            text=caption_text,
            section_path=section_path,
            section_id_path=section_id_path,
            section_depth=section_depth,
            source_element_id=table_id,
            metadata={
                "table_id": table_id,
                "label": label,
            },
        )

        if table_element is not None:
            rows = descendants_named(
                table_element,
                "tr",
            )

            for row_index, row in enumerate(
                rows,
                start=1,
            ):
                cells: list[
                    dict[str, Any]
                ] = []

                for cell in row:
                    cell_name = local_name(
                        cell.tag
                    )

                    if cell_name not in {
                        "th",
                        "td",
                    }:
                        continue

                    cell_value = element_text(
                        cell
                    )

                    cells.append(
                        {
                            "type": cell_name,
                            "text": cell_value,
                            "colspan": (
                                cell.attrib.get(
                                    "colspan"
                                )
                            ),
                            "rowspan": (
                                cell.attrib.get(
                                    "rowspan"
                                )
                            ),
                        }
                    )

                if not cells:
                    continue

                is_header = any(
                    cell[
                        "type"
                    ] == "th"
                    for cell in cells
                )

                row_record = {
                    "row_index": row_index,
                    "is_header": is_header,
                    "cells": cells,
                }

                table_record[
                    "rows"
                ].append(
                    row_record
                )

                cell_texts = [
                    cell[
                        "text"
                    ]
                    for cell in cells
                    if cell[
                        "text"
                    ]
                ]

                row_text_parts = [
                    value
                    for value in [
                        label,
                        caption,
                        " | ".join(
                            cell_texts
                        ),
                    ]
                    if value
                ]

                row_text = (
                    " — ".join(
                        row_text_parts
                    )
                )

                self.add_block(
                    block_type="table_row",
                    text=row_text,
                    section_path=section_path,
                    section_id_path=section_id_path,
                    section_depth=section_depth,
                    source_element_id=table_id,
                    metadata={
                        "table_id": table_id,
                        "table_label": label,
                        "row_index": row_index,
                        "is_header": is_header,
                        "cells": [
                            cell[
                                "text"
                            ]
                            for cell in cells
                        ],
                    },
                )

        # Preserve table notes/footnotes.
        table_foot = (
            first_direct_child(
                table_wrap,
                "table-wrap-foot",
            )
        )

        note_text = element_text(
            table_foot
        )

        if note_text:
            table_record[
                "notes"
            ] = note_text

            self.add_block(
                block_type="table_note",
                text=normalize_text(
                    " ".join(
                        value
                        for value in [
                            label,
                            note_text,
                        ]
                        if value
                    )
                ),
                section_path=section_path,
                section_id_path=section_id_path,
                section_depth=section_depth,
                source_element_id=table_id,
                metadata={
                    "table_id": table_id,
                    "table_label": label,
                },
            )

        self.tables.append(
            table_record
        )

    # --------------------------------------------------------
    # Figures
    # --------------------------------------------------------

    def process_figure(
        self,
        figure: ElementTree.Element,
        section_path: list[str],
        section_id_path: list[str],
        section_depth: int,
    ) -> None:
        figure_id = (
            figure.attrib.get(
                "id"
            )
        )

        label = element_text(
            first_direct_child(
                figure,
                "label",
            )
        )

        caption = element_text(
            first_direct_child(
                figure,
                "caption",
            )
        )

        figure_record = {
            "figure_id": figure_id,
            "label": label,
            "caption": caption,
            "section_path": list(
                section_path
            ),
            "section_id_path": list(
                section_id_path
            ),
        }

        self.figures.append(
            figure_record
        )

        figure_text = normalize_text(
            " ".join(
                value
                for value in [
                    label,
                    caption,
                ]
                if value
            )
        )

        self.add_block(
            block_type="figure_caption",
            text=figure_text,
            section_path=section_path,
            section_id_path=section_id_path,
            section_depth=section_depth,
            source_element_id=figure_id,
            metadata={
                "figure_id": figure_id,
                "label": label,
            },
        )

    # --------------------------------------------------------
    # Section
    # --------------------------------------------------------

    def process_section(
        self,
        section: ElementTree.Element,
        parent_path: list[str],
        parent_id_path: list[str],
        depth: int,
    ) -> None:
        title = element_text(
            first_direct_child(
                section,
                "title",
            )
        )

        if not title:
            title = (
                "[UNTITLED SECTION]"
            )

        generated_section_id = (
            self.next_section_id()
        )

        source_section_id = (
            section.attrib.get(
                "id"
            )
        )

        section_path = (
            parent_path
            + [title]
        )

        section_id_path = (
            parent_id_path
            + [
                generated_section_id
            ]
        )

        section_record = {
            "section_id": generated_section_id,
            "source_section_id": (
                source_section_id
            ),
            "title": title,
            "depth": depth,
            "path": list(
                section_path
            ),
            "section_id_path": list(
                section_id_path
            ),
        }

        self.sections.append(
            section_record
        )

        for child in section:
            name = local_name(
                child.tag
            )

            if name == "title":
                continue

            if name == "p":
                self.process_paragraph(
                    child,
                    section_path,
                    section_id_path,
                    depth,
                )

            elif name == "table-wrap":
                self.process_table(
                    child,
                    section_path,
                    section_id_path,
                    depth,
                )

            elif name == "fig":
                self.process_figure(
                    child,
                    section_path,
                    section_id_path,
                    depth,
                )

            elif name == "sec":
                self.process_section(
                    child,
                    section_path,
                    section_id_path,
                    depth + 1,
                )

            else:
                # Some JATS documents wrap paragraphs/tables
                # in additional containers.
                self.process_container(
                    child,
                    section_path,
                    section_id_path,
                    depth,
                )

    # --------------------------------------------------------
    # Generic container
    # --------------------------------------------------------

    def process_container(
        self,
        container: ElementTree.Element,
        section_path: list[str],
        section_id_path: list[str],
        section_depth: int,
    ) -> None:
        container_name = local_name(
            container.tag
        )

        if container_name in {
            "ref-list",
            "ack",
        }:
            return

        for child in container:
            name = local_name(
                child.tag
            )

            if name == "p":
                self.process_paragraph(
                    child,
                    section_path,
                    section_id_path,
                    section_depth,
                )

            elif name == "table-wrap":
                self.process_table(
                    child,
                    section_path,
                    section_id_path,
                    section_depth,
                )

            elif name == "fig":
                self.process_figure(
                    child,
                    section_path,
                    section_id_path,
                    section_depth,
                )

            elif name == "sec":
                self.process_section(
                    child,
                    section_path,
                    section_id_path,
                    section_depth + 1,
                )

            else:
                self.process_container(
                    child,
                    section_path,
                    section_id_path,
                    section_depth,
                )

    # --------------------------------------------------------
    # Body
    # --------------------------------------------------------

    def process_body(
        self,
        body: ElementTree.Element,
    ) -> None:
        for child in body:
            name = local_name(
                child.tag
            )

            if name == "sec":
                self.process_section(
                    child,
                    parent_path=[],
                    parent_id_path=[],
                    depth=1,
                )

            elif name == "p":
                self.process_paragraph(
                    child,
                    section_path=[
                        "[BODY]",
                    ],
                    section_id_path=[],
                    section_depth=0,
                )

            elif name == "table-wrap":
                self.process_table(
                    child,
                    section_path=[
                        "[BODY]",
                    ],
                    section_id_path=[],
                    section_depth=0,
                )

            elif name == "fig":
                self.process_figure(
                    child,
                    section_path=[
                        "[BODY]",
                    ],
                    section_id_path=[],
                    section_depth=0,
                )

            else:
                self.process_container(
                    child,
                    section_path=[
                        "[BODY]",
                    ],
                    section_id_path=[],
                    section_depth=0,
                )


# ============================================================
# Source integrity counters
# ============================================================

def count_body_prose_paragraphs(
    body: ElementTree.Element,
) -> int:
    count = 0

    def walk(
        node: ElementTree.Element,
    ) -> None:
        nonlocal count

        name = local_name(
            node.tag
        )

        if name in {
            "table-wrap",
            "fig",
            "ref-list",
        }:
            return

        if name == "p":
            if paragraph_text(
                node
            ):
                count += 1

            # Do not recursively count inline content
            # inside a paragraph as new paragraphs.
            return

        for child in node:
            walk(
                child
            )

    walk(
        body
    )

    return count


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Convert PMC JATS XML into a "
            "normalized MedicalPlab extraction."
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
        .lower()
    )

    xml_path = (
        RAW_DIR
        / specialty
        / f"{args.document_id}.xml"
    )

    if not xml_path.exists():
        raise FileNotFoundError(
            f"XML not found: {xml_path}"
        )

    print(
        "\nMedicalPlab PMC JATS Extraction"
    )

    print("=" * 64)

    print(
        f"Document : {args.document_id}"
    )

    print(
        f"Source   : {xml_path}"
    )

    source_sha256 = (
        sha256_file(
            xml_path
        )
    )

    print(
        f"SHA256   : {source_sha256}"
    )

    print(
        "Step 1   : parsing JATS XML..."
    )

    try:
        tree = ElementTree.parse(
            xml_path
        )

    except ElementTree.ParseError as error:
        raise ValueError(
            f"Invalid XML: {error}"
        ) from error

    root = tree.getroot()

    article = find_article(
        root
    )

    front = first_direct_child(
        article,
        "front",
    )

    body = first_direct_child(
        article,
        "body",
    )

    back = first_direct_child(
        article,
        "back",
    )

    if body is None:
        raise ValueError(
            "JATS article has no body."
        )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    article_title = element_text(
        find_first_descendant(
            front,
            "article-title",
        )
        if front is not None
        else None
    )

    journal_title = element_text(
        find_first_descendant(
            front,
            "journal-title",
        )
        if front is not None
        else None
    )

    article_ids = (
        extract_article_ids(
            front
        )
    )

    publication_year = (
        extract_publication_year(
            front
        )
    )

    # --------------------------------------------------------
    # Extract
    # --------------------------------------------------------

    print(
        "Step 2   : extracting structured "
        "content..."
    )

    extractor = JATSExtractor(
        args.document_id
    )

    extractor.process_abstracts(
        front
    )

    extractor.process_body(
        body
    )

    # --------------------------------------------------------
    # Reference metadata only
    # --------------------------------------------------------

    references = (
        descendants_named(
            back,
            "ref",
        )
        if back is not None
        else []
    )

    reference_ids = [
        reference.attrib.get(
            "id"
        )
        for reference in references
        if reference.attrib.get(
            "id"
        )
    ]

    # --------------------------------------------------------
    # Integrity counts
    # --------------------------------------------------------

    source_section_count = len(
        descendants_named(
            body,
            "sec",
        )
    )

    source_paragraph_count = (
        count_body_prose_paragraphs(
            body
        )
    )

    source_tables = (
        descendants_named(
            body,
            "table-wrap",
        )
    )

    source_table_count = len(
        source_tables
    )

    source_table_row_count = sum(
        len(
            descendants_named(
                table,
                "tr",
            )
        )
        for table in source_tables
    )

    extracted_paragraph_count = sum(
        1
        for block in extractor.blocks
        if block[
            "block_type"
        ] == "paragraph"
    )

    extracted_table_row_count = sum(
        len(
            table[
                "rows"
            ]
        )
        for table in extractor.tables
    )

    checks = {
        "sections": {
            "source": (
                source_section_count
            ),
            "extracted": (
                len(
                    extractor.sections
                )
            ),
        },
        "prose_paragraphs": {
            "source": (
                source_paragraph_count
            ),
            "extracted": (
                extracted_paragraph_count
            ),
        },
        "tables": {
            "source": (
                source_table_count
            ),
            "extracted": (
                len(
                    extractor.tables
                )
            ),
        },
        "table_rows": {
            "source": (
                source_table_row_count
            ),
            "extracted": (
                extracted_table_row_count
            ),
        },
        "references": {
            "source": (
                len(
                    references
                )
            ),
            "included_in_rag_blocks": 0,
        },
    }

    warnings: list[str] = []

    for check_name in [
        "sections",
        "prose_paragraphs",
        "tables",
        "table_rows",
    ]:
        check = checks[
            check_name
        ]

        if (
            check[
                "source"
            ]
            != check[
                "extracted"
            ]
        ):
            warnings.append(
                f"{check_name} count mismatch: "
                f"source={check['source']} "
                f"extracted={check['extracted']}"
            )

    status = (
        "PASS"
        if not warnings
        else "REVIEW"
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    output = {
        "schema_version": (
            "medicalplab-jats-normalized-v1"
        ),
        "document_id": (
            args.document_id
        ),
        "source_format": (
            "pmc_jats_xml"
        ),
        "source": {
            "file": str(
                xml_path.relative_to(
                    PROJECT_ROOT
                )
            ),
            "sha256": (
                source_sha256
            ),
        },
        "article": {
            "title": (
                article_title
            ),
            "journal": (
                journal_title
            ),
            "publication_year": (
                publication_year
            ),
            "identifiers": (
                article_ids
            ),
        },
        "sections": (
            extractor.sections
        ),
        "blocks": (
            extractor.blocks
        ),
        "tables": (
            extractor.tables
        ),
        "figures": (
            extractor.figures
        ),
        "references": {
            "count": (
                len(
                    references
                )
            ),
            "ids": (
                reference_ids
            ),
            "included_in_rag_blocks": (
                False
            ),
        },
    }

    quality = {
        "document_id": (
            args.document_id
        ),
        "source_format": (
            "pmc_jats_xml"
        ),
        "source_sha256": (
            source_sha256
        ),
        "checks": (
            checks
        ),
        "warnings": (
            warnings
        ),
        "validation": (
            status
        ),
    }

    output_dir = (
        PROCESSED_DIR
        / specialty
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / (
            f"{args.document_id}"
            ".jats.json"
        )
    )

    quality_path = (
        output_dir
        / (
            f"{args.document_id}"
            ".jats.quality.json"
        )
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2,
        )

    with quality_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            quality,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print(
        "Step 3   : validating extraction "
        "integrity..."
    )

    print(
        "\nExtraction Summary"
    )

    print("-" * 64)

    print(
        f"Sections       : "
        f"{len(extractor.sections)}"
    )

    print(
        f"Paragraphs     : "
        f"{extracted_paragraph_count}"
    )

    print(
        f"Tables         : "
        f"{len(extractor.tables)}"
    )

    print(
        f"Table rows     : "
        f"{extracted_table_row_count}"
    )

    print(
        f"Figures        : "
        f"{len(extractor.figures)}"
    )

    print(
        f"References     : "
        f"{len(references)} "
        f"(excluded from RAG blocks)"
    )

    print(
        f"Total blocks   : "
        f"{len(extractor.blocks)}"
    )

    print(
        "\nIntegrity Checks"
    )

    print("-" * 64)

    for name, check in checks.items():
        if name == "references":
            print(
                f"{name:<16}: "
                f"{check['source']} source | "
                f"0 RAG blocks"
            )

            continue

        passed = (
            check[
                "source"
            ]
            == check[
                "extracted"
            ]
        )

        print(
            f"{name:<16}: "
            f"{check['source']} source | "
            f"{check['extracted']} extracted | "
            f"{'PASS ✅' if passed else 'MISMATCH ❌'}"
        )

    print(
        "\n"
        + "=" * 64
    )

    print(
        f"Validation     : "
        f"{status}"
        + (
            " ✅"
            if status == "PASS"
            else " ⚠️"
        )
    )

    if warnings:
        for warning in warnings:
            print(
                f"WARNING        : "
                f"{warning}"
            )

    print(
        f"Output         : "
        f"{output_path}"
    )

    print(
        f"Quality report : "
        f"{quality_path}"
    )


if __name__ == "__main__":
    main()