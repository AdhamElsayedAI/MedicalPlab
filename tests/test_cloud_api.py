"""Test suite for MedicalPlab Production Cloud FastAPI backend."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check_endpoint(client):
    """Verify health endpoint returns 200 and expected schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "MedicalPlab API"


def test_root_endpoint(client):
    """Verify root discovery endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "MedicalPlab" in data["service"]


def test_ai_chat_stemi_query(client):
    """Verify AI tutor returns clinical reasoning and NICE citations."""
    response = client.post(
        "/ai/chat",
        json={"query": "What is the revascularisation window for STEMI under NICE guidelines?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "citations" in data
    assert len(data["citations"]) > 0
    assert data["safety_validated"] is True
    assert "PCI" in data["explanation"] or "coronary" in data["explanation"].lower()


def test_ai_chat_safety_interception_pregnancy(client):
    """Verify safety interceptor blocks ACE inhibitors in pregnancy."""
    response = client.post(
        "/ai/chat",
        json={"query": "Can I give an ACE inhibitor to a pregnant patient?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "safety_interception"
    assert data["interception_triggered"] is True
    assert "contraindicated" in data["explanation"].lower()
    assert "CG127" in data["explanation"]


def test_ai_chat_safety_interception_nitrates(client):
    """Verify safety interceptor blocks nitrates in RV STEMI."""
    response = client.post(
        "/ai/chat",
        json={"query": "Should I administer nitrates in acute inferior STEMI with RV involvement?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "safety_interception"
    assert data["interception_triggered"] is True
    assert "contraindicated" in data["explanation"].lower()


def test_student_analytics_endpoint(client):
    """Verify student analytics endpoint returns Bayesian tracking."""
    response = client.get(
        "/student/analytics",
        headers={"X-User-Id": "user_alice", "X-Tenant-Id": "tenant_nhs_demo"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "student_id" in data
    assert "total_attempts" in data
    assert "overall_accuracy" in data


def test_student_attempts_endpoint(client):
    """Verify recording student attempt updates state."""
    response = client.post(
        "/student/attempts",
        json={"topic": "Cardiology", "is_correct": True, "time_spent_seconds": 25.0},
        headers={"X-User-Id": "user_alice", "X-Tenant-Id": "tenant_nhs_demo"},
    )
    assert response.status_code in (200, 201)
    data = response.json()
    assert "attempt_id" in data


def test_cors_headers(client):
    """Verify CORS headers are present on preflight options."""
    response = client.options(
        "/health",
        headers={
            "Origin": "https://medical-plab.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
