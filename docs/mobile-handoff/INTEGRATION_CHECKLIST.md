# MedicalPlab — Mobile Integration Verification Checklist
**Document Version:** 1.1.0  
**Target Release:** `v1.1.0-startup-handoff`  
**Purpose:** Pre-flight quality and compliance gate for client applications integrating with MedicalPlab.

---

## 1. Environment & Connectivity
- [ ] Base URL dynamically configurable via build flavors / environment variables (e.g. `API_BASE_URL`).
- [ ] Android cleartext HTTP permitted only for local development (`10.0.2.2:8000` in `network_security_config.xml`).
- [ ] iOS App Transport Security (ATS) configured to allow local loopback (`127.0.0.1:8000`).
- [ ] Pre-flight `/health` check succeeds with HTTP 200 prior to launching learner interface.
- [ ] Pre-flight `/ready` check verifies `runtime_mode` and `data_manifest: "verified"`.

## 2. Identity & Headers
- [ ] `X-User-Id` header is injected automatically on every learner-scoped request.
- [ ] App handles empty or missing `X-User-Id` gracefully by prompting for demo learner handle.
- [ ] App UI clearly indicates pilot/demo status: `X-User-Id` is demo partitioning, not production cryptographic auth.

## 3. University Preclinical Practice
- [ ] Subject and topic selectors populate from `GET /api/v1/university/subjects` and `GET /api/v1/university/topics`.
- [ ] Active question fetched via `GET /api/v1/university/question` without client-side answer leakage.
- [ ] Answer submissions supply unique `idempotency_key` (UUID v4) to `POST /api/v1/university/answer`.
- [ ] Instant feedback displays deterministic explanation, correctness pill, and distractor signal.

## 4. Adaptive Learning & State
- [ ] `GET /api/v1/adaptive/state` reflects updated topic streaks and recommended difficulty tiers.
- [ ] Next recommended action (`GET /api/v1/adaptive/recommendation`) prompts student to initiate remediation if distractor pattern detected.

## 5. Bounded Socratic Remediation
- [ ] Remediation initiates via `POST /api/v1/remediation/start` returning preceptor cognitive probe (Turn 1).
- [ ] Client tracks active `session_id` and bounds conversation to a maximum of 3 turns.
- [ ] Guided hints (Turn 2) and synthesis consolidation (Turn 3) handled via `POST /api/v1/remediation/turn`.
- [ ] Answer keys are never disclosed during remediation dialogue.

## 6. Independent Held-Out Transfer Gate
- [ ] Client displays dedicated held-out transfer problem from `GET /api/v1/remediation/session/{session_id}/transfer`.
- [ ] Transfer answer evaluated via `POST /api/v1/remediation/session/{session_id}/transfer`.
- [ ] UI explicitly indicates that dialogue alone did not award mastery; only the independent transfer outcome certifies understanding.

## 7. Evidence-Grounded AI Tutor
- [ ] Natural language questions sent to `POST /api/v1/tutor/chat` with optional subject/topic context.
- [ ] Response claims render with expandable citation pills showing PMCID, source title, quote, and license provenance.
- [ ] Fallback state (`fallback_applied: true`) is detected and rendered with procedural guidance notice (`SAFE_FALLBACK`).

## 8. 3D Spatial Anatomy
- [ ] Three.js or native WebView loads verified GLB meshes from `GET /api/v1/anatomy/manifest`.
- [ ] Session initialized via `POST /api/v1/anatomy/session/start`.
- [ ] Interactive mesh clicks dispatch structured scene actions (`HIGHLIGHT_STRUCTURE`, `FOCUS_STRUCTURE`, `ISOLATE_STRUCTURE`).
- [ ] Independent structure challenge submitted to `POST /api/v1/anatomy/session/{session_id}/challenge` and scored deterministically.

## 9. Unified Progress Telemetry
- [ ] Student dashboard consumes `GET /api/v1/learner/progress`.
- [ ] Telemetry displays unified metrics across preclinical questions, remediation completions, transfer passes, and 3D challenges.

## 10. PLAB Clinical Governance & Content Safety
- [ ] When `plab_preview_qa: true`, candidate questions are explicitly badged as "Preview QA Candidate — Under Clinician Review".
- [ ] Production mode (`plab_preview_qa: false`) fails closed to 0 released items without crashing.
- [ ] Candidate items are never represented as official released examination questions.

## 11. Error Handling, Timeouts & Network Resilience
- [ ] HTTP 400 (Bad Request): Validation feedback displayed to user.
- [ ] HTTP 403 (Session Ownership): Stale session cleared and learner redirected.
- [ ] HTTP 404 (Not Found): Stale question/session cleanly refreshed.
- [ ] HTTP 422 (Unprocessable): Schema validation errors caught in dev builds.
- [ ] HTTP 503 (Feature Disabled): Friendly fallback banner displayed.
- [ ] Client requests enforce a 15-second network timeout.
- [ ] Offline status detected; user notified that live scoring and evidence verification require network connectivity (`OFFLINE_SYNC_SUPPORTED = NO`).

## 12. Staging Smoke Verification
- [ ] All 7 core journey steps executed successfully against live HTTPS staging environment.
- [ ] Synthetic test account used (no real learner PII transmitted).
