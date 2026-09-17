# MedicalPlab — Mobile Developer Integration & API Contract Handoff
**Document Version:** 1.1.0  
**API Namespace:** `/api/v1`  
**API Contract Freeze:** Certified Runtime Baseline  
**OpenAPI Specification:** [`docs/mobile-handoff/openapi.json`](./openapi.json)  
**Postman Collection:** [`docs/mobile-handoff/MedicalPlab.mobile.postman_collection.json`](./MedicalPlab.mobile.postman_collection.json)  
**Postman Environment:** [`docs/mobile-handoff/MedicalPlab.mobile.postman_environment.json`](./MedicalPlab.mobile.postman_environment.json)

---

## 1. What MedicalPlab API Provides
MedicalPlab is an adaptive, evidence-grounded medical learning platform backend. It exposes high-integrity REST/JSON APIs for:
1. **Preclinical University Learning:** Curriculum-mapped renal physiology question bank with instant explanations and automatic telemetry generation.
2. **Clinical PLAB Learning:** Clinical scenario questions with evidence grounding and audit logging (currently governed under strict Preview QA / Golden-Question gating).
3. **Grounded Socratic Tutor:** Multi-turn conversational tutor backed by peer-reviewed Open Access literature (PubMed Central / HuBMAP) with verification and zero answer hallucination.
4. **Adaptive Learning Engine:** Continuous learner mastery profiling, error tracking, and personalized next-step learning recommendations.
5. **Intelligent Socratic Remediation:** Bounded 3-turn Socratic dialogues (`PROBE` -> `GUIDE` -> `CONSOLIDATE`) triggering held-out transfer problem verification.
6. **Generative 3D Anatomy Lab:** Renderer-agnostic anatomical scene actions and deterministic interactive spatial identification challenges (HuBMAP Human Reference Atlas).
7. **Unified Learner Progress:** Single-call aggregated dashboard projection spanning University, PLAB, Adaptive, and 3D Anatomy tracks.

---

## 2. Quick Start
To run the certified MedicalPlab backend locally:
```bash
# 1. Clone repository and navigate to root
cd MedicalPlab

# 2. Configure Python environment & feature flags
export PYTHONPATH="src"
export MEDICALPLAB_RUNTIME_MODE="pilot"
export MEDICALPLAB_PHASE_2B_ENABLED="1"
export MEDICALPLAB_ANATOMY_3D_ENABLED="1"

# For PLAB QA/demo testing:
export MEDICALPLAB_PLAB_PREVIEW_QA="1"

# 3. Start authoritative server
python -m uvicorn production_main:app --host 0.0.0.0 --port 8000 --workers 1
```

Verify backend health:
```bash
curl -s http://127.0.0.1:8000/health
# Expected: {"status":"healthy","service":"MedicalPlab Product API","version":"1.1.0",...}
```

---

## 3. Base URL Contract
The mobile client **must** store and read the backend Base URL from client configuration:
```
MEDICALPLAB_API_BASE_URL
```
**Never hardcode `localhost` or `127.0.0.1` inside mobile application code.**

### Network Environment Guidance:
- **Local Machine / Simulator / Emulator:**
  - iOS Simulator: `http://127.0.0.1:8000`
  - Android Emulator: `http://10.0.2.2:8000` (Android maps 10.0.2.2 to the host loopback)
- **Physical Device (LAN Development):**
  - Run Uvicorn listening on `0.0.0.0:8000`.
  - Configure mobile app with the developer machine's LAN IP: `http://<development-host-ip>:8000`.
  - *Note: A physical device cannot reach your computer using its own `127.0.0.1`.*
- **Staging / Production:**
  - `https://<deployed-medicalplab-api>` (Production deployments MUST expose MedicalPlab through HTTPS with a valid TLS certificate).

---

## 4. Canonical Learner Identity (`X-User-Id`)
Every learner-scoped request **must** provide the learner identity header:
```http
X-User-Id: <learner_identifier>
```
- **Type:** String (8 to 120 characters, URL-safe alphanumeric, dashes, underscores).
- **Example:** `X-User-Id: learner_mobile_dev_001`
- **Backward Compatibility:** `X-Learner-Id` is accepted as a legacy alias in 3D Anatomy and CORS configurations. New mobile implementations must standardize on `X-User-Id`.
- **Missing Header Behavior:** Endpoints utilizing canonical identity resolution (`resolve_learner_id(required=True)`) fail closed with `HTTP 401 Unauthorized` (`{"detail": {"code": "USER_ID_REQUIRED", "message": "X-User-Id header is required."}}`). Note: University endpoints enforce header presence via FastAPI dependency validation and return `HTTP 422 Unprocessable Entity`; Anatomy session initialization returns `HTTP 400 Bad Request` if `learner_id` is omitted from both header and body.

---

## 5. Security & Authentication Reality
> [!IMPORTANT]
> **Identity Contract Only — Not Cryptographic Authentication.**
> `X-User-Id` establishes learner state isolation and progress partitioning across the API. It is **not** a signed JWT, session cookie, or OAuth token.
>
> **Status:** `MOBILE_PRODUCTION_AUTH_READY = NO`
>
> This design is intentional for the hackathon/pilot integration gate to allow rapid, zero-friction client development and offline demonstration. A production mobile release must terminate TLS and introduce a token-issuing identity gateway (e.g., OAuth2 / Supabase / Firebase / Cognito) upstream of the API.

---

## 6. Authoritative Endpoint Classification Matrix
All 44 operations across 43 paths in OpenAPI are categorized into exactly one lifecycle classification:

| Method | Path | Domain | Classification | Identity Req? | Idempotent? | Mutates State? | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GET** | `/health` | System | `MOBILE_PUBLIC` | No | Yes | No | Liveness probe & uptime |
| **GET** | `/ready` | System | `MOBILE_PUBLIC` | No | Yes | No | Readiness & governance blockers |
| **GET** | `/api/v1/version` | System | `MOBILE_PUBLIC` | No | Yes | No | API version & contract date |
| **GET** | `/` | System | `LEGACY_NOT_FOR_NEW_MOBILE` | No | Yes | No | Root server landing info |
| **GET** | `/api/v1/university/subjects` | University | `MOBILE_PUBLIC` | No | Yes | No | List subjects & question counts |
| **GET** | `/api/v1/university/topics` | University | `MOBILE_PUBLIC` | No | Yes | No | List topics for a subject |
| **GET** | `/api/v1/university/question` | University | `MOBILE_PUBLIC` | No | Yes | No | Fetch next question (no leak) |
| **POST** | `/api/v1/university/answer` | University | `MOBILE_PUBLIC` | **Yes** | **Yes** | **Yes** | Submit answer & receive explanation |
| **GET** | `/api/v1/university/progress` | University | `MOBILE_PUBLIC` | **Yes** | Yes | No | Retrieve university track progress |
| **GET** | `/api/v1/plab/questions` | PLAB | `MOBILE_PREVIEW_ONLY` | No | Yes | No | List PLAB questions (Preview QA only) |
| **GET** | `/api/v1/plab/questions/{id}` | PLAB | `MOBILE_PREVIEW_ONLY` | No | Yes | No | Fetch PLAB question (no leak) |
| **POST** | `/api/v1/plab/evaluate` | PLAB | `MOBILE_PREVIEW_ONLY` | **Yes** | **Yes** | **Yes** | Evaluate PLAB answer with RAG evidence |
| **GET** | `/api/v1/plab/progress` | PLAB | `MOBILE_PREVIEW_ONLY` | **Yes** | Yes | No | Retrieve PLAB track progress |
| **POST** | `/api/v1/tutor/chat` | Tutor | `MOBILE_PUBLIC` | Optional | No | No | Socratic grounded dialogue |
| **GET** | `/api/v1/adaptive/state` | Adaptive | `MOBILE_PUBLIC` | **Yes** | Yes | No | Retrieve mastery & error telemetry |
| **GET** | `/api/v1/adaptive/recommendation` | Adaptive | `MOBILE_PUBLIC` | **Yes** | Yes | No | Recommended next learning step |
| **POST** | `/api/v1/remediation/start` | Remediation | `MOBILE_PUBLIC` | **Yes** | **Yes** | **Yes** | Start 3-turn remediation (Turn 1) |
| **POST** | `/api/v1/remediation/turn` | Remediation | `MOBILE_PUBLIC` | **Yes** | **Yes** | **Yes** | Advance dialogue (Turn 2 / Turn 3) |
| **GET** | `/api/v1/remediation/session/{id}` | Remediation | `MOBILE_PUBLIC` | **Yes** | Yes | No | Resume & view remediation session |
| **GET** | `/api/v1/remediation/session/{id}/transfer` | Remediation | `MOBILE_PUBLIC` | **Yes** | Yes | No | Fetch held-out transfer item (no leak) |
| **POST** | `/api/v1/remediation/session/{id}/transfer` | Remediation | `MOBILE_PUBLIC` | **Yes** | **Yes** | **Yes** | Submit transfer item answer |
| **POST** | `/api/v1/remediation/session/{id}/abandon` | Remediation | `MOBILE_PUBLIC` | **Yes** | **Yes** | **Yes** | Explicitly abandon session |
| **GET** | `/api/v1/anatomy/manifest` | 3D Anatomy | `MOBILE_PUBLIC` | No | Yes | No | 3D anatomical manifest & CC BY 4.0 |
| **GET** | `/api/v1/anatomy/structures` | 3D Anatomy | `MOBILE_PUBLIC` | No | Yes | No | Supported anatomical structures |
| **POST** | `/api/v1/anatomy/session/start` | 3D Anatomy | `MOBILE_PUBLIC` | **Yes** | **Yes** | **Yes** | Initialize 3D Anatomy lesson session |
| **GET** | `/api/v1/anatomy/session/{id}` | 3D Anatomy | `MOBILE_PUBLIC` | **Yes** | Yes | No | Inspect anatomy session state |
| **POST** | `/api/v1/anatomy/session/{id}/interact` | 3D Anatomy | `MOBILE_PUBLIC` | **Yes** | No | **Yes** | Advance dialogue / structure click |
| **POST** | `/api/v1/anatomy/session/{id}/challenge` | 3D Anatomy | `MOBILE_PUBLIC` | **Yes** | **Yes** | **Yes** | Submit 3D structure challenge answer |
| **GET** | `/api/v1/learner/progress` | Progress | `MOBILE_PUBLIC` | **Yes** | Yes | No | Canonical unified dashboard projection |
| **GET** | `/api/v1/progress` | Progress | `MOBILE_PUBLIC` | **Yes** | Yes | No | Backward-compatible progress alias |
| **GET** | `/api/v1/learning-intelligence/reasoning-gaps` | Intelligence | `EDUCATOR_ONLY` | No | Yes | No | Cohort analytics (N>=3 suppression) |
| **POST** | `/api/v1/adaptive/event` | Adaptive | `INTERNAL_ONLY` | **Yes** | Yes | Yes | Telemetry ingestion (auto-emitted) |
| **POST** | `/api/v1/adaptive/remediate` | Adaptive | `INTERNAL_ONLY` | **Yes** | No | Yes | Internal remediation trigger |
| **GET** | `/api/v1/adaptive/loop-status` | Adaptive | `INTERNAL_ONLY` | **Yes** | Yes | No | Background worker status |
| **PATCH** | `/api/v1/internal/plab/questions/{id}/revision` | Internal | `INTERNAL_ONLY` | No | No | Yes | Clinician question revision |
| **GET** | `/api/v1/internal/plab/review/status/{id}` | Internal | `INTERNAL_ONLY` | No | Yes | No | Clinician review status |
| **POST** | `/api/v1/internal/plab/review/{id}/decision` | Internal | `INTERNAL_ONLY` | No | Yes | Yes | Clinician approval decision |
| **GET** | `/api/v1/internal/plab/review/{id}/promotion-eligibility` | Internal | `INTERNAL_ONLY` | No | Yes | No | Golden promotion eligibility check |
| **POST** | `/api/v1/internal/plab/review/{id}/start` | Internal | `INTERNAL_ONLY` | No | Yes | Yes | Start clinician review lock |
| **GET** | `/api/v1/internal/plab/reviews` | Internal | `INTERNAL_ONLY` | No | Yes | No | List reviews across corpus |
| **GET** | `/api/v1/internal/plab/telemetry` | Internal | `INTERNAL_ONLY` | No | Yes | No | Review governance telemetry |
| **POST** | `/api/v1/anatomy/command` | 3D Anatomy | `LEGACY_NOT_FOR_NEW_MOBILE` | No | Yes | No | Legacy command string validator |
| **POST** | `/api/v1/clinical/reason` | Clinical AI | `LEGACY_NOT_FOR_NEW_MOBILE` | No | No | No | Unwired legacy clinical endpoint (503) |
| **POST** | `/api/v1/learn/query` | Learn | `LEGACY_NOT_FOR_NEW_MOBILE` | No | Yes | No | Cross-track retrieval debug endpoint |

---

## 7. University Learning Flow
1. **Query Curriculum:**
   - `GET /api/v1/university/subjects` -> returns `{"items": [{"name": "Renal physiology", "count": 6}]}`.
   - `GET /api/v1/university/topics?subject=Renal%20physiology` -> returns `{"items": [{"name": "Glomerular filtration barrier", "count": 3}, ...]}`.
2. **Fetch Question:**
   - `GET /api/v1/university/question?subject=...&topic=...`
   - Delivered question contains `id`, `stem`, `options` (dictionary of `A`, `B`, `C`, `D`, `E`), `subject`, `topic`, `difficulty`.
   - **Zero pre-submission answer leakage:** `correct_answer`, `is_correct`, and `explanation` are omitted.
3. **Submit Answer:**
   - `POST /api/v1/university/answer` with `{"question_id": "...", "selected_option": "B", "idempotency_key": "..."}`.
   - Header: `X-User-Id: <user_id>`.
   - Returns: `is_correct: bool`, `attempt_id: str`, `explanation: str`, and automatically emits telemetry into the Adaptive engine.
4. **Check Progress:**
   - `GET /api/v1/university/progress` -> returns `attempted`, `correct`, `accuracy`, and topic-level mastery.

---

## 8. PLAB Flow & Governance Contract
> [!WARNING]
> **Strict Governance: Public Release is Gated.**
> - `PLAB_PUBLIC_RELEASE_READY = NO`
> - `PLAB_GOLDEN_PROMOTION_REQUIRED = YES`
>
> In default production mode, `GET /api/v1/plab/questions` returns `count: 0` (`policy: GOLDEN_ONLY`) because no clinician-promoted golden items exist yet.
>
> **Preview QA Mode (For Mentors, Judges, and QA Engineers):**
> When the backend is run with `MEDICALPLAB_PLAB_PREVIEW_QA=1`, the 36 candidate questions become available with `content_mode: "PREVIEW_QA"` and an explicit banner warning: *"Not clinically approved; internal QA only"*.
>
> **Mobile Client Rule:** Public student applications must **not** present preview items as approved PLAB curriculum. Display an informational empty state unless Preview QA is enabled.

---

## 9. Grounded Tutor / RAG Flow
- **Endpoint:** `POST /api/v1/tutor/chat`
- **Request Body:**
  ```json
  {
    "query": "Explain how podocyte foot processes prevent proteinuria.",
    "topic": "Glomerular filtration barrier",
    "mode": "auto"
  }
  ```
- **Response Structure:**
  - `message`: Socratic text explanation.
  - `support_status`: `"SUPPORTED"` (evidence verified) or `"SAFE_FALLBACK"` (insufficient evidence or refusal).
  - `citations`: List of literature references (`document_id`, `quote`, `title`, `license`).
  - `verification`: Propositional verification summary (`supported_propositions`, `unsupported_propositions`, `veto_flags`).
- **Mobile Client Rule:** Always render citations provided in the response payload. Never attempt to perform client-side web search or retrieval.

---

## 10. Adaptive Learning Flow
- **State:** `GET /api/v1/adaptive/state` -> Returns full learner mastery model: `topic_mastery`, `weak_topics`, `total_attempts`, `overall_accuracy`.
- **Recommendation:** `GET /api/v1/adaptive/recommendation` -> Returns the optimal immediate next action:
  - `ASK_GROUNDED_TUTOR`: Suggested Socratic query for a recurring weak topic.
  - `SOLVE_TARGETED_QUESTION`: Next curriculum question.
- **Important:** Do **not** call `POST /api/v1/adaptive/event` from mobile clients. University, PLAB, and Anatomy interactions automatically emit learning events server-side.

---

## 11. Socratic Remediation Flow
When a learner selects a known distractor (e.g. on `UNI-RENAL-001` selecting `B`), an intelligent 3-turn remediation session can be initiated:

```
[Start Session] -> Turn 1: PROBE (Challenge flawed premise)
      │
[Advance Turn]  -> Turn 2: GUIDE (Grounded mechanistic clue)
      │
[Advance Turn]  -> Turn 3: CONSOLIDATE (Check readiness -> AWAITING_TRANSFER)
      │
[Fetch Item]    -> GET /session/{id}/transfer (Held-out transfer problem, no leak)
      │
[Submit Answer] -> POST /session/{id}/transfer (Deterministic scoring)
      │
      ▼
  Outcomes:
  - TRANSFER_CONFIRMED     (Unassisted correct transfer)
  - TRANSFER_NOT_CONFIRMED (Incorrect transfer)
  - UNRESOLVED             (Assisted or turn limit reached)
  - ABANDONED              (Explicit student exit)
  - SAFETY_FALLBACK        (Verification / evidence failure)
```

### Exact Remediation Enums:
- **`RemediationLifecycleState`:** `"CREATED"`, `"REMEDIATING"`, `"AWAITING_TRANSFER"`, `"COMPLETED"`
- **`RemediationStatus`:** `"PROBING"`, `"GUIDING"`, `"CONFIRMING"`, `"RESOLVED"`, `"UNRESOLVED"`
- **`RemediationOutcome`:** `"TRANSFER_CONFIRMED"`, `"TRANSFER_NOT_CONFIRMED"`, `"UNRESOLVED"`, `"ABANDONED"`, `"SAFETY_FALLBACK"`
- **`SocraticStrategyType`:** `"GUIDED_RECALL"`, `"CONTRAST_CASE"`, `"STEPWISE_DECOMPOSITION"`, `"COUNTEREXAMPLE_PROBE"`

- **Resume Support:** A session can be resumed at any time via `GET /api/v1/remediation/session/{session_id}`.
- **Abandonment:** `POST /api/v1/remediation/session/{session_id}/abandon`.

---

## 12. 3D Anatomy Lab Flow (Renderer-Agnostic)
The backend does **not** mandate or execute client 3D rendering. The mobile developer may implement the rendering viewport using Three.js inside a WebView, native SceneKit (iOS), Filament (Android), or Flutter OpenGL.

1. **Get Manifest:** `GET /api/v1/anatomy/manifest` provides 8 renal structures mapped to HuBMAP CCF 3D Reference Objects.
2. **Start Session:** `POST /api/v1/anatomy/session/start` with `{"learner_id": "...", "learning_objective": "RENAL_BLOOD_FLOW_AND_HILUM"}`.
   - Returns session ID (`anat_...`) and initial lesson state (`INTRO`).
3. **Interact / Guide:** `POST /api/v1/anatomy/session/{session_id}/interact`
   - Client sends student action (e.g. `selected_structure_id: "renal_vein_left"`).
   - Server returns structured `scene_actions` using exact `AnatomyActionType` values:
     - `{"action": "HIGHLIGHT_STRUCTURE", "structure_id": "renal_vein_left"}`
     - `{"action": "SET_STRUCTURE_OPACITY", "opacity": 0.2, "duration_ms": 300}`
4. **Challenge:** `POST /api/v1/anatomy/session/{session_id}/challenge`
   - Target structure: `renal_artery_left`.
   - Client submits user selection: `{"selected_structure_id": "renal_artery_left"}`.
   - Server deterministically evaluates correctness and returns `ChallengeResult` (`CORRECT` / `INCORRECT`).

### Exact 3D Anatomy Enums:
- **`AnatomyActionType`:** `"FOCUS_STRUCTURE"`, `"HIGHLIGHT_STRUCTURE"`, `"ISOLATE_STRUCTURE"`, `"SHOW_STRUCTURE"`, `"HIDE_STRUCTURE"`, `"SHOW_RELATION"`, `"SET_STRUCTURE_OPACITY"`, `"RESET_SCENE"`
- **`LessonState`:** `"INTRO"`, `"GUIDED_VESSELS"`, `"GUIDED_IDENTIFICATION"`, `"CHALLENGE_READY"`, `"CHALLENGE_ACTIVE"`, `"COMPLETED"`
- **`ChallengeResult`:** `"PENDING"`, `"CORRECT"`, `"INCORRECT"`
- **`InteractionRequestType`:** `"IDENTIFY_STRUCTURE"`, `"EXPLORE_SCENE"`

---

## 13. Unified Learner Progress
- **Endpoint:** `GET /api/v1/learner/progress` (or compatibility alias `GET /api/v1/progress`).
- **Characteristics:** **Read-Only Dashboard Projection**.
- Combines live metrics across:
  - `university`: total attempted, accuracy, topic breakdowns.
  - `plab`: attempted, overall accuracy, governance content policy.
  - `adaptive`: total recorded events, weak topics count, top recommendation.
  - `anatomy`: completed challenges, accuracy, objectives mastered.
  - `summary`: cross-module unified mastery index.

---

## 14. Request Examples (Framework-Neutral `curl`)

### University Answer Submission:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/university/answer \
  -H "Content-Type: application/json" \
  -H "X-User-Id: learner_dev_001" \
  -d '{
    "question_id": "UNI-RENAL-001",
    "selected_option": "B",
    "idempotency_key": "idemp-uni-req-001"
  }'
```

### Tutor Socratic Chat:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/tutor/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: learner_dev_001" \
  -d '{
    "query": "What triggers renin secretion from the juxtaglomerular apparatus?",
    "topic": "RAAS mechanisms",
    "mode": "auto"
  }'
```

### Anatomy Challenge Submission:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/anatomy/session/anat_sample_01/challenge \
  -H "Content-Type: application/json" \
  -H "X-User-Id: learner_dev_001" \
  -d '{
    "learner_id": "learner_dev_001",
    "selected_structure_id": "renal_artery_left"
  }'
```

---

## 15. Response Examples

### University Answer Response:
```json
{
  "question_id": "UNI-RENAL-001",
  "selected_option": "B",
  "is_correct": false,
  "attempt_id": "att-4f1a8c9b2e",
  "subject": "Renal physiology",
  "topic": "RAAS mechanisms",
  "explanation": "Renin converts angiotensinogen to angiotensin I; ACE converts angiotensin I to angiotensin II.",
  "learning_feedback": "Review the enzymatic cascade order of the RAAS pathway."
}
```

### Unified Progress Response:
```json
{
  "learner_id": "learner_dev_001",
  "university": {
    "track": "university",
    "attempted": 1,
    "correct": 0,
    "accuracy": 0.0
  },
  "plab": {
    "total_attempts": 0,
    "overall_accuracy": 0.0,
    "content_policy": "GOLDEN_ONLY"
  },
  "adaptive": {
    "total_attempts": 1,
    "correct_attempts": 0,
    "overall_accuracy": 0.0,
    "weak_topics_count": 1
  },
  "anatomy": {
    "sessions_count": 1,
    "challenges_completed": 1,
    "challenge_accuracy": 1.0
  },
  "summary": {
    "total_activities": 3,
    "learning_status": "ACTIVE"
  }
}
```

---

## 16. Authoritative Error Matrix

| HTTP Status | Error Code / Detail | Meaning | Mobile UX Action | Retry Safe? | User Msg Safe? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `401 Unauthorized` | `USER_ID_REQUIRED` ("X-User-Id header is required.") | Missing learner identity on canonical endpoints (`resolve_learner_id(required=True)`) | Ensure `X-User-Id` is attached in HTTP headers before dispatching | No | Yes ("Please select or sign into a profile.") |
| `400 Bad Request` | `learner_id must not be empty` | Missing identity in 3D Anatomy request body and header | Supply `learner_id` in request body or header | No | Yes ("Please select or sign into a profile.") |
| `403 Forbidden` | `QUESTION_NOT_AVAILABLE` ("Question is not approved for student use.") | Attempted evaluation on unpromoted PLAB question in strict mode | Block question presentation; guide student to approved items | No | Yes ("This clinical question is awaiting clinician promotion.") |
| `403 Forbidden` | `Session does not belong to the requesting user` / `SESSION_ACCESS_FORBIDDEN` | Cross-learner session access attempt | Invalidate local cached session ID; return to list | No | Yes ("You do not have access to this session.") |
| `403 Forbidden` | `Phase 3 synthetic demo cohorts are disabled...` | Attempted access to educator cohort analytics | Do not render educator analytics in student app | No | Yes ("Educator analytics require educator authorization.") |
| `404 Not Found` | `Remediation session '...' not found` / `Question not found` | Invalid or expired session ID or nonexistent question ID | Clear stale session state and offer new diagnostic | No | Yes ("Learning session not found or expired.") |
| `409 Conflict` | `IDEMPOTENCY_CONFLICT` / `This attempt was already submitted with another answer.` | Reusing idempotency key with conflicting answers or payload | Do not resubmit with same key; fetch state with GET or use new key | No | Yes ("A submission with this request key was already recorded.") |
| `422 Unprocess.` | `Field required / validation error` | Malformed JSON, invalid enum (e.g. option not A-E), or missing FastAPI header dependency | Validate fields locally before submission | No | Yes ("Invalid input format.") |
| `422 Unprocess.` | `UNSUPPORTED_ANATOMY_REQUEST` | Requested structure not in 3D ontology | Prompt learner to select supported renal anatomy | No | Yes ("This structure is outside the current 3D lab module.") |
| `503 Serv. Unavail`| `PLAB_CONTENT_UNAVAILABLE` ("PLAB data integrity validation failed...") | Active production corpus unavailable or checksum mismatch | Retry after backoff; platform self-checks integrity | Yes | Yes ("Clinical exam content is temporarily unavailable.") |
| `503 Serv. Unavail`| `Socratic remediation engine is currently disabled...` | Feature flag disabled on backend | Hide or disable remediation CTA in UI | Yes | Yes ("This module is temporarily unavailable for maintenance.") |
| `503 Serv. Unavail`| `MedicalPlab 3D Anatomy Engine is currently disabled...` | Feature flag disabled on backend | Hide or disable 3D anatomy lab tab | Yes | Yes ("3D Anatomy Lab is currently offline.") |
| `503 Serv. Unavail`| `CLINICAL_AI_NOT_CONFIGURED` | Legacy clinical reasoning endpoint called | Do not invoke `/clinical/reason`; use `/tutor/chat` | No | Yes ("Clinical reasoning service unavailable.") |

---

## 17. Idempotency & Mobile Retry Matrix

| Operation | Idempotency Key Location | Mechanism | Retry Safe? | Duplicate Behavior | Conflict Behavior |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `POST /university/answer` | Request JSON: `idempotency_key` | Server attempt deduplication | **YES** | Returns cached evaluation attempt without re-scoring | `HTTP 409`: Rejects submission if key reused with differing answer |
| `POST /plab/evaluate` | Request JSON: `idempotency_key` | Pilot service attempt registry | **YES** | Returns cached evaluation attempt and feedback | `HTTP 409 IDEMPOTENCY_CONFLICT`: Rejects duplicate key with conflicting answer |
| `POST /remediation/start` | Request JSON: `idempotency_key` | Controller session registry | **YES** | Returns existing session without creating duplicates | Reuses existing active session for attempt |
| `POST /remediation/turn` | Request JSON: `idempotency_key` | Turn history deduplication | **YES** | Returns existing turn response | Prevents duplicate dialogue advancement |
| `POST /remediation/transfer` | Request JSON: `idempotency_key` | Assessment locking | **YES** | Returns cached transfer outcome | `HTTP 409`: Rejects conflicting transfer payload |
| `POST /remediation/abandon` | Path parameter: `session_id` | State transition guard | **YES** | Re-asserts `ABANDONED` status | Idempotent terminal transition |
| `POST /anatomy/session/start` | Parameter: `learner_id` | Session repository | **YES** | Creates or resumes session | Safe lifecycle initiation |
| `POST /anatomy/challenge` | Parameter: `session_id` | Challenge evaluator | **YES** | Returns deterministic evaluation | Locks challenge state |

---

## 18. State Persistence & Resume Matrix

| Domain | State Classification | Survives App Restart? | Survives Backend Restart? | Resume Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **University Attempts** | `PERSISTENT` | Yes | Yes (SQLite/DB) | `GET /api/v1/university/progress` |
| **PLAB Attempts** | `PERSISTENT` | Yes | Yes (Pilot DB) | `GET /api/v1/plab/progress` |
| **Adaptive Mastery** | `DERIVED` | Yes (recomputed) | Yes (recomputed from authoritative module-owned persistence) | `GET /api/v1/adaptive/state` |
| **Remediation Sessions** | `SESSION_LIFECYCLE` | Yes | Yes (Controller DB) | `GET /api/v1/remediation/session/{id}` |
| **3D Anatomy Sessions** | `SESSION_LIFECYCLE` | Yes | Yes (Anatomy Repo) | `GET /api/v1/anatomy/session/{id}` |
| **Tutor Conversation** | `EPHEMERAL` (Client) | No (unless cached locally)| No | Client retains turn history; sends `query` |
| **Unified Progress** | `DERIVED` (Read-only) | Yes (recomputed) | Yes (recomputed from authoritative module-owned persistence) | `GET /api/v1/learner/progress` |

> [!NOTE]
> **Adaptive State Ownership:** Adaptive Mastery has no separate "Telemetry DB". The `UnifiedLearnerStateManager` recomputes mastery on demand from authoritative module-owned persistence (University SQLite `university_attempts`, PLAB pilot attempt registry, and 3D Anatomy repository sessions). Server restarts safely recompute state from these underlying stores without loss of learner evidence.
>
> **Offline Sync:** `OFFLINE_SYNC_SUPPORTED = NO`. The backend does not support offline queueing or conflict resolution. The mobile app must have an active network connection for scoring and tutor dialogue.

---

## 19. Backend Feature Flags & Configuration
The following environment variables govern backend behavior:
- `MEDICALPLAB_RUNTIME_MODE`: Set to `pilot` or `production` to activate strict fail-closed validation.
- `MEDICALPLAB_PLAB_PREVIEW_QA`: Set to `1` to enable candidate PLAB preview questions for QA/demo review.
- `MEDICALPLAB_PHASE_2B_ENABLED`: Set to `1` to enable Socratic remediation routes.
- `MEDICALPLAB_ANATOMY_3D_ENABLED`: Set to `1` to enable 3D Anatomy Lab endpoints.
- `ALLOWED_ORIGINS`: Comma-separated CORS origins (e.g. `http://localhost:3000`).

---

## 20. 10-Minute Mobile Smoke Test Checklist
Perform these 10 steps sequentially to verify your mobile app integration:
1. **Health Check:** `GET /health` -> confirms backend is healthy and in pilot/production mode.
2. **Readiness Check:** `GET /ready` -> confirms `engineering_ready: true`.
3. **University Subjects:** `GET /api/v1/university/subjects` -> confirms subject listing.
4. **University Question Delivery:** `GET /api/v1/university/question?...` -> confirms question stem and options without answer leak.
5. **University Answer Submission:** `POST /api/v1/university/answer` -> submit option `B` with idempotency key; receive correctness and feedback.
6. **Adaptive State Check:** `GET /api/v1/adaptive/state` -> confirms learner telemetry recorded the attempt.
7. **Grounded Tutor Query:** `POST /api/v1/tutor/chat` -> ask a renal physiology question; confirm citations and message return.
8. **3D Anatomy Manifest & Session:** `GET /api/v1/anatomy/manifest` followed by `POST /api/v1/anatomy/session/start` -> confirm session ID returned.
9. **3D Anatomy Challenge:** `POST /api/v1/anatomy/session/{id}/challenge` with `selected_structure_id: "renal_artery_left"` -> confirms deterministic correct evaluation.
10. **Unified Progress Projection:** `GET /api/v1/learner/progress` -> confirms progress aggregated across University, Adaptive, and Anatomy tracks.

*(Optional)* **PLAB Preview QA Check:** With `MEDICALPLAB_PLAB_PREVIEW_QA=1`, execute `GET /api/v1/plab/questions` to verify 36 candidate questions with preview warnings.

---

## 21. Mobile Developer Integration Checklist
External mobile developers can tick off each item:
- [ ] Base URL configured via `MEDICALPLAB_API_BASE_URL` (no hardcoded localhost).
- [ ] `X-User-Id` header automatically attached to all authorized HTTP requests.
- [ ] University question flow implemented (fetch question, display options, submit answer, display feedback).
- [ ] PLAB governance contract respected: no preview items presented as approved clinical curriculum.
- [ ] Tutor RAG chat UI renders backend citations and respect `support_status`.
- [ ] Adaptive recommendation banner consumed and mapped to deep links in UI.
- [ ] Socratic remediation 3-turn state machine handled (`PROBE` -> `GUIDE` -> `CONSOLIDATE` -> Transfer).
- [ ] 3D Anatomy session IDs stored and structure scene actions dispatched to 3D renderer.
- [ ] Unified Progress dashboard rendered using single `GET /api/v1/learner/progress` read.
- [ ] HTTP 400/403/422/503 errors gracefully mapped to user-friendly alert banners.
- [ ] Network retries send identical `idempotency_key` to prevent duplicate attempts.
- [ ] Zero client-side scoring logic implemented (server remains sole source of truth).

---

## 22. Known Release Limitations
1. **Zero Native Mobile Code in Repo:** Native mobile applications (iOS/Android/Flutter/React Native) are developed in external consumer repositories (`REAL_NATIVE_MOBILE_SOURCE_IN_REPO = NO`).
2. **Identity Header Only:** Production token authentication (OAuth/JWT) must be provided by an upstream API gateway (`MOBILE_PRODUCTION_AUTH_READY = NO`).
3. **PLAB Golden Promotion Required:** PLAB curriculum is locked in `GOLDEN_ONLY` mode until clinicians formally approve questions (`PLAB_PUBLIC_RELEASE_READY = NO`, `PLAB_GOLDEN_PROMOTION_REQUIRED = YES`).
4. **No Offline Sync:** The client requires network connectivity for evaluation and tutor interaction (`OFFLINE_SYNC_SUPPORTED = NO`).
5. **Renderer Responsibility:** The 3D viewport implementation is client-owned; the backend delivers structured spatial coordinates and actions.
