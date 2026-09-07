"""Independent Stage-E data contracts for Adaptive Learning & Student Intelligence Layer.

Domain models are completely independent of Stage-B, Stage-C, and Stage-D structures.
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


class MasteryLevel(str, Enum):
    BEGINNER = "beginner"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    ADVANCED = "advanced"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecommendationPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class QuestionDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True)
class QuestionAttempt:
    """Record of a single student attempt on a question."""

    attempt_id: str
    student_id: str
    question_id: str
    topic: str
    correct: bool
    timestamp: float
    difficulty: str = "medium"

    def __post_init__(self):
        strings(self.attempt_id, self.student_id, self.question_id, self.topic)
        require(isinstance(self.correct, bool), "'correct' must be a boolean")
        require(isinstance(self.timestamp, (int, float)) and self.timestamp >= 0, "'timestamp' must be >= 0")
        normalized_diff = str(self.difficulty).strip().lower()
        require(
            normalized_diff in {d.value for d in QuestionDifficulty},
            f"Invalid difficulty '{self.difficulty}', must be one of: {[d.value for d in QuestionDifficulty]}",
        )


@dataclass(frozen=True)
class TopicMastery:
    """Deterministic mastery statistics for a specific medical topic."""

    topic: str
    total_attempts: int
    correct_attempts: int
    accuracy: float
    mastery_level: MasteryLevel
    confidence_level: ConfidenceLevel

    def __post_init__(self):
        strings(self.topic)
        require(isinstance(self.total_attempts, int) and self.total_attempts >= 0, "'total_attempts' must be >= 0")
        require(isinstance(self.correct_attempts, int) and self.correct_attempts >= 0, "'correct_attempts' must be >= 0")
        require(
            self.correct_attempts <= self.total_attempts,
            f"correct_attempts ({self.correct_attempts}) cannot exceed total_attempts ({self.total_attempts})",
        )
        require(
            isinstance(self.accuracy, (int, float)) and 0.0 <= self.accuracy <= 1.0,
            f"'accuracy' must be between 0.0 and 1.0, got {self.accuracy}",
        )
        require(
            isinstance(self.mastery_level, MasteryLevel),
            f"'mastery_level' must be a MasteryLevel enum, got {self.mastery_level}",
        )
        require(
            isinstance(self.confidence_level, ConfidenceLevel),
            f"'confidence_level' must be a ConfidenceLevel enum, got {self.confidence_level}",
        )


@dataclass(frozen=True)
class KnowledgeGap:
    """Identified learning deficit in a specific medical topic with explainability."""

    topic: str
    gap_score: float
    reason: str

    def __post_init__(self):
        strings(self.topic, self.reason)
        require(
            isinstance(self.gap_score, (int, float)) and 0.0 <= self.gap_score <= 1.0,
            f"'gap_score' must be between 0.0 and 1.0, got {self.gap_score}",
        )


@dataclass(frozen=True)
class LearningRecommendation:
    """Actionable, explainable learning intervention for the student."""

    topic: str
    priority: RecommendationPriority
    reason: str
    recommended_action: str
    target_difficulty: str = "medium"

    def __post_init__(self):
        strings(self.topic, self.reason, self.recommended_action)
        require(
            isinstance(self.priority, RecommendationPriority),
            f"'priority' must be a RecommendationPriority enum, got {self.priority}",
        )
        normalized_diff = str(self.target_difficulty).strip().lower()
        require(
            normalized_diff in {d.value for d in QuestionDifficulty},
            f"Invalid target_difficulty '{self.target_difficulty}'",
        )


@dataclass(frozen=True)
class StudentProfile:
    """Persistent student intelligence profile."""

    student_id: str
    created_at: float
    topics: tuple[str, ...]
    mastery_scores: tuple[TopicMastery, ...]
    weak_topics: tuple[str, ...]
    learning_level: MasteryLevel

    def __post_init__(self):
        strings(self.student_id)
        require(isinstance(self.created_at, (int, float)) and self.created_at >= 0, "'created_at' must be >= 0")
        require(isinstance(self.topics, tuple), "'topics' must be a tuple")
        require(all(isinstance(t, str) and t.strip() for t in self.topics), "All topics must be non-empty strings")
        require(isinstance(self.mastery_scores, tuple), "'mastery_scores' must be a tuple")
        require(
            all(isinstance(m, TopicMastery) for m in self.mastery_scores),
            "All mastery_scores must be TopicMastery instances",
        )
        require(isinstance(self.weak_topics, tuple), "'weak_topics' must be a tuple")
        require(
            all(isinstance(w, str) and w.strip() for w in self.weak_topics),
            "All weak_topics must be non-empty strings",
        )
        require(
            isinstance(self.learning_level, MasteryLevel),
            f"'learning_level' must be a MasteryLevel enum, got {self.learning_level}",
        )


@dataclass(frozen=True)
class LearningReport:
    """Comprehensive diagnostic and recommendation report returned by StageEPipeline."""

    student_profile: StudentProfile
    knowledge_gaps: tuple[KnowledgeGap, ...]
    recommendations: tuple[LearningRecommendation, ...]
    next_learning_actions: tuple[str, ...]
    generated_at: float

    def __post_init__(self):
        require(
            isinstance(self.student_profile, StudentProfile),
            "'student_profile' must be a StudentProfile instance",
        )
        require(isinstance(self.knowledge_gaps, tuple), "'knowledge_gaps' must be a tuple")
        require(
            all(isinstance(g, KnowledgeGap) for g in self.knowledge_gaps),
            "All knowledge_gaps must be KnowledgeGap instances",
        )
        require(isinstance(self.recommendations, tuple), "'recommendations' must be a tuple")
        require(
            all(isinstance(r, LearningRecommendation) for r in self.recommendations),
            "All recommendations must be LearningRecommendation instances",
        )
        require(isinstance(self.next_learning_actions, tuple), "'next_learning_actions' must be a tuple")
        require(
            all(isinstance(a, str) and a.strip() for a in self.next_learning_actions),
            "All next_learning_actions must be non-empty strings",
        )
        require(isinstance(self.generated_at, (int, float)) and self.generated_at >= 0, "'generated_at' must be >= 0")
