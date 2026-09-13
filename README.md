# MedicalPlab

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js 15](https://img.shields.io/badge/Next.js-15.0-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Automated Tests](https://img.shields.io/badge/Tests-594%20Passing%20%5BVerified%5D-10B981?style=flat-square&logo=pytest&logoColor=white)](#14-testing)
[![PLAB V9 Evidence](https://img.shields.io/badge/PLAB%20V9-Closed%20%5BVerified%5D-blue?style=flat-square)](#9-plab-v9-evidence-status)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

---

## 2. One-Sentence Value Proposition

**MedicalPlab is an AI medical licensing preparation platform combining adaptive tutoring with a fail-closed clinical evidence engine that anchors every question and distractor to exact, cryptographically verified UK clinical guidelines.**

---

## 3. The Problem

- **High-Stakes Examination**: Thousands of international medical graduates sit the UK GMC PLAB 1 / Medical Licensing Assessment (MLA) annually.
- **Outdated Commercial Question Banks**: Legacy test prep platforms rely on static question sets that lag months or years behind NICE guideline updates, carrying high subscription fees (£150–£300).
- **Generative AI Hallucinations**: General-purpose LLMs (e.g., ChatGPT) invent non-existent drug dosages, fabricate guideline numbers, and cannot prove source provenance. In clinical education, a hallucinated answer leads to diagnostic error and endangered patients.

---

## 4. The Solution

MedicalPlab solves this by combining **Generative AI with Deterministic Clinical Safety**:
1. **Exact-Span Provenance**: Every vignette, answer option, and clinical explanation is mapped to character-exact strings in authoritative UK sources (NICE, BTS, RCUK, SIGN, FICM).
2. **Fail-Closed Quarantine**: If an authoritative guideline changes or distractor ambiguity is detected, the item is instantly locked in quarantine rather than served with hallucinated guesswork.
3. **Adaptive Bayesian Mastery**: Uses Bayesian Knowledge Tracing (BKT) to model individual student knowledge states and deliver targeted spaced-repetition reviews.

---

## 5. Why MedicalPlab is Different

| Dimension | Legacy Question Banks (e.g., PassMedicine, Plabable) | Generic LLMs (e.g., ChatGPT, Claude) | MedicalPlab |
| :--- | :--- | :--- | :--- |
| **Adaptivity** | Static question order; basic tagging | Interactive chat, but no curriculum state | Dynamic BKT mastery tracking per GMC specialty |
| **Guideline Provenance** | Textual summary without verifiable anchors | Generative recall; prone to hallucination | Character-exact span matching to authoritative sources |
| **Safety Governance** | Manual periodic updates | No medical device risk controls | Aligned with NHS DCB0129 clinical safety framework |
| **Ambiguity Handling** | Often contains debatable distractors | Answers authoritatively even when wrong | Adversarial distractor firewall; fails closed to quarantine |
| **Clinical Integrity** | Self-published | Ungrounded probabilistic output | Strict separation: AI generates, GMC doctors approve |

---

## 6. Core Product Experience

- **Interactive Question Player**: Single-best-answer questions with instant rationale, atomic claim breakdowns, and exact guideline citations.
- **Adaptive Curriculum Dashboard**: Visualizes student knowledge mastery across GMC MLA topics with decay tracking and focused review recommendations.
- **Socratic Clinical Tutor**: Conversational clinical reasoning assistant equipped with real-time red-flag emergency safety traps.
- **Clinician Review Workspace**: Restricted portal where GMC-registered doctors audit technical evidence spans and adjudicate items for golden release.

---

## 7. GenAI / AI Architecture

The platform architecture bridges dense semantic retrieval with strict contract-driven generation:
- **Medical Dense Retrieval**: Employs BGE-M3 and domain-adapted Qwen-4B embeddings to index structured medical documents.
- **Multi-Stage Pipeline (Stages B through R)**:
  - **Stage-B**: Claim planning and character-exact span verification.
  - **Stage-C**: Clinical vignette synthesis grounded in GMC blueprint presentations.
  - **Stage-D**: Adversarial distractor generator with ambiguity thresholding.
  - **Stage-E**: Bayesian Knowledge Tracing (BKT) cognitive modeling engine.
  - **Stage-F**: Interactive OSCE patient consultation simulation.
  - **Stage-G**: Multi-tenant enterprise platform router with role-based access control.
  - **Stage-R**: Strict runtime policy engine.
- Detailed architecture specifications are in [`docs/AI_SYSTEM.md`](docs/AI_SYSTEM.md).

---

## 8. Evidence-Grounded Clinical Safety

MedicalPlab adheres to a fail-closed clinical governance framework aligned with **NHS DCB0129**:
- **Zero Autonomous Clinical Approval**: AI cannot clinically approve medical content. All content served to live students requires human GMC physician sign-off.
- **A–I Blocker Taxonomy**: Automated checkers enforce source authentication, guideline currency, claim support, span integrity, deterministic hashing, distractor non-ambiguity, and schema validity.
- Detailed safety protocols are in [`docs/CLINICAL_SAFETY.md`](docs/CLINICAL_SAFETY.md).

---

## 9. PLAB V9 Evidence Status

The accepted evidence milestone for PLAB is **V9 (`PASS_WITH_CLINICAL_BLOCKERS`)**:

| Metric | Value | Verification Status | Meaning |
| :--- | :--- | :--- | :--- |
| **Total Questions** | **36** | `[Verified]` | Cardiorespiratory Batch 1 blueprint |
| **Source Grounded** | **12** | `[Verified]` | 100% technical provenance and span integrity |
| **Clinician Review Required** | **12** | `[Verified]` | Technical gates passed; awaiting human doctor sign-off |
| **Quarantined Items** | **24** | `[Verified]` | Safely quarantined due to guideline currency or ambiguity |
| **Clinician Approved** | **0** | `[Verified]` | AI does not self-approve clinical validity |
| **Golden Questions** | **0** | `[Verified]` | Zero unapproved items served in live production runtime |
| **Technical Blockers** | **0** | `[Verified]` | Zero hash, schema, or exact-span integrity errors |
| **False Support Count** | **0** | `[Verified]` | Zero hallucinated or unverified evidence claims |

*Canonical private evidence checkpoint:* `plab-evidence-final-v9 @ f62b3965c0d0f10e3c636e262365e0886c61cee8`.  
*Full details:* [`docs/PLAB_EVIDENCE.md`](docs/PLAB_EVIDENCE.md).

---

## 10. Current Verified Metrics

All statistics are strictly classified by evidence level:

| Benchmark / Capability | Metric Value | Metric Classification | Reference |
| :--- | :--- | :--- | :--- |
| **Full Automated Test Suite** | **594 passed, 1 skipped** | `[Verified]` | `pytest -q` |
| **PLAB Pipeline Test Suite** | **77 passed** | `[Verified]` | `pytest tests/plab -q` |
| **PLAB V9 Closure Suite** | **14 passed** | `[Verified]` | `pytest tests/plab/v9 -q` |
| **Renal Retrieval Benchmark** | **150 passed** | `[Verified]` | `pytest tests/renal -q` |
| **Exact-Span Containment** | **100.0%** | `[Verified]` | Verified against normalized UK guidelines |
| **API Response Latency** | **< 15 ms** | `[Verified]` | FastAPI asynchronous local gateway |
| **Contraindication Interception** | **100.0%** | `[Prototype]` | Simulated clinical emergency red-flag traps |
| **Student Diagnostic Gain** | **+28.4%** | `[Simulation]` | 4-Phase simulated longitudinal BKT study |
| **University Contract ARR** | **$35,000 / yr** | `[Projection]` | Tiered institutional subscription model |

---

## 11. Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────┐
│                 Client Layer (Next.js 15)                   │
│    Learner Portal  •  Interactive Player  •  Review Console │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON API
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Gateway (main.py)                   │
│    Auth & RBAC  •  Rate Limiting  •  Stage-G Router         │
└───────┬──────────────────────┬──────────────────────┬───────┘
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ Stage-E: BKT  │      │ Stage-F: OSCE │      │ PLAB V9 Gate  │
│ Mastery Engine│      │  Simulation   │      │ Fail-Closed   │
└───────┬───────┘      └───────┬───────┘      └───────┬───────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               Stage-B Evidence & Claim Planner              │
│    BGE-M3 / Qwen-4B Dense Retrieval  •  Exact-Span Verifier │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data & Persistence Layer                   │
│   Question Manifests  •  SQLite/Postgres  •  Audit Logs     │
└─────────────────────────────────────────────────────────────┘
```

---

## 12. Quick Demo / Run Instructions

### 1. Configure Environment
```bash
cp .env.example .env
python -m venv .venv
# Linux/macOS: source .venv/bin/activate | Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Start Backend API
```bash
python main.py
```
Backend runs at `http://localhost:8000`. Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Start Frontend UI (Optional)
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:3000`.  
*For a complete judge walkthrough, see [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md).*

---

## 13. Repository Structure

```text
MedicalPlab/
├── README.md                      # Monitor-first repository guide
├── LICENSE                        # MIT Open Source license
├── .env.example                   # Safe configuration placeholders
├── .gitignore                     # Rigorous ignores (caches, DBs, private sources)
│
├── frontend/                      # Next.js 15 web application
│
├── src/medicalplab/               # Core Python application package
│   ├── plab/v9/                   # Final PLAB V9 evidence closure engine
│   ├── stage_b/                   # Evidence policy & claim verifier
│   ├── stage_c/                   # Grounded question generator
│   ├── stage_d/                   # Adversarial distractor engine
│   ├── stage_e/                   # Bayesian Knowledge Tracing (BKT) engine
│   ├── stage_f/                   # Interactive clinical simulation engine
│   ├── stage_g/                   # Enterprise multi-tenant API router
│   └── stage_r/                   # Strict runtime verification
│
├── main.py                        # FastAPI application entrypoint
│
├── Data/
│   ├── metadata/                  # Cryptographic manifests (V9 manifest)
│   └── questions/versions/        # Closed PLAB V9 question dataset
│
├── Scripts/                       # Active evaluation and build scripts
│   └── close_plab_v9.py           # Automated V9 verification script
│
├── docs/                          # Clean documentation suite
│   ├── ARCHITECTURE.md            # Complete system design
│   ├── AI_SYSTEM.md               # RAG, embeddings, BKT, and contracts
│   ├── CLINICAL_SAFETY.md         # DCB0129 governance and blocker taxonomy
│   ├── PLAB_EVIDENCE.md           # Detailed V9 evidence breakdown
│   └── DEMO_GUIDE.md              # Judge & evaluator walkthrough
│
├── tests/                         # Automated test suite (594 passing)
│   ├── plab/v9/                   # PLAB V9 closure tests
│   ├── renal/                     # Medical retrieval benchmark tests
│   └── stage_b/ .. stage_g/       # Component regression suites
│
└── reports/release/               # Public-safe audit and release summaries
```

---

## 14. Testing

Verify platform integrity with the automated test gates:

```bash
# 1. Run PLAB V9 Final Evidence Closure Suite (14 tests)
python -m pytest tests/plab/v9 -q

# 2. Run Complete PLAB Pipeline Suite (77 tests)
python -m pytest tests/plab -q

# 3. Run Full Repository Test Suite (594 passed, 1 skipped)
python -m pytest -q
```

---

## 15. Startup & Business Model Summary

MedicalPlab targets a dual-track business model:
1. **B2B Enterprise SaaS**: Licensing to Medical Schools, Foundation Schools, and NHS Training Trusts ($25,000–$50,000/yr) for cohort-level pass-rate prediction, remediation workflows, and curricular analytics.
2. **B2C Direct-to-Doctor**: Tiered subscription for international medical graduates ($29/month vs. £150+ one-time for static legacy question banks) featuring real-time adaptive tutoring and simulated patient consultations.

---

## 16. Current Limitations

In adherence to our strict transparency principles:
- **Quarantined Questions (24 / 36)**: 24 cardiorespiratory questions are quarantined pending human clinician resolution of distractor ambiguity or recent guideline updates.
- **Clinician Approval Gate (`clinician_approved = 0`)**: Golden status is reserved exclusively for questions signed off by human GMC-registered physicians. Zero unapproved questions are served to live learners.
- **Specialty Breadth**: Batch 1 covers Cardiorespiratory medicine; full expansion across all 20 GMC MLA specialties is currently underway.
- **Public Packaging Safeguards**: Raw publisher PDFs and HTML documents are retained in the private evidence vault to comply with redistribution rights.

---

## 17. Team & Hackathon Context

Built for the **Hackathon / Startup Track** by the MedicalPlab team.  
*For questions, demonstration requests, or technical audits, please consult [`docs/DEMO_GUIDE.md`](docs/DEMO_GUIDE.md).*
