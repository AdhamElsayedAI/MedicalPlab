"""Evidence loader for Stage-B pipeline.

Converts processed chunk artifacts into strict EvidenceBlock contracts.

"""

import json
from pathlib import Path

from .models import EvidenceBlock


def normalize_reference(chunk_id: str) -> str:
    """
    Convert processed chunk id:

    DOC-WHO-CARD-0001-B0001-C01

    into Stage-B reference:

    DOC-WHO-CARD-0001:B0001:C01
    """

    if "-B" not in chunk_id:
        return chunk_id

    document_part, block_part = chunk_id.split("-B", 1)

    block_id, chunk_part = block_part.split("-", 1)

    return f"{document_part}:B{block_id}:{chunk_part}"


def load_evidence_blocks(path: str | Path) -> list[EvidenceBlock]:

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    document_id = data["document_id"]
    source_id = data["source_id"]

    blocks = []

    for chunk in data["chunks"]:

        ref = normalize_reference(chunk["chunk_id"])

        block = EvidenceBlock(
            ref=ref,
            document_id=document_id,
            source=source_id,
            heading=chunk.get("heading", ""),
            section=chunk.get("section_path", [""])[0],
            text=chunk["text"],
            block_type=chunk.get("block_type", "text"),
        )

        blocks.append(block)

    return blocks


def load_top10_evidence(
    path: str | Path,
) -> tuple[EvidenceBlock, ...]:

    blocks = load_evidence_blocks(path)

    if len(blocks) < 10:
        raise ValueError(
            f"Need at least 10 evidence blocks, found {len(blocks)}"
        )

    return tuple(blocks[:10])