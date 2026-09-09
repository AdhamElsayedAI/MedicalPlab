# MedicalPlab Cardiorespiratory Corpus Snapshot v1

**Corpus ID:** `medicalplab-cardiorespiratory-corpus-v1`  
**Version:** `1.0.0`  
**Created:** 2026-09-09T06:27:00Z  
**Verification State:** LOCAL VERIFIED (13 documents, 817 chunks)  

---

## 1. Verified Ingested Documents

All 13 documents below exist locally in `Data/raw/` and `Data/processed/` with complete provenance chains:
`raw XML/PDF → JATS extraction → canonical adaptation → structure-aware chunking → chunk validation (PASS) → chunk integrity validation (PASS)`.

| Document ID | Specialty | Title | License | Chunks | Chunks SHA-256 (first 16) | Status |
|---|---|---|---|---:|---|---|
| `DOC-WHO-CARD-0001` | Cardiology | Guideline for the pharmacological treatment of hypertension in adults | CC BY-NC-SA 3.0 IGO | 83 | `a84ad34a2b7e66cc` | VERIFIED |
| `DOC-PMC-CARD-0002` | Cardiology | Outpatient management of essential hypertension: a review based on latest clinical guidelines | CC BY 4.0 | 144 | `1845f390f095bd4c` | VERIFIED |
| `DOC-PMC-CARD-0008` | Cardiology | Advances in Atrial Fibrillation Management: A Guide for General Internists | CC BY 4.0 | 42 | `89fa22ffd17bb2dc` | VERIFIED |
| `DOC-PMC-CARD-0009` | Cardiology | Recent Advances and Future Directions in Syncope Management: A Comprehensive Narrative Review | CC BY 4.0 | 54 | `c5d9a8d1556d7945` | VERIFIED |
| `DOC-PMC-RESP-0003` | Respiratory | Phenotype to Treatable Traits-Based Management in Chronic Obstructive Pulmonary Disease | CC BY 4.0 | 64 | `b74e4a51e5aede2e` | VERIFIED |
| `DOC-PMC-EMERG-0001` | Emergency | Cardiopulmonary Resuscitation: Clinical Updates and Perspectives | CC BY 4.0 | 11 | `b818b59b85ce13cb` | VERIFIED |
| `DOC-PMC-RESP-0004` | Respiratory | Comparison of Observation Alone Versus Interventional Procedures in Pneumothorax | CC BY 4.0 | 58 | `c9d40acc922efa2a` | VERIFIED |
| `DOC-PMC-RESP-0005` | Respiratory | Diagnosis and Management of Acute Respiratory Distress Syndrome in a Time of COVID-19 | CC BY 4.0 | 38 | `e9559a614664aa77` | VERIFIED |
| `DOC-PMC-CARD-0010` | Cardiology | Management of cardiogenic shock: a narrative review | CC BY 4.0 | 77 | `13fce0136cdc72d1` | VERIFIED |
| `DOC-PMC-CARD-0011` | Cardiology | Native Infective Endocarditis: A State-of-the-Art-Review | CC BY 4.0 | 85 | `f68ad8c3aee8f495` | VERIFIED |
| `DOC-PMC-CARD-0012` | Cardiology | Implantable Cardiac Devices in Patients with Brady- and Tachy-Arrhythmias | CC BY 4.0 | 69 | `c0c5fb99b9a6917e` | VERIFIED |
| `DOC-PMC-CARD-0013` | Cardiology | Diagnostic Challenges in Aortic Stenosis | CC BY 4.0 | 62 | `7ee814bff044e82c` | VERIFIED |
| `DOC-PMC-CARD-0014` | Cardiology | Functional Mitral Valve Regurgitation: Mitral Valve Repair or Replacement? | CC BY 4.0 | 30 | `be86e4a7cf022676` | VERIFIED |

**Total Verified Corpus Chunks: 817**

---

## 2. Unverified Historical Claims & Exclusions

### Wave 1 Missing Artifacts (Preserved as NOT VERIFIED)
The following 6 documents from the earlier 8-document / 702-chunk checkpoint report were not transferred to this workspace and do not exist locally:
- `DOC-PMC-CARD-0003` (Heart failure, reported 88 chunks)
- `DOC-PMC-CARD-0004` (ACS/STEMI/NSTEMI, reported 34 chunks)
- `DOC-PMC-CARD-0005` (Type B aortic dissection, reported 49 chunks)
- `DOC-PMC-CARD-0006` (Pericardial effusion/tamponade, reported 44 chunks)
- `DOC-PMC-CARD-0007` (Pulmonary embolism, reported 108 chunks)
- `DOC-PMC-RESP-0001` (Asthma, reported 62 chunks)
- `DOC-PMC-RESP-0002` (Pneumonia, reported 173 chunks)

These remain flagged as **NOT VERIFIED** and are excluded from the verified local snapshot.

### Licensing & Reference Exclusions
The following authoritative sources are excluded from production RAG ingestion per licensing rules:
- **NICE Guidelines** (`SRC-NICE-*`): NICE UK Open Content Licence requires separate licensing/permission for AI use. Reference/verification only.
- **Resuscitation Council UK (RCUK)** ALS 2025: Reference only.
- **British Thoracic Society (BTS)** Pleural 2023: Reference only.
- **GMC Sample Questions** (`SRC-GMC-PLAB1-SAMPLES-2024`): Evaluation/calibration only. NEVER ingested into RAG or question banks.

---

## 3. Historical Evaluation Artifacts Integrity Note

Historical evaluation artifacts (`evaluation/results/*.json`, `evaluation/retrieval_eval_multisource_heldout_v1.json`, `evaluation/HELDOUT_FREEZE_MANIFEST.json`) remain untouched. All new benchmark evaluations on this expanded 817-chunk corpus will be saved to newly versioned result files.
