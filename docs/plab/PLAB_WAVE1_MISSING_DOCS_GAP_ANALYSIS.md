# PLAB Historical Wave 1 Missing Documents: Systematic Coverage Gap Analysis

**Date:** 2026-09-09  
**Corpus Baseline:** `medicalplab-cardiorespiratory-corpus-v1` (13 documents, 817 chunks)  
**Status:** COMPLETE GAP ANALYSIS (Post-Wave-2 / Pre-Wave-3 Evaluation)  
**Core Policy:** Do NOT automatically ingest unverified historical documents. Ingestion must be justified by measurable evidence need, not chunk or document count.

---

## 1. Context & Verification Status

In the initial project records, 8 Cardiorespiratory documents (702 chunks) were reported for Wave 1.
Independent local inspection confirmed:
- `DOC-WHO-CARD-0001` (83 chunks): **LOCAL VERIFIED**
- `DOC-PMC-CARD-0002` (144 chunks): **LOCAL VERIFIED**
- Wave 1 Verified Subtotal: **227 chunks**

The remaining 6 Wave 1 PMC documents (`DOC-PMC-CARD-0003` to `0007`, `DOC-PMC-RESP-0001` to `0002`) were NOT found locally and are flagged as **NOT VERIFIED**.

In Wave 2, 11 new open-access PMC documents were ingested through the JATS pipeline, expanding the verified corpus to **13 documents, 817 chunks**.

---

## 2. Document-by-Document Gap Analysis

| Missing Document Candidate | Topic | Priority | Current 817-Chunk Coverage State | Does it close a real topic gap? | Expected Retrieval Impact | Redundancy vs Value Assessment | Recommendation |
|---|---|---|---|---|---|---|---|
| `DOC-PMC-CARD-0003` (reported 88 chunks) | **Heart Failure** | P0 | Partial (`DOC-PMC-CARD-0010` cardiogenic shock covers acute decompensation; `DOC-PMC-CARD-0014` covers functional MR in HF). Missing chronic quadruple therapy (ARNI/ACEi, BB, MRA, SGLT2i). | **YES** | High (vital for chronic HF pharmacological queries) | High Value. Quadruple therapy is a core PLAB 1 staple. | **RECOMMEND INGESTION IN WAVE 3** (select verified CC BY 4.0 PMC article on chronic HF guidelines). |
| `DOC-PMC-CARD-0004` (reported 34 chunks) | **Acute Coronary Syndromes (ACS/STEMI/NSTEMI)** | P0 | Partial (`DOC-PMC-CARD-0010` covers ischaemic shock). Missing acute STEMI vs NSTEMI pathways, troponin interpretation, primary PCI vs thrombolysis, DAPT duration. | **YES** | High (core emergency cardiology queries) | High Value. Essential emergency competency in MLA content map. | **RECOMMEND INGESTION IN WAVE 3** (select fresh CC BY 4.0 PMC review on ACS diagnosis and management). |
| `DOC-PMC-CARD-0005` (reported 49 chunks) | **Type B Aortic Dissection** | P0 | Minimal (covered only generally in vascular overviews; `DOC-PMC-CARD-0013` is Aortic Stenosis). Missing Stanford classification, IV labetalol BP targets (SBP 100-120), TEVAR indications. | **YES** | Medium | High Value. Distinctive clinical vignette with specific hemodynamic targets. | **RECOMMEND INGESTION IN WAVE 3**. |
| `DOC-PMC-CARD-0006` (reported 44 chunks) | **Pericardial Effusion & Tamponade** | P0 | Minimal. Missing Beck's triad (hypotension, JVP elevation, muffled heart sounds), electrical alternans, pulsus paradoxus, urgent pericardiocentesis. | **YES** | Medium | High Value. High-yield emergency vignette. | **RECOMMEND INGESTION IN WAVE 3**. |
| `DOC-PMC-CARD-0007` (reported 108 chunks) | **Pulmonary Embolism (PE)** | P0 | Minimal (`DOC-PMC-CARD-0008` mentions DOAC anticoagulation for AF; `DOC-PMC-CARD-0010` mentions RV failure). Missing Wells score, D-dimer thresholding, CTPA, thrombolysis in massive PE. | **YES** | Very High (P0 respiratory/cardiovascular intersection) | High Value. One of the highest frequency conditions on PLAB 1. | **RECOMMEND INGESTION IN WAVE 3**. |
| `DOC-PMC-RESP-0001` (reported 62 chunks) | **Asthma** | P0 | Minimal (COPD in `DOC-PMC-RESP-0003` discusses bronchodilators). Missing PEFR criteria for acute severe/life-threatening asthma, BTS/SIGN/NICE NG245 stepped chronic management, magnesium sulfate indications. | **YES** | Very High | High Value. Fundamental acute & outpatient respiratory curriculum item. | **RECOMMEND INGESTION IN WAVE 3**. |
| `DOC-PMC-RESP-0002` (reported 173 chunks) | **Pneumonia (CAP / HAP)** | P0 | Minimal. Missing CURB-65 calculation, microbiological investigation, empiric antibiotic selection, severity triage. | **YES** | Very High | High Value. High-frequency PLAB condition. | **RECOMMEND INGESTION IN WAVE 3**. |

---

## 3. Strategic Execution Plan

1. **Current Wave 2 Baseline (817 chunks):**
   - The current 13 documents provide strong, deep, verified coverage across:
     - Hypertension (227 chunks)
     - Atrial Fibrillation (42 chunks)
     - Syncope (54 chunks)
     - COPD (64 chunks)
     - Resuscitation / CPR (11 chunks)
     - Pneumothorax (58 chunks)
     - ARDS (38 chunks)
     - Cardiogenic Shock (77 chunks)
     - Infective Endocarditis (85 chunks)
     - Bradyarrhythmias / Pacing (69 chunks)
     - Aortic Stenosis (62 chunks)
     - Mitral Regurgitation (30 chunks)
2. **Current Controlled PLAB Generation Strategy:**
   - The first 30–40 question batch will be strictly generated from the **12 strongly supported topics** above.
   - Topics with evidence gaps (e.g. Asthma, PE, acute CAP, chronic HF) will be held back from question generation until Wave 3, ensuring verified evidence grounding against local corpus chunks.
3. **Wave 3 Roadmap:**
   - After completing the 817-chunk benchmark, evidence calibration, and initial 30-40 question batch, ingesting clean, open-access, CC BY 4.0 PMC sources for the 7 gaps identified above will complete full Cardiorespiratory coverage.
