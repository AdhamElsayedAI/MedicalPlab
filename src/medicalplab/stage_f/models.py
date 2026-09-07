"""Independent Stage-F data contracts for Platform Orchestration & Learning Intelligence.

All dataclasses are immutable and frozen.
Only generic utilities (require, strings, exact_keys, strict_json, ContractError, normalize) are reused.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from medicalplab.stage_b.models import (
    ContractError,
    exact_keys,
    require,
    strict_json,
    strings,
)
from medicalplab.stage_b.evidence_policy import normalize


class PlatformIntent(str, Enum):
    TEACHING = "teaching"
    ASSESSMENT = "assessment"
    LEARNING_ANALYSIS = "learning_analysis"
    EXAM = "exam"
    CASE_SIMULATION = "case_simulation"


class ExamMode(str, Enum):
    PRACTICE = "practice"
    EXAM = "exam"
    REVIEW = "review"


class PlatformDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GoalStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"


@dataclass(frozen=True)
class UserGoal:
    """Target learning goal established by or for a student."""

    goal_id: str
    student_id: str
    target_topic: str
    target_mastery: str
    target_accuracy: float = 0.80
    deadline_timestamp: float | None = None
    status: GoalStatus = GoalStatus.NOT_STARTED

    def __post_init__(self):
        strings(self.goal_id, self.student_id, self.target_topic, self.target_mastery)
        require(
            isinstance(self.target_accuracy, (int, float)) and 0.0 <= self.target_accuracy <= 1.0,
            "'target_accuracy' must be between 0.0 and 1.0",
        )
        require(isinstance(self.status, GoalStatus), f"'status' must be GoalStatus enum, got {self.status}")
        if self.deadline_timestamp is not None:
            require(
                isinstance(self.deadline_timestamp, (int, float)) and self.deadline_timestamp >= 0,
                "'deadline_timestamp' must be >= 0",
            )


@dataclass(frozen=True)
class SessionContext:
    """Active context tracking a student's learning session."""

    session_id: str
    student_id: str
    current_topic: str
    learning_objective: str
    difficulty_context: PlatformDifficulty
    interactions_count: int
    created_at: float
    last_active_at: float

    def __post_init__(self):
        strings(self.session_id, self.student_id, self.current_topic, self.learning_objective)
        require(
            isinstance(self.difficulty_context, PlatformDifficulty),
            f"'difficulty_context' must be PlatformDifficulty enum, got {self.difficulty_context}",
        )
        require(isinstance(self.interactions_count, int) and self.interactions_count >= 0, "'interactions_count' must be >= 0")
        require(isinstance(self.created_at, (int, float)) and self.created_at >= 0, "'created_at' must be >= 0")
        require(isinstance(self.last_active_at, (int, float)) and self.last_active_at >= 0, "'last_active_at' must be >= 0")


@dataclass(frozen=True)
class ExamConfig:
    """Configuration for an exam instance."""

    exam_id: str
    student_id: str
    mode: ExamMode
    topic: str
    question_count: int
    time_limit_minutes: int
    pass_percentage: float = 0.70

    def __post_init__(self):
        strings(self.exam_id, self.student_id, self.topic)
        require(isinstance(self.mode, ExamMode), f"'mode' must be ExamMode enum, got {self.mode}")
        require(isinstance(self.question_count, int) and self.question_count >= 1, "'question_count' must be >= 1")
        require(isinstance(self.time_limit_minutes, int) and self.time_limit_minutes >= 1, "'time_limit_minutes' must be >= 1")
        require(
            isinstance(self.pass_percentage, (int, float)) and 0.0 <= self.pass_percentage <= 1.0,
            "'pass_percentage' must be between 0.0 and 1.0",
        )


@dataclass(frozen=True)
class ExamQuestion:
    """Question item within an exam."""

    question_id: str
    topic: str
    question: str
    options: tuple[str, ...]
    correct_answer: str
    explanation: str
    difficulty: PlatformDifficulty
    citations: tuple[str, ...] = ()

    def __post_init__(self):
        strings(self.question_id, self.topic, self.question, self.correct_answer, self.explanation)
        require(isinstance(self.options, tuple) and len(self.options) >= 2, "'options' must be a tuple with >= 2 items")
        require(
            isinstance(self.difficulty, PlatformDifficulty),
            f"'difficulty' must be PlatformDifficulty enum, got {self.difficulty}",
        )
        require(isinstance(self.citations, tuple), "'citations' must be a tuple")


@dataclass(frozen=True)
class ExamSubmission:
    """Student submission for an exam."""

    exam_id: str
    student_id: str
    answers: tuple[tuple[str, str], ...]  # ((question_id, selected_option), ...)
    time_taken_seconds: float

    def __post_init__(self):
        strings(self.exam_id, self.student_id)
        require(isinstance(self.answers, tuple), "'answers' must be a tuple of (qid, answer) pairs")
        require(isinstance(self.time_taken_seconds, (int, float)) and self.time_taken_seconds >= 0, "'time_taken_seconds' must be >= 0")


@dataclass(frozen=True)
class ExamAnalytics:
    """Comprehensive performance analytics from an exam feeding Stage-E."""

    exam_id: str
    student_id: str
    topic: str
    score: int
    total_questions: int
    percentage: float
    passed: bool
    mode: ExamMode
    question_results: tuple[tuple[str, bool, str, str], ...]  # (qid, is_correct, selected, correct)
    attempt_records: tuple[tuple[str, str, str, bool, str], ...]  # (attempt_id, qid, topic, correct, difficulty)

    def __post_init__(self):
        strings(self.exam_id, self.student_id, self.topic)
        require(isinstance(self.score, int) and 0 <= self.score <= self.total_questions, "Invalid score")
        require(isinstance(self.percentage, (int, float)) and 0.0 <= self.percentage <= 1.0, "'percentage' must be between 0.0 and 1.0")
        require(isinstance(self.passed, bool), "'passed' must be a boolean")
        require(isinstance(self.mode, ExamMode), "'mode' must be ExamMode enum")
        require(isinstance(self.question_results, tuple), "'question_results' must be a tuple")
        require(isinstance(self.attempt_records, tuple), "'attempt_records' must be a tuple")


@dataclass(frozen=True)
class CaseSimulationStep:
    """Single clinical reasoning step in an evidence-grounded case simulation."""

    step_number: int
    findings: str
    recommended_action: str
    rationale: str
    citations: tuple[str, ...]

    def __post_init__(self):
        require(isinstance(self.step_number, int) and self.step_number >= 1, "'step_number' must be >= 1")
        strings(self.findings, self.recommended_action, self.rationale)
        require(isinstance(self.citations, tuple), "'citations' must be a tuple")


@dataclass(frozen=True)
class CaseSimulationResult:
    """Completed evidence-grounded patient clinical case simulation."""

    simulation_id: str
    student_id: str
    topic: str
    vignette: str
    steps: tuple[CaseSimulationStep, ...]
    clinical_safety_verified: bool
    completed: bool

    def __post_init__(self):
        strings(self.simulation_id, self.student_id, self.topic, self.vignette)
        require(isinstance(self.steps, tuple) and len(self.steps) >= 1, "'steps' must be a non-empty tuple")
        require(isinstance(self.clinical_safety_verified, bool), "'clinical_safety_verified' must be a boolean")
        require(isinstance(self.completed, bool), "'completed' must be a boolean")


@dataclass(frozen=True)
class StudyMilestone:
    """Targeted learning milestone in a personalized study curriculum."""

    milestone_id: str
    topic: str
    target_difficulty: PlatformDifficulty
    objective: str
    priority: str
    recommended_actions: tuple[str, ...]

    def __post_init__(self):
        strings(self.milestone_id, self.topic, self.objective, self.priority)
        require(
            isinstance(self.target_difficulty, PlatformDifficulty),
            f"'target_difficulty' must be PlatformDifficulty enum, got {self.target_difficulty}",
        )
        require(isinstance(self.recommended_actions, tuple), "'recommended_actions' must be a tuple")


@dataclass(frozen=True)
class PersonalizedStudyPlan:
    """Complete personalized study plan generated from student mastery metrics."""

    plan_id: str
    student_id: str
    created_at: float
    overall_learning_level: str
    milestones: tuple[StudyMilestone, ...]
    summary: str

    def __post_init__(self):
        strings(self.plan_id, self.student_id, self.overall_learning_level, self.summary)
        require(isinstance(self.created_at, (int, float)) and self.created_at >= 0, "'created_at' must be >= 0")
        require(isinstance(self.milestones, tuple), "'milestones' must be a tuple")


@dataclass(frozen=True)
class LearningLoopCycle:
    """Audit cycle tracking student progression before and after educational interventions."""

    cycle_id: str
    student_id: str
    topic: str
    initial_mastery: str
    interventions_applied: tuple[str, ...]
    resulting_mastery: str
    mastery_improved: bool
    timestamp: float

    def __post_init__(self):
        strings(self.cycle_id, self.student_id, self.topic, self.initial_mastery, self.resulting_mastery)
        require(isinstance(self.interventions_applied, tuple), "'interventions_applied' must be a tuple")
        require(isinstance(self.mastery_improved, bool), "'mastery_improved' must be a boolean")
        require(isinstance(self.timestamp, (int, float)) and self.timestamp >= 0, "'timestamp' must be >= 0")


@dataclass(frozen=True)
class PlatformResponse:
    """Unified response returned by MedicalPlabPlatformOrchestrator."""

    intent: PlatformIntent
    session_id: str
    payload: tuple[tuple[str, str], ...]  # Serialized key-value pairs for immutable payload storage
    explanation: str
    next_actions: tuple[str, ...]

    def __post_init__(self):
        strings(self.session_id, self.explanation)
        require(
            isinstance(self.intent, PlatformIntent),
            f"'intent' must be PlatformIntent enum, got {self.intent}",
        )
        require(isinstance(self.payload, tuple), "'payload' must be a tuple of key-value pairs")
        require(isinstance(self.next_actions, tuple), "'next_actions' must be a tuple")
