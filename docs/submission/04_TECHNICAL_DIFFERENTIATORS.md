# Technical Differentiators

> **Fourteen engineering moats separating MedicalPlab from wrapper applications.**

---

## 1. The Fourteen Core Technical Differentiators

### 1. Persistent & Derived Learner State
Learner progression is tracked across individual questions, topics, and sessions using structured state vectors. The system tracks historical attempts, mastery confidence, error frequencies, and remediation stages rather than relying on ephemeral chat context.

### 2. Wrong Answer $\ne$ Proven Misconception
An incorrect option choice is never treated as a clinical or psychological diagnosis. An error generates a provisional, heuristic reasoning-pattern signal—a hypothesis to be tested and resolved, rather than a permanent label.

### 3. Heuristic Reasoning-Pattern Detection
Distractor options are mapped to specific cognitive stumbling blocks (e.g. `PATTERN-RAAS-SUB-01`, confusing enzyme activation sequences). When a student selects a diagnostic distractor, the system triggers tailored remediation targeting the underlying mechanism rather than generic restatement.

### 4. Bounded Socratic Remediation
Remediation is constrained to a strictly bounded 3-turn Socratic dialogue. The system asks targeted leading questions to prompt learner deduction while preventing answer leakage. If the student remains stuck after 3 turns, the engine safely resolves the dialogue with an evidence-backed summary.

### 5. Independent Held-Out Transfer Verification
Comprehension cannot be certified through conversational explanation alone. Once a concept is reviewed during remediation, the platform serves an unprompted, held-out transfer challenge (`UNI-RENAL-001-T` $\rightarrow$ Correct Answer: `A — Angiotensinogen`). Successful completion awards a verified transfer confirmation (`TRANSFER_CONFIRMED`), providing an independent cognitive signal distinct from standard practice attempts.

### 6. Single Evidence-Grounded Tutor Architecture
All generative tutoring requests pass through a unified pipeline (`Adaptive Layer` $\rightarrow$ `TutorService` $\rightarrow$ `Shared Evidence Engine`). There are no ad-hoc LLM calls, unmonitored agent threads, or competing retrieval paths.

### 7. Rights & Provenance Gating
Every retrieved chunk undergoes automated rights validation. MedicalPlab enforces PubMed Central (PMC) open-access CC-BY compliance, ensuring all retrieved literature includes PMCID provenance, attribution metadata, and licensing validation.

### 8. Verification & Safe Fallback
Generative outputs are audited for textual entailment against retrieved literature. If the context does not support the explanation or retrieval confidence is insufficient, the system safely abstains (`SAFE_FALLBACK`) rather than presenting speculative information.

### 9. Cognitive Anatomy: "Structure Carries Signal"
Spatial anatomy is integrated directly into the pedagogical loop. 3D models are not static visual aids; they receive structured scene actions dispatched by the tutor, spotlighting anatomy relevant to the student's reasoning gap.

### 10. Deterministic Anatomy Challenge Scoring
Generative AI never creates geometry or evaluates spatial accuracy. Mesh assets are pre-validated, and challenge scoring is performed deterministically via Three.js camera raycast calculations against UBERON anatomical ontology IDs.

### 11. Unified Learner Progress Synchronization
Cross-module telemetry (University questions, Adaptive quizzes, Socratic remediation, Cognitive Anatomy challenges) rolls up into a unified progress schema (`/api/v1/progress`). Progress is partitioned cleanly per learner identity (`X-User-Id`).

### 12. Governed PLAB Content Workflow
Content integrity is strictly regulated. Examination materials are partitioned into candidate preview questions and verified golden content. In standard production mode, the platform fails closed (`PLAB_GOLDEN_PROMOTION_REQUIRED = YES`) to ensure unvalidated candidate items are never served as official exam questions.

### 13. Local-First Reproducible Engineering
The entire system runs locally out of the box with zero external dependencies: **$0 cloud cost, 0 cloud secrets, 0 GPU requirements, and 0 mandatory paid API keys**. Developers and judges can clone the repository, run one command, and experience the full platform with deterministic local stubs.

### 14. Frozen Mobile API Contract
MedicalPlab ships with a validated OpenAPI 3.1.0 specification comprising 43 paths and 44 operations. Mobile compatibility is certified via a 12/12 automated integration contract test suite, complete with Postman environments for localhost, Android emulator (`10.0.2.2`), and local LAN testing.

---

## 2. Live Verified Engineering Metrics

All metrics reflect current, reproducible tests in the repository:

| Metric | Verified Value | Status |
| :--- | :--- | :--- |
| **API Contract** | 43 paths / 44 operations | Validated (OpenAPI 3.1.0) |
| **OpenAPI Contract Drift** | 0 drift detected | PASS |
| **Backend Integration Suite** | 23 / 23 tests passing | PASS |
| **Mobile API Contract Suite** | 12 / 12 tests passing | PASS |
| **Staging Security Suite** | 15 / 15 tests passing | PASS |
| **Documentation Link Integrity** | 39 / 39 markdown files checked (0 broken links) | PASS |
| **GitHub Actions Main CI** | 8 / 8 jobs completed & green | PASS |
| **Clean Checkout Simulation** | 12 / 12 verification steps passed | PASS |
| **Local Runtime Memory Footprint** | Docker smoke test passed under 512 MB | PASS |
| **Supported Python Runtime** | `>=3.11,<3.13` (Python 3.11 or 3.12) | Verified |
| **Minimum Node.js Runtime** | `>=20.9.0` (Node 20 LTS / 22 LTS) | Verified |
