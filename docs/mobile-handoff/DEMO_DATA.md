# MedicalPlab Demo Fixtures & Seed Content Reference

This document catalogs the verified educational questions, distractor mappings, and held-out transfer items available in the repository for mobile demo and testing.

> **Data Integrity & Security Boundary Notice:**
> 1. **Synthetic Demo Fixtures:** The questions and transfer items documented here are pre-seeded basic science educational content and synthetic test fixtures sourced from `Data/university/questions.json` and `src/medicalplab/remediation/transfer.py`.
> 2. **Developer Verification Only:** Any answer keys shown below are provided strictly for developer verification, end-to-end testing, and smoke validation.
> 3. **Never Bundle Keys in Mobile Runtime:** The mobile client application must **never** bundle, hardcode, or infer hidden answer keys client-side. The backend remains strictly authoritative for correctness.
> 4. **Production Independence:** Real clinical assessment content must never rely on exposed demo keys or predictable fixtures.
> 5. **Server-Side Key Stripping:** The runtime endpoints (`GET /api/v1/university/question` and `GET /api/v1/remediation/session/{session_id}/transfer`) strictly strip all `correct_answer`, `explanation`, and annotation fields before sending payloads to the mobile client.

---

## 1. Learner Identity Conventions

- **Default Demo Learner ID:** `demo-student-001`
- **Dynamic Mobile Device Format:** `uni-<uuidv4>` (e.g. `uni-e47b1980-84c9-4b13-a4c3-10e82c5f110a`)
- **Header:** `X-User-Id: <learner_id>`

---

## 2. Educational Structure Hierarchy

- **Subject:** `Renal physiology`
  - **Topic 1:** `RAAS mechanisms` (3 questions)
  - **Topic 2:** `Glomerular filtration barrier` (2 questions)

---

## 3. Question Bank & Remediation Scenarios

### Question 1: UNI-RENAL-001 (Recommended Remediation Demo)
Demonstrates the full 11-step learning journey with confirmed held-out transfer.

- **Question ID:** `UNI-RENAL-001`
- **Subject:** `Renal physiology`
- **Topic:** `RAAS mechanisms`
- **Stem:** *"In the renin-angiotensin pathway, which substrate does active renin cleave to form angiotensin I?"*
- **Options:**
  - `A`: Angiotensinogen **[CORRECT ANSWER]**
  - `B`: Angiotensin II **[DEMO DISTRACTOR]** — *Triggers RAAS substrate confusion (`PATTERN-RAAS-SUB-01`)*
  - `C`: Aldosterone
  - `D`: Albumin
- **Correct Option:** `A`
- **Recommended Demo Flow:**
  1. Submit Option `B` to trigger incorrect feedback.
  2. Call `/api/v1/adaptive/recommendation` $\rightarrow$ returns action `ASK_GROUNDED_TUTOR`.
  3. Start Socratic remediation with `question_id: "UNI-RENAL-001"`, `selected_option: "B"`.
  4. Complete 3 Socratic turns.
  5. Session transitions to `AWAITING_TRANSFER` with `transfer_available: true`.
  6. Dispenses held-out transfer item `UNI-RENAL-001-T`.

#### Paired Held-Out Transfer Item: UNI-RENAL-001-T
- **Question ID:** `UNI-RENAL-001-T`
- **Stem:** *"In an investigation of renovascular regulation, an elevated plasma renin activity is observed. Which circulating hepatic globular glycoprotein serves as the direct cleavage substrate for active renin?"*
- **Options:**
  - `A`: Angiotensinogen **[CORRECT ANSWER]**
  - `B`: Angiotensin II
  - `C`: Aldosterone
  - `D`: Bradykinin
- **Correct Option:** `A`
- **Scoring Result:** Submitting `A` with `was_assisted: false` produces `outcome: "TRANSFER_CONFIRMED"`.

---

### Question 2: UNI-RENAL-002 (Alternative Transfer Demo)
- **Question ID:** `UNI-RENAL-002`
- **Subject:** `Renal physiology`
- **Topic:** `RAAS mechanisms`
- **Stem:** *"Which enzyme converts angiotensin I into angiotensin II?"*
- **Options:**
  - `A`: Renin **[DEMO DISTRACTOR]** — *Triggers enzyme role inversion*
  - `B`: Angiotensin-converting enzyme (ACE) **[CORRECT ANSWER]**
  - `C`: Pepsin
  - `D`: Amylase
- **Correct Option:** `B`
- **Paired Held-Out Transfer Item:** `UNI-RENAL-002-T` (Correct Option: `B`, Angiotensin-converting enzyme).

---

### Question 3: UNI-RENAL-003 (Transfer Unavailable Demo)
Demonstrates graceful fallback when a topic/question does not have a paired held-out transfer item.

- **Question ID:** `UNI-RENAL-003`
- **Subject:** `Renal physiology`
- **Topic:** `RAAS mechanisms`
- **Stem:** *"Which receptor mediates the main classical effects of angiotensin II in the RAAS pathway described here?"*
- **Options:**
  - `A`: Insulin receptor **[DEMO DISTRACTOR]**
  - `B`: Nicotinic acetylcholine receptor
  - `C`: Type 1 angiotensin II receptor (AT1R) **[CORRECT ANSWER]**
  - `D`: Thyroid hormone receptor
- **Correct Option:** `C`
- **Transfer Status:** **NO TRANSFER ITEM REGISTERED**.
- **Expected Behavior:**
  1. Complete Turns 1, 2, and 3.
  2. Requesting `GET /api/v1/remediation/session/{session_id}/transfer` returns `HTTP 404 Not Found` (`"No eligible held-out transfer item available for question 'UNI-RENAL-003'"`).
  3. Mobile UI must gracefully inform student that transfer assessment is unavailable and complete the session with `outcome: "UNRESOLVED"`.

---

### Question 4: UNI-RENAL-004 (Glomerular Filtration Demo)
- **Question ID:** `UNI-RENAL-004`
- **Subject:** `Renal physiology`
- **Topic:** `Glomerular filtration barrier`
- **Stem:** *"Which pair of cell types forms the two cellular sides of the glomerular filtration barrier?"*
- **Options:**
  - `A`: Hepatocytes and cholangiocytes
  - `B`: Osteoblasts and osteoclasts
  - `C`: Neurons and astrocytes
  - `D`: Fenestrated endothelial cells and podocytes **[CORRECT ANSWER]**
- **Correct Option:** `D`
- **Transfer Status:** No held-out transfer item registered.

---

### Question 5: UNI-RENAL-005
- **Question ID:** `UNI-RENAL-005`
- **Subject:** `Renal physiology`
- **Topic:** `Glomerular filtration barrier`
- **Stem:** *"What lies between the fenestrated endothelium and podocytes in the glomerular filtration barrier?"*
- **Options:**
  - `A`: Glomerular basement membrane **[CORRECT ANSWER]**
  - `B`: Articular cartilage
  - `C`: Myelin sheath
  - `D`: Epidermal keratin layer
- **Correct Option:** `A`
- **Transfer Status:** No held-out transfer item registered.

---

## 4. Summary Matrix of Working Test Data

| Question ID | Subject | Topic | Correct Option | Demo Distractor | Transfer Item Available? | Transfer Item ID | Transfer Correct Option |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| `UNI-RENAL-001` | Renal physiology | RAAS mechanisms | `A` | `B` | **YES** | `UNI-RENAL-001-T` | `A` |
| `UNI-RENAL-002` | Renal physiology | RAAS mechanisms | `B` | `A` | **YES** | `UNI-RENAL-002-T` | `B` |
| `UNI-RENAL-003` | Renal physiology | RAAS mechanisms | `C` | `A` | **NO (404)** | None | N/A |
| `UNI-RENAL-004` | Renal physiology | Glomerular filtration | `D` | `A` | **NO (404)** | None | N/A |
| `UNI-RENAL-005` | Renal physiology | Glomerular filtration | `A` | `B` | **NO (404)** | None | N/A |
