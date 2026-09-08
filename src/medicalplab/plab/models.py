"""Stable PLAB product-domain models.

These contracts intentionally use five answer choices to match the current
PLAB 1 single-best-answer format. They do not replace Stage-C; they provide the
product-facing contract that Stage-C output must eventually satisfy/adapt to.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


PLAB_OPTION_KEYS = ("A", "B", "C", "D", "E")


class PLABQuestionStatus(str, Enum):
    DRAFT = "draft"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class PLABChoice:
    id: str
    text: str

    def __post_init__(self) -> None:
        if self.id not in PLAB_OPTION_KEYS:
            raise ValueError(f"PLAB choice id must be one of {PLAB_OPTION_KEYS}")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("PLAB choice text must be a non-empty string")


@dataclass(frozen=True)
class PLABCitation:
    ref: str
    quote: str
    document_id: str

    def __post_init__(self) -> None:
        for value, label in (
            (self.ref, "ref"),
            (self.quote, "quote"),
            (self.document_id, "document_id"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"PLAB citation {label} must be a non-empty string")


@dataclass(frozen=True)
class PLABQuestion:
    question_id: str
    stem: str
    choices: tuple[PLABChoice, ...]
    correct_answer: str
    explanation: str
    specialty: str
    topic: str
    learning_objective: str
    difficulty: str
    citations: tuple[PLABCitation, ...]
    status: PLABQuestionStatus = PLABQuestionStatus.DRAFT
    schema_version: str = "plab-question-v1"

    def __post_init__(self) -> None:
        required_strings = {
            "question_id": self.question_id,
            "stem": self.stem,
            "explanation": self.explanation,
            "specialty": self.specialty,
            "topic": self.topic,
            "learning_objective": self.learning_objective,
            "difficulty": self.difficulty,
            "schema_version": self.schema_version,
        }
        for label, value in required_strings.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label} must be a non-empty string")

        if len(self.choices) != 5:
            raise ValueError("PLAB 1 question must contain exactly five choices")

        choice_ids = tuple(choice.id for choice in self.choices)
        if choice_ids != PLAB_OPTION_KEYS:
            raise ValueError(f"PLAB choices must be ordered exactly as {PLAB_OPTION_KEYS}")

        if len({choice.text.strip().casefold() for choice in self.choices}) != 5:
            raise ValueError("PLAB choice texts must be unique")

        if self.correct_answer not in PLAB_OPTION_KEYS:
            raise ValueError(f"correct_answer must be one of {PLAB_OPTION_KEYS}")

        if self.difficulty not in {"easy", "medium", "hard"}:
            raise ValueError("difficulty must be easy, medium, or hard")

        if not self.citations:
            raise ValueError("PLAB question requires at least one evidence citation")

    def correct_choice(self) -> PLABChoice:
        return next(choice for choice in self.choices if choice.id == self.correct_answer)
