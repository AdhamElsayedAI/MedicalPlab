"""Tests for Remediation Loop Controller and Bounded Socratic Lifecycle."""
from unittest.mock import MagicMock
import pytest

from medicalplab.remediation.bridge import RemediationTutorBridge
from medicalplab.remediation.controller import (
    RemediationError,
    RemediationLoopController,
)
from medicalplab.remediation.models import (
    RemediationLifecycleState,
    RemediationOutcome,
    RemediationStatus,
    CANONICAL_SAFETY_FALLBACK_MESSAGE,
)
from medicalplab.tutor.models import TutorChatResponse


@pytest.fixture
def controller(tmp_path):
    test_db = tmp_path / "test_remediation.sqlite3"
    return RemediationLoopController(db_path=test_db)


def test_controller_start_session(controller: RemediationLoopController):
    response = controller.start_session(
        user_id="test_student_123",
        question_id="UNI-RENAL-001",
        selected_option="B",
        topic="RAAS mechanisms",
        attempt_id="ATT-START-01",
    )

    assert response.session_id.startswith("REM-")
    assert response.turn_number == 1
    assert response.max_turns == 3
    assert response.is_complete is False
    assert response.lifecycle_state == RemediationLifecycleState.REMEDIATING
    assert response.outcome is None
    assert response.remediation_status == RemediationStatus.PROBING
    assert response.pattern_id == "PATTERN-RAAS-SUB-01"
    assert response.timeline.status == "IN_PROGRESS"
    assert "Selected Option B" in response.timeline.initial_pattern
    assert response.tutor_message
    assert response.socratic_probe
    assert response.transfer_available is False


def test_controller_three_turn_lifecycle_and_transfer_readiness(controller: RemediationLoopController):
    user_id = "test_student_456"

    # Turn 1: Probe
    turn1 = controller.start_session(
        user_id=user_id,
        question_id="UNI-RENAL-001",
        selected_option="B",
        topic="RAAS mechanisms",
    )
    assert turn1.turn_number == 1
    assert turn1.is_complete is False
    assert turn1.lifecycle_state == RemediationLifecycleState.REMEDIATING
    assert turn1.transfer_available is False

    # Turn 2: Guide
    turn2 = controller.advance_turn(
        session_id=turn1.session_id,
        user_id=user_id,
        student_message="Renin is released by juxtaglomerular cells in response to low blood pressure.",
    )
    assert turn2.session_id == turn1.session_id
    assert turn2.turn_number == 2
    assert turn2.is_complete is False
    assert turn2.lifecycle_state == RemediationLifecycleState.REMEDIATING
    assert turn2.timeline.status == "IN_PROGRESS"
    assert turn2.transfer_available is False

    # Turn 3: Consolidate & Check Readiness (AWAITING_TRANSFER)
    # INVARIANT: Turn 3 does NOT declare learning success! It transitions to AWAITING_TRANSFER.
    turn3 = controller.advance_turn(
        session_id=turn1.session_id,
        user_id=user_id,
        student_message="Renin converts angiotensinogen into Angiotensin I. Then ACE converts Ang I into Angiotensin II.",
    )
    assert turn3.session_id == turn1.session_id
    assert turn3.turn_number == 3
    assert turn3.lifecycle_state == RemediationLifecycleState.AWAITING_TRANSFER
    assert turn3.transfer_available is True
    assert turn3.timeline.status == "AWAITING_TRANSFER"

    # Turn 4 Attempt: Must return awaiting transfer state without advancing turn counter
    turn4 = controller.advance_turn(
        session_id=turn1.session_id,
        user_id=user_id,
        student_message="Another message after completion.",
    )
    assert turn4.turn_number == 3
    assert turn4.lifecycle_state == RemediationLifecycleState.AWAITING_TRANSFER
    assert turn4.transfer_available is True


def test_controller_abandon_session(controller: RemediationLoopController):
    user_id = "test_student_abandon"
    start = controller.start_session(
        user_id=user_id,
        question_id="UNI-RENAL-001",
        selected_option="B",
    )

    abandon_resp = controller.abandon_session(
        session_id=start.session_id,
        user_id=user_id,
        reason="Student closed browser",
    )

    assert abandon_resp.is_complete is True
    assert abandon_resp.lifecycle_state == RemediationLifecycleState.COMPLETED
    assert abandon_resp.outcome == RemediationOutcome.ABANDONED
    assert abandon_resp.timeline.status == "UNRESOLVED"


def test_controller_idempotency(controller: RemediationLoopController):
    user_id = "test_student_idempotent"
    start = controller.start_session(
        user_id=user_id,
        question_id="UNI-RENAL-001",
        selected_option="B",
    )

    # First Turn 2 advance with key
    turn2_first = controller.advance_turn(
        session_id=start.session_id,
        user_id=user_id,
        student_message="Response 1",
        idempotency_key="KEY-T2-001",
    )
    assert turn2_first.turn_number == 2

    # Replay identical Turn 2 request with same key
    turn2_replay = controller.advance_turn(
        session_id=start.session_id,
        user_id=user_id,
        student_message="Response 1",
        idempotency_key="KEY-T2-001",
    )
    assert turn2_replay.turn_number == 2
    assert turn2_replay.tutor_message == turn2_first.tutor_message


def test_controller_safety_fallback(tmp_path):
    mock_bridge = MagicMock(spec=RemediationTutorBridge)
    mock_bridge.invoke_tutor_turn.return_value = TutorChatResponse(
        response_id="RESP-FB",
        session_id="SESS-FB",
        mode="misconception_diagnosis",
        message="I could not verify enough evidence.",
        support_status="SAFE_FALLBACK",
        fallback_applied=True,
    )

    ctrl = RemediationLoopController(
        bridge=mock_bridge,
        db_path=tmp_path / "test_safety_fb.sqlite3",
    )
    resp = ctrl.start_session(
        user_id="safe_student",
        question_id="UNI-RENAL-001",
        selected_option="B",
    )

    assert resp.is_complete is True
    assert resp.lifecycle_state == RemediationLifecycleState.COMPLETED
    assert resp.outcome == RemediationOutcome.SAFETY_FALLBACK
    assert resp.transfer_available is False
    assert resp.remediation_status == RemediationStatus.UNRESOLVED
    assert resp.remediation_status not in (RemediationStatus.PROBING, RemediationStatus.GUIDING, RemediationStatus.CONFIRMING)
    assert "awaiting" not in resp.timeline.transfer_result.lower()
    assert resp.timeline.transfer_result == "Remediation stopped safely; no transfer assessment performed."
    assert resp.timeline.status == "SAFETY_FALLBACK"
    assert resp.socratic_probe is None
    assert resp.tutor_message == CANONICAL_SAFETY_FALLBACK_MESSAGE
    assert resp.citations == []

    # No transfer action may be available for a safety fallback session
    with pytest.raises(RemediationError) as exc_info:
        ctrl.get_transfer_item(resp.session_id, user_id="safe_student")
    assert exc_info.value.status_code == 422

    # Verify persisted session retrieval maintains coherent terminal fallback state
    persisted = ctrl.get_session(resp.session_id, user_id="safe_student")
    assert persisted is not None
    assert persisted.is_complete is True
    assert persisted.lifecycle_state == RemediationLifecycleState.COMPLETED
    assert persisted.outcome == RemediationOutcome.SAFETY_FALLBACK
    assert persisted.remediation_status == RemediationStatus.UNRESOLVED
    assert persisted.timeline.status == "SAFETY_FALLBACK"
    assert "awaiting" not in persisted.timeline.transfer_result.lower()
    assert persisted.timeline.transfer_result == "Remediation stopped safely; no transfer assessment performed."
    assert persisted.turns[-1].tutor_message == CANONICAL_SAFETY_FALLBACK_MESSAGE
    assert persisted.turns[-1].socratic_probe is None
    assert persisted.turns[-1].citations == []


def test_controller_user_ownership(controller: RemediationLoopController):
    turn1 = controller.start_session(
        user_id="legitimate_owner",
        question_id="UNI-RENAL-001",
        selected_option="B",
    )

    with pytest.raises(RemediationError) as exc:
        controller.advance_turn(
            session_id=turn1.session_id,
            user_id="impostor_user",
            student_message="Attempting to hijack session",
        )
    assert exc.value.status_code == 403


def test_controller_session_not_found(controller: RemediationLoopController):
    with pytest.raises(RemediationError) as exc:
        controller.advance_turn(
            session_id="NON-EXISTENT-SESSION",
            user_id="test_user",
            student_message="Hello",
        )
    assert exc.value.status_code == 404


def test_correct_answer_rejected_for_remediation(controller: RemediationLoopController):
    """Correct answer 'A' for UNI-RENAL-001 must be rejected; remediation is distractor-only."""
    with pytest.raises(RemediationError) as exc:
        controller.start_session(
            user_id="student_correct",
            question_id="UNI-RENAL-001",
            selected_option="A",  # Correct answer
        )
    assert exc.value.status_code == 422
    assert "correct answer" in str(exc.value).lower()


def test_authoritative_assistance_overrides_client_was_assisted_false(controller: RemediationLoopController):
    """If server session recorded assistance, client sending was_assisted=False MUST NOT obtain TRANSFER_CONFIRMED."""
    user_id = "assisted_manipulation_student"
    s1 = controller.start_session(
        user_id=user_id,
        question_id="UNI-RENAL-001",
        selected_option="B",
    )
    # Advance to Turn 2 & 3
    controller.advance_turn(session_id=s1.session_id, user_id=user_id, student_message="Renin is from JGA.")
    s3 = controller.advance_turn(session_id=s1.session_id, user_id=user_id, student_message="Renin converts angiotensinogen to Ang I.")
    assert s3.lifecycle_state == RemediationLifecycleState.AWAITING_TRANSFER

    # Student solicits extra assistance while in AWAITING_TRANSFER
    controller.advance_turn(session_id=s1.session_id, user_id=user_id, student_message="Give me extra help on the transfer question.")

    # Legitimate transfer item dispensed
    item = controller.get_transfer_item(session_id=s1.session_id, user_id=user_id)
    assert item.question_id == "UNI-RENAL-001-T"

    # Manipulated client attempts to send was_assisted=False to bypass disqualification
    resp = controller.submit_transfer(
        session_id=s1.session_id,
        user_id=user_id,
        question_id=item.question_id,
        selected_option="A",  # Correct answer on transfer
        was_assisted=False,    # CLIENT CLAIMS FALSE!
    )
    # Server authority MUST override client boolean to UNRESOLVED
    assert resp.outcome == RemediationOutcome.UNRESOLVED
    assert resp.is_correct is True
    assert "unconfirmed" in resp.timeline.transfer_result.lower()


def test_transfer_without_item_dispensed_rejected(controller: RemediationLoopController):
    """Submitting a transfer answer without prior get_transfer_item must be rejected before scoring (422)."""
    user_id = "no_dispense_student"
    s1 = controller.start_session(
        user_id=user_id,
        question_id="UNI-RENAL-001",
        selected_option="B",
    )
    controller.advance_turn(session_id=s1.session_id, user_id=user_id, student_message="Renin is from JGA.")
    controller.advance_turn(session_id=s1.session_id, user_id=user_id, student_message="Renin converts angiotensinogen to Ang I.")

    # Never called get_transfer_item! Directly submits transfer -> Must be rejected with 422
    with pytest.raises(RemediationError) as exc:
        controller.submit_transfer(
            session_id=s1.session_id,
            user_id=user_id,
            question_id="UNI-RENAL-001-T",
            selected_option="A",
            was_assisted=False,
        )
    assert exc.value.status_code == 422
    assert "not been dispensed" in str(exc.value).lower()


def test_transfer_mismatched_question_rejected(controller: RemediationLoopController):
    """Submitting a question ID that differs from dispensed item must be rejected before scoring (422)."""
    user_id = "mismatch_student"
    s1 = controller.start_session(
        user_id=user_id,
        question_id="UNI-RENAL-001",
        selected_option="B",
    )
    controller.advance_turn(session_id=s1.session_id, user_id=user_id, student_message="Renin is from JGA.")
    controller.advance_turn(session_id=s1.session_id, user_id=user_id, student_message="Renin converts angiotensinogen to Ang I.")
    item = controller.get_transfer_item(session_id=s1.session_id, user_id=user_id)
    assert item.question_id == "UNI-RENAL-001-T"

    with pytest.raises(RemediationError) as exc:
        controller.submit_transfer(
            session_id=s1.session_id,
            user_id=user_id,
            question_id="UNI-RENAL-999-WRONG",
            selected_option="A",
            was_assisted=False,
        )
    assert exc.value.status_code == 422
    assert "does not match dispensed" in str(exc.value).lower()


def test_all_session_endpoints_reject_cross_user_access(controller: RemediationLoopController):
    """All session endpoints must enforce user ownership and return 403 on cross-user access."""
    legit_user = "user_alpha"
    impostor = "user_beta"

    s = controller.start_session(user_id=legit_user, question_id="UNI-RENAL-001", selected_option="B")
    session_id = s.session_id

    # 1. get_session
    with pytest.raises(RemediationError) as exc:
        controller.get_session(session_id, user_id=impostor)
    assert exc.value.status_code == 403

    # 2. advance_turn
    with pytest.raises(RemediationError) as exc:
        controller.advance_turn(session_id=session_id, user_id=impostor, student_message="Hijack")
    assert exc.value.status_code == 403

    # Advance cleanly to AWAITING_TRANSFER
    controller.advance_turn(session_id=session_id, user_id=legit_user, student_message="Renin from JGA")
    controller.advance_turn(session_id=session_id, user_id=legit_user, student_message="Renin converts angiotensinogen")

    # 3. get_transfer_item
    with pytest.raises(RemediationError) as exc:
        controller.get_transfer_item(session_id=session_id, user_id=impostor)
    assert exc.value.status_code == 403

    # 4. submit_transfer
    with pytest.raises(RemediationError) as exc:
        controller.submit_transfer(
            session_id=session_id,
            user_id=impostor,
            question_id="UNI-RENAL-001-T",
            selected_option="A",
        )
    assert exc.value.status_code == 403

    # 5. abandon_session
    with pytest.raises(RemediationError) as exc:
        controller.abandon_session(session_id=session_id, user_id=impostor)
    assert exc.value.status_code == 403


def test_controller_persistence_across_instances(tmp_path):
    """Session state must survive process/controller restart via SQLite backing."""
    db_file = tmp_path / "persistence_test.sqlite3"
    ctrl1 = RemediationLoopController(db_path=db_file)

    s1 = ctrl1.start_session(user_id="persisted_user", question_id="UNI-RENAL-001", selected_option="B")
    ctrl1.advance_turn(session_id=s1.session_id, user_id="persisted_user", student_message="Renin is from JGA.")

    # Instantiate a completely fresh controller with the same db_path (simulating server restart)
    ctrl2 = RemediationLoopController(db_path=db_file)
    restored = ctrl2.get_session(s1.session_id, user_id="persisted_user")

    assert restored is not None
    assert restored.session_id == s1.session_id
    assert restored.user_id == "persisted_user"
    assert restored.turn_number == 2
    assert restored.remediation_status == RemediationStatus.GUIDING


def test_attempt_provenance_validation(tmp_path):
    """Rigorous attempt provenance: nonexistent (404), foreign-owned (403), correct (422), mismatched (422), valid incorrect (200)."""
    import sqlite3
    from contextlib import closing

    db_path = tmp_path / "provenance_test.sqlite3"
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("""
            CREATE TABLE university_attempts (
                user_id TEXT NOT NULL,
                attempt_key TEXT NOT NULL,
                question_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                selected TEXT NOT NULL,
                correct INTEGER NOT NULL,
                PRIMARY KEY(user_id, attempt_key)
            )
        """)
        # Seed 1: Valid incorrect attempt owned by student_alpha
        conn.execute(
            "INSERT INTO university_attempts VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("student_alpha", "ATT-ALPHA-01", "UNI-RENAL-001", "Renal", "RAAS mechanisms", "B", 0),
        )
        # Seed 2: Correct attempt owned by student_alpha
        conn.execute(
            "INSERT INTO university_attempts VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("student_alpha", "ATT-ALPHA-CORRECT", "UNI-RENAL-001", "Renal", "RAAS mechanisms", "A", 1),
        )
        # Seed 3: Foreign-owned attempt by student_beta
        conn.execute(
            "INSERT INTO university_attempts VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("student_beta", "ATT-BETA-01", "UNI-RENAL-001", "Renal", "RAAS mechanisms", "B", 0),
        )
        conn.commit()

    ctrl = RemediationLoopController(db_path=db_path)

    # 1. Nonexistent attempt rejected with 404
    with pytest.raises(RemediationError) as exc_404:
        ctrl.start_session(
            user_id="student_alpha",
            question_id="UNI-RENAL-001",
            selected_option="B",
            attempt_id="ATT-DOES-NOT-EXIST",
        )
    assert exc_404.value.status_code == 404
    assert "not found" in str(exc_404.value).lower()

    # 2. Foreign-owned attempt rejected with 403
    with pytest.raises(RemediationError) as exc_403:
        ctrl.start_session(
            user_id="student_alpha",
            question_id="UNI-RENAL-001",
            selected_option="B",
            attempt_id="ATT-BETA-01",
        )
    assert exc_403.value.status_code == 403
    assert "another learner" in str(exc_403.value).lower()

    # 3. Correct attempt rejected with 422 (avoids leaking answer key)
    with pytest.raises(RemediationError) as exc_422_corr:
        ctrl.start_session(
            user_id="student_alpha",
            question_id="UNI-RENAL-001",
            selected_option="A",
            attempt_id="ATT-ALPHA-CORRECT",
        )
    assert exc_422_corr.value.status_code == 422
    assert "incorrect" in str(exc_422_corr.value).lower()

    # 4. Mismatched question/selected option rejected with 422
    with pytest.raises(RemediationError) as exc_422_mismatch:
        ctrl.start_session(
            user_id="student_alpha",
            question_id="UNI-RENAL-001",
            selected_option="C",  # Attempt was recorded with option 'B'
            attempt_id="ATT-ALPHA-01",
        )
    assert exc_422_mismatch.value.status_code == 422
    assert "does not match" in str(exc_422_mismatch.value).lower()

    # 5. Valid owned persisted incorrect attempt accepted with 200
    valid_resp = ctrl.start_session(
        user_id="student_alpha",
        question_id="UNI-RENAL-001",
        selected_option="B",
        attempt_id="ATT-ALPHA-01",
    )
    assert valid_resp.turn_number == 1
    assert valid_resp.session_id.startswith("REM-")
    session = ctrl.get_session(valid_resp.session_id, user_id="student_alpha")
    assert session.original_attempt_id == "ATT-ALPHA-01"


def test_transfer_idempotency_and_conflicting_payload(controller: RemediationLoopController):
    """Verify duplicate submission, terminal session retry, and conflicting payload rejection (409)."""
    user_id = "idempotency_student"
    s1 = controller.start_session(user_id=user_id, question_id="UNI-RENAL-001", selected_option="B")
    controller.advance_turn(session_id=s1.session_id, user_id=user_id, student_message="Renin is from JGA.")
    controller.advance_turn(session_id=s1.session_id, user_id=user_id, student_message="Renin converts angiotensinogen to Ang I.")
    item = controller.get_transfer_item(session_id=s1.session_id, user_id=user_id)

    # 1. First submission with idempotency key
    resp1 = controller.submit_transfer(
        session_id=s1.session_id,
        user_id=user_id,
        question_id=item.question_id,
        selected_option="A",
        idempotency_key="IDEM-TRANSFER-100",
    )
    assert resp1.outcome == RemediationOutcome.TRANSFER_CONFIRMED

    # 2. Replay with exact same idempotency key and payload -> returns cached response (effectively-once)
    resp2 = controller.submit_transfer(
        session_id=s1.session_id,
        user_id=user_id,
        question_id=item.question_id,
        selected_option="A",
        idempotency_key="IDEM-TRANSFER-100",
    )
    assert resp2.outcome == RemediationOutcome.TRANSFER_CONFIRMED
    assert "already completed" in resp2.explanation.lower()

    # 3. Conflicting payload with same idempotency key -> rejected with 409
    with pytest.raises(RemediationError) as exc_409:
        controller.submit_transfer(
            session_id=s1.session_id,
            user_id=user_id,
            question_id=item.question_id,
            selected_option="B",  # Conflicting answer!
            idempotency_key="IDEM-TRANSFER-100",
        )
    assert exc_409.value.status_code == 409
    assert "conflicting" in str(exc_409.value).lower()

    # 4. Different idempotency key on completed terminal session -> returns terminal response without re-scoring
    resp4 = controller.submit_transfer(
        session_id=s1.session_id,
        user_id=user_id,
        question_id=item.question_id,
        selected_option="A",
        idempotency_key="IDEM-TRANSFER-200",
    )
    assert resp4.outcome == RemediationOutcome.TRANSFER_CONFIRMED
