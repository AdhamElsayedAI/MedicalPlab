"""End-to-end MVP Journey Tests for Phase 2B Intelligent Socratic Remediation."""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from main import app
from medicalplab.remediation.api import configure_remediation_controller
from medicalplab.remediation.bridge import RemediationTutorBridge
from medicalplab.remediation.controller import RemediationLoopController
from medicalplab.remediation.models import CANONICAL_SAFETY_FALLBACK_MESSAGE
from medicalplab.tutor.models import TutorChatResponse


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_e2e_journey_happy_path_transfer_confirmed(client: TestClient):
    """Full vertical slice: Original error -> Turn 1 -> Turn 2 -> Turn 3 -> Transfer -> Next Rec."""
    user_id = "test_e2e_learner_happy"

    # Step 0: Record initial incorrect attempt in university track
    ans_res = client.post(
        "/api/v1/university/answer",
        json={
            "question_id": "UNI-RENAL-001",
            "selected_option": "B",
            "attempt_key": "ATT-E2E-01",
            "idempotency_key": "ATT-E2E-01",
        },
        headers={"X-User-Id": user_id},
    )
    assert ans_res.status_code == 200

    # Step 1: Start remediation from original attempt (UNI-RENAL-001 Option B)
    start_resp = client.post(
        "/api/v1/remediation/start",
        json={
            "question_id": "UNI-RENAL-001",
            "selected_option": "B",
            "topic": "RAAS mechanisms",
            "attempt_id": "ATT-E2E-01",
        },
        headers={"X-User-Id": user_id},
    )
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    session_id = start_data["session_id"]
    assert start_data["turn_number"] == 1
    assert start_data["pattern_id"] == "PATTERN-RAAS-SUB-01"
    assert start_data["timeline"]["status"] == "IN_PROGRESS"
    assert start_data["transfer_available"] is False

    # Step 2: Advance to Turn 2 (Mechanistic Guidance)
    t2_resp = client.post(
        "/api/v1/remediation/turn",
        json={
            "session_id": session_id,
            "student_message": "Renin is an enzyme secreted by the juxtaglomerular apparatus.",
        },
        headers={"X-User-Id": user_id},
    )
    assert t2_resp.status_code == 200
    t2_data = t2_resp.json()
    assert t2_data["turn_number"] == 2
    assert t2_data["remediation_status"] == "GUIDING"
    assert t2_data["transfer_available"] is False

    # Step 3: Advance to Turn 3 (Consolidation & Readiness Check)
    t3_resp = client.post(
        "/api/v1/remediation/turn",
        json={
            "session_id": session_id,
            "student_message": "Renin acts on hepatic angiotensinogen to form Ang I, which ACE converts to Ang II.",
        },
        headers={"X-User-Id": user_id},
    )
    assert t3_resp.status_code == 200
    t3_data = t3_resp.json()
    assert t3_data["turn_number"] == 3
    # Critical invariant: must be AWAITING_TRANSFER, transfer_available is True
    assert t3_data["lifecycle_state"] == "AWAITING_TRANSFER"
    assert t3_data["transfer_available"] is True
    assert t3_data["timeline"]["status"] == "AWAITING_TRANSFER"

    # Step 4: Fetch eligible held-out transfer item
    t_item_resp = client.get(
        f"/api/v1/remediation/session/{session_id}/transfer",
        headers={"X-User-Id": user_id},
    )
    assert t_item_resp.status_code == 200
    t_item = t_item_resp.json()
    assert t_item["question_id"] == "UNI-RENAL-001-T"
    assert "correct_answer" not in t_item
    assert "explanation" not in t_item

    # Step 5: Submit correct answer to transfer item
    sub_resp = client.post(
        f"/api/v1/remediation/session/{session_id}/transfer",
        json={
            "session_id": session_id,
            "question_id": t_item["question_id"],
            "selected_option": "A",
            "was_assisted": False,
        },
        headers={"X-User-Id": user_id},
    )
    assert sub_resp.status_code == 200
    sub_data = sub_resp.json()
    assert sub_data["outcome"] == "TRANSFER_CONFIRMED"
    assert sub_data["is_correct"] is True
    assert sub_data["timeline"]["status"] == "COMPLETED"
    assert "Transfer demonstrated" in sub_data["timeline"]["transfer_result"]
    assert sub_data["timeline"]["next_recommendation"] is not None


def test_e2e_journey_unmapped_distractor_abstention(client: TestClient):
    """Unmapped distractor must cleanly abstain with INSUFFICIENT_EVIDENCE without guessing."""
    user_id = "test_e2e_learner_abstain"

    resp = client.post(
        "/api/v1/remediation/start",
        json={
            "question_id": "UNKNOWN-QUESTION-XYZ",
            "selected_option": "D",
            "topic": "Renal physiology",
        },
        headers={"X-User-Id": user_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pattern_id"] == "PATTERN-GEN-FALLBACK"
    assert "Abstaining" in data["timeline"]["learning_gap"]


def test_e2e_journey_assisted_transfer_unresolved(client: TestClient):
    """Assisted transfer answers must be marked UNRESOLVED and never confirm transfer."""
    user_id = "test_e2e_learner_assisted"

    # Start and advance through 3 turns
    s_resp = client.post(
        "/api/v1/remediation/start",
        json={"question_id": "UNI-RENAL-001", "selected_option": "B"},
        headers={"X-User-Id": user_id},
    )
    session_id = s_resp.json()["session_id"]

    client.post(
        "/api/v1/remediation/turn",
        json={"session_id": session_id, "student_message": "Renin is an enzyme secreted by the juxtaglomerular apparatus."},
        headers={"X-User-Id": user_id},
    )
    client.post(
        "/api/v1/remediation/turn",
        json={"session_id": session_id, "student_message": "Renin converts angiotensinogen to angiotensin I."},
        headers={"X-User-Id": user_id},
    )

    # Dispense transfer item first
    t_item_resp = client.get(
        f"/api/v1/remediation/session/{session_id}/transfer",
        headers={"X-User-Id": user_id},
    )
    assert t_item_resp.status_code == 200
    t_item = t_item_resp.json()

    # Submit correct answer but with was_assisted=True
    sub_resp = client.post(
        f"/api/v1/remediation/session/{session_id}/transfer",
        json={
            "session_id": session_id,
            "question_id": t_item["question_id"],
            "selected_option": "A",
            "was_assisted": True,
        },
        headers={"X-User-Id": user_id},
    )
    assert sub_resp.status_code == 200
    data = sub_resp.json()
    assert data["outcome"] == "UNRESOLVED"
    assert data["is_correct"] is True  # Answer was right, but disqualified due to assistance
    assert "unconfirmed" in data["timeline"]["transfer_result"].lower()


def test_e2e_journey_safety_fallback(tmp_path, client: TestClient):
    """Verification failure in TutorService must trigger SAFETY_FALLBACK terminal state."""
    mock_bridge = MagicMock(spec=RemediationTutorBridge)
    mock_bridge.invoke_tutor_turn.return_value = TutorChatResponse(
        response_id="RESP-FB-E2E",
        session_id="SESS-FB-E2E",
        mode="misconception_diagnosis",
        message="Safety verification failed to confirm claims against evidence.",
        support_status="SAFE_FALLBACK",
        fallback_applied=True,
    )

    custom_controller = RemediationLoopController(
        bridge=mock_bridge,
        db_path=tmp_path / "e2e_safety.sqlite3",
    )
    configure_remediation_controller(custom_controller)

    try:
        resp = client.post(
            "/api/v1/remediation/start",
            json={"question_id": "UNI-RENAL-001", "selected_option": "B"},
            headers={"X-User-Id": "safety_learner"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_complete"] is True
        assert data["lifecycle_state"] == "COMPLETED"
        assert data["outcome"] == "SAFETY_FALLBACK"
        assert data["transfer_available"] is False
        assert data["remediation_status"] == "UNRESOLVED"
        assert data["remediation_status"] not in ("PROBING", "GUIDING", "CONFIRMING")
        assert "awaiting" not in data["timeline"]["transfer_result"].lower()
        assert data["timeline"]["transfer_result"] == "Remediation stopped safely; no transfer assessment performed."
        assert data["timeline"]["status"] == "SAFETY_FALLBACK"
        assert data["socratic_probe"] is None
        assert data["tutor_message"] == CANONICAL_SAFETY_FALLBACK_MESSAGE
        assert data["citations"] == []

        # Verify no transfer assessment is allowed
        t_resp = client.get(
            f"/api/v1/remediation/session/{data['session_id']}/transfer",
            headers={"X-User-Id": "safety_learner"},
        )
        assert t_resp.status_code == 422

        # Verify persisted session retrieval maintains coherent terminal fallback state
        get_sess = client.get(
            f"/api/v1/remediation/session/{data['session_id']}",
            headers={"X-User-Id": "safety_learner"},
        )
        assert get_sess.status_code == 200
        sess_data = get_sess.json()
        assert sess_data["is_complete"] is True
        assert sess_data["lifecycle_state"] == "COMPLETED"
        assert sess_data["outcome"] == "SAFETY_FALLBACK"
        assert sess_data["timeline"]["status"] == "SAFETY_FALLBACK"
        assert "awaiting" not in sess_data["timeline"]["transfer_result"].lower()
        assert sess_data["timeline"]["transfer_result"] == "Remediation stopped safely; no transfer assessment performed."
        assert sess_data["turns"][-1]["tutor_message"] == CANONICAL_SAFETY_FALLBACK_MESSAGE
        assert sess_data["turns"][-1]["socratic_probe"] is None
        assert sess_data["turns"][-1]["citations"] == []
    finally:
        configure_remediation_controller(None)
