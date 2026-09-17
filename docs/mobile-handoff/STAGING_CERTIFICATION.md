# MedicalPlab — Staging Environment Certification
## ⚠️ NON-DURABLE INTEGRATION / DEMONSTRATION STAGING
**Date:** September 18, 2026  
**Git Baseline SHA:** `2078d142088f4c689975ab7f560a2107170b07a8`  
**Target Branch:** `release/final-mentor-mobile-handoff`  
**Region:** `europe-west1`  
**Runtime Mode:** `production` / `pilot`  
**API Specification Version:** `1.1.0`  
**OpenAPI Contract SHA-256:** `e17f06cd4fb4cebca4f14ab4ffbd702cfa9b3eaf050da55f8a5c1c5b0dccfb95`  
**Postman Suite SHA-256:** `a1a01939706a168c610c5c6f11f96355f2b2d88fe85c354512b9455c170b2895`  
**Target Staging Base URL (BFF Gateway):** `https://medicalplab-bff-staging.europe-west1.run.app` (Public, Gate: `X-Staging-Key`)  
**Target Backend Service URL:** `https://medicalplab-api-staging.europe-west1.run.app` (Private, `--no-allow-unauthenticated`)  

> [!WARNING]
> **Non-Durable Staging.** This environment uses ephemeral SQLite storage. Learner state, session progress, and remediation records do NOT persist across Cloud Run container lifecycle restarts (`STAGING_PERSISTENCE_CERTIFIED = NO`). This environment is suitable for API contract verification, mobile integration testing, and live mentor demonstrations only. It is NOT equivalent to a production-grade durable environment.

---

## 1. Staging Infrastructure & Deployment Status

```
[Vercel Next.js UI]
        │
        ▼ (Same-origin server proxy /api/medicalplab/* with server-only STAGING_ACCESS_KEY)
[Public Cloud Run: medicalplab-bff] (Gate: X-Staging-Key, min=0, max=1, europe-west1)
        │
        ▼ (Google IAM ID Token: roles/run.invoker)
[Private Cloud Run: medicalplab-api] (--no-allow-unauthenticated, min=0, max=1, concurrency=4)
        │
        ▼
[Ephemeral SQLite: Data/persistence/]
```

### Authoritative Deployment Status
- **Current GCP Cloud Run Deployment:** `MEDICALPLAB_ZERO_COST_STAGING_BLOCKED_USER_GCP_SETUP`
- **Backend Staging URL:** `NOT_PROVISIONED`
- **BFF Staging URL:** `NOT_PROVISIONED`
- **Root Cause:** GCP Project ID, Workload Identity Federation / Service Account Key, and `STAGING_ACCESS_KEY` secrets are not yet configured in GitHub Repository Settings.
- **Fail-Closed Guarantee:** The GitHub Actions deployment workflow (`deploy-cloud-run.yml`) fails closed with an explicit error rather than falsely reporting green success when secrets are missing.
- **Artifact Registry Cleanup Policy:** `PENDING_GCP_RESOURCE_CREATION` (will retain recent tagged revisions and delete untagged/stale images once repository is created; no paid scanning).
- **Public Browser Proxy Security:** `MENTOR_SESSION_GATE = YES`, `PUBLIC_BROWSER_PROXY_OPEN = NO` (HttpOnly signed session cookie required at `/api/medicalplab/*`).

### Corrected Human Setup & Automated Deployment Sequence

1. **Create / Select GCP Project & Link Billing**:
   Create project in GCP Console (e.g. `medicalplab-staging`) and attach standard billing.
2. **Enable Required Google APIs**:
   `gcloud services enable run.googleapis.com artifactregistry.googleapis.com iam.googleapis.com --project <PROJECT_ID>`
3. **Create Artifact Registry Docker Repository**:
   `gcloud artifacts repositories create medicalplab --repository-format=docker --location=europe-west1 --project <PROJECT_ID>`
4. **Create Runtime Service Accounts**:
   - `medicalplab-api-runtime` (Private backend identity)
   - `medicalplab-bff-runtime` (Public BFF gateway identity)
5. **Create Deployment Identity (WIF or SA Key)**:
   Grant `medicalplab-deploy` deployment identity: `roles/run.admin`, `roles/artifactregistry.writer`, `roles/iam.serviceAccountUser`.
6. **Configure GitHub Repository Secrets**:
   `GCP_PROJECT_ID`, `GCP_WIF_PROVIDER` / `GCP_SA_KEY`, `GCP_WIF_SERVICE_ACCOUNT`, `STAGING_ACCESS_KEY`.
7. **Configure Vercel Environment Variables**:
   `BFF_BASE_URL`, `STAGING_ACCESS_KEY` (server-only), `MENTOR_ACCESS_CODE` (server-only).
8. **Run Deployment**:
   Trigger `workflow_dispatch` on GitHub Actions:
   - Deploys private `medicalplab-api` with `pilot` runtime mode and demo feature flags enabled (`MEDICALPLAB_PHASE_2B_ENABLED=1`, `MEDICALPLAB_ANATOMY_3D_ENABLED=1`).
   - Automatically establishes `roles/run.invoker` policy binding for `medicalplab-bff-runtime` on `medicalplab-api`.
   - Deploys public `medicalplab-bff` gateway.
   - Executes automated security boundary tests (anonymous backend rejection, BFF key verification).

---

## 2. Staging Persistence Architecture Truth

> [!CAUTION]
> **`STAGING_PERSISTENCE_CERTIFIED = NO`**  
> Staging uses module-owned SQLite storage (`Data/persistence/`). In serverless environments (Google Cloud Run), local container storage is **ephemeral** and resets on container lifecycle restarts. This environment does NOT certify data durability.

- **Persistence Backend:** Local SQLite (`Data/persistence/`) — ephemeral on Cloud Run.
- **Data Durability:** NOT CERTIFIED. Session state may be lost across container restarts.
- **Recommended Usage:** API contract testing, mobile integration smoke tests, and live supervised demonstrations only.
- **Recommended Configuration:** `min-instances: 0`, `max-instances: 1` to minimize restart probability during active demonstrations.
- **Production Standard:** Durable managed cloud persistence (PostgreSQL / Cloud SQL) is required for institutional multi-tenant production deployment.

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
4. **`STAGING_PERSISTENCE_CERTIFIED = NO`**  
   Staging SQLite storage is ephemeral in Cloud Run serverless environments. Learner session data may not survive container restarts. Do not measure persistence SLAs against this environment.
