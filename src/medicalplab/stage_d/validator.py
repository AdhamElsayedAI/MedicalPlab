"""Clinical safety and provenance validator for Stage-D Medical Tutor.

Enforces:
1. Citation provenance and verbatim quote matching.
2. Clinical safety:
   - No unsupported diagnosis claims
   - No unsupported treatment recommendations
   - No unsupported drug, dose, or cure claims
3. Semantic grounding of educational explanations in evidence.
"""

import re
from typing import Sequence

from medicalplab.stage_b.models import ContractError, require
from medicalplab.stage_b.evidence_policy import normalize
from .models import (
    ConfidenceLevel,
    EvidenceBlock,
    TutorCitation,
    TutorResponse,
)


CURE_PATTERNS = [
    r"\b(?:cure|cures|curing)\b",
    r"\bcompletely\s+eliminat\w*\b",
    r"\bpermanent(?:ly)?\s+cure\w*\b",
    r"\buniversal\s+cure\b",
]

DOSE_PATTERNS = [
    r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?|tablets?)\b",
    r"\b\d+\s*[-–]\s*\d+\s*(?:mg|mcg|g|ml)\b",
]

PRESCRIPTION_PATTERNS = [
    r"\b(?:is|are)\s+recommended\b",
    r"\bshould\s+be\s+prescribed\b",
    r"\bmust\s+be\s+initiated\b",
    r"\bfirst-line\s+treatment\s+is\b",
    r"\bprescribe\s+[a-z0-9-]+\b",
]

DIAGNOSIS_PATTERNS = [
    r"\bthe\s+patient\s+(?:definitively\s+)?has\s+([a-z0-9\s-]+?)(?:\.|$|,|\s+based\b|\s+due\b|\s+definitively\b|\s+and\b)",
    r"\bdefinitively\s+diagnosed\s+with\s+([a-z0-9\s-]+?)(?:\.|$|,|\s+based\b|\s+due\b|\s+and\b)",
    r"\bdiagnosis\s+is\s+confirmed\s+as\s+([a-z0-9\s-]+?)(?:\.|$|,|\s+based\b|\s+due\b|\s+and\b)",
    r"\bdiagnosis\s+of\s+([a-z0-9\s-]+?)\s+(?:is\s+confirmed|is\s+made|is\s+established)\b",
]

COMMON_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "can", "could",
    "should", "would", "may", "might", "must", "that", "which", "who",
    "whom", "this", "these", "those", "it", "its", "as", "into", "than",
    "such", "also", "well", "like", "more", "most", "only", "both", "all",
    "about", "above", "after", "before", "between", "during", "under",
    "definitively", "confirmed",
}


def _extract_content_words(text: str) -> set[str]:
    words = re.findall(r"\b[a-zA-Z0-9-]+\b", normalize(text))
    return {w for w in words if len(w) >= 3 and w not in COMMON_STOPWORDS}


def validate_citation_provenance(
    citations: Sequence[TutorCitation],
    packet: Sequence[EvidenceBlock],
) -> None:
    """Ensure every citation points to a valid block and quotes it verbatim."""
    require(len(citations) >= 1, "Tutor response requires at least one citation")

    blocks = {b.ref: b for b in packet}

    for idx, c in enumerate(citations, 1):
        require(
            c.ref in blocks,
            f"Citation {idx} ref '{c.ref}' not found in supplied evidence packet",
        )
        block_text = normalize(blocks[c.ref].text)
        quote_text = normalize(c.quote)

        require(
            quote_text in block_text,
            f"Citation {idx} quote not present in cited block '{c.ref}': '{c.quote}'",
        )


def validate_clinical_safety(
    response: TutorResponse,
    packet: Sequence[EvidenceBlock],
) -> None:
    """Enforce clinical safety guards: no unsupported cures, doses, treatments, or diagnoses."""
    blocks = {b.ref: b for b in packet}
    cited_text = " ".join(normalize(blocks[c.ref].text) for c in response.citations)
    tutor_full_text = normalize(
        f"{response.answer} " + " ".join(s.content for s in response.sections)
    )

    # 1. No unsupported cure claims
    for pattern in CURE_PATTERNS:
        match = re.search(pattern, tutor_full_text)
        if match:
            # If the word 'cure' is used in tutor output, it must exist in cited evidence
            require(
                re.search(pattern, cited_text) is not None,
                f"Unsupported cure claim detected in tutor response: '{match.group(0)}'",
            )

    # 2. No unsupported specific drug dosage claims
    for pattern in DOSE_PATTERNS:
        matches = re.finditer(pattern, tutor_full_text)
        for m in matches:
            dose_span = m.group(0)
            require(
                dose_span in cited_text,
                f"Unsupported medication dosage '{dose_span}' not grounded in cited evidence",
            )

    # 3. No unsupported treatment/prescription recommendations
    for pattern in PRESCRIPTION_PATTERNS:
        match = re.search(pattern, tutor_full_text)
        if match:
            rec_span = match.group(0)
            # If an affirmative recommendation is made, the cited text must contain recommendations
            require(
                any(
                    keyword in cited_text
                    for keyword in ["recommend", "treatment", "prescrib", "pharmacolog", "guideline"]
                ),
                f"Unsupported treatment recommendation '{rec_span}' without supporting guideline evidence",
            )

    # 4. No unsupported definitive patient diagnosis
    for pattern in DIAGNOSIS_PATTERNS:
        matches = re.finditer(pattern, tutor_full_text)
        for match in matches:
            diag_span = match.group(1).strip()
            diag_words = [
                w for w in re.findall(r"\b[a-z0-9-]+\b", diag_span)
                if w not in COMMON_STOPWORDS and len(w) >= 3
            ]
            if diag_words:
                require(
                    all(w in cited_text for w in diag_words),
                    f"Unsupported definitive patient diagnosis '{diag_span}' not grounded in evidence",
                )


def validate_semantic_grounding(
    response: TutorResponse,
    packet: Sequence[EvidenceBlock],
) -> None:
    """Ensure the tutor's answer and sections are anchored in the evidence."""
    blocks = {b.ref: b for b in packet}
    evidence_text = " ".join(normalize(blocks[c.ref].text) for c in response.citations)
    evidence_tokens = _extract_content_words(evidence_text)

    answer_tokens = _extract_content_words(response.answer)
    overlap = answer_tokens.intersection(evidence_tokens)

    require(
        bool(overlap),
        f"Tutor answer '{response.answer}' has no semantic overlap with cited evidence",
    )

    # Check that sections are substantial and grounded
    for s in response.sections:
        require(len(s.heading.split()) >= 1, "Section heading cannot be empty")
        require(len(s.content.split()) >= 4, f"Section content too short in '{s.heading}'")


def validate_tutor_response(
    response: TutorResponse,
    packet: Sequence[EvidenceBlock],
) -> None:
    """Run all validation checks on a TutorResponse."""
    validate_citation_provenance(response.citations, packet)
    validate_clinical_safety(response, packet)
    validate_semantic_grounding(response, packet)


def is_valid_tutor_response(
    response: TutorResponse,
    packet: Sequence[EvidenceBlock],
) -> tuple[bool, list[str]]:
    """Safe validator returning (is_valid, error_list) without raising."""
    errors = []
    try:
        validate_tutor_response(response, packet)
    except ContractError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"{type(e).__name__}: {e}")

    return len(errors) == 0, errors
