import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DIR = (
    PROJECT_ROOT
    / "Data"
    / "processed"
)


def load_json(path: Path) -> dict[str, Any]:
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


def validate_integrity(
    sections: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    minimum_split_characters: int,
    maximum_characters: int,
) -> list[str]:
    errors: list[str] = []

    # ---------------------------------------------------------
    # Unique chunk IDs
    # ---------------------------------------------------------

    chunk_ids = [
        chunk.get("chunk_id")
        for chunk in chunks
    ]

    if len(chunk_ids) != len(set(chunk_ids)):
        errors.append(
            "Duplicate chunk_id values detected."
        )

    # ---------------------------------------------------------
    # Group chunks by original source block
    # ---------------------------------------------------------

    chunks_by_block: dict[
        int,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for chunk in chunks:
        block_index = chunk.get(
            "source_block_index"
        )

        if not isinstance(block_index, int):
            errors.append(
                "Chunk has invalid source_block_index."
            )
            continue

        chunks_by_block[
            block_index
        ].append(chunk)

    # ---------------------------------------------------------
    # Validate each source section
    # ---------------------------------------------------------

    for section in sections:
        block_index = section.get(
            "block_index"
        )

        if not isinstance(block_index, int):
            errors.append(
                "Section has invalid block_index."
            )
            continue

        source_text = normalize_text(
            str(
                section.get(
                    "text",
                    "",
                )
            )
        )

        block_chunks = chunks_by_block.get(
            block_index,
            [],
        )

        # Empty structural blocks should produce no chunks.
        if not source_text:
            if block_chunks:
                errors.append(
                    f"Empty source block {block_index} "
                    "unexpectedly produced chunks."
                )

            continue

        # Every non-empty block must produce at least one chunk.
        if not block_chunks:
            errors.append(
                f"Non-empty source block {block_index} "
                "produced no chunks."
            )

            continue

        # Sort into original order.
        block_chunks = sorted(
            block_chunks,
            key=lambda chunk: (
                chunk.get(
                    "chunk_index",
                    0,
                )
            ),
        )

        expected_count = len(
            block_chunks
        )

        actual_indexes = [
            chunk.get(
                "chunk_index"
            )
            for chunk in block_chunks
        ]

        expected_indexes = list(
            range(
                1,
                expected_count + 1,
            )
        )

        if actual_indexes != expected_indexes:
            errors.append(
                f"Block {block_index}: "
                "chunk indexes are not contiguous."
            )

        # Every chunk should agree on the total count.
        for chunk in block_chunks:
            if (
                chunk.get(
                    "chunk_count_in_block"
                )
                != expected_count
            ):
                errors.append(
                    f"Block {block_index}: "
                    "chunk_count_in_block mismatch."
                )

        # Reconstruct original block text.
        reconstructed = normalize_text(
            " ".join(
                str(
                    chunk.get(
                        "text",
                        "",
                    )
                )
                for chunk in block_chunks
            )
        )

        if reconstructed != source_text:
            errors.append(
                f"Block {block_index}: "
                "reconstructed chunk text does not "
                "match source block."
            )

        # -----------------------------------------------------
        # Metadata consistency
        # -----------------------------------------------------

        fields_to_match = (
            "block_type",
            "section_number",
            "section_level",
            "parent_section_number",
            "parent_section_heading",
            "heading",
            "start_page",
            "end_page",
        )

        for chunk in block_chunks:
            for field in fields_to_match:
                if (
                    chunk.get(field)
                    != section.get(field)
                ):
                    errors.append(
                        f"Block {block_index}: "
                        f"metadata mismatch for '{field}'."
                    )

            if (
                chunk.get(
                    "section_path"
                )
                != section.get(
                    "section_path"
                )
            ):
                errors.append(
                    f"Block {block_index}: "
                    "section_path mismatch."
                )

        # -----------------------------------------------------
        # Split rules
        # -----------------------------------------------------

        is_split_block = (
            expected_count > 1
        )

        for chunk in block_chunks:
            if (
                chunk.get("is_split")
                != is_split_block
            ):
                errors.append(
                    f"Block {block_index}: "
                    "is_split metadata is incorrect."
                )

            character_count = chunk.get(
                "character_count"
            )

            if not isinstance(
                character_count,
                int,
            ):
                errors.append(
                    f"Block {block_index}: "
                    "invalid character_count."
                )

                continue

            if character_count > maximum_characters:
                errors.append(
                    f"Block {block_index}: "
                    f"chunk exceeds maximum "
                    f"{maximum_characters} characters."
                )

            # IMPORTANT:
            # The minimum applies only to chunks created by
            # splitting a larger source block.
            #
            # Naturally short 1/1 blocks are valid.
            if (
                is_split_block
                and character_count
                < minimum_split_characters
            ):
                errors.append(
                    f"Block {block_index}: "
                    f"split chunk is smaller than "
                    f"{minimum_split_characters} characters."
                )

    # ---------------------------------------------------------
    # Ensure chunks do not reference unknown blocks
    # ---------------------------------------------------------

    valid_block_indexes = {
        section.get(
            "block_index"
        )
        for section in sections
    }

    for block_index in chunks_by_block:
        if (
            block_index
            not in valid_block_indexes
        ):
            errors.append(
                f"Chunk references unknown "
                f"source block {block_index}."
            )

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate MedicalPlab chunk reconstruction, "
            "ordering and metadata integrity."
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

    sections_path = (
        PROCESSED_DIR
        / specialty
        / (
            f"{args.document_id}"
            ".sections.enriched.json"
        )
    )

    chunks_path = (
        PROCESSED_DIR
        / specialty
        / (
            f"{args.document_id}"
            ".chunks.json"
        )
    )

    if not sections_path.exists():
        raise FileNotFoundError(
            f"Enriched sections not found: "
            f"{sections_path}"
        )

    if not chunks_path.exists():
        raise FileNotFoundError(
            f"Chunks not found: "
            f"{chunks_path}"
        )

    sections_document = load_json(
        sections_path
    )

    chunk_document = load_json(
        chunks_path
    )

    sections = sections_document.get(
        "sections",
        [],
    )

    chunks = chunk_document.get(
        "chunks",
        [],
    )

    config = chunk_document.get(
        "chunking",
        {},
    )

    if not isinstance(sections, list):
        raise ValueError(
            "sections must be a list."
        )

    if not isinstance(chunks, list):
        raise ValueError(
            "chunks must be a list."
        )

    minimum_split_characters = int(
        config.get(
            "minimum_characters",
            350,
        )
    )

    maximum_characters = int(
        config.get(
            "maximum_characters",
            1800,
        )
    )

    errors = validate_integrity(
        sections,
        chunks,
        minimum_split_characters,
        maximum_characters,
    )

    nonempty_blocks = [
        section
        for section in sections
        if normalize_text(
            str(
                section.get(
                    "text",
                    "",
                )
            )
        )
    ]

    split_blocks = {
        chunk.get(
            "source_block_index"
        )
        for chunk in chunks
        if chunk.get(
            "chunk_count_in_block",
            1,
        )
        > 1
    }

    natural_short_chunks = [
        chunk
        for chunk in chunks
        if (
            chunk.get(
                "chunk_count_in_block"
            )
            == 1
            and chunk.get(
                "character_count",
                0,
            )
            < minimum_split_characters
        )
    ]

    undersized_split_chunks = [
        chunk
        for chunk in chunks
        if (
            chunk.get(
                "chunk_count_in_block",
                1,
            )
            > 1
            and chunk.get(
                "character_count",
                0,
            )
            < minimum_split_characters
        )
    ]

    print(
        "\nMedicalPlab Chunk Integrity Validator"
    )
    print("=" * 46)

    print(
        f"Document                   : "
        f"{args.document_id}"
    )

    print(
        f"Source blocks              : "
        f"{len(sections)}"
    )

    print(
        f"Non-empty source blocks    : "
        f"{len(nonempty_blocks)}"
    )

    print(
        f"Chunks                     : "
        f"{len(chunks)}"
    )

    print(
        f"Split source blocks        : "
        f"{len(split_blocks)}"
    )

    print(
        f"Natural short chunks       : "
        f"{len(natural_short_chunks)}"
    )

    print(
        f"Undersized split chunks    : "
        f"{len(undersized_split_chunks)}"
    )

    print(
        f"Integrity errors           : "
        f"{len(errors)}"
    )

    print(
        f"Validation                 : "
        f"{'PASS ✅' if not errors else 'FAIL ❌'}"
    )

    if natural_short_chunks:
        print(
            "\nNatural short blocks (allowed)"
        )
        print("-" * 80)

        for chunk in natural_short_chunks:
            print(
                f"{chunk['chunk_id']} | "
                f"{chunk['character_count']} chars | "
                f"{chunk['heading']}"
            )

    if errors:
        print(
            "\nIntegrity errors"
        )
        print("-" * 80)

        for error in errors:
            print(
                f"- {error}"
            )

        raise SystemExit(1)


if __name__ == "__main__":
    main()