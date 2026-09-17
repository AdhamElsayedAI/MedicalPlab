"""MedicalPlab Staging BFF (Backend-For-Frontend) Security Gateway.

Transport and security infrastructure only.
Zero medical business logic. Zero domain imports.

Responsibilities:
1. Staging Access Gate: Validates X-Staging-Key using constant-time comparison.
2. Route & Method Allow-list: Restricts to frozen contract endpoints; blocks /internal/*.
3. Payload Size Limit: Enforces 1MB max body limit.
4. Header Sanitization: Strips inbound Authorization/Host/Forwarded headers; forwards X-User-Id.
5. Google IAM ID Token: Mints Google ID token server-side for backend Cloud Run service.
6. Rate Limiting: In-memory sliding-window IP throttling for abuse prevention.
"""
from __future__ import annotations

import logging
import os
import secrets
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger("medicalplab.bff")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Configuration
BACKEND_SERVICE_URL = os.environ.get("BACKEND_SERVICE_URL", "http://localhost:8080").rstrip("/")
DEV_MOCK_AUTH = os.environ.get("DEV_MOCK_AUTH", "0").strip().lower() in {"1", "true", "yes"}
STAGING_ACCESS_KEY = os.environ.get("STAGING_ACCESS_KEY", "").strip()

if not DEV_MOCK_AUTH:
    if not STAGING_ACCESS_KEY:
        raise RuntimeError(
            "Fatal: STAGING_ACCESS_KEY environment variable is required for BFF gateway operation. "
            "Server cannot start with an empty or missing staging secret."
        )
    is_local_backend = BACKEND_SERVICE_URL.startswith(("http://localhost", "http://127.0.0.1"))
    if not is_local_backend and not BACKEND_SERVICE_URL.startswith("https://"):
        raise RuntimeError(
            "Fatal: BACKEND_SERVICE_URL must use HTTPS when real Google IAM authentication is active."
        )
else:
    if not STAGING_ACCESS_KEY:
        STAGING_ACCESS_KEY = "staging-dev-key-change-me"

MAX_BODY_BYTES = int(os.environ.get("MAX_BODY_BYTES", str(1024 * 1024)))  # 1 MB
REQUEST_TIMEOUT_SECONDS = float(os.environ.get("REQUEST_TIMEOUT_SECONDS", "30.0"))
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120"))

# Route allow-list definitions
EXACT_ALLOWED_PATHS = {
    "/health",
    "/ready",
    "/api/v1/version",
    "/api/v1/tutor/chat",
    "/api/v1/learner/progress",
}

PREFIX_ALLOWED_PATHS = (
    "/api/v1/university/",
    "/api/v1/adaptive/",
    "/api/v1/remediation/",
    "/api/v1/anatomy/",
    "/api/v1/plab/",
)

ALLOWED_METHODS = {"GET", "POST", "HEAD", "OPTIONS"}

# In-memory rate limiting: ip -> list of timestamps
_rate_limits: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(client_ip: str) -> bool:
    now = time.time()
    window_start = now - 60.0
    timestamps = [ts for ts in _rate_limits[client_ip] if ts > window_start]
    if len(timestamps) >= RATE_LIMIT_PER_MINUTE:
        _rate_limits[client_ip] = timestamps
        return False
    timestamps.append(now)
    _rate_limits[client_ip] = timestamps
    return True


def is_path_allowed(path: str) -> tuple[bool, str | None]:
    """Check if the requested path is allowed on the staging gateway."""
    # Explicitly forbid /internal/*
    if path == "/internal" or path.startswith("/internal/"):
        return False, "Access to internal endpoints is forbidden on staging gateway"

    if path in EXACT_ALLOWED_PATHS:
        return True, None

    for prefix in PREFIX_ALLOWED_PATHS:
        if path.startswith(prefix) or path == prefix.rstrip("/"):
            return True, None

    return False, "Route not allowed on staging gateway"


def mint_google_id_token(audience: str) -> str | None:
    """Fetch a Google ID Token from Cloud Run metadata server for the target audience."""
    if DEV_MOCK_AUTH:
        return "mock-dev-token"
    try:
        from google.auth.transport.requests import Request as GoogleAuthRequest
        from google.oauth2 import id_token

        auth_req = GoogleAuthRequest()
        token = id_token.fetch_id_token(auth_req, audience)
        return str(token)
    except Exception as exc:
        logger.debug("Could not fetch Google ID token from metadata service (%s); attempting fallback", exc)
        return None


@asynccontextmanager
async def lifespan(_: FastAPI):
    owns_client = False
    if not hasattr(app.state, "http_client") or app.state.http_client is None:
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
        app.state.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS),
            limits=limits,
            follow_redirects=False,
        )
        owns_client = True
    yield
    if owns_client and hasattr(app.state, "http_client") and app.state.http_client is not None:
        await app.state.http_client.aclose()



app = FastAPI(
    title="MedicalPlab Staging BFF Gateway",
    description="Secure reverse proxy and IAM authentication gateway for MedicalPlab Staging",
    version="1.1.0",
    lifespan=lifespan,
)

# CORS configuration for browser clients (explicit origins default)
allowed_origins_env = os.environ.get(
    "ALLOWED_ORIGINS",
    "https://medical-plab.vercel.app,http://localhost:3000,http://127.0.0.1:3000",
)
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True if allowed_origins != ["*"] else False,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)


@app.api_route("/{full_path:path}", methods=["GET", "POST", "HEAD", "OPTIONS", "PUT", "PATCH", "DELETE"])
async def proxy_gateway(request: Request, full_path: str):
    path = "/" + full_path.lstrip("/")

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return Response(status_code=204)

    # 1. Method Allow-list
    if request.method not in ALLOWED_METHODS:
        return JSONResponse(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            content={"detail": f"Method '{request.method}' not allowed on staging gateway"},
        )

    # 2. Staging Access Key Gate (Constant-Time Verification)
    client_key = request.headers.get("X-Staging-Key") or request.headers.get("x-staging-key")
    if not client_key or not secrets.compare_digest(client_key, STAGING_ACCESS_KEY):
        logger.warning("Rejected unauthorized request to %s: invalid or missing X-Staging-Key", path)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or missing staging access key"},
            headers={"WWW-Authenticate": "X-Staging-Key"},
        )

    # 3. Path Allow-list & /internal/* Block
    allowed, rejection_reason = is_path_allowed(path)
    if not allowed:
        status_code = status.HTTP_403_FORBIDDEN if "forbidden" in (rejection_reason or "").lower() else status.HTTP_404_NOT_FOUND
        logger.warning("Rejected path %s: %s", path, rejection_reason)
        return JSONResponse(
            status_code=status_code,
            content={"detail": rejection_reason or "Not found"},
        )

    # 4. Rate Limiting (Abuse Guard)
    client_host = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_host):
        logger.warning("Rate limit exceeded for client %s on %s", client_host, path)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please slow down."},
        )

    # 5. Body Size Limit (enforced on content-length and streaming read)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Payload exceeds size limit of {MAX_BODY_BYTES} bytes"},
                )
        except ValueError:
            pass

    body_chunks: list[bytes] = []
    total_bytes = 0
    async for chunk in request.stream():
        total_bytes += len(chunk)
        if total_bytes > MAX_BODY_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": f"Payload exceeds size limit of {MAX_BODY_BYTES} bytes"},
            )
        body_chunks.append(chunk)

    body_bytes = b"".join(body_chunks)

    # 6. Sanitize Headers & Attach Google IAM ID Token
    target_url = f"{BACKEND_SERVICE_URL}{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    outbound_headers: dict[str, str] = {}

    # Forward safe client headers
    for h in ("content-type", "accept", "x-user-id", "x-learner-id", "x-request-id"):
        val = request.headers.get(h)
        if val:
            outbound_headers[h] = val

    # Add or forward X-Request-Id
    if "x-request-id" not in outbound_headers:
        outbound_headers["x-request-id"] = f"req-{uuid.uuid4().hex[:12]}"

    # Explicitly drop incoming Authorization / Host / Forwarded headers
    # And mint Cloud Run IAM Authorization token
    id_token = mint_google_id_token(BACKEND_SERVICE_URL)
    if id_token:
        outbound_headers["authorization"] = f"Bearer {id_token}"

    # 7. Proxy Request to Private Backend
    client: httpx.AsyncClient = getattr(app.state, "http_client", None)
    if client is None:
        client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)

    try:
        backend_resp = await client.request(
            method=request.method,
            url=target_url,
            content=body_bytes if body_bytes else None,
            headers=outbound_headers,
        )
    except httpx.TimeoutException:
        logger.error("Timeout proxying %s %s to backend", request.method, path)
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={"detail": "Backend request timed out"},
        )
    except Exception as exc:
        logger.error("Error proxying %s %s to backend: %s", request.method, path, exc)
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": f"Backend communication error: {type(exc).__name__}"},
        )

    # 8. Return Response with Preserved Status and Content-Type
    response_headers: dict[str, str] = {}
    for h in ("content-type", "x-request-id"):
        if h in backend_resp.headers:
            response_headers[h] = backend_resp.headers[h]

    return Response(
        content=backend_resp.content,
        status_code=backend_resp.status_code,
        headers=response_headers,
        media_type=backend_resp.headers.get("content-type"),
    )
