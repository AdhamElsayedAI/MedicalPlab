"""Tests for Remediation API endpoints and lifecycle routes."""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_api_start_remediation(client: TestClient):
    payload = {
        "question_id": "UNI-RENAL-001",
        "selected_option": "B",
        "topic": "RAAS mechanisms",
    }
    response = client.post(
        "/api/v1/remediation/start",
        json=payload,
        headers={"X-User-Id": "test_api_student_01"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["session_id"].startswith("REM-")
    assert data["turn_number"] == 1
    assert data["max_turns"] == 3
    assert data["is_complete"] is False
    assert data["lifecycle_state"] == "REMEDIATING"
    assert data["remediation_status"] == "PROBING"
    assert data["pattern_id"] == "PATTERN-RAAS-SUB-01"
    assert "timeline" in data
    assert data["timeline"]["status"] == "IN_PROGRESS"
    assert data["tutor_message"]
    assert data["socratic_probe"]
    assert data["transfer_available"] is False


def test_api_advance_turn_lifecycle(client: TestClient):
    user_id = "test_api_student_02"

    # 1. Start session
    start_resp = client.post(
        "/api/v1/remediation/start",
        json={
            "question_id": "UNI-RENAL-001",
            "selected_option": "B",
            "topic": "RAAS mechanisms",
        },
        headers={"X-User-Id": user_id},
    )
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]

    # 2. Advance to Turn 2 (Guide)
    turn2_resp = client.post(
        "/api/v1/remediation/turn",
        json={
            "session_id": session_id,
            "student_message": "Renin acts at the beginning of the cascade on angiotensinogen.",
        },
        headers={"X-User-Id": user_id},
    )
    assert turn2_resp.status_code == 200
    data2 = turn2_resp.json()
    assert data2["turn_number"] == 2
    assert data2["is_complete"] is False
    assert data2["lifecycle_state"] == "REMEDIATING"
    assert data2["remediation_status"] == "GUIDING"

    # 3. Advance to Turn 3 (Consolidate -> Awaiting Transfer)
    turn3_resp = client.post(
        "/api/v1/remediation/turn",
        json={
            "session_id": session_id,
            "student_message": "Renin cleaves angiotensinogen to Ang I, and ACE cleaves Ang I to Ang II.",
        },
        headers={"X-User-Id": user_id},
    )
    assert turn3_resp.status_code == 200
    data3 = turn3_resp.json()
    assert data3["turn_number"] == 3
    assert data3["lifecycle_state"] == "AWAITING_TRANSFER"
    assert data3["transfer_available"] is True
    assert data3["timeline"]["status"] == "AWAITING_TRANSFER"

    # 4. GET session inspection
    get_resp = client.get(
        f"/api/v1/remediation/session/{session_id}",
        headers={"X-User-Id": user_id},
    )
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["session_id"] == session_id
    assert get_data["turn_number"] == 3
    assert get_data["lifecycle_state"] == "AWAITING_TRANSFER"
    assert len(get_data["turns"]) == 3


def test_api_abandon_session(client: TestClient):
    user_id = "test_api_student_abandon"
    start_resp = client.post(
        "/api/v1/remediation/start",
        json={
            "question_id": "UNI-RENAL-001",
            "selected_option": "B",
        },
        headers={"X-User-Id": user_id},
    )
    session_id = start_resp.json()["session_id"]

    abandon_resp = client.post(
        f"/api/v1/remediation/session/{session_id}/abandon",
        headers={"X-User-Id": user_id},
    )
    assert abandon_resp.status_code == 200
    data = abandon_resp.json()
    assert data["is_complete"] is True
    assert data["lifecycle_state"] == "COMPLETED"
    assert data["outcome"] == "ABANDONED"


def test_api_invalid_session_returns_404(client: TestClient):
    response = client.post(
        "/api/v1/remediation/turn",
        json={
            "session_id": "REM-NONEXISTENT",
            "student_message": "Test message",
        },
        headers={"X-User-Id": "test_user"},
    )
    assert response.status_code == 404
