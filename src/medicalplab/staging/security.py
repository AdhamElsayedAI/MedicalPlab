"""MedicalPlab Direct Staging Security Middleware.

Enforces zero-cost staging access control directly within FastAPI when deployed
on single-service platforms (such as Render Free Web Service) without a separate BFF gateway.

Responsibilities:
1. Feature Flag: MEDICALPLAB_STAGING_GATE_ENABLED=1 enables access control.
   When disabled (0), normal application behavior is preserved completely unchanged.
2. Startup Safety: Fails closed (RuntimeError) if gate is enabled but STAGING_ACCESS_KEY is missing.
3. Public Health: GET /health is permitted without key for Render platform health checks.
4. Route Allow-list: Restricts internet traffic to frozen contract endpoints; blocks /internal/* and /docs.
5. Key Verification: Requires valid X-Staging-Key using constant-time comparison.
6. Header Preservation: Preserves X-User-Id / X-Learner-Id and X-Request-Id.
7. Payload Protection: Enforces 1 MB body limit and method allow-list.
"""
from __future__ import annotations

import logging
import os
import secrets
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("medicalplab.staging.security")

# Constants
MAX_BODY_BYTES = 1024 * 1024  # 1 MB
ALLOWED_METHODS = {"GET", "POST", "HEAD", "OPTIONS"}

EXACT_ALLOWED_PATHS = {
    "/ready",
    "/api/v1/version",
    "/api/v1/tutor/chat",
    "/api/v1/learner/progress",
    "/api/v1/progress",
}

PREFIX_ALLOWED_PATHS = (
    "/api/v1/university/",
    "/api/v1/adaptive/",
    "/api/v1/remediation/",
    "/api/v1/anatomy/",
    "/api/v1/plab/",
)


def is_staging_gate_enabled() -> bool:
    """Check if the direct staging access gate is active."""
    return os.environ.get("MEDICALPLAB_STAGING_GATE_ENABLED", "0").strip().lower() in {"1", "true", "yes"}


def get_staging_access_key() -> str:
    """Read the configured staging secret key."""
    return os.environ.get("STAGING_ACCESS_KEY", "").strip()


def validate_staging_configuration() -> None:
    """Fail closed at application startup if staging gate is active but secret is missing."""
    if is_staging_gate_enabled():
        key = get_staging_access_key()
        if not key:
            raise RuntimeError(
                "Fatal: STAGING_ACCESS_KEY environment variable is required when "
                "MEDICALPLAB_STAGING_GATE_ENABLED is enabled. Server startup aborted."
            )


def is_path_allowlisted(path: str) -> bool:
    """Check if the requested path belongs to the frozen contract endpoints."""
    if path in EXACT_ALLOWED_PATHS:
        return True
    for prefix in PREFIX_ALLOWED_PATHS:
        if path.startswith(prefix) or path == prefix.rstrip("/"):
            return True
    return False


class StagingSecurityMiddleware(BaseHTTPMiddleware):
    """Direct ASGI security middleware for MedicalPlab Staging on Render."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # If staging gate is not enabled, pass through transparently
        if not is_staging_gate_enabled():
            return await call_next(request)

        path = "/" + request.url.path.lstrip("/")

        # 1. Public Health Route (Render Platform Health Check Probe)
        if path == "/health" and request.method in {"GET", "HEAD"}:
            return await call_next(request)

        # 2. Block Documentation & Schema Endpoints from Public Internet Staging
        if path in {"/docs", "/redoc", "/openapi.json"} or path.startswith(("/docs/", "/redoc/")):
            return JSONResponse(
                status_code=403,
                content={"detail": "API documentation and schema endpoints are disabled in staging environment."},
            )

        # 3. Block Internal Review / Admin Endpoints
        if path == "/internal" or path.startswith("/internal/"):
            return JSONResponse(
                status_code=403,
                content={"detail": "Access to internal endpoints is forbidden on staging gateway."},
            )

        # 4. Method Allow-List & CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.method not in ALLOWED_METHODS:
            return JSONResponse(
                status_code=405,
                content={"detail": f"Method '{request.method}' not allowed on staging gateway."},
            )

        # 5. Staging Access Key Gate (Constant-Time Verification)
        client_key = request.headers.get("x-staging-key") or request.headers.get("X-Staging-Key")
        configured_key = get_staging_access_key()
        if not client_key or not secrets.compare_digest(client_key, configured_key):
            logger.warning("Rejected unauthorized staging access to %s: invalid or missing X-Staging-Key", path)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing staging access key."},
                headers={"WWW-Authenticate": "X-Staging-Key"},
            )

        # 6. Route Allow-List Check
        if not is_path_allowlisted(path):
            return JSONResponse(
                status_code=404,
                content={"detail": "Route not allowed on staging gateway."},
            )

        # 7. Payload Size Protection
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_BODY_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"Payload exceeds size limit of {MAX_BODY_BYTES} bytes."},
                    )
            except ValueError:
                pass

        # 8. Request ID Tracking
        request_id = request.headers.get("x-request-id") or f"req-{uuid.uuid4().hex[:12]}"

        response: Response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
