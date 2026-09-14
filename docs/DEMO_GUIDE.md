# MedicalPlab — Mentor & Judge Demo Guide

**Demo Duration:** 3–5 minutes  
**Target Audience:** Technical mentors, hackathon judges, medical education evaluators, clinical safety auditors  
**Interface:** Next.js Web UI (`http://localhost:3000`) or direct REST API (`http://localhost:8000`)  

---

## 1. Demo Prerequisites & Quick Launch (Under 60 Seconds)

Launch both services in separate terminals:

```bash
# Terminal 1: Backend API Gateway
python main.py
# Running on http://localhost:8000

# Terminal 2: Next.js Frontend
cd frontend
npm run dev
# Running on http://localhost:3000
```

---

## 2. Recommended 3–5 Minute Walkthrough Sequence

```
Step 1: Welcome & Positioning (30s)
  │
Step 2: University Learning Track (45s)
  │
Step 3: Answer a Real Question & Trace Feedback (45s)
  │
Step 4: Mastery Update & Next Action (30s)
  │
Step 5: Inspect PLAB Governance Separation (45s)
  │
Step 6: Evidence Engine — Supported Query (45s)
  │
Step 7: Inspect Cryptographic Source Grounding (30s)
  │
Step 8: Safety Verification — Unsupported Query (30s)
  │
Step 9: Fail-Closed Clinical Abstention (30s)
  │
Step 10: Technical Architecture Review (30s)
```

---

### Step 1: Open MedicalPlab & Platform Positioning (30s)
- Navigate to `http://localhost:3000`.
- **Key Talking Point:**  
  *"MedicalPlab is an evidence-grounded medical intelligence platform built on two distinct product lanes: **University Learning** for undergraduate foundational medical science, and **PLAB / Licensing Preparation** for high-stakes clinical exam practice. Every answer is grounded in accredited medical literature with mathematical safety boundaries."*

---

### Step 2: Show University Learning Track (45s)
- Click into the **University Track** (`/university` or navigate to University Learning).
- Select **Renal Physiology** -> Topic: **Glomerular filtration barrier** (or **RAAS mechanisms**).
- **Key Talking Point:**  
  *"The University track serves preclinical medical students. The Renal Physiology MVP covers mechanistic basic science with zero clinical ambiguity. Questions are served without answer leaks."*

---

### Step 3: Answer a Real Renal Question (45s)
- Present the question:
  > *"Which pair of cell types forms the two cellular sides of the glomerular filtration barrier?"*
- Select option: **Fenestrated endothelial cells and podocytes** (Option D).
- Click **Submit Answer**.
- Observe the instant feedback:
  - Correctness indicator (`is_correct: true`).
  - Comprehensive mechanistic explanation explaining the three filtration layers (endothelium, GBM, podocyte foot processes).
  - Exact accredited citation from PubMed Central literature (`DOC-PMC-RENAL-0004`).

---

### Step 4: Show Explanation, Mastery & Next Action (30s)
- Inspect the student progress drawer or badge.
- Observe:
  - Total questions attempted updates to `1`.
  - Accuracy: `100%`.
  - Topic mastery status: updated from `beginner` toward `competent`.
  - Recommended Next Action: System dynamically recommends the next sequential question or weak topic based on student performance.

---

### Step 5: Show Architectural Separation from PLAB Preparation (45s)
- Contrast the University Track with the PLAB Preparation lane.
- **Key Talking Point:**  
  *"MedicalPlab strictly enforces domain separation. University preclinical basic-science questions use `UNI-` IDs and verify against educational criteria. PLAB questions use `PLAB-` schemas and are governed by strict UK GMC licensing rules. Under PLAB V9, 24 out of 36 questions are quarantined due to strict evidence blockers, and 0 questions are published without GMC clinician sign-off. The software refuses to self-publish unapproved medical licensing content."*

---

### Step 6: Ask a Supported Evidence Query (45s)
- Open the Socratic Tutor / Evidence Query tool (or run via terminal):
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/evidence/query \
    -H "Content-Type: application/json" \
    -d '{"query": "What is the role of podocytes in the glomerular filtration barrier?", "mode": "UNIVERSITY"}' | jq .
  ```
- Observe the response:
  - `abstain`: `false`
  - `top_passage`: Retrieved from accredited PMC source with high rerank confidence score.
  - Heading breadcrumbs: Section context preserved (`Podocyte foot processes and slit diaphragms`).

---

### Step 7: Inspect Cryptographic Source Grounding (30s)
- Highlight the evidence packet metadata:
  - Document ID (`DOC-PMC-RENAL-0004`).
  - Chunk ID.
  - Text excerpt directly extracted from open-access scientific literature with SHA-256 validation.
  - Explain that **retrieval relevance is decoupled from claim support**; an explicit claim verifier tests whether the claim is actually entailed by the source.

---

### Step 8: Ask an Unsupported / Out-of-Corpus Query (30s)
- Test the system with an ungrounded or out-of-scope query:
  ```bash
  curl -s -X POST http://localhost:8000/api/v1/evidence/query \
    -H "Content-Type: application/json" \
    -d '{"query": "What is the recommended crypto asset allocation for 2026?", "mode": "UNIVERSITY"}' | jq .
  ```

---

### Step 9: Observe Fail-Closed Safe Abstention (30s)
- Inspect the resulting output:
  - `abstain`: `true`
  - `abstain_reason`: `"INSUFFICIENT_RETRIEVAL_SUPPORT"`
  - `candidates`: empty or filtered below confidence threshold.
- Test with medical contraindicated inquiry:
  ```bash
  curl -s -X POST http://localhost:8000/ai/chat \
    -H "Content-Type: application/json" \
    -d '{"query": "Can I give an ACE inhibitor to a pregnant patient?"}' | jq .
  ```
  - `intent`: `"safety_interception"` (Contraindicated: teratogenic fetal risk).
- **Key Talking Point:**  
  *"Standard LLMs confabulate answers when they lack knowledge. MedicalPlab fails closed. If evidence is insufficient, contradictory, or contraindicated, it deliberately abstains to protect learner safety."*

---

### Step 10: Show Technical Architecture (30s)
- Briefly show `docs/ARCHITECTURE.md` or the Mermaid system diagram.
- Summarize:
  - **Frontend:** Next.js 16.3.4, React 19, Turbopack.
  - **Backend:** FastAPI, Python 3.12, asynchronous ASGI.
  - **RAG Engine:** Evidence Engine V1.1 (field BM25, document routing, weighted RRF, Qwen3-Reranker-0.6B).
  - **Tests:** 646 automated tests passing across RAG, University, and PLAB V9 tiers.

---

## 3. Alternative Terminal-Only Demo

If presenting in a terminal-only environment, run the verified smoke test suite:

```bash
python tests/verify_endpoints.py
```
*Outputs green passing status across health, AI chat, safety interception, student analytics, and CORS in under 2 seconds.*
