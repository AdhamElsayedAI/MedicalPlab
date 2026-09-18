"""Unit tests for MedicalPlab Staging BFF Gateway.

Verifies:
1. Invalid or missing X-Staging-Key is rejected (HTTP 401)
2. Valid X-Staging-Key is accepted (proxied to backend)
3. Disallowed routes are rejected (HTTP 404)
4. Internal routes (/internal/*) are forbidden (HTTP 403)
5. Method allow-list enforcement (HTTP 405)
6. Body size limit enforcement (>1MB -> HTTP 413)
7. Client Authorization header is stripped and replaced with Google IAM token
8. X-User-Id and X-Request-Id are forwarded unchanged
9. Backend status codes, content-types, and bodies are preserved
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

# Ensure staging is in python path
staging_path = Path(__file__).resolve().parent.parent.parent / "staging"
if str(staging_path) not in sys.path:
    sys.path.insert(0, str(staging_path))

os.environ["STAGING_ACCESS_KEY"] = "test-secret-staging-key-12345"
os.environ["DEV_MOCK_AUTH"] = "1"
os.environ["BACKEND_SERVICE_URL"] = "http://internal-fastapi:8080"

from bff.main import app, STAGING_ACCESS_KEY


@pytest.fixture
def mock_backend():
    """Fixture providing a mock AsyncClient."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    # Default backend response
    mock_client.request.return_value = httpx.Response(
        status_code=200,
        json={"status": "ok", "service": "medicalplab-api"},
        headers={"content-type": "application/json", "x-request-id": "req-backend-1"},
    )
    return mock_client


@pytest.fixture
def client(mock_backend):
    app.state.http_client = mock_backend
    with TestClient(app) as test_client:
        app.state.http_client = mock_backend
        yield test_client
    app.state.http_client = None


def test_missing_staging_key_denied(client, mock_backend):
    """Requests missing X-Staging-Key must return 401 Unauthorized."""
    response = client.get("/health")
    assert response.status_code == 401
    assert "Invalid or missing" in response.json()["detail"]
    mock_backend.request.assert_not_called()


def test_invalid_staging_key_denied(client, mock_backend):
    """Requests with incorrect X-Staging-Key must return 401 Unauthorized."""
    response = client.get(
        "/health",
        headers={"X-Staging-Key": "wrong-key-value"},
    )
    assert response.status_code == 401
    assert "Invalid or missing" in response.json()["detail"]
    mock_backend.request.assert_not_called()


def test_valid_staging_key_accepted(client, mock_backend):
    """Requests with correct X-Staging-Key must pass the gate and reach backend."""
    response = client.get(
        "/health",
        headers={"X-Staging-Key": STAGING_ACCESS_KEY},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert mock_backend.request.call_count == 1
    call_args = mock_backend.request.call_args
    assert call_args.kwargs["method"] == "GET"
    assert "http://internal-fastapi:8080/health" in call_args.kwargs["url"]


def test_disallowed_route_rejected(client, mock_backend):
    """Routes outside the contract allow-list must return 404."""
    response = client.get(
        "/unknown/admin/path",
        headers={"X-Staging-Key": STAGING_ACCESS_KEY},
    )
    assert response.status_code == 404
    assert "Route not allowed" in response.json()["detail"]
    mock_backend.request.assert_not_called()


def test_internal_route_forbidden(client, mock_backend):
    """Routes under /internal/* must return 403 Forbidden."""
    for path in ["/internal", "/internal/review", "/internal/eval"]:
        response = client.get(
            path,
            headers={"X-Staging-Key": STAGING_ACCESS_KEY},
        )
        assert response.status_code == 403, f"Expected 403 for {path}, got {response.status_code}"
        assert "forbidden" in response.json()["detail"].lower()
    mock_backend.request.assert_not_called()


def test_allowed_contract_prefixes(client, mock_backend):
    """Verify all allowed contract prefixes pass the path check."""
    allowed_endpoints = [
        "/ready",
        "/api/v1/version",
        "/api/v1/university/subjects",
        "/api/v1/adaptive/state",
        "/api/v1/remediation/start",
        "/api/v1/tutor/chat",
        "/api/v1/anatomy/session",
        "/api/v1/learner/progress",
        "/api/v1/plab/preview",
    ]
    for ep in allowed_endpoints:
        response = client.get(
            ep,
            headers={"X-Staging-Key": STAGING_ACCESS_KEY},
        )
        assert response.status_code == 200, f"Expected 200 for {ep}, got {response.status_code}"


def test_disallowed_method_rejected(client, mock_backend):
    """Methods outside GET/POST/HEAD/OPTIONS must return 405 Method Not Allowed."""
    response = client.delete(
        "/api/v1/learner/progress",
        headers={"X-Staging-Key": STAGING_ACCESS_KEY},
    )
    assert response.status_code == 405
    assert "Method 'DELETE' not allowed" in response.json()["detail"]
    mock_backend.request.assert_not_called()


def test_incoming_authorization_stripped_and_minted(client, mock_backend):
    """Client Authorization header must be stripped; Google IAM token attached."""
    response = client.get(
        "/health",
        headers={
            "X-Staging-Key": STAGING_ACCESS_KEY,
            "Authorization": "Bearer rogue-attacker-token-12345",
        },
    )
    assert response.status_code == 200
    call_args = mock_backend.request.call_args
    sent_headers = call_args.kwargs["headers"]
    # Verify the rogue client token was NOT forwarded
    assert sent_headers.get("authorization") != "Bearer rogue-attacker-token-12345"
    # With DEV_MOCK_AUTH=1, it should be the minted mock token
    assert sent_headers.get("authorization") == "Bearer mock-dev-token"


def test_x_user_id_forwarded_unchanged(client, mock_backend):
    """X-User-Id header must be forwarded untouched to the backend."""
    response = client.get(
        "/api/v1/learner/progress",
        headers={
            "X-Staging-Key": STAGING_ACCESS_KEY,
            "X-User-Id": "learner-synthetic-uuid-42",
        },
    )
    assert response.status_code == 200
    call_args = mock_backend.request.call_args
    sent_headers = call_args.kwargs["headers"]
    assert sent_headers.get("x-user-id") == "learner-synthetic-uuid-42"


def test_backend_status_codes_preserved(client, mock_backend):
    """BFF must faithfully pass through backend status codes (404, 422, 500)."""
    for code in [404, 422, 500]:
        mock_backend.request.return_value = httpx.Response(
            status_code=code,
            json={"error": f"Simulated backend error {code}"},
            headers={"content-type": "application/json"},
        )
        response = client.post(
            "/api/v1/tutor/chat",
            headers={"X-Staging-Key": STAGING_ACCESS_KEY},
            json={"query": "test query"},
        )
        assert response.status_code == code
        assert response.json()["error"] == f"Simulated backend error {code}"


def test_body_size_limit_enforced(client, mock_backend):
    """Requests exceeding 1MB must be rejected with 413 Request Entity Too Large."""
    # 1MB + 10 bytes
    large_payload = "a" * (1024 * 1024 + 10)
    response = client.post(
        "/api/v1/tutor/chat",
        headers={
            "X-Staging-Key": STAGING_ACCESS_KEY,
            "Content-Type": "text/plain",
        },
        content=large_payload,
    )
    assert response.status_code == 413
    assert "Payload exceeds size limit" in response.json()["detail"]
    mock_backend.request.assert_not_called()


def test_missing_staging_key_fails_closed_in_production():
    """When DEV_MOCK_AUTH is disabled, an empty STAGING_ACCESS_KEY must fail startup."""
    import importlib
    import bff.main
    with patch.dict(os.environ, {"DEV_MOCK_AUTH": "0", "STAGING_ACCESS_KEY": ""}):
        with pytest.raises(RuntimeError) as exc_info:
            importlib.reload(bff.main)
        assert "STAGING_ACCESS_KEY environment variable is required" in str(exc_info.value)
    # Restore normal module state
    with patch.dict(os.environ, {"DEV_MOCK_AUTH": "1", "STAGING_ACCESS_KEY": STAGING_ACCESS_KEY}):
        importlib.reload(bff.main)

