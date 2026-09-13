# System Architecture & Technical Design

## 1. Architectural Overview

MedicalPlab is an enterprise-grade AI medical education platform built to prepare international medical graduates and medical students for the UK General Medical Council (GMC) PLAB 1 / Medical Licensing Assessment (MLA).

The platform bridges generative AI with deterministic clinical safety, enforcing exact source-grounded evidence pipelines and formal clinical risk controls (DCB0129).

```text
┌─────────────────────────────────────────────────────────────────┐
│                       Client Applications                       │
│     Next.js 15 Web Application  │  Mobile & API Consumers       │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP / REST / JSON
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Application Gateway                   │
│           (main.py / src/medicalplab/stage_g/product_api.py)    │
│  - Authentication & RBAC        - Rate Limiting & Audit Log     │
│  - CORS & Security Headers      - Multi-Tenant Router           │
└───────┬────────────────────────┬────────────────────────┬───────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│   Learning    │        │   Clinical    │        │  PLAB V9      │
│  & Adaptive   │        │  Simulation   │        │   Evidence    │
│  (Stage-E)    │        │  (Stage-F)    │        │   Pipeline    │
│  - BKT Engine │        │  - OSCE Turn- │        │  - Exact-Span │
│  - Spaced Rep │        │    by-turn    │        │  - Blocker G  │
│  - Analytics  │        │  - Safety Trap│        │  - Fail-Closed│
└───────┬───────┘        └───────┬───────┘        └───────┬───────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Authoritative Evidence Engine                  │
│   (Stage-B Claim Planner & Multi-Source RAG Dense Retriever)    │
│  - BGE-M3 & Qwen-4B Medical Dense Embeddings                    │
│  - Neural Two-Layer Firewall & Contrastive Reranker             │
│  - Canonical Block Parser (NICE, BTS, RCUK, SIGN, PMC XML)      │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Persistence Subsystem                      │
│  - Multi-Tenant Data Store (SQLite / PostgreSQL)                │
│  - Deterministic Question Vault & Checksum Manifests            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Frontend UI** | Next.js 15, React 19, TypeScript | Server Components, fast rendering, type-safe API client |
| **Styling** | Vanilla CSS Design System | Curated medical color palette, zero CSS bloat, fluid responsiveness |
| **Backend API** | FastAPI, Uvicorn, Python 3.11+ | High throughput async ASGI, automatic OpenAPI generation |
| **Data Validation** | Pydantic V2 | Strict type coercion and contract validation across all AI inputs |
| **Adaptive Learning** | Bayesian Knowledge Tracing (BKT) | Empirically grounded cognitive mastery tracking over heuristic scoring |
| **Embeddings & Search** | BGE-M3 / Qwen-4B Domain Adapted | Specialized for clinical entity density and cross-guideline semantics |
| **Evidence Closure** | PLAB V9 SHA-256 Engine | Deterministic cryptographic guarantees for exact source spans |
| **Testing** | Pytest, Pytest-Subtests | Comprehensive unit, integration, and clinical safety test suites |

---

## 3. Core Component Subsystems

### 3.1. Frontend (`frontend/`)
- Modern, clean user interface designed for clinical learners.
- **Interactive Question Player**: Instant feedback with exact guideline citations, atomic claim breakdowns, and distractor refutations.
- **Curriculum Mastery Dashboard**: Specialty-level radar charts and knowledge decay alerts driven by Stage-E BKT.
- **Clinician Review Workspace**: Restricted portal for GMC doctors to inspect technical evidence spans, distractor metrics, and adjudicate questions.

### 3.2. Backend API Gateway (`main.py` & `src/medicalplab/`)
- Modular FastAPI routers under `/api/v1/`:
  - `/questions`: Fetch curriculum items, filter by specialty/system, submit answers.
  - `/analytics`: Real-time student cognitive profile, predicted exam pass probability.
  - `/simulation`: Interactive clinical patient consultation session.
  - `/review`: Authenticated clinician review queue and sign-off endpoints.
  - `/health`: Automated liveness and dependency health checks.

### 3.3. Stage-G Enterprise Multi-Tenancy
- Dedicated tenant partitioning for medical schools and hospital trusts.
- Strict isolation of student progress records, customized institutional curricula, and proprietary question banks.

### 3.4. Persistence & Storage Architecture
- Abstracted persistence interface (`src/medicalplab/plab/persistence.py`).
- Read-only deterministic JSON question versions for immutable release integrity.
- Encrypted SQLite / PostgreSQL for dynamic user sessions, progress histories, and audit events.

---

## 4. Security & Compliance Architecture

1. **Zero Secret Leaks**: All configuration managed through clean environment variables. Template provided in `.env.example`.
2. **Role-Based Access Control (RBAC)**: Fine-grained permissions separating Students, Educators, Reviewers, and Platform Admins.
3. **Data Privacy**: No patient data ingested or stored. Student exam records encrypted at rest.
4. **DCB0129 Compliance**: Integrated clinical risk management protocols and automated safety blocker quarantines.
