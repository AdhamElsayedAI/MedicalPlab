"""Data models and request/response contracts for the Grounded Generative Tutor."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


TutorMode = Literal[
    "auto",
    "socratic_hint",
    "mechanistic_explanation",
    "misconception_diagnosis",
    "distractor_explanation",
    "concept_comparison",
    "revision_summary",
]

PedagogicalState = Literal[
    "PRE_SUBMISSION",
    "POST_SUBMISSION",
    "GENERAL_STUDY",
]


class TutorChatRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=4000, description="Learner clinical/physiological query")
    mode: TutorMode = Field(default="auto", description="Pedagogical dialogue mode")
    session_id: str | None = Field(default=None, description="Client session UUID")
    learner_id: str | None = Field(default=None, description="Anonymized learner ID (demo/device)")
    question_id: str | None = Field(default=None, description="University question ID (e.g. UNI-RENAL-001)")
    attempt_key: str | None = Field(
        default=None,
        description="Submission proof key issued upon University answer submission; mandatory to unlock POST_SUBMISSION",
    )
    topic: str | None = Field(default=None, description="Physiological topic (e.g. Glomerular filtration barrier)")
    hint_level: int | None = Field(default=None, ge=1, le=3, description="1: Concept, 2: Mechanism, 3: Near-answer")
    selected_option: str | None = Field(default=None, pattern="^[A-E]$", description="Option selected by learner")
    is_submitted: bool | None = Field(
        default=None,
        description="Client-provided hint; strictly NON-AUTHORITATIVE and ignored by server for state elevation",
    )
    max_context_turns: int = Field(default=3, ge=1, le=5, description="Maximum previous dialogue turns to include")


class TutorCitationDTO(BaseModel):
    ref: str
    quote: str
    document_id: str
    pmcid: str | None = None
    title: str
    license: str
    chunk_id: str


class DistractorItem(BaseModel):
    option: str
    text: str
    why_incorrect: str
    supported_by_ref: str


class LatencyBreakdownDTO(BaseModel):
    retrieval_ms: float = 0.0
    ttft_ms: float | None = None
    generation_ms: float = 0.0
    post_verify_ms: float = 0.0
    total_ms: float = 0.0


class TutorVerificationSummaryDTO(BaseModel):
    total_propositions: int = 0
    supported_propositions: int = 0
    unsupported_propositions: int = 0
    non_factual_statements: int = 0
    veto_flags: list[str] = Field(default_factory=list)


class TutorChatResponse(BaseModel):
    response_id: str
    session_id: str
    mode: str
    message: str
    socratic_question: str | None = None
    hints: list[str] | None = None
    misconception: str | None = None
    mechanistic_explanation: str | None = None
    distractor_analysis: list[DistractorItem] | None = None
    revision_summary: str | None = None
    citations: list[TutorCitationDTO] = Field(default_factory=list)
    evidence_packet_id: str | None = None
    support_status: Literal["SUPPORTED", "SAFE_FALLBACK", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "ABSTAIN"] = "SUPPORTED"
    abstain: bool = False
    abstain_reason: str | None = None
    fallback_applied: bool = False
    pedagogical_state: PedagogicalState = "PRE_SUBMISSION"
    # `provider`/`model` reflect the ACTUAL provider/model that produced a generation attempt
    # this turn (kept for backward compatibility with existing callers). They are duplicated
    # explicitly below as `actual_generation_provider`/`actual_generation_model` alongside the
    # originally requested provider/model, so a fallback model can never silently masquerade as
    # the primary one in reporting/audit contexts.
    provider: str = "stub"
    model: str = "stub"
    requested_provider: str = "stub"
    requested_model: str = "stub"
    actual_generation_provider: str = "stub"
    actual_generation_model: str = "stub"
    provider_failover_applied: bool = False
    primary_provider_error: str | None = None
    latency_breakdown: LatencyBreakdownDTO = Field(default_factory=LatencyBreakdownDTO)
    # SERVED verification: always describes the propositions in the content actually shown to
    # the learner (recomputed against SAFE_FALLBACK content when a generated draft is rejected).
    verification: TutorVerificationSummaryDTO = Field(default_factory=TutorVerificationSummaryDTO)
    # DRAFT verification: only populated when a generated draft was rejected and replaced by
    # SAFE_FALLBACK. Describes the REJECTED draft's own proposition verification result; must
    # never be conflated with `verification` (the served content).
    draft_verification: TutorVerificationSummaryDTO | None = None


class TutorDraftCitation(BaseModel):
    ref: str
    quote: str
    document_id: str
    chunk_id: str


class TutorDraftOutput(BaseModel):
    """Schema expected from GenerativeProvider structured generation."""
    message: str
    socratic_question: str | None = None
    hints: list[str] | None = None
    misconception: str | None = None
    mechanistic_explanation: str | None = None
    distractor_analysis: list[dict[str, Any]] | None = None
    revision_summary: str | None = None
    citations: list[TutorDraftCitation] = Field(default_factory=list)


PropositionCategory = Literal[
    "FACTUAL_CLAIM",
    "SOCRATIC_QUESTION",
    "EDUCATIONAL_HINT",
    "CONVERSATIONAL_META",
]


class ExtractedProposition(BaseModel):
    prop_id: str
    text: str
    source_field: str
    classification: Literal["SUBSTANTIVE_FACTUAL", "NON_FACTUAL_PEDAGOGICAL_LANGUAGE"]
    category: PropositionCategory = "FACTUAL_CLAIM"
    cited_ref: str | None = None
    is_supported: bool = False
    verification_reason: str | None = None
    veto_trigger: str | None = None
    # Forensic metadata: which evidence candidate was actually evaluated, and the raw
    # verifier result, captured alongside the existing decision (never changes it).
    verified_document_id: str | None = None
    verified_chunk_id: str | None = None
    verifier_state: str | None = None
    verifier_confidence: float | None = None


class ForensicPropositionRecord(BaseModel):
    """Non-sensitive audit record for a single substantive proposition, sufficient to
    distinguish MODEL_GENERATION_ERROR / VERIFIER_FALSE_POSITIVE / EVIDENCE_BINDING_ERROR /
    RETRIEVAL_MISMATCH on a later forensic review, without needing another live call.

    Never carries API keys, auth headers, hidden prompts, chain-of-thought, PII, or
    restricted-publisher content. Proposition/evidence text is included only when the
    caller's redaction policy allows it (`store_full_text`) and, for evidence, only when
    the source document's DisplayQuotationStatus permits it; otherwise only a stable hash
    plus source/chunk identifiers are retained.
    """

    request_id: str
    proposition_id: str
    source_field: str
    classification: Literal["SUBSTANTIVE_FACTUAL", "NON_FACTUAL_PEDAGOGICAL_LANGUAGE"]
    category: PropositionCategory = "FACTUAL_CLAIM"

    proposition_text: str | None = None
    proposition_text_hash: str

    evidence_document_id: str | None = None
    evidence_chunk_id: str | None = None
    evidence_excerpt: str | None = None
    evidence_text_hash: str | None = None

    verifier_state: str | None = None
    verifier_confidence: float | None = None
    veto_flags: list[str] = Field(default_factory=list)
    is_supported: bool

    requested_provider: str
    requested_model: str
    actual_generation_provider: str
    actual_generation_model: str
    provider_failover_applied: bool

    support_status: str
    reached_learner: bool
