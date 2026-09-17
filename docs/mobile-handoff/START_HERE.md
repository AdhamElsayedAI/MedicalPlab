# MedicalPlab — Mobile Integration: Quick Start Guide
**Version:** 1.1.0  
**Target Audience:** iOS, Android, and React Native Mobile Developers  
**Authoritative Backend Contract:** Frozen Baseline

---

## 1. Configure API Base URL
Point your mobile HTTP client to the authoritative MedicalPlab backend:
- **Local Dev / Simulator:** `http://127.0.0.1:8000` (or `http://10.0.2.2:8000` for Android Emulator)
- **Staging / Remote:** Configured via your environment variable (e.g., `EXPO_PUBLIC_API_URL` or `API_BASE_URL`)

---

## 2. Send Mandatory `X-User-Id` Header
MedicalPlab uses synthetic learner partitioning for pilot and demo integrations.
- Every learner-scoped request **MUST** include the `X-User-Id` header (e.g., `X-User-Id: mobile_demo_learner_01`).
- *Important Security Truth:* `X-User-Id` is an identity-partitioning contract for pilot/demo integration. It is **NOT** cryptographic production authentication (`MOBILE_PRODUCTION_AUTH_READY = NO`). Cryptographic JWT/OAuth2 tokens will be integrated in a dedicated auth phase.

---

## 3. Import Postman Collection & Environment
Everything you need to test the API contract is pre-packaged in this directory:
1. Import [`MedicalPlab.mobile.postman_collection.json`](./MedicalPlab.mobile.postman_collection.json) into Postman or Insomnia.
2. Import [`MedicalPlab.mobile.postman_environment.json`](./MedicalPlab.mobile.postman_environment.json).
3. Set `base_url` to `http://127.0.0.1:8000` and `user_id` to your synthetic identifier.

---

## 4. Run Smoke Tests
Verify connectivity and baseline contract integrity:
```bash
# 1. Health check
curl http://127.0.0.1:8000/health

# 2. Version check
curl http://127.0.0.1:8000/api/v1/version

# 3. Preclinical question list
curl -H "X-User-Id: mobile_dev_01" http://127.0.0.1:8000/api/v1/university/questions
```
For automated verification, consult [`SMOKE_TESTS.md`](./SMOKE_TESTS.md).

---

## 5. Primary Learner Endpoints & Flow
Integrate your mobile views against these frozen endpoints:
1. **Preclinical Practice:** `GET /api/v1/university/questions` & `POST /api/v1/university/submit`
2. **Adaptive State & Recommendations:** `GET /api/v1/adaptive/state` & `GET /api/v1/adaptive/recommendation`
3. **Socratic Remediation (Bounded 3-turn):** `POST /api/v1/remediation/start` & `POST /api/v1/remediation/turn`
4. **Held-Out Transfer:** `POST /api/v1/remediation/transfer/submit`
5. **Evidence-Grounded AI Tutor:** `POST /api/v1/tutor/chat`
6. **3D Anatomy Lab:** `GET /api/v1/anatomy/manifest`, `POST /api/v1/anatomy/session/start`, `POST /api/v1/anatomy/session/{session_id}/interact`, `POST /api/v1/anatomy/session/{session_id}/challenge`
7. **Unified Learner Progress:** `GET /api/v1/learner/progress`

For detailed request/response schemas, refer to:
- [`MOBILE_DEVELOPER_HANDOFF.md`](./MOBILE_DEVELOPER_HANDOFF.md) — Comprehensive technical guide
- [`API_CONTRACT.md`](./API_CONTRACT.md) — Concise endpoint matrix
- [`openapi.json`](./openapi.json) — Full OpenAPI 3.1.0 specification

---

## 6. Clinical Governance & Content Safety
- **PLAB Preview QA:** The 36 candidate questions available under `MEDICALPLAB_PLAB_PREVIEW_QA=1` are for engineering, mentor demos, and review only.
- **Fail-Closed Production Standard:** In strict production mode (`MEDICALPLAB_PLAB_PREVIEW_QA=0`), `GET /api/v1/plab/questions` returns `GOLDEN_ONLY` (0 released items).
- **Hard Rule:** Never represent candidate questions in your mobile client as released or clinician-approved production curriculum.
