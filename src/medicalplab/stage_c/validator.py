"""Validation layer for Stage-C generated questions.

Enforces evidence grounding, citation provenance, distractor validity,
explanation grounding, and difficulty consistency rules.
"""

import re
from typing import Sequence

from medicalplab.stage_b.models import ContractError, require
from medicalplab.stage_b.evidence_policy import normalize
from .models import (
    DifficultyLevel,
    EvidenceBlock,
    GeneratedQuestion,
    VALID_OPTION_KEYS,
)


COMMON_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "can", "could",
    "should", "would", "may", "might", "must", "that", "which", "who",
    "whom", "this", "these", "those", "it", "its", "as", "into", "than",
    "using", "used", "use", "make", "made", "such", "also", "well", "like",
    "more", "most", "only", "both", "either", "neither", "each", "every",
    "other", "another", "some", "any", "all", "same", "different", "about",
    "above", "across", "after", "against", "along", "among", "around",
    "before", "behind", "below", "beneath", "beside", "between", "beyond",
    "during", "inside", "near", "outside", "over", "through", "throughout",
    "under", "until", "upon", "within", "without", "how", "what", "when",
    "where", "why", "which",
}


def _extract_content_tokens(text: str) -> set[str]:
    """Extract normalized alphanumeric words of length >= 3, excluding stopwords."""
    words = re.findall(r"\b[a-zA-Z0-9-]+\b", normalize(text))
    return {w for w in words if len(w) >= 3 and w not in COMMON_STOPWORDS}


def validate_citation_provenance(
    question: GeneratedQuestion,
    packet: Sequence[EvidenceBlock],
) -> None:
    """Validate that every citation references a valid block and quotes it accurately."""
    require(len(question.citations) >= 1, "Question must have at least one citation")

    blocks = {b.ref: b for b in packet}

    for c in question.citations:
        require(
            c.ref in blocks,
            f"Citation ref '{c.ref}' not found in supplied evidence packet",
        )
        block_text_norm = normalize(blocks[c.ref].text)
        quote_norm = normalize(c.quote)

        require(
            len(quote_norm.split()) >= 3,
            f"Citation quote too short: '{c.quote}'",
        )

        require(
            quote_norm in block_text_norm,
            f"Citation quote not found in cited block '{c.ref}': '{c.quote}'",
        )


def validate_options_integrity(question: GeneratedQuestion) -> None:
    """Ensure all options are distinct, non-empty, and correctly labeled."""
    require(len(question.options) == 4, "Question must have exactly 4 options")
    require(
        question.correct_answer in VALID_OPTION_KEYS,
        f"Correct answer pointer '{question.correct_answer}' invalid",
    )

    option_texts = [normalize(question.get_option_text(k)) for k in VALID_OPTION_KEYS]

    # All options must be mutually distinct
    require(
        len(set(option_texts)) == 4,
        "All 4 MCQ options must have distinct text",
    )

    # Correct answer text must be non-empty
    correct_text = question.get_correct_option_text().strip()
    require(len(correct_text.split()) >= 1, "Correct answer text cannot be empty")


def validate_option_grounding(
    question: GeneratedQuestion,
    packet: Sequence[EvidenceBlock],
) -> None:
    """Verify that the correct answer is grounded in evidence, and distractors are not accidentally true."""
    blocks = {b.ref: b for b in packet}
    cited_text = " ".join(normalize(blocks[c.ref].text) for c in question.citations)
    cited_quotes = " ".join(normalize(c.quote) for c in question.citations)

    correct_text = question.get_correct_option_text()
    correct_tokens = _extract_content_tokens(correct_text)

    # 1. Correct answer must share key semantic tokens with cited evidence quote
    quote_tokens = _extract_content_tokens(cited_quotes)
    evidence_tokens = _extract_content_tokens(cited_text)

    overlap_with_quote = correct_tokens.intersection(quote_tokens)
    overlap_with_evidence = correct_tokens.intersection(evidence_tokens)
    overlap = overlap_with_quote or overlap_with_evidence

    required_overlap = min(2, len(correct_tokens)) if correct_tokens else 1

    require(
        len(overlap) >= required_overlap,
        f"Correct answer '{correct_text}' is not sufficiently grounded in cited evidence (overlap: {overlap})",
    )

    # 2. Distractor Guard: Distractors must NOT be verbatim copies of sentences from the evidence
    for key in VALID_OPTION_KEYS:
        if key == question.correct_answer:
            continue
        distractor = question.get_option_text(key)
        distractor_norm = normalize(distractor)

        # A distractor of 5+ words should not be a verbatim substring of cited evidence
        if len(distractor_norm.split()) >= 5:
            for b in packet:
                require(
                    distractor_norm not in normalize(b.text),
                    f"Distractor ({key}) '{distractor}' is a verbatim quote from evidence block '{b.ref}', making it unintentionally true",
                )


def validate_explanation_grounding(
    question: GeneratedQuestion,
    packet: Sequence[EvidenceBlock],
) -> None:
    """Ensure explanation references the evidence and explains why the answer is correct."""
    explanation_norm = normalize(question.explanation)
    require(
        len(explanation_norm.split()) >= 4,
        "Explanation is too brief",
    )

    blocks = {b.ref: b for b in packet}
    cited_text = " ".join(normalize(blocks[c.ref].text) for c in question.citations)
    cited_tokens = _extract_content_tokens(cited_text)
    explanation_tokens = _extract_content_tokens(question.explanation)

    # Explanation must be anchored in the cited evidence vocabulary
    overlap = explanation_tokens.intersection(cited_tokens)
    require(
        bool(overlap),
        "Explanation has no content overlap with cited evidence",
    )


def validate_difficulty_consistency(question: GeneratedQuestion) -> None:
    """Check difficulty rating consistency."""
    require(
        question.difficulty in {d.value for d in DifficultyLevel},
        f"Invalid difficulty: {question.difficulty}",
    )

    # If question has multiple citations across different evidence blocks, it is at least 'medium' or 'hard'
    distinct_refs = {c.ref for c in question.citations}
    if len(distinct_refs) > 2 and question.difficulty == DifficultyLevel.EASY.value:
        raise ContractError(
            "Question synthesizing more than 2 evidence blocks cannot be classified as 'easy'",
        )


def validate_question(
    question: GeneratedQuestion,
    packet: Sequence[EvidenceBlock],
) -> None:
    """Complete validation pipeline for a Stage-C generated question."""
    validate_citation_provenance(question, packet)
    validate_options_integrity(question)
    validate_option_grounding(question, packet)
    validate_explanation_grounding(question, packet)
    validate_difficulty_consistency(question)


def is_valid_question(
    question: GeneratedQuestion,
    packet: Sequence[EvidenceBlock],
) -> tuple[bool, list[str]]:
    """Safe validator that returns (is_valid, list_of_errors) without raising."""
    errors = []
    try:
        validate_question(question, packet)
    except ContractError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"{type(e).__name__}: {e}")

    return len(errors) == 0, errors
