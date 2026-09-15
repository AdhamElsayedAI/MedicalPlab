"""Tests for Adaptive API endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_get_adaptive_state_endpoint(client: TestClient):
    response = client.get("/api/v1/adaptive/state", headers={"X-User-Id": "test_api_learner"})
    assert response.status_code == 200
    data = response.json()
    assert data["learner_id"] == "test_api_learner"
    assert "total_attempts" in data
    assert "topic_mastery" in data
    assert "weak_topics" in data
    assert "recommendations" in data


def test_get_adaptive_recommendation_endpoint(client: TestClient):
    response = client.get("/api/v1/adaptive/recommendation", headers={"X-User-Id": "test_api_learner"})
    assert response.status_code == 200
    # Recommendation can be an object or null
    data = response.json()
    if data is not None:
        assert "action" in data
        assert "topic" in data
        assert "reason" in data


def test_record_adaptive_event_endpoint(client: TestClient):
    payload = {
        "event_type": "QUESTION_ATTEMPT",
        "subject": "Renal physiology",
        "topic": "RAAS mechanisms",
        "question_id": "UNI-RENAL-001",
        "selected_option": "B",
        "is_correct": False,
        "timestamp": 1700000000.0,
    }
    response = client.post(
        "/api/v1/adaptive/event",
        json=payload,
        headers={"X-User-Id": "test_event_learner"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["learner_id"] == "test_event_learner"
    assert data["total_attempts"] >= 1
    # Check that weakness or attempt was recorded
    assert "RAAS mechanisms" in data["topic_mastery"]
    assert data["topic_mastery"]["RAAS mechanisms"]["total_attempts"] >= 1


def test_trigger_adaptive_remediation_endpoint(client: TestClient):
    payload = {
        "topic": "RAAS mechanisms",
        "question_id": "UNI-RENAL-001",
        "preferred_mode": "socratic_hint",
    }
    response = client.post(
        "/api/v1/adaptive/remediate",
        json=payload,
        headers={"X-User-Id": "test_remediate_learner"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "response_id" in data
    assert "message" in data
    assert "verification" in data
    assert data["verification"]["unsupported_propositions"] == 0


def test_loop_status_endpoint(client: TestClient):
    response = client.get(
        "/api/v1/adaptive/loop-status?topic=RAAS%20mechanisms&baseline_mastery=beginner",
        headers={"X-User-Id": "test_loop_learner"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["learner_id"] == "test_loop_learner"
    assert data["topic"] == "RAAS mechanisms"
    assert "mastery_improved" in data
