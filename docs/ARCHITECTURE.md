# MedicalPlab — System Architecture & Technical Design

## 1. Architectural Overview

MedicalPlab is an evidence-grounded medical education and clinical intelligence platform built on two distinct, architecturally decoupled product lanes:
1. **University Learning**: Preclinical undergraduate medical education focusing on mechanistic physiology and basic-science comprehension (Renal Physiology MVP: Glomerular filtration barrier & RAAS mechanisms).
2. **PLAB / Licensing Preparation**: High-stakes licensing examination preparation (UK GMC PLAB 1 / MLA) enforcing strict cryptographic source provenance, automated blocker taxonomy, and mandatory GMC clinician review boundaries.

```mermaid
graph TD
    Learner(["Medical Student / Preclinical Learner / Licensing Candidate"])
    
    subgraph Frontend["Next.js 16.3.4 Client (React 19 + Turbopack)"]
        UI["Product UI & Mode Selector"]
        UniView["University Learning Studio<br/>(/university)"]
        PLABView["PLAB Practice & Review Room<br/>(/)"]
        OfflineCache["Client Fallback Cache"]
    end

    Learner --> UI
    UI --> UniView
    UI --> PLABView
    UI -.-> OfflineCache

    subgraph Gateway["FastAPI Application Layer"]
        MainEntry["Local & Demo Gateway<br/>(main.py:app)"]
        ProdEntry["Strict Pilot / Production Gateway<br/>(production_main.py:app)"]
        AuthMiddleware["CORS, Process-Time Header & Rate Limiting"]
    end

    UniView -- "HTTP REST" --> AuthMiddleware
    PLABView -- "HTTP REST" --> AuthMiddleware
    AuthMiddleware --> MainEntry
    AuthMiddleware --> ProdEntry

    subgraph CoreServices["Shared Backend & AI Subsystems"]
        UniService["University Service<br/>(Renal Basic-Science Question Bank)"]
        PLABService["PLAB V9 Service<br/>(Governance, Quarantine, Provenance)"]
        EvidenceEngine["Canonical Evidence Engine V1.1<br/>(Routing, Field BM25, Weighted RRF, Qwen3-Reranker)"]
        SafetyGate["Central Claim Verifier<br/>(Fail-Closed Safety Gate)"]
        MasteryEngine["Mastery & Progress Engine<br/>(Bayesian Knowledge Tracing)"]
    end

    MainEntry --> UniService
    MainEntry --> EvidenceEngine
    MainEntry --> MasteryEngine
    ProdEntry --> PLABService
    ProdEntry --> UniService

    EvidenceEngine --> SafetyGate

    subgraph DataPersistence["Data & Evidence Storage"]
        UniBank["Data/university/questions.json<br/>(Verified Educational Bank)"]
        PLABBank["Data/questions/cardiorespiratory_batch_1.json<br/>(Public-Safe PLAB Subset)"]
        Corpus["Data/processed/renal_v1/<br/>(16 Open-Access PMC Articles, 2,192 Chunks)"]
        DB["SQLite Persistence<br/>(university.sqlite3 / pilot.db)"]
    end

    UniService --> UniBank
    UniService --> DB
    PLABService --> PLABBank
    PLABService --> DB
    EvidenceEngine --> Corpus
```

---

## 2. Technology Stack & Versions

| Layer | Component | Version / Technology | Architectural Role |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | Next.js | `16.3.4` (Turbopack) | Server Components, fast hydration, client resilience |
| **UI Library** | React | `19.2.8` | Declarative UI state, reactive learning components |
| **Frontend Styling** | TailwindCSS | `4.x` | Modern, responsive medical UI tokens |
| **Icons & Animation** | Lucide / Framer Motion | `1.42.0` / `13.2.0` | Polished micro-interactions and status indicators |
| **Backend Framework** | FastAPI | `0.115+` (Python 3.12/3.11) | Asynchronous ASGI, typed Pydantic contracts |
| **ASGI Server** | Uvicorn | `0.34+` | Production async event loop |
| **Lexical Retrieval** | Custom BM25 | Pure Python / NumPy | Field-aware title (1.0), heading (2.0), body (1.0) |
| **Neural Reranking** | Qwen3-Reranker | `Qwen/Qwen3-Reranker-0.6B` | Cross-encoder contextual relevance verification |
| **Claim Verification** | CentralClaimVerifier | Deterministic Rule Engine | Polarity, numeric consistency, directional entailment |
| **Student Modeling** | Bayesian Knowledge Tracing | Custom BKT | Dynamic mastery updates, weak topic recommendations |
| **Containerization** | Docker | Multi-stage, non-root | Google Cloud Run, HF Spaces, portable deployment |

---

## 3. Product Lanes & Architectural Boundaries

### Lane 1: University Learning
- **Focus:** Preclinical undergraduate medical education.
- **Current MVP:** Renal Physiology (Glomerular filtration barrier & RAAS mechanisms).
- **Taxonomy:** Subject -> Topic -> Question -> Feedback -> Explanation -> Mastery.
- **Contract:** Zero answer key leakage in question payloads (`options` dict without correct key).
- **Safety Status:** `VERIFIED_EDUCATIONAL`. Fail-closed on missing fields or broken encodings.

### Lane 2: PLAB / Licensing Preparation
- **Focus:** High-stakes licensing examinations (UK GMC PLAB 1 / MLA).
- **Governance:** 9-point blocker taxonomy (Blockers A through I).
- **Safety Policy:**
  - 24 out of 36 questions quarantined due to strict evidence/distractor blockers.
  - 0 questions published as "Golden" without GMC clinician sign-off.
  - Complete character-exact span containment in accredited clinical guidelines.

---

## 4. API Entrypoint Specialization

1. **`main.py` (Local & Demo Gateway)**:
   - Provides full developer ergonomics, CORS, Socratic chat (`/ai/chat`), University endpoints (`/api/v1/university/*`), direct evidence queries (`/api/v1/evidence/query`), and student analytics (`/student/*`).
   - Serves as the primary local development and hackathon judge evaluation entrypoint.

2. **`production_main.py` (Strict Pilot & Production Gateway)**:
   - Requires `MEDICALPLAB_RUNTIME_MODE=pilot` or `production`.
   - Enforces data integrity manifests on startup; fails closed if files are missing or modified.
   - Strictly validates PLAB governance counts before serving questions.

---

## 5. Security, Privacy & Integrity Invariants

- **No Live Secrets:** Repository contains zero hardcoded API keys, passwords, or production tokens. Pointers use `.env.example`.
- **No Private Publisher Redistribution:** Full proprietary publisher guideline text remains in the private canonical evidence vault (`plab-evidence-final-v9`); the public repository tracks only open-access PMC literature and public-safe synthetic verification fixtures.
- **Cryptographic Reproducibility:** Every question and evidence chunk is tracked with SHA-256 digests. Line-ending normalization (`UTF8_LF_CANONICAL_TEXT`) ensures cross-platform cryptographic reproducibility.
