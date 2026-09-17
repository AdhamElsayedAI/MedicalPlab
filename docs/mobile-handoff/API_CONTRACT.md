# MedicalPlab REST API Contract — Mobile Developer Reference

This document provides the exhaustive specification of all backend endpoints relevant to mobile client development. All endpoints are derived directly from the runtime FastAPI application.

---

## 1. Endpoint Classification Inventory

### Category A: REQUIRED FOR MOBILE MVP
These endpoints support the complete, authoritative student learning journey.

| Method | Path | Description | Authentication / Headers |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/university/subjects` | List all available preclinical/clinical subjects | None required |
| `GET` | `/api/v1/university/topics` | List topics within a chosen subject | Query parameter `subject` |
| `GET` | `/api/v1/university/question` | Fetch a question within a topic without answer keys | Query parameters `subject`, `topic`, optional `after` |
| `POST` | `/api/v1/university/answer` | Submit student answer, persist attempt, return verification feedback | Header `X-User-Id` (min 8 chars) |
| `GET` | `/api/v1/adaptive/recommendation` | Retrieve highest-priority next learning action | Header `X-User-Id` or query `learner_id` |
| `GET` | `/api/v1/adaptive/state` | Retrieve full learner mastery profile, accuracy, and weak topics | Header `X-User-Id` or query `learner_id` |
| `POST` | `/api/v1/remediation/start` | Initiate a bounded 3-turn Socratic remediation session (Turn 1: Probe) | Header `X-User-Id` |
| `POST` | `/api/v1/remediation/turn` | Advance Socratic dialogue (Turn 2: Guide, Turn 3: Consolidate) | Header `X-User-Id` |
| `GET` | `/api/v1/remediation/session/{session_id}/transfer` | Retrieve eligible held-out transfer item (without answer keys) | Header `X-User-Id` |
| `POST` | `/api/v1/remediation/session/{session_id}/transfer` | Submit transfer answer for deterministic server-side evaluation | Header `X-User-Id` |
| `POST` | `/api/v1/remediation/session/{session_id}/abandon` | Explicitly abandon an ongoing remediation session | Header `X-User-Id` |
| `GET` | `/api/v1/remediation/session/{session_id}` | Retrieve authoritative session state, chat history, and timeline | Header `X-User-Id` |

| `GET` | `/api/v1/learner/progress` | Retrieve unified read-only learner progress across University, PLAB, Anatomy, and Adaptive | Header `X-User-Id` (or `X-Learner-Id`) |
| `GET` | `/api/v1/plab/questions` | List clinical PLAB exam questions | None required |
| `POST` | `/api/v1/plab/evaluate` | Evaluate PLAB question answer, emit LearningEvent, detect reasoning gap | Header `X-User-Id` |
| `GET` | `/api/v1/plab/progress` | Retrieve PLAB module-owned attempt history and accuracy | Header `X-User-Id` |

---

### Category B: OPTIONAL FOR MOBILE MVP
Secondary capabilities that enhance the mobile app but are not strictly required for the core student loop.

| Method | Path | Description | Usage Note |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` or `/api/v1/health` | Health check & service readiness | Useful for mobile connectivity monitoring |
| `POST` | `/api/v1/anatomy/session/start` | Initialize 3D Anatomy learning session | Header `X-User-Id` or `X-Learner-Id` |
| `POST` | `/api/v1/anatomy/session/{session_id}/challenge` | Submit deterministic anatomy pin challenge | Header `X-User-Id` or `X-Learner-Id` |
| `POST` | `/api/v1/tutor/chat` | Direct conversational tutor for open-ended clinical questions | Optional free-form tutor interface |
| `GET` | `/api/v1/cases` | List PLAB scenario cases | PLAB exam simulation track |
| `GET` | `/api/v1/cases/{case_id}` | Retrieve individual clinical case | PLAB exam simulation track |

---

### Category C: WEB / EDUCATOR ONLY
Educator-facing analytics and backend administrative routes. **Do not implement on mobile client.**

| Method | Path | Description | Reason for Exclusion |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/learning-intelligence/reasoning-gaps` | Cross-learner cohort reasoning-gap radar | Aggregated educator portal; enforces $N \ge 3$ privacy suppression |
| `GET` | `/api/v1/eval/status` | Benchmark evaluation status | Internal quality assurance |
| `POST` | `/api/v1/eval/run` | Trigger evaluation runner | Administrative compute operation |
| `GET` | `/api/v1/university/status` | Question bank audit status | Content management pipeline |

---

### Category D: INTERNAL / DO NOT USE DIRECTLY
Low-level pipeline endpoints, internal telemetry routes, or backwards-compatibility shims.

| Method | Path | Description | Identity Requirement |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/adaptive/event` | Internal telemetry ingestion (auto-emitted) | **Yes** (`resolve_learner_id(required=True)` -> `HTTP 401`) |
| `POST` | `/api/v1/adaptive/remediate` | Internal remediation trigger | **Yes** (`resolve_learner_id(required=True)` -> `HTTP 401`) |
| `GET` | `/api/v1/adaptive/loop-status` | Internal background loop evaluation | **Yes** (`resolve_learner_id(required=True)` -> `HTTP 401`) |
| `POST` | `/api/v1/evidence/packet` | Low-level RAG evidence packet retrieval | None |
| `POST` | `/api/v1/evidence/stage-e/retrieve` | Legacy stage-e retrieval service | None |
| `POST` | `/api/v1/query` | Direct raw vector search | None |
| `ALL` | `/{full_path:path}` | Universal Stage-G fallback proxy | None |

---

## 2. Universal Headers & Identity Contract

All mobile requests that interact with learner state **MUST** supply the `X-User-Id` header:

```http
Content-Type: application/json
X-User-Id: uni-e2a48b39-6541-4567-89ab-cdef01234567
```

### Invariants:
- **Format:** String between 8 and 120 characters (`min_length=8, max_length=120`).
- **Generation:** Created by the mobile app on first launch using UUIDv4 (recommended prefix: `uni-`).
- **Persistence:** Stored in secure local device storage.
- **Ownership:** Sessions and attempts belong strictly to the `X-User-Id` that created them. If a request sends a different `X-User-Id` for an existing session or attempt, the server returns `HTTP 403 Forbidden` (`Session does not belong to the requesting user.` / `SESSION_ACCESS_FORBIDDEN`).
- **Missing Header Behavior:** Endpoints utilizing canonical identity resolution (`resolve_learner_id(required=True)`) or `_student_id` fail closed with `HTTP 401 Unauthorized` (`{"detail": {"code": "USER_ID_REQUIRED", "message": "X-User-Id header is required."}}`). Note: University endpoints enforce header presence via FastAPI dependency validation and return `HTTP 422 Unprocessable Entity`; Anatomy session initialization returns `HTTP 400 Bad Request` if `learner_id` is omitted from both header and body.
- **Backward Compatibility:** `X-Learner-Id` is accepted as an alias in 3D Anatomy and progress projections. New mobile implementations must standardize on `X-User-Id`.

---

## 3. Required Endpoints Specification

### 3.1. List Subjects
Retrieve the list of available medical subjects and the question count for each.

- **URL:** `GET /api/v1/university/subjects`
- **Headers:** None required.
- **Response `200 OK`:**
  ```json
  {
    "items": [
      {
        "name": "Renal physiology",
        "count": 5
      }
    ]
  }
  ```

---

### 3.2. List Topics
Retrieve topics belonging to a specific subject.

- **URL:** `GET /api/v1/university/topics?subject=Renal%20physiology`
- **Query Parameters:**
  - `subject` (string, required): Exact name of the subject.
- **Response `200 OK`:**
  ```json
  {
    "items": [
      {
        "name": "Glomerular filtration barrier",
        "count": 2
      },
      {
        "name": "RAAS mechanisms",
        "count": 3
      }
    ]
  }
  ```
- **Error `404 Not Found`:** If the subject does not exist.

---

### 3.3. Retrieve Question (No Answer Leaks)
Fetch the next available question in a topic.

- **URL:** `GET /api/v1/university/question?subject=Renal%20physiology&topic=RAAS%20mechanisms`
- **Query Parameters:**
  - `subject` (string, required)
  - `topic` (string, required)
  - `after` (string, optional): ID of the previous question (e.g. `UNI-RENAL-001`) to advance to the next in sequence.
- **Security Check:** The returned object contains **ONLY** question presentation data (`id`, `stem`, `options`, `subject`, `topic`, `difficulty`). **It NEVER leaks `correct_answer`, `explanation`, or evidence references.**
- **Response `200 OK`:**
  ```json
  {
    "question": {
      "id": "UNI-RENAL-001",
      "track": "university",
      "stem": "In the renin-angiotensin pathway, which substrate does active renin cleave to form angiotensin I?",
      "subject": "Renal physiology",
      "topic": "RAAS mechanisms",
      "options": {
        "A": "Angiotensinogen",
        "B": "Angiotensin II",
        "C": "Aldosterone",
        "D": "Albumin"
      },
      "difficulty": "easy"
    },
    "position": 1,
    "total": 3
  }
  ```
- **Topic Complete Response:** When all questions have been served:
  ```json
  {
    "question": null,
    "next_action": "review_topic"
  }
  ```

---

### 3.4. Submit Answer & Receive Immediate Feedback
Submit the student's selected option. The server records the attempt in durable storage and returns authoritative feedback.

- **URL:** `POST /api/v1/university/answer`
- **Headers:** `X-User-Id` (required, 8-120 chars)
- **Request Body:**
  ```json
  {
    "question_id": "UNI-RENAL-001",
    "selected_option": "B",
    "idempotency_key": "att-8f92a10b-4567"
  }
  ```
- **Field Details:**
  - `question_id`: Exact ID of the question (e.g. `UNI-RENAL-001`).
  - `selected_option`: Single character matching `^[A-E]$`.
  - `idempotency_key`: Client-generated unique UUID preventing duplicate submissions.
- **Response `200 OK`:**
  ```json
  {
    "question_id": "UNI-RENAL-001",
    "is_correct": false,
    "correct_answer": "A",
    "explanation": "Renin acts on angiotensinogen to form angiotensin I. ACE then converts angiotensin I to angiotensin II; these are distinct steps in the pathway.",
    "subject": "Renal physiology",
    "topic": "RAAS mechanisms",
    "source": {
      "title": "The Renin-Angiotensin-aldosterone system in vascular inflammation and remodeling.",
      "url": "https://europepmc.org/article/PMC/PMC3997861",
      "license": "CC BY 3.0"
    },
    "next_action": "next_question",
    "progress": {
      "track": "university",
      "attempted": 1,
      "correct": 0,
      "accuracy": 0.0,
      "topics": [ ... ],
      "weak_topics": [ ... ],
      "recommendation": { ... }
    }
  }
  ```
- **Idempotency Semantics:**
  - Resending the exact same `(user_id, idempotency_key)` with the same `selected_option` returns the original response without creating a duplicate record.
  - Submitting a different `selected_option` with an already-used `idempotency_key` returns `HTTP 409 Conflict`.

---

### 3.5. Retrieve Adaptive Recommendation
Query the Adaptive Decision Engine to determine the pedagogical next step for the learner.

- **URL:** `GET /api/v1/adaptive/recommendation`
- **Headers:** `X-User-Id` (optional query parameter `learner_id` can also be used).
- **Response `200 OK` (when remediation is advised):**
  ```json
  {
    "recommendation_id": "rec-f912c401",
    "action": "ASK_GROUNDED_TUTOR",
    "subject": "Renal physiology",
    "topic": "RAAS mechanisms",
    "priority": "high",
    "target_question_id": "UNI-RENAL-001",
    "tutor_mode": "socratic",
    "tutor_query": "I am having difficulty understanding RAAS mechanisms. Can you explain the core mechanism?",
    "reason": "1 recent incorrect attempts detected (failure rate: 100.0%)",
    "explanation": "Focus on RAAS mechanisms: 1 recent errors detected. Socratic remediation recommended to consolidate underlying concepts."
  }
  ```
- **Adaptive Actions Enum (`action`):**
  - `ASK_GROUNDED_TUTOR`: Initiate Socratic remediation for an identified misconception.
  - `SOLVE_TARGETED_QUESTION`: Practice questions targeting a developing topic.
  - `REVIEW_CONCEPT`: Review foundational concepts for a topic needing revision.
  - `REPEAT_TOPIC`: Reinforce topic after incomplete remediation.

---

### 3.6. Retrieve Learner State
Unified educational view of learner accuracy, mastery levels, and active weaknesses.

- **URL:** `GET /api/v1/adaptive/state`
- **Headers:** `X-User-Id` (required -> `HTTP 401 USER_ID_REQUIRED` if omitted)
- **State Classification:** `DERIVED`. Recomputed on demand by `UnifiedLearnerStateManager` from authoritative module-owned persistence (University SQLite `university_attempts`, PLAB pilot attempt registry, and 3D Anatomy repository sessions). There is no dedicated "Telemetry DB". Server restarts safely recompute state without losing learner progress.
- **Response `200 OK`:**
  ```json
  {
    "learner_id": "uni-smoke-0a61d6c6",
    "total_attempts": 1,
    "correct_attempts": 0,
    "overall_accuracy": 0.0,
    "topic_mastery": {
      "RAAS mechanisms": {
        "subject": "Renal physiology",
        "topic": "RAAS mechanisms",
        "total_attempts": 1,
        "correct_attempts": 0,
        "accuracy": 0.0,
        "mastery_score": 0.0,
        "mastery_level": "beginner",
        "mastery_status": "needs_review",
        "confidence": "low",
        "consecutive_errors": 1,
        "last_attempt_correct": false
      }
    },
    "weak_topics": [
      {
        "subject": "Renal physiology",
        "topic": "RAAS mechanisms",
        "priority": "high",
        "failure_rate": 1.0,
        "missed_count": 1,
        "total_attempts": 1,
        "consecutive_errors": 1,
        "reason": "1 recent incorrect attempts detected (failure rate: 100.0%)"
      }
    ],
    "recommendations": [ ... ]
  }
  ```

---

### 3.7. Socratic Remediation: Start Session (Turn 1: Probe)
Initiate a bounded 3-turn Socratic remediation session for an incorrect answer.

- **URL:** `POST /api/v1/remediation/start`
- **Headers:** `X-User-Id` (required)
- **Prerequisite:** Feature flag `MEDICALPLAB_PHASE_2B_ENABLED=true` must be set on server.
- **Request Body:**
  ```json
  {
    "question_id": "UNI-RENAL-001",
    "selected_option": "B",
    "attempt_id": "att-8f92a10b-4567",
    "idempotency_key": "rem-start-uuid-1"
  }
  ```
- **Business Rules Enforced:**
  - `question_id` must exist in the question bank (404 otherwise).
  - `selected_option` must be an **incorrect** distractor. Submitting the correct answer returns `HTTP 422`.
  - If `attempt_id` is supplied, the server validates provenance in `university_attempts`. Attempt must exist (404), belong to the requesting user (403), match the question/option (422), and be incorrect (422).
- **Response `200 OK` (Turn 1 Probe):**
  ```json
  {
    "session_id": "REM-E1703DEAD098",
    "turn_number": 1,
    "max_turns": 3,
    "is_complete": false,
    "lifecycle_state": "REMEDIATING",
    "outcome": null,
    "remediation_status": "PROBING",
    "pattern_id": "PATTERN-RAAS-SUB-01",
    "reasoning_pattern": "substrate_confusion",
    "strategy": "GUIDED_RECALL",
    "timeline": {
      "initial_pattern": "Selected Option B: Inverting the substrate-enzyme relationship in the renin pathway",
      "learning_gap": "Pedagogical category: general_conceptual_gap. Confusing renin's substrate (angiotensinogen) with downstream products",
      "guided_practice": "Turn 1: Socratic probe initiated",
      "transfer_result": "Awaiting independent transfer assessment",
      "next_recommendation": null,
      "status": "IN_PROGRESS"
    },
    "tutor_message": "Let's explore this step by step. What is the initial molecule released by the liver that renin acts upon?",
    "socratic_probe": "What is the initial molecule released by the liver?",
    "citations": [
      {
        "source": "DOC-PMC-RENAL-0001",
        "chunk_id": "DOC-PMC-RENAL-0001-B0003-C01",
        "excerpt": "Active renin acts upon its substrate, angiotensinogen..."
      }
    ],
    "transfer_available": false
  }
  ```

---

### 3.8. Socratic Remediation: Advance Turn (Turns 2 & 3)
Advance the dialogue through Turn 2 (Guide) and Turn 3 (Consolidate).

- **URL:** `POST /api/v1/remediation/turn`
- **Headers:** `X-User-Id` (required)
- **Request Body:**
  ```json
  {
    "session_id": "REM-E1703DEAD098",
    "student_message": "I understand that macula densa senses sodium, and juxtaglomerular cells secrete renin to act on angiotensinogen.",
    "idempotency_key": "turn-2-uuid"
  }
  ```
- **Turn Progression Lifecycle:**
  - **Turn 2 (GUIDE):** Server provides a scaffolded clue to guide the student toward resolving the misconception. Returns `turn_number: 2`, `lifecycle_state: "REMEDIATING"`, `transfer_available: false`.
  - **Turn 3 (CONSOLIDATE):** Synthesizes the physiological concept and tests readiness for independent transfer.
    - If question has held-out transfer support: returns `turn_number: 3`, `lifecycle_state: "AWAITING_TRANSFER"`, `transfer_available: true`.
    - If question has NO transfer support: returns `turn_number: 3`, `lifecycle_state: "AWAITING_TRANSFER"`, `transfer_available: true` (or `transfer_available: false` if terminal).
- **Turn Bound Rule:** Calling `/turn` after Turn 3 returns `HTTP 400 Bad Request` ("Turn progression out of bounds").

---

### 3.9. Retrieve Held-out Transfer Item (No Answer Leaks)
Fetch the independent held-out assessment question once the session reaches `AWAITING_TRANSFER`.

- **URL:** `GET /api/v1/remediation/session/{session_id}/transfer`
- **Headers:** `X-User-Id` (required)
- **Prerequisites:** Session must be in `lifecycle_state: "AWAITING_TRANSFER"` (returns `HTTP 422` otherwise).
- **Security Check:** Strictly stripped of correct answers, explanations, or distractor annotations.
- **Response `200 OK`:**
  ```json
  {
    "question_id": "UNI-RENAL-001-T",
    "stem": "In an investigation of renovascular regulation, an elevated plasma renin activity is observed. Which circulating hepatic globular glycoprotein serves as the direct cleavage substrate for active renin?",
    "options": {
      "A": "Angiotensinogen",
      "B": "Angiotensin II",
      "C": "Aldosterone",
      "D": "Bradykinin"
    },
    "subject": "Renal physiology",
    "topic": "RAAS mechanisms",
    "difficulty": "medium",
    "evidence_title": "The Renin-Angiotensin-aldosterone system in vascular inflammation and remodeling.",
    "evidence_license": "CC BY 3.0"
  }
  ```
- **Transfer Unavailable Response `404 Not Found`:** If the question does not have a registered held-out transfer item (e.g. `UNI-RENAL-003`), the endpoint returns:
  ```json
  {
    "detail": "No eligible held-out transfer item available for question 'UNI-RENAL-003'."
  }
  ```

---

### 3.10. Submit Transfer Answer & Score Deterministically
Submit the student's selected answer for the transfer item.

- **URL:** `POST /api/v1/remediation/session/{session_id}/transfer`
- **Headers:** `X-User-Id` (required)
- **Request Body:**
  ```json
  {
    "session_id": "REM-E1703DEAD098",
    "question_id": "UNI-RENAL-001-T",
    "selected_option": "A",
    "was_assisted": false,
    "idempotency_key": "submit-transfer-uuid"
  }
  ```
- **Invariants:**
  - The transfer item must have been dispensed via `GET /transfer` first (`HTTP 422` if not).
  - `question_id` must match the dispensed item (`HTTP 422` if mismatch).
  - `was_assisted`: If true, the attempt is strictly disqualified from `TRANSFER_CONFIRMED`.
- **Response `200 OK` (when correct and unassisted):**
  ```json
  {
    "session_id": "REM-E1703DEAD098",
    "outcome": "TRANSFER_CONFIRMED",
    "is_correct": true,
    "explanation": "Active renin specifically cleaves the peptide bond in circulating angiotensinogen...",
    "citations": [ ... ],
    "timeline": {
      "initial_pattern": "Selected Option B: Inverting the substrate-enzyme relationship...",
      "learning_gap": "Pedagogical category: general_conceptual_gap...",
      "guided_practice": "Completed 3 Socratic guidance turns",
      "transfer_result": "Independent transfer confirmed on held-out question UNI-RENAL-001-T",
      "next_recommendation": "Recommended action: SOLVE_TARGETED_QUESTION on RAAS mechanisms.",
      "status": "COMPLETED"
    },
    "next_recommendation": {
      "explanation": "Recommended action: SOLVE_TARGETED_QUESTION on RAAS mechanisms."
    }
  }
  ```
- **Response `200 OK` (when incorrect):**
  ```json
  {
    "session_id": "REM-E1703DEAD098",
    "outcome": "TRANSFER_NOT_CONFIRMED",
    "is_correct": false,
    "explanation": "Active renin specifically cleaves the peptide bond in circulating angiotensinogen...",
    "citations": [ ... ],
    "timeline": {
      "status": "COMPLETED",
      "transfer_result": "Transfer assessment not confirmed: submitted incorrect option B"
    }
  }
  ```

---

### 3.11. Abandon Remediation Session
Explicitly exit or abandon an active remediation dialogue.

- **URL:** `POST /api/v1/remediation/session/{session_id}/abandon`
- **Headers:** `X-User-Id` (required)
- **Response `200 OK`:**
  ```json
  {
    "session_id": "REM-E1703DEAD098",
    "turn_number": 2,
    "max_turns": 3,
    "is_complete": true,
    "lifecycle_state": "COMPLETED",
    "outcome": "ABANDONED",
    "remediation_status": "UNRESOLVED",
    "timeline": {
      "status": "COMPLETED",
      "transfer_result": "Session abandoned: Learner exited session"
    },
    "transfer_available": false
  }
  ```

---

### 3.12. Inspect / Restore Remediation Session (GET)
Retrieve the complete session state, turn history, and timeline. Used on app launch, resume, or page reload.

- **URL:** `GET /api/v1/remediation/session/{session_id}`
- **Headers:** `X-User-Id` (required; validates ownership)
- **Response `200 OK`:**
  ```json
  {
    "session_id": "REM-E1703DEAD098",
    "user_id": "uni-smoke-0a61d6c6",
    "question_id": "UNI-RENAL-001",
    "topic": "RAAS mechanisms",
    "turn_number": 3,
    "max_turns": 3,
    "is_complete": true,
    "lifecycle_state": "COMPLETED",
    "outcome": "TRANSFER_CONFIRMED",
    "strategy": "GUIDED_RECALL",
    "timeline": {
      "initial_pattern": "Selected Option B...",
      "learning_gap": "Pedagogical category: general_conceptual_gap...",
      "guided_practice": "Completed 3 Socratic guidance turns",
      "transfer_result": "Independent transfer confirmed on held-out question UNI-RENAL-001-T",
      "next_recommendation": "Recommended action: SOLVE_TARGETED_QUESTION on RAAS mechanisms.",
      "status": "COMPLETED"
    },
    "turns": [
      {
        "turn_number": 1,
        "phase": "PROBE",
        "tutor_message": "...",
        "socratic_probe": "...",
        "student_message": null,
        "citations": [ ... ],
        "is_safety_fallback": false
      },
      {
        "turn_number": 2,
        "phase": "GUIDE",
        "tutor_message": "...",
        "socratic_probe": "...",
        "student_message": "I understand that macula densa...",
        "citations": [ ... ],
        "is_safety_fallback": false
      },
      {
        "turn_number": 3,
        "phase": "CONSOLIDATE",
        "tutor_message": "...",
        "socratic_probe": "...",
        "student_message": "Juxtaglomerular cells directly...",
        "citations": [ ... ],
        "is_safety_fallback": false
      }
    ],
    "transfer_item": null,
    "transfer_attempt": {
      "question_id": "UNI-RENAL-001-T",
      "submitted_option": "A",
      "is_correct": true,
      "was_assisted": false
    }
  }
  ```

---

## 4. PLAB Clinical Exam Mobile Contract & Readiness State

### 4.1. Contract Separation: Preview QA vs. Public Student Ready

The PLAB clinical exam preparation endpoints (`/api/v1/plab/*`) operate under a strict governance gate to prevent unapproved medical content from reaching production student clients:

| Dimension | `PLAB_PREVIEW_QA` / Internal Demo | `PLAB_PUBLIC_STUDENT_READY` |
| :--- | :--- | :--- |
| **Server Flag** | `MEDICALPLAB_PLAB_PREVIEW_QA=1` | Default production (`golden_only=True`, no flag) |
| **Intended Audience** | Internal engineering, QA testing, mentor demonstration | Public medical students |
| **Question Status** | Seeded candidate items in review workflow | Clinician-reviewed, formally promoted **Golden Questions** |
| **`GET /api/v1/plab/questions`** | Returns candidate items with `content_mode: "PREVIEW_QA"` and explicit warning | Returns `count: 0`, `items: []`, `content_policy: "GOLDEN_ONLY"` until golden promotion |
| **`POST /api/v1/plab/evaluate`** | Evaluates answers, reveals explanations, detects reasoning gaps | Returns `HTTP 403 QUESTION_NOT_AVAILABLE` for unpromoted questions |
| **Answer Leakage** | **Zero leakage** pre-answer (`correct_answer`, `explanation`, `citations` omitted) | **Zero leakage** |

> [!WARNING]
> **Mobile Client Enforcement Rule:**
> Mobile clients MUST distinguish between internal demo/preview QA and public student production. Mobile clients MUST NOT present preview-only PLAB questions as production-ready student curriculum.

### 4.2. Mobile Integration Certification Status

As of Phase 6.1:
- **Mobile Backend Handoff Status:** `MOBILE_BACKEND_HANDOFF_READY`
- **Public Student Release Status:** `PLAB_PUBLIC_RELEASE_READY = NO`
- **Prerequisite for Student Release:** `PLAB_GOLDEN_PROMOTION_REQUIRED = YES`

Backend API contracts, schema serialization, idempotency validation, error matrices, and reasoning-gap bridges are fully hardened and integration-tested for mobile handoff. Public student release of the PLAB exam track requires completion of the clinician review workflow to promote candidate items to golden status.

---

## 5. Exact Mobile Runtime Enum Contract

Mobile client applications must serialize and deserialize exact runtime string enum values (not approximate UI presentation strings):

### 5.1. Socratic Remediation Enums
- **`RemediationLifecycleState`:**
  - `"CREATED"`: Initialized from failed attempt.
  - `"REMEDIATING"`: In-progress 3-turn Socratic dialogue (Turns 1-3).
  - `"AWAITING_TRANSFER"`: Dialogue completed; awaiting independent transfer assessment.
  - `"COMPLETED"`: Concluded with terminal outcome.
- **`RemediationStatus`:**
  - `"PROBING"`: Turn 1 (Challenging flawed premise neutrally).
  - `"GUIDING"`: Turn 2 (Providing grounded mechanistic clue).
  - `"CONFIRMING"`: Turn 3 (Synthesizing and checking readiness).
  - `"RESOLVED"`: Backward-compatible resolution indicator.
  - `"UNRESOLVED"`: Terminal non-resolution.
- **`RemediationOutcome`:**
  - `"TRANSFER_CONFIRMED"`: Correct on held-out transfer item without assistance.
  - `"TRANSFER_NOT_CONFIRMED"`: Incorrect on held-out transfer item.
  - `"UNRESOLVED"`: Assisted transfer, unavailable transfer item, or turn limit reached.
  - `"ABANDONED"`: Explicit student exit or cancellation.
  - `"SAFETY_FALLBACK"`: Retrieval failure or claim verification fail-closed fallback.
- **`SocraticStrategyType`:**
  - `"GUIDED_RECALL"`
  - `"CONTRAST_CASE"`
  - `"STEPWISE_DECOMPOSITION"`
  - `"COUNTEREXAMPLE_PROBE"`

### 5.2. 3D Anatomy Lab Enums
- **`AnatomyActionType`:**
  - `"FOCUS_STRUCTURE"`: Camera focus and recenter on structure.
  - `"HIGHLIGHT_STRUCTURE"`: Visual outline / mesh highlight.
  - `"ISOLATE_STRUCTURE"`: Isolate target structure; hide others.
  - `"SHOW_STRUCTURE"`: Make target structure visible.
  - `"HIDE_STRUCTURE"`: Hide target structure.
  - `"SHOW_RELATION"`: Draw anatomical relationship / flow indicator.
  - `"SET_STRUCTURE_OPACITY"`: Adjust transparency (`opacity: 0.0 - 1.0`).
  - `"RESET_SCENE"`: Restore baseline 3D camera and visibility.
- **`LessonState`:**
  - `"INTRO"`: Introductory orientation.
  - `"GUIDED_VESSELS"`: Guided vessel identification.
  - `"GUIDED_IDENTIFICATION"`: Guided parenchymal structures.
  - `"CHALLENGE_READY"`: Challenge ready for student attempt.
  - `"CHALLENGE_ACTIVE"`: Challenge currently active.
  - `"COMPLETED"`: Lesson completed.
- **`ChallengeResult`:**
  - `"PENDING"`: Awaiting evaluation.
  - `"CORRECT"`: Challenge successfully identified target structure.
  - `"INCORRECT"`: Wrong structure identified.
- **`InteractionRequestType`:**
  - `"IDENTIFY_STRUCTURE"`: Prompt requesting identification of structure.
  - `"EXPLORE_SCENE"`: Open exploratory navigation prompt.

