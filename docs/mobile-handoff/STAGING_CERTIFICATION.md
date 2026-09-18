# MedicalPlab — Staging Environment Certification
## ⚠️ NON-DURABLE INTEGRATION / DEMONSTRATION STAGING (RENDER FREE)
**Date:** September 18, 2026  
**Provider:** Render (Free Web Service)  
**Target Branch:** `release/final-mentor-mobile-handoff`  
**PR:** #4  
**Region:** `frankfurt` (Frankfurt, Germany — nearest verified free region to Egypt)  
**Plan:** Free ($0 expected under current Render Free plan and current verified usage limits)  
**Runtime Mode:** `pilot`  
**API Specification Version:** `1.1.0`  
**OpenAPI Contract SHA-256:** `e17f06cd4fb4cebca4f14ab4ffbd702cfa9b3eaf050da55f8a5c1c5b0dccfb95`  
**Postman Suite SHA-256:** `a1a01939706a168c610c5c6f11f96355f2b2d88fe85c354512b9455c170b2895`  
**Staging Base URL:** `NOT_PROVISIONED` (Awaiting user creation in Render Dashboard)  
**Target Expected Staging URL:** `https://medicalplab-staging.onrender.com`  

> [!WARNING]
> **Non-Durable Staging.** This environment uses ephemeral container filesystem storage. Learner state, session progress, and remediation records do NOT persist across Render service restarts, spin-down sleep cycles, or redeployments (`STAGING_PERSISTENCE_CERTIFIED = NO`). This environment is certified for API contract verification, mobile integration testing, and live mentor demonstrations only. It is NOT equivalent to a production-grade durable environment.

---

## 1. Staging Architecture & Deployment Topology

```
Mentor Browser
      ↓
Vercel Next.js UI (https://medical-plab.vercel.app)
      ↓
Mentor Session Gate (Signed HttpOnly cookie: MENTOR_ACCESS_CODE)
      ↓
Vercel Same-Origin Server Proxy (/api/medicalplab/*)
      ↓
Server-only X-Staging-Key injection (MEDICALPLAB_STAGING_BASE_URL)
      ↓
Render Free Web Service (Docker runtime, 512MB RAM, frankfurt)
      ↓
FastAPI ASGI Staging Security Middleware (src/medicalplab/staging/security.py)
      ↓
FastAPI production_main.py:app
      ↓
Ephemeral SQLite Storage (Data/persistence/)

Mobile / Postman Client
      ↓
Direct HTTPS with X-Staging-Key + X-User-Id
      ↓
Render Free Web Service (FastAPI)
```

### Key Architectural Invariants
- **Single Service Architecture:** The Render staging deployment consists of **one** Web Service (`medicalplab-staging`). There is no separate BFF proxy container or Google IAM token exchange.
- **Direct ASGI Staging Gate:** Access control is enforced directly by `StagingSecurityMiddleware` in `production_main.py:app` via `MEDICALPLAB_STAGING_GATE_ENABLED=1`.
- **Public Health Probe:** `GET /health` is unauthenticated to support Render platform health checking.
- **Fail-Closed Gate:** Missing `STAGING_ACCESS_KEY` during startup raises a fatal `RuntimeError`.
- **Blocked Routes:** Internet staging explicitly blocks `/internal/*`, `/docs`, `/redoc`, and `/openapi.json` with HTTP 403. Unknown routes return HTTP 404.
- **Method Safety:** Restricts HTTP methods to `GET`, `POST`, `HEAD`, `OPTIONS`. Disallowed methods return HTTP 405.
- **Payload Safety:** Enforces 1 MB maximum request body size (HTTP 413).
- **Server-Only Secrets:** Next.js proxy keeps `STAGING_ACCESS_KEY`, `MENTOR_ACCESS_CODE`, and `MENTOR_SESSION_SECRET` strictly server-side. No `NEXT_PUBLIC_*` secret leakage.

---

## 2. Current Pre-Deployment Certification State

| Metric / Property | Certified Value | Notes |
| :--- | :--- | :--- |
| **ACTIVE_STAGING_PROVIDER** | `RENDER` | GCP staging abandoned due to billing setup blockage |
| **GCP_AUTOMATIC_DEPLOYMENT_ENABLED** | `NO` | `deploy-cloud-run.yml` converted to inactive manual reference |
| **RENDER_DEPLOYMENT_STATUS** | `BLOCKED_USER_RENDER_SETUP` | Requires user connection in Render dashboard |
| **RENDER_STAGING_URL** | `NOT_PROVISIONED` | Provisioned after user setup |
| **EXTERNAL_MOBILE_SMOKE** | `BLOCKED_RENDER_DEPLOYMENT` | Certified locally; awaiting live Render HTTPS endpoint |
| **RENDER_FREE_PLAN_VERIFIED** | `YES` | Verified against current official `render.com/docs/free` |
| **RENDER_PAYMENT_METHOD_REQUIRED** | `NO` | No credit/debit card required for free web service |
| **RENDER_REGION_SELECTED** | `frankfurt` | Closest available region to Egypt supported on Free tier |
| **RENDER_FREE_RAM_MB** | `512` | Official Render Free Web Service memory limit |
| **MEASURED_PEAK_RAM_MB** | `~60.76` (heap) / `~110` (RSS) | Measured under full representative learner flows |
| **MEMORY_HEADROOM_MB** | `~400` | >75% safety headroom under 512 MB limit |
| **BACKEND_IMAGE_SIZE_MB** | `~271` | Production multi-stage Docker image |
| **GPU_REQUIRED** | `NO` | CPU-only PyTorch-free production runtime |
| **TORCH_IN_PRODUCTION_IMAGE** | `NO` | Zero heavy ML dependencies in production image |
| **LOCAL_QWEN_WEIGHTS_IN_IMAGE** | `NO` | Zero local weights; deterministic stub tutor on staging |
| **STAGING_PERSISTENCE_CERTIFIED** | `NO` | Ephemeral filesystem only; learner state resets on sleep/restart |

---

## 3. Human Setup Sequence for Render Dashboard

Because the coding assistant cannot log in to your personal Render dashboard or GitHub OAuth authorizations, follow these steps to activate the staging web service:

1. **Open Render Dashboard:**
   Navigate to [https://dashboard.render.com](https://dashboard.render.com).
2. **Connect GitHub Account:**
   Ensure your GitHub account (`AdhamElsayedAI`) is linked to Render.
3. **Create New Web Service from Blueprint or Git Repository:**
   - Option A (Blueprint): Select **New +** &rarr; **Blueprint**, point to `AdhamElsayedAI/MedicalPlab`, select branch `release/final-mentor-mobile-handoff`. Render will parse `render.yaml`.
   - Option B (Manual Web Service): Select **New +** &rarr; **Web Service**, select `AdhamElsayedAI/MedicalPlab`, branch `release/final-mentor-mobile-handoff`, Runtime: **Docker**, Plan: **Free**, Region: **Frankfurt**.
4. **Confirm Plan = Free:**
   Verify that **Free** ($0/month) is selected. Confirm no credit/debit card is requested or charged.
5. **Set Environment Variables:**
   Configure the following in the Render service settings:
   - `MEDICALPLAB_RUNTIME_MODE` = `pilot`
   - `MEDICALPLAB_PLAB_PREVIEW_QA` = `1`
   - `MEDICALPLAB_PHASE_2B_ENABLED` = `1`
   - `MEDICALPLAB_ANATOMY_3D_ENABLED` = `1`
   - `MEDICALPLAB_TUTOR_PROVIDER` = `stub`
   - `MEDICALPLAB_STAGING_GATE_ENABLED` = `1`
   - `STAGING_ACCESS_KEY` = `<choose-a-strong-secret-key>`
   - `ALLOWED_ORIGINS` = `*`
6. **Trigger Deployment:**
   Deploy branch `release/final-mentor-mobile-handoff`.
7. **Obtain Live Staging URL:**
   Capture the provisioned HTTPS URL (e.g., `https://medicalplab-staging.onrender.com`).
8. **Update Vercel Server Environment:**
   In your Vercel Project Settings (`medical-plab`):
   - `MEDICALPLAB_STAGING_BASE_URL` = `<actual Render URL>`
   - `STAGING_ACCESS_KEY` = `<same secret key>`
   - `MENTOR_ACCESS_CODE` = `<mentor password>`

---

## 4. Post-Deployment Verification & Smoke Testing

Once the live Render HTTPS URL is active:

### 1. External Security Gate Verification
```bash
# A. Public Health Probe (Must return HTTP 200 without key)
curl -i https://<render-service>.onrender.com/health

# B. Unauthenticated Version Check (Must return HTTP 401 Unauthorized)
curl -i https://<render-service>.onrender.com/api/v1/version

# C. Invalid Staging Key (Must return HTTP 401 Unauthorized)
curl -i -H "X-Staging-Key: invalid-key" https://<render-service>.onrender.com/api/v1/version

# D. Authenticated Version Check (Must return HTTP 200 OK)
curl -i -H "X-Staging-Key: <YOUR_KEY>" https://<render-service>.onrender.com/api/v1/version

# E. Internal Route Block (Must return HTTP 403 Forbidden even with valid key)
curl -i -H "X-Staging-Key: <YOUR_KEY>" https://<render-service>.onrender.com/internal/audit
```

### 2. Pre-Demo Warm-Up Sequence
Run the warm-up script 5-10 minutes prior to demonstrations to wake the free-tier container from sleep:
```bash
python Scripts/warm_staging.py --url https://<render-service>.onrender.com --staging-key <YOUR_KEY>
```

---

## 5. Cost Language & Resource Limits

> [!NOTE]
> **$0 expected under current Render Free plan and current verified usage limits.**
> - Render Free Web Services provide 750 free instance hours per month across a workspace.
> - Free services automatically spin down after 15 minutes of inactivity.
> - Inbound web requests wake sleeping instances with a cold start of ~30–60 seconds.
> - No intentional paid infrastructure is used.
> - Pricing and terms are subject to Render's current official service terms.
