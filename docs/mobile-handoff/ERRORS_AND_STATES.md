# MedicalPlab Error Matrix, States & Session Recovery

This document details the HTTP error codes, lifecycle state machine enums, terminal safety fallback rules, and session resume mechanics.

---

## 1. Mobile Error Matrix

Every error response from the backend follows standard FastAPI JSON format:
```json
{
  "detail": "Descriptive human-readable error explanation."
}
```

| HTTP Status | Triggering Scenario | Backend Meaning | Mobile Client UX Action | Retry Safe? |
| :---: | :--- | :--- | :--- | :---: |
| **`401`** | Omitted or empty `X-User-Id` on canonical learner endpoints | `USER_ID_REQUIRED`: `resolve_learner_id(required=True)` failed closed | Attach valid `X-User-Id` header before issuing request. | **No** |
| **`400`** | Missing `learner_id` on 3D Anatomy session start or turn $> 3$ | Request parameter missing or turn progression out of bounds | Supply `learner_id` in header/body or advance to transfer. | **No** |
| **`403`** | Evaluating unpromoted PLAB question in strict production mode | `QUESTION_NOT_AVAILABLE`: Question not approved for student release | Block question presentation; guide learner to promoted questions. | **No** |
| **`403`** | `X-User-Id` mismatch on `/remediation/session/{id}` or `/attempt` | `SESSION_ACCESS_FORBIDDEN`: Resource belongs to a different learner ID | Clear cached session ID; restart session with current device ID. | **No** |
| **`403`** | Attempted access to educator cohort analytics (`/reasoning-gaps`) | Educator role required ($N \ge 3$ privacy suppression enforced) | Hide educator analytics tabs in mobile student application. | **No** |
| **`404`** | Requesting invalid subject, topic, question ID, or expired session | Resource does not exist in active content or session expired | Display "Content Not Found" toast and navigate back to list. | **No** |
| **`409`** | Reusing `idempotency_key` with conflicting options or payload | `IDEMPOTENCY_CONFLICT`: Key was already submitted with different data | Display "Submission Conflict" toast; fetch latest state with GET. | **No** |
| **`422`** | Missing required JSON fields, invalid enums, or University header | Validation error (e.g. option not A-E, or missing required field) | Validate request schema and fields locally before submission. | **No** |
| **`422`** | `UNSUPPORTED_ANATOMY_REQUEST` or invalid remediation phase | Structure not in 3D ontology or action taken in wrong state | Restrict interactions to active supported ontology and state. | **No** |
| **`500`** | Unexpected server-side internal exception | Internal server processing failure | Show retry banner: "Service temporarily unavailable. Please retry." | **Yes** |
| **`503`** | Active PLAB production corpus unavailable or checksum mismatch | `PLAB_CONTENT_UNAVAILABLE`: Data integrity verification failed | Retry after exponential backoff; backend self-checks integrity. | **Yes** |
| **`503`** | `MEDICALPLAB_PHASE_2B_ENABLED=0` or `ANATOMY_3D_ENABLED=0` | Corresponding engine is disabled by feature flag on backend | Hide or disable corresponding CTA / tab in mobile UI. | **Yes** |

---

## 2. Remediation Lifecycle States & Enums

### Lifecycle State (`RemediationLifecycleState`)
Tracks the overarching state machine phase of the session:

```typescript
export enum RemediationLifecycleState {
  CREATED = "CREATED",                     // Session initialized from original question attempt
  REMEDIATING = "REMEDIATING",             // In-progress 3-turn Socratic dialogue (Turns 1, 2, or 3)
  AWAITING_TRANSFER = "AWAITING_TRANSFER", // Dialogue concluded; awaiting independent transfer assessment
  COMPLETED = "COMPLETED",                 // Concluded with terminal outcome
}
```

### Terminal Outcome (`RemediationOutcome`)
Set when `lifecycle_state === "COMPLETED"`:

```typescript
export enum RemediationOutcome {
  TRANSFER_CONFIRMED = "TRANSFER_CONFIRMED",         // Correct on held-out transfer item without assistance
  TRANSFER_NOT_CONFIRMED = "TRANSFER_NOT_CONFIRMED", // Incorrect on held-out transfer item
  UNRESOLVED = "UNRESOLVED",                         // Assisted transfer, unavailable transfer item, or turn limit reached
  ABANDONED = "ABANDONED",                           // Explicit student exit or timeout
  SAFETY_FALLBACK = "SAFETY_FALLBACK",               // Pipeline verification or retrieval failure
}
```

### Transitional Dialogue Status (`RemediationStatus`)
Used for conversational UI status badges:
- `PROBING`: Turn 1 (Challenging flawed premise neutrally)
- `GUIDING`: Turn 2 (Providing grounded mechanistic clue)
- `CONFIRMING`: Turn 3 (Synthesizing and checking readiness)
- `RESOLVED`: Backward-compatible resolution indicator
- `UNRESOLVED`: Terminal non-resolution

---

## 3. Terminal SAFETY_FALLBACK Contract

The backend incorporates fail-closed safety. If an underlying AI model hallucinates, fails clinical claim verification, or evidence retrieval is compromised, the server initiates an unrecoverable terminal safety fallback:

### Exact Fallback Payload Signature:
```json
{
  "session_id": "REM-01F0210586E8",
  "turn_number": 1,
  "max_turns": 3,
  "is_complete": true,
  "lifecycle_state": "COMPLETED",
  "outcome": "SAFETY_FALLBACK",
  "remediation_status": "UNRESOLVED",
  "timeline": {
    "guided_practice": "Remediation concluded due to safety fallback",
    "transfer_result": "Remediation stopped safely; no transfer assessment performed.",
    "status": "SAFETY_FALLBACK"
  },
  "tutor_message": "I couldn't verify enough evidence to give a fully grounded explanation right now. Let's work through this together using what you already know.",
  "socratic_probe": null,
  "citations": [],
  "transfer_available": false
}
```

### Strict Mobile Client Obligations:
1. **Never attempt further turns:** Do not allow the user to send messages once `outcome === "SAFETY_FALLBACK"`.
2. **Hide transfer controls:** Ensure the "Take Transfer Assessment" button is completely hidden (`transfer_available: false`).
3. **Display Canonical Message:** Show the explanation text provided in `tutor_message`.
4. **Offer Safe Exit:** Provide a navigation button to return to the topics or subjects menu.

---

## 4. Session Resume & App Restart Mechanics

Mobile applications must reliably resume sessions across app backgrounding, OS termination, network reconnection, and device restarts.

### Authoritative Resume Protocol:
1. **Locally Store Active Pointer:**
   - Whenever `POST /api/v1/remediation/start` succeeds, store `active_remediation_session_id` in local device storage.
2. **On App Resume / Foregrounding:**
   - If an `active_remediation_session_id` exists, call:
     ```http
     GET /api/v1/remediation/session/{session_id}
     X-User-Id: uni-e2a48b39-...
     ```
3. **Inspect Server State:**
   - **If `is_complete === false` and `lifecycle_state === "REMEDIATING"`:**
     - Restore chat history from `turns` array.
     - Restore current turn prompt from the last turn in `turns`.
     - Enable the message input box.
   - **If `is_complete === false` and `lifecycle_state === "AWAITING_TRANSFER"`:**
     - Restore chat history in read-only mode.
     - Check if `transfer_attempt` exists:
       - If null: Fetch transfer item via `GET /remediation/session/{id}/transfer` and present question.
   - **If `is_complete === true` (Completed, Abandoned, or Safety Fallback):**
     - Display the completed summary card with the recorded `outcome`.
     - Clear `active_remediation_session_id` from local device storage.

### Idempotency & Zero Duplicate Learning Effects
- The mobile app must generate a unique UUID for `idempotency_key` on each POST.
- If an in-flight network request times out or disconnects:
  - The client may safely resend the identical POST payload with the **same** `idempotency_key`.
  - The backend returns the previously computed turn or transfer score without creating duplicate database rows or inflating learning metrics.
  - Submitting a **different** answer or message with the same idempotency key is rejected with `HTTP 409 Conflict`.

---

## 5. 3D Anatomy States & Structured Enums

The 3D Anatomy service delivers deterministic scene actions and structured evaluation states:

### Scene Action Type (`AnatomyActionType`)
Dispatched by server in `POST /anatomy/session/{id}/interact`:
```typescript
export enum AnatomyActionType {
  FOCUS_STRUCTURE = "FOCUS_STRUCTURE",           // Camera focus on anatomy item
  HIGHLIGHT_STRUCTURE = "HIGHLIGHT_STRUCTURE",   // Visual highlight/outline
  ISOLATE_STRUCTURE = "ISOLATE_STRUCTURE",       // Isolate item; hide rest
  SHOW_STRUCTURE = "SHOW_STRUCTURE",             // Make structure visible
  HIDE_STRUCTURE = "HIDE_STRUCTURE",             // Hide structure
  SHOW_RELATION = "SHOW_RELATION",               // Visual link between structures
  SET_STRUCTURE_OPACITY = "SET_STRUCTURE_OPACITY", // Set transparency (0.0 to 1.0)
  RESET_SCENE = "RESET_SCENE",                   // Restore baseline 3D scene
}
```

### Lesson State (`LessonState`)
State machine progression of the 3D guided lesson:
```typescript
export enum LessonState {
  INTRO = "INTRO",
  GUIDED_VESSELS = "GUIDED_VESSELS",
  GUIDED_IDENTIFICATION = "GUIDED_IDENTIFICATION",
  CHALLENGE_READY = "CHALLENGE_READY",
  CHALLENGE_ACTIVE = "CHALLENGE_ACTIVE",
  COMPLETED = "COMPLETED",
}
```

### Challenge Evaluation Result (`ChallengeResult`)
Deterministic pin test assessment outcome returned by `POST /anatomy/session/{id}/challenge`:
```typescript
export enum ChallengeResult {
  PENDING = "PENDING",
  CORRECT = "CORRECT",
  INCORRECT = "INCORRECT",
}
```

### Interaction Request Type (`InteractionRequestType`)
AI guidance prompt category:
- `IDENTIFY_STRUCTURE`: Prompt requesting student to locate/tap an anatomical structure.
- `EXPLORE_SCENE`: Open exploratory rotation/inspection prompt.
