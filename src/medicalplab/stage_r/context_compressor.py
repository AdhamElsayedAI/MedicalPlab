"""Extractive context compression engine for Stage-R.

Performs safe, extractive sentence-level filtering to reduce boilerplate without
rewriting, summarizing, or compromising citation quotes and evidence provenance.
"""

import re
from typing import Sequence, Union

from medicalplab.stage_b.models import require
from medicalplab.stage_b.evidence_policy import normalize
from .models import (
    EvidenceBlock,
    EvidenceCandidate,
    RerankedEvidence,
    RetrievalQuery,
)


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences while preserving sentence content."""
    # Split on sentence terminals followed by whitespace
    raw_sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in raw_sentences if s.strip()]


def extract_relevant_sentences(
    text: str,
    query: RetrievalQuery,
    max_sentences: int = 3,
    min_length_threshold: int = 160,
) -> str:
    """Extract the most relevant sentences in original sequence without any rewriting.
    
    If text is already compact (<= min_length_threshold), returns original text unchanged.
    """
    if len(text.strip()) <= min_length_threshold:
        return text.strip()

    sentences = _split_into_sentences(text)
    if len(sentences) <= max_sentences:
        return text.strip()

    # Score each sentence based on query overlap and entity match
    query_terms = {w for w in normalize(query.normalized_query).split() if len(w) >= 3}
    entity_terms = {normalize(e) for e in query.entities}

    scored_indices: list[tuple[float, int]] = []

    for idx, sentence in enumerate(sentences):
        s_norm = normalize(sentence)
        s_words = set(s_norm.split())

        overlap = len(query_terms.intersection(s_words))
        entity_hit = 2.0 if any(e in s_norm for e in entity_terms) else 0.0

        # Preference for informative sentences
        score = float(overlap) + entity_hit
        scored_indices.append((score, idx))

    # Pick top sentences by score
    scored_indices.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    selected_indices = sorted(idx for score, idx in scored_indices[:max_sentences])

    # Reconstruct in original document sequence (never permute)
    selected_sentences = [sentences[i] for i in selected_indices]
    return " ".join(selected_sentences)


class ContextCompressor:
    """Safe, extractive context compressor preserving 100% verbatim accuracy."""

    def __init__(self, max_sentences_per_block: int = 3):
        require(max_sentences_per_block >= 1, "'max_sentences_per_block' must be >= 1")
        self.max_sentences = max_sentences_per_block

    def compress(
        self,
        query: RetrievalQuery,
        evidence: Sequence[Union[RerankedEvidence, EvidenceCandidate, EvidenceBlock]],
    ) -> tuple[Union[RerankedEvidence, EvidenceCandidate, EvidenceBlock], ...]:
        """Compress evidence blocks by extracting only salient sentences."""
        require(isinstance(query, RetrievalQuery), "query must be a RetrievalQuery instance")

        compressed: list[Union[RerankedEvidence, EvidenceCandidate, EvidenceBlock]] = []

        for item in evidence:
            extracted_text = extract_relevant_sentences(
                item.text,
                query=query,
                max_sentences=self.max_sentences,
            )

            # Preserve the exact object type and provenance fields
            if isinstance(item, RerankedEvidence):
                compressed.append(
                    RerankedEvidence(
                        ref=item.ref,
                        document_id=item.document_id,
                        source=item.source,
                        heading=item.heading,
                        section=item.section,
                        text=extracted_text,
                        retrieval_score=item.retrieval_score,
                        rerank_score=item.rerank_score,
                        final_score=item.final_score,
                        score_breakdown=item.score_breakdown,
                    )
                )
            elif isinstance(item, EvidenceCandidate):
                compressed.append(
                    EvidenceCandidate(
                        ref=item.ref,
                        document_id=item.document_id,
                        source=item.source,
                        heading=item.heading,
                        section=item.section,
                        text=extracted_text,
                        score=item.score,
                        score_breakdown=item.score_breakdown,
                    )
                )
            elif isinstance(item, EvidenceBlock):
                compressed.append(
                    EvidenceBlock(
                        ref=item.ref,
                        document_id=item.document_id,
                        source=item.source,
                        heading=item.heading,
                        section=item.section,
                        text=extracted_text,
                        block_type=item.block_type,
                    )
                )
            else:
                raise TypeError(f"Unsupported evidence type: {type(item)}")

        return tuple(compressed)
