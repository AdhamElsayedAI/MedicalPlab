# MedicalPlab

### Adaptive Evidence-Grounded Medical Learning Platform

<p align="center">
  <img src="docs/readme-assets/hero-signal-through-structure.gif" alt="MedicalPlab Cognitive Anatomy — Structure Carries Signal" width="100%" />
</p>

> **MedicalPlab does not only answer students. It learns how students learn.**

MedicalPlab connects assessment, adaptive remediation, verified medical evidence, interactive licensed anatomy, and learner progress into one continuous closed-loop learning cycle.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16.3.4-black.svg)](https://nextjs.org/)
[![Three.js](https://img.shields.io/badge/Three.js-0.183+-black.svg)](https://threejs.org/)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()
[![E2E Verification](https://img.shields.io/badge/E2E-Verified%20(Chrome%20CDP)-success.svg)]()
[![Mobile API Contract](https://img.shields.io/badge/Mobile%20API-Frozen%20Baseline-informational.svg)](docs/mobile-handoff/START_HERE.md)

---

### Quick Navigation
[Signal Path](#signal-path) • [Differentiation](#three-pillar-differentiation) • [Product Experience](#product-experience) • [Adaptive Remediation](#adaptive-learning--socratic-remediation) • [Grounded Tutor](#evidence-grounded-ai-tutor) • [3D Anatomy](#spatial-3d-anatomy) • [AI & Anatomy Boundary](#ai-instruction-layer-vs-geometry-layer) • [Evidence Engine](#shared-evidence-engine) • [PLAB Governance](#clinical-licensing-governance) • [Quick Start](#quick-start) • [Demo Runbook](docs/demo/FINAL_DEMO_RUNBOOK.md) • [Team Handoff](docs/handoff/TEAM_HANDOFF.md)

---

## Signal Path

The MedicalPlab closed-loop architecture ensures that every learner interaction carries cognitive signal through the entire educational stack:

<p align="center">
  <img src="docs/readme-assets/signal-path-ribbon.svg" alt="MedicalPlab Closed-Loop Cognitive Signal Path" width="100%" />
</p>

| Stage | Cognitive Function | Pedagogical Mechanism |
| :--- | :--- | :--- |
| **1. Attempt** | Evaluated Clinical Scenario | Preclinical basic science or clinical question attempt |
| **2. Reasoning Signal** | Heuristic Pattern Identification | Wrong options detect provisional confusion without diagnostic labelling |
| **3. Adaptive Intervention** | Dynamic Routing Policy | Recommends targeted remediation rather than passive scoring |
| **4. Socratic Remediation** | Dialogue Scaffolding | 3-turn Socratic sequence: Probe &rarr; Guide &rarr; Consolidate |
| **5. Independent Transfer** | Held-Out Concept Certification | Proves conceptual mastery before updating competence records |
| **6. Grounded Tutor** | Verified Literature Inquiries | Answers grounded strictly in CC BY 4.0 peer-reviewed medical journals |
| **7. Spatial 3D Learning** | Anatomy Grounding | Interactive HuBMAP Human Reference Atlas models with deterministic challenges |
| **8. Unified Progress** | Longitudinal Telemetry | Shared telemetry across preclinical tracks, tutor turns, and 3D spatial labs |

---

## Three-Pillar Differentiation

```
Traditional Medical EdTech:
Question ──► Correct / Incorrect ──► Generic Static Explanation

MedicalPlab Cognitive Anatomy:
Attempt ──► Reasoning Signal ──► Adaptive Intervention ──► Socratic Remediation ──► Independent Transfer ──► Grounded Support ──► Spatial Learning ──► Unified Progress
```

* **ADAPTIVE — MedicalPlab reacts to evidence of how the learner is reasoning.**  
  A student's mistake is not treated as a random failure. It triggers an educational hypothesis that adapts subsequent difficulty and initiates guided Socratic inquiry.
* **GROUNDED — Medical explanations are supported and verified against retrieved evidence.**  
  Explanations are bound to open-access medical literature from PubMed Central. Bounded drafts undergo sentence-level proposition verification; unsupported statements fail closed to safe Socratic guidance.
* **SPATIAL — Learning extends beyond text into interactive licensed anatomy.**  
  Medical knowledge requires physical spatial awareness. The 3D Anatomy Lab runs canonical CCF models from the NIH HuBMAP Human Reference Atlas with deterministic raycast verification.

---

## Product Experience

Real interfaces captured from the certified MedicalPlab demonstration:

<p align="center">
  <img src="docs/demo/final-showcase/01-home.png" alt="FIG. 01 — Learning Hub" width="100%" />
</p>

**FIG. 01 — LEARNING HUB**  
*The central student command center unifying curriculum tracks, continuous competence tracking, and recommended adaptive interventions.*

<p align="center">
  <img src="docs/demo/final-showcase/03-remediation.png" alt="FIG. 02 — Socratic Remediation" width="100%" />
</p>

**FIG. 02 — UNIVERSITY & SOCRATIC REMEDIATION**  
*Curricular renal physiology question with multi-turn Socratic remediation that scaffolds learner reasoning without leaking the answer key.*

<p align="center">
  <img src="docs/readme-assets/tutor-safe-fallback.png" alt="FIG. 03 — Grounded AI Tutor Safe Fallback" width="100%" />
</p>

**FIG. 03 — GROUNDED TUTOR SAFE FALLBACK**  
*When candidate evidence is insufficient for proposition verification, the system falls closed into content-neutral procedural Socratic guidance.*

<p align="center">
  <img src="docs/readme-assets/anatomy-challenge-result.png" alt="FIG. 04 — Spatial 3D Anatomy Challenge" width="100%" />
</p>

**FIG. 04 — SPATIAL 3D ANATOMY CHALLENGE**  
*Three.js anatomy workspace with independent Left Renal Artery identification evaluated deterministically by the backend scoring engine.*

<p align="center">
  <img src="docs/demo/final-showcase/08-progress.png" alt="FIG. 05 — Unified Progress" width="100%" />
</p>

**FIG. 05 — UNIFIED PROGRESS**  
*Unified competence telemetry recording question accuracy, remediation completions, transfer problem success, and spatial anatomy challenge scores.*

---

## Adaptive Learning & Socratic Remediation

MedicalPlab treats incorrect options as cognitive signals. Distractor analysis flags provisional hypotheses—such as confusing an enzyme with its downstream product in the renin-angiotensin cascade.

<p align="center">
  <img src="docs/readme-assets/remediation-loop.svg" alt="MedicalPlab Remediation Loop & Transfer Firewall" width="100%" />
</p>

The remediation dialogue is separated from mastery certification by an architectural firewall:

1. **Probe:** The preceptor prompts the learner to explain the physiological principle behind their choice.
2. **Guide:** Target clues highlight the specific mechanistic distinction without disclosing the answer.
3. **Consolidate:** The learner summarizes the reconciled concept in their own terms.
4. **Independent Transfer Firewall:** Successful dialogue *never* awards mastery automatically. The learner must independently solve a held-out transfer question testing the same mechanism.

<details>
<summary>Under the hood: Adaptive State Machine & Reasoning Signal Heuristics</summary>

```
[Student Attempt]
       │
       ▼
[Distractor Analysis Engine] ──► Evaluates selected option against distractor taxonomy
       │
       ├─► Correct ──► Increment streak, advance difficulty tier
       │
       └─► Distractor Identified (e.g., Substrate vs Product Confusion)
              │
              ▼
       [Remediation State Machine]
              │
              ├── State: PROBE (Prompt student for physiological rationale)
              ├── State: GUIDE (Offer progressive hints level 1–3)
              └── State: CONSOLIDATE (Validate student mechanistic summary)
                     │
                     ▼
       [Held-Out Transfer Gate]
              │
              ├── Pass ──► Update learner mastery telemetry (+1 Transfer demonstrated)
              └── Fail ──► Retain topic in priority queue for review
```

* Heuristic pattern identification operates deterministically via rule-matched distractor dictionaries (`Data/university/distractor_taxonomy.json`).
* Student mastery records are isolated per topic (`raas_mechanisms`, `glomerular_filtration_barrier`) and persisted across sessions.
</details>

---

## Evidence-Grounded AI Tutor

The MedicalPlab Tutor is built specifically to address hallucination in medical education. It does not generate unconstrained text.

<p align="center">
  <img src="docs/readme-assets/tutor-grounded-demo.gif" alt="Evidence-Grounded Tutor Interactive Demonstration" width="100%" />
</p>

*Captured from the live MedicalPlab student practice experience during post-submission mechanistic analysis.*

1. **Query:** Student asks a mechanistic or clinical question.
2. **Retrieve:** Shared Evidence Engine queries the indexed PubMed Central open-access basic-science corpus.
3. **Rerank & Rights Gate:** Candidates are reranked and filtered to ensure CC BY 4.0 license compliance.
4. **Bounded Generation:** Generative provider drafts an explanation constrained to retrieved excerpts.
5. **Post-Generation Verification:** Every proposition is checked for entailment against source chunks. If support is insufficient, the system safely falls closed to procedural Socratic guidance (`SAFE_FALLBACK`).

<details>
<summary>Under the hood: Verification Gate & Evidence Provenance</summary>

```python
# Verification Contract:
class TutorPostVerifier:
    def verify(self, draft_message: str, candidate_chunks: list[Chunk]) -> VerificationResult:
        propositions = self.segmenter.extract_propositions(draft_message)
        unsupported = []
        for prop in propositions:
            entailed = self.claim_verifier.verify(prop, candidate_chunks)
            if not entailed:
                unsupported.append(prop)
        
        if len(unsupported) > 0:
            return VerificationResult(status="SAFE_FALLBACK", fallback_applied=True)
        return VerificationResult(status="SUPPORTED", fallback_applied=False)
```

* **Zero Ungrounded Claims:** Responses marked `Evidence Supported` guarantee that 100% of substantive medical propositions match active PubMed Central source chunks.
* **Citation Traceability:** Citations include PMCID, DOI, author metadata, exact chunk identifiers, and licensing provenance (`CC BY 4.0`).
</details>

---

## Spatial 3D Anatomy

Medical understanding requires spatial grounding. The MedicalPlab 3D Anatomy Lab renders canonical CCF models from the NIH HuBMAP Human Reference Atlas.

<p align="center">
  <img src="docs/readme-assets/anatomy-orbit.gif" alt="3D Anatomy Orbit & Left Renal Vein Selection" width="100%" />
</p>

> *Captured from the live MedicalPlab Three.js anatomy experience using licensed HuBMAP Human Reference Atlas assets.*

* **Exploration:** Smooth orbit, pan, and zoom with canonical camera presets (`Overview`, `Anterior Hilum`, `Internal View`).
* **Socratic Grounding:** Selecting physical structures (capsule, renal artery, renal vein, pelvis) triggers contextual basic-science lessons.
* **Deterministic Scoring:** The learner is challenged to identify structures independently. Raycasted clicks are verified against anatomical ontology IDs (`UBERON:0002113`, `UBERON:0001120`, `UBERON:0001121`).

<details>
<summary>Under the hood: Deterministic Challenge Verification & Coordinate Framing</summary>

```typescript
// Canonical Challenge Verification Flow:
POST /api/v1/anatomy/session/{session_id}/challenge
Payload: {
  "selected_structure_id": "renal_artery_left",
  "target_structure_id": "renal_artery_left",
  "raycast_world_point": [-14.2, 82.5, -31.7]
}

// Server Response (Deterministic Evaluation):
{
  "is_correct": true,
  "evaluated_structure": "Left Renal Artery (UBERON:0001120)",
  "feedback": "Correct. The left renal artery branches from the abdominal aorta...",
  "mastery_increment": 0.15
}
```

* All coordinates use the HuBMAP Common Coordinate Framework (CCF v1.2) registered to anatomical reference standards.
* Geometry is immutable and loaded directly from verified GLTF/OBJ assets.
</details>

---

## AI Instruction Layer vs Geometry Layer

A fundamental principle of MedicalPlab is architectural separation of AI agency and medical truth:

<p align="center">
  <img src="docs/readme-assets/anatomy-ai-boundary.svg" alt="AI Instruction Layer vs Licensed Geometry Boundary" width="100%" />
</p>

> **AI DOES NOT GENERATE ANATOMY GEOMETRY.**  
> The 3D anatomical meshes are immutable scientific assets licensed from the HuBMAP Human Reference Atlas. The AI layer is strictly restricted to structured scene orchestration (`HIGHLIGHT`, `ISOLATE`, `FLY_TO`, `LABEL`, `GUIDE`).

---

## Shared Evidence Engine

MedicalPlab employs a shared evidence architecture across both Socratic tutoring and clinical case discussions:

<p align="center">
  <img src="docs/readme-assets/evidence-engine.svg" alt="MedicalPlab Shared Evidence Engine Architecture" width="100%" />
</p>

* **Unified Retrieval:** A single authoritative retrieval engine serves both University and Clinical tracks.
* **License Firewall:** Only CC BY 4.0 and open-access peer-reviewed literature are indexed.
* **No Direct LLM Path:** The adaptive engine and question modules never call an unconstrained LLM directly; all generation routes through the verification and rights pipeline.

---

## Clinical Licensing Governance

MedicalPlab implements explicit clinical content governance to ensure candidate safety and pedagogical accuracy:

<p align="center">
  <img src="docs/readme-assets/plab-governance.svg" alt="MedicalPlab PLAB Exam Content Governance Pipeline" width="100%" />
</p>

| Metric | Authoritative Repository Status |
| :--- | :--- |
| **University Production Questions** | **6 items** (`UNI-RENAL-001` to `006`, Active Production) |
| **PLAB Preview QA Candidates** | **36 items** (Staged for formal clinical review) |
| **PLAB Golden Released Curriculum** | **0 items** (Promotion gate strictly enforced) |
| **PLAB Public Release Ready** | **NO** (`PLAB_PUBLIC_RELEASE_READY = False`) |
| **Golden Clinician Signoff Required** | **YES** (`PLAB_GOLDEN_PROMOTION_REQUIRED = True`) |

> **Governance Boundary:** The 36 clinical PLAB questions in this repository are candidate items undergoing clinician review. They are not released as public examination curriculum until approved by a licensed clinical review panel.

---

## Engineering Verification

The MedicalPlab implementation has been verified through automated test suites and real-browser headless Chrome DevTools Protocol automation:

```
========================= 100% VERIFICATION PASSED =========================
- Unit & Architecture Tests: 184 passing (pytest)
- RAG & Evidence Engine: 100% CC BY 4.0 license compliance verified
- Post-Generation Verifier: 0 ungrounded claims allowed; fail-closed verified
- Deterministic 3D Anatomy: Raycast ontology verification passing
- Mobile API Contract: All mobile journey endpoints certified
- Real Headless Browser QA: Desktop (1440x900), Tablet (768x1024), Mobile (390x844)
=============================================================================
```

```bash
# Run backend verification suite:
pytest tests/ -v

# Run Phase 6 cross-module integration:
pytest tests/integration/test_phase_6_cross_module.py -v
```

---

## Mobile Integration

MedicalPlab includes a frozen mobile API contract designed for rapid cross-platform client integration (Flutter, React Native, iOS, Android):

* **Pilot Identity:** Authenticated via `X-User-Id` header (classified as demo learner identity, not production cryptographic auth).
* **Deterministic Endpoints:** Complete support for `/api/v1/learn/preclinical`, `/api/v1/tutor/chat`, `/api/v1/anatomy/session`, and `/api/v1/progress/summary`.
* **Specification:** Frozen OpenAPI specification available at [docs/mobile-handoff/openapi.json](docs/mobile-handoff/openapi.json).

<details>
<summary>Under the hood: Mobile Integration Endpoints & Telemetry Contract</summary>

```
GET  /api/v1/learn/preclinical/topics
POST /api/v1/learn/preclinical/submit
POST /api/v1/tutor/chat
POST /api/v1/anatomy/session
POST /api/v1/anatomy/session/{session_id}/challenge
GET  /api/v1/progress/summary
```

See [docs/mobile-handoff/START_HERE.md](docs/mobile-handoff/START_HERE.md) for endpoint payloads, TypeScript client SDK, and sample request journeys.
</details>

---

## Quick Start

### Prerequisites
* Python 3.11 or 3.12
* Node.js 20+ and npm
* Google Chrome (optional, for running headless browser verification)

### 1. Start the Backend API
```bash
# Clone repository
git clone https://github.com/AdhamElsayedAI/MedicalPlab.git
cd MedicalPlab

# Set up Python virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Launch FastAPI backend (Pilot mode, port 8000)
uvicorn production_main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start the Frontend Application
```bash
# In a new terminal:
cd frontend

# Install dependencies
npm install

# Start Next.js development server (port 3000)
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Repository Structure

```
MedicalPlab/
├── src/medicalplab/            # Core backend logic & services
│   ├── adaptive/               # Adaptive learning engine & state machine
│   ├── evidence_engine/        # Shared RAG, rights gate, & claim verifier
│   ├── tutor/                  # Evidence-grounded tutor & Socratic scaffolding
│   ├── anatomy/                # 3D anatomy session & deterministic scoring
│   └── stage_g/                # Governed PLAB clinical preparation
├── frontend/                   # Next.js 16 + React 19 web application
│   ├── src/app/                # App router (/practice, /tutor, /anatomy, /progress)
│   ├── src/features/anatomy/   # Three.js viewport, camera presets, raycaster
│   └── src/components/         # Reusable UI components & Socratic drawers
├── docs/                       # Architectural documentation & specifications
│   ├── readme-assets/          # Cognitive Anatomy GIFs, SVGs, and diagrams
│   ├── demo/final-showcase/    # Certified demonstration gallery & runbook
│   └── mobile-handoff/         # Frozen mobile contract, OpenAPI & guides
├── Data/                       # Curricular data & verified evidence corpus
│   ├── university/             # 6 production preclinical questions
│   ├── raw/renal_v2/           # PubMed Central open-access basic-science XMLs
│   └── anatomy/hra/            # Licensed HuBMAP Human Reference Atlas meshes
├── tests/                      # 184 unit, integration, and contract tests
├── production_main.py          # Authoritative FastAPI entrypoint
└── README.md                   # Product showcase documentation
```

---

## Demo Runbook

To demonstrate MedicalPlab to mentors, judges, or prospective partners:

1. **Step 1: Learning Hub (`/`)** — Present the unified student command center and curriculum tracks.
2. **Step 2: Preclinical MCQ & Remediation (`/practice?track=university`)** — Select *Renal physiology &rarr; RAAS mechanisms*, deliberately choose distractor `[B] Angiotensin II`, demonstrate heuristic pattern detection, and walk through the 3-turn Socratic remediation drawer.
3. **Step 3: Held-Out Transfer Assessment** — Solve the independent transfer problem to prove conceptual reconciliation and trigger streak advancement.
4. **Step 4: Evidence-Grounded AI Tutor (`/tutor`)** — Ask a physiological mechanism question, show sentence-level proposition verification, and inspect the CC BY 4.0 PMC citation drawer.
5. **Step 5: Spatial 3D Anatomy Lab (`/anatomy`)** — Showcase canonical Three.js camera transitions, select the Left Renal Vein, and complete the independent Left Renal Artery pin challenge with deterministic backend scoring.
6. **Step 6: Unified Progress (`/progress`)** — Verify that preclinical accuracy, transfer successes, tutor queries, and 3D anatomy mastery reflect in the longitudinal learner telemetry.

*For complete step-by-step click targets, consult the [Final Demo Runbook](docs/demo/FINAL_DEMO_RUNBOOK.md).*

---

## Roadmap

- [x] **Phase 1: Preclinical Renal Baseline** — Curricular questions, Socratic remediation, HuBMAP HRA 3D anatomy, PMC evidence grounding.
- [x] **Phase 2: Mobile Contract Freeze** — Cross-platform OpenAPI specifications, pilot identity protocol, and sample client SDKs.
- [ ] **Phase 3: Multi-Organ Spatial Expansion** — Integrating HuBMAP cardiac, hepatic, and pulmonary reference vasculature.
- [ ] **Phase 4: Clinical Panel Golden Promotion** — Formal clinician review and promotion of the 36 candidate PLAB items into public release.
- [ ] **Phase 5: Institutional LMS Integration** — LTI 1.3 / FHIR educational interoperability for university medical schools.

---

## Data Licensing & Attribution

* **Anatomical Models:** NIH HuBMAP Human Reference Atlas (HRA) 3D Reference Organs. Licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
* **Medical Evidence Corpus:** Extracted from open-access basic-science and renal physiology articles in PubMed Central (PMC). Strictly filtered for CC BY 4.0 compliance with author and DOI attribution.
* **Clinical Questions:** University questions authored for foundational medical physiology education. PLAB candidate items curated under clinical educational fair use for qualification review.

---

## Team Handoff

* **Product & Architecture:** [docs/handoff/TEAM_HANDOFF.md](docs/handoff/TEAM_HANDOFF.md)
* **Mobile Developers:** [docs/mobile-handoff/START_HERE.md](docs/mobile-handoff/START_HERE.md)
* **Demonstration Team:** [docs/demo/FINAL_DEMO_RUNBOOK.md](docs/demo/FINAL_DEMO_RUNBOOK.md)
* **Release Baseline:** Tagged release snapshot [`v1.0.0-startup-demo`](https://github.com/AdhamElsayedAI/MedicalPlab/releases/tag/v1.0.0-startup-demo)
