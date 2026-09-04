import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
)


DEFAULT_TARGET_CHARS = 1400
DEFAULT_MAX_CHARS = 1800
DEFAULT_MIN_CHARS = 350


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object."""
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
    """Save JSON as UTF-8."""
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


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace for integrity comparison only."""
    return re.sub(
        r"\s+",
        " ",
        text.strip(),
    )


def sha256_text(text: str) -> str:
    """Return SHA-256 of UTF-8 text."""
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def candidate_boundaries(
    text: str,
    minimum: int,
    maximum: int,
) -> list[tuple[int, int]]:
    """
    Find safe split candidates.

    Lower priority value = stronger boundary.

    Priority:
        0 -> sentence ending
        1 -> semicolon / colon
        2 -> general whitespace
    """
    candidates: list[
        tuple[int, int]
    ] = []

    # Strong sentence boundaries.
    for match in re.finditer(
        r"(?<=[.!?])\s+(?=[A-Z0-9\[])",
        text,
    ):
        position = match.start()

        if minimum <= position <= maximum:
            candidates.append(
                (position, 0)
            )

    # Secondary clause boundaries.
    for match in re.finditer(
        r"(?<=[;:])\s+",
        text,
    ):
        position = match.start()

        if minimum <= position <= maximum:
            candidates.append(
                (position, 1)
            )

    # Final fallback: whitespace.
    for match in re.finditer(
        r"\s+",
        text,
    ):
        position = match.start()

        if minimum <= position <= maximum:
            candidates.append(
                (position, 2)
            )

    return candidates


def choose_split_boundary(
    text: str,
    target_chars: int,
    max_chars: int,
    min_chars: int,
) -> int:
    """
    Choose the safest boundary near the target size.

    Avoid creating an undersized final fragment whenever
    possible.
    """
    if len(text) <= max_chars:
        return len(text)

    candidates = candidate_boundaries(
        text,
        min_chars,
        max_chars,
    )

    if not candidates:
        raise ValueError(
            "Unable to find a safe whitespace boundary "
            f"within {max_chars} characters."
        )

    safe_candidates: list[
        tuple[int, int]
    ] = []

    for position, priority in candidates:
        remaining = (
            len(text)
            - position
        )

        # If another fragment remains, avoid making it
        # smaller than the configured minimum.
        if (
            0 < remaining < min_chars
        ):
            continue

        safe_candidates.append(
            (position, priority)
        )

    if not safe_candidates:
        safe_candidates = candidates

    # Prefer semantic boundary quality first, then
    # closeness to target.
    best_position, _ = min(
        safe_candidates,
        key=lambda item: (
            item[1],
            abs(
                item[0]
                - target_chars
            ),
        ),
    )

    return best_position


def split_text_losslessly(
    text: str,
    target_chars: int,
    max_chars: int,
    min_chars: int,
) -> list[str]:
    """
    Split normalized section text without rewriting it.

    No overlap is introduced.

    Reconstruction using a single space between chunks must
    equal the normalized source text.
    """
    text = normalize_whitespace(
        text
    )

    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []

    remaining = text

    while len(remaining) > max_chars:
        boundary = choose_split_boundary(
            remaining,
            target_chars,
            max_chars,
            min_chars,
        )

        chunk = (
            remaining[
                :boundary
            ]
            .strip()
        )

        if not chunk:
            raise ValueError(
                "Chunking produced an empty fragment."
            )

        chunks.append(
            chunk
        )

        remaining = (
            remaining[
                boundary:
            ]
            .strip()
        )

    if remaining:
        chunks.append(
            remaining
        )

    reconstructed = normalize_whitespace(
        " ".join(chunks)
    )

    if reconstructed != text:
        raise ValueError(
            "Lossless chunk reconstruction failed."
        )

    return chunks


def build_chunks(
    document: dict[str, Any],
    target_chars: int,
    max_chars: int,
    min_chars: int,
) -> tuple[
    list[dict[str, Any]],
    dict[str, Any],
]:
    """
    Convert enriched structural blocks into canonical
    retrieval chunks.
    """
    sections = document.get(
        "sections",
        [],
    )

    if not isinstance(
        sections,
        list,
    ):
        raise ValueError(
            "Document sections must be a list."
        )

    document_id = document.get(
        "document_id"
    )

    source_id = document.get(
        "source_id"
    )

    specialty = document.get(
        "medical_specialty"
    )

    topics = document.get(
        "topics",
        [],
    )

    if not isinstance(
        document_id,
        str,
    ):
        raise ValueError(
            "Missing document_id."
        )

    if not isinstance(
        source_id,
        str,
    ):
        raise ValueError(
            "Missing source_id."
        )

    if not isinstance(
        specialty,
        str,
    ):
        raise ValueError(
            "Missing medical_specialty."
        )

    if not isinstance(
        topics,
        list,
    ):
        raise ValueError(
            "topics must be a list."
        )

    chunks: list[
        dict[str, Any]
    ] = []

    skipped_empty_blocks: list[
        int
    ] = []

    split_blocks: list[
        int
    ] = []

    block_type_counter: Counter[
        str
    ] = Counter()

    for section in sections:
        block_index = section.get(
            "block_index"
        )

        if not isinstance(
            block_index,
            int,
        ):
            raise ValueError(
                "Every section must have an integer "
                "block_index."
            )

        text = str(
            section.get(
                "text",
                "",
            )
        ).strip()

        if not text:
            skipped_empty_blocks.append(
                block_index
            )
            continue

        parts = split_text_losslessly(
            text,
            target_chars,
            max_chars,
            min_chars,
        )

        chunk_count = len(parts)

        if chunk_count > 1:
            split_blocks.append(
                block_index
            )

        block_type = str(
            section.get(
                "block_type",
                "",
            )
        )

        block_type_counter[
            block_type
        ] += chunk_count

        source_block_hash = (
            section.get(
                "content_sha256"
            )
        )

        for chunk_index, part in enumerate(
            parts,
            start=1,
        ):
            # Block-local IDs remain stable if an unrelated
            # block elsewhere in the document changes.
            chunk_id = (
                f"{document_id}"
                f"-B{block_index:04d}"
                f"-C{chunk_index:02d}"
            )

            chunk = {
                "chunk_id": chunk_id,
                "document_id": (
                    document_id
                ),
                "source_id": source_id,
                "medical_specialty": (
                    specialty
                ),
                "topics": topics,
                "source_block_index": (
                    block_index
                ),
                "source_block_sha256": (
                    source_block_hash
                ),
                "block_type": block_type,
                "section_number": (
                    section.get(
                        "section_number"
                    )
                ),
                "section_level": (
                    section.get(
                        "section_level",
                        0,
                    )
                ),
                "parent_section_number": (
                    section.get(
                        "parent_section_number"
                    )
                ),
                "parent_section_heading": (
                    section.get(
                        "parent_section_heading"
                    )
                ),
                "section_path": (
                    section.get(
                        "section_path",
                        [],
                    )
                ),
                "heading": str(
                    section.get(
                        "heading",
                        "",
                    )
                ),
                "start_page": (
                    section.get(
                        "start_page"
                    )
                ),
                "end_page": (
                    section.get(
                        "end_page"
                    )
                ),
                "chunk_index": (
                    chunk_index
                ),
                "chunk_count_in_block": (
                    chunk_count
                ),
                "is_split": (
                    chunk_count > 1
                ),
                "text": part,
                "character_count": (
                    len(part)
                ),
                "content_sha256": (
                    sha256_text(
                        part
                    )
                ),
            }

            # Preserve source-agnostic provenance when available.
            # Existing PDF/WHO sections that do not contain these
            # fields keep their previous chunk output unchanged.
            for provenance_field in (
                "provenance_type",
                "source_locator",
                "source_format",
            ):
                if provenance_field in section:
                    chunk[provenance_field] = section[
                        provenance_field
                    ]

            # Keep the source-faithful section_path
            # unchanged while passing through the
            # optional semantic retrieval hierarchy.
            if "retrieval_section_path" in section:
                chunk["retrieval_section_path"] = section[
                    "retrieval_section_path"
                ]

            chunks.append(
                chunk
            )

    character_counts = [
        chunk[
            "character_count"
        ]
        for chunk in chunks
    ]

    report = {
        "total_source_blocks": (
            len(sections)
        ),
        "nonempty_source_blocks": (
            len(sections)
            - len(
                skipped_empty_blocks
            )
        ),
        "skipped_empty_blocks": (
            skipped_empty_blocks
        ),
        "skipped_empty_block_count": (
            len(
                skipped_empty_blocks
            )
        ),
        "split_source_blocks": (
            split_blocks
        ),
        "split_source_block_count": (
            len(split_blocks)
        ),
        "total_chunks": len(
            chunks
        ),
        "chunk_type_counts": dict(
            block_type_counter
        ),
        "minimum_chunk_characters": (
            min(character_counts)
            if character_counts
            else 0
        ),
        "maximum_chunk_characters": (
            max(character_counts)
            if character_counts
            else 0
        ),
        "average_chunk_characters": (
            round(
                sum(
                    character_counts
                )
                / len(
                    character_counts
                ),
                2,
            )
            if character_counts
            else 0
        ),
    }

    return chunks, report


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create structure-aware retrieval chunks "
            "from enriched MedicalPlab sections."
        )
    )

    parser.add_argument(
        "document_id",
    )

    parser.add_argument(
        "--specialty",
        default="Cardiology",
    )

    parser.add_argument(
        "--target-chars",
        type=int,
        default=DEFAULT_TARGET_CHARS,
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=DEFAULT_MAX_CHARS,
    )

    parser.add_argument(
        "--min-chars",
        type=int,
        default=DEFAULT_MIN_CHARS,
    )

    args = parser.parse_args()

    if not (
        0
        < args.min_chars
        <= args.target_chars
        <= args.max_chars
    ):
        raise ValueError(
            "Chunk sizes must satisfy: "
            "0 < min <= target <= max."
        )

    specialty = normalize_folder_name(
        args.specialty
    )

    input_path = (
        PROCESSED_DIR
        / specialty
        / (
            f"{args.document_id}"
            ".sections.enriched.json"
        )
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Enriched sections not found: "
            f"{input_path}"
        )

    document = load_json(
        input_path
    )

    chunks, report = build_chunks(
        document,
        args.target_chars,
        args.max_chars,
        args.min_chars,
    )

    output = {
        "document_id": (
            document.get(
                "document_id"
            )
        ),
        "source_id": (
            document.get(
                "source_id"
            )
        ),
        "title": (
            document.get(
                "title"
            )
        ),
        "medical_specialty": (
            document.get(
                "medical_specialty"
            )
        ),
        "topics": (
            document.get(
                "topics"
            )
        ),
        "source_sha256": (
            document.get(
                "source_sha256"
            )
        ),
        "chunking": {
            "pipeline_version": "v1",
            "strategy": (
                "structure_aware_lossless"
            ),
            "target_characters": (
                args.target_chars
            ),
            "maximum_characters": (
                args.max_chars
            ),
            "minimum_characters": (
                args.min_chars
            ),
            "overlap_characters": 0,
            "generated_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
        },
        "chunks": chunks,
    }

    output_path = (
        PROCESSED_DIR
        / specialty
        / (
            f"{args.document_id}"
            ".chunks.json"
        )
    )

    report_path = (
        PROCESSED_DIR
        / specialty
        / (
            f"{args.document_id}"
            ".chunks.quality.json"
        )
    )

    save_json(
        output_path,
        output,
    )

    quality_report = {
        "document_id": (
            args.document_id
        ),
        "chunking_config": (
            output[
                "chunking"
            ]
        ),
        **report,
    }

    save_json(
        report_path,
        quality_report,
    )

    print(
        "\nMedicalPlab Structure-Aware Chunker"
    )
    print("=" * 45)

    print(
        f"Document                  : "
        f"{args.document_id}"
    )

    print(
        f"Source blocks             : "
        f"{report['total_source_blocks']}"
    )

    print(
        f"Non-empty blocks          : "
        f"{report['nonempty_source_blocks']}"
    )

    print(
        f"Skipped empty blocks      : "
        f"{report['skipped_empty_block_count']}"
    )

    print(
        f"Split source blocks       : "
        f"{report['split_source_block_count']}"
    )

    print(
        f"Total chunks              : "
        f"{report['total_chunks']}"
    )

    print(
        f"Min chunk characters      : "
        f"{report['minimum_chunk_characters']}"
    )

    print(
        f"Max chunk characters      : "
        f"{report['maximum_chunk_characters']}"
    )

    print(
        f"Average chunk characters  : "
        f"{report['average_chunk_characters']}"
    )

    print(
        "\nChunk Type Summary"
    )
    print("-" * 45)

    for block_type, count in sorted(
        report[
            "chunk_type_counts"
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
        "\nChunk Samples"
    )
    print("-" * 100)

    for chunk in chunks[:12]:
        print(
            f"{chunk['chunk_id']} "
            f"[{chunk['block_type']}] "
            f"P{chunk['start_page']}"
            f"-P{chunk['end_page']} "
            f"{chunk['character_count']} chars"
        )

        print(
            f"    Parent: "
            f"{chunk.get('parent_section_number')} "
            f"{chunk.get('parent_section_heading')}"
        )

        print(
            f"    {chunk['text'][:160]}"
        )

    print(
        f"\nOutput                    : "
        f"{output_path}"
    )

    print(
        f"Quality report            : "
        f"{report_path}"
    )


if __name__ == "__main__":
    main()