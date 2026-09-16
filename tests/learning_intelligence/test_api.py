"""API integration tests for Phase 3 Learning Intelligence / Reasoning-Gap Radar."""
from __future__ import annotations

import pytest
from starlette.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)
def test_get_reasoning_gaps_demo_cohort_success(client):
    """GET /api/v1/learning-intelligence/reasoning-gaps returns 200 with valid demo radar."""
    response = client.get("/api/v1/learning-intelligence/reasoning-gaps?cohort_id=cohort_demo_renal_01")
    assert response.status_code == 200
    data = response.json()

    assert data["cohort_id"] == "cohort_demo_renal_01"
    assert data["is_demo_data"] is True
    assert data["sufficiency_status"] == "SUFFICIENT"
    assert data["min_cohort_n"] == 3
    assert data["total_eligible_learners"] == 13
    assert data["total_eligible_sessions"] == 13
    assert len(data["reasoning_gaps"]) == 3

    # Verify overall transfer effectiveness
    ote = data["overall_transfer_effectiveness"]
    assert ote["transfer_attempted_count"] == 13
    assert ote["assisted_excluded_count"] == 1
    assert ote["qualified_independent_transfer_count"] == 12  # 13 - 1
    assert ote["transfer_demonstrated_count"] == 9
    assert ote["transfer_not_demonstrated_count"] == 3
    assert ote["transfer_demonstration_rate"] == 0.75  # 9 / 12 = 75%

    # Verify SUB-01 transfer metrics
    sub_gap = next(g for g in data["reasoning_gaps"] if g["pattern_id"] == "PATTERN-RAAS-SUB-01")
    assert sub_gap["unique_learners_count"] == 6
    assert sub_gap["pattern_learner_count"] == 6
    st = sub_gap["transfer_metrics"]
    assert st["transfer_attempted_count"] == 6
    assert st["assisted_excluded_count"] == 1
    assert st["qualified_independent_transfer_count"] == 5
    assert st["transfer_demonstrated_count"] == 4
    assert st["transfer_not_demonstrated_count"] == 1
    assert st["transfer_demonstration_rate"] == 0.8  # 4 / 5 = 80%

    # Verify no learner identities in response
    resp_text = response.text
    for i in range(1, 15):
        assert f"demo_learner_{i:03d}" not in resp_text


def test_caller_cannot_override_or_lower_min_cohort_n(client):
    """Invariant: Caller supplying min_cohort_n query parameter cannot lower privacy threshold."""
    # Attempting to supply min_cohort_n=1 via query param must be ignored
    response = client.get("/api/v1/learning-intelligence/reasoning-gaps?cohort_id=cohort_demo_renal_01&min_cohort_n=1")
    assert response.status_code == 200
    data = response.json()
    assert data["min_cohort_n"] == 3  # Remains strictly 3 server-side


def test_server_side_small_n_privacy_suppression(client, monkeypatch):
    """Invariant: Server-side MIN_COHORT_N config suppresses cohort when learners < threshold."""
    monkeypatch.setenv("MEDICALPLAB_PHASE_3_MIN_COHORT_N", "20")
    response = client.get("/api/v1/learning-intelligence/reasoning-gaps?cohort_id=cohort_demo_renal_01")
    assert response.status_code == 200
    data = response.json()
    assert data["sufficiency_status"] == "INSUFFICIENT_COHORT_DATA"
    assert data["min_cohort_n"] == 20
    assert data["reasoning_gaps"] == []
    assert data["total_eligible_learners"] == 13


def test_unknown_cohort_rejected_with_404(client):
    """Invariant: Arbitrary unknown cohort_id must be rejected safely with HTTP 404."""
    response = client.get("/api/v1/learning-intelligence/reasoning-gaps?cohort_id=unknown_cohort_999")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "not a registered cohort" in detail or "unknown_cohort_999" in detail


def test_demo_cohort_isolation_in_production(client, monkeypatch):
    """Invariant: Demo cohort is blocked (403) in production runtime unless explicitly enabled."""
    # 1. In production runtime without demo enablement -> 403 Forbidden
    monkeypatch.setenv("MEDICALPLAB_RUNTIME_MODE", "production")
    monkeypatch.delenv("MEDICALPLAB_PHASE_3_DEMO_ENABLED", raising=False)
    response = client.get("/api/v1/learning-intelligence/reasoning-gaps?cohort_id=cohort_demo_renal_01")
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"]

    # 2. In production runtime with explicit MEDICALPLAB_PHASE_3_DEMO_ENABLED=true -> 200 OK
    monkeypatch.setenv("MEDICALPLAB_PHASE_3_DEMO_ENABLED", "true")
    response_enabled = client.get("/api/v1/learning-intelligence/reasoning-gaps?cohort_id=cohort_demo_renal_01")
    assert response_enabled.status_code == 200
    assert response_enabled.json()["is_demo_data"] is True


def test_get_reasoning_gaps_topic_filter(client):
    """GET /api/v1/learning-intelligence/reasoning-gaps with topic filter."""
    response = client.get("/api/v1/learning-intelligence/reasoning-gaps?cohort_id=cohort_demo_renal_01&topic=preclinical_renal")
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "preclinical_renal"
    assert data["total_eligible_learners"] == 13
