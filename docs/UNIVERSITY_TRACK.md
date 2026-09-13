# University Learning Track

## Purpose
The University Learning Track provides undergraduate medical students with focused, source-backed practice on foundational basic-science concepts. Unlike licensing-oriented clinical exam preparation (e.g., PLAB), this track emphasizes mechanistic comprehension, basic physiology, and curriculum-aligned preclinical learning.

## Target User
Undergraduate medical students, preclinical trainees, and healthcare students studying foundational medical sciences prior to clinical licensing examinations.

## Current University Scope
- **Lane**: Renal Basic-Science University Learning MVP
- **Total Questions**: 6
- **Servable Questions**: 6 (`VERIFIED_EDUCATIONAL`)
- **Review Required Questions**: 0
- **Quarantined Questions**: 0
- **Identities**: Anonymous learner identity (`uni-<uuid>`) persisted in browser `localStorage`. No institutional authentication required for this MVP.

## Subject & Topic Hierarchy
- **Subject**: `Renal physiology` (6 questions)
  - **Topic**: `RAAS mechanisms` (3 questions)
    - `UNI-RENAL-001`: Substrate cleaved by renin (Angiotensinogen)
    - `UNI-RENAL-002`: Enzyme converting Angiotensin I to II (ACE)
    - `UNI-RENAL-003`: Effector receptor for Angiotensin II (AT1R)
  - **Topic**: `Glomerular filtration barrier` (3 questions)
    - `UNI-RENAL-004`: Cellular components of the filtration barrier (Endothelium & Podocytes)
    - `UNI-RENAL-005`: Intermediate layer separating cellular components (GBM)
    - `UNI-RENAL-006`: Core physiological function of glomerular filtration

## University vs PLAB Separation
Separation between the University Track and PLAB licensing preparation is absolute and enforced at every architectural boundary:
1. **Question Pool Isolation**:
   - University questions use the prefix `UNI-` with `track: "university"`.
   - PLAB questions use `PLAB-` prefixes with licensing schema contracts.
   - Zero pool overlap: University API queries never return PLAB questions; PLAB endpoints reject `UNI-` question IDs.
2. **Persistence & State Isolation**:
   - University attempts persist independently to `Data/persistence/university.sqlite3` in the `university_attempts` table.
   - PLAB attempts and reviews persist in `pilot.db`.
   - Answering University questions never mutates PLAB learner progress, attempt records, or governance counts.
3. **No Failover / Fallback**:
   - If University content or storage is unavailable, the system fails closed with professional HTTP 503 errors. It never falls back to PLAB content.
4. **Governance & Review Policy**:
   - University questions carry educational verification status (`VERIFIED_EDUCATIONAL`).
   - University questions do not inherit or claim PLAB UK clinician sign-off or golden exam status.

## Content Quality & Traceability Policy
- **Source-Grounded Provenance**: Every question is grounded in an existing public, open-access publication in `Data/processed/renal_v1/` (e.g., `DOC-PMC-RENAL-0001`, `DOC-PMC-RENAL-0002`).
- **Integrity Anchors**: Every question includes an exact text excerpt and its SHA-256 checksum (`excerpt_sha256`), license information (CC BY 3.0 / CC BY 4.0), and official public URL.
- **Fail-Closed Bank Audit**: Any malformed field, broken character encoding (`\ufffd`, mojibake), duplicate stem/ID, missing explanation, invalid option structure, or mismatched excerpt checksum causes immediate quarantine of the question.

## Question Status Model
- `VERIFIED_EDUCATIONAL`: Passes structural audit, conforms to basic-science content kind, has valid SHA-256 evidence integrity, and is servable to students.
- `REVIEW_REQUIRED`: Educational question requiring structural or content review; strictly excluded from normal student mode.
- `QUARANTINED`: Content with validation failures, missing fields, duplicate text, or clinical decision requirements without proper review; completely excluded from student serving.

## Learning Loop
1. **Explore**: Student browses available subjects (`GET /api/v1/university/subjects`).
2. **Select Topic**: Student chooses a topic within the subject (`GET /api/v1/university/topics?subject=...`).
3. **Practice**: Student retrieves sequential questions without answer leakage (`GET /api/v1/university/question?subject=...&topic=...`).
4. **Submit**: Student submits an answer with an idempotent attempt key (`POST /api/v1/university/answer`).
5. **Feedback**: Student receives instantaneous correctness feedback, official correct answer, complete mechanistic explanation, and direct source citations.
6. **Progress**: Student reviews cumulative attempts, accuracy, and topic-specific mastery levels (`GET /api/v1/university/progress`).
7. **Navigate / Next Action**: System directs student to the next question (`next_question`) or recommends topic review upon topic completion (`review_topic`).

## Persistence & Mastery Logic
- **Storage**: Independent SQLite database with immediate transaction isolation and foreign learner scoping.
- **Idempotency**: Submissions with identical `(user_id, attempt_key)` replay the recorded result; conflicting option submissions for the same attempt key reject with HTTP 409.
- **Mastery Mapping**: Reuses MedicalPlab's validated mastery thresholds (`determine_mastery_level`):
  - `< 60%` accuracy: `beginner` / Needs review
  - `60% - 79%`: `competent`
  - `80% - 89%`: `proficient`
  - `≥ 90%` (with volume): `mastered`
- **Adaptive Recommendation**: Weakest topic with attempts and `< 60%` accuracy is recommended first; otherwise, the least practiced topic is suggested.

## AI Tutor Status
- **Status**: `INTENTIONALLY_DEFERRED`.
- No experimental RAG pipelines, external LLMs, or unstable agent frameworks are introduced in this release. All learning interaction is deterministic, source-verified, and fail-closed.

## Known Limitations
- Current scope is strictly limited to the Renal Basic-Science MVP (6 questions).
- Learner state is scoped to client-generated device IDs stored in `localStorage`; clearing browser data resets local progress.
- Does not provide full multi-course LMS features, user account management, or institutional gradebook exports.

## Future Deferred Features
- Additional preclinical disciplines: Cardiovascular physiology, Respiratory physiology, Neuroanatomy, and Medical Biochemistry.
- Bounded, evidence-grounded AI Tutor dialogue using verified curriculum chunks.
- Spaced repetition scheduling based on forgetting curve models.
- Institutional cohort analytics for medical school faculty.
