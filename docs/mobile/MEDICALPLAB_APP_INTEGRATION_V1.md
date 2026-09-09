# MedicalPlab Application & Mobile Integration Handoff (v1.0.0)

This document provides the authoritative, production-grade integration contract for the mobile/application engineering team. Engineers integrating client applications (iOS, Android, React Native, or Flutter) do not need to read backend code. All endpoints, schemas, headers, error envelopes, and flows are specified here.

---

## 1. Network & Environment Configuration

| Environment | Base URL | Content Gate | Notes |
| :--- | :--- | :--- | :--- |
| **Local Development** | `http://localhost:8000` | Golden only (or Preview QA if enabled) | Default backend port |
| **Internal QA / Staging** | `https://staging-api.medicalplab.com` | Explicit `MEDICALPLAB_PLAB_PREVIEW_QA=true` | Shows QA warning banners |
| **Production Pilot** | `https://api.medicalplab.com` | Strict Golden Only | Fails closed; 0 unapproved questions served |

---

## 2. Authentication & Headers

| Header | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `Content-Type` | String | Yes (`application/json`) | For all POST/PATCH requests |
| `X-User-Id` | String | Yes (for student actions) | Unique student/device identifier (e.g. `STU-9921`) |
| `X-Idempotency-Key` | String | Yes (for answer evaluation) | UUIDv4 per submission to guarantee idempotency |
| `Authorization` | String | Only for Clinician Review | `Bearer <token>` for review/governance endpoints |

---

## 3. Standard API Error Envelope

All 4xx and 5xx responses conform to this uniform JSON envelope:

```json
{
  "detail": {
    "code": "ERROR_CODE_STRING",
    "message": "Human-readable explanation of why the action was rejected."
  }
}
```

### Standard Error Codes

| HTTP Status | Code | Meaning | Client Handling |
| :--- | :--- | :--- | :--- |
| `401` | `USER_ID_REQUIRED` | Missing `X-User-Id` header | Attach authenticated student ID |
| `403` | `QUESTION_NOT_AVAILABLE` | Question pending clinical review / unapproved in production | Inform user question is not yet published |
| `404` | `QUESTION_NOT_FOUND` | Question ID does not exist | Check question ID |
| `409` | `IDEMPOTENCY_CONFLICT` | Idempotency key reused with different answer | Generate a new key for new attempts |
| `422` | `INVALID_OPTION` | Selected option not in `["A", "B", "C", "D", "E"]` | Validate input on client before submit |
| `422` | `UNSUPPORTED_ANATOMY_REQUEST` | Structure not in verified 11-structure cardiovascular ontology | Render friendly anatomy scope notice |
| `503` | `CLINICAL_AI_NOT_CONFIGURED` | Live clinical LLM reasoning backend not active | Fail closed; do not synthesize hallucination |

---

## 4. Endpoints & Schemas

### 4.1 PLAB SBA Question Experience

#### A. List Available Questions
- **Method:** `GET`
- **Path:** `/api/v1/plab/questions`
- **Behavior:**
  - In normal production with 0 Golden questions: returns `{"items": [], "count": 0, "content_policy": "GOLDEN_ONLY"}`.
  - In internal QA / demo (`MEDICALPLAB_PLAB_PREVIEW_QA=true`): returns verified candidate questions with `content_policy: "PREVIEW_QA_EXPLICIT"`.
- **Pre-Answer Security Guarantee:** Pre-answer DTO **never** leaks `correct_answer`, `isCorrect`, `explanation`, or reviewer internals.

**Response Example (200 OK):**
```json
{
  "items": [
    {
      "question_id": "PLAB-CARD-0001",
      "stem": "A 58-year-old male presents to the Emergency Department with severe central crushing chest pain radiating to his left jaw...",
      "options": [
        {"id": "A", "text": "Emergency percutaneous coronary intervention"},
        {"id": "B", "text": "Intravenous thrombolysis with alteplase"},
        {"id": "C", "text": "Oral bisoprolol and outpatient follow-up"},
        {"id": "D", "text": "Sublingual glyceryl trinitrate and discharge"},
        {"id": "E", "text": "High-dose oral aspirin alone"}
      ],
      "topic": "Acute Coronary Syndrome",
      "specialty": "Cardiorespiratory",
      "difficulty": "medium",
      "question_version": "1.0.0",
      "content_mode": "PREVIEW_QA",
      "warning": "Not clinically approved; internal QA only."
    }
  ],
  "count": 1,
  "content_policy": "PREVIEW_QA_EXPLICIT"
}
```

#### B. Fetch Single Question
- **Method:** `GET`
- **Path:** `/api/v1/plab/questions/{question_id}`
- **Security:** Returns `403 QUESTION_NOT_AVAILABLE` if requested question is not Golden (unless PREVIEW_QA is active).

#### C. Evaluate Student Answer
- **Method:** `POST`
- **Path:** `/api/v1/plab/evaluate`
- **Headers:** `X-User-Id: STU-101`

**Request Example:**
```json
{
  "question_id": "PLAB-CARD-0001",
  "selected_option": "A",
  "idempotency_key": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "response_time_ms": 14200
}
```

**Post-Answer Response Example (200 OK):**
```json
{
  "attempt_id": "ATT-E7D3F192A0B4",
  "correct": true,
  "selected_answer": "A",
  "correct_answer": "A",
  "explanation": "NICE guidelines [NG185] recommend immediate primary PCI for patients presenting with acute STEMI within 12 hours of symptom onset...",
  "citations": [
    {
      "document_id": "DOC-PMC-CARD-0002",
      "reference": "NICE Guideline NG185 Section 1.2"
    }
  ],
  "topic": "Acute Coronary Syndrome",
  "learning_feedback": "Correct. Review the explanation to consolidate the learning point.",
  "question_version": "1.0.0",
  "content_mode": "PREVIEW_QA"
}
```

#### D. Fetch Student Progress & Weak Areas
- **Method:** `GET`
- **Path:** `/api/v1/plab/progress`
- **Headers:** `X-User-Id: STU-101`

**Response Example (200 OK):**
```json
{
  "user_id": "STU-101",
  "question_count": 36,
  "total_attempts": 8,
  "correct_attempts": 6,
  "overall_accuracy": 0.75,
  "recent_accuracy": 0.80,
  "first_attempt_accuracy": 0.70,
  "question_completion": 0.222,
  "topic_accuracy": {
    "Acute Coronary Syndrome": {"attempts": 4, "correct": 4, "accuracy": 1.0},
    "Heart Failure": {"attempts": 4, "correct": 2, "accuracy": 0.5}
  },
  "weak_topics": ["Heart Failure"],
  "strongest_topics": ["Acute Coronary Syndrome"],
  "mastery_model": "descriptive_attempt_metrics"
}
```

---

### 4.2 Course Learning Track (Cardiorespiratory & Renal/Urinary)

#### A. Execute Grounded Learning Query
- **Method:** `POST`
- **Path:** `/api/v1/learn/query`

**Cardiorespiratory Request Example:**
```json
{
  "course_id": "cardiorespiratory",
  "query": "What is the primary intervention for anterior STEMI?",
  "intent": "explain"
}
```

**Cardiorespiratory Grounded Response Example (200 OK):**
```json
{
  "course_id": "cardiorespiratory",
  "query": "What is the primary intervention for anterior STEMI?",
  "grounding_status": "GROUNDED",
  "answer": "Based on verified UK Cardiorespiratory clinical guidance (NICE NG185): Emergency percutaneous coronary intervention (PCI) is the preferred reperfusion strategy...",
  "explanation": "Evidence sufficiency gate PASSED with score 0.8450 (calibrated threshold tau=0.7223). Clinical guidance retrieved from section 'Acute Reperfusion' of DOC-PMC-CARD-0002.",
  "citations": [
    {
      "document_id": "DOC-PMC-CARD-0002",
      "title": "Clinical Management of Acute Coronary Syndromes",
      "section": "Acute Reperfusion Protocol",
      "reference": "DOC-PMC-CARD-0002#DOC-PMC-CARD-0002-B0014-C02"
    }
  ],
  "evidence_sufficiency_score": 0.8450,
  "evidence_sufficiency_state": "SUFFICIENT",
  "learning_check": null,
  "trace_id": "LRN-A83B9210F4D1",
  "warning": null
}
```

**Urinary Track Query Request Example:**
```json
{
  "course_id": "urinary_renal",
  "query": "What are the diagnostic criteria for acute kidney injury?",
  "intent": "explain"
}
```

**Renal v1 Grounded Extractive Response Example:**
```json
{
  "course_id": "urinary_renal",
  "query": "What are the diagnostic criteria for acute kidney injury?",
  "grounding_status": "GROUNDED",
  "answer": "<extractive text from the top frozen Renal v1 evidence chunk>",
  "explanation": "Extractive answer from the top frozen Renal v1 evidence chunk; dense score 0.900000 passed threshold 0.819929.",
  "citations": [{
    "document_id": "DOC-PMC-RENAL-0006",
    "title": "The Japanese clinical practice guideline for acute kidney injury 2016.",
    "section": "Abstract",
    "reference": "DOC-PMC-RENAL-0006#DOC-PMC-RENAL-0006-B0001-C01"
  }],
  "evidence_sufficiency_score": 0.9,
  "evidence_sufficiency_state": "SUFFICIENT",
  "learning_check": null,
  "trace_id": "LRN-C71E04B291AA",
  "warning": null
}
```

Renal v1 uses the frozen section-aware, metadata-aware Qwen dense configuration. Clients must still handle `INSUFFICIENT_EVIDENCE`, `UNSUPPORTED`, and `DATA_SOURCE_MISSING`. For `intent: "quiz"`, the current response contains no learning check and warns that Renal SBA generation is blocked because the measured evidence-recall gate did not pass. Do not present renal content as clinically approved; Human reviewed and Golden counts remain 0.

---

### 4.3 3D Anatomy AI & Viewport Commands

#### A. List Registered Anatomy Structures
- **Method:** `GET`
- **Path:** `/api/v1/anatomy/structures`
- **Ontology Scope:** Exactly 11 verified cardiovascular structures:
  `heart`, `lad`, `rca`, `lcx`, `aorta`, `left_atrium`, `right_atrium`, `left_ventricle`, `right_ventricle`, `mitral_valve`, `aortic_valve`.

#### B. Natural-Language Anatomy Command
- **Method:** `POST`
- **Path:** `/api/v1/anatomy/command`
- **Supports:**
  - Natural language: `{"query": "Show me the left ventricle"}`
  - Direct scene action: `{"action": "focus", "structure_ids": ["left_ventricle"]}`
  - Actions supported: `show`, `hide`, `focus`, `highlight`, `isolate`, `ghost`, `reset`.

**Supported Request Example:**
```json
{
  "query": "Show me the left ventricle"
}
```

**Supported Response Example (200 OK):**
```json
{
  "schema_version": "anatomy-command-v1",
  "validated": true,
  "command": {
    "action": "show",
    "structure_ids": ["left_ventricle"],
    "opacity": null
  },
  "educational_context": {
    "structure_id": "left_ventricle",
    "name": "Left Ventricle",
    "system": "cardiovascular",
    "format": "procedural_threejs",
    "camera_target": [0.2, -0.2, 0.1],
    "default_zoom": 1.6,
    "educational_summary": "Primary high-pressure systemic pump delivering blood to systemic organs across the aortic valve.",
    "related_structures": ["mitral_valve", "aortic_valve"]
  }
}
```

**Unsupported Structure Request Example:**
```json
{
  "query": "Show me the kidney"
}
```

**Unsupported Response (422 Unprocessable Entity):**
```json
{
  "detail": {
    "code": "UNSUPPORTED_ANATOMY_REQUEST",
    "message": "UNSUPPORTED_STRUCTURE: Structure 'kidney' is outside the verified cardiovascular anatomy ontology (11 structures supported)."
  }
}
```

---

## 5. Client Integration Checklist

- [ ] Attach `X-User-Id` header to every student request.
- [ ] Generate UUIDv4 for `X-Idempotency-Key` on every SBA answer evaluation submission.
- [ ] In production, handle empty PLAB question lists gracefully (shows "Curriculum under final clinician review").
- [ ] If `content_mode == "PREVIEW_QA"`, display banner: `"NOT CLINICALLY APPROVED — INTERNAL QA"`.
- [ ] Route natural language 3D viewport commands to `POST /api/v1/anatomy/command` and pass the returned `command` directly to the Three.js viewport controller.
- [ ] In course learning, check `grounding_status`: if `DATA_SOURCE_MISSING` or `INSUFFICIENT_EVIDENCE`, display the safety warning and explanation without hallucinated content.

