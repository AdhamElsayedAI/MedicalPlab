# MedicalPlab — Production Deployment Guide

This guide documents the production deployment architecture, container build procedures, environment variable configurations, and automated operational verification for the MedicalPlab ecosystem.

---

## 1. Production Architecture Overview

MedicalPlab decouples high-performance client presentation from clinical AI reasoning and evidence verification:

```mermaid
graph TD
    User(["Clinician / Student / Faculty<br/>(Any Web or Mobile Device)"])
    
    subgraph FrontendEdge["Vercel Global Edge Network"]
        NextJS["MedicalPlab Next.js 16.3.4 (React 19)<br/>https://medical-plab.vercel.app"]
        Cache["Resilient Client-Side Fallback Cache<br/>(Offline Continuity)"]
    end
    
    subgraph CloudBackend["Production Cloud Backend (Google Cloud Run / Render)"]
        FastAPIGW["FastAPI High-Performance Gateway<br/>(uvicorn main:app or production_main:app)"]
        Health["Health Check Probes<br/>GET /health (HTTP 200 OK)"]
        CORS["CORS Policy Middleware<br/>Allowed: https://medical-plab.vercel.app"]
    end
    
    subgraph AIPipeline["Medical AI Intelligence Core"]
        EvidenceEngine["Evidence Engine V1.1<br/>(Document Router, Field BM25, RRF, Qwen3-Reranker)"]
        UniversityService["University Learning Service<br/>(Renal Basic-Science Track)"]
        PLABService["PLAB V9 Service<br/>(Governance, Quarantine, Provenance)"]
        ClaimVerifier["Central Claim Verifier<br/>(Fail-Closed Safety Gate)"]
    end
    
    subgraph KnowledgeBase["Clinical Knowledge & Evidence Layer"]
        PMC["Peer-Reviewed Literature (PubMed Central JATS DOC-PMC-RENAL-*)"]
        NICE["NICE Guidelines & UK Protocols (NICE, BTS, RCUK, SIGN)"]
    end
    
    User --> NextJS
    NextJS -.-> Cache
    NextJS -- "HTTPS REST (NEXT_PUBLIC_API_URL)" --> FastAPIGW
    FastAPIGW --> Health
    FastAPIGW --> CORS
    FastAPIGW --> UniversityService
    FastAPIGW --> PLABService
    FastAPIGW --> EvidenceEngine
    EvidenceEngine --> ClaimVerifier
    EvidenceEngine <--> PMC
    EvidenceEngine <--> NICE
```

---

## 2. Entrypoints: `main.py` vs `production_main.py`

MedicalPlab provides two explicit, specialized FastAPI entrypoints:

| Dimension | `main.py` | `production_main.py` |
| :--- | :--- | :--- |
| **Intended Environment** | Local development, interactive demos, judges | Strict pilot & institutional production |
| **Runtime Mode** | Flexible demo runtime | Requires `MEDICALPLAB_RUNTIME_MODE=pilot` or `production` |
| **Socratic AI Chat (`/ai/chat`)** | Enabled (grounded with Evidence Engine V1.1) | Fails closed on unverified inquiries |
| **Data Manifest Check** | Logged on startup | Strict blocker: aborts startup on mismatch |
| **PLAB Governance Gate** | Serves review questions in preview mode | Strictly serves 0 questions if Golden count is 0 |
| **University Track** | Active (`/api/v1/university/*`) | Active (`/api/v1/university/*`) |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` | `uvicorn production_main:app --host 0.0.0.0 --port $PORT` |

---

## 3. Deployment Classification Matrix

MedicalPlab distinguishes between canonical production deployments, supported optional targets, and retired legacy configurations:

| Tier | Target Platform | Component | Configuration Assets | Status & Support Level |
| :--- | :--- | :--- | :--- | :--- |
| **CANONICAL** | **Google Cloud Run** | Backend Cloud API | `Dockerfile`, `cloudbuild.yaml`, `.github/workflows/deploy-cloud-run.yml` | Fully automated production deployment with auto-scaling, unprivileged non-root container, and fail-closed readiness probes. |
| **CANONICAL** | **Vercel** | Web Client UI | `frontend/vercel.json`, `frontend/package.json` | Global edge distribution for Next.js 16.3.4 (React 19) client application at `https://medical-plab.vercel.app`. |
| **SUPPORTED OPTIONAL** | **Docker Standalone** | Backend API | `Dockerfile`, `deploy/deploy_cloud_run.sh` | Local developer containers, self-hosted Docker hosts, or ECS/GKE clusters. |
| **SUPPORTED OPTIONAL** | **Render PaaS** | Backend API | `render.yaml` | Supported PaaS deployment running `production_main:app` with automated health check probes. |
| **LEGACY / RETIRED** | **Heroku / Procfile** | Process Runner | `Procfile` (obsolete) | Legacy Heroku-style process runner; unmaintained and superseded by containerized Cloud Run deployment. |

---

## 4. Deployment Pathways

### Pathway A: Google Cloud Run (Canonical Backend)

The repository includes a production Dockerfile and automated deployment scripts:

1. **Automated Shell Deployment**:
   ```bash
   # Using PowerShell:
   .\deploy\deploy_cloud_run.ps1 -ProjectId "YOUR_GCP_PROJECT_ID" -Region "us-central1"
   
   # Using Bash:
   bash ./deploy/deploy_cloud_run.sh YOUR_GCP_PROJECT_ID us-central1
   ```

2. **Automated CI/CD via GitHub Actions**:
   `.github/workflows/deploy-cloud-run.yml` automatically builds the container image using Google Cloud Build (`cloudbuild.yaml`) and deploys to Cloud Run on push to main branches.

### Pathway B: Vercel (Canonical Frontend)

1. Connect the `frontend/` directory to Vercel.
2. Vercel automatically detects `frontend/vercel.json` and Next.js 16 Turbopack settings.
3. Set environment variable:
   - `NEXT_PUBLIC_API_URL`: URL of the deployed Google Cloud Run backend API.

### Pathway C: Docker Standalone (Supported Optional)

Build and run the non-root container locally or on any container platform:

```bash
# Build production container image
docker build -t medicalplab-api:latest .

# Run container with environment variables
docker run -d \
  -p 8000:8000 \
  -e PORT=8000 \
  -e ALLOWED_ORIGINS="http://localhost:3000,https://medical-plab.vercel.app" \
  -e MEDICALPLAB_RUNTIME_MODE=pilot \
  --name medicalplab \
  medicalplab-api:latest
```

### Pathway D: Render PaaS (Supported Optional)

The repository includes a declarative `render.yaml`:
1. Connect your GitHub repository to [Render.com](https://render.com).
2. Render detects `render.yaml` automatically.
3. Deploys `production_main:app` with automated health checking on `/health`.

---

## 5. Environment Variables Reference

| Variable | Default | Required | Description |
| :--- | :--- | :---: | :--- |
| `PORT` | `8000` | No | Listening port for Uvicorn ASGI server |
| `ALLOWED_ORIGINS` | `https://medical-plab.vercel.app,http://localhost:3000` | No | Comma-separated list of allowed CORS origins |
| `MEDICALPLAB_RUNTIME_MODE` | `pilot` | For `production_main.py` | Runtime mode: `demo`, `pilot`, or `production` |
| `MEDICALPLAB_DATA_ROOT` | `./Data` | No | Root path to public-safe medical data and manifests |
| `MEDICALPLAB_PLAB_PREVIEW_QA` | `false` | No | When `true`, allows preview of unapproved PLAB questions for internal QA |
| `MEDICALPLAB_UNIVERSITY_DB` | `Data/persistence/university.sqlite3` | No | SQLite database path for University learner progress |

---

## 6. Health Probes & Verification

Verify the deployed service:

```bash
# 1. Health Probe (returns 200 OK with uptime and platform info)
curl -s http://localhost:8000/health | jq .

# 2. Production Readiness Probe (production_main.py only)
curl -s http://localhost:8000/ready | jq .

# 3. Direct Canonical Evidence Engine Query
curl -s -X POST http://localhost:8000/api/v1/evidence/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the function of podocytes?", "mode": "UNIVERSITY"}' | jq .
```
