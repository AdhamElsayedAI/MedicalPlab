"""
FastAPI contract tests for canonical and legacy tutor endpoints.

Verifies:
1. /api/v1/tutor/chat (canonical product API)
   - Status 200 on valid request.
   - Request schema validation (HTTP 422 on invalid query length, bad hint_level, bad selected_option).
   - X-User-Id header extraction.
   - Fail-closed pre-submission default when attempt_key is omitted.
   - Client is_submitted=True flag ignored by server.
2. /ai/chat (legacy gateway)
   - Status 200 on valid payload.
   - Response envelope compatibility (explanation, citations, tutor_response).
   - Status 400 on empty query.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from main import app as main_app
from medicalplab.stage_g.product_api import router as product_router

product_app = FastAPI()
product_app.include_router(product_router)

client_canonical = TestClient(product_app)
client_legacy = TestClient(main_app)


def test_canonical_tutor_chat_success():
    payload = {
        "query": "How does efferent arteriolar resistance influence GFR?",
        "topic": "Renal Physiology",
        "mode": "socratic_hint",
        "hint_level": 1,
    }
    headers = {"X-User-Id": "student_test_123"}
    resp = client_canonical.post("/api/v1/tutor/chat", json=payload, headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert "response_id" in data
    assert "message" in data
    assert "pedagogical_state" in data
    assert data["support_status"] in ["SUPPORTED", "SAFE_FALLBACK", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "ABSTAIN"]
    assert "latency_breakdown" in data
    assert "verification" in data


def test_canonical_tutor_chat_validation_errors():
    # Empty query (< 2 characters)
    resp_empty = client_canonical.post("/api/v1/tutor/chat", json={"query": ""})
    assert resp_empty.status_code == 422

    # Invalid hint_level (> 3)
    resp_bad_hint = client_canonical.post("/api/v1/tutor/chat", json={"query": "Valid query", "hint_level": 5})
    assert resp_bad_hint.status_code == 422

    # Invalid option letter
    resp_bad_opt = client_canonical.post("/api/v1/tutor/chat", json={"query": "Valid query", "selected_option": "Z"})
    assert resp_bad_opt.status_code == 422


def test_canonical_tutor_pre_submission_invariants():
    payload = {
        "query": "Can you give me a hint on this question?",
        "question_id": "UNI-RENAL-001",
        "is_submitted": True,  # Non-authoritative hint
        "attempt_key": None,   # No authoritative proof
    }
    resp = client_canonical.post("/api/v1/tutor/chat", json=payload, headers={"X-User-Id": "demo_user"})
    assert resp.status_code == 200
    data = resp.json()
    # Server must strictly enforce PRE_SUBMISSION
    assert data["pedagogical_state"] == "PRE_SUBMISSION"
    # Never leak the correct answer
    assert "The correct answer is" not in data["message"]


def test_legacy_ai_chat_success():
    payload = {
        "query": "Explain renin secretion from the juxtaglomerular apparatus",
        "question_id": "UNI-RENAL-001",
    }
    headers = {"X-User-Id": "legacy_user"}
    resp = client_legacy.post("/ai/chat", json=payload, headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert "explanation" in data
    assert "citations" in data
    assert "tutor_response" in data
    assert data["safety_validated"] is True


def test_legacy_ai_chat_empty_query_returns_400():
    resp = client_legacy.post("/ai/chat", json={"query": ""})
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
