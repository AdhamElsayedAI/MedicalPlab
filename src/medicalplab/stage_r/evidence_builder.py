"""Evidence packet builder for Stage-R.

Deduplicates and validates retrieved evidence, ensuring full compatibility with downstream
Stage-B, Stage-C, Stage-D, and Stage-E components.
"""

from typing import Any, Mapping, Sequence, Union

from medicalplab.stage_b.models import require, strings
from .models import (
    EvidenceBlock,
    EvidenceCandidate,
    EvidencePacket,
    RerankedEvidence,
)


def build_evidence_packet(
    query: str,
    evidence: Sequence[Union[RerankedEvidence, EvidenceCandidate, EvidenceBlock]],
    top_k: int = 5,
    metadata: Mapping[str, Any] | None = None,
) -> EvidencePacket:
    """Construct an immutable EvidencePacket with deduplicated Top-K blocks."""
    strings(query)
    require(top_k >= 1, "'top_k' must be >= 1")
    require(
        isinstance(evidence, (list, tuple)),
        "'evidence' must be a sequence of evidence items",
    )

    clean_blocks: list[EvidenceBlock] = []
    seen_refs: set[str] = set()

    for item in evidence:
        if len(clean_blocks) >= top_k:
            break

        ref = item.ref.strip()
        if ref in seen_refs:
            continue

        # Invariant validations
        require(len(ref) > 0, "Evidence block 'ref' cannot be empty")
        require(len(item.text.strip()) > 0, f"Evidence block '{ref}' text cannot be empty")
        require(len(item.source.strip()) > 0, f"Evidence block '{ref}' source cannot be empty")

        clean_blocks.append(
            EvidenceBlock(
                ref=ref,
                document_id=item.document_id.strip(),
                source=item.source.strip(),
                heading=item.heading.strip(),
                section=item.section.strip(),
                text=item.text.strip(),
                block_type="text",
            )
        )
        seen_refs.add(ref)

    require(len(clean_blocks) >= 1, "EvidencePacket requires at least one valid evidence block")

    # Serialize metadata map into immutable tuple of pairs
    meta_pairs: list[tuple[str, str]] = []
    if metadata:
        for k, v in metadata.items():
            meta_pairs.append((str(k), str(v)))

    return EvidencePacket(
        query=query.strip(),
        blocks=tuple(clean_blocks),
        top_k=top_k,
        metadata=tuple(meta_pairs),
    )
