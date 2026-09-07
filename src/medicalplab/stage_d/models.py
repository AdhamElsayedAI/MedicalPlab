"""Independent Stage-D data contracts for Medical Tutor Reasoning Layer.

Domain models are completely independent of Stage-B and Stage-C structures.
Only generic utilities (require, strict_json, exact_keys, strings, ContractError, normalize) are reused.
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


class TutorMode(str, Enum):
    EXPLANATION = "explanation"
    TEACHING = "teaching"
    CASE_DISCUSSION = "case_discussion"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class TutorCitation:
    ref: str
    quote: str

    def __post_init__(self):
        strings(self.ref, self.quote)
        require(
            len(normalize(self.quote).split()) >= 3,
            f"Citation quote must be at least 3 words, got: '{self.quote}'",
        )


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
class TutorSection:
    heading: str
    content: str

    def __post_init__(self):
        strings(self.heading, self.content)


@dataclass(frozen=True)
class TutorRequest:
    query: str
    evidence: tuple[EvidenceBlock, ...]
    mode: TutorMode | None = None
    context: str | None = None

    def __post_init__(self):
        strings(self.query)
        require(
            isinstance(self.evidence, tuple) and len(self.evidence) >= 1,
            "TutorRequest requires at least one EvidenceBlock",
        )
        require(
            all(isinstance(b, EvidenceBlock) for b in self.evidence),
            "All items in evidence must be EvidenceBlock instances",
        )
        if self.mode is not None:
            require(
                isinstance(self.mode, TutorMode),
                f"mode must be TutorMode instance or None, got: {self.mode}",
            )
        if self.context is not None:
            require(
                isinstance(self.context, str) and self.context.strip(),
                "context must be a non-empty string when provided",
            )


@dataclass(frozen=True)
class TutorResponse:
    query: str
    mode: TutorMode
    answer: str
    sections: tuple[TutorSection, ...]
    citations: tuple[TutorCitation, ...]
    confidence: ConfidenceLevel
    unsupported_aspects: tuple[str, ...] = ()

    def __post_init__(self):
        strings(self.query, self.answer)

        require(
            isinstance(self.mode, TutorMode),
            f"mode must be a TutorMode enum, got: {self.mode}",
        )

        require(
            isinstance(self.confidence, ConfidenceLevel),
            f"confidence must be a ConfidenceLevel enum, got: {self.confidence}",
        )

        require(
            isinstance(self.sections, tuple) and len(self.sections) >= 1,
            "TutorResponse must contain at least one TutorSection",
        )
        require(
            all(isinstance(s, TutorSection) for s in self.sections),
            "All sections must be TutorSection instances",
        )

        require(
            isinstance(self.citations, tuple) and len(self.citations) >= 1,
            "TutorResponse must contain at least one TutorCitation",
        )
        require(
            all(isinstance(c, TutorCitation) for c in self.citations),
            "All citations must be TutorCitation instances",
        )

        require(
            isinstance(self.unsupported_aspects, tuple),
            "unsupported_aspects must be a tuple of strings",
        )
        require(
            all(isinstance(u, str) and u.strip() for u in self.unsupported_aspects),
            "All unsupported_aspects entries must be non-empty strings",
        )
