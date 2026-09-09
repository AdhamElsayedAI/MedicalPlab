from dataclasses import replace
import json
from pathlib import Path

import pytest

from medicalplab.plab.governance import (
    REVIEW_DIMENSIONS,
    ReviewDecision,
    ReviewFinding,
    ReviewRecord,
    ReviewStatus,
    create_revision,
    evaluate_golden_promotion,
    question_content_hash,
)
from medicalplab.plab.models import PLABCitation, PLABChoice, PLABQuestion, PLABQuestionStatus


def payload():
    return {
        "question_id": "PLAB-TEST-0001",
        "stem": "A patient presents with enough clinical detail for a valid single best answer question.",
        "choices": [{"id": key, "text": f"Option {key}"} for key in "ABCDE"],
        "correct_answer": "A",
        "explanation": "The cited evidence directly supports option A as the single best answer.",
        "specialty": "Cardiology",
        "topic": "Test topic",
        "learning_objective": "Use evidence to choose the best answer.",
        "difficulty": "medium",
        "citations": [{"ref": "DOC:B1", "document_id": "DOC", "quote": "direct evidence"}],
    }


def question(data):
    return PLABQuestion(
        question_id=data["question_id"],
        stem=data["stem"],
        choices=tuple(PLABChoice(**choice) for choice in data["choices"]),
        correct_answer=data["correct_answer"],
        explanation=data["explanation"],
        specialty=data["specialty"],
        topic=data["topic"],
        learning_objective=data["learning_objective"],
        difficulty=data["difficulty"],
        citations=tuple(PLABCitation(**citation) for citation in data["citations"]),
        status=PLABQuestionStatus.APPROVED,
    )


def approved_review(data):
    record = ReviewRecord(
        question_id=data["question_id"],
        question_version=1,
        question_content_sha256=question_content_hash(data),
    ).start("clinician-1", "Clinical Reviewer")
    return record.decide(
        ReviewDecision.APPROVED,
        {dimension: ReviewFinding.PASS for dimension in REVIEW_DIMENSIONS},
    )


def test_review_requires_real_identity_and_complete_findings():
    data = payload()
    record = ReviewRecord(data["question_id"], 1, question_content_hash(data))
    with pytest.raises(ValueError, match="reviewer_missing"):
        record.start(" ")
    in_review = record.start("clinician-1")
    with pytest.raises(ValueError, match="review_findings_incomplete"):
        in_review.decide(ReviewDecision.APPROVED, {})


def test_approval_requires_every_dimension_to_pass():
    data = payload()
    record = ReviewRecord(data["question_id"], 1, question_content_hash(data)).start("clinician-1")
    findings = {dimension: ReviewFinding.PASS for dimension in REVIEW_DIMENSIONS}
    findings["evidence_adequacy"] = ReviewFinding.EDIT
    with pytest.raises(ValueError, match="approval_requires_all_dimensions_pass"):
        record.decide(ReviewDecision.APPROVED, findings)


def test_golden_promotion_passes_only_after_complete_unchanged_approval():
    data = payload()
    result = evaluate_golden_promotion(
        question(data), data, 1, approved_review(data), ["Direct evidence is present."], True, True
    )
    assert result.promoted is True
    assert result.error_codes == ()


def test_golden_promotion_fails_closed_without_human_review():
    data = payload()
    record = ReviewRecord(data["question_id"], 1, question_content_hash(data))
    result = evaluate_golden_promotion(question(data), data, 1, record, ["direct evidence"], True, True)
    assert result.promoted is False
    assert {
        "human_review_missing",
        "review_decision_not_approved",
        "reviewer_missing",
        "review_timestamp_missing",
        "uk_alignment_unresolved",
    }.issubset(result.error_codes)


def test_change_after_approval_invalidates_promotion():
    data = payload()
    changed = {**data, "explanation": data["explanation"] + " Clinically meaningful edit."}
    result = evaluate_golden_promotion(
        question(changed), changed, 1, approved_review(data), ["direct evidence"], True, True
    )
    assert result.promoted is False
    assert "question_changed_after_review" in result.error_codes


def test_revision_is_auditable_and_requires_re_review():
    data = payload()
    changed = {**data, "stem": data["stem"] + " Additional clinical finding."}
    revision = create_revision(data, changed, 1, "Resolve ambiguity", "editor-1", "Please clarify timing")
    assert revision.version == 2
    assert revision.parent_version == 1
    assert revision.changed_fields == ("stem",)
    review = replace(
        approved_review(data),
        question_version=revision.version,
        question_content_sha256=revision.content_sha256,
        review_status=ReviewStatus.REVISED,
        final_decision=None,
        reviewed_at=None,
    )
    assert review.start("clinician-2").review_status is ReviewStatus.RE_REVIEW


def test_real_batch_queue_contains_no_fabricated_human_review():
    root = Path(__file__).resolve().parents[2]
    batch = json.loads((root / "Data/questions/cardiorespiratory_batch_1.json").read_text(encoding="utf-8"))
    queue = json.loads((root / "Data/questions/cardiorespiratory_batch_1_review_queue.json").read_text(encoding="utf-8"))
    questions = {question["question_id"]: question for question in batch["questions"]}
    assert queue["total_queued"] == 36
    assert queue["golden_count"] == 0
    for item in queue["queue"]:
        assert item["review_status"] == "pending"
        assert item["reviewer_id"] is None
        assert item["reviewed_at"] is None
        assert item["final_decision"] is None
        assert item["golden_status"] is False
        assert item["question_version"] == 1
        assert item["question_content_sha256"] == question_content_hash(questions[item["question_id"]])
