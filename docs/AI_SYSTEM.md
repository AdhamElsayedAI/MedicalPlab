# AI System & Pipeline Architecture

## 1. Overview

The MedicalPlab AI system is an end-to-end evidence-grounded generative and retrieval architecture tailored for medical education. Unlike standard unconstrained conversational agents, MedicalPlab employs a multi-stage deterministic pipeline where every generative step is bounded by verifiable retrieval contracts and mathematical knowledge modeling.

---

## 2. Multi-Source RAG & Dense Retrieval

### Specialized Retrieval Pipeline
The retrieval subsystem ingests and indexes authoritative medical corpora (NICE guidelines, WHO clinical guidelines, British Thoracic Society statements, Resuscitation Council UK protocols, and PMC open-access clinical literature):

1. **Structure-Preserving Parser**: Documents are parsed into canonical hierarchical blocks preserving section levels, heading breadcrumbs, table contexts, and element provenances.
2. **Dense Semantic Retrieval**: High-dimensional medical embeddings (BGE-M3 and Qwen-4B Medical Domain Adapted LoRA) capture nuanced clinical phrasing (e.g., matching *"pleuritic chest pain with right bundle branch block"* to *"acute pulmonary embolism"*).
3. **Two-Layer Neural Firewall & Reranker**: Cross-encoder rerankers filter irrelevant or contradictory chunks, achieving high precision in evidence sufficiency classification.

### Verified Retrieval Performance
- **Renal Benchmark V5/V6**: 100% precision on held-out safety suites; zero false-support classifications.
- **Cardiorespiratory Retrieval**: Exact-span locator accuracy with zero hallucinated offsets.

---

## 3. The Stage Architecture (Stages B through R)

MedicalPlab is modularized into discrete, testable pipeline stages:

```text
 authoritative sources
          │
          ▼
   [ Stage-R: Strict Runtime Engine ]
          │
          ▼
   [ Stage-B: Evidence & Claim Planner ]
          │  ├── Evidence policy validation
          │  ├── Atomic claim decomposition
          │  └── Character-exact span verifier
          │
          ├──► [ Stage-C: Question Generation ]
          │         └── Grounded vignette and stem creation
          │
          ├──► [ Stage-D: Adversarial Distractor Engine ]
          │         └── High-plausibility distractor mining & ambiguity gating
          │
          ├──► [ Stage-E: Adaptive Learning & Student Modeling ]
          │         └── Bayesian Knowledge Tracing (BKT) & mastery tracking
          │
          ├──► [ Stage-F: Interactive Clinical Simulation ]
          │         └── Turn-based OSCE patient consultation & diagnostic reasoning
          │
          └──► [ Stage-G: Multi-Tenant Platform Orchestration ]
                    └── Enterprise tenant isolation, API routing, and audit logs
```

### Stage Deep Dive

#### Stage-B: Evidence Aggregation & Claim Planner
- Decomposes medical explanations into discrete atomic claims.
- Asserts that every claim is directly entailed by a corresponding evidence span from an authoritative document.
- Employs strict Pydantic models with schema validation.

#### Stage-C: Grounded Question Generation
- Synthesizes UK GMC PLAB 1 single-best-answer (SBA) questions based on real clinical presentations.
- Forbids free-form extrapolation: stems must reflect validated clinical case patterns.

#### Stage-D: Adversarial Distractor Mining
- Generates clinically tempting distractors based on common student cognitive biases (e.g., confusion between rate vs. rhythm control in atrial fibrillation, or inappropriate immediate ACEi in acute kidney injury).
- Validates that distractors are unequivocally incorrect under current guidance, preventing ambiguous test items.

#### Stage-E: Adaptive Learning Engine (Bayesian Knowledge Tracing)
- Models student mastery across the GMC MLA curriculum using Bayesian Knowledge Tracing (BKT):
  $$P(L_{t+1}) = P(L_t \mid \text{Obs}) + (1 - P(L_t \mid \text{Obs})) \cdot T$$
  incorporating slip ($S$) and guess ($G$) parameters calibrated per medical specialty.
- Implements spaced repetition scheduling based on individual student mastery curves.

#### Stage-F: Clinical Simulation Engine
- Provides interactive, conversational simulated patient encounters.
- Allows students to take histories, order diagnostic investigations, and formulate management plans while evaluating clinical safety at each step.

#### Stage-G: Platform Orchestrator & Enterprise Tenant Management
- Full multi-tenant data partitioning for medical universities, NHS trusts, and student cohorts.
- Role-Based Access Control (RBAC): Student, Instructor, Clinician Reviewer, System Administrator.
- Audit logging for all AI interactions and review actions.

---

## 4. Contract-Driven AI Execution

All LLM integrations adhere to rigid contract boundaries:
- **No Direct String Interpolation**: Prompts are parameterized via version-controlled templates.
- **JSON-Schema Enforcement**: LLM outputs are parsed into strict models. Malformed JSON or schema deviations trigger automatic retry or fail-closed abort.
- **Offline / Mock Testability**: Every AI component implements stub/offline backends, allowing 100% of unit and integration tests to execute deterministically without external API dependencies or network calls.
