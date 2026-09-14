"""Test suite for MedicalPlab Production Cloud FastAPI backend."""

from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

import main
from medicalplab.evidence_engine.service import CanonicalEvidenceEngine


class _DirectSupportModel:
    """Deterministic endpoint-test double for a strong reranker decision."""

    def predict(self, pairs, **kwargs):
        return np.full(len(pairs), 8.0, dtype=np.float32)


@pytest.fixture
def client():
    return TestClient(main.app)


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


def test_ai_chat_supported_renal_query(client, monkeypatch):
    """Verify a supported query traverses the canonical evidence engine."""
    engine = CanonicalEvidenceEngine(data_root=Path(__file__).resolve().parents[1] / "Data")
    engine.reranker.model = _DirectSupportModel()
    engine.reranker.is_degraded = False
    monkeypatch.setattr(main, "_evidence_engine", engine)
    response = client.post(
        "/ai/chat",
        json={"query": "What evidence describes 1.1. RAAS in relation to aldosterone?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "explanation" in data
    assert "citations" in data
    assert len(data["citations"]) == 1
    assert data["safety_validated"] is True
    assert data["abstain"] is False
    assert "RAAS" in data["explanation"] or "aldosterone" in data["explanation"].lower()


def test_ai_chat_unsupported_pregnancy_abstains(client, monkeypatch):
    """Verify an unsupported high-risk query has no hard-coded bypass."""
    engine = CanonicalEvidenceEngine(data_root=Path(__file__).resolve().parents[1] / "Data")
    engine.reranker.is_degraded = True
    monkeypatch.setattr(main, "_evidence_engine", engine)
    response = client.post(
        "/ai/chat",
        json={"query": "Can I give an ACE inhibitor to a pregnant patient?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "abstain"
    assert data["abstain"] is True
    assert data["citations"] == []


def test_ai_chat_unsupported_nitrates_abstains(client, monkeypatch):
    """Verify unsupported emergency guidance fails closed without prose."""
    engine = CanonicalEvidenceEngine(data_root=Path(__file__).resolve().parents[1] / "Data")
    engine.reranker.is_degraded = True
    monkeypatch.setattr(main, "_evidence_engine", engine)
    response = client.post(
        "/ai/chat",
        json={"query": "Should I administer nitrates in acute inferior STEMI with RV involvement?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "abstain"
    assert data["abstain"] is True
    assert data["citations"] == []


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
