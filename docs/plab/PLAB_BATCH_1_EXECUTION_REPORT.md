# MedicalPlab Cardiorespiratory PLAB 1 SBA Batch 1 Execution Report

**Batch Identifier:** `cardiorespiratory_batch_1_v1`  
**Date:** 2026-09-09  
**Branch:** `ai-data-execution-v1`  
**Status:** **AUTOMATED VALIDATION PASSED — PENDING CLINICAL HUMAN REVIEW** ⏳  
**Corpus Baseline:** `medicalplab-cardiorespiratory-corpus-v1` (13 documents, 817 chunks)  
**Total Questions Generated & Validated:** 36 questions  
**Batch Output File:** [`Data/questions/cardiorespiratory_batch_1.json`](file:///c:/Users/Adham%20Elsayed/Downloads/MedicalPlab-dev/MedicalPlab-dev/Data/questions/cardiorespiratory_batch_1.json)  
**Automated Test Suite:** [`tests/plab/test_cardiorespiratory_batch_1.py`](file:///c:/Users/Adham%20Elsayed/Downloads/MedicalPlab-dev/MedicalPlab-dev/tests/plab/test_cardiorespiratory_batch_1.py) (4/4 tests passing)

---

## 1. Executive Summary

This report documents the generation, automated contract validation, and initial evidence-linkage verification of the first **Cardiorespiratory Single Best Answer (SBA) question batch** for MedicalPlab. 
All 36 questions were developed to conform to the GMC PLAB 1 / UK MLA five-option single-best-answer format and were verified against locally cached chunks from the frozen 817-chunk cardiorespiratory corpus snapshot.

Key Validation Milestones:
1. **12 Mapped UK Topics Covered:** Exactly 3 single-best-answer questions per topic across all 12 topics verified in [`PLAB_UK_GROUND_TRUTH_12_TOPIC_GATE.md`](file:///c:/Users/Adham%20Elsayed/Downloads/MedicalPlab-dev/MedicalPlab-dev/docs/plab/PLAB_UK_GROUND_TRUTH_12_TOPIC_GATE.md).
2. **PLAB 1 Contract Adherence:** Every question contains exactly five choices (A, B, C, D, E), a single best answer pointer, distinct distractor texts, a clinical vignette stem (>=8 words), and a detailed educational explanation (>=8 words).
3. **Automated Evidence Linkage (36/36 PASS):** 36/36 questions passed automated evidence-linkage validation with exact verbatim citation matching against the 817-chunk local corpus snapshot. Exact citation matching confirms evidence linkage; it does not substitute for independent clinical review.
4. **UK Clinical Authority Reconciliation:** Structured clinical propositions were cross-referenced against authoritative UK clinical references (NICE, RCUK, BTS, FICM, and BSAC).
5. **Balanced Answer Key Distribution:** Designed to prevent option-position bias:
   - **A:** 8 (22.2%)
   - **B:** 7 (19.4%)
   - **C:** 7 (19.4%)
   - **D:** 7 (19.4%)
   - **E:** 7 (19.4%)

---

## 2. Topic Distribution & Evidence Attribution Matrix

| # | Topic | Questions | Specialty | Supporting Document(s) | Primary Cited Chunk(s) | UK Clinical Authority / Reference | Key Clinical Reconciliation Point |
|---|---|---|---|---|---|---|---|
| 1 | **Hypertension (Essential & Secondary)** | `PLAB-CARD-0001`<br>`PLAB-CARD-0002`<br>`PLAB-CARD-0003` | Cardiology | `DOC-WHO-CARD-0001`<br>`DOC-PMC-CARD-0002` | `DOC-WHO-CARD-0001-B0001-C01`<br>`DOC-PMC-CARD-0002-B0003-C01`<br>`DOC-WHO-CARD-0001-B0001-C03` | NICE NG136 | Step 1 CCB for age >=55 or Black-African/Caribbean; aldosterone/renin ratio for suspected Conn's with hypokalemia; Step 2 ACEi+CCB combination. |
| 2 | **Atrial Fibrillation** | `PLAB-CARD-0004`<br>`PLAB-CARD-0005`<br>`PLAB-CARD-0006` | Cardiology | `DOC-PMC-CARD-0008` | `DOC-PMC-CARD-0008-B0015-C01`<br>`DOC-PMC-CARD-0008-B0018-C01`<br>`DOC-PMC-CARD-0008-B0011-C01` | NICE NG196 | CHA2DS2-VASc score determines DOAC indication (score >=1 men, >=2 women); standard beta-blockers 1st-line rate control; smoking/alcohol lifestyle intervention reduces recurrence. |
| 3 | **Syncope & Transient Loss of Consciousness** | `PLAB-CARD-0007`<br>`PLAB-CARD-0008`<br>`PLAB-CARD-0009` | Cardiology | `DOC-PMC-CARD-0009` | `DOC-PMC-CARD-0009-B0009-C01`<br>`DOC-PMC-CARD-0009-B0010-C01`<br>`DOC-PMC-CARD-0009-B0020-C01` | NICE CG109 | Orthostatic hypotension criteria (>=20 mmHg drop); red flags (exertional syncope, FHx sudden death <40 yrs, abnormal ECG) mandate urgent specialist referral; carotid sinus syndrome (asystole >3s or BP drop >50 mmHg). |
| 4 | **Chronic Obstructive Pulmonary Disease (COPD)** | `PLAB-RESP-0001`<br>`PLAB-RESP-0002`<br>`PLAB-RESP-0003` | Respiratory Medicine | `DOC-PMC-RESP-0003` | `DOC-PMC-RESP-0003-B0020-C01`<br>`DOC-PMC-RESP-0003-B0022-C01`<br>`DOC-PMC-RESP-0003-B0010-C01` | NICE NG115 / BTS | Controlled oxygen target 88–92% via 24/28% Venturi mask for acute hypercapnic risk; LABA+LAMA dual bronchodilator for non-asthmatic breathless COPD; blood eosinophils (>300 cells/uL) guide ICS escalation. |
| 5 | **Cardiopulmonary Resuscitation & Cardiac Arrest** | `PLAB-EMERG-0001`<br>`PLAB-EMERG-0002`<br>`PLAB-EMERG-0003` | Emergency Medicine | `DOC-PMC-EMERG-0001` | `DOC-PMC-EMERG-0001-B0001-C01`<br>`DOC-PMC-EMERG-0001-B0002-C01`<br>`DOC-PMC-EMERG-0001-B0005-C01` | RCUK ALS 2021/2025 | Adrenaline 1 mg IV and amiodarone 300 mg IV post-3rd shock in VF/pVT; high-quality compression metrics (rate 100-120/min, depth 5-6 cm, full recoil); post-ROSC targeted temperature management avoiding fever. |
| 6 | **Pneumothorax** | `PLAB-RESP-0004`<br>`PLAB-RESP-0005`<br>`PLAB-RESP-0006` | Respiratory Medicine | `DOC-PMC-RESP-0004` | `DOC-PMC-RESP-0004-B0001-C01`<br>`DOC-PMC-RESP-0004-B0004-C01`<br>`DOC-PMC-RESP-0004-B0030-C01` | BTS Pleural Statement 2023 | Conservative observation in stable primary spontaneous pneumothorax regardless of size; male predominance and smoking/apical blebs; landmark trial (Brown et al. NEJM 2020) non-inferiority for observation. |
| 7 | **Acute Respiratory Distress Syndrome (ARDS)** | `PLAB-RESP-0007`<br>`PLAB-RESP-0008`<br>`PLAB-RESP-0009` | Respiratory Medicine | `DOC-PMC-RESP-0005` | `DOC-PMC-RESP-0005-B0014-C01`<br>`DOC-PMC-RESP-0005-B0027-C01`<br>`DOC-PMC-RESP-0005-B0025-C01` | FICM / ICS | Berlin criteria definition and severity by PaO2/FiO2 ratio (severe <=100 mmHg); lung-protective ventilation (tidal volume 4-6 mL/kg PBW, plateau pressure <30 cmH2O); prone positioning >=16 hours/day for PaO2/FiO2 <150 mmHg. |
| 8 | **Cardiogenic Shock** | `PLAB-CARD-0010`<br>`PLAB-CARD-0011`<br>`PLAB-CARD-0012` | Cardiology | `DOC-PMC-CARD-0010` | `DOC-PMC-CARD-0010-B0041-C01`<br>`DOC-PMC-CARD-0010-B0042-C01`<br>`DOC-PMC-CARD-0010-B0023-C01` | NICE NG185 / BCS | Norepinephrine is 1st-line vasopressor (lower arrhythmia risk than dopamine); dobutamine is 1st-line inotrope for low cardiac output; emergent coronary revascularisation (primary PCI) is the cornerstone mortality-reducing intervention. |
| 9 | **Infective Endocarditis (IE)** | `PLAB-CARD-0013`<br>`PLAB-CARD-0014`<br>`PLAB-CARD-0015` | Cardiology | `DOC-PMC-CARD-0011` | `DOC-PMC-CARD-0011-B0032-C01`<br>`DOC-PMC-CARD-0011-B0012-C01`<br>`DOC-PMC-CARD-0011-B0020-C01` | BSAC / NICE CG64 | 3 sets of blood cultures prior to antibiotics satisfy major Duke criterion; TEE indicated for prosthetic valves or suspected complications; UK NICE CG64 explicitly advises against routine antibiotic prophylaxis for dental procedures. |
| 10 | **Bradyarrhythmias & Conduction Blocks** | `PLAB-CARD-0016`<br>`PLAB-CARD-0017`<br>`PLAB-CARD-0018` | Cardiology | `DOC-PMC-CARD-0012` | `DOC-PMC-CARD-0012-B0002-C01`<br>`DOC-PMC-CARD-0012-B0003-C01`<br>`DOC-PMC-CARD-0012-B0006-C01` | RCUK / NICE | Atropine 500 mcg IV initial therapy for symptomatic bradycardia with adverse features; pacing-induced cardiomyopathy due to RV apical pacing dyssynchrony; His-bundle pacing reduces HF hospitalisations and new AF. |
| 11 | **Aortic Stenosis (Valvular Heart Disease)** | `PLAB-CARD-0019`<br>`PLAB-CARD-0020`<br>`PLAB-CARD-0021` | Cardiology | `DOC-PMC-CARD-0013` | `DOC-PMC-CARD-0013-B0001-C01`<br>`DOC-PMC-CARD-0013-B0002-C01`<br>`DOC-PMC-CARD-0013-B0029-C03` | NICE NG208 | Classic presentation triad (angina, syncope, dyspnea) with slow-rising pulse and murmur radiating to carotids; severe AS criteria (Vmax >=4 m/s, mean gradient >=40 mmHg, AVA <1.0 cm2); MDCT is reference technique for TAVI planning. |
| 12 | **Functional Mitral Regurgitation** | `PLAB-CARD-0022`<br>`PLAB-CARD-0023`<br>`PLAB-CARD-0024` | Cardiology | `DOC-PMC-CARD-0014` | `DOC-PMC-CARD-0014-B0002-C01`<br>`DOC-PMC-CARD-0014-B0001-C01`<br>`DOC-PMC-CARD-0014-B0022-C01` | NICE NG208 / NG106 | Pathophysiology (LV remodeling with morphologically normal leaflets); guideline-directed medical therapy for HFrEF is mandatory first-line; recurrent MR is the principal long-term challenge of annuloplasty repair. |

---

## 3. Difficulty Breakdown

- **Easy:** 10 questions (27.8%) — Core foundational knowledge, first-line drug selection, classic diagnostic criteria.
- **Medium:** 19 questions (52.8%) — Stepped-care algorithms, risk calculation (CHA2DS2-VASc), imaging modality selection, acute emergency interventions.
- **Hard:** 7 questions (19.4%) — Refractory scenarios (severe ARDS prone positioning, treatable trait phenotyping, trial evidence interpretation, physiological pacing).

---

## 4. Verification & Automated Test Results

The generated batch was subjected to two levels of automated testing:
1. **Script Validation:** `Scripts/generate_cardiorespiratory_plab_batch1.py` executes `validate_plab_question` across all 36 questions with exact evidence texts retrieved directly from the corpus snapshot. Result: **36/36 PASS**.
2. **Automated Unit Testing:** `pytest tests/plab/test_cardiorespiratory_batch_1.py` runs a 4-test suite checking metadata, complete 12-topic coverage, balanced answer keys, and end-to-end evidence grounding. Result: **4/4 PASS** in 0.08s.

The question batch has passed all automated contract and evidence-linkage validation checks and is now queued for independent human medical review. It is NOT yet approved as Golden.

