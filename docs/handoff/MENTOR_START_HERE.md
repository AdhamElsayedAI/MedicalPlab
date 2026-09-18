# MedicalPlab — Mentor & Evaluator Quick Briefing
**Target Read Time:** 2–3 minutes  
**Audience:** Mentors, Judges, Technical Due-Diligence Reviewers, Medical Faculty

---

## 1. What MedicalPlab Does
MedicalPlab is an **Adaptive Evidence-Grounded Medical Learning Platform**. 

Most medical assessment platforms operate as passive question banks: a learner selects an option, gets a score, and reads a static explanation. MedicalPlab fundamentally changes this dynamic by treating learner interactions as cognitive signals:
- **Heuristic Reasoning Signals:** Selected distractors may map to heuristic reasoning-pattern signals (e.g., misidentifying efferent vs. afferent arteriolar constriction in GFR regulation).
- **Closed-Loop Learning:** Rather than endless drills, MedicalPlab routes the learner into a bounded Socratic dialogue, verifies independent conceptual transfer with a held-out clinical vignette, grounds explanations in peer-reviewed evidence via an AI Tutor, and anchors spatial relationships through an interactive 3D anatomical viewer.

> **Core Product Thesis:** *"MedicalPlab does not only answer students. It learns how students learn."*

---

## 2. Why It Is Technically Different
1. **Generation as a Capability, Not an Authority:** Generative LLMs never provide unconstrained medical responses. Every generative claim must be bounded by retrieved literature and verified before delivery.
2. **Distractor-Aware Reasoning Signals:** Distractors are not just "incorrect"; selected distractors may map to heuristic reasoning-pattern signals.
3. **Independent Transfer Testing:** Socratic dialogue alone does not certify learning. Transfer is measured by performance on an unprompted, held-out clinical transfer problem.
4. **Unified Spatial Cognition:** 3D anatomy is directly connected to the cognitive state, allowing guided anatomical tours and structure identification challenges.
5. **AI / Scientific Asset Separation:** AI orchestrates pedagogical camera and scene actions; fixed, scientifically validated HuBMAP Human Reference Atlas (HRA) geometry remains the immutable spatial authority.
6. **Strict Clinical Governance:** PLAB exam candidates cannot self-promote to released status without clinician panel sign-off (Golden released = 0, Preview QA = 36).

---

## 3. Generative AI Architecture
MedicalPlab employs a dual-pipeline generative intelligence architecture:

```
[LEARNER QUERY] ──► [HYBRID RETRIEVAL (BM25 + Dense)] ──► [NEURAL RERANK (Qwen)]
                          │
                          ▼
            [BOUNDED EVIDENCE CONTEXT]
                          │
                          ▼
             [GENERATIVE REASONING DRAFT]
                          │
                          ▼
            [NLI CLAIM VERIFICATION GATE] ──► PASS: Grounded Response + Citations
                                          └──► FAIL: SAFE_FALLBACK
```

- **Retrieval & Rights Gate:** Hybrid BM25 lexical search and Reciprocal Rank Fusion (RRF) with CC-BY open-access PMC literature gating.
- **Neural Reranker:** In-domain cross-encoder scoring ensures high clinical relevance.
- **Fail-Closed Proposition Verification:** Generated statements are parsed into claims and verified against retrieved evidence. Unverified claims trigger deterministic `SAFE_FALLBACK`.
- **Pedagogical Action Routing:** In parallel, learner state drives bounded Socratic remediation (maximum 3 turns) and 3D scene actions.

---

## 4. Engineering Verification & Mobile Readiness
- **Backend Quality Gate:** 23/23 end-to-end integration tests passing (`tests/integration/test_phase_6_cross_module.py`).
- **Mobile Contract:** 12/12 mobile contract tests passing (`tests/integration/test_mobile_api_contract.py`).
- **OpenAPI 3.1.0 Contract:** 43 paths, 44 operations matching live runtime with 0 drift.
- **Mobile Hand-off:** Complete Postman collection with staging/local environments, Dart/Flutter and React Native client examples, and an integration checklist.
- **Frontend Stack:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, Three.js spatial canvas (0 build errors).

---

## 5. Current Capabilities vs. Future Vision

### BUILT TODAY (CURRENT)
- **Preclinical University Track:** 6 validated preclinical questions spanning renal physiology and hemodynamics.
- **Adaptive Remediation Engine:** Selected distractors may map to heuristic reasoning-pattern signals; bounded Socratic remediation (max 3 turns).
- **Independent Transfer Assessment:** Held-out problem generation evaluating conceptual transfer.
- **Evidence-Grounded AI Tutor:** Hybrid retrieval + Qwen neural reranking + NLI proposition verification + safe fallback.
- **Interactive 3D Renal Anatomy:** HuBMAP HRA renal model, guided anatomical tours, and deterministic artery identification challenge.
- **Unified Progress Tracking:** Cross-module learner progress tracking across questions, remediation, tutor sessions, and spatial challenges.
- **PLAB Preview QA Governance:** 36 clinician-review candidates isolated under Preview QA mode.
- **Mobile Contract & OpenAPI:** Fully documented, drift-tested REST API contract with synthetic `X-User-Id` learner state partitioning.

> [!WARNING]
> **`X-User-Id` is NOT cryptographic authentication and is NOT a secure authorization boundary.**
> It is synthetic caller-supplied learner partitioning for pilot state isolation. On a public unauthenticated API endpoint, any caller can supply any `X-User-Id` value. Remote staging deployments enforce closed-staging access control via the `X-Staging-Key` pre-shared key header, and web browser access via the Vercel Mentor Session Gate, rather than relying on `X-User-Id` as an access control mechanism. `PUBLIC_UNAUTHENTICATED_PILOT_API = NO`.

### FUTURE INTELLIGENCE ROADMAP (FUTURE / NOT IMPLEMENTED)
- **Multi-Organ Spatial Anatomy:** Extending HRA coverage to cardiovascular, respiratory, hepatic, and neuroanatomy systems.
- **Multimodal Educational Reasoning:** Explaining ECG rhythms, radiologic images, and pathology histology strictly for student learning (non-diagnostic).
- **Frontier Model Router:** Replaceable provider abstraction (OpenAI o-series, Claude, Gemini, open weights) behind an immutable MedicalPlab verification contract.
- **Institutional Scale:** Enterprise SSO, multi-tenant university deployment, faculty review workflows, LMS integration (LTI 1.3), and native iOS/Android applications with durable cloud storage.

---

## 6. Where to Go Next

- **Interactive Product Demo Runbook:** [`docs/demo/FINAL_DEMO_RUNBOOK.md`](../demo/FINAL_DEMO_RUNBOOK.md) *(Step-by-step 3-minute evaluation walkthrough)*
- **Deep Architecture Specification:** [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md)
- **AI & Evidence Engine Details:** [`docs/AI_SYSTEM.md`](../AI_SYSTEM.md)
- **Mobile Developer Integration:** [`docs/mobile-handoff/START_HERE.md`](../mobile-handoff/START_HERE.md)
- **Clinical Safety & Governance:** [`docs/CLINICAL_SAFETY.md`](../CLINICAL_SAFETY.md)
- **Full Repository Overview:** [`README.md`](../../README.md)
