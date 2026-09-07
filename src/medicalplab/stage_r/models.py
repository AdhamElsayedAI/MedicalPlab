"""Independent Stage-R data contracts for Advanced Medical Retrieval Intelligence Layer.

Domain models are completely independent of Stage-B, Stage-C, Stage-D, and Stage-E structures.
Only generic utilities (require, strings, exact_keys, strict_json, ContractError, normalize) are reused.
All dataclasses are immutable and frozen.
"""

from dataclasses import dataclass
from enum import Enum

from medicalplab.stage_b.models import (
    ContractError,
    exact_keys,
    require,
    strict_json,
    strings,
)
from medicalplab.stage_b.evidence_policy import normalize


class QueryIntent(str, Enum):
    DEFINITION = "definition"
    TREATMENT = "treatment"
    DOSAGE = "dosage"
    SYMPTOM = "symptom"
    DISEASE = "disease"
    GUIDELINE = "guideline"
    EDUCATIONAL = "educational"


@dataclass(frozen=True)
class ScoreBreakdown:
    """Detailed score component breakdown for retrieval explainability."""

    dense_score: float
    sparse_score: float
    alpha: float
    hybrid_score: float
    rerank_score: float = 0.0
    final_score: float = 0.0

    def __post_init__(self):
        require(isinstance(self.dense_score, (int, float)), "'dense_score' must be numeric")
        require(isinstance(self.sparse_score, (int, float)), "'sparse_score' must be numeric")
        require(
            isinstance(self.alpha, (int, float)) and 0.0 <= self.alpha <= 1.0,
            "'alpha' must be between 0.0 and 1.0",
        )
        require(isinstance(self.hybrid_score, (int, float)), "'hybrid_score' must be numeric")
        require(isinstance(self.rerank_score, (int, float)), "'rerank_score' must be numeric")
        require(isinstance(self.final_score, (int, float)), "'final_score' must be numeric")


@dataclass(frozen=True)
class RetrievalQuery:
    """Structured representation of an analyzed and expanded retrieval query."""

    raw_query: str
    normalized_query: str
    expanded_terms: tuple[str, ...]
    intent: QueryIntent
    entities: tuple[str, ...]

    def __post_init__(self):
        strings(self.raw_query, self.normalized_query)
        require(isinstance(self.intent, QueryIntent), f"'intent' must be QueryIntent enum, got {self.intent}")
        require(isinstance(self.expanded_terms, tuple), "'expanded_terms' must be a tuple")
        require(
            all(isinstance(t, str) and t.strip() for t in self.expanded_terms),
            "All expanded_terms must be non-empty strings",
        )
        require(isinstance(self.entities, tuple), "'entities' must be a tuple")
        require(
            all(isinstance(e, str) and e.strip() for e in self.entities),
            "All entities must be non-empty strings",
        )


@dataclass(frozen=True)
class EvidenceCandidate:
    """Intermediate candidate evidence block retrieved from hybrid search."""

    ref: str
    document_id: str
    source: str
    heading: str
    section: str
    text: str
    score: float
    score_breakdown: ScoreBreakdown | None = None

    def __post_init__(self):
        strings(self.ref, self.document_id, self.source, self.text)
        require(isinstance(self.score, (int, float)), "'score' must be numeric")
        if self.score_breakdown is not None:
            require(
                isinstance(self.score_breakdown, ScoreBreakdown),
                "'score_breakdown' must be a ScoreBreakdown instance",
            )


@dataclass(frozen=True)
class RerankedEvidence:
    """Evidence candidate with multi-factor clinical reranking scores."""

    ref: str
    document_id: str
    source: str
    heading: str
    section: str
    text: str
    retrieval_score: float
    rerank_score: float
    final_score: float
    score_breakdown: ScoreBreakdown | None = None

    def __post_init__(self):
        strings(self.ref, self.document_id, self.source, self.text)
        require(isinstance(self.retrieval_score, (int, float)), "'retrieval_score' must be numeric")
        require(isinstance(self.rerank_score, (int, float)), "'rerank_score' must be numeric")
        require(isinstance(self.final_score, (int, float)), "'final_score' must be numeric")


@dataclass(frozen=True)
class EvidenceBlock:
    """Standardized medical evidence block compatible across MedicalPlab stages."""

    ref: str
    document_id: str
    source: str
    heading: str
    section: str
    text: str
    block_type: str = "text"

    def __post_init__(self):
        strings(self.ref, self.document_id, self.source, self.text)


@dataclass(frozen=True)
class EvidencePacket:
    """Final Top-K evidence packet ready for downstream consuming stages."""

    query: str
    blocks: tuple[EvidenceBlock, ...]
    top_k: int
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self):
        strings(self.query)
        require(isinstance(self.top_k, int) and self.top_k >= 1, "'top_k' must be >= 1")
        require(isinstance(self.blocks, tuple), "'blocks' must be a tuple")
        require(
            all(isinstance(b, EvidenceBlock) for b in self.blocks),
            "All items in blocks must be EvidenceBlock instances",
        )
        require(isinstance(self.metadata, tuple), "'metadata' must be a tuple of key-value pairs")


@dataclass(frozen=True)
class EvaluationResult:
    """Information retrieval evaluation metrics across a test set."""

    recall_at_k: float
    precision_at_k: float
    hit_rate: float
    mrr: float
    k: int

    def __post_init__(self):
        require(isinstance(self.k, int) and self.k >= 1, "'k' must be an integer >= 1")
        for metric_name, val in [
            ("recall_at_k", self.recall_at_k),
            ("precision_at_k", self.precision_at_k),
            ("hit_rate", self.hit_rate),
            ("mrr", self.mrr),
        ]:
            require(
                isinstance(val, (int, float)) and 0.0 <= val <= 1.0,
                f"'{metric_name}' must be between 0.0 and 1.0, got {val}",
            )
