# MedicalPlab Staging BFF (Backend-For-Frontend) Gateway

## Architecture Overview

The Staging BFF Gateway is a lightweight, zero-business-logic reverse proxy deployed as a public Cloud Run service (`medicalplab-bff`) in front of the private backend Cloud Run service (`medicalplab-api`).

```
[Mobile App / Postman / Vercel Server Proxy]
                   │
                   │ HTTPS + X-Staging-Key + X-User-Id
                   ▼
       [Cloud Run: medicalplab-bff]
       (Public, min=0, max=1)
                   │
                   │ Google IAM ID Token (roles/run.invoker)
                   │ Strips Client Authorization/Host headers
                   │ Forwards X-User-Id
                   ▼
       [Cloud Run: medicalplab-api]
       (Private --no-allow-unauthenticated, min=0, max=1)
                   │
                   ▼
       [Ephemeral SQLite]
```

## Responsibilities

1. **Staging Access Gate**: Validates the `X-Staging-Key` header using constant-time comparison (`secrets.compare_digest`). Requests with missing or invalid keys receive HTTP 401.
2. **Route Allow-List**: Only permits frozen contract routes:
   - `/health`, `/ready`, `/api/v1/version`
   - `/api/v1/university/*`
   - `/api/v1/adaptive/*`
   - `/api/v1/remediation/*`
   - `/api/v1/tutor/chat`
   - `/api/v1/anatomy/*`
   - `/api/v1/learner/progress`
   - `/api/v1/plab/*`
3. **Internal Route Hard Block**: Explicitly blocks `/internal/*` with HTTP 403.
4. **Method Allow-List**: Restricts HTTP methods to `GET`, `POST`, `HEAD`, `OPTIONS`. All other methods receive HTTP 405.
5. **Payload Size Limit**: Rejects request bodies exceeding 1 MB with HTTP 413.
6. **Header Sanitization**: Drops client-provided `Authorization`, `Host`, and `X-Forwarded-*` headers to prevent spoofing.
7. **Google IAM Authentication**: Mints a Google ID token server-side via Cloud Run metadata server and attaches it as `Authorization: Bearer <id_token>` when calling the private backend.
8. **Learner Identity Preservation**: Forwards `X-User-Id` / `X-Learner-Id` and `X-Request-Id` unchanged.
9. **Abuse Protection**: In-memory sliding-window IP rate limiter (default 120 requests/minute).

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `BACKEND_SERVICE_URL` | `http://localhost:8080` | URL of the private backend Cloud Run service |
| `STAGING_ACCESS_KEY` | `staging-dev-key-change-me` | Secret required in `X-Staging-Key` |
| `DEV_MOCK_AUTH` | `0` | Set to `1` to mock IAM token generation locally |
| `MAX_BODY_BYTES` | `1048576` (1 MB) | Maximum request body size |
| `REQUEST_TIMEOUT_SECONDS` | `30.0` | Upstream backend request timeout |
| `RATE_LIMIT_PER_MINUTE` | `120` | Maximum requests per minute per IP |
| `ALLOWED_ORIGINS` | `*` | Allowed CORS origins for browser/Vercel preview |

## Local Development

```bash
cd staging/bff
pip install -r requirements.txt
DEV_MOCK_AUTH=1 STAGING_ACCESS_KEY=local-test-key BACKEND_SERVICE_URL=http://localhost:8000 uvicorn main:app --port 8080
```
