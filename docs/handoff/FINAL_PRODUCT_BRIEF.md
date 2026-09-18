# MedicalPlab — Final Product Brief & Technical Handoff
**Document Version:** 1.0.0-final  
**Canonical Product Identity:** MedicalPlab — Adaptive Evidence-Grounded Medical Learning Platform  
**Target Audience:** Mentors, Startup Evaluators, Technical Due-Diligence Reviewers, Clinical Educators  
**Delivery Model:** Local-First / Reproducible Clone-and-Run (Zero Cloud Dependencies)  

---

## Executive Summary

> **"MedicalPlab does not only answer students. It learns how students learn."**

Modern medical education suffers from two contrasting technological failure modes:
1. **Passive, Static Question Banks:** Traditional platforms reduce complex physiological and clinical training to rote multiple-choice drilling. When a student chooses a wrong answer, they receive an arbitrary score penalty and a static explanation. The system never isolates the underlying heuristic defect or confirms whether the learner truly understands the mechanism.
2. **Unconstrained Medical Chatbots:** Generic conversational LLM wrappers ("ChatGPT for doctors") generate plausible-sounding medical assertions without evidence boundaries, operate completely statelessly without tracking mastery, hallucinate unverified claims, and lack any spatial or physical anatomical grounding.

**MedicalPlab** solves both problems by establishing an **adaptive, closed-loop educational learning intelligence system**. It couples:
- Evidence-grounded generative tutoring bounded by peer-reviewed literature,
- Diagnostic distractor-level reasoning pattern signals,
- Multi-turn bounded Socratic remediation drawers,
- Independent held-out clinical transfer verification,
- Scientifically validated 3D spatial anatomy (HuBMAP Human Reference Atlas), and
- Clinician-governed exam content pipelines.

Generative AI in MedicalPlab is deployed strictly as a **controlled educational capability**, never as an unconstrained medical authority.

---

## 1. Product Positioning & Value Proposition

| Dimension | Generic Medical Chatbot | Traditional Question Bank | MedicalPlab |
| :--- | :--- | :--- | :--- |
| **Learner State** | Stateless (prompt &rarr; answer &rarr; forget) | Coarse accuracy score (%) | Longitudinal, multi-topic cognitive state |
| **Error Handling** | Generic conversational reply | Binary right/wrong + text blob | Distractor mapped to heuristic reasoning signal |
| **Intervention** | Immediate complete answer | Passive reading | Bounded 3-turn Socratic remediation |
| **Competence Proof** | None (user confirmation) | Re-testing same question | Unprompted, held-out clinical transfer problem |
| **Medical Authority** | Model weights (hallucination risk) | Author-written static database | Retrieved open-access PMC literature + NLI verification |
| **Anatomical Context** | Text descriptions or 2D diagrams | Static 2D textbook images | Interactive HuBMAP HRA 3D spatial CCF models |
| **Spatial Evaluation** | None | None | Deterministic backend raycasting on ontology IDs |
| **Content Governance**| None | Manual curation | Segregated Preview QA vs Clinician-Approved Golden |

---

## 2. The MedicalPlab Learning Loop

The fundamental differentiator of MedicalPlab is its closed-loop cognitive spine:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        1. Curricular Question                          │
│        Preclinical basic-science vignette with distractors             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Learner attempt
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   2. Diagnostic Reasoning Signal                       │
│    Distractor taxonomy maps mistake to heuristic cognitive signal      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Triggers adaptive policy
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 3. Bounded Socratic Remediation Drawer                 │
│      Turn 1: Probe ──► Turn 2: Guide ──► Turn 3: Consolidate           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Unlocks transfer challenge
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                4. Independent Held-Out Transfer Problem                │
│    Unseen clinical vignette verifies conceptual generalization         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Confirmed transfer
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   5. Unified Progress Synchronization                  │
│       Updates topic-level learner state across questions, tutor,       │
│                     and 3D spatial anatomy                             │
└────────────────────────────────────────────────────────────────────────┘
```

### Key Principles of the Loop
- **Wrong Answer &ne; Confirmed Misconception:** An incorrect answer provides a *provisional heuristic signal*—a hypothesis to test through dialogue, not an immutable diagnosis of incompetence.
- **Firewalled Dialogue:** Socratic conversation scaffolds student thinking; it does **not** count as proof of competence.
- **Held-Out Generalization:** Learner state only advances when the student independently solves an unprompted, structurally distinct held-out transfer problem (`UNI-RENAL-001-T`).

---

## 3. Generative AI Architecture & Safety Boundaries

MedicalPlab decouples generative fluency from medical truth. The generative model operates inside a **deterministic verification container**.

```
[Student Query / Remediation Context]
                 │
                 ▼
     [Shared Evidence Engine]
                 │
  ┌──────────────┴──────────────┐
  │ Hybrid Retrieval            │ ──► BM25 Lexical + Dense Embeddings (RRF Fusion)
  │ Rights & License Gate       │ ──► Open-Access CC-BY PMC Literature Gating
  │ In-Domain Reranker          │ ──► Neural Cross-Encoder Reranking
  └──────────────┬──────────────┘
                 │ Top-k Chunks (Bounded Context)
                 ▼
     [Generative Reasoning Draft]
                 │ Unverified Draft
                 ▼
     [NLI Proposition Verifier]
                 │
        ┌────────┴────────┐
        │                 │
     [PASSED]          [FAILED]
        │                 │
        ▼                 ▼
  Grounded Output    SAFE_FALLBACK
  with Citations     (Content-neutral procedural
  (PMCID / DOI)       Socratic guidance; 0 claims)
```

### What Generative AI Does
- Formulates multi-turn Socratic probing questions.
- Generates grounded, accessible explanations bounded strictly by retrieved excerpts.
- Emits structured JSON payloads for Three.js scene actions (`FOCUS_STRUCTURE`, `HIGHLIGHT_STRUCTURE`, `RESET_SCENE`).

### What Generative AI NEVER Controls
- **Medical Ground Truth:** The model is not the source of truth; PMC evidence is.
- **Challenge Scoring:** Spatial anatomy pin challenges and transfer problems are evaluated deterministically.
- **Anatomical Geometry:** 3D meshes are immutable NIH HuBMAP assets; AI never creates or deforms geometry.
- **Clinical Governance:** Candidate PLAB items remain gated behind Preview QA until authorized by human clinicians.

---

## 4. Cognitive Anatomy: "Structure Carries Signal"

Anatomy in MedicalPlab is not a cosmetic visual viewer; it is an active cognitive grounding instrument:
- **Scientific Provenance:** Uses canonical 3D meshes from the **NIH HuBMAP Human Reference Atlas (HRA)** registered to the Common Coordinate Framework (CCF v1.3/v2.0).
- **Guided Spatial Exploration:** Programmed exploration sequences (e.g., `renal_vein_left` anterior hilar inspection) ground vascular hemodynamics in physical organs.
- **Deterministic Challenge Engine:** In spatial challenge mode, the learner must independently identify target structures (e.g., `renal_artery_left`). The client Three.js raycaster sends hit coordinates to the backend, which evaluates correctness against UBERON anatomical ontology IDs (`UBERON:0001120`).

---

## 5. Engineering Confidence & Certified Metrics

All figures below are certified against the active repository HEAD:

| Metric / Quality Gate | Certified Status | Implementation & Verification |
| :--- | :---: | :--- |
| **API Endpoints & Operations** | **43 paths / 44 operations** | Frozen OpenAPI 3.1.0 contract; **0 drift** |
| **Backend Integration Suite** | **23 / 23 PASS** | `pytest tests/integration/` |
| **Mobile Contract Tests** | **12 / 12 PASS** | `pytest tests/integration/test_mobile_api_contract.py` |
| **Render/Staging Security Gate** | **15 / 15 PASS** | `pytest tests/staging/test_staging_security.py` |
| **Frontend Production Build** | **PASS** | Next.js 16.3.4 (Turbopack, App Router, React 19) |
| **Repository Link Integrity** | **PASS (0 broken links)** | `python Scripts/verify_repository_handoff.py` (38 docs) |
| **Clean Checkout Release Gate**| **PASS** | `python Scripts/verify_local_release.py` |
| **GitHub Actions CI** | **8 / 8 Jobs PASS** | CI run on `release/final-mentor-mobile-handoff` |
| **Container Memory Footprint** | **PASS (< 512MB RAM)** | Validated under Render Free memory limits |

---

## 6. Local-First Delivery: Clone-and-Run Guarantee

MedicalPlab adheres to a **strict local-first distribution standard**:
- **$0 Cost:** Requires zero cloud accounts (no Google Cloud, no Render, no AWS).
- **No Payment Cards:** Fully runnable without credit card billing or subscription gates.
- **No Paid LLM Keys Required:** Defaults to `MEDICALPLAB_TUTOR_PROVIDER=stub` for deterministic, zero-cost pedagogical responses.
- **CPU-Only Hardware:** Standard workstations run the complete product; no GPU or PyTorch CUDA setup is required.

### Quick Commands
```powershell
# 1. Start Backend (PowerShell)
.\Scripts\start_local.ps1

# 2. Start Frontend (Second Terminal)
cd frontend && npm install && npm run dev

# 3. Access Web UI
http://localhost:3000
```
*(On Linux/macOS, use `./Scripts/start_local.sh`)*

---

## 7. Startup Defensibility & Technical Moats

Why is MedicalPlab defensible against commodity LLM wrappers?
1. **The Learning Loop Moat:** A generic LLM answers student questions; MedicalPlab orchestrates a multi-step cognitive loop (Assessment &rarr; Heuristic Signal &rarr; Bounded Socratic Remediation &rarr; Transfer Gate &rarr; Progress Update). Replacing the LLM does not recreate this architecture.
2. **Proprietary Distractor Taxonomy:** Curated mapping of high-yield physiological distractors to specific cognitive misattributions.
3. **Fail-Closed NLI Verification Pipeline:** Atomic proposition segmentation and cross-encoder entailment ensure medical trustworthiness.
4. **Authoritative 3D Spatial Ontology Mapping:** HuBMAP CCF models tied directly to cognitive remediation objectives and deterministic raycasting.
5. **Two-Tiered Clinical Content Governance:** Structural separation between experimental candidate items and released clinical curricula.

---

## 8. Current Project Status: Operational Boundaries

To maintain rigorous technical credibility, MedicalPlab explicitly documents what is built today versus what is scheduled for future horizons:

### Ready Now (Verified Today)
- Complete local product execution (University, Socratic remediation, transfer challenge, grounded tutor, 3D anatomy, progress).
- Standalone clone-and-run verified across Windows, Linux, and macOS.
- 43-endpoint frozen REST API with OpenAPI 3.1.0 and comprehensive Postman collection.
- 36 PLAB candidate questions under Preview QA governance.
- 512MB containerized Docker image with zero ML model weights.

### Intentionally Not Production-Ready (Honest Boundaries)
- **`MOBILE_PRODUCTION_AUTH_READY = NO`**: Learner identity via `X-User-Id` is for demo partitioning and local contract testing. It is not cryptographic production authentication.
- **`PLAB_PUBLIC_RELEASE_READY = NO`**: Candidate clinical questions are gated behind Preview QA. They require clinician review panel signoff before public release (`PLAB_GOLDEN_PROMOTION_REQUIRED = YES`, Golden released = 0).
- **`OFFLINE_SYNC_SUPPORTED = NO`**: The client requires connectivity to the local or hosted REST backend.
- **`REAL_NATIVE_MOBILE_SOURCE_IN_REPO = NO`**: The repository delivers the complete backend, web client, OpenAPI specs, Postman suites, and Dart/TS client examples. Native iOS/Android app repositories remain downstream.
- **`CLOUD_DEPLOYMENT_REQUIRED = NO`**: Cloud infrastructure (Render/GCP) is optional and not configured as a delivery prerequisite.

---

## 9. Future Intelligence Horizons

```
Horizon 1: Multi-Organ Spatial Anatomy (Cardiovascular, Respiratory, Neuroanatomy CCF)
       │
Horizon 2: Multimodal Generative Learning (ECG Socratic rhythm interpretation, imaging landmarks)
       │
Horizon 3: Frontier Model Router Orchestration (Provider-agnostic frontier model routing)
       │
Horizon 4: Institutional Enterprise Platform (SAML/OIDC SSO, clinician portal, LTI 1.3 LMS integration)
```

---

## 10. Key Documentation Index

- **Local Execution:** [Local Run Guide](../LOCAL_RUN_GUIDE.md) &bull; [Mentor Runbook](MENTOR_LOCAL_RUN.md)
- **Evaluator Briefing:** [Mentor Start Here](MENTOR_START_HERE.md) &bull; [Final Demo Runbook](../demo/FINAL_DEMO_RUNBOOK.md)
- **Mobile Engineering:** [Mobile Start Here](../mobile-handoff/START_HERE.md) &bull; [API Contract](../mobile-handoff/API_CONTRACT.md) &bull; [Client Examples](../mobile-handoff/CLIENT_EXAMPLES.md)
- **Clinical Governance:** [Clinical Safety](../CLINICAL_SAFETY.md) &bull; [PLAB Provenance](../PLAB_PROVENANCE_AND_DATA_GOVERNANCE.md) &bull; [Third-Party Anatomy](../../THIRD_PARTY_NOTICES_ANATOMY.md)
- **Architecture:** [Stage B System Spec](../stage_b.md) &bull; [AI System Architecture](../AI_SYSTEM.md)
