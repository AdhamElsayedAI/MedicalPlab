# MedicalPlab — Executive Summary

> **"MedicalPlab does not only answer students. It learns how students learn."**

---

## 1. Problem Statement
Medical students increasingly turn to generic Large Language Models (LLMs) as ad-hoc study aids. While conversational models generate fluent explanations, they suffer from foundational deficiencies when applied to medical education:
1. **No Learner State Tracking:** Generic LLMs treat each interaction in isolation, lacking awareness of historical learning trajectories or cumulative mastery.
2. **Conflation of Error with Understanding:** Standard chatbots view incorrect responses as binary failures, failing to differentiate superficial recall lapses from systematic reasoning misconceptions.
3. **Absence of Transfer Verification:** Generic tutors explain a concept and assume comprehension, without testing whether the learner can independently apply the principle to novel, unprompted scenarios.
4. **Ungrounded Hallucination & Safety Risks:** Medical explanations often lack verifiable literature provenance, risking subtle medical misinformation without safe abstention boundaries.

---

## 2. The MedicalPlab Solution
MedicalPlab is an **Adaptive Evidence-Grounded Medical Learning Platform** designed for medical students and educational institutions. Rather than acting as a passive question-answering bot, MedicalPlab wraps AI within a rigorous, deterministic cognitive framework.

### The Canonical Learning Loop
```
Learner Attempt (Multiple-Choice / Clinical Scenario)
         ↓
Learner State Update (Topic mastery, cognitive history)
         ↓
Reasoning-Pattern Signal Detection (Heuristic hypothesis generation)
         ↓
Bounded Socratic Remediation (3-turn conversational guidance without answer leakage)
         ↓
Independent Transfer Challenge (Held-out, unprompted clinical validation)
         ↓
Unified Progress Synchronization (Calibrated mastery update)
```

---

## 3. Key Implemented Modules

| Module | Core Capability | Engineering Reality |
| :--- | :--- | :--- |
| **University Learning** | Curated clinical questions across core specialties (e.g., Renal, Cardiorespiratory). | Deterministic evaluation, detailed clinical rationales. |
| **Adaptive Learning** | Dynamic tracking of learner state and topic mastery vectors. | Heuristic reasoning-pattern signals; wrong answer $\ne$ proven misconception. |
| **Socratic Remediation** | Dialogue engine prompting guided discovery rather than lecturing. | Bounded 3-turn limit; strict answer concealment; fail-closed fallback. |
| **Grounded Tutor** | Evidence-backed clinical tutoring. | Authoritative single retrieval path; CC-BY open-access PMC literature; NLI verification. |
| **Cognitive Anatomy** | 3D anatomical exploration (*"Structure carries signal"*). | Deterministic raycast scoring; zero AI geometry generation; separate guided vs challenge targets. |
| **Unified Progress** | Cross-module learner trajectory synchronization. | Partitioned per-learner state (`X-User-Id`), deterministic rollups. |
| **Governed PLAB** | Examination preparation workflow. | Candidate preview workflow (`PLAB_GOLDEN_PROMOTION_REQUIRED = YES`); fails closed in golden mode. |

---

## 4. Current Operational Truth

### What Is Working Now (Verified in Repository)
- **Local-First Reproducibility:** 100% clone-and-run functionality requiring **$0 cost, 0 cloud secrets, 0 GPU, and 0 paid LLM keys** (deterministic local fallback providers active).
- **Frozen Mobile API Contract:** 43 paths / 44 operations, OpenAPI 3.1.0 certified with 12/12 passing automated contract tests.
- **Automated Quality Certification:** 23/23 backend integration tests passing; 15/15 staging security tests passing; 8/8 CI jobs passing on GitHub Actions.
- **Deterministic AI Boundaries:** Medical truth and challenge scoring remain governed by validated fixtures and deterministic algorithms, not arbitrary LLM output.

### What Is Not Production-Ready Yet (Honest Product Boundaries)
- **Authentication:** `X-User-Id` is currently used for client partitioning; enterprise cryptographic authentication (OAuth2/OIDC) is planned for the next milestone.
- **PLAB Golden Content:** The repository contains 36 candidate preview questions. Golden release status requires formal clinician sign-off.
- **Offline Sync:** Mobile clients require network connectivity to the local or hosted backend; offline synchronization is not supported in this prototype.
