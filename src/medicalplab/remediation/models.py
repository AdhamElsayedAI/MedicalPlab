"""Data models and schemas for MedicalPlab Phase 2B Intelligent Socratic Remediation Engine.

Adheres strictly to the mandatory Phase 2B engineering invariants:
1. Epistemic uncertainty: Behavioral hypotheses (HYPOTHESIS, POSSIBLE_PATTERN, INSUFFICIENT_EVIDENCE),
   never uncalibrated clinical claims.
2. Zero medical factual truth in taxonomy schemas (evidence references and chunk IDs only).
3. Separation of conversation from learning measurement: dialogue completion does not confirm transfer.
   Only independent, held-out transfer assessment supplies transfer confirmation.
4. Bounded 3-turn Socratic lifecycle: Turn 1 (Probe) -> Turn 2 (Guide) -> Turn 3 (Consolidate & Check Readiness).
5. 5-Stage Reasoning Progression Timeline UX tracking:
   Initial Answer -> Possible Learning Gap -> Guided Remediation -> Transfer Result -> Next Recommendation.
6. Qualified Learning Evidence integration: zero unsupported mastery inflation in Phase 2A.
"""
from __future__ import annotations

from enum import Enum
import time
from typing import Any, Literal
from pydantic import BaseModel, Field


class EpistemicType(str, Enum):
    """Epistemic classification of detection findings."""
    HYPOTHESIS = "HYPOTHESIS"


class DetectionStatus(str, Enum):
    """Calibrated classification of pattern detection observations."""
    CONFIRMED_PATTERN = "CONFIRMED_PATTERN"        # Multi-attempt behavioral corroboration (unreachable in MVP)
    POSSIBLE_PATTERN = "POSSIBLE_PATTERN"          # Single observed distractor matching reviewed taxonomy
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE" # Unmapped, ambiguous, or sub-threshold distractor


class EvidenceStrength(str, Enum):
    """Qualitative evidence strength classification (avoiding false numeric precision)."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class ReasoningPatternCategory(str, Enum):
    """Categorization of cognitive/reasoning errors in medical education."""
    UPSTREAM_DOWNSTREAM_INVERSION = "upstream_downstream_inversion"
    ENZYME_ROLE_INVERSION = "enzyme_role_inversion"
    RECEPTOR_SPECIFICITY_CONFUSION = "receptor_specificity_confusion"
    PHYSIOLOGICAL_FEEDBACK_MISDIRECTION = "physiological_feedback_misdirection"
    ANATOMICAL_COMPARTMENT_CONFLATION = "anatomical_compartment_conflation"
    CLINICAL_SYNDROME_OVERLAP = "clinical_syndrome_overlap"
    GENERAL_CONCEPTUAL_GAP = "general_conceptual_gap"


class SocraticStrategyType(str, Enum):
    """Socratic pedagogical remediation strategies."""
    GUIDED_RECALL = "GUIDED_RECALL"                # Default MVP initial strategy
    CONTRAST_CASE = "CONTRAST_CASE"
    STEPWISE_DECOMPOSITION = "STEPWISE_DECOMPOSITION"
    COUNTEREXAMPLE_PROBE = "COUNTEREXAMPLE_PROBE"


class RemediationLifecycleState(str, Enum):
    """State machine lifecycle stages of a remediation session."""
    CREATED = "CREATED"                            # Initialized from original attempt
    REMEDIATING = "REMEDIATING"                    # In-progress 3-turn Socratic dialogue
    AWAITING_TRANSFER = "AWAITING_TRANSFER"        # Dialogue concluded; awaiting independent transfer assessment
    COMPLETED = "COMPLETED"                        # Session concluded with terminal outcome


class RemediationOutcome(str, Enum):
    """Terminal outcomes for a remediation intervention."""
    TRANSFER_CONFIRMED = "TRANSFER_CONFIRMED"         # Correct on eligible held-out transfer item (unassisted)
    TRANSFER_NOT_CONFIRMED = "TRANSFER_NOT_CONFIRMED" # Incorrect on eligible held-out transfer item
    UNRESOLVED = "UNRESOLVED"                         # Assisted transfer, unavailable transfer item, or turn limit reached
    ABANDONED = "ABANDONED"                           # Explicit student exit or timeout
    SAFETY_FALLBACK = "SAFETY_FALLBACK"               # Verification or retrieval failure in evidence pipeline


class RemediationStatus(str, Enum):
    """Transitional UI dialogue stages (retained for backward-compatible views)."""
    PROBING = "PROBING"          # Turn 1: Challenge flawed premise
    GUIDING = "GUIDING"          # Turn 2: Provide grounded mechanistic clue
    CONFIRMING = "CONFIRMING"    # Turn 3: Consolidate reasoning / check readiness
    RESOLVED = "RESOLVED"        # Backward-compatibility alias
    UNRESOLVED = "UNRESOLVED"    # Terminal non-resolution


CANONICAL_SAFETY_FALLBACK_MESSAGE: str = (
    "I couldn't verify enough evidence to give a fully grounded explanation right now. "
    "Let's work through this together using what you already know."
)


# --- Taxonomy & Pattern Models ---

class ReasoningPatternTaxonomyItem(BaseModel):
    """Canonical taxonomy entry.

    CRITICAL INVARIANT:
    Zero medical truth storage. No factual statements or clinical assertions.
    Stores strictly the cognitive pattern, pedagogical category, strategy,
    and evidence references (chunk IDs) for live retrieval.
    """
    pattern_id: str
    topic: str
    category: ReasoningPatternCategory
    reasoning_pattern: str
    recommended_strategy: SocraticStrategyType = SocraticStrategyType.GUIDED_RECALL
    evidence_references: list[str] = Field(default_factory=list)
    version: str = "1.0.0"
    review_status: str = "VERIFIED_EDUCATIONAL"


class DistractorMapping(BaseModel):
    """Deterministic association of a specific distractor option to a reasoning pattern."""
    question_id: str
    distractor_option: str = Field(pattern="^[A-E]$")
    pattern_id: str
    confidence_weight: float = Field(ge=0.0, le=1.0, default=0.85)
    detection_rationale: str
    rule_version: str = "1.0.0"


class PatternHypothesis(BaseModel):
    """Explainable, versioned hypothesis of a learner's suspected cognitive gap."""
    hypothesis_id: str
    epistemic_type: EpistemicType = EpistemicType.HYPOTHESIS
    detection_status: DetectionStatus
    category: ReasoningPatternCategory
    pattern_id: str
    candidate_pattern: str
    evidence_strength: EvidenceStrength = EvidenceStrength.MODERATE
    detection_rationale: str
    rule_version: str = "1.0.0"
    taxonomy_version: str = "1.0.0"
    supporting_signals: list[str] = Field(default_factory=list)
    ambiguity_reason: str | None = None
    is_fallback: bool = False


class DetectedLearningGap(BaseModel):
    """Backward-compatible wrapper for PatternHypothesis in existing service code."""
    pattern_id: str
    topic: str
    category: ReasoningPatternCategory
    reasoning_pattern: str
    recommended_strategy: SocraticStrategyType
    confidence: float = Field(ge=0.0, le=1.0, default=0.75)
    detection_rationale: str
    evidence_references: list[str] = Field(default_factory=list)
    is_fallback: bool = False
    hypothesis: PatternHypothesis | None = None


# --- Learner Signals & Transfer Assessment ---

class PerformanceSignal(BaseModel):
    """Validated server-side attempt record triggering remediation."""
    attempt_id: str
    learner_id: str
    question_id: str
    question_version: str = "1.0.0"
    selected_option: str
    correct_option: str
    is_correct: bool
    topic: str
    subject: str = "Renal physiology"
    timestamp: float = Field(default_factory=time.time)
    was_assisted: bool = False
    prior_exposure_count: int = 0


class TransferItemDTO(BaseModel):
    """Held-out transfer assessment item delivered to learner.

    STRICT INVARIANT:
    Excludes correct_answer, explanation, or distractor annotations to prevent answer key leakage.
    """
    question_id: str
    stem: str
    options: dict[str, str]
    subject: str
    topic: str
    difficulty: str
    evidence_title: str | None = None
    evidence_license: str | None = None


class TransferAttempt(BaseModel):
    """Scored submission on an independent transfer item."""
    question_id: str
    question_version: str = "1.0.0"
    submitted_option: str = Field(pattern="^[A-E]$")
    is_correct: bool
    was_assisted: bool = False
    prior_exposure_count: int = 0
    submitted_at: float = Field(default_factory=time.time)


class QualifiedLearningEvidenceEvent(BaseModel):
    """Event emitted to Phase 2A Adaptive Learning Engine upon remediation resolution."""
    event_id: str
    learner_id: str
    original_question_id: str
    transfer_question_id: str | None = None
    topic: str
    subject: str = "Renal physiology"
    outcome: RemediationOutcome
    is_transfer_confirmed: bool
    was_assisted: bool
    timestamp: float = Field(default_factory=time.time)


# --- Timeline & Turn Records ---

class ReasoningTimelineItem(BaseModel):
    """5-stage reasoning progression tracking the complete educational journey."""
    initial_pattern: str = Field(description="Description of the initial distractor choice and suspected premise")
    learning_gap: str = Field(description="Calibrated hypothesis of the underlying reasoning pattern")
    guided_practice: str = Field(default="In progress", description="Status of bounded 3-turn Socratic practice")
    transfer_result: str = Field(default="Awaiting independent transfer assessment", description="Independent assessment result")
    next_recommendation: str | None = Field(default=None, description="Adaptive recommendation from Phase 2A")
    corrected_reasoning: str | None = Field(default=None, description="Deprecated alias for guided practice synthesis")
    status: Literal["IN_PROGRESS", "RESOLVED", "UNRESOLVED", "AWAITING_TRANSFER", "COMPLETED", "SAFETY_FALLBACK"] = "IN_PROGRESS"


class RemediationTurnRecord(BaseModel):
    """Audit record for an individual dialogue turn within the 3-turn limit."""
    turn_number: int = Field(ge=1, le=3)
    phase: Literal["PROBE", "GUIDE", "CONFIRM", "CONSOLIDATE"]
    tutor_message: str
    socratic_probe: str | None = None
    student_message: str | None = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)
    is_safety_fallback: bool = False


class RemediationSessionState(BaseModel):
    """Complete in-flight or completed state of a Socratic remediation session."""
    session_id: str
    user_id: str
    original_attempt_id: str = "ATTEMPT-LEGACY"
    question_id: str
    selected_option: str
    topic: str
    turn_number: int = Field(default=1, ge=1, le=3)
    max_turns: int = 3
    is_complete: bool = False
    lifecycle_state: RemediationLifecycleState = RemediationLifecycleState.CREATED
    outcome: RemediationOutcome | None = None
    remediation_status: RemediationStatus = RemediationStatus.PROBING
    detected_gap: DetectedLearningGap
    hypothesis: PatternHypothesis | None = None
    strategy: SocraticStrategyType = SocraticStrategyType.GUIDED_RECALL
    timeline: ReasoningTimelineItem
    turns: list[RemediationTurnRecord] = Field(default_factory=list)
    transfer_question_id: str | None = None
    transfer_attempt: TransferAttempt | None = None
    assistance_invoked: bool = False
    evidence_status: Literal["NONE", "PENDING", "DELIVERING", "DELIVERED"] = "NONE"
    idempotency_keys: list[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


# --- REST API Request & Response Contracts ---

class StartRemediationRequest(BaseModel):
    """POST /api/v1/remediation/start payload."""
    question_id: str = Field(min_length=3, max_length=120)
    selected_option: str = Field(pattern="^[A-E]$")
    topic: str | None = Field(default=None, max_length=200)
    attempt_id: str | None = Field(default=None, max_length=120)
    idempotency_key: str | None = Field(default=None, max_length=120)


class TurnRemediationRequest(BaseModel):
    """POST /api/v1/remediation/turn payload."""
    session_id: str = Field(min_length=8, max_length=120)
    student_message: str = Field(min_length=1, max_length=4000)
    idempotency_key: str | None = Field(default=None, max_length=120)


class TransferSubmissionRequest(BaseModel):
    """POST /api/v1/remediation/session/{session_id}/transfer payload."""
    session_id: str = Field(min_length=8, max_length=120)
    question_id: str = Field(min_length=3, max_length=120)
    selected_option: str = Field(pattern="^[A-E]$")
    was_assisted: bool = False
    idempotency_key: str | None = Field(default=None, max_length=120)


class TransferSubmissionResponse(BaseModel):
    """Response returned when a transfer item is scored."""
    session_id: str
    outcome: RemediationOutcome
    is_correct: bool
    explanation: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    timeline: ReasoningTimelineItem
    next_recommendation: dict[str, Any] | None = None


class RemediationTurnResponse(BaseModel):
    """Response contract returned by dialogue progression endpoints."""
    session_id: str
    turn_number: int = Field(ge=1, le=3)
    max_turns: int = 3
    is_complete: bool
    lifecycle_state: RemediationLifecycleState = RemediationLifecycleState.REMEDIATING
    outcome: RemediationOutcome | None = None
    remediation_status: RemediationStatus = RemediationStatus.PROBING
    pattern_id: str | None = None
    reasoning_pattern: str | None = None
    strategy: SocraticStrategyType = SocraticStrategyType.GUIDED_RECALL
    timeline: ReasoningTimelineItem
    tutor_message: str
    socratic_probe: str | None = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    transfer_available: bool = False


class RemediationSessionResponse(BaseModel):
    """Full session inspection response for GET /api/v1/remediation/session/{session_id}."""
    session_id: str
    user_id: str
    question_id: str
    topic: str
    turn_number: int
    max_turns: int
    is_complete: bool
    lifecycle_state: RemediationLifecycleState
    outcome: RemediationOutcome | None = None
    strategy: SocraticStrategyType
    timeline: ReasoningTimelineItem
    turns: list[RemediationTurnRecord]
    transfer_item: TransferItemDTO | None = None
    transfer_attempt: TransferAttempt | None = None
