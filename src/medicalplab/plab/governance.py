"""Fail-closed PLAB clinical review, revision, and Golden promotion workflow."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping, Sequence

from .models import PLAB_OPTION_KEYS, PLABQuestion
from .validation import validate_plab_question


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    REVISE = "revise"
    REVISED = "revised"
    RE_REVIEW = "re_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewFinding(str, Enum):
    PASS = "pass"
    EDIT = "edit"
    FAIL = "fail"


class ReviewDecision(str, Enum):
    APPROVED = "APPROVED"
    REVISE = "REVISE"
    REJECT = "REJECT"


REVIEW_DIMENSIONS = (
    "clinical_correctness",
    "sba_unambiguity",
    "uk_alignment",
    "evidence_adequacy",
    "distractor_quality",
    "explanation_quality",
)

CLINICALLY_MEANINGFUL_FIELDS = (
    "stem",
    "choices",
    "correct_answer",
    "explanation",
    "topic",
    "learning_objective",
    "difficulty",
    "citations",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def question_content_hash(question: Mapping[str, object]) -> str:
    payload = {field: question.get(field) for field in CLINICALLY_MEANINGFUL_FIELDS}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReviewRecord:
    question_id: str
    question_version: int
    question_content_sha256: str
    review_status: ReviewStatus = ReviewStatus.PENDING
    clinical_correctness: ReviewFinding | None = None
    sba_unambiguity: ReviewFinding | None = None
    uk_alignment: ReviewFinding | None = None
    evidence_adequacy: ReviewFinding | None = None
    distractor_quality: ReviewFinding | None = None
    explanation_quality: ReviewFinding | None = None
    reviewer_id: str | None = None
    reviewer_name: str | None = None
    review_started_at: str | None = None
    reviewed_at: str | None = None
    review_comments: str | None = None
    revision_notes: str | None = None
    final_decision: ReviewDecision | None = None
    golden_status: bool = False

    def start(self, reviewer_id: str, reviewer_name: str | None = None) -> "ReviewRecord":
        if self.review_status not in {
            ReviewStatus.PENDING,
            ReviewStatus.REVISED,
            ReviewStatus.RE_REVIEW,
        }:
            raise ValueError("invalid_review_transition")
        if not reviewer_id.strip():
            raise ValueError("reviewer_missing")
        status = (
            ReviewStatus.RE_REVIEW
            if self.review_status in {ReviewStatus.REVISED, ReviewStatus.RE_REVIEW}
            else ReviewStatus.IN_REVIEW
        )
        return replace(
            self,
            review_status=status,
            reviewer_id=reviewer_id.strip(),
            reviewer_name=reviewer_name.strip() if reviewer_name else None,
            review_started_at=utc_now(),
            reviewed_at=None,
            final_decision=None,
            golden_status=False,
        )

    def decide(
        self,
        decision: ReviewDecision,
        findings: Mapping[str, ReviewFinding],
        comments: str | None = None,
        revision_notes: str | None = None,
    ) -> "ReviewRecord":
        if self.review_status not in {ReviewStatus.IN_REVIEW, ReviewStatus.RE_REVIEW}:
            raise ValueError("review_not_in_progress")
        if not self.reviewer_id:
            raise ValueError("reviewer_missing")
        if set(findings) != set(REVIEW_DIMENSIONS):
            raise ValueError("review_findings_incomplete")
        if decision is ReviewDecision.APPROVED and any(
            finding is not ReviewFinding.PASS for finding in findings.values()
        ):
            raise ValueError("approval_requires_all_dimensions_pass")
        if decision is ReviewDecision.REVISE and not (revision_notes or "").strip():
            raise ValueError("revision_notes_missing")

        status = {
            ReviewDecision.APPROVED: ReviewStatus.APPROVED,
            ReviewDecision.REVISE: ReviewStatus.REVISE,
            ReviewDecision.REJECT: ReviewStatus.REJECTED,
        }[decision]
        return replace(
            self,
            review_status=status,
            reviewed_at=utc_now(),
            review_comments=comments.strip() if comments else None,
            revision_notes=revision_notes.strip() if revision_notes else None,
            final_decision=decision,
            golden_status=False,
            **findings,
        )


@dataclass(frozen=True)
class QuestionRevision:
    question_id: str
    version: int
    content_sha256: str
    parent_version: int | None
    revision_reason: str | None
    changed_fields: tuple[str, ...]
    reviewer_feedback: str | None
    editor_id: str | None
    created_at: str


def create_revision(
    previous: Mapping[str, object],
    updated: Mapping[str, object],
    previous_version: int,
    revision_reason: str,
    editor_id: str,
    reviewer_feedback: str | None = None,
) -> QuestionRevision:
    changed = tuple(
        field for field in CLINICALLY_MEANINGFUL_FIELDS if previous.get(field) != updated.get(field)
    )
    if not changed:
        raise ValueError("no_clinically_meaningful_change")
    if not revision_reason.strip():
        raise ValueError("revision_reason_missing")
    if not editor_id.strip():
        raise ValueError("editor_missing")
    return QuestionRevision(
        question_id=str(updated["question_id"]),
        version=previous_version + 1,
        content_sha256=question_content_hash(updated),
        parent_version=previous_version,
        revision_reason=revision_reason.strip(),
        changed_fields=changed,
        reviewer_feedback=reviewer_feedback.strip() if reviewer_feedback else None,
        editor_id=editor_id.strip(),
        created_at=utc_now(),
    )


@dataclass(frozen=True)
class PromotionResult:
    promoted: bool
    error_codes: tuple[str, ...]


def evaluate_golden_promotion(
    question: PLABQuestion,
    question_payload: Mapping[str, object],
    question_version: int,
    review: ReviewRecord,
    evidence_texts: Sequence[str],
    citation_resolves: bool,
    uk_reconciliation_acceptable: bool,
) -> PromotionResult:
    errors: list[str] = []
    validation_errors = validate_plab_question(question, evidence_texts)
    if validation_errors or tuple(choice.id for choice in question.choices) != PLAB_OPTION_KEYS:
        errors.append("automated_validation_failed")
    if not citation_resolves:
        errors.append("citation_unresolved")
    if any(error.startswith("citation_quote_not_found") for error in validation_errors):
        errors.append("evidence_validation_failed")
    if not uk_reconciliation_acceptable or review.uk_alignment is not ReviewFinding.PASS:
        errors.append("uk_alignment_unresolved")
    if review.review_status is not ReviewStatus.APPROVED:
        errors.append("human_review_missing")
    if review.final_decision is not ReviewDecision.APPROVED:
        errors.append("review_decision_not_approved")
    if not review.reviewer_id:
        errors.append("reviewer_missing")
    if not review.reviewed_at:
        errors.append("review_timestamp_missing")
    if review.question_version != question_version:
        errors.append("question_version_mismatch")
    if review.question_content_sha256 != question_content_hash(question_payload):
        errors.append("question_changed_after_review")
    if any(getattr(review, dimension) is not ReviewFinding.PASS for dimension in REVIEW_DIMENSIONS):
        errors.append("review_findings_incomplete")
    return PromotionResult(promoted=not errors, error_codes=tuple(dict.fromkeys(errors)))
