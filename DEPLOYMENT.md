# MedicalPlab Production Cloud Deployment Guide

This guide documents the complete production architecture, cloud deployment procedures, environment variable configurations, and automated verification for MedicalPlab's full-stack ecosystem.

---

## 1. Production Architecture Overview

MedicalPlab is decoupled into a globally distributed edge frontend (Vercel) and a high-throughput, evidence-grounded Python AI backend (Render / Railway / Cloud PaaS):

```mermaid
graph TD
    User["Clinician / Student / Faculty<br/>(Any Web or Mobile Device)"]
    
    subgraph FrontendEdge["Vercel Global Edge Network"]
        NextJS["MedicalPlab Next.js 16.3.4 (Turbopack)<br/>https://medical-plab.vercel.app"]
        Cache["Resilient Client-Side Fallback Cache<br/>(Zero-Downtime Offline Continuity)"]
    end
    
    subgraph CloudBackend["Production Cloud Backend (Render / Railway)"]
        FastAPIGW["FastAPI High-Performance Gateway<br/>uvicorn main:app (0.0.0.0:$PORT)"]
        Health["Health Check Endpoint<br/>GET /health (HTTP 200 OK)"]
        CORS["CORS Policy Middleware<br/>Allowed: https://medical-plab.vercel.app"]
    end
    
    subgraph AIPipeline["Medical AI Intelligence Core (Stages B-G)"]
        StageG["Stage-G: Multi-Tenant REST Router & Sessions"]
        StageD["Stage-D: Socratic Tutor & Clinical Safety Gate"]
        StageE["Stage-E: Bayesian Knowledge Tracing (BKT)"]
        StageR["Stage-R: Source-Aware Hybrid Retrieval"]
    end
    
    subgraph KnowledgeBase["Clinical Knowledge & Evidence Layer"]
        NICE["NICE Guidelines (NG185, CG127, NG136)"]
        WHO["WHO Clinical Protocols (Cardiovascular 2021)"]
        PMC["Peer-Reviewed Literature (PubMed Central JATS)"]
    end
    
    User --> NextJS
    NextJS -.-> Cache
    NextJS -- "HTTPS REST (NEXT_PUBLIC_API_URL)" --> FastAPIGW
    FastAPIGW --> Health
    FastAPIGW --> CORS
    FastAPIGW --> StageG
    StageG --> StageD
    StageG --> StageE
    StageG --> StageR
    StageR <--> NICE
    StageR <--> WHO
    StageR <--> PMC

    classDef user fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef edge fill:#1e293b,stroke:#818cf8,stroke-width:2px,color:#f8fafc;
    classDef cloud fill:#022c22,stroke:#10b981,stroke-width:2px,color:#f8fafc;
    classDef ai fill:#31104b,stroke:#c084fc,stroke-width:2px,color:#f8fafc;
    classDef kb fill:#450a0a,stroke:#f59e0b,stroke-width:2px,color:#f8fafc;

    class User user;
    class NextJS,Cache edge;
    class FastAPIGW,Health,CORS cloud;
    class StageG,StageD,StageE,StageR ai;
    class NICE,WHO,PMC kb;
```

---

## 2. Environment Variables Specification

### Frontend (`frontend/.env.local` & Vercel Dashboard)
| Variable | Production Value | Description |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | `https://medicalplab-api.onrender.com` | Base URL of the public Python FastAPI backend. Defaults to `http://localhost:8000` if unset. |

### Backend (Render / Railway / Cloud Container)
| Variable | Production Value | Description |
| :--- | :--- | :--- |
| `PORT` | `8000` (Assigned dynamically by cloud provider) | Port on which Uvicorn binds (`0.0.0.0:$PORT`). |
| `ALLOWED_ORIGINS` | `https://medical-plab.vercel.app,http://localhost:3000` | Comma-separated CORS allowed origins. Default permits all with wildcard fallback. |

---

## 3. Backend Cloud Deployment Guide

### 3.1. Deploying on Render (Blueprint Deployment)

The repository includes a ready-to-use [`render.yaml`](render.yaml) Blueprint:

The repository includes a ready-to-use [`render.yaml`](render.yaml) Blueprint:

```yaml
services:
  - type: web
    name: medicalplab-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.8
      - key: ALLOWED_ORIGINS
        value: https://medical-plab.vercel.app,http://localhost:3000
```

### 3.2. Deploying on Railway

1. Install Railway CLI: `npm i -g @railway/cli`
2. Initialize project: `railway init`
3. Railway automatically detects [`Procfile`](Procfile) and [`requirements.txt`](requirements.txt):
   ```text
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
4. Set environment variables via Railway Dashboard:
   - `ALLOWED_ORIGINS`: `https://medical-plab.vercel.app,http://localhost:3000`
   - `PORT`: `8000`
5. Deploy: `railway up`

### 3.3. Deploying via Docker (Any Container Host)

The repository includes a multi-stage production [`Dockerfile`](Dockerfile):

```bash
# Build Docker image
docker build -t medicalplab-api .

# Run locally on port 8000
docker run -p 8000:8000 -e PORT=8000 medicalplab-api
```

---

## 4. Connecting Frontend (Vercel) to Cloud Backend

Once your backend is deployed:

1. Open your **Vercel Dashboard:** [https://vercel.com/dashboard](https://vercel.com/dashboard).
2. Select the **`medical-plab`** project.
3. Navigate to **Settings** $\to$ **Environment Variables**.
4. Add or update:
   - **Key:** `NEXT_PUBLIC_API_URL`
   - **Value:** `https://YOUR_BACKEND_URL` (e.g. `https://medicalplab-api.onrender.com`)
   - **Environments:** Select **Production**, **Preview**, and **Development**.
5. Click **Save**.
6. Trigger a redeployment:
   - Go to **Deployments** $\to$ Select latest deployment $\to$ Click **Redeploy** (or push a new commit to `main`).

---

## 5. Local Development Workflow

### Starting the Full Stack Locally

#### 1. Backend:
```bash
# In repository root:
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux

pip install -r requirements.txt

# Start production FastAPI backend:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at `http://localhost:8000/docs`.

#### 2. Frontend:
```bash
# In frontend directory:
cd frontend
npm install
npm run dev
```
Application will be live at `http://localhost:3000`.

---

## 6. Automated Testing & Verification

Execute the complete test suite before pushing any changes:

```bash
# Backend unit and cloud API integration tests (196 passing tests)
pytest tests/test_cloud_api.py -v
pytest tests/stage_g/ tests/stage_f/ tests/stage_d/ tests/stage_e/ tests/stage_r/ tests/stage_c/

# Frontend typechecking & production build verification
cd frontend
npm run build
```

---

## 7. Production Endpoints Reference

| Endpoint | Method | Purpose | Sample Response |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | Load balancer health check | `{"status": "healthy", "service": "MedicalPlab API"}` |
| `/` | `GET` | Root discovery & metadata | `{"service": "MedicalPlab...", "status": "healthy"}` |
| `/ai/chat` | `POST` | Grounded Socratic reasoning | `{"explanation": "...", "citations": [...], "safety_validated": true}` |
| `/student/analytics` | `GET` | Bayesian mastery metrics | `{"student_id": "...", "overall_accuracy": 0.57}` |
| `/student/attempts` | `POST` | Record student attempt | `{"attempt_id": "...", "message": "Attempt recorded"}` |
| `/docs` | `GET` | Interactive Swagger UI | OpenAPI 3.1 documentation viewer |
