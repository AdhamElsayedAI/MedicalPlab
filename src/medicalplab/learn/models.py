"""Domain models and contracts for Course Learning."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class CourseTrack(str, Enum):
    CARDIORESPIRATORY = "cardiorespiratory"
    URINARY_RENAL = "urinary_renal"
    ANATOMY = "anatomy"
    PHYSIOLOGY = "physiology"
    SURGERY = "surgery"


class LearningIntent(str, Enum):
    EXPLAIN = "explain"
    QUESTION = "question"
    COMPARE = "compare"
    CHECK = "check"


class GroundingStatus(str, Enum):
    GROUNDED = "GROUNDED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNSUPPORTED = "UNSUPPORTED"
    DATA_SOURCE_MISSING = "DATA_SOURCE_MISSING"


@dataclass(frozen=True)
class StudentCitation:
    document_id: str
    title: str
    section: str | None
    reference: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LearningCheckChoice:
    id: str  # "A", "B", "C", "D", "E"
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LearningCheck:
    stem: str
    choices: tuple[LearningCheckChoice, ...]
    correct_answer: str
    explanation: str
    learning_objective: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "stem": self.stem,
            "choices": [c.to_dict() for c in self.choices],
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "learning_objective": self.learning_objective,
        }


@dataclass(frozen=True)
class CourseQueryRequest:
    course_id: str
    query: str
    intent: str | None = None


@dataclass(frozen=True)
class CourseQueryResponse:
    course_id: str
    query: str
    grounding_status: GroundingStatus
    answer: str | None
    explanation: str | None
    citations: tuple[StudentCitation, ...]
    evidence_sufficiency_score: float | None
    evidence_sufficiency_state: str  # "SUFFICIENT", "INSUFFICIENT", "NO_EVIDENCE"
    learning_check: dict[str, Any] | None
    trace_id: str
    warning: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "course_id": self.course_id,
            "query": self.query,
            "grounding_status": self.grounding_status.value,
            "answer": self.answer,
            "explanation": self.explanation,
            "citations": [c.to_dict() for c in self.citations],
            "evidence_sufficiency_score": self.evidence_sufficiency_score,
            "evidence_sufficiency_state": self.evidence_sufficiency_state,
            "learning_check": self.learning_check,
            "trace_id": self.trace_id,
            "warning": self.warning,
        }
