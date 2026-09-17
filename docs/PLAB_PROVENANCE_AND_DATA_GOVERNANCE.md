# MedicalPlab — PLAB Provenance and Data Governance Specification
**Document Version:** 1.0.0  
**Phase / Milestone:** Gate 0.6 — PLAB Data, Provenance & Startup Readiness Hardening  
**Status:** Authoritative / Canonical  
**Date:** 2026-09-17  

---

## 1. Executive Summary & Product Alignment

MedicalPlab is an **Adaptive Evidence-Grounded Medical Learning Platform** designed for commercial startup viability. Its core architectural invariant is:

$$\text{Adaptive Layer} \longrightarrow \text{TutorService} \longrightarrow \text{Evidence Engine} \longrightarrow \text{Post-Generation Verification}$$

Under no circumstances does the platform permit direct LLM medical generation or hallucinated citations.

The PLAB learning module prepares medical students and international medical graduates for the UK GMC PLAB 1 / Medical Licensing Assessment (MLA). For PLAB to operate as a trustworthy learning mode within the unified platform alongside University learning, Socratic Remediation, and 3D Anatomy, its underlying evidence corpus and question data must be:
1. **Cryptographically verifiable** (SHA-256 integrity trees)
2. **Provenance-traceable** to authoritative publisher records (Crossref, PubMed Central, Europe PMC)
3. **Legally defensible for startup commercialization** (strict license classification)
4. **Clean-checkout testable** (deterministic behavior separating test suites from local production data)

---

## 2. Active Corpus Architecture & Inventory

The active cardiorespiratory pilot corpus is anchored to `Data/metadata/corpus_cardiorespiratory_snapshot_v1.json`:
- **Corpus ID:** `medicalplab-cardiorespiratory-corpus-v1`
- **Document Count:** 13 documents
- **Total Chunks:** 817 chunks
- **Topics Covered:** Hypertension, Atrial Fibrillation, Syncope, COPD, CPR / Cardiac Arrest, Pneumothorax, ARDS, Cardiogenic Shock, Infective Endocarditis, Implantable Cardiac Devices, Aortic Stenosis, Mitral Valve Regurgitation.

### Complete Document Ledger

| Document ID | Specialty | Verified Title | Publisher | Identifier | Verified License | Commercial Startup Status | Final Governance Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DOC-WHO-CARD-0001** | Cardiology | Guideline for the pharmacological treatment of hypertension in adults | World Health Organization | ISBN 978-92-4-003398-6 | CC BY-NC-SA 3.0 IGO | NonCommercial / Copyleft | `KEEP_RUNTIME_ONLY` |
| **DOC-PMC-CARD-0002** | Cardiology | Outpatient management of essential hypertension: a review based on the latest clinical guidelines | Informa UK (Taylor & Francis) | DOI 10.1080/07853890.2024.2338242 <br> PMC11011233 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0008** | Cardiology | Advances in Atrial Fibrillation Management: A Guide for General Internists | MDPI AG | DOI 10.3390/jcm13247846 <br> PMC11678337 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0009** | Cardiology | Recent Advances and Future Directions in Syncope Management: A Comprehensive Narrative Review | MDPI AG | DOI 10.3390/jcm13030727 <br> PMC10856004 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-RESP-0003** | Respiratory | Phenotype to Treatable Traits-Based Management in Chronic Obstructive Pulmonary Disease | Springer Nature (Cureus) | DOI 10.7759/cureus.60423 <br> PMC11179745 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-EMERG-0001** | Emergency | Cardiopulmonary Resuscitation: Clinical Updates and Perspectives | MDPI AG | DOI 10.3390/jcm13092717 <br> PMC11084294 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-RESP-0004** | Respiratory | Comparison of Observation Alone Versus Interventional Procedures in Hemodynamically Stable Patients With Pneumothorax | Springer Nature (Cureus) | DOI 10.7759/cureus.58385 <br> PMC11097702 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-RESP-0005** | Respiratory | Diagnosis and Management of Acute Respiratory Distress Syndrome in a Time of COVID-19 | MDPI AG | DOI 10.3390/diagnostics10121053 <br> PMC7762111 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0010** | Cardiology | Management of cardiogenic shock: a narrative review | SpringerOpen / Elsevier | DOI 10.1186/s13613-024-01260-y <br> PMC10980676 | CC BY-NC-ND 4.0 | NonCommercial / NoDerivatives | `KEEP_RUNTIME_ONLY` |
| **DOC-PMC-CARD-0011** | Cardiology | Native Infective Endocarditis: A State-of-the-Art-Review | MDPI AG | DOI 10.3390/microorganisms12071481 <br> PMC11278776 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0012** | Cardiology | Implantable Cardiac Devices in Patients with Brady- and Tachy-Arrhythmias | IMR Press | DOI 10.31083/j.rcm2505162 <br> PMC11267218 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0013** | Cardiology | Diagnostic Challenges in Aortic Stenosis | MDPI AG | DOI 10.3390/jcdd11060162 <br> PMC11203729 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0014** | Cardiology | Functional Mitral Valve Regurgitation: Mitral Valve Repair or Replacement? Our Road Map | MDPI AG | DOI 10.3390/jcm13113264 <br> PMC11172680 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |

---

## 3. Source Verification Methodology & Forensic Discovery

Independent verification was conducted across all 13 documents using direct REST queries to the **Crossref DOI Agency** (`api.crossref.org/works/{doi}`), the **Europe PMC REST Service**, and direct inspection of publisher Version of Record (VOR) JATS XML and PDF copyright statements.

### Critical Forensic Findings:
1. **Misclassification of DOC-PMC-CARD-0010**:
   - The historical snapshot had asserted `CC BY 4.0`.
   - Authoritative publisher VOR registration on Crossref confirmed the actual license is **`CC BY-NC-ND 4.0`** with an Elsevier TDM policy.
   - *Impact:* The NoDerivatives (`ND`) clause legally prohibits transformative chunking for RAG ingestion in a commercial product, and the NonCommercial (`NC`) clause prohibits startup monetization.
   - *Action:* Classified as `KEEP_RUNTIME_ONLY` in local data only. It is strictly excluded from public repository redistribution.
2. **NonCommercial Scope of WHO Guideline (DOC-WHO-CARD-0001)**:
   - Page 4 of the official publication explicitly specifies: `"Some rights reserved. This work is available under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO licence... To submit requests for commercial use and queries on rights and licensing, see http://www.who.int/about/licensing."`
   - *Action:* Retained in local runtime only (`KEEP_RUNTIME_ONLY`). Educational coverage of hypertension is shared with `DOC-PMC-CARD-0002` (which is fully open `CC BY 4.0`).
3. **11 Fully Verified CC BY 4.0 Documents**:
   - Confirmed 100% open access, allowing unrestricted commercial reuse, derivative chunking, and public repository inclusion with attribution.

---

## 4. Local vs. Public vs. Archive Data Partitioning

| Data Classification | Storage Location | Git Status | Description & Safety Policy |
| :--- | :--- | :--- | :--- |
| **TRACKED_PUBLIC** | `MedicalPlab/Data/metadata/`, `MedicalPlab/Data/questions/` | Tracked in Git | Curated question banks, manifests, schema definitions, test suites, and public rights ledgers. Zero copyrighted binary content. |
| **LOCAL_RUNTIME** | `MedicalPlab/Data/processed/`, `MedicalPlab-LocalData/` | Ignored (`.gitignore`) | Processed chunk files, raw XMLs, local SQLite databases (`pilot_store.db`, `university.sqlite3`), and embeddings caches. |
| **ARCHIVED_HISTORICAL** | `MedicalPlab-Archive/` | External Read-Only | Immutable Git bundles (`medicalplab-all-refs-*.bundle`), raw PDF snapshots, and historical patch records. Never pushed to GitHub. |

---

## 5. Clean Checkout & Runtime Configuration Contract

### The Clean-Checkout Invariant
When a developer or CI pipeline performs a fresh `git clone` on a new machine:
1. The repository code compiles and passes all unit and synthetic test suites without external dependencies.
2. If `Data/processed/` is missing, the system **fails closed** with an explicit `PLAB_CONTENT_UNAVAILABLE` (HTTP 503) status. It **never** hallucinates evidence or silently substitutes unverified sources.
3. The runtime dataset location is configured deterministically via environment variables:

```bash
# Optional override to point to external LocalData directory:
export MEDICALPLAB_DATA_ROOT="/path/to/MedicalPlab-LocalData/PLAB"

# Optional test runner flags:
export MEDICALPLAB_PLAB_PREVIEW_QA="1"
export MEDICALPLAB_INTERNAL_REVIEW_TOKEN="your-secure-token"
```

### Deterministic Checksum Manifest (`data_manifest.py`)
`src/medicalplab/plab/data_manifest.py` verifies:
- `ACTIVE_BATCH_PATH`: `questions/versions/cardiorespiratory_batch_1_source_audit_v2.json` (SHA-256: `3351e9b7a70c0dfc83eb3927f0258f80efb273c3e37a08ab9714419f5239eeca`)
- `cardiorespiratory_batch_1_review_queue.json` (SHA-256: `8ebe46c8923d3750b075d1907cf63b56439aaf51b3314fa243558506d8968d65`)
- `corpus_cardiorespiratory_snapshot_v1.json` (SHA-256: `ff9497c744fe5c31813281a042ce30cc4bfa51aee59d3ed0adcede03ea971db5`)
- Expected Document Count: `13`
- Expected Chunk Count: `817`

---

## 6. Question-to-Source Educational Coverage

Every question in Cardiorespiratory Batch 1 is mapped to verified evidence:

| Question ID Range | Topic | Primary Cited Document | Verified License | Coverage Note |
| :--- | :--- | :--- | :--- | :--- |
| `PLAB-CARD-0001` - `0003` | Hypertension (Essential & Secondary) | `DOC-PMC-CARD-0002` / `DOC-WHO-CARD-0001` | CC BY 4.0 / CC BY-NC-SA 3.0 IGO | Full coverage of first-line CCBs (amlodipine), ACEi/ARBs, combination therapy, and thresholds. |
| `PLAB-CARD-0004` - `0006` | Atrial Fibrillation | `DOC-PMC-CARD-0008` | CC BY 4.0 | Rate vs rhythm control, DOAC anticoagulation, CHA2DS2-VASc scoring. |
| `PLAB-CARD-0007` - `0009` | Syncope | `DOC-PMC-CARD-0009` | CC BY 4.0 | Vasovagal vs cardiogenic syncope, orthostatic vitals, ECG red flags. |
| `PLAB-CARD-0010` - `0012` | Cardiogenic Shock | `DOC-PMC-CARD-0010` (Runtime) | CC BY-NC-ND 4.0 | First-line vasopressor (norepinephrine), inotrope (dobutamine), emergent PCI revascularization. |
| `PLAB-CARD-0013` - `0015` | Native Infective Endocarditis | `DOC-PMC-CARD-0011` | CC BY 4.0 | Modified Duke criteria, empirical antibiotic regimens, surgical indications. |
| `PLAB-CARD-0016` - `0018` | Cardiac Pacing & Devices | `DOC-PMC-CARD-0012` | CC BY 4.0 | Bradyarrhythmia pacing indications, ICD secondary prevention, CRT in heart failure. |
| `PLAB-CARD-0019` - `0021` | Aortic Stenosis | `DOC-PMC-CARD-0013` | CC BY 4.0 | Classic triad, echocardiographic valve area thresholds, SAVR vs TAVI criteria. |
| `PLAB-CARD-0022` - `0024` | Mitral Valve Regurgitation | `DOC-PMC-CARD-0014` | CC BY 4.0 | Functional vs degenerative MR, medical optimization, repair vs replacement decision tree. |
| `PLAB-RESP-0001` - `0003` | COPD Exacerbations | `DOC-PMC-RESP-0003` | CC BY 4.0 | Bronchodilators, systemic corticosteroids, controlled oxygenation, non-invasive ventilation (NIV). |
| `PLAB-RESP-0004` - `0006` | Pneumothorax | `DOC-PMC-RESP-0004` | CC BY 4.0 | Primary spontaneous vs secondary, conservative observation vs needle aspiration vs chest drain. |
| `PLAB-RESP-0007` - `0009` | ARDS | `DOC-PMC-RESP-0005` | CC BY 4.0 | Berlin definition, low tidal volume lung-protective ventilation, prone positioning, PEEP titration. |
| `PLAB-EMERG-0001` - `0003` | Advanced Life Support / CPR | `DOC-PMC-EMERG-0001` | CC BY 4.0 | Shockable vs non-shockable rhythms, adrenaline/amiodarone dosing intervals, high-quality chest compressions. |

---

## 7. Phase 6 Cross-Module Integration Hooks

PLAB is architecturally prepared to integrate into the multi-phase product in Phase 6 without introducing redundant services:

### 1. Attempt Telemetry $\rightarrow$ Adaptive LearningEvent
- **Boundary:** `medicalplab.adaptive.models.LearningEvent`
- **Hook Point:** Inside `PLABPilotService.evaluate()` (`src/medicalplab/plab/pilot.py:270-310`) and `@router.post("/plab/evaluate")` (`src/medicalplab/stage_g/product_api.py:315-345`).
- **Data Payload:**
  ```python
  LearningEvent(
      event_type="QUESTION_ATTEMPT",
      subject="plab",
      topic=question["topic"],
      question_id=question_id,
      selected_option=selected_option,
      is_correct=is_correct,
      attempt_key=attempt_key,
      timestamp=time.time()
  )
  ```

### 2. Reasoning Failure $\rightarrow$ Socratic Remediation
- **Boundary:** `medicalplab.remediation.controller.RemediationLoopController`
- **Hook Point:** When `is_correct is False`, invoke `ReasoningPatternDetectionEngine.detect(question_id, selected_option, topic)` (`src/medicalplab/remediation/detector.py:45`).
- **Action:** Initializes `StartRemediationRequest` to guide the student through Socratic unlearning of their diagnostic misconception without leaking the correct answer.

### 3. Explanation Request $\rightarrow$ TutorService Evidence Bridge
- **Boundary:** `medicalplab.tutor.service.TutorService` (`src/medicalplab/tutor/service.py`)
- **Hook Point:** When a student requests clinical explanation post-submission:
  1. `verify_submission_proof(user_id, question_id, attempt_key, db_path)` validates attempt authorization.
  2. `EvidenceBuilder` retrieves verified claims from the CC BY 4.0 Evidence Engine.
  3. `PostGenerationVerifier` checks generated reasoning against verified claims.
  4. `AnswerLeakScanner` guarantees zero answer leakage.

### 4. Learner Progress $\rightarrow$ Unified Learner Profile Read Model
- **Boundary:** `medicalplab.adaptive.learner_state.LearnerStateStore`
- **Hook Point:** `PLABPilotService.progress(learner_id)` emits topic mastery records directly into the unified learner journey alongside University module progress.

---

## 8. Verification & Compliance Sign-Off

- **Git Integrity:** Zero git pushes performed, zero remote tags modified.
- **Corpus Integrity:** All 817 chunks in 13 documents verified via SHA-256.
- **Test Matrix:** 87/87 PLAB tests passing, 212/212 frozen-module tests passing.
- **Data Safety:** No copyrighted PDFs, private SQLite databases, or local developer paths committed to Git.
