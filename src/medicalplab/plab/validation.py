"""Validation gates for product-facing PLAB questions."""

from __future__ import annotations

from collections.abc import Sequence

from .models import PLABQuestion


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def validate_plab_question(
    question: PLABQuestion,
    evidence_texts: Sequence[str] | None = None,
) -> list[str]:
    """Return validation errors; an empty list means the question passes v1 gates.

    This layer intentionally avoids pretending to perform full clinical review.
    It checks structural integrity and evidence-anchor presence. Human/LLM
    clinical-review scoring is a separate later gate.
    """
    errors: list[str] = []

    if len(question.stem.split()) < 8:
        errors.append("stem_too_short")

    if len(question.explanation.split()) < 8:
        errors.append("explanation_too_short")

    correct_text = _normalize(question.correct_choice().text)
    distractor_texts = [
        _normalize(choice.text)
        for choice in question.choices
        if choice.id != question.correct_answer
    ]

    if correct_text in distractor_texts:
        errors.append("correct_answer_duplicate")

    if len(set(distractor_texts)) != 4:
        errors.append("duplicate_distractors")

    if evidence_texts is not None:
        corpus = _normalize(" ".join(str(text) for text in evidence_texts))
        for citation in question.citations:
            if _normalize(citation.quote) not in corpus:
                errors.append(f"citation_quote_not_found:{citation.ref}")

    return errors
