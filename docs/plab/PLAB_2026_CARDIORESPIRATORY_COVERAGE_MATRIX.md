# PLAB 2026 Cardiorespiratory Coverage Matrix

**Status:** verified against the current GMC MLA content map applicable to assessments from **September 2026 onward**.  
**Verified on:** 2026-09-09  
**Purpose:** product coverage blueprint for MedicalPlab PLAB, RAG, clinical-reasoning and anatomy work.  

## Truth boundary

The GMC MLA content map is the official exam-content framework. MedicalPlab priorities (`P0`, `P1`, `P2`) are **product priorities**, not GMC weightings. The current GMC map is organised into six domains and explicitly connects domains rather than prescribing isolated topic silos. GMC uses acute coronary syndromes as an example: candidates are expected to understand coronary anatomy, interpret signs/symptoms in context, and formulate a prioritised differential diagnosis to guide management.

PLAB is MLA-compliant: PLAB 1 maps to the MLA AKT requirements and PLAB 2 maps to the MLA CPSA requirements. The current content map provides the framework for both. This file therefore does **not** claim that every topic below is guaranteed to appear in PLAB 1 or PLAB 2, nor does it assign unofficial exam weights.

## Official current MLA anchors

- Current content map: https://www.gmc-uk.org/education/medical-licensing-assessment/mla-content-map
- PLAB and MLA: https://www.gmc-uk.org/education/medical-licensing-assessment/plab-and-the-mla
- PLAB 1 preparation resources: https://www.gmc-uk.org/registration-and-licensing/join-our-registers/plab/plab-1-guide/what-resources-should-you-use-to-prepare
- PLAB 1 official sample questions: https://www.gmc-uk.org/registration-and-licensing/join-our-registers/plab/plab-1-guide/sample-questions

The GMC states that the current map applies from September 2026 onward and is a live document. MedicalPlab must re-check it before future large question-generation runs.

---

## Coverage-state legend

- `LOCAL_VALIDATED_REPORTED` — previous Codex workspace report states a licence-safe local document was ingested and passed the repository pipeline; the raw/processed `Data/` artifacts are intentionally not in Git and have **not** been independently re-executed from this remote session.
- `PARTIAL_LOCAL_VALIDATED_REPORTED` — supporting material exists in the reported local corpus, but coverage is indirect/broader than the topic.
- `REFERENCE_ONLY` — authoritative UK source selected but not legally approved for AI/RAG ingestion.
- `GAP` — no adequate dedicated ingestible source is currently registered for the topic.

## Patient presentations relevant to the Cardiorespiratory product slice

These are official Domain 5 patient presentations. The current map is A–Z rather than rigidly mapped to a single body system, so the list below is a MedicalPlab relevance selection from the official list.

| Official patient presentation | MedicalPlab priority | Current evidence state | Next action |
|---|---:|---|---|
| Blackouts and faints | P1 | GAP | UK authority + licence-safe syncope evidence |
| Breathlessness | P0 | PARTIAL_LOCAL_VALIDATED_REPORTED | broaden dedicated acute dyspnoea evidence |
| Cardiorespiratory arrest | P0 | GAP | resuscitation authority + licence-safe evidence |
| Chest pain | P0 | PARTIAL_LOCAL_VALIDATED_REPORTED | reconcile ACS evidence with UK ground truth |
| Choking | P1 | GAP | airway/resuscitation source wave |
| Cough | P1 | PARTIAL_LOCAL_VALIDATED_REPORTED | respiratory diagnostic source wave |
| Cyanosis | P0 | PARTIAL_LOCAL_VALIDATED_REPORTED | acute deterioration source wave |
| Deteriorating patient | P0 | PARTIAL_LOCAL_VALIDATED_REPORTED | UK deterioration/resuscitation authority |
| Haemoptysis | P1 | PARTIAL_LOCAL_VALIDATED_REPORTED | dedicated respiratory differential evidence |
| Heart murmurs | P1 | GAP | valvular disease source wave |
| High blood pressure | P0 | LOCAL_VALIDATED_REPORTED | UK reconciliation + PLAB questions |
| Low blood pressure | P0 | PARTIAL_LOCAL_VALIDATED_REPORTED | shock/deterioration source wave |
| Pain on inspiration | P1 | PARTIAL_LOCAL_VALIDATED_REPORTED | PE/pneumothorax/pleural evidence expansion |
| Palpitations | P0 | GAP | arrhythmia source wave |
| Patient on anti-coagulant therapy | P1 | PARTIAL_LOCAL_VALIDATED_REPORTED | UK prescribing/safety reconciliation |
| Patient on anti-platelet therapy | P1 | PARTIAL_LOCAL_VALIDATED_REPORTED | ACS prescribing/safety reconciliation |
| Peripheral oedema and ankle swelling | P1 | PARTIAL_LOCAL_VALIDATED_REPORTED | HF/VTE/renal differential coverage |
| Pleural effusion | P1 | GAP | dedicated pleural evidence |
| Pulseless limb | P0 | GAP | acute limb ischaemia source wave |
| Shock | P0 | PARTIAL_LOCAL_VALIDATED_REPORTED | dedicated shock/resuscitation evidence |
| Stridor | P0 | GAP | airway emergency source wave |
| Swollen limb(s) | P1 | PARTIAL_LOCAL_VALIDATED_REPORTED | DVT differential + UK verification |
| Wheeze | P0 | PARTIAL_LOCAL_VALIDATED_REPORTED | asthma/COPD UK reconciliation |

---

## Domain 6 — Heart and vasculature

The following conditions are listed by GMC in the current 2026 map under **Heart and vasculature**.

| Official condition | Priority | UK ground-truth status | Ingestible support | Current MedicalPlab state | Product link |
|---|---:|---|---:|---|---|
| Acute coronary syndromes | P0 | NICE NG185 reference-only / permission required for AI | yes | LOCAL_VALIDATED_REPORTED | PLAB + Clinical + Anatomy |
| Aneurysms, ischaemic limb and occlusions | P1 | gap | no | GAP | PLAB + Clinical |
| Aortic aneurysm | P1 | gap | partial | PARTIAL_LOCAL_VALIDATED_REPORTED | PLAB + Clinical + Anatomy |
| Aortic dissection | P0 | UK authority gap in current selected set | yes | LOCAL_VALIDATED_REPORTED | PLAB + Clinical + Anatomy |
| Aortic valve disease | P1 | gap | no | GAP | PLAB + Clinical + Anatomy |
| Arterial thrombosis/embolism | P1 | gap | no | GAP | PLAB + Clinical |
| Bradyarrhythmias (including AV block) | P0 | gap | no | GAP | PLAB + Clinical |
| Cardiac arrest | P0 | gap | no | GAP | PLAB + Clinical |
| Cardiomyopathy | P1 | partial via HF sources | partial | PARTIAL_LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Carotid dissection | P2 | gap | no | GAP | PLAB |
| Congenital heart disease | P2 | gap | no | GAP | PLAB |
| Deep vein thrombosis | P1 | NICE NG158 reference-only / permission required for AI | yes | PARTIAL_LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Gangrene | P2 | gap | no | GAP | PLAB |
| Heart failure | P0 | NICE NG106 reference-only / permission required for AI | yes | LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Hypertension (essential or secondary) | P0 | NICE NG136 reference-only / permission required for AI | yes | LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Infective endocarditis | P1 | gap | no | GAP | PLAB + Clinical |
| Ischaemic heart disease (including stable angina) | P0 | partial UK ACS spine | partial | PARTIAL_LOCAL_VALIDATED_REPORTED | PLAB + Clinical + Anatomy |
| Mitral valve disease | P1 | gap | no | GAP | PLAB + Clinical + Anatomy |
| Myocarditis | P1 | gap | no | GAP | PLAB + Clinical |
| Orthostatic/postural hypotension | P1 | partial via hypertension guidance | no dedicated | GAP | PLAB + Clinical |
| Pericardial disease (including pericarditis, pericardial effusion, cardiac tamponade) | P0 | UK authority gap in current selected set | yes | LOCAL_VALIDATED_REPORTED | PLAB + Clinical + Anatomy |
| Peripheral vascular disease | P1 | gap | no | GAP | PLAB + Clinical |
| Pulmonary embolism | P0 | NICE NG158 reference-only / permission required for AI | yes | LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Pulmonary hypertension | P1 | partial | partial | PARTIAL_LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Right heart valve disease | P1 | gap | no | GAP | PLAB + Clinical + Anatomy |
| Shock | P0 | gap | partial | PARTIAL_LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Superior vena cava obstruction | P2 | gap | no | GAP | PLAB + Clinical |
| Syncope (including vasovagal, cardiac) | P0 | gap | no | GAP | PLAB + Clinical |
| Tachyarrhythmias (including AF, atrial flutter, SVT, torsades, VT, VF) | P0 | gap | no | GAP | PLAB + Clinical |
| Venous insufficiency (including varicose veins) | P2 | gap | no | GAP | PLAB |

---

## Domain 6 — Lungs, pleura and airways

The following conditions are listed by GMC in the current 2026 map under **Lungs, pleura and airways**.

| Official condition | Priority | UK ground-truth status | Ingestible support | Current MedicalPlab state | Product link |
|---|---:|---|---:|---|---|
| Acute bronchitis | P1 | gap | partial | PARTIAL_LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Acute respiratory distress syndrome (ARDS) | P0 | gap | no | GAP | PLAB + Clinical |
| Asthma | P0 | NICE/BTS/SIGN NG245 reference-only / permission required for AI | yes | LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Asthma-COPD overlap | P1 | NICE asthma + COPD references only | partial | PARTIAL_LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Bronchiectasis | P1 | gap | no | GAP | PLAB + Clinical |
| Chronic obstructive pulmonary disease (COPD) | P0 | NICE NG115 reference-only / permission required for AI | no dedicated selected source | GAP | PLAB + Clinical |
| Empyema | P1 | partial via pneumonia | partial | PARTIAL_LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Interstitial lung disease (including fibrotic lung disease) | P2 | gap | no | GAP | PLAB + Clinical |
| Lower respiratory tract infection | P1 | NICE NG250 partial spine | yes | PARTIAL_LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Lung abscess | P2 | gap | no | GAP | PLAB + Clinical |
| Lung cancer | P1 | gap | no | GAP | PLAB + Clinical |
| Obstructive sleep apnoea | P2 | gap | no | GAP | PLAB |
| Occupational lung disease | P2 | gap | no | GAP | PLAB |
| Pleural effusion | P1 | gap | no dedicated | GAP | PLAB + Clinical |
| Pneumonia | P0 | NICE NG250 reference-only / permission required for AI | yes | LOCAL_VALIDATED_REPORTED | PLAB + Clinical |
| Pneumothorax | P0 | gap | no | GAP | PLAB + Clinical |
| Respiratory arrest | P0 | gap | no | GAP | PLAB + Clinical |
| Respiratory failure | P0 | gap | no | GAP | PLAB + Clinical |
| Sarcoidosis | P2 | gap | no | GAP | PLAB + Clinical |

---

## P0 acquisition wave after the current 8-source checkpoint

The next source wave should close the highest-risk gaps before broad question generation:

1. Tachyarrhythmias / AF / SVT / VT / VF
2. Bradyarrhythmias / AV block
3. Cardiac arrest and cardiorespiratory arrest
4. Syncope
5. COPD (dedicated commercial-compatible evidence)
6. Pneumothorax
7. Respiratory failure / ARDS
8. Shock / deteriorating patient
9. Valvular disease (aortic + mitral)
10. Infective endocarditis

## Question-generation readiness

**Ready for a controlled first batch, not ready for broad Cardiorespiratory completion.**

The reported local corpus has dedicated licence-safe supporting evidence for ACS, hypertension, heart failure, aortic dissection, pericardial disease/tamponade, PE, asthma and pneumonia. These topics may enter a **small evidence-backed PLAB question-generation wave only after UK-ground-truth reconciliation**. NICE references must remain reference/verification sources unless MedicalPlab receives explicit AI reuse permission/licensing.

The next broad Cardiorespiratory batch must wait until the P0 gaps above have dedicated sources.
