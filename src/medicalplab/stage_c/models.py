"""Independent Stage-C data contracts for Evidence-Grounded Medical Question Generation.

Domain models are completely independent of Stage-B domain structures.
Only generic utilities (require, strict_json, exact_keys, normalize) are reused.
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


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    MCQ = "mcq"


VALID_OPTION_KEYS = ("A", "B", "C", "D")


@dataclass(frozen=True)
class Citation:
    ref: str
    quote: str

    def __post_init__(self):
        strings(self.ref, self.quote)


@dataclass(frozen=True)
class EvidenceBlock:
    ref: str
    document_id: str
    source: str
    heading: str
    section: str
    text: str
    block_type: str = "text"

    def __post_init__(self):
        strings(
            self.ref,
            self.document_id,
            self.source,
            self.text,
        )


@dataclass(frozen=True)
class GeneratedQuestion:
    question_id: str
    question_type: str
    question: str
    options: tuple[str, ...]
    correct_answer: str
    explanation: str
    difficulty: str
    topic: str
    citations: tuple[Citation, ...]

    def __post_init__(self):
        strings(
            self.question_id,
            self.question,
            self.explanation,
            self.topic,
        )

        require(
            self.question_type == QuestionType.MCQ.value,
            f"Invalid question type: {self.question_type}",
        )

        require(
            isinstance(self.options, tuple) and len(self.options) == 4,
            "MCQ must have exactly 4 options",
        )

        # Verify options are labeled A, B, C, D
        for expected_key, opt in zip(VALID_OPTION_KEYS, self.options):
            require(
                isinstance(opt, str) and opt.strip(),
                "Option text must be non-empty string",
            )
            clean_opt = opt.strip()
            require(
                clean_opt.startswith(f"{expected_key}.") or clean_opt.startswith(f"{expected_key})"),
                f"Option must start with '{expected_key}.' or '{expected_key})', got: {opt}",
            )

        require(
            self.correct_answer in VALID_OPTION_KEYS,
            f"correct_answer must be one of {VALID_OPTION_KEYS}, got: {self.correct_answer}",
        )

        require(
            self.difficulty in {d.value for d in DifficultyLevel},
            f"Invalid difficulty: {self.difficulty}",
        )

        require(
            isinstance(self.citations, tuple) and len(self.citations) >= 1,
            "Question requires at least one citation",
        )

        require(
            all(isinstance(c, Citation) for c in self.citations),
            "All citations must be Citation instances",
        )

    def get_option_text(self, key: str) -> str:
        """Return text of option for key ('A', 'B', 'C', 'D') without prefix."""
        require(key in VALID_OPTION_KEYS, f"Invalid option key: {key}")
        idx = VALID_OPTION_KEYS.index(key)
        raw = self.options[idx].strip()
        # strip 'A. ' or 'A) '
        if len(raw) >= 3 and raw[1] in {".", ")"} and raw[2] == " ":
            return raw[3:].strip()
        if len(raw) >= 2 and raw[1] in {".", ")"}:
            return raw[2:].strip()
        return raw

    def get_correct_option_text(self) -> str:
        """Return the text of the correct option."""
        return self.get_option_text(self.correct_answer)

    def get_distractor_texts(self) -> tuple[str, ...]:
        """Return texts of the 3 incorrect options (distractors)."""
        return tuple(
            self.get_option_text(k)
            for k in VALID_OPTION_KEYS
            if k != self.correct_answer
        )
