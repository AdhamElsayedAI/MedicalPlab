"""Response parser and builder for Stage-D Medical Tutor.
"""

from medicalplab.stage_b.models import (
    ContractError,
    exact_keys,
    require,
    strict_json,
)
from .models import (
    ConfidenceLevel,
    TutorCitation,
    TutorMode,
    TutorResponse,
    TutorSection,
)


REQUIRED_TUTOR_KEYS = [
    "answer",
    "sections",
    "citations",
    "confidence",
]


def parse_tutor_response(
    raw: str,
    query: str,
    mode: TutorMode,
) -> TutorResponse:
    """Parse raw JSON output from the tutor model into an immutable TutorResponse."""
    obj = strict_json(raw)

    require(isinstance(obj, dict), "Tutor output must be a JSON object")

    # Check required keys
    for k in REQUIRED_TUTOR_KEYS:
        require(k in obj, f"Missing required key in tutor response: '{k}'")

    # Parse sections
    require(isinstance(obj["sections"], list), "'sections' must be a list")
    require(len(obj["sections"]) >= 1, "At least one section must be provided")

    sections = []
    for idx, s in enumerate(obj["sections"], 1):
        require(isinstance(s, dict), f"Section {idx} must be a JSON object")
        exact_keys(s, ["heading", "content"])
        sections.append(
            TutorSection(
                heading=str(s["heading"]).strip(),
                content=str(s["content"]).strip(),
            )
        )

    # Parse citations
    require(isinstance(obj["citations"], list), "'citations' must be a list")
    require(len(obj["citations"]) >= 1, "At least one citation must be provided")

    citations = []
    for idx, c in enumerate(obj["citations"], 1):
        require(isinstance(c, dict), f"Citation {idx} must be a JSON object")
        exact_keys(c, ["ref", "quote"])
        citations.append(
            TutorCitation(
                ref=str(c["ref"]).strip(),
                quote=str(c["quote"]).strip(),
            )
        )

    # Parse confidence
    raw_confidence = str(obj["confidence"]).strip().lower()
    require(
        raw_confidence in {c.value for c in ConfidenceLevel},
        f"Invalid confidence level: '{raw_confidence}'",
    )
    confidence = ConfidenceLevel(raw_confidence)

    # Parse optional unsupported_aspects
    raw_unsupported = obj.get("unsupported_aspects", [])
    require(
        isinstance(raw_unsupported, list),
        "'unsupported_aspects' must be a list when provided",
    )
    unsupported_aspects = tuple(str(item).strip() for item in raw_unsupported if str(item).strip())

    return TutorResponse(
        query=query,
        mode=mode,
        answer=str(obj["answer"]).strip(),
        sections=tuple(sections),
        citations=tuple(citations),
        confidence=confidence,
        unsupported_aspects=unsupported_aspects,
    )
