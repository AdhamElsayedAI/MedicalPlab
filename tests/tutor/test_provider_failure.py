"""
Tests for provider failure modes, timeouts, rate limits, and safe pedagogical fallback.

Verifies:
1. Timeout handling (e.g. httpx.TimeoutException or TimeoutError).
2. Rate limit handling (HTTP 429).
3. Server error handling (HTTP 500).
4. Malformed JSON handling.
5. State-specific fallback behavior:
   - PRE_SUBMISSION: Safe conceptual hint without leaking answers or raw passages.
   - POST_SUBMISSION: Static verified question explanation.
"""

import httpx
from medicalplab.tutor.models import TutorChatRequest
from medicalplab.tutor.provider import GenerativeProvider, ProviderResponse
from medicalplab.tutor.service import TutorService


class TimeoutFailingProvider:
    provider_name: str = "failing_mock"
    model_name: str = "mock-timeout"

    def generate_structured(self, *args, **kwargs) -> ProviderResponse:
        raise httpx.ReadTimeout("Cloud LLM API timed out after 30.0s")


class RateLimitFailingProvider:
    provider_name: str = "failing_mock"
    model_name: str = "mock-429"

    def generate_structured(self, *args, **kwargs) -> ProviderResponse:
        req = httpx.Request("POST", "https://api.example.com/generate")
        resp = httpx.Response(429, request=req, text="Rate limit exceeded")
        raise httpx.HTTPStatusError("429 Too Many Requests", request=req, response=resp)


class ServerErrorFailingProvider:
    provider_name: str = "failing_mock"
    model_name: str = "mock-500"

    def generate_structured(self, *args, **kwargs) -> ProviderResponse:
        req = httpx.Request("POST", "https://api.example.com/generate")
        resp = httpx.Response(500, request=req, text="Internal Server Error")
        raise httpx.HTTPStatusError("500 Internal Server Error", request=req, response=resp)


class MalformedJSONProvider:
    provider_name: str = "malformed_mock"
    model_name: str = "mock-garbage"

    def generate_structured(self, *args, **kwargs) -> ProviderResponse:
        return ProviderResponse(
            raw_text="<<<NOT JSON AT ALL>>> { incomplete: true",
            structured_data=None,
            input_tokens=100,
            output_tokens=10,
            provider="malformed_mock",
            model="mock-garbage",
        )


def test_provider_timeout_triggers_safe_fallback():
    service = TutorService(provider=TimeoutFailingProvider())
    req = TutorChatRequest(
        query="Explain renin release mechanisms",
        question_id="UNI-RENAL-001",
    )
    res = service.chat(req, x_user_id="student_user")

    assert res.fallback_applied is True
    assert res.pedagogical_state == "PRE_SUBMISSION"
    assert "couldn't verify enough evidence" in res.message
    assert res.socratic_question is not None
    assert len(res.hints or []) >= 1


def test_provider_rate_limit_triggers_safe_fallback():
    service = TutorService(provider=RateLimitFailingProvider())
    req = TutorChatRequest(
        query="How does angiotensin II regulate efferent tone?",
        question_id="UNI-RENAL-001",
    )
    res = service.chat(req, x_user_id="student_user")

    assert res.fallback_applied is True
    assert res.pedagogical_state == "PRE_SUBMISSION"
    assert "couldn't verify enough evidence" in res.message


def test_provider_server_error_triggers_safe_fallback():
    service = TutorService(provider=ServerErrorFailingProvider())
    req = TutorChatRequest(
        query="Explain the filtration barrier",
        question_id="UNI-RENAL-001",
    )
    res = service.chat(req, x_user_id="student_user")

    assert res.fallback_applied is True
    assert res.pedagogical_state == "PRE_SUBMISSION"


def test_provider_malformed_json_triggers_safe_fallback():
    service = TutorService(provider=MalformedJSONProvider())
    req = TutorChatRequest(
        query="Why is podocyte charge important?",
        question_id="UNI-RENAL-001",
    )
    res = service.chat(req, x_user_id="student_user")

    assert res.fallback_applied is True
    assert res.pedagogical_state == "PRE_SUBMISSION"


def test_post_submission_failure_serves_verified_explanation(tmp_path):
    # In POST_SUBMISSION with verified attempt key, fallback provides static verified explanation
    import sqlite3
    db_file = tmp_path / "test_uni.sqlite3"
    with sqlite3.connect(db_file) as conn:
        conn.execute(
            """
            CREATE TABLE university_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                selected_option TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                attempt_key TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO university_attempts (user_id, question_id, selected_option, is_correct, attempt_key, timestamp)
            VALUES ('learner_verified', 'UNI-RENAL-001', 'C', 1, 'valid_key_abc', '2026-09-14T12:00:00Z')
            """
        )
        conn.commit()

    # Pass db_path to service via monkeypatch or testing verify_submission_proof directly
    from unittest.mock import patch
    with patch("medicalplab.tutor.service.verify_submission_proof", return_value="POST_SUBMISSION"):
        service = TutorService(provider=TimeoutFailingProvider())
        req = TutorChatRequest(
            query="Can you explain why option C was correct?",
            question_id="UNI-RENAL-001",
            attempt_key="valid_key_abc",
        )
        res = service.chat(req, x_user_id="learner_verified")

        assert res.fallback_applied is True
        assert res.pedagogical_state == "POST_SUBMISSION"
        assert "Post-submission review" in res.message
        # In post-submission fallback, static question explanation is included
        assert res.revision_summary is not None
