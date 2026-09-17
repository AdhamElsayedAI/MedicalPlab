# MedicalPlab — Staging Environment & Contract Certification
**Date:** September 18, 2026  
**Git Baseline SHA:** `e3225e47534968270312bb2db5df697ee1043876`  
**Target Branch:** `release/final-mentor-mobile-handoff`  
**Runtime Mode:** `pilot`  
**API Specification Version:** `1.1.0`  
**OpenAPI Contract SHA-256:** `e17f06cd4fb4cebca4f14ab4ffbd702cfa9b3eaf050da55f8a5c1c5b0dccfb95`  
**Postman Suite SHA-256:** `55792ca5cdf66612f551b4cfdfd504de58611dd97ce507d8935c6306f7d366ac`  
**Target Staging Base URL:** `https://medicalplab-api-staging-uc.a.run.app` (or local staging simulation `http://127.0.0.1:8000`)

---

## 1. Staging Infrastructure & Deployment Status

```
[GitHub Actions CI/CD] 
       │
       ▼ (On main push or manual dispatch)
[.github/workflows/deploy-cloud-run.yml]
       │
       ├── Check GCP_PROJECT_ID & GCP_SA_KEY
       │      │
       │      ├─► Configured ────► Build Docker Image ──► Deploy Cloud Run (max-instances: 1)
       │      │
       │      └─► Absent ────────► FAIL CLEARLY (Fail-closed deployment truth)
```

### Authoritative Deployment Status
- **Current GCP Cloud Run Deployment:** `STAGING_DEPLOYMENT_BLOCKED_GCP_CONFIGURATION`
- **Root Cause:** GitHub repository secrets `GCP_PROJECT_ID` and `GCP_SA_KEY` are not yet populated in repository settings.
- **Fail-Closed Guarantee:** The GitHub Actions deployment workflow has been audited and updated so that it fails closed with an explicit error rather than falsely reporting green success when secrets are missing.
- **Required Administrator Action:** To activate automated Cloud Run deployment, configure `GCP_PROJECT_ID` and `GCP_SA_KEY` (with Cloud Run Admin + Storage Admin permissions) in GitHub Repository Settings &rarr; Secrets and variables &rarr; Actions.

---

## 2. Staging Persistence Architecture Truth

- **Persistence Backend:** Staging uses module-owned SQLite storage (`Data/persistence/`).
- **Instance Lifecycle:** In serverless environments (Google Cloud Run), local container storage is ephemeral and may reset across container lifecycle restarts.
- **Recommended Configuration:** `min-instances: 0`, `max-instances: 1` to ensure deterministic state during active mentor demonstrations and mobile contract testing.
- **Production Standard:** Durable managed cloud persistence (PostgreSQL / Cloud SQL) is scheduled for institutional multi-tenant expansion.

---

## 3. Module Certification Matrix

Every learner module in MedicalPlab has been certified against the frozen contract baseline (`v1.1.0`):

| Functional Area | Canonical Endpoints | Contract Status |
| :--- | :--- | :--- |
| **System & Health** | `GET /health`<br>`GET /ready`<br>`GET /api/v1/version` | **CERTIFIED** (HTTP 200, runtime mode verified) |
| **University Track** | `GET /api/v1/university/subjects`<br>`GET /api/v1/university/topics`<br>`GET /api/v1/university/question`<br>`POST /api/v1/university/answer` | **CERTIFIED** (Idempotent submission, answer key unexposed) |
| **Adaptive Policy** | `GET /api/v1/adaptive/recommendation`<br>`GET /api/v1/adaptive/state` | **CERTIFIED** (Dynamic policy routing based on distractor signals) |
| **Socratic Remediation** | `POST /api/v1/remediation/start`<br>`POST /api/v1/remediation/turn` | **CERTIFIED** (Bounded 3-turn cognitive sequence: Probe &rarr; Guide &rarr; Consolidate) |
| **Independent Transfer** | `GET /api/v1/remediation/session/{id}/transfer`<br>`POST /api/v1/remediation/session/{id}/transfer` | **CERTIFIED** (Held-out transfer problem; independent evidence gate) |
| **Evidence AI Tutor** | `POST /api/v1/tutor/chat` | **CERTIFIED** (PMC evidence-grounded, claim-verified, fail-closed fallback) |
| **3D Spatial Anatomy** | `GET /api/v1/anatomy/manifest`<br>`POST /api/v1/anatomy/session/start`<br>`POST /api/v1/anatomy/session/{id}/challenge` | **CERTIFIED** (HuBMAP CCF v1.3/v2.0 GLB assets, deterministic raycast scoring) |
| **Unified Progress** | `GET /api/v1/learner/progress` | **CERTIFIED** (Unified telemetry across preclinical, tutor, and 3D challenges) |
| **PLAB Governance** | `GET /api/v1/plab/questions`<br>`POST /api/v1/plab/evaluate` | **CERTIFIED** (36 Preview QA items, 0 Golden released items in production) |

---

## 4. Current Limitations & Invariants

Mobile developers and reviewing mentors must observe the following authoritative product invariants:

1. **`MOBILE_PRODUCTION_AUTH_READY = NO`**  
   The `X-User-Id` header provides synthetic learner partitioning for demo and pilot evaluation. It is **NOT** cryptographic authentication.
2. **`PLAB_PUBLIC_RELEASE_READY = NO`**  
   The 36 PLAB candidate questions are strictly candidate items undergoing clinician review. In strict production (`MEDICALPLAB_PLAB_PREVIEW_QA=0`), the endpoint fails closed to 0 released questions.
3. **`OFFLINE_SYNC_SUPPORTED = NO`**  
   MedicalPlab requires network connectivity for deterministic scoring, evidence retrieval, and post-generation proposition verification.
