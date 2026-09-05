import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_FILES = [
    PROJECT_ROOT
    / "Data"
    / "processed"
    / "cardiology"
    / "DOC-WHO-CARD-0001.chunks.json",
    PROJECT_ROOT
    / "Data"
    / "processed"
    / "cardiology"
    / "DOC-PMC-CARD-0002.chunks.json",
]

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "Data"
    / "audit"
    / "evidence_catalog_multisource_v2.md"
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_chunks(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)

    if isinstance(data, dict):
        if "chunks" in data:
            chunks = data["chunks"]
        else:
            chunks = [data]
    elif isinstance(data, list):
        chunks = data
    else:
        raise ValueError(
            f"Unsupported JSON structure in {path}"
        )

    if not isinstance(chunks, list):
        raise ValueError(
            f"'chunks' must be a list in {path}"
        )

    cleaned: list[dict[str, Any]] = []

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        if not isinstance(chunk, dict):
            raise ValueError(
                f"Chunk #{index} in {path} "
                "is not a JSON object."
            )

        cleaned.append(chunk)

    return cleaned


def normalize_path(
    value: Any,
) -> str:
    if not isinstance(value, list):
        return ""

    return " > ".join(
        str(part)
        for part in value
        if str(part).strip()
    )


def one_line(text: Any) -> str:
    if not isinstance(text, str):
        return ""

    return " ".join(
        text.split()
    )


def truncate(
    text: str,
    limit: int,
) -> str:
    if len(text) <= limit:
        return text

    return (
        text[: max(0, limit - 3)]
        .rstrip()
        + "..."
    )


def format_locator(
    chunk: dict[str, Any],
) -> str:
    provenance_type = chunk.get(
        "provenance_type"
    )

    if provenance_type == "page":
        start_page = chunk.get(
            "start_page"
        )
        end_page = chunk.get(
            "end_page"
        )

        if (
            isinstance(start_page, int)
            and isinstance(end_page, int)
        ):
            if start_page == end_page:
                return f"page {start_page}"

            return (
                f"pages {start_page}-{end_page}"
            )

    source_locator = chunk.get(
        "source_locator"
    )

    if source_locator:
        return str(source_locator)

    return ""


def build_catalog(
    files: list[Path],
    preview_chars: int,
) -> str:
    chunks: list[dict[str, Any]] = []

    for file_path in files:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Chunk file not found: "
                f"{file_path}"
            )

        chunks.extend(
            load_chunks(file_path)
        )

    by_document: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for chunk in chunks:
        document_id = str(
            chunk.get(
                "document_id",
                "UNKNOWN",
            )
        )

        by_document[
            document_id
        ].append(chunk)

    lines: list[str] = []

    lines.append(
        "# MedicalPlab Multi-Source "
        "Evidence Catalog v2"
    )
    lines.append("")
    lines.append(
        "> Generated from the local "
        "validated retrieval chunks. "
        "Use this catalog to manually "
        "design the real multi-source "
        "DEV evaluation set. Do not use "
        "retriever rankings as gold labels."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        f"- Documents: "
        f"{len(by_document)}"
    )
    lines.append(
        f"- Chunks: {len(chunks)}"
    )

    total_blocks = len(
        {
            (
                str(
                    chunk.get(
                        "document_id"
                    )
                ),
                int(
                    chunk.get(
                        "source_block_index",
                        -1,
                    )
                ),
            )
            for chunk in chunks
        }
    )

    lines.append(
        f"- Unique source blocks: "
        f"{total_blocks}"
    )
    lines.append(
        f"- Preview characters per "
        f"source block: {preview_chars}"
    )
    lines.append("")

    for document_id in sorted(
        by_document
    ):
        document_chunks = (
            by_document[document_id]
        )

        groups: dict[
            int,
            list[dict[str, Any]],
        ] = defaultdict(list)

        for chunk in document_chunks:
            block_index = chunk.get(
                "source_block_index"
            )

            if not isinstance(
                block_index,
                int,
            ):
                raise ValueError(
                    f"Chunk "
                    f"{chunk.get('chunk_id')} "
                    "has no integer "
                    "source_block_index."
                )

            groups[
                block_index
            ].append(chunk)

        lines.append(
            f"# {document_id}"
        )
        lines.append("")
        lines.append(
            f"- Chunks: "
            f"{len(document_chunks)}"
        )
        lines.append(
            f"- Source blocks: "
            f"{len(groups)}"
        )
        lines.append("")

        for block_index in sorted(
            groups
        ):
            block_chunks = sorted(
                groups[block_index],
                key=lambda item: int(
                    item.get(
                        "chunk_index",
                        1,
                    )
                ),
            )

            first = block_chunks[0]

            block_type = str(
                first.get(
                    "block_type",
                    "",
                )
            )

            section_number = (
                first.get(
                    "section_number"
                )
            )

            parent_section_number = (
                first.get(
                    "parent_section_number"
                )
            )

            heading = one_line(
                first.get(
                    "heading",
                    "",
                )
            )

            source_path = (
                normalize_path(
                    first.get(
                        "section_path"
                    )
                )
            )

            retrieval_path = (
                normalize_path(
                    first.get(
                        "retrieval_section_path"
                    )
                )
            )

            locator = (
                format_locator(first)
            )

            combined_text = " ".join(
                one_line(
                    chunk.get(
                        "text",
                        "",
                    )
                )
                for chunk in block_chunks
            ).strip()

            preview = truncate(
                combined_text,
                preview_chars,
            )

            lines.append(
                f"## B{block_index:04d}"
            )
            lines.append("")
            lines.append(
                f"- **Block index:** "
                f"{block_index}"
            )
            lines.append(
                f"- **Block type:** "
                f"`{block_type}`"
            )
            lines.append(
                f"- **Chunks in block:** "
                f"{len(block_chunks)}"
            )

            if section_number is not None:
                lines.append(
                    "- **Section number:** "
                    f"`{section_number}`"
                )

            if (
                parent_section_number
                is not None
            ):
                lines.append(
                    "- **Parent section:** "
                    f"`{parent_section_number}`"
                )

            if heading:
                lines.append(
                    f"- **Heading:** "
                    f"{heading}"
                )

            if source_path:
                lines.append(
                    "- **Source path:** "
                    f"{source_path}"
                )

            if (
                retrieval_path
                and retrieval_path
                != source_path
            ):
                lines.append(
                    "- **Retrieval path:** "
                    f"{retrieval_path}"
                )

            if locator:
                lines.append(
                    f"- **Locator:** "
                    f"`{locator}`"
                )

            lines.append("")
            lines.append(
                "**Evidence preview**"
            )
            lines.append("")
            lines.append(preview)
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Export a compact, document-aware "
            "catalog of MedicalPlab retrieval "
            "evidence blocks for manual "
            "multi-source evaluation design."
        )
    )

    parser.add_argument(
        "--files",
        nargs="+",
        type=Path,
        default=DEFAULT_FILES,
        help=(
            "Chunk JSON files. Defaults to "
            "the current WHO and PMC "
            "cardiology chunk files."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=(
            "Markdown output path. Defaults "
            "to Data/audit/"
            "evidence_catalog_multisource_v2.md"
        ),
    )

    parser.add_argument(
        "--preview-chars",
        type=int,
        default=600,
        help=(
            "Maximum evidence preview "
            "characters per source block."
        ),
    )

    args = parser.parse_args()

    if args.preview_chars < 100:
        raise ValueError(
            "--preview-chars must be "
            "at least 100."
        )

    files = [
        path
        if path.is_absolute()
        else PROJECT_ROOT / path
        for path in args.files
    ]

    output = (
        args.output
        if args.output.is_absolute()
        else PROJECT_ROOT / args.output
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    catalog = build_catalog(
        files=files,
        preview_chars=args.preview_chars,
    )

    output.write_text(
        catalog,
        encoding="utf-8",
        newline="\n",
    )

    print(
        "\nMedicalPlab Multi-Source "
        "Evidence Catalog"
    )
    print("=" * 44)
    print(
        f"Documents : {len(files)}"
    )
    print(
        f"Output    : {output}"
    )
    print(
        "Status    : PASS"
    )


if __name__ == "__main__":
    main()
