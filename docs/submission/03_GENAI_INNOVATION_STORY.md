# GenAI Innovation Story: Controlled Educational Intelligence

> **"The model participates in learning. The model does not become the source of truth."**

---

## 1. The Core Architectural Philosophy

In medical education, unconstrained generative AI is dangerous. A probabilistic model that generates medical facts without deterministic safeguards risks teaching incorrect clinical reasoning.

MedicalPlab addresses this challenge with a **hybrid architectural model**:
- **Generative AI provides dynamic pedagogical capability:** phrasing Socratic questions, explaining complex physiological cascades, and mapping natural-language queries to educational scene actions.
- **Deterministic software enforces medical safety and educational rigor:** retrieving verified open-access literature, enforcing rights and licensing, checking natural language entailment, deterministically scoring assessments, and governing 3D anatomy.

---

## 2. Explicit Boundary Separation

| Dimension | Role of Generative AI | Deterministic / Verified Software Boundary |
| :--- | :--- | :--- |
| **Medical Evidence** | Synthesizes conversational explanations strictly within retrieved passage context. | Authoritative PubMed Central CC-BY retrieval, semantic chunking, and rights provenance gating. |
| **Verification & Safety** | Proposes educational responses based on evidence. | Entailment / Natural Language Inference (NLI) verification. Fails closed (`SAFE_FALLBACK`) if unsupported. |
| **Assessment & Scoring** | None. AI does not score student attempts or award marks. | Deterministic string/ID equality evaluation against held-out ground truth. |
| **Remediation Dialogue** | Drives Socratic inquiry, posing leading questions without lecturing. | Strict 3-turn dialogue cap; token filters preventing answer leakage; fallback to structured summary. |
| **Cognitive Anatomy** | Translates natural language requests (e.g. *"zoom in on the renal vein"*) into structured JSON scene actions. | 100% pre-authored Three.js assets; raycast hit-testing against UBERON ontology IDs. Zero AI geometry generation. |
| **Learner Diagnosis** | Formulates provisional heuristic hypothesis signals. | "Wrong answer $\ne$ confirmed misconception". No clinical, psychological, or diagnostic labeling. |

---

## 3. The Single Authoritative Architecture

MedicalPlab enforces a single, unified pipeline for all evidence-grounded educational intelligence:

```
[ Learner Interaction / Inquiry ]
              ↓
      [ Adaptive Layer ]
              ↓
       [ TutorService ]
              ↓
  [ Shared Evidence Engine ]
              ↓
  [ PubMed Central Retrieval ]  <-- CC-BY Open Access literature corpus
              ↓
  [ Rights & Provenance Gate ]  <-- Confirms license, attribution, & PMCID
              ↓
    [ NLI Verification Gate ]   <-- Validates claim entailment against sources
              ↓
    ┌───────────────────────┐
    │ Entailment Verified?  │
    └───────────────────────┘
       /                 \
    [YES]                [NO]
      ↓                   ↓
[ Grounded Response ]   [ Safe Abstention (SAFE_FALLBACK) ]
(With PMCID citation)   (Refusal to generate ungrounded claims)
```

### Why This Architecture Wins
1. **Zero Hallucinated Citations:** Passages must exist in the validated local index or remote verified corpus before generation occurs.
2. **Safe Fallback by Design:** When evidence is ambiguous or retrieval falls below confidence thresholds, the system defaults to a safe abstention notice rather than fabricating a response.
3. **Provider Agnostic:** The architecture cleanly decouples the retrieval and validation harness from LLM inference. In local development or resource-constrained environments, a deterministic stub provider guarantees full testability with $0 API overhead. In hosted environments, verified adapter implementations are provided for Google Gemini and OpenAI, with additional frontier models (e.g., Claude) and local open-weight runtimes planned on the future model-router roadmap without changing the safety boundaries.

---

## 4. Structure Carries Signal: The 3D Anatomy Innovation

In traditional anatomy apps, 3D models are static encyclopedias. In MedicalPlab's **Cognitive Anatomy Lab**, structure is an active educational transducer:
- When a student struggles with renal vascular resistance, the Socratic tutor can dispatch structured scene actions (`HIGHLIGHT_STRUCTURE`, `FOCUS_CAMERA`) to spotlight the relevant anatomy.
- **AI never generates Three.js code or mesh geometry.** Instead, AI acts as an intent parser emitting structured parameters (e.g. target ID: `renal_vein_left`).
- In independent challenge mode, the student must physically locate the corresponding counterpart (e.g. `renal_artery_left`). Accuracy is computed deterministically by calculating camera-to-mesh raycast intersection distances against the 3D scene graph.
