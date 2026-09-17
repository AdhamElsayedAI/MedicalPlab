# MedicalPlab — PLAB Provenance and Data Governance Specification
**Document Version:** 1.1.0  
**Phase / Milestone:** Gate 0.6.1 — PLAB Provenance Correction & Final Closure  
**Status:** Authoritative / Canonical  
**Date:** 2026-09-17  

---

## 1. Executive Summary & Product Alignment

MedicalPlab is an **Adaptive Evidence-Grounded Medical Learning Platform** designed for commercial startup viability. Its core architectural invariant is:

$$\text{Adaptive Layer} \longrightarrow \text{TutorService} \longrightarrow \text{Evidence Engine} \longrightarrow \text{Post-Generation Verification}$$

Under no circumstances does the platform permit direct LLM medical generation or hallucinated citations.

The PLAB learning module prepares medical students and international medical graduates for the UK GMC PLAB 1 / Medical Licensing Assessment (MLA). For PLAB to operate as a trustworthy learning mode within the unified platform alongside University learning, Socratic Remediation, and 3D Anatomy, its underlying evidence corpus and question data must be:
1. **Cryptographically verifiable** (SHA-256 integrity trees)
2. **Authoritatively provenance-traceable** directly to official publisher Version of Record (VOR) and PubMed Central (PMC) sections
3. **Commercially defensible for startup operation** (strict separation of active startup-safe sources from reference-only restricted material)
4. **Clean-checkout testable** (deterministic behavior separating test suites from local production data, with fail-closed HTTP 503 behavior when production data is omitted)

---

## 2. Active Startup-Safe vs. Reference-Only Corpus Architecture

The cardiorespiratory pilot evidence corpus is strictly partitioned to guarantee commercial safety:

### Corpus Partitioning Summary

| Category | Document Count | Chunk Count | Commercial Reuse | Ingestion / Runtime Status |
| :--- | :--- | :--- | :--- | :--- |
| **ACTIVE_STARTUP_SAFE** | **12** | **734** | **Unrestricted (CC BY 4.0)** | Active in retrieval index & startup runtime |
| **REFERENCE_ONLY** | **1** | **83** | **NonCommercial Only (CC BY-NC-SA 3.0 IGO)** | Quarantined from active commercial retrieval |
| **ARCHIVED_LOCAL** | **0** | **0** | N/A | Preserved in external archive |
| **UNRESOLVED** | **0** | **0** | N/A | None |

- **Active Startup-Safe Documents:** 12 documents (all verified CC BY 4.0)
- **Active Startup-Safe Chunks:** 734 chunks
- **Reference-Only Quarantined Documents:** 1 document (`DOC-WHO-CARD-0001`, 83 chunks)
- **Topics Covered:** Hypertension, Atrial Fibrillation, Syncope, COPD, CPR / Cardiac Arrest, Pneumothorax, ARDS, Cardiogenic Shock, Infective Endocarditis, Implantable Cardiac Devices, Aortic Stenosis, Mitral Valve Regurgitation.

### Complete 13-Source Governance Ledger

| Document ID | Specialty | Verified Title | Publisher | PMCID / DOI | Verified License | Commercial Startup Status | Final Governance Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DOC-WHO-CARD-0001** | Cardiology | Guideline for the pharmacological treatment of hypertension in adults | World Health Organization | ISBN 978-92-4-003398-6 | CC BY-NC-SA 3.0 IGO | NonCommercial / Copyleft | `REFERENCE_ONLY_NON_ACTIVE` |
| **DOC-PMC-CARD-0002** | Cardiology | Outpatient management of essential hypertension: a review based on the latest clinical guidelines | Informa UK (Taylor & Francis) | PMC11011233 <br> 10.1080/07853890.2024.2338242 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0008** | Cardiology | Advances in Atrial Fibrillation Management: A Guide for General Internists | MDPI AG | PMC11678337 <br> 10.3390/jcm13247846 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0009** | Cardiology | Recent Advances and Future Directions in Syncope Management: A Comprehensive Narrative Review | MDPI AG | PMC10856004 <br> 10.3390/jcm13030727 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0010** | Cardiology | Management of cardiogenic shock: a narrative review | SpringerOpen / BioMed Central | PMC10980676 <br> 10.1186/s13613-024-01260-y | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0011** | Cardiology | Native Infective Endocarditis: A State-of-the-Art-Review | MDPI AG | PMC11278776 <br> 10.3390/microorganisms12071481 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0012** | Cardiology | Implantable Cardiac Devices in Patients with Brady- and Tachy-Arrhythmias | IMR Press | PMC11267218 <br> 10.31083/j.rcm2505162 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0013** | Cardiology | Diagnostic Challenges in Aortic Stenosis | MDPI AG | PMC11203729 <br> 10.3390/jcdd11060162 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-CARD-0014** | Cardiology | Functional Mitral Valve Regurgitation: Mitral Valve Repair or Replacement? Our Road Map | MDPI AG | PMC11172680 <br> 10.3390/jcm13113264 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-RESP-0003** | Respiratory | Phenotype to Treatable Traits-Based Management in Chronic Obstructive Pulmonary Disease | Springer Nature (Cureus) | PMC11179745 <br> 10.7759/cureus.60423 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-RESP-0004** | Respiratory | Comparison of Observation Alone Versus Interventional Procedures in Hemodynamically Stable Patients With Pneumothorax | Springer Nature (Cureus) | PMC11097702 <br> 10.7759/cureus.58385 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-RESP-0005** | Respiratory | Diagnosis and Management of Acute Respiratory Distress Syndrome in a Time of COVID-19 | MDPI AG | PMC7762111 <br> 10.3390/diagnostics10121053 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |
| **DOC-PMC-EMERG-0001** | Emergency | Cardiopulmonary Resuscitation: Clinical Updates and Perspectives | MDPI AG | PMC11084294 <br> 10.3390/jcm13092717 | CC BY 4.0 | Commercial Safe | `KEEP_PUBLIC` |

---

## 3. Source Verification Methodology & Forensic Discovery

Source rights were verified using the strongest available rights authorities:
1. Official publisher Version of Record (VOR) copyright and license section
2. PubMed Central (PMC) full-text JATS XML permissions element (`<license_ref>`, `<license-p>`)
3. Official WHO publication rights declaration (ISBN 978-92-4-003398-6)
4. Crossref DOI API utilized solely as supporting metadata, never as the sole authority for copyright or licensing decisions.

### Critical Forensic Corrections:

1. **Definitive CC BY 4.0 Verification for DOC-PMC-CARD-0010**:
   - *Previous Gate 0.6 Status:* Incorrectly classified as `CC BY-NC-ND 4.0` / `KEEP_RUNTIME_ONLY` due to an automated Crossref query capturing a secondary Elsevier TDM syndication record.
   - *Independent VOR Audit:* Direct examination of the official PubMed Central JATS XML (`DOC-PMC-CARD-0010.xml`) and the *Annals of Intensive Care* (SpringerOpen) Version of Record confirmed:
     - `<ali:license_ref>https://creativecommons.org/licenses/by/4.0/</ali:license_ref>`
     - `<license-p>Open Access This article is licensed under a Creative Commons Attribution 4.0 International License, which permits use, sharing, adaptation, distribution and reproduction in any medium or format, as long as you give appropriate credit to the original author(s) and the source...</license-p>`
   - *Correction:* Reclassified to `CC BY 4.0`, `commercial_use = true`, `redistribution = true`, `derivative_processing = true`, `final_action = KEEP_PUBLIC`.
   - *Outcome:* Retained in the active startup-safe retrieval corpus; false Elsevier / CC BY-NC-ND classification completely expunged.

2. **NonCommercial Quarantining of WHO Guideline (DOC-WHO-CARD-0001)**:
   - *Authoritative Rights Notice:* Official WHO publication page 4 specifies: `"This work is available under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 IGO licence (CC BY-NC-SA 3.0 IGO)... To submit requests for commercial use and queries on rights and licensing, see http://www.who.int/about/licensing."`
   - *Startup Governance Action:* The NonCommercial and ShareAlike copyleft clauses prevent commercial startup deployment. While historical/local material is preserved, WHO text/chunks are **quarantined from the ACTIVE startup retrieval corpus** and classified as `REFERENCE_ONLY_NON_ACTIVE`.
   - *Coverage Safety:* The educational requirements of `PLAB-CARD-0001` and `PLAB-CARD-0003` are fully covered by `DOC-PMC-CARD-0002` (CC BY 4.0).

3. **Active Startup-Safe Corpus Totals**:
   - Exactly **12 documents** and **734 chunks** comprise the active startup-safe corpus.
   - Zero active retrieval chunks are linked to NC, NC-SA, NC-ND, ND, or unknown-license sources.

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
When a developer or CI pipeline performs a fresh `git clone` on a new machine without external files:
1. The repository code compiles and passes all unit, synthetic, and property tests deterministically.
2. If `Data/processed/` or production data root is intentionally unavailable, the runtime **fails closed** with `PLAB_CONTENT_UNAVAILABLE` (HTTP 503).
3. The platform never hallucinates evidence or silently substitutes unverified sources.

### Runtime Environment Variables
```bash
# Optional override to point to external LocalData directory:
export MEDICALPLAB_DATA_ROOT="/path/to/MedicalPlab-LocalData/PLAB"

# Optional test runner flags:
export MEDICALPLAB_PLAB_PREVIEW_QA="1"
export MEDICALPLAB_INTERNAL_REVIEW_TOKEN="your-secure-token"
```

---

## 6. Question-to-Source Educational Coverage (36/36 Active Coverage)

All 36 questions in Cardiorespiratory Batch 1 are confirmed covered by `ACTIVE_STARTUP_SAFE` evidence:

| Question ID Range | Topic | Active Startup-Safe Document | Verified License | Coverage Note |
| :--- | :--- | :--- | :--- | :--- |
| `PLAB-CARD-0001` - `0003` | Hypertension (Essential & Secondary) | `DOC-PMC-CARD-0002` | CC BY 4.0 | Full coverage of first-line CCBs (amlodipine 5mg dosing, Table 5), ACEi/ARBs, combination therapy, and secondary HTN screening (aldosterone-renin ratio). Historical WHO reference quarantined to reference-only. |
| `PLAB-CARD-0004` - `0006` | Atrial Fibrillation | `DOC-PMC-CARD-0008` | CC BY 4.0 | Rate vs rhythm control, DOAC anticoagulation, CHA2DS2-VASc scoring. |
| `PLAB-CARD-0007` - `0009` | Syncope | `DOC-PMC-CARD-0009` | CC BY 4.0 | Vasovagal vs cardiogenic syncope, orthostatic vitals, ECG red flags. |
| `PLAB-CARD-0010` - `0012` | Cardiogenic Shock | `DOC-PMC-CARD-0010` | CC BY 4.0 | First-line vasopressor (norepinephrine), inotrope (dobutamine), emergent PCI revascularization. |
| `PLAB-CARD-0013` - `0015` | Native Infective Endocarditis | `DOC-PMC-CARD-0011` | CC BY 4.0 | Modified Duke criteria, empirical antibiotic regimens, surgical indications. |
| `PLAB-CARD-0016` - `0018` | Cardiac Pacing & Devices | `DOC-PMC-CARD-0012` | CC BY 4.0 | Bradyarrhythmia pacing indications, ICD secondary prevention, CRT in heart failure. |
| `PLAB-CARD-0019` - `0021` | Aortic Stenosis | `DOC-PMC-CARD-0013` | CC BY 4.0 | Classic triad, echocardiographic valve area thresholds, SAVR vs TAVI criteria. |
| `PLAB-CARD-0022` - `0024` | Mitral Valve Regurgitation | `DOC-PMC-CARD-0014` | CC BY 4.0 | Functional vs degenerative MR, medical optimization, repair vs replacement decision tree. |
| `PLAB-RESP-0001` - `0003` | COPD Exacerbations | `DOC-PMC-RESP-0003` | CC BY 4.0 | Bronchodilators, systemic corticosteroids, controlled oxygenation, non-invasive ventilation (NIV). |
| `PLAB-RESP-0004` - `0006` | Pneumothorax | `DOC-PMC-RESP-0004` | CC BY 4.0 | Primary spontaneous vs secondary, conservative observation vs needle aspiration vs chest drain. |
| `PLAB-RESP-0007` - `0009` | ARDS | `DOC-PMC-RESP-0005` | CC BY 4.0 | Berlin definition, low tidal volume lung-protective ventilation, prone positioning, PEEP titration. |
| `PLAB-EMERG-0001` - `0003` | Advanced Life Support / CPR | `DOC-PMC-EMERG-0001` | CC BY 4.0 | Shockable vs non-shockable rhythms, adrenaline/amiodarone dosing intervals, high-quality chest compressions. |

Machine-checkable verification artifact: `Data/metadata/plab_question_evidence_coverage_v1.json` (36 / 36 covered).

---

## 7. Phase 6 Integration Architecture & Contracts

### 1. Target Architecture: Decentralized Module-Owned Persistence
The architecture centers on a **stable shared learner identity** federating module-owned data stores, with Phase 6 providing read-only unified progress composition:

```
Stable Shared Learner Identity
        │
        ├───► PLAB Module-Owned Persistence (`pilot_store.db` / `PLABPilotService`)
        ├───► University Module-Owned Persistence (`university.sqlite3` / `UniversityService`)
        ├───► Adaptive Learner State Store (`LearnerStateStore` / `LearningEvent`)
        ├───► Anatomy Module-Owned Sessions (`anatomy.sqlite3` / `AnatomyService`)
        │
        └───► Phase 6 Read-Only Unified Learner-Progress Composition
```

#### Explicit Architectural Invariant (Anti-Bloat Constraint):
DO NOT introduce:
- Central learner profile database
- Global session database
- PostgreSQL / Redis infrastructure
- JWT / monolithic auth overhaul
- New standalone "learner-profile" microservice

Phase 6 implements thin adapters and read-only query composition across existing module stores.

### 2. Attempt Telemetry $\longrightarrow$ Adaptive LearningEvent
- **Boundary:** `medicalplab.adaptive.models.LearningEvent`
- **Hook Point:** Inside `PLABPilotService.evaluate()` (`src/medicalplab/plab/pilot.py`) and `@router.post("/plab/evaluate")`.
- **Contract Payload:**
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

### 3. Incorrect Reasoning Signal $\longrightarrow$ Socratic Remediation
- **Critical Semantic Distinction:** **Wrong answer $\neq$ proven misconception.**
- **Integration Flow:**
  ```
  PLAB evaluation
      │
      ▼
  incorrect / partial reasoning signal
      │
      ▼
  ReasoningPatternDetectionEngine
      │
      ▼
  pattern / confidence / evidence check
      │
      ▼
  eligible remediation trigger
      │
      ▼
  RemediationLoopController
  ```
- **Preserved Phase 2B Invariant:** No overclaiming of misconceptions. An incorrect answer generates an initial reasoning signal. Remediation is only triggered if `ReasoningPatternDetectionEngine` detects an evidence-backed cognitive distortion with sufficient confidence. Maximum remediation loop count remains strictly bounded by existing frozen policies.

### 4. Grounded Explanation Invariant $\longrightarrow$ TutorService
- **Flow:** `PLAB Explanation Request -> TutorService -> Evidence Engine -> Post-Generation Verification`
- Under no circumstances may PLAB bypass this chain to query an LLM directly.
- `AnswerLeakScanner` guarantees zero answer leakage.

---

## 8. Verification & Compliance Sign-Off

- **Git Integrity:** Clean working tree, zero remote pushes, zero remote tags modified.
- **Source Rights Audit:** 12 active startup-safe documents (734 chunks) verified CC BY 4.0; 1 reference-only document (83 chunks) quarantined under CC BY-NC-SA 3.0 IGO.
- **Coverage Invariant:** 36 / 36 PLAB questions confirmed covered by active startup-safe sources.
- **Test Integrity:** All 355 historical unit tests passing without regression.
- **Data Governance:** Tracked Git repository contains zero copyrighted raw PDFs, raw XMLs, private SQLite databases, or local developer paths.
