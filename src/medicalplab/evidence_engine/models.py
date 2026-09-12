"""
MedicalPlab Shared Evidence Engine V2 — Immutable Core Data Contracts
======================================================================
Defines unified data models and contracts for:
- QueryRepresentation (original, canonical, neutral_target)
- DocumentCard (deterministic, extractive-only corpus document descriptors)
- RetrievedCandidate (multi-channel candidate with provenance tracking)
- VerificationState (SUPPORTED, PARTIALLY_SUPPORTED, CONTRADICTED, NOT_SUPPORTED)
- ClaimVerificationResult (atomic claim grounding outcome with veto flags)
- EvidencePacket (end-to-end evidence bundle for downstream tutors and engines)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence


class VerificationState(str, Enum):
    """4-state claim grounding classification for MedicalPlab."""
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"


class PlabVerificationStatus(str, Enum):
    """Classification for PLAB SBA questions."""
    EVIDENCE_VERIFIED = "EVIDENCE_VERIFIED"
    NEEDS_SOURCE_REPAIR = "NEEDS_SOURCE_REPAIR"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class QueryRepresentation:
    """Exact three clinical query representations."""
    original_query: str
    canonical_query: str
    neutral_target: str
    has_negation: bool = False
    detected_entities: list[str] = field(default_factory=list)
    transformations: list[str] = field(default_factory=list)


@dataclass
class DocumentCard:
    """Deterministic, extractive document card without generative hallucination."""
    document_id: str
    title: str
    authority: str
    abstract: str
    topic_tags: list[str] = field(default_factory=list)
    section_headings: list[str] = field(default_factory=list)
    synopsis: str = ""
    license_name: str = ""
    doi: str | None = None
    pmcid: str | None = None
    sha256: str = ""
    authority_score: int = 0
    embedding: list[float] | None = None

    def render_routing_text(self) -> str:
        """Extractive deterministic text used for document router cross-encoding."""
        topics_str = ", ".join(self.topic_tags) if self.topic_tags else "General Nephrology"
        headings_preview = " | ".join(self.section_headings[:15]) if self.section_headings else "N/A"
        abstract_snippet = self.abstract[:500] if self.abstract else self.synopsis[:500]
        return (
            f"Title: {self.title}\n"
            f"Authority / Source: {self.authority}\n"
            f"Topics: {topics_str}\n"
            f"Major Sections: {headings_preview}\n"
            f"Overview: {abstract_snippet}"
        )


@dataclass
class RetrievedCandidate:
    """Candidate passage with multi-channel rank and provenance tracking."""
    chunk_id: str
    document_id: str
    section_path: list[str] = field(default_factory=list)
    heading: str = ""
    text: str = ""
    doc_title: str = ""
    fused_score: float = 0.0
    channel_ranks: dict[str, int] = field(default_factory=dict)
    channel_scores: dict[str, float] = field(default_factory=dict)
    rerank_score: float = 0.0

    def render_structured_passage(self) -> str:
        """Hierarchical structured passage representation for cross-encoder reranking."""
        sec_str = " > ".join(self.section_path) if self.section_path else self.heading or "General"
        return (
            f"Title: {self.doc_title}\n"
            f"Section Path: {sec_str}\n"
            f"Heading: {self.heading}\n"
            f"Evidence: {self.text}"
        )


@dataclass
class ClaimVerificationResult:
    """Grounding outcome for an individual atomic clinical proposition."""
    claim_id: str
    claim_text: str
    state: VerificationState
    confidence: float
    cited_chunk_id: str | None = None
    cited_document_id: str | None = None
    cited_section: str | None = None
    evidence_span: str | None = None
    rationale: str = ""
    veto_flags: list[str] = field(default_factory=list)
    is_high_risk: bool = False


@dataclass
class EvidencePacket:
    """End-to-end evidence bundle provided to clinical reasoning, tutor, and PLAB."""
    query: QueryRepresentation
    routed_document_ids: list[str]
    candidates: list[RetrievedCandidate]
    top_passage: RetrievedCandidate | None
    claim_verifications: list[ClaimVerificationResult] = field(default_factory=list)
    abstain: bool = False
    abstain_reason: str | None = None
