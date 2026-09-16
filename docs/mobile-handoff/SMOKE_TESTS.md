# MedicalPlab Mobile Contract Smoke Test Guide

This document provides a set of `curl` commands demonstrating the complete 11-step mobile learning journey against a running MedicalPlab backend.

> **Developer Verification Notice:**
> The answer options shown below (e.g. Option B for distractor trigger, Option A for transfer verification) are synthetic fixtures for developer testing and contract validation only. Mobile runtime clients must never store, bundle, or rely on answer keys client-side. The backend remains strictly authoritative for scoring.

---

## 0. Prerequisites & Server Launch

Start the backend with the required Phase 2B remediation flag enabled:

```bash
# Bash / Linux / macOS
export MEDICALPLAB_PHASE_2B_ENABLED=true
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Windows PowerShell
$env:MEDICALPLAB_PHASE_2B_ENABLED = "true"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Set a consistent test learner ID in your shell:
```bash
LEARNER_ID="uni-test-mobile-001"
BASE_URL="http://127.0.0.1:8000"
```

---

## Step 1: Obtain a Question

Request a question from the `Renal physiology` subject, `RAAS mechanisms` topic:

```bash
curl -X GET "${BASE_URL}/api/v1/university/question?subject=Renal%20physiology&topic=RAAS%20mechanisms" \
  -H "X-User-Id: ${LEARNER_ID}"
```

**Expected Response (`200 OK`):**
Returns question `UNI-RENAL-001` with stem and options A, B, C, D. **Verify that `correct_answer` is not present.**

---

## Step 2: Submit Known Wrong Answer

Submit Option `B` (incorrect distractor: Angiotensin II):

```bash
curl -X POST "${BASE_URL}/api/v1/university/answer" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: ${LEARNER_ID}" \
  -d '{
    "question_id": "UNI-RENAL-001",
    "selected_option": "B",
    "idempotency_key": "att-smoke-key-001"
  }'
```

**Expected Response (`200 OK`):**
```json
{
  "question_id": "UNI-RENAL-001",
  "is_correct": false,
  "correct_answer": "A",
  "explanation": "Renin acts on angiotensinogen to form angiotensin I..."
}
```

---

## Step 3: Obtain Adaptive Recommendation

Fetch the next pedagogical action suggested by the Adaptive Decision Engine:

```bash
curl -X GET "${BASE_URL}/api/v1/adaptive/recommendation" \
  -H "X-User-Id: ${LEARNER_ID}"
```

**Expected Response (`200 OK`):**
```json
{
  "action": "ASK_GROUNDED_TUTOR",
  "topic": "RAAS mechanisms",
  "priority": "high",
  "target_question_id": "UNI-RENAL-001"
}
```

---

## Step 4: Start Socratic Remediation (Turn 1: Probe)

Initiate a 3-turn remediation session for the incorrect answer:

```bash
curl -X POST "${BASE_URL}/api/v1/remediation/start" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: ${LEARNER_ID}" \
  -d '{
    "question_id": "UNI-RENAL-001",
    "selected_option": "B",
    "attempt_id": "att-smoke-key-001",
    "idempotency_key": "rem-start-key-001"
  }'
```

**Expected Response (`200 OK`):**
Extract `session_id` (e.g. `REM-A1B2C3D4E5F6`).
- `turn_number`: `1`
- `lifecycle_state`: `"REMEDIATING"`
- `transfer_available`: `false`
- `socratic_probe`: Neural/evidence probe challenging the flawed premise.

---

## Step 5: Advance Turn 2 (Guide)

Submit the student's explanation for Turn 1 to receive a grounded mechanistic clue:

```bash
SESSION_ID="<REPLACE_WITH_SESSION_ID_FROM_STEP_4>"

curl -X POST "${BASE_URL}/api/v1/remediation/turn" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: ${LEARNER_ID}" \
  -d "{
    \"session_id\": \"${SESSION_ID}\",
    \"student_message\": \"I understand that macula densa cells sense sodium concentration.\",
    \"idempotency_key\": \"turn-2-key-001\"
  }"
```

**Expected Response (`200 OK`):**
- `turn_number`: `2`
- `lifecycle_state`: `"REMEDIATING"`

---

## Step 6: Advance Turn 3 (Consolidate & Reach AWAITING_TRANSFER)

Submit the student's Turn 2 explanation to complete the dialogue:

```bash
curl -X POST "${BASE_URL}/api/v1/remediation/turn" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: ${LEARNER_ID}" \
  -d "{
    \"session_id\": \"${SESSION_ID}\",
    \"student_message\": \"Juxtaglomerular cells secrete renin into the bloodstream to act upon circulating angiotensinogen.\",
    \"idempotency_key\": \"turn-3-key-001\"
  }"
```

**Expected Response (`200 OK`):**
- `turn_number`: `3`
- `lifecycle_state`: `"AWAITING_TRANSFER"`
- `transfer_available`: `true`

---

## Step 7: Retrieve Held-Out Transfer Question

Dispense the independent transfer item:

```bash
curl -X GET "${BASE_URL}/api/v1/remediation/session/${SESSION_ID}/transfer" \
  -H "X-User-Id: ${LEARNER_ID}"
```

**Expected Response (`200 OK`):**
- `question_id`: `"UNI-RENAL-001-T"`
- `stem`: *"In an investigation of renovascular regulation, an elevated plasma renin activity is observed..."*
- Options: `A`, `B`, `C`, `D`. **No answer keys or explanations leaked.**

---

## Step 8: Submit Transfer Answer

Submit Option `A` (Angiotensinogen) with `was_assisted: false`:

```bash
curl -X POST "${BASE_URL}/api/v1/remediation/session/${SESSION_ID}/transfer" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: ${LEARNER_ID}" \
  -d "{
    \"session_id\": \"${SESSION_ID}\",
    \"question_id\": \"UNI-RENAL-001-T\",
    \"selected_option\": \"A\",
    \"was_assisted\": false,
    \"idempotency_key\": \"trans-submit-key-001\"
  }"
```

**Expected Response (`200 OK`):**
- `outcome`: `"TRANSFER_CONFIRMED"`
- `is_correct`: `true`
- `timeline.status`: `"COMPLETED"`

---

## Step 9: Verify Updated Learner State

Query the updated learner profile:

```bash
curl -X GET "${BASE_URL}/api/v1/adaptive/state" \
  -H "X-User-Id: ${LEARNER_ID}"
```

**Expected Response (`200 OK`):**
Returns updated `total_attempts`, accuracy, and mastery records.

---

## Step 10: Inspect / Resume Completed Session

Query the session state via `GET`:

```bash
curl -X GET "${BASE_URL}/api/v1/remediation/session/${SESSION_ID}" \
  -H "X-User-Id: ${LEARNER_ID}"
```

**Expected Response (`200 OK`):**
- `lifecycle_state`: `"COMPLETED"`
- `outcome`: `"TRANSFER_CONFIRMED"`
- `turns`: Array of 3 turn records containing tutor messages and student inputs.

---

## Step 11: Automated Python Smoke Test

To run this entire flow programmatically with automated assertions, run the test script:

```bash
python scratch/test_e2e_mobile_handoff.py
```
