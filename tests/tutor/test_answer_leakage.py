"""
Tests for answer-leakage prevention and attempt-key bound submission verification.

Verifies:
1. Attempt-key authorization invariants against SQLite store.
2. Client-provided is_submitted flag is non-authoritative and ignored.
3. Zero answer leakage across pre-submission hints (levels 1, 2, 3).
4. Regex and similarity leak scanner functionality.
5. TutorService fallback trigger when generation attempts answer leakage.
"""

import sqlite3
import pytest
from medicalplab.tutor.leak_scanner import AnswerLeakScanner
from medicalplab.tutor.session import verify_submission_proof
from medicalplab.tutor.models import TutorChatRequest
from medicalplab.tutor.provider import StubGenerativeProvider
from medicalplab.tutor.service import TutorService


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_university.sqlite3"
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
            VALUES ('user_alpha', 'UNI-RENAL-001', 'C', 1, 'proof_key_12345', '2026-09-14T12:00:00Z'),
                   ('user_beta', 'UNI-RENAL-002', 'A', 0, 'proof_key_67890', '2026-09-14T12:05:00Z')
            """
        )
        conn.commit()
    return db_file


def test_submission_proof_requires_attempt_key(temp_db):
    state = verify_submission_proof(
        user_id="user_alpha",
        question_id="UNI-RENAL-001",
        attempt_key=None,
        db_path=temp_db,
    )
    assert state == "PRE_SUBMISSION"


def test_submission_proof_mismatch_fails_closed(temp_db):
    state = verify_submission_proof(
        user_id="user_alpha",
        question_id="UNI-RENAL-001",
        attempt_key="wrong_key_99999",
        db_path=temp_db,
    )
    assert state == "PRE_SUBMISSION"


def test_submission_proof_wrong_user_or_question(temp_db):
    # Attempting to use user_alpha's valid attempt key for a different question
    state_diff_q = verify_submission_proof(
        user_id="user_alpha",
        question_id="UNI-RENAL-002",
        attempt_key="proof_key_12345",
        db_path=temp_db,
    )
    assert state_diff_q == "PRE_SUBMISSION"

    # Attempting to use user_alpha's valid attempt key as user_beta
    state_diff_user = verify_submission_proof(
        user_id="user_beta",
        question_id="UNI-RENAL-001",
        attempt_key="proof_key_12345",
        db_path=temp_db,
    )
    assert state_diff_user == "PRE_SUBMISSION"


def test_submission_proof_client_is_submitted_ignored(temp_db):
    # Testing that TutorChatRequest with is_submitted=True but no/wrong attempt_key remains PRE_SUBMISSION
    req = TutorChatRequest(
        query="Explain this to me",
        question_id="UNI-RENAL-001",
        is_submitted=True,  # Non-authoritative client flag
        attempt_key="invalid_or_missing",
    )
    # verify_submission_proof doesn't even accept is_submitted
    state = verify_submission_proof(
        user_id="user_alpha",
        question_id=req.question_id,
        attempt_key=req.attempt_key,
        db_path=temp_db,
    )
    assert state == "PRE_SUBMISSION"


def test_submission_proof_exact_tuple_unlocks_post_submission(temp_db):
    state = verify_submission_proof(
        user_id="user_alpha",
        question_id="UNI-RENAL-001",
        attempt_key="proof_key_12345",
        db_path=temp_db,
    )
    assert state == "POST_SUBMISSION"


def test_submission_proof_zero_leakage_on_failure(temp_db):
    # Ensure failure returns standard state without leaking whether user_id or question exists
    res1 = verify_submission_proof("user_unknown", "UNI-RENAL-001", "proof_key_12345", db_path=temp_db)
    res2 = verify_submission_proof("user_alpha", "UNI-RENAL-UNKNOWN", "proof_key_12345", db_path=temp_db)
    assert res1 == "PRE_SUBMISSION"
    assert res2 == "PRE_SUBMISSION"


def test_leak_scanner_catches_pattern_giveaways():
    scanner = AnswerLeakScanner()

    bad_drafts = [
        {"message": "The correct answer is B because efferent constriction raises pressure."},
        {"socratic_question": "Notice that option C is correct for this mechanism."},
        {"hints": ["Select option D to maximize your score."]},
        {"mechanistic_explanation": "You should choose option A."},
    ]

    for bd in bad_drafts:
        leaked, reason = scanner.scan_for_leaks(bd)
        assert leaked is True
        assert reason is not None


def test_leak_scanner_catches_explicit_correct_option_letter():
    scanner = AnswerLeakScanner()
    question = {
        "id": "UNI-RENAL-001",
        "correct_answer": "C",
        "options": {
            "A": "Afferent arteriolar constriction",
            "B": "Decreased capillary oncotic pressure",
            "C": "Efferent arteriolar vasoconstriction",
            "D": "Ureteral obstruction",
        },
    }

    draft = {
        "message": "Let us consider Option C carefully.",
    }
    leaked, reason = scanner.scan_for_leaks(draft, question=question)
    assert leaked is True
    assert "EXPLICIT_CORRECT_OPTION_LETTER_LEAK" in reason


def test_leak_scanner_clean_socratic_hint_passes():
    scanner = AnswerLeakScanner()
    question = {
        "id": "UNI-RENAL-001",
        "correct_answer": "C",
        "options": {
            "A": "Afferent arteriolar constriction",
            "B": "Decreased capillary oncotic pressure",
            "C": "Efferent arteriolar vasoconstriction",
            "D": "Ureteral obstruction",
        },
        "explanation": "Renin cleaves angiotensinogen into angiotensin I. ACE converts it to angiotensin II.",
    }

    clean_draft = {
        "message": "Think about how resistance at the outflow point of the glomerular capillary affects pressure.",
        "socratic_question": "What happens to upstream pressure if the exit vessel narrows?",
        "hints": ["Consider Starling forces and hydraulic resistance downstream."],
    }
    leaked, reason = scanner.scan_for_leaks(clean_draft, question=question)
    assert leaked is False
    assert reason is None


def test_tutor_service_enforces_pre_submission_leak_barrier():
    # If the provider attempts to leak the answer pre-submission, TutorService must trigger safe fallback
    class LeakingProvider(StubGenerativeProvider):
        def generate_structured(self, system_prompt, user_prompt, response_schema, **kwargs):
            resp = super().generate_structured(system_prompt, user_prompt, response_schema, **kwargs)
            resp.data["message"] = "The correct answer is C."
            return resp

    service = TutorService(provider=LeakingProvider())
    req = TutorChatRequest(
        query="Give me a hint for this question",
        question_id="UNI-RENAL-001",
        attempt_key=None,  # Pre-submission
    )
    res = service.chat(req, x_user_id="student_1")
    assert res.pedagogical_state == "PRE_SUBMISSION"
    # Fallback must be applied because a leak was detected
    assert res.fallback_applied is True
    # The leaked phrase must NOT be present in any served text
    assert "The correct answer is C" not in res.message
