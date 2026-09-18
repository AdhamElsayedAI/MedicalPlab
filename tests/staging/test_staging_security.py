"""Automated security gate tests for MedicalPlab Direct Staging (Render Free).

Verifies the 10 critical staging gate invariants:
1. GET /health without staging key = 200 (Public Render health check)
2. GET /api/v1/version without key = 401 Unauthorized
3. Invalid X-Staging-Key = 401 Unauthorized
4. Valid X-Staging-Key = request reaches backend route (200 OK)
5. /internal/* = 403 Forbidden even with valid key
6. /docs and /redoc = 403 Forbidden
7. /openapi.json = 403 Forbidden
8. X-User-Id reaches application unchanged
9. Missing STAGING_ACCESS_KEY while staging gate enabled = startup failure (fail-closed)
10. Staging gate disabled = existing product contract remains completely unchanged
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure baseline environment for test imports
TEST_STAGING_KEY = "render-staging-test-key-2026-sec"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://localhost:8000"
os.environ["MEDICALPLAB_RUNTIME_MODE"] = "pilot"
os.environ["MEDICALPLAB_PLAB_PREVIEW_QA"] = "1"
os.environ["MEDICALPLAB_PHASE_2B_ENABLED"] = "1"
os.environ["MEDICALPLAB_ANATOMY_3D_ENABLED"] = "1"
os.environ["MEDICALPLAB_STAGING_GATE_ENABLED"] = "1"
os.environ["STAGING_ACCESS_KEY"] = TEST_STAGING_KEY

from medicalplab.staging.security import (
    validate_staging_configuration,
    is_staging_gate_enabled,
    get_staging_access_key,
    is_path_allowlisted,
)
from production_main import app


@pytest.fixture
def staging_client():
    """Client configured with staging gate enabled."""
    with patch.dict(
        os.environ,
        {
            "MEDICALPLAB_STAGING_GATE_ENABLED": "1",
            "STAGING_ACCESS_KEY": TEST_STAGING_KEY,
        },
    ):
        with TestClient(app) as client:
            yield client


@pytest.fixture
def open_client():
    """Client configured with staging gate disabled (standard direct access)."""
    with patch.dict(
        os.environ,
        {
            "MEDICALPLAB_STAGING_GATE_ENABLED": "0",
            "STAGING_ACCESS_KEY": "",
        },
    ):
        with TestClient(app) as client:
            yield client


# Invariant 1: Public Health Route
def test_public_health_without_key(staging_client):
    """GET /health must return 200 without any staging key (Render platform probe)."""
    response = staging_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["runtime_mode"] == "pilot"


# Invariant 2: Version without key rejected
def test_version_without_staging_key_rejected(staging_client):
    """GET /api/v1/version without X-Staging-Key must be rejected with 401."""
    response = staging_client.get("/api/v1/version")
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    assert response.json()["detail"] == "Invalid or missing staging access key."


# Invariant 3: Invalid key rejected
def test_invalid_staging_key_rejected(staging_client):
    """Requests with incorrect X-Staging-Key must return 401."""
    response = staging_client.get(
        "/api/v1/version",
        headers={"X-Staging-Key": "wrong-key-value"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing staging access key."


# Invariant 4: Valid key reaches backend route
def test_valid_staging_key_accepted(staging_client):
    """Requests with valid X-Staging-Key must reach the protected backend route."""
    response = staging_client.get(
        "/api/v1/version",
        headers={"X-Staging-Key": TEST_STAGING_KEY},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "MedicalPlab Product API"
    assert data["api_version"] == "v1"
    assert "x-request-id" in response.headers


# Invariant 5: Internal routes blocked
def test_internal_routes_blocked_even_with_valid_key(staging_client):
    """Internal routes (/internal/*) must return 403 Forbidden even with a valid key."""
    routes = ["/internal", "/internal/audit", "/internal/review/status"]
    for route in routes:
        response = staging_client.get(
            route,
            headers={"X-Staging-Key": TEST_STAGING_KEY},
        )
        assert response.status_code == 403
        assert "internal endpoints is forbidden" in response.json()["detail"]


# Invariant 6: Docs and redoc blocked
def test_docs_and_redoc_blocked(staging_client):
    """Documentation endpoints (/docs, /redoc) must return 403 Forbidden."""
    for path in ["/docs", "/redoc", "/docs/oauth2-redirect"]:
        response = staging_client.get(
            path,
            headers={"X-Staging-Key": TEST_STAGING_KEY},
        )
        assert response.status_code == 403
        assert "documentation and schema endpoints are disabled" in response.json()["detail"]


# Invariant 7: Schema endpoints blocked
def test_openapi_schema_blocked(staging_client):
    """OpenAPI schema endpoint (/openapi.json) must return 403 Forbidden."""
    response = staging_client.get(
        "/openapi.json",
        headers={"X-Staging-Key": TEST_STAGING_KEY},
    )
    assert response.status_code == 403
    assert "documentation and schema endpoints are disabled" in response.json()["detail"]


# Invariant 8: X-User-Id reaches application unchanged
def test_user_id_forwarded_unchanged(staging_client):
    """X-User-Id / X-Learner-Id must be received by application routes unchanged."""
    test_user_id = "synthetic-learner-render-smoke-42"
    response = staging_client.get(
        "/api/v1/progress",
        headers={
            "X-Staging-Key": TEST_STAGING_KEY,
            "X-User-Id": test_user_id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["learner_id"] == test_user_id


# Invariant 9: Missing secret while gate enabled fails closed
def test_missing_staging_key_fails_closed():
    """Startup validation must raise RuntimeError when staging gate is enabled without key."""
    with patch.dict(
        os.environ,
        {
            "MEDICALPLAB_STAGING_GATE_ENABLED": "1",
            "STAGING_ACCESS_KEY": "",
        },
    ):
        with pytest.raises(RuntimeError) as exc_info:
            validate_staging_configuration()
        assert "STAGING_ACCESS_KEY environment variable is required" in str(exc_info.value)


def test_missing_staging_key_env_unset_fails_closed():
    """Startup validation must raise RuntimeError when STAGING_ACCESS_KEY is absent."""
    with patch.dict(
        os.environ,
        {"MEDICALPLAB_STAGING_GATE_ENABLED": "1"},
        clear=False,
    ):
        if "STAGING_ACCESS_KEY" in os.environ:
            del os.environ["STAGING_ACCESS_KEY"]
        with pytest.raises(RuntimeError) as exc_info:
            validate_staging_configuration()
        assert "STAGING_ACCESS_KEY environment variable is required" in str(exc_info.value)


# Invariant 10: Gate disabled behaves transparently
def test_gate_disabled_leaves_contract_unchanged(open_client):
    """When MEDICALPLAB_STAGING_GATE_ENABLED=0, requests succeed without X-Staging-Key."""
    response = open_client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "MedicalPlab Product API"


# Additional safety tests
def test_unknown_routes_return_404_with_valid_key(staging_client):
    """Unknown or non-allowlisted routes return 404 even with valid key."""
    response = staging_client.get(
        "/api/v1/nonexistent/route",
        headers={"X-Staging-Key": TEST_STAGING_KEY},
    )
    assert response.status_code == 404
    assert "Route not allowed" in response.json()["detail"]


def test_disallowed_methods_return_405(staging_client):
    """Disallowed HTTP methods return 405 on the staging gateway."""
    response = staging_client.delete(
        "/api/v1/version",
        headers={"X-Staging-Key": TEST_STAGING_KEY},
    )
    assert response.status_code == 405
    assert "Method 'DELETE' not allowed" in response.json()["detail"]


def test_cors_preflight_options(staging_client):
    """CORS preflight OPTIONS requests are allowed through to CORS middleware."""
    response = staging_client.options(
        "/api/v1/version",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Staging-Key,X-User-Id",
        },
    )
    assert response.status_code in {200, 204}


def test_oversized_payload_rejected(staging_client):
    """Payloads exceeding 1MB limit return 413 Payload Too Large."""
    oversized_headers = {
        "X-Staging-Key": TEST_STAGING_KEY,
        "Content-Length": str(2 * 1024 * 1024),
    }
    response = staging_client.post(
        "/api/v1/tutor/chat",
        headers=oversized_headers,
        content=b"x",
    )
    assert response.status_code == 413
    assert "Payload exceeds size limit" in response.json()["detail"]
