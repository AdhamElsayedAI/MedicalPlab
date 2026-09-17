# MedicalPlab Mobile API Handoff — Quick Start Guide

Welcome to the **MedicalPlab** Backend API handoff package. This guide is written specifically for mobile developers (iOS / Android / Flutter / React Native) integrating MedicalPlab into mobile client applications.

You do **not** need to read or understand backend internals (such as Evidence Engine RAG, BM25 reranking, claim verification pipelines, or SQLite storage details). The backend provides a deterministic REST API contract and manages all educational state authoritatively.

---

## 1. Backend Start Command

To launch the local MedicalPlab API server for development and testing:

```bash
# 1. Set required runtime mode and feature flags
export PYTHONPATH="src"
export MEDICALPLAB_RUNTIME_MODE="pilot"
export MEDICALPLAB_PHASE_2B_ENABLED="1"
export MEDICALPLAB_ANATOMY_3D_ENABLED="1"

# For PLAB preview QA / demo mode (optional):
export MEDICALPLAB_PLAB_PREVIEW_QA="1"

# 2. Launch production FastAPI application with Uvicorn
python -m uvicorn production_main:app --host 127.0.0.1 --port 8000 --workers 1
```

*(On Windows PowerShell):*
```powershell
$env:PYTHONPATH = "src"
$env:MEDICALPLAB_RUNTIME_MODE = "pilot"
$env:MEDICALPLAB_PHASE_2B_ENABLED = "1"
$env:MEDICALPLAB_ANATOMY_3D_ENABLED = "1"
# $env:MEDICALPLAB_PLAB_PREVIEW_QA = "1" # (Optional for QA review)
python -m uvicorn production_main:app --host 127.0.0.1 --port 8000 --workers 1
```

---

## 2. Base URL & Network Configuration

- **Local Development Base URL:** `http://127.0.0.1:8000` (or `http://10.0.2.2:8000` for Android Emulator)
- **Content Type:** All requests and responses use `application/json; charset=utf-8`.
- **CORS:** The backend enables permissive CORS headers for local debugging and cross-origin access.

---

## 3. Swagger UI & OpenAPI Specification

- **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Interactive ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Live OpenAPI JSON:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- **Snapshot File in Repo:** [`docs/mobile-handoff/openapi.json`](./openapi.json)

---

## 4. Required Runtime Flags & Environment Variables

| Variable | Type | Default | Required for Mobile Demo | Description |
| :--- | :--- | :--- | :--- | :--- |
| `MEDICALPLAB_PHASE_2B_ENABLED` | Boolean (`true`/`false`) | `false` | **YES (`true`)** | Activates the Phase 2B Socratic Remediation & Transfer engine. If false, `/api/v1/remediation/*` returns `503 Service Unavailable`. |
| `MEDICALPLAB_PLAB_PREVIEW_QA` | Boolean (`1`/`0`) | `0` | For Demo / QA | Enables Preview QA mode for PLAB clinical questions. In strict default production (`0`), `/api/v1/plab/questions` returns `count: 0` (`PLAB_PUBLIC_RELEASE_READY = NO`, `PLAB_GOLDEN_PROMOTION_REQUIRED = YES`). For internal QA/demo, set to `1` (`content_mode: "PREVIEW_QA"`). |
| `MEDICALPLAB_TUTOR_PROVIDER` | String | `stub` | Optional (`stub` default) | AI provider mode for tutor responses. Default `stub` runs completely deterministic, offline-safe, with zero external LLM dependencies. This stub is for demo and test validation only; it does not represent live clinical LLM generation. |
| `ALLOWED_ORIGINS` | Comma-separated | `*` | Optional | Allowed CORS origins. |

> **Security & Governance Note:**
> 1. Never hardcode secrets, API keys, or administrative tokens in mobile client bundles.
> 2. Mobile clients must distinguish `PLAB_PREVIEW_QA / INTERNAL_DEMO` from `PLAB_PUBLIC_STUDENT_READY`. Preview-only questions must never be presented as production student curriculum. Mobile integration status: `MOBILE_BACKEND_HANDOFF_READY` with `PLAB_PUBLIC_RELEASE_READY = NO` and `PLAB_GOLDEN_PROMOTION_REQUIRED = YES`.


---

## 5. Learner Identity Rule (MVP Identity Model)

### What it is
In the current MVP, full authentication (e.g., OAuth2, JWT, SSO) is **not yet implemented**. The backend uses an **anonymous device / client-generated identity model**.

### Identity Generation & Persistence Rule
1. **Header Name:** `X-User-Id`
2. **Format Requirement:** Non-empty string between 8 and 120 characters (e.g., `uni-` prefix + UUIDv4: `uni-a1b2c3d4-e5f6-7890-abcd-ef1234567890`).
3. **Storage:** The mobile client **MUST** generate this UUID on first app launch and persist it securely in durable device storage (e.g., `SharedPreferences` on Android, `Keychain` / `UserDefaults` on iOS, or `AsyncStorage`).
4. **Header Enforcement:** Every API request must include:
   ```http
   X-User-Id: uni-4f8a1234-abcd-5678-90ef-1234567890ab
   ```
5. **Backend Default Fallback:** If `X-User-Id` is omitted, some endpoints default to `"demo-student-001"`, but `/api/v1/university/answer` and `/progress` enforce `min_length=8` and will return `HTTP 422` if missing.
6. **Ownership Mismatch:** If a request provides an `X-User-Id` that does not match the session or attempt owner, the server returns `HTTP 403 Forbidden`.
7. **Device Change / Reinstall Limitation:** Because identity is stored locally on the client device:
   - Uninstalling the app clears local storage and resets the learner identity.
   - Cross-device sync is not available in the MVP.
   - For demo continuity, the app may provide a "Demo Profile" switch setting the header back to a known test ID (e.g. `demo-student-001`).

---

## 6. Mobile Security & Authority Boundary

The backend is **authoritative** for all educational measurements and state transitions:
- **Authoritative Server Capabilities:**
  - Correctness verification
  - Mastery and educational progress calculation
  - Adaptive recommendation selection
  - Remediation turn bounding and lifecycle transitions
  - Transfer qualification and deterministic scoring
  - Session ownership verification

- **Strict Mobile Client Prohibitions:**
  - The mobile client **MUST NOT** infer question correctness or bypass server evaluation.
  - The mobile client **MUST NOT** calculate or adjust mastery scores client-side.
  - The mobile client **MUST NOT** declare transfer success or conversation completion as mastery.
  - The mobile client **MUST NOT** reproduce adaptive heuristics or decision logic.
  - The mobile client **MUST NOT** bundle, store, or cache hidden answer keys.
  - The mobile client **MUST NOT** bypass `X-User-Id` ownership semantics.
  - The mobile client **MUST NOT** blindly replay POST requests after app restart; it must inspect server state via `GET`.

---

## 7. Main Mobile Learning Flow

The student journey flows through a deterministic, backend-authoritative loop:

```
[1. Select Subject] ──> GET /api/v1/university/subjects
          │
[2. Select Topic]   ──> GET /api/v1/university/topics?subject=...
          │
[3. Fetch Question] ──> GET /api/v1/university/question?subject=...&topic=...
          │
[4. Submit Answer]  ──> POST /api/v1/university/answer
          │
          ├── If Correct: Show explanation, proceed to next question
          └── If Incorrect:
                    │
[5. Adaptive Check] ──> GET /api/v1/adaptive/recommendation
                    │
[6. Remediation]    ──> POST /api/v1/remediation/start (Turn 1: Probe)
                    ──> POST /api/v1/remediation/turn  (Turn 2: Guide)
                    ──> POST /api/v1/remediation/turn  (Turn 3: Consolidate)
                    │
          ┌─────────┴──────────────────────────────┐
          │ (If transfer available)                │ (If transfer unavailable)
[7. Fetch Transfer]                                │
    GET /remediation/session/{id}/transfer         │ Lifecycle = COMPLETED
          │                                        │ Outcome = UNRESOLVED
[8. Submit Transfer]                               │
    POST /remediation/session/{id}/transfer        │
    (Outcome: TRANSFER_CONFIRMED                   │
     or TRANSFER_NOT_CONFIRMED)                    │
          │                                        │
          └─────────────────┬──────────────────────┘
                            │
[9. Refresh State] ──> GET /api/v1/adaptive/state
```

See [`MOBILE_FLOW.md`](./MOBILE_FLOW.md) for full flow specifications and state charts.

---

## 8. Endpoint Contract Reference

For exhaustive parameter tables, schemas, and payload examples, refer to:
- [`API_CONTRACT.md`](./API_CONTRACT.md): Complete mobile endpoint inventory categorized into Required, Optional, Web-Only, and Internal.

---

## 9. Demo Data & Known Working Test Fixtures

Pre-seeded educational questions and test fixtures:
- **Subject:** `Renal physiology`
- **Topic:** `RAAS mechanisms`
- **Remediation Demo Question:** `UNI-RENAL-001` (Correct Answer: `A`; Distractor: `B` triggers RAAS substrate confusion).
- **Held-out Transfer Item:** `UNI-RENAL-001-T` (Correct Answer: `A`).
- **Transfer Unavailable Demo Question:** `UNI-RENAL-003` (Triggers remediation, but intentionally has no held-out transfer item, demonstrating graceful fallback).

See [`DEMO_DATA.md`](./DEMO_DATA.md) for complete question content and test cases.

---

## 10. Error Handling & Terminal Safety Fallback

The backend returns standard HTTP status codes:
- `400 Bad Request`: Invalid turn progression or malformed parameters.
- `403 Forbidden`: Ownership mismatch (`X-User-Id` does not match the creator of the attempt or session).
- `404 Not Found`: Unknown question ID, session ID, or no eligible transfer item available.
- `409 Conflict`: Idempotency key conflict (reused with different parameters).
- `422 Unprocessable Entity`: Business invariant violated (e.g. attempting to remediate a correct answer, or submitting transfer before turn 3).
- `503 Service Unavailable`: Feature flag `MEDICALPLAB_PHASE_2B_ENABLED` is disabled.

### Terminal Fallback Contract (`SAFETY_FALLBACK`)
If the underlying AI verification fails or evidence cannot be grounded:
- `lifecycle_state`: `"COMPLETED"`
- `outcome`: `"SAFETY_FALLBACK"`
- `transfer_available`: `false`
- `tutor_message`: Canonical safe fallback message.
- **Mobile UX Action:** Display the safe explanation, hide input controls, and present a button to return to topics or review. **Mobile MUST NOT attempt further turns after terminal fallback.**

See [`ERRORS_AND_STATES.md`](./ERRORS_AND_STATES.md) for the complete error matrix.

---

## 11. Session Resume & App Restart Behavior

When the mobile app is killed, backgrounded, or encounters a network drop:
- The backend SQLite database persistently tracks session progress.
- Call `GET /api/v1/remediation/session/{session_id}` on app resume to restore exact turn state, chat history, and timeline.
- **NEVER re-post** earlier turns; the backend is strictly idempotent via `idempotency_key` and rejects duplicate turn progressions.

See [`ERRORS_AND_STATES.md`](./ERRORS_AND_STATES.md#session-resume-behavior) for recovery patterns.

---

## 12. Handoff Package Contents

1. [`MOBILE_DEVELOPER_HANDOFF.md`](./MOBILE_DEVELOPER_HANDOFF.md) — *Authoritative first-read developer guide with request/response examples and matrices.*
2. [`MedicalPlab.mobile.postman_collection.json`](./MedicalPlab.mobile.postman_collection.json) — *Ready-to-run Postman collection (29 requests across 8 consumer folders).*
3. [`MedicalPlab.mobile.postman_environment.json`](./MedicalPlab.mobile.postman_environment.json) — *Postman environment with non-secret variable placeholders.*
4. [`README.md`](./README.md) — *Quickstart & integration rules.*
5. [`API_CONTRACT.md`](./API_CONTRACT.md) — *Exhaustive REST API contract with schemas and DTOs.*
6. [`MOBILE_FLOW.md`](./MOBILE_FLOW.md) — *Complete end-to-end learning flow and state machine.*
7. [`ERRORS_AND_STATES.md`](./ERRORS_AND_STATES.md) — *Error matrix, terminal states, and resume patterns.*
8. [`DEMO_DATA.md`](./DEMO_DATA.md) — *Synthetic demo questions, distractors, and transfer items.*
9. [`SMOKE_TESTS.md`](./SMOKE_TESTS.md) — *Practical curl examples for the 11-step end-to-end smoke test.*
10. [`openapi.json`](./openapi.json) — *Frozen runtime OpenAPI 3.1 specification.*
