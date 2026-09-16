"""Tests for Independent Transfer Assessment Service and Endpoints."""
import pytest
from fastapi.testclient import TestClient

from main import app
from medicalplab.remediation.models import RemediationOutcome
from medicalplab.remediation.transfer import TransferAssessmentService


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_transfer_service_eligible_selection():
    service = TransferAssessmentService()

    item = service.get_eligible_transfer_item("UNI-RENAL-001")
    assert item is not None
    assert item.question_id == "UNI-RENAL-001-T"
    assert item.topic == "RAAS mechanisms"
    assert "A" in item.options

    # Verify zero answer leakage
    item_dict = item.model_dump()
    assert "correct_answer" not in item_dict
    assert "explanation" not in item_dict


def test_transfer_service_exposure_exclusion():
    service = TransferAssessmentService()

    # If the transfer item is already exposed, it must be excluded
    item = service.get_eligible_transfer_item(
        original_question_id="UNI-RENAL-001",
        exposed_item_ids=["UNI-RENAL-001-T"],
    )
    assert item is None


def test_transfer_service_unassisted_scoring():
    service = TransferAssessmentService()

    # Correct submission: Option A
    outcome_correct, attempt_c, exp_c, cit_c = service.score_transfer_submission(
        original_question_id="UNI-RENAL-001",
        question_id="UNI-RENAL-001-T",
        selected_option="A",
        was_assisted=False,
    )
    assert outcome_correct == RemediationOutcome.TRANSFER_CONFIRMED
    assert attempt_c.is_correct is True
    assert attempt_c.was_assisted is False
    assert len(cit_c) > 0

    # Incorrect submission: Option B
    outcome_inc, attempt_i, exp_i, cit_i = service.score_transfer_submission(
        original_question_id="UNI-RENAL-001",
        question_id="UNI-RENAL-001-T",
        selected_option="B",
        was_assisted=False,
    )
    assert outcome_inc == RemediationOutcome.TRANSFER_NOT_CONFIRMED
    assert attempt_i.is_correct is False


def test_transfer_service_assisted_disqualification():
    """INVARIANT: Assisted success cannot confirm independent transfer."""
    service = TransferAssessmentService()

    # Correct answer but marked assisted
    outcome, attempt, exp, cit = service.score_transfer_submission(
        original_question_id="UNI-RENAL-001",
        question_id="UNI-RENAL-001-T",
        selected_option="A",
        was_assisted=True,
    )
    # Must yield UNRESOLVED, not TRANSFER_CONFIRMED
    assert outcome == RemediationOutcome.UNRESOLVED
    assert attempt.is_correct is True
    assert attempt.was_assisted is True


def test_full_remediation_and_transfer_api_flow(client: TestClient):
    user_id = "test_e2e_student_transfer"

    # 1. Start session (Turn 1)
    s_resp = client.post(
        "/api/v1/remediation/start",
        json={"question_id": "UNI-RENAL-001", "selected_option": "B"},
        headers={"X-User-Id": user_id},
    )
    assert s_resp.status_code == 200
    session_id = s_resp.json()["session_id"]

    # 2. Advance to Turn 2
    t2_resp = client.post(
        "/api/v1/remediation/turn",
        json={"session_id": session_id, "student_message": "Renin acts first."},
        headers={"X-User-Id": user_id},
    )
    assert t2_resp.status_code == 200

    # 3. Advance to Turn 3 (Transitions to AWAITING_TRANSFER)
    t3_resp = client.post(
        "/api/v1/remediation/turn",
        json={"session_id": session_id, "student_message": "Renin cleaves angiotensinogen into Ang I."},
        headers={"X-User-Id": user_id},
    )
    assert t3_resp.status_code == 200
    assert t3_resp.json()["lifecycle_state"] == "AWAITING_TRANSFER"
    assert t3_resp.json()["transfer_available"] is True

    # 4. Fetch independent transfer item
    t_item_resp = client.get(
        f"/api/v1/remediation/session/{session_id}/transfer",
        headers={"X-User-Id": user_id},
    )
    assert t_item_resp.status_code == 200
    t_item = t_item_resp.json()
    assert t_item["question_id"] == "UNI-RENAL-001-T"
    assert "correct_answer" not in t_item

    # 5. Submit correct transfer answer
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
    assert "Transfer demonstrated" in sub_data["timeline"]["transfer_result"]
    assert sub_data["timeline"]["status"] == "COMPLETED"
    assert sub_data["timeline"]["next_recommendation"] is not None
