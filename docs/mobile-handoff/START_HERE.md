# MedicalPlab — 10-Minute Mobile Developer Integration Guide
**Target Platforms:** iOS (Swift/SwiftUI), Android (Kotlin/Compose), React Native / Expo, Flutter  
**API Specification:** OpenAPI 3.1.0 ([`openapi.json`](./openapi.json))  
**Postman Suite:** [`MedicalPlab.mobile.postman_collection.json`](./MedicalPlab.mobile.postman_collection.json)  
**Authoritative Backend Contract:** Frozen Baseline (`v1.1.0`)

---

## 1. Quick Architecture Overview

MedicalPlab provides a clean, stateless REST API designed for mobile educational clients. Mobile clients handle UI/UX, local animations, and user interaction, while the backend maintains deterministic scoring, adaptive state, RAG verification, and learning telemetry.

```
[Mobile App (Flutter / React Native / Native)]
      │
      ├── Header: X-User-Id: <learner_id>  (Pilot/Demo identity partitioning)
      │
      ├── 1. Preclinical MCQs      ──► GET  /api/v1/university/question
      │                                POST /api/v1/university/answer
      │
      ├── 2. Adaptive Policy       ──► GET  /api/v1/adaptive/recommendation
      │                                GET  /api/v1/adaptive/state
      │
      ├── 3. Socratic Remediation  ──► POST /api/v1/remediation/start
      │                                POST /api/v1/remediation/turn
      │
      ├── 4. Held-Out Transfer     ──► GET  /api/v1/remediation/session/{id}/transfer
      │                                POST /api/v1/remediation/session/{id}/transfer
      │
      ├── 5. Grounded AI Tutor     ──► POST /api/v1/tutor/chat
      │
      ├── 6. 3D Anatomy Lab        ──► POST /api/v1/anatomy/session/start
      │                                POST /api/v1/anatomy/session/{id}/challenge
      │
      └── 7. Unified Progress      ──► GET  /api/v1/learner/progress
```

---

## 2. Base URLs & Network Setup

Configure your mobile HTTP client with the appropriate base URL:

| Environment | Base URL | Notes |
| :--- | :--- | :--- |
| **Local Dev (iOS Simulator / Desktop)** | `http://127.0.0.1:8000` | Run backend via `python -m uvicorn production_main:app --port 8000` |
| **Local Dev (Android Emulator)** | `http://10.0.2.2:8000` | Android loopback alias for host machine `127.0.0.1` |
| **Physical Device (LAN)** | `http://<YOUR_LOCAL_IP>:8000` | Ensure firewall allows inbound on port 8000 |
| **Staging / Remote** | Configured via environment | See [Staging Certification](./STAGING_CERTIFICATION.md) |

---

## 3. Learner Identity Protocol (`X-User-Id`)

Every learner-scoped request requires an `X-User-Id` header identifying the student session.

```http
X-User-Id: learner_mobile_001
```

> [!IMPORTANT]
> **Pilot Identity Partitioning Contract:** `X-User-Id` partitions learner progress, mastery state, and remediation sessions for development and pilot testing. It is **NOT** cryptographic production authentication (`MOBILE_PRODUCTION_AUTH_READY = NO`). Production JWT / OAuth2 authentication will be introduced in institutional deployments.

---

## 4. System Verification (Step 0)

Before executing learner flows, verify server health and contract metadata:

```bash
# 1. Health check
curl -X GET http://127.0.0.1:8000/health

# 2. Readiness & runtime configuration check
curl -X GET http://127.0.0.1:8000/ready

# 3. Contract version and feature flags
curl -X GET http://127.0.0.1:8000/api/v1/version
```

**Expected `/ready` response:**
```json
{
  "status": "ready",
  "runtime_mode": "pilot",
  "plab_preview_qa": true,
  "data_manifest": "verified"
}
```

---

## 5. The Core 7-Step Mobile Learner Journey

### Step 1: Preclinical Question & Answer
Fetch curriculum topics and request an active preclinical question:

```bash
# Get subjects & topics:
curl -H "X-User-Id: learner_01" http://127.0.0.1:8000/api/v1/university/subjects
curl -H "X-User-Id: learner_01" "http://127.0.0.1:8000/api/v1/university/topics?subject=Renal%20physiology"

# Fetch question (Notice: correct answer is never leaked in the question payload):
curl -H "X-User-Id: learner_01" "http://127.0.0.1:8000/api/v1/university/question?subject=Renal%20physiology&topic=RAAS%20mechanisms"
```

Submit student's answer with an `idempotency_key`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/university/answer \
  -H "Content-Type: application/json" \
  -H "X-User-Id: learner_01" \
  -d '{
    "question_id": "UNI-RENAL-001",
    "selected_option": "B",
    "idempotency_key": "att-idemp-001"
  }'
```

**Response (`200 OK`):**
```json
{
  "is_correct": false,
  "explanation": "Active renin acts specifically on angiotensinogen...",
  "distractor_signal": "SUBSTRATE_VS_PRODUCT_CONFUSION",
  "recommended_action": "REMEDIATE"
}
```

---

### Step 2: Adaptive Recommendations
Inspect the learner's updated mastery state and next recommended action:

```bash
curl -H "X-User-Id: learner_01" http://127.0.0.1:8000/api/v1/adaptive/recommendation
curl -H "X-User-Id: learner_01" http://127.0.0.1:8000/api/v1/adaptive/state
```

---

### Step 3: Socratic Remediation (Bounded 3-Turn Scaffolding)
Initiate dialogue when an educational distractor signal is triggered:

```bash
# Start remediation session (Turn 1: Preceptor Probe):
curl -X POST http://127.0.0.1:8000/api/v1/remediation/start \
  -H "Content-Type: application/json" \
  -H "X-User-Id: learner_01" \
  -d '{
    "learner_id": "learner_01",
    "question_id": "UNI-RENAL-001",
    "trigger_distractor": "B"
  }'
```

**Response:** Returns `session_id` (e.g. `REM-01`), preceptor prompt ("What does active renin cleave directly?"), and `turn: 1`.

Advance the dialogue (Turn 2 Guide &rarr; Turn 3 Consolidate):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/remediation/turn \
  -H "Content-Type: application/json" \
  -H "X-User-Id: learner_01" \
  -d '{
    "session_id": "REM-01",
    "learner_id": "learner_01",
    "learner_message": "Renin acts on angiotensinogen produced by the liver."
  }'
```

---

### Step 4: Independent Held-Out Transfer Item
Remediation scaffolding does NOT update learner state alone. The learner must independently pass an unseen transfer problem:

```bash
# 1. Fetch held-out transfer question:
curl -H "X-User-Id: learner_01" http://127.0.0.1:8000/api/v1/remediation/session/REM-01/transfer

# 2. Submit transfer answer:
curl -X POST http://127.0.0.1:8000/api/v1/remediation/session/REM-01/transfer \
  -H "Content-Type: application/json" \
  -H "X-User-Id: learner_01" \
  -d '{
    "session_id": "REM-01",
    "learner_id": "learner_01",
    "selected_option": "A"
  }'
```

---

### Step 5: Evidence-Grounded AI Tutor
Student submits free-form medical inquiries verified against open-access medical literature:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/tutor/chat \
  -H "Content-Type: application/json" \
  -H "X-User-Id: learner_01" \
  -d '{
    "query": "Explain the exact proteolytic action of renin on angiotensinogen.",
    "topic": "RAAS mechanisms",
    "mode": "mechanistic_explanation"
  }'
```

**Response features:**
- Substantive claims are strictly verified against retrieved PMC chunks.
- Citations include PMCID, title, quote, and license provenance (`cit.license`).
- If evidence is unsupported, the system fails closed with `SAFE_FALLBACK` (zero ungrounded claims).

---

### Step 6: 3D Anatomy Lab
Integrate the 3D anatomical viewer using licensed HuBMAP CCF models:

```bash
# 1. Get anatomical manifest & asset URLs:
curl http://127.0.0.1:8000/api/v1/anatomy/manifest

# 2. Start anatomy session:
curl -X POST http://127.0.0.1:8000/api/v1/anatomy/session/start \
  -H "Content-Type: application/json" \
  -H "X-User-Id: learner_01" \
  -d '{
    "learner_id": "learner_01",
    "learning_objective": "RENAL_BLOOD_FLOW_AND_HILUM"
  }'

# 3. Submit independent 3D structure identification challenge:
curl -X POST http://127.0.0.1:8000/api/v1/anatomy/session/ANAT-01/challenge \
  -H "Content-Type: application/json" \
  -H "X-User-Id: learner_01" \
  -d '{
    "learner_id": "learner_01",
    "selected_structure_id": "renal_artery_left"
  }'
```

---

### Step 7: Unified Learner Progress
Display the student's unified longitudinal competence dashboard:

```bash
curl -H "X-User-Id: learner_01" http://127.0.0.1:8000/api/v1/learner/progress
```

**Metrics included:**
- `total_attempts`, `accuracy_rate`
- `remediation_sessions_completed`
- `transfer_problems_passed`
- `anatomy_challenges_completed`
- `topic_mastery` dictionary

---

## 6. Error Handling & HTTP Status Codes

MedicalPlab adheres to standard RFC 7807 problem details:

| HTTP Status | Meaning | Typical Trigger | Client Action |
| :--- | :--- | :--- | :--- |
| `400 Bad Request` | Missing/Invalid payload | Missing `selected_option`, empty `learner_id` | Validate input client-side before sending |
| `403 Forbidden` | Ownership mismatch | Requesting session owned by different `learner_id` | Clear stale session ID from local storage |
| `404 Not Found` | Entity not found | Unknown `question_id` or expired `session_id` | Refresh question or start new remediation |
| `422 Unprocessable`| Pydantic schema error | Type mismatch in JSON body | Check schema against [`openapi.json`](./openapi.json) |
| `503 Service Unavail`| Feature disabled | Anatomy disabled or strict Golden PLAB empty | Display safe fallback notice |

---

## 7. Clinical Governance & Content Safety

1. **Preclinical Production Questions (6 active items):** Verified active curriculum (`UNI-RENAL-001` to `006`).
2. **PLAB Candidate Bank (36 preview items):** Only accessible when `MEDICALPLAB_PLAB_PREVIEW_QA=1`. These are candidate items staged for clinician review.
3. **Fail-Closed Golden Standard:** In production mode (`MEDICALPLAB_PLAB_PREVIEW_QA=0`), `GET /api/v1/plab/questions` returns `0 items`.
4. **Mobile Client Rule:** Never display candidate questions as released medical exam items.

---

## 8. Development Resources

- [Flutter & React Native Code Examples](./CLIENT_EXAMPLES.md)
- [Mobile Developer Integration Checklist](./INTEGRATION_CHECKLIST.md)
- [Comprehensive API Contract Matrix](./API_CONTRACT.md)
- [Full Technical Handoff Document](./MOBILE_DEVELOPER_HANDOFF.md)
- [Automated Smoke Tests](./SMOKE_TESTS.md)
