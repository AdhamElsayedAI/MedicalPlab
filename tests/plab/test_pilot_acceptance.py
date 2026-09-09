"""End-to-end acceptance tests for the PLAB pilot product boundary."""

from __future__ import annotations

import importlib
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from medicalplab.plab.governance import question_content_hash
from medicalplab.plab.pilot import PLABPilotService
from medicalplab.stage_g.product_api import configure_plab_service, router


def question_payload():
    return {
        "question_id": "PLAB-TEST-0001",
        "stem": "A patient presents with enough clinical detail for a valid single best answer question.",
        "choices": [{"id": key, "text": f"Option {key}"} for key in "ABCDE"],
        "correct_answer": "A",
        "explanation": "The cited direct evidence supports option A as the single best answer.",
        "specialty": "Cardiology",
        "topic": "Test topic",
        "learning_objective": "Use evidence to choose the best answer.",
        "difficulty": "medium",
        "citations": [{"ref": "DOC:B1", "document_id": "DOC", "quote": "direct evidence"}],
        "status": "needs_review",
        "schema_version": "plab-question-v1",
    }


def review_payload(question, approved=False):
    payload = {
        "question_id": question["question_id"],
        "question_version": 1,
        "question_content_sha256": question_content_hash(question),
        "review_status": "pending",
        "reviewer_id": None,
        "reviewer_name": None,
        "review_started_at": None,
        "reviewed_at": None,
        "review_comments": None,
        "revision_notes": None,
        "final_decision": None,
        "golden_status": False,
        "risk_level": "HIGH",
        "automated_schema_valid": True,
        "automated_evidence_valid": True,
        "automated_uk_check": "CURATED_RULE_COMPARED_PENDING_CLINICAL_SIGN_OFF",
    }
    for dimension in (
        "clinical_correctness",
        "sba_unambiguity",
        "uk_alignment",
        "evidence_adequacy",
        "distractor_quality",
        "explanation_quality",
    ):
        payload[dimension] = None
    if approved:
        payload.update(
            review_status="approved",
            reviewer_id="TEST-CLINICIAN",
            reviewer_name="Synthetic acceptance fixture",
            review_started_at="2026-01-01T00:00:00+00:00",
            reviewed_at="2026-01-01T00:01:00+00:00",
            final_decision="APPROVED",
            golden_status=True,
        )
        for dimension in (
            "clinical_correctness",
            "sba_unambiguity",
            "uk_alignment",
            "evidence_adequacy",
            "distractor_quality",
            "explanation_quality",
        ):
            payload[dimension] = "pass"
    return payload


def service(approved=False, preview=False, evidence=True):
    question = question_payload()
    chunks = {"DOC:B1": {"document_id": "DOC", "text": "This direct evidence is present."}} if evidence else {}
    return PLABPilotService(
        [question], [review_payload(question, approved)], chunks,
        "test-batch-v1", preview_qa=preview,
    )


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as test_client:
        yield test_client
    configure_plab_service(None)


def test_health_and_runtime_identification(monkeypatch):
    monkeypatch.setenv("MEDICALPLAB_RUNTIME_MODE", "pilot")
    sys.modules.pop("production_main", None)
    production = importlib.import_module("production_main")
    response = TestClient(production.app).get("/health")
    assert response.status_code == 200
    assert response.json()["runtime_mode"] == "pilot"


def test_approved_question_fetch_hides_answers_and_preserves_version(client):
    configure_plab_service(service(approved=True))
    response = client.get("/api/v1/plab/questions/PLAB-TEST-0001")
    assert response.status_code == 200
    body = response.json()
    assert body["question_version"] == 1
    assert body["content_mode"] == "GOLDEN"
    assert "correct_answer" not in body
    assert "explanation" not in body
    assert all("isCorrect" not in option for option in body["options"])


def test_pending_question_is_blocked_from_normal_student_flow(client):
    configure_plab_service(service())
    response = client.get("/api/v1/plab/questions/PLAB-TEST-0001")
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "QUESTION_NOT_AVAILABLE"


def test_preview_mode_is_explicit_and_never_looks_golden(client):
    configure_plab_service(service(preview=True))
    body = client.get("/api/v1/plab/questions/PLAB-TEST-0001").json()
    assert body["content_mode"] == "PREVIEW_QA"
    assert "Not clinically approved" in body["warning"]


def test_correct_and_wrong_evaluation_reveal_explanation_only_after_submission(client):
    configure_plab_service(service(approved=True))
    headers = {"X-User-Id": "student-1"}
    correct = client.post(
        "/api/v1/plab/evaluate", headers=headers,
        json={"question_id": "PLAB-TEST-0001", "selected_option": "A", "idempotency_key": "correct-0001"},
    )
    wrong = client.post(
        "/api/v1/plab/evaluate", headers=headers,
        json={"question_id": "PLAB-TEST-0001", "selected_option": "B", "idempotency_key": "wrong-00001"},
    )
    assert correct.json()["correct"] is True
    assert wrong.json()["correct"] is False
    assert correct.json()["correct_answer"] == "A"
    assert "explanation" in correct.json()


def test_attempt_retry_is_idempotent_and_progress_is_truthful(client):
    configured = service(approved=True)
    configure_plab_service(configured)
    headers = {"X-User-Id": "student-1"}
    request = {"question_id": "PLAB-TEST-0001", "selected_option": "A", "idempotency_key": "retry-key-0001"}
    first = client.post("/api/v1/plab/evaluate", headers=headers, json=request)
    second = client.post("/api/v1/plab/evaluate", headers=headers, json=request)
    assert first.json()["attempt_id"] == second.json()["attempt_id"]
    assert len(configured.attempts) == 1
    progress = client.get("/api/v1/plab/progress", headers=headers).json()
    assert progress["question_count"] == 1
    assert progress["overall_accuracy"] == 1.0
    assert progress["mastery_model"] == "descriptive_attempt_metrics"


def test_invalid_option_and_unknown_question_are_rejected(client):
    configure_plab_service(service(approved=True))
    headers = {"X-User-Id": "student-1"}
    invalid = client.post(
        "/api/v1/plab/evaluate", headers=headers,
        json={"question_id": "PLAB-TEST-0001", "selected_option": "Z", "idempotency_key": "invalid-0001"},
    )
    unknown = client.get("/api/v1/plab/questions/UNKNOWN")
    assert invalid.status_code == 422
    assert unknown.status_code == 404


def test_unavailable_dynamic_clinical_backend_fails_closed(client):
    response = client.post("/api/v1/clinical/reason", json={"query": "Explain chest pain"})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "CLINICAL_AI_NOT_CONFIGURED"


def test_insufficient_evidence_prevents_student_availability(client):
    configure_plab_service(service(approved=True, evidence=False))
    response = client.get("/api/v1/plab/questions/PLAB-TEST-0001")
    assert response.status_code == 403


def test_reviewer_endpoint_blocks_student_role(client, monkeypatch):
    configure_plab_service(service())
    monkeypatch.setenv("MEDICALPLAB_INTERNAL_REVIEW_TOKEN", "secret-review-token")
    response = client.get(
        "/api/v1/internal/plab/review/status/PLAB-TEST-0001",
        headers={"Authorization": "Bearer secret-review-token", "X-User-Id": "student-1", "X-User-Role": "STUDENT"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "REVIEWER_ROLE_REQUIRED"


def test_golden_promotion_fails_without_completed_clinician_review():
    configured = service()
    assert configured.is_golden("PLAB-TEST-0001") is False
    assert configured.governance_counts()["golden"] == 0


def test_version_endpoint_works(client):
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert data["api_version"] == "v1"
    assert "runtime_mode" in data


def test_golden_promotion_rejects_missing_reviewer_id():
    configured = service(approved=True)
    review = configured.reviews["PLAB-TEST-0001"]
    broken_review = review.__class__(
        **{**review.__dict__, "reviewer_id": None}
    )
    configured.reviews["PLAB-TEST-0001"] = broken_review
    assert configured.is_golden("PLAB-TEST-0001") is False
    res = configured._promotion("PLAB-TEST-0001")
    assert "reviewer_missing" in res.error_codes


def test_golden_promotion_rejects_missing_review_timestamp():
    configured = service(approved=True)
    review = configured.reviews["PLAB-TEST-0001"]
    broken_review = review.__class__(
        **{**review.__dict__, "reviewed_at": None}
    )
    configured.reviews["PLAB-TEST-0001"] = broken_review
    assert configured.is_golden("PLAB-TEST-0001") is False
    res = configured._promotion("PLAB-TEST-0001")
    assert "review_timestamp_missing" in res.error_codes


def test_golden_promotion_rejects_changed_content_after_review():
    configured = service(approved=True)
    # Mutate question content after approval
    configured.questions["PLAB-TEST-0001"]["stem"] = "Altered stem that has not been clinician-approved."
    assert configured.is_golden("PLAB-TEST-0001") is False
    res = configured._promotion("PLAB-TEST-0001")
    assert "question_changed_after_review" in res.error_codes


def test_missing_corpus_fails_closed(monkeypatch):
    monkeypatch.setenv("MEDICALPLAB_DATA_ROOT", "C:/non_existent_data_directory_for_fail_closed_test")
    from medicalplab.plab.pilot import PLABProductError
    with pytest.raises(PLABProductError) as exc_info:
        PLABPilotService.load_default()
    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "PLAB_CONTENT_UNAVAILABLE"


def test_question_revision_increments_version_and_resets_approval():
    configured = service(approved=True)
    assert configured.is_golden("PLAB-TEST-0001") is True
    assert configured.reviews["PLAB-TEST-0001"].question_version == 1

    revised_status = configured.revise_question(
        question_id="PLAB-TEST-0001",
        updated={"stem": "Updated stem with improved clinical phrasing."},
        revision_reason="Refined clinical vignette clarity.",
        editor_id="CLINICAL-EDITOR-1",
    )
    assert revised_status["question_version"] == 2
    assert revised_status["review_status"] == "revised"
    assert revised_status["golden_status"] is False
    assert configured.is_golden("PLAB-TEST-0001") is False
    assert len(revised_status["revision_history"]) == 1


def test_progress_tracks_first_attempt_accuracy_and_completion():
    configured = service(approved=True)
    # First attempt: wrong
    configured.evaluate(
        user_id="user-analytics-1",
        question_id="PLAB-TEST-0001",
        selected_option="B",
        idempotency_key="attempt-1",
    )
    # Second attempt on same question: correct
    configured.evaluate(
        user_id="user-analytics-1",
        question_id="PLAB-TEST-0001",
        selected_option="A",
        idempotency_key="attempt-2",
    )
    prog = configured.progress("user-analytics-1")
    assert prog["total_attempts"] == 2
    assert prog["correct_attempts"] == 1
    assert prog["overall_accuracy"] == 0.5
    # First attempt was wrong (0.0)
    assert prog["first_attempt_accuracy"] == 0.0
    assert prog["question_completion"] == 1.0


def test_reviewer_authorized_workflow(client, monkeypatch):
    configured = service()
    configure_plab_service(configured)
    monkeypatch.setenv("MEDICALPLAB_INTERNAL_REVIEW_TOKEN", "valid-reviewer-token")
    headers = {
        "Authorization": "Bearer valid-reviewer-token",
        "X-User-Id": "DR-EXAMINER-1",
        "X-User-Role": "DOCTOR",
    }
    # 1. Start review
    start_resp = client.post(
        "/api/v1/internal/plab/review/PLAB-TEST-0001/start",
        headers=headers,
        json={"reviewer_name": "Dr. Examiner"},
    )
    assert start_resp.status_code == 200
    assert start_resp.json()["review_status"] == "in_review"

    # 2. Submit rejection
    reject_resp = client.post(
        "/api/v1/internal/plab/review/PLAB-TEST-0001/decision",
        headers=headers,
        json={
            "final_decision": "REJECT",
            "clinical_correctness": "fail",
            "sba_unambiguity": "fail",
            "uk_alignment": "fail",
            "evidence_adequacy": "fail",
            "distractor_quality": "fail",
            "explanation_quality": "fail",
            "review_comments": "Vignette does not meet PLAB standard.",
        },
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["review_status"] == "rejected"
    assert reject_resp.json()["golden_status"] is False
