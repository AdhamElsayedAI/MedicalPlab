# MedicalPlab Phase 6 — Final Cross-Module Product Integration Architecture & Verification

## 1. Executive Summary & Product North Star

**Product North Star:**  
> *"MedicalPlab is an Adaptive Evidence-Grounded Medical Learning Platform. MedicalPlab does not only answer students. It learns how students learn."*

MedicalPlab brings together University preclinical education, PLAB clinical exam preparation, 3D Generative Anatomy, Grounded Socratic Tutoring, Adaptive Mastery Tracking, Socratic Remediation, and Cohort Learning Intelligence into **one coherent, startup-ready learning product**.

Phase 6 connects these systems through **thin adapters**, **stable learner identity**, the standard **`LearningEvent`** boundary, and **read-only product composition**, while preserving strict module-owned persistence and frozen behavioral contracts.

---

## 2. Core Architecture & Non-Negotiable Invariants

```
                            SHARED LEARNER IDENTITY
                          (Canonical Header: X-User-Id)
                                       |
        +------------------------------+------------------------------+
        |                              |                              |
   UNIVERSITY                         PLAB                        3D ANATOMY
(university.sqlite3)             (pilot_store.db)              (anatomy.sqlite3)
        |                              |                              |
        +---------------------- LEARNING SIGNALS ---------------------+
                                       |
                                       v
                                ADAPTIVE LAYER
                            (LearnerStateStore)
                                       |
                              LEARNER STATE UPDATE
                                       |
                     +-----------------+-----------------+
                     |                                   |
                     v                                   v
               NEXT ACTIVITY                     REASONING SUPPORT
         (Adaptive Recommendation)                       |
                                               SOCRATIC REMEDIATION
                                              (RemediationLoopController)
                                                         |
                                                  TRANSFER CHECK
```

### Explanatory AI Medical Pipeline (Zero Bypass Invariant)
Every generative medical explanation in the product strictly adheres to:
```
Learning Mode (University, PLAB, Remediation, Tutor)
       |
       v
TutorService
       |
       v
Evidence Engine / Central RAG Retrieval
       |
       v
SourceRightsGate (Verified open-access renal basic science)
       |
       v
Post-Generation Verification (Provenance + Claims + Clinical Safety Vetoes)
       |
       v
Learner Response
```
- **NO direct LLM bypasses.**
- **NO duplicate RAG pipelines or vector stores.**
- **NO ungrounded medical generation.**

### 3D Anatomy Invariant
- Deterministic Three.js execution and deterministic server-side challenge scoring (`renal_vein_left` guided target, `renal_artery_left` independent challenge).
- AI emits only structured educational actions; never raw scene mutations or challenge correctness decisions.
- Telemetry vs Pedagogical Signal separation: Only meaningful educational milestones (challenge submissions, structure discoveries) emit `LearningEvent`s. Raw camera pans or clicks are discarded.

---

## 3. Shared Learner Identity

- **Canonical Header:** `X-User-Id`
- **Backward-Compatible Header Alias:** `X-Learner-Id`
- **Query/Body Fallback:** `learner_id` / `user_id`
- **Implementation:** `medicalplab.identity.resolve_learner_id`
- **Behavior:** Ensures consistent identification across all module endpoints without requiring a centralized monolithic user database or schema migration.

| Module | External Input Header | Internal Field | Module Store Key |
| :--- | :--- | :--- | :--- |
| **University** | `X-User-Id` | `user_id` | `university_attempts.user_id` |
| **PLAB** | `X-User-Id` | `user_id` | `pilot_store.db: attempts.user_id` |
| **3D Anatomy** | `X-User-Id` / `X-Learner-Id` | `learner_id` | `anatomy.sqlite3: anatomy_sessions.learner_id` |
| **Adaptive** | `X-User-Id` | `learner_id` | `LearnerStateStore.learner_id` |
| **Remediation** | `X-User-Id` | `user_id` | `remediation_sessions.user_id` |
| **Tutor** | `X-User-Id` | `server_user_id` | `tutor_telemetry.learner_id` |
| **Unified Progress** | `X-User-Id` | `learner_id` | Read-only aggregation |

---

## 4. Cross-Module Event Boundaries (`LearningEvent`)

No new event schemas were created. All modules emit standard `medicalplab.adaptive.models.LearningEvent` instances:

1. **University Question Attempt:**
   - Emits `QUESTION_ATTEMPT` on `POST /api/v1/university/answer`.
   - Domain: Preclinical basic science / renal physiology.
2. **PLAB Question Evaluation:**
   - Emits `QUESTION_ATTEMPT` on `POST /api/v1/plab/evaluate`.
   - Domain: Clinical cardiorespiratory / emergency medicine.
3. **3D Anatomy Challenge Completion:**
   - Emits `ANATOMY_CHALLENGE` on `POST /api/v1/anatomy/session/{id}/challenge`.
   - Domain: Macroscopic renal anatomy & vascular relations.

The Adaptive Engine (`LearnerStateStore.get_raw_attempts`) aggregates attempts non-destructively across all module stores (`university_attempts`, `pilot_store.db`, `anatomy.sqlite3`), enabling real-time mastery tracking across the entire curriculum.

---

## 5. PLAB → Socratic Remediation Bridge

Remediation is **never** triggered merely because an answer is incorrect.

### Pipeline:
1. Student selects a distractor on a PLAB clinical question (`POST /api/v1/plab/evaluate`).
2. `ReasoningPatternDetectionEngine.detect_hypothesis` evaluates whether the selected distractor maps to an established reasoning misconception pattern (e.g., `PATTERN-RAAS-ENZ-01`: Enzymatic cleavage role reversal in RAAS).
3. If unmapped: `remediation.eligible = False`. Normal feedback returned.
4. If mapped: `remediation.eligible = True`, returning `pattern_id`, `reasoning_pattern`, and `strategy`.
5. Student initiates remediation (`POST /api/v1/remediation/start`).
6. Bounded 3-turn Socratic loop executes:
   - **Turn 1 (Probe):** Socratic probe into the underlying physiological cascade.
   - **Turn 2 (Guide):** Stepwise decomposition of the biochemical pathway.
   - **Turn 3 (Consolidate):** Mechanistic synthesis grounded in verified basic-science evidence.
7. Held-out transfer item (`PLAB-CARD-0001-T`) is retrieved (`GET /.../transfer`) and evaluated deterministically (`POST /.../transfer`).

---

## 6. Read-Only Unified Learner Progress

**Endpoint:** `GET /api/v1/learner/progress` (alias: `GET /api/v1/progress`)  
**Header:** `X-User-Id: <learner_id>`

### Response Schema:
```json
{
  "learner_id": "stu_demo_01",
  "university": {
    "total_questions": 36,
    "attempted": 5,
    "correct": 4,
    "accuracy": 0.8
  },
  "plab": {
    "total_questions": 36,
    "total_attempts": 3,
    "correct_attempts": 2,
    "accuracy": 0.67
  },
  "anatomy": {
    "total_sessions": 2,
    "challenges_completed": 1,
    "challenges_correct": 1,
    "accuracy": 1.0,
    "structures_explored_count": 4
  },
  "adaptive": {
    "mastery_level": "DEVELOPING",
    "mastery_score": 0.72,
    "weak_topics": ["Hypertension (Essential & Secondary)"],
    "recommended_action": {
      "type": "REMEDIATE",
      "target_topic": "Hypertension (Essential & Secondary)"
    }
  },
  "summary": {
    "total_questions_attempted": 9,
    "overall_accuracy": 0.78,
    "active_modules": ["university", "plab", "anatomy"]
  }
}
```

*Data Ownership:* University owns `university.sqlite3`, PLAB owns `pilot_store.db`, Anatomy owns `anatomy.sqlite3`, Adaptive owns `learner_state.db`. The progress layer is purely a read-only projection.

---

## 7. Learning Intelligence Boundary

- **Educator-facing cohort analytics:** `GET /api/v1/learning-intelligence/reasoning-gaps`.
- **Privacy Suppression:** Enforces strict $N \ge 3$ minimum learner threshold. Individual learner IDs are never exposed in cohort intelligence.
- **Separation:** Student-facing progress endpoints and educator-facing cohort radar endpoints are strictly decoupled.

---

## 8. Production Routing Table

Mounted in both `production_main.py` and `main.py`:

| Service / Domain | Prefix | Endpoints |
| :--- | :--- | :--- |
| **University** | `/api/v1/university` | `/subjects`, `/topics`, `/question`, `/answer`, `/progress` |
| **PLAB** | `/api/v1/plab` | `/questions`, `/questions/{id}`, `/evaluate`, `/progress` |
| **Internal PLAB** | `/api/v1/internal/plab` | `/reviews`, `/review/*`, `/telemetry` |
| **3D Anatomy** | `/api/v1/anatomy` | `/structures`, `/command`, `/manifest`, `/session/start`, `/session/{id}`, `/session/{id}/interact`, `/session/{id}/challenge` |
| **Grounded Tutor** | `/api/v1/tutor` | `/chat` |
| **Adaptive Learning** | `/api/v1/adaptive` | `/state`, `/recommendation`, `/event`, `/remediate`, `/loop-status` |
| **Socratic Remediation** | `/api/v1/remediation` | `/start`, `/turn`, `/session/{id}`, `/session/{id}/transfer`, `/session/{id}/abandon` |
| **Learning Intelligence** | `/api/v1/learning-intelligence` | `/reasoning-gaps` |
| **Unified Progress** | `/api/v1/learner` | `/progress` (and `/api/v1/progress`) |

---

## 9. Test Verification Matrix

| Suite | Tests Collected | Passed | Failed | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 6 Integration** | 11 | 11 | 0 | **PASS** |
| **PLAB Regression** | 87 | 87 | 0 | **PASS** |
| **Grounded Tutor** | 82 | 82 | 0 | **PASS** |
| **Adaptive Learning** | 26 | 26 | 0 | **PASS** |
| **Socratic Remediation** | 60 | 60 | 0 | **PASS** |
| **University Track** | 36 | 36 | 0 | **PASS** |
| **Learning Intelligence** | 21 | 21 | 0 | **PASS** |
| **3D Anatomy** | 43 | 43 | 0 | **PASS** |
| **Clean Checkout Isolated PLAB** | 87 | 87 | 0 | **PASS** |
| **Total Test Suite** | **378** | **378** | **0** | **100% GREEN** |

---

## 10. Startup Demo Narrative

1. **Learner Onboarding:** Student logs into MedicalPlab with identity `X-User-Id: demo_medic_01`.
2. **University Session:** Learner answers renal physiology questions. Adaptive engine registers attempt and observes topic mastery.
3. **PLAB Clinical Exam:** Learner attempts clinical hypertension scenario (`PLAB-CARD-0001`). Chooses distractor Option B (Ramipril).
4. **Reasoning Gap Detection:** Platform identifies `PATTERN-RAAS-ENZ-01` (enzyme/cascade misconception).
5. **Socratic Remediation:** Learner enters Socratic dialogue. Tutor walks through 3 turns grounded in basic science, followed by successful transfer on a held-out clinical item.
6. **3D Anatomy Exploration:** Learner launches 3D Renal Hilum session, navigates structures, and completes deterministic challenge identifying `renal_artery_left`.
7. **Unified Progress Projection:** Student retrieves `/api/v1/learner/progress`, viewing an integrated dashboard across University, PLAB, Anatomy, and Adaptive recommendations.
8. **Educator Cohort Radar:** Faculty opens `/api/v1/learning-intelligence/reasoning-gaps` to inspect aggregate misconception trends across cohort students ($N \ge 3$) without violating individual student privacy.
