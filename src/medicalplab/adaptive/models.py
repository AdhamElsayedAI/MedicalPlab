"""Data models for Phase 2A Adaptive Grounded Learning Engine."""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field


class MasteryLevel(str, Enum):
    BEGINNER = "beginner"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    ADVANCED = "advanced"


class MasteryStatus(str, Enum):
    NOT_STARTED = "not_started"
    NEEDS_REVIEW = "needs_review"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WeaknessPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AdaptiveActionType(str, Enum):
    SOLVE_TARGETED_QUESTION = "SOLVE_TARGETED_QUESTION"
    ASK_GROUNDED_TUTOR = "ASK_GROUNDED_TUTOR"
    REVIEW_CONCEPT = "REVIEW_CONCEPT"
    REPEAT_TOPIC = "REPEAT_TOPIC"


class AttemptRecord(BaseModel):
    """Normalized representation of a single learner attempt."""
    attempt_key: str
    question_id: str
    subject: str
    topic: str
    selected: str
    correct: bool
    timestamp: float | None = None


class TopicMasteryRecord(BaseModel):
    """Deterministic mastery status for an individual subject/topic."""
    subject: str
    topic: str
    total_attempts: int = 0
    correct_attempts: int = 0
    accuracy: float | None = None
    mastery_score: float = 0.0
    mastery_level: MasteryLevel = MasteryLevel.BEGINNER
    mastery_status: MasteryStatus = MasteryStatus.NOT_STARTED
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    consecutive_errors: int = 0
    last_attempt_correct: bool | None = None


class WeakTopicRecord(BaseModel):
    """Identified knowledge deficit in a specific medical topic."""
    subject: str
    topic: str
    priority: WeaknessPriority
    failure_rate: float
    missed_count: int
    total_attempts: int
    consecutive_errors: int = 0
    reason: str


class AdaptiveRecommendation(BaseModel):
    """Next best pedagogical action chosen by the decision engine."""
    recommendation_id: str
    action: AdaptiveActionType
    subject: str
    topic: str
    priority: WeaknessPriority
    target_question_id: str | None = None
    tutor_mode: str | None = None
    tutor_query: str | None = None
    reason: str
    explanation: str


class LearnerState(BaseModel):
    """Unified educational representation of the learner."""
    learner_id: str
    total_attempts: int = 0
    correct_attempts: int = 0
    overall_accuracy: float | None = None
    topic_mastery: dict[str, TopicMasteryRecord] = Field(default_factory=dict)
    weak_topics: list[WeakTopicRecord] = Field(default_factory=list)
    recent_activity: list[AttemptRecord] = Field(default_factory=list)
    recommendations: list[AdaptiveRecommendation] = Field(default_factory=list)


class LearningEvent(BaseModel):
    """Incoming learning telemetry event."""
    event_id: str | None = None
    learner_id: str | None = None
    event_type: Literal["QUESTION_ATTEMPT", "TUTOR_INTERVENTION", "TOPIC_REVIEW"] = "QUESTION_ATTEMPT"
    subject: str
    topic: str
    question_id: str | None = None
    selected_option: str | None = None
    is_correct: bool | None = None
    attempt_key: str | None = None
    timestamp: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RemediationRequest(BaseModel):
    """Request to generate an evidence-grounded tutor intervention for a weakness."""
    topic: str | None = None
    question_id: str | None = None
    preferred_mode: str | None = None
    custom_query: str | None = None
