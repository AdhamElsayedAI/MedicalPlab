"""Focused safety tests for Phase 2B SAFETY_FALLBACK content contract normalization."""
from unittest.mock import MagicMock
import pytest

from medicalplab.remediation.bridge import RemediationTutorBridge
from medicalplab.remediation.controller import (
    RemediationError,
    RemediationLoopController,
)
from medicalplab.remediation.models import (
    CANONICAL_SAFETY_FALLBACK_MESSAGE,
    RemediationLifecycleState,
    RemediationOutcome,
    RemediationStatus,
)
from medicalplab.tutor.models import TutorChatResponse, TutorCitationDTO


SUBSTANTIVE_UPSTREAM_CLAIM = (
    "Post-submission review for RAAS mechanisms: Renin acts on angiotensinogen to form angiotensin I. "
    "ACE then converts angiotensin I to angiotensin II; these are distinct steps in the pathway."
)


def test_safety_fallback_normalizes_substantive_upstream_content(tmp_path):
    """A. SAFETY_FALLBACK normalizes substantive upstream content from tutor/bridge."""
    mock_bridge = MagicMock(spec=RemediationTutorBridge)
    mock_bridge.invoke_tutor_turn.return_value = TutorChatResponse(
        response_id="RESP-SUBSTANTIVE-FALLBACK",
        session_id="SESS-SUBSTANTIVE-FALLBACK",
        mode="misconception_diagnosis",
        message=SUBSTANTIVE_UPSTREAM_CLAIM,
        support_status="SAFE_FALLBACK",
        fallback_applied=True,
        citations=[],
    )

    ctrl = RemediationLoopController(
        bridge=mock_bridge,
        db_path=tmp_path / "test_safety_content.sqlite3",
    )
    resp = ctrl.start_session(
        user_id="safe_learner_a",
        question_id="UNI-RENAL-001",
        selected_option="B",
    )

    # Invariant assertions on the response
    assert resp.tutor_message == CANONICAL_SAFETY_FALLBACK_MESSAGE
    assert SUBSTANTIVE_UPSTREAM_CLAIM not in resp.tutor_message
    assert resp.socratic_probe is None
    assert resp.citations == []
    assert resp.lifecycle_state == RemediationLifecycleState.COMPLETED
    assert resp.outcome == RemediationOutcome.SAFETY_FALLBACK
    assert resp.remediation_status == RemediationStatus.UNRESOLVED
    assert resp.transfer_available is False
    assert resp.is_complete is True


def test_persisted_reloaded_safety_fallback_remains_safe(tmp_path):
    """B. Persisted/reloaded SAFETY_FALLBACK remains safe and uncited."""
    mock_bridge = MagicMock(spec=RemediationTutorBridge)
    mock_bridge.invoke_tutor_turn.return_value = TutorChatResponse(
        response_id="RESP-PERSIST-FALLBACK",
        session_id="SESS-PERSIST-FALLBACK",
        mode="misconception_diagnosis",
        message=SUBSTANTIVE_UPSTREAM_CLAIM,
        support_status="SAFE_FALLBACK",
        fallback_applied=True,
        citations=[],
    )

    db_path = tmp_path / "test_safety_persist.sqlite3"
    ctrl = RemediationLoopController(
        bridge=mock_bridge,
        db_path=db_path,
    )
    resp = ctrl.start_session(
        user_id="safe_learner_b",
        question_id="UNI-RENAL-001",
        selected_option="B",
    )

    # Create a fresh controller instance pointing to the same SQLite DB to simulate complete process reload
    fresh_ctrl = RemediationLoopController(db_path=db_path)
    persisted = fresh_ctrl.get_session(resp.session_id, user_id="safe_learner_b")

    assert persisted is not None
    assert persisted.is_complete is True
    assert persisted.lifecycle_state == RemediationLifecycleState.COMPLETED
    assert persisted.outcome == RemediationOutcome.SAFETY_FALLBACK
    assert persisted.remediation_status == RemediationStatus.UNRESOLVED
    assert persisted.timeline.status == "SAFETY_FALLBACK"
    assert "awaiting" not in persisted.timeline.transfer_result.lower()
    assert persisted.timeline.transfer_result == "Remediation stopped safely; no transfer assessment performed."

    # Verify turns contain only canonical safe message
    assert len(persisted.turns) >= 1
    last_turn = persisted.turns[-1]
    assert last_turn.tutor_message == CANONICAL_SAFETY_FALLBACK_MESSAGE
    assert SUBSTANTIVE_UPSTREAM_CLAIM not in last_turn.tutor_message
    assert last_turn.socratic_probe is None
    assert last_turn.citations == []

    # Attempting to fetch transfer item must be rejected
    with pytest.raises(RemediationError) as exc_info:
        fresh_ctrl.get_transfer_item(resp.session_id, user_id="safe_learner_b")
    assert exc_info.value.status_code == 422


def test_normal_supported_remediation_remains_unchanged(tmp_path):
    """C. Normal supported remediation with valid citations must NOT be normalized."""
    valid_explanation = "Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I."
    mock_bridge = MagicMock(spec=RemediationTutorBridge)
    mock_bridge.invoke_tutor_turn.return_value = TutorChatResponse(
        response_id="RESP-VALID",
        session_id="SESS-VALID",
        mode="misconception_diagnosis",
        message=valid_explanation,
        support_status="SUPPORTED",
        fallback_applied=False,
        citations=[
            TutorCitationDTO(
                ref="DOC-PMC-RENAL-0001:C001",
                quote="Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I (Ang I).",
                document_id="DOC-PMC-RENAL-0001",
                chunk_id="DOC-PMC-RENAL-0001-B0003-C01",
                title="Renin-Angiotensin System",
                license="CC BY 3.0",
            )
        ],
    )

    ctrl = RemediationLoopController(
        bridge=mock_bridge,
        db_path=tmp_path / "test_normal_supported.sqlite3",
    )
    resp = ctrl.start_session(
        user_id="normal_learner",
        question_id="UNI-RENAL-001",
        selected_option="B",
    )

    # Invariants for supported turn
    assert resp.tutor_message == valid_explanation
    assert resp.tutor_message != CANONICAL_SAFETY_FALLBACK_MESSAGE
    assert resp.lifecycle_state == RemediationLifecycleState.REMEDIATING
    assert resp.outcome is None
    assert resp.remediation_status == RemediationStatus.PROBING
    assert len(resp.citations) == 1
    assert resp.citations[0]["ref"] == "DOC-PMC-RENAL-0001:C001"


def test_safety_fallback_turn2_and_turn3_normalization(tmp_path):
    """D. Fallback occurring on Turn 2 or Turn 3 also normalizes substantive content."""
    mock_bridge = MagicMock(spec=RemediationTutorBridge)

    # Turn 1: normal supported probe
    mock_bridge.invoke_tutor_turn.return_value = TutorChatResponse(
        response_id="RESP-T1-SUPPORTED",
        session_id="SESS-T2-FALLBACK",
        mode="misconception_diagnosis",
        message="Let us trace the initial cleavage step.",
        support_status="SUPPORTED",
        fallback_applied=False,
        citations=[
            TutorCitationDTO(
                ref="DOC-PMC-RENAL-0001:C001",
                quote="Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I (Ang I).",
                document_id="DOC-PMC-RENAL-0001",
                chunk_id="DOC-PMC-RENAL-0001-B0003-C01",
                title="Renin-Angiotensin System",
                license="CC BY 3.0",
            )
        ],
    )

    ctrl = RemediationLoopController(
        bridge=mock_bridge,
        db_path=tmp_path / "test_t2_t3_fallback.sqlite3",
    )
    t1 = ctrl.start_session(
        user_id="turn2_learner",
        question_id="UNI-RENAL-001",
        selected_option="B",
    )
    assert t1.outcome is None

    # Turn 2: upstream provider fails and returns substantive text with SAFE_FALLBACK
    mock_bridge.invoke_tutor_turn.return_value = TutorChatResponse(
        response_id="RESP-T2-FALLBACK",
        session_id="SESS-T2-FALLBACK",
        mode="misconception_diagnosis",
        message=SUBSTANTIVE_UPSTREAM_CLAIM,
        support_status="SAFE_FALLBACK",
        fallback_applied=True,
        citations=[],
    )

    t2 = ctrl.advance_turn(
        session_id=t1.session_id,
        user_id="turn2_learner",
        student_message="Renin makes angiotensin II directly.",
    )

    # Turn 2 fallback normalization assertions
    assert t2.is_complete is True
    assert t2.lifecycle_state == RemediationLifecycleState.COMPLETED
    assert t2.outcome == RemediationOutcome.SAFETY_FALLBACK
    assert t2.remediation_status == RemediationStatus.UNRESOLVED
    assert t2.tutor_message == CANONICAL_SAFETY_FALLBACK_MESSAGE
    assert SUBSTANTIVE_UPSTREAM_CLAIM not in t2.tutor_message
    assert t2.socratic_probe is None
    assert t2.citations == []
    assert t2.transfer_available is False
