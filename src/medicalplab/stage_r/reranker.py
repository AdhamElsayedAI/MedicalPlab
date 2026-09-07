"""Medical reranking engine for Stage-R.

Provides multi-factor clinical reranking assessing query overlap, medical entity matches,
section/heading relevance, and evidence density. Includes abstract interface.
"""

from abc import ABC, abstractmethod
import re
from typing import Sequence

from medicalplab.stage_b.models import require
from medicalplab.stage_b.evidence_policy import normalize
from .models import (
    EvidenceCandidate,
    QueryIntent,
    RerankedEvidence,
    RetrievalQuery,
    ScoreBreakdown,
)


INTENT_SECTION_KEYWORDS: dict[QueryIntent, tuple[str, ...]] = {
    QueryIntent.TREATMENT: (
        "treatment",
        "management",
        "therapy",
        "pharmacolog",
        "intervention",
        "medication",
    ),
    QueryIntent.DEFINITION: (
        "definition",
        "criteria",
        "classification",
        "diagnostic",
        "introduction",
        "overview",
    ),
    QueryIntent.DOSAGE: (
        "dosage",
        "dosing",
        "administration",
        "posology",
        "regimen",
    ),
    QueryIntent.SYMPTOM: (
        "symptom",
        "clinical feature",
        "presentation",
        "manifestation",
        "sign",
    ),
    QueryIntent.GUIDELINE: (
        "guideline",
        "recommendation",
        "protocol",
        "algorithm",
        "standard",
    ),
    QueryIntent.EDUCATIONAL: (
        "pathophysiology",
        "mechanism",
        "overview",
        "principle",
        "etiology",
    ),
    QueryIntent.DISEASE: (
        "etiology",
        "epidemiology",
        "risk factor",
        "pathology",
    ),
}

COMMON_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "this", "that", "these", "those", "it", "its", "as", "into", "than",
    "can", "could", "should", "would", "may", "might", "must", "which",
}


class RerankerInterface(ABC):
    """Abstract interface for medical evidence rerankers."""

    @abstractmethod
    def rerank(
        self,
        query: RetrievalQuery,
        candidates: Sequence[EvidenceCandidate],
        top_k: int = 5,
    ) -> tuple[RerankedEvidence, ...]:
        """Rerank candidates based on multi-factor clinical relevance."""
        raise NotImplementedError


class MedicalReranker(RerankerInterface):
    """Deterministic clinical multi-factor reranker."""

    def __init__(
        self,
        retrieval_weight: float = 0.40,
        rerank_weight: float = 0.60,
    ):
        require(
            isinstance(retrieval_weight, (int, float)) and 0.0 <= retrieval_weight <= 1.0,
            "'retrieval_weight' must be between 0.0 and 1.0",
        )
        require(
            isinstance(rerank_weight, (int, float)) and 0.0 <= rerank_weight <= 1.0,
            "'rerank_weight' must be between 0.0 and 1.0",
        )
        self.retrieval_weight = float(retrieval_weight)
        self.rerank_weight = float(rerank_weight)

    def _compute_query_overlap(self, query: RetrievalQuery, block_text: str) -> float:
        q_words = {w for w in normalize(query.raw_query).split() if w not in COMMON_STOPWORDS}
        if not q_words:
            return 0.0
        b_words = set(normalize(block_text).split())
        overlap = len(q_words.intersection(b_words))
        return round(overlap / len(q_words), 4)

    def _compute_entity_match(self, query: RetrievalQuery, block_text: str) -> float:
        if not query.entities:
            return 0.5  # Neutral when query contains no specific cataloged entity

        b_norm = normalize(block_text)
        matches = sum(1 for e in query.entities if normalize(e) in b_norm)
        return round(matches / len(query.entities), 4)

    def _compute_section_relevance(self, query: RetrievalQuery, heading: str, section: str) -> float:
        combined = normalize(f"{heading} {section}")
        target_keywords = INTENT_SECTION_KEYWORDS.get(query.intent, ())
        for kw in target_keywords:
            if kw in combined:
                return 1.0
        return 0.3  # Baseline relevance if not directly matching intent

    def _compute_evidence_density(self, block_text: str) -> float:
        words = [w for w in normalize(block_text).split() if len(w) >= 2]
        if not words:
            return 0.0
        content_words = [w for w in words if w not in COMMON_STOPWORDS and len(w) >= 3]
        return round(min(1.0, len(content_words) / len(words)), 4)

    def rerank(
        self,
        query: RetrievalQuery,
        candidates: Sequence[EvidenceCandidate],
        top_k: int = 5,
    ) -> tuple[RerankedEvidence, ...]:
        require(isinstance(query, RetrievalQuery), "query must be a RetrievalQuery instance")
        require(top_k >= 1, "top_k must be >= 1")

        if not candidates:
            return ()

        reranked: list[RerankedEvidence] = []

        for c in candidates:
            full_text = f"{c.heading} {c.section} {c.text}"

            overlap_score = self._compute_query_overlap(query, full_text)
            entity_score = self._compute_entity_match(query, full_text)
            section_score = self._compute_section_relevance(query, c.heading, c.section)
            density_score = self._compute_evidence_density(c.text)

            # Composite multi-factor rerank score
            raw_rerank = (
                0.35 * entity_score
                + 0.30 * overlap_score
                + 0.20 * section_score
                + 0.15 * density_score
            )
            rerank_score = round(raw_rerank, 4)

            # Combined final score
            final_score = round(
                self.retrieval_weight * c.score + self.rerank_weight * rerank_score,
                4,
            )

            # Build explainability breakdown
            if c.score_breakdown is not None:
                breakdown = ScoreBreakdown(
                    dense_score=c.score_breakdown.dense_score,
                    sparse_score=c.score_breakdown.sparse_score,
                    alpha=c.score_breakdown.alpha,
                    hybrid_score=c.score_breakdown.hybrid_score,
                    rerank_score=rerank_score,
                    final_score=final_score,
                )
            else:
                breakdown = ScoreBreakdown(
                    dense_score=0.0,
                    sparse_score=0.0,
                    alpha=0.5,
                    hybrid_score=c.score,
                    rerank_score=rerank_score,
                    final_score=final_score,
                )

            reranked.append(
                RerankedEvidence(
                    ref=c.ref,
                    document_id=c.document_id,
                    source=c.source,
                    heading=c.heading,
                    section=c.section,
                    text=c.text,
                    retrieval_score=c.score,
                    rerank_score=rerank_score,
                    final_score=final_score,
                    score_breakdown=breakdown,
                )
            )

        # Sort descending by final score
        reranked.sort(key=lambda r: r.final_score, reverse=True)
        return tuple(reranked[:top_k])
