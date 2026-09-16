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

| HTTP Status | Triggering Scenario | Backend Meaning | Mobile Client UX Action |
| :---: | :--- | :--- | :--- |
| **`400`** | Calling `/remediation/turn` after Turn 3 | Turn progression out of bounds ($>3$) | Disable turn input; navigate student to Transfer Assessment or Topic overview. |
| **`403`** | `X-User-Id` header mismatch on `/remediation/session/{id}` or `/attempt` | Requested resource belongs to a different learner ID | Clear cached session ID; prompt user to restart session with current device ID. |
| **`404`** | Requesting invalid subject, topic, or question ID | Resource does not exist in active educational content | Display "Content Not Found" toast and navigate back to Subjects list. |
| **`404`** | `GET /remediation/session/{id}` with unknown session ID | Remediation session does not exist or was evicted | Clear local active session pointer; return user to practice question. |
| **`404`** | `GET /remediation/session/{id}/transfer` on questions without transfer | Question does not have a paired held-out transfer item (e.g. `UNI-RENAL-003`) | Inform learner that transfer item is not available; mark session resolved/complete and return to topics. |
| **`409`** | Reusing `idempotency_key` with conflicting options or answers | Attempt or transfer was already submitted with a different payload | Display "Submission Conflict" toast; fetch latest state via `GET` without retrying POST. |
| **`422`** | Missing or empty `X-User-Id` on `/answer` or `/progress` | Header length $< 8$ or $> 120$ characters | Ensure mobile local storage initializes `uni-<uuid>` before issuing requests. |
| **`422`** | Calling `/remediation/start` for a **correct** answer | Remediation is strictly reserved for incorrect options/distractors | Prevent student from triggering remediation on correct answers; prompt for next question. |
| **`422`** | Calling `/remediation/session/{id}/transfer` before reaching `AWAITING_TRANSFER` | Dialogue turns 1-3 have not yet concluded | Block transfer navigation; keep student on current dialogue turn. |
| **`422`** | Submitting transfer answer without first calling `GET /transfer` | Transfer item has not yet been dispensed by server | Fetch transfer item via `GET /transfer` before displaying assessment UI. |
| **`422`** | Submitted transfer question ID does not match dispensed item | Client submitted answer for wrong question | Ensure client submits matching `question_id` received from `GET /transfer`. |
| **`500`** | Unexpected server-side failure in RAG or scoring engine | Internal server exception | Show generic retry banner: "Service temporarily unavailable. Please retry shortly." |
| **`503`** | `MEDICALPLAB_PHASE_2B_ENABLED` feature flag is disabled | Phase 2B remediation engine is turned off on server | Show notice: "Socratic remediation is currently unavailable in this environment." |

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
