import argparse
import hashlib
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


# ============================================================
# XML helpers
# ============================================================

def local_name(
    tag: str,
) -> str:
    return (
        tag.split("}")[-1]
        if "}" in tag
        else tag
    )


def element_text(
    element: ElementTree.Element | None,
) -> str:
    if element is None:
        return ""

    text = " ".join(
        part.strip()
        for part in element.itertext()
        if part.strip()
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def first_child(
    element: ElementTree.Element,
    child_name: str,
) -> ElementTree.Element | None:
    for child in element:
        if (
            local_name(
                child.tag
            )
            == child_name
        ):
            return child

    return None


def descendants_named(
    element: ElementTree.Element,
    name: str,
) -> list[ElementTree.Element]:
    return [
        item
        for item in element.iter()
        if local_name(
            item.tag
        )
        == name
    ]


def find_first_descendant(
    element: ElementTree.Element,
    name: str,
) -> ElementTree.Element | None:
    for item in element.iter():
        if (
            local_name(
                item.tag
            )
            == name
        ):
            return item

    return None


def find_article(
    root: ElementTree.Element,
) -> ElementTree.Element:
    if (
        local_name(
            root.tag
        )
        == "article"
    ):
        return root

    for element in root.iter():
        if (
            local_name(
                element.tag
            )
            == "article"
        ):
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
# Section inspection
# ============================================================

def collect_sections(
    parent: ElementTree.Element,
    parent_path: list[str] | None = None,
    depth: int = 1,
) -> list[dict[str, Any]]:
    if parent_path is None:
        parent_path = []

    sections: list[
        dict[str, Any]
    ] = []

    for child in parent:
        if (
            local_name(
                child.tag
            )
            != "sec"
        ):
            continue

        title_element = first_child(
            child,
            "title",
        )

        title = element_text(
            title_element
        )

        if not title:
            title = (
                "[UNTITLED SECTION]"
            )

        path = (
            parent_path
            + [title]
        )

        direct_paragraphs = [
            element
            for element in child
            if local_name(
                element.tag
            )
            == "p"
        ]

        direct_tables = [
            element
            for element in child
            if local_name(
                element.tag
            )
            == "table-wrap"
        ]

        direct_figures = [
            element
            for element in child
            if local_name(
                element.tag
            )
            == "fig"
        ]

        sections.append(
            {
                "depth": depth,
                "title": title,
                "path": path,
                "direct_paragraphs": len(
                    direct_paragraphs
                ),
                "direct_tables": len(
                    direct_tables
                ),
                "direct_figures": len(
                    direct_figures
                ),
            }
        )

        sections.extend(
            collect_sections(
                child,
                parent_path=path,
                depth=(
                    depth + 1
                ),
            )
        )

    return sections


# ============================================================
# Paragraph inspection
# ============================================================

SKIP_PROSE_CONTAINERS = {
    "table-wrap",
    "fig",
    "ref-list",
}


def count_body_prose_paragraphs(
    element: ElementTree.Element,
) -> int:
    count = 0

    def walk(
        node: ElementTree.Element,
    ) -> None:
        nonlocal count

        name = local_name(
            node.tag
        )

        if name in SKIP_PROSE_CONTAINERS:
            return

        if name == "p":
            text = element_text(
                node
            )

            if text:
                count += 1

        for child in node:
            walk(
                child
            )

    walk(
        element
    )

    return count


# ============================================================
# Table inspection
# ============================================================

def table_summary(
    table_wrap: ElementTree.Element,
    index: int,
) -> dict[str, Any]:
    label_element = first_child(
        table_wrap,
        "label",
    )

    caption_element = first_child(
        table_wrap,
        "caption",
    )

    label = element_text(
        label_element
    )

    caption = element_text(
        caption_element
    )

    table_element = (
        find_first_descendant(
            table_wrap,
            "table",
        )
    )

    rows = 0
    cells = 0

    if table_element is not None:
        rows = len(
            descendants_named(
                table_element,
                "tr",
            )
        )

        cells = (
            len(
                descendants_named(
                    table_element,
                    "td",
                )
            )
            + len(
                descendants_named(
                    table_element,
                    "th",
                )
            )
        )

    table_id = (
        table_wrap.attrib.get(
            "id"
        )
    )

    return {
        "index": index,
        "id": table_id,
        "label": label,
        "caption": caption,
        "rows": rows,
        "cells": cells,
    }


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Audit PMC JATS XML structure before "
            "MedicalPlab ingestion."
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

    xml_path = (
        RAW_DIR
        / args.specialty.lower()
        / f"{args.document_id}.xml"
    )

    if not xml_path.exists():
        raise FileNotFoundError(
            f"XML not found: {xml_path}"
        )

    print(
        "\nMedicalPlab PMC JATS Structure Audit"
    )

    print("=" * 72)

    print(
        f"Document : {args.document_id}"
    )

    print(
        f"XML      : {xml_path}"
    )

    print(
        f"Size     : "
        f"{xml_path.stat().st_size:,} bytes"
    )

    print(
        f"SHA256   : "
        f"{sha256_file(xml_path)}"
    )

    # --------------------------------------------------------
    # Parse XML
    # --------------------------------------------------------

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

    print(
        "JATS     : article found ✅"
    )

    # --------------------------------------------------------
    # Front matter
    # --------------------------------------------------------

    front = first_child(
        article,
        "front",
    )

    body = first_child(
        article,
        "body",
    )

    back = first_child(
        article,
        "back",
    )

    print(
        f"Front    : "
        f"{'YES' if front is not None else 'NO'}"
    )

    print(
        f"Body     : "
        f"{'YES' if body is not None else 'NO'}"
    )

    print(
        f"Back     : "
        f"{'YES' if back is not None else 'NO'}"
    )

    if body is None:
        raise ValueError(
            "JATS article has no <body> element."
        )

    # --------------------------------------------------------
    # Article metadata
    # --------------------------------------------------------

    article_title = ""

    journal_title = ""

    if front is not None:
        article_title_element = (
            find_first_descendant(
                front,
                "article-title",
            )
        )

        journal_title_element = (
            find_first_descendant(
                front,
                "journal-title",
            )
        )

        article_title = element_text(
            article_title_element
        )

        journal_title = element_text(
            journal_title_element
        )

    print(
        "\nArticle Metadata"
    )

    print("-" * 72)

    print(
        f"Journal  : {journal_title}"
    )

    print(
        f"Title    : {article_title}"
    )

    # --------------------------------------------------------
    # Abstract
    # --------------------------------------------------------

    abstract_elements = (
        descendants_named(
            front,
            "abstract",
        )
        if front is not None
        else []
    )

    abstract_texts = [
        element_text(
            abstract
        )
        for abstract in abstract_elements
    ]

    abstract_texts = [
        text
        for text in abstract_texts
        if text
    ]

    print(
        "\nAbstract"
    )

    print("-" * 72)

    print(
        f"Abstract blocks       : "
        f"{len(abstract_texts)}"
    )

    print(
        f"Abstract characters   : "
        f"{sum(len(text) for text in abstract_texts):,}"
    )

    if abstract_texts:
        preview = (
            abstract_texts[0][
                :500
            ]
        )

        print(
            f"Preview               : "
            f"{preview}"
        )

    # --------------------------------------------------------
    # Body structure
    # --------------------------------------------------------

    sections = collect_sections(
        body
    )

    body_paragraphs = (
        count_body_prose_paragraphs(
            body
        )
    )

    print(
        "\nBody Structure"
    )

    print("-" * 72)

    print(
        f"Sections              : "
        f"{len(sections)}"
    )

    print(
        f"Prose paragraphs      : "
        f"{body_paragraphs}"
    )

    max_depth = max(
        (
            section[
                "depth"
            ]
            for section in sections
        ),
        default=0,
    )

    print(
        f"Maximum section depth : "
        f"{max_depth}"
    )

    print(
        "\nSection Hierarchy"
    )

    print("-" * 100)

    for index, section in enumerate(
        sections,
        start=1,
    ):
        indent = (
            "  "
            * (
                section[
                    "depth"
                ]
                - 1
            )
        )

        print(
            f"{index:02d}. "
            f"{indent}"
            f"{section['title']}"
        )

        print(
            f"    "
            f"depth={section['depth']} | "
            f"paragraphs={section['direct_paragraphs']} | "
            f"tables={section['direct_tables']} | "
            f"figures={section['direct_figures']}"
        )

    # --------------------------------------------------------
    # Tables
    # --------------------------------------------------------

    all_table_wraps = (
        descendants_named(
            article,
            "table-wrap",
        )
    )

    body_table_wraps = (
        descendants_named(
            body,
            "table-wrap",
        )
    )

    tables = [
        table_summary(
            table_wrap,
            index,
        )
        for index, table_wrap
        in enumerate(
            all_table_wraps,
            start=1,
        )
    ]

    print(
        "\nTables"
    )

    print("-" * 100)

    print(
        f"Article tables        : "
        f"{len(all_table_wraps)}"
    )

    print(
        f"Body tables           : "
        f"{len(body_table_wraps)}"
    )

    found_table_numbers: set[int] = set()

    for table in tables:
        label = (
            table[
                "label"
            ]
            or (
                f"Table {table['index']}"
            )
        )

        match = re.search(
            r"\bTable\s+(\d+)",
            label,
            flags=re.IGNORECASE,
        )

        if match:
            found_table_numbers.add(
                int(
                    match.group(1)
                )
            )

        print(
            f"\n{label}"
        )

        print(
            f"  ID      : "
            f"{table['id']}"
        )

        print(
            f"  Caption : "
            f"{table['caption'][:300]}"
        )

        print(
            f"  Rows    : "
            f"{table['rows']}"
        )

        print(
            f"  Cells   : "
            f"{table['cells']}"
        )

    expected_tables = {
        1,
        2,
        3,
        4,
        5,
        6,
    }

    missing_tables = (
        expected_tables
        - found_table_numbers
    )

    print(
        "\nExpected Table Check"
    )

    print("-" * 72)

    print(
        f"Expected : "
        f"{sorted(expected_tables)}"
    )

    print(
        f"Found    : "
        f"{sorted(found_table_numbers)}"
    )

    print(
        f"Missing  : "
        f"{sorted(missing_tables)}"
    )

    # --------------------------------------------------------
    # References
    # --------------------------------------------------------

    ref_lists = (
        descendants_named(
            back,
            "ref-list",
        )
        if back is not None
        else []
    )

    references: list[
        ElementTree.Element
    ] = []

    for ref_list in ref_lists:
        references.extend(
            descendants_named(
                ref_list,
                "ref",
            )
        )

    print(
        "\nReferences"
    )

    print("-" * 72)

    print(
        f"Reference lists       : "
        f"{len(ref_lists)}"
    )

    print(
        f"References            : "
        f"{len(references)}"
    )

    # --------------------------------------------------------
    # Integrity summary
    # --------------------------------------------------------

    warnings: list[str] = []

    if not article_title:
        warnings.append(
            "Article title missing."
        )

    if not sections:
        warnings.append(
            "No body sections found."
        )

    if body_paragraphs == 0:
        warnings.append(
            "No body prose paragraphs found."
        )

    if missing_tables:
        warnings.append(
            "Expected tables are missing."
        )

    if not references:
        warnings.append(
            "No structured references found."
        )

    print(
        "\n"
        + "=" * 72
    )

    print(
        "JATS Audit Summary"
    )

    print("-" * 72)

    print(
        f"Structured sections   : "
        f"{len(sections)}"
    )

    print(
        f"Body paragraphs       : "
        f"{body_paragraphs}"
    )

    print(
        f"Structured tables     : "
        f"{len(all_table_wraps)}"
    )

    print(
        f"Structured references : "
        f"{len(references)}"
    )

    print(
        f"Warnings              : "
        f"{len(warnings)}"
    )

    if warnings:
        print(
            "Validation            : REVIEW ⚠️"
        )

        for warning in warnings:
            print(
                f"- {warning}"
            )

    else:
        print(
            "Validation            : PASS ✅"
        )


if __name__ == "__main__":
    main()