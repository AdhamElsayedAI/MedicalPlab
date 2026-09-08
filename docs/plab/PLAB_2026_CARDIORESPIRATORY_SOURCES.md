# PLAB 2026 Cardiorespiratory Sources

**Status:** curated source set continued from the Codex checkpoint and independently re-checked where web-verifiable on 2026-09-09.

## Selection policy

MedicalPlab separates four roles:

1. **Exam blueprint** — defines PLAB/MLA scope and style.
2. **UK clinical ground truth** — authoritative current UK best-practice verification.
3. **Commercial-compatible supporting evidence** — material that can enter the RAG/question-generation corpus.
4. **Evaluation-only** — official samples/benchmarks used to calibrate style or evaluate, never copied into the production question bank.

Authority is not permission. A highly authoritative source may remain `REFERENCE_ONLY` or `PERMISSION_REQUIRED` for AI use.

## Licence classifications

- `INGEST_ALLOWED` — licence verified as compatible with the intended commercial RAG/question-generation use, subject to attribution/terms.
- `REFERENCE_ONLY` — may be used as an external authoritative reference but not bulk-ingested into the AI corpus under the currently verified terms.
- `PERMISSION_REQUIRED` — explicit permission/licensing required before AI ingestion or derived AI use.
- `EVALUATION_ONLY` — used only for calibration/evaluation, not training/question-bank ingestion.
- `BLOCKED` — deliberately excluded.
- `NOT_VERIFIED` — insufficient evidence to make a safe licensing claim.

## Selected source set

| ID | Exact title | Organization | Role | Licence class | RAG | Q-gen | Main coverage |
|---|---|---|---|---|---|---|---|
| SRC-GMC-MLA-2026 | MLA content map | General Medical Council | blueprint | REFERENCE_ONLY | no | no | official MLA/PLAB scope |
| SRC-GMC-PLAB1-GUIDE | PLAB 1 guide | General Medical Council | blueprint | REFERENCE_ONLY | no | no | PLAB 1 format/resources |
| SRC-GMC-PLAB1-SAMPLES-2024 | Sample questions for PLAB 1 | General Medical Council | evaluation | EVALUATION_ONLY | no | no | SBA style/calibration |
| SRC-NICE-NG185 | Acute coronary syndromes | NICE | uk_ground_truth | PERMISSION_REQUIRED | no | no | ACS/STEMI/NSTEMI |
| SRC-NICE-NG106 | Chronic heart failure in adults: diagnosis and management | NICE | uk_ground_truth | PERMISSION_REQUIRED | no | no | heart failure |
| SRC-NICE-NG136 | Hypertension in adults: diagnosis and management | NICE | uk_ground_truth | PERMISSION_REQUIRED | no | no | hypertension |
| SRC-NICE-NG158 | Venous thromboembolic diseases: diagnosis, management and thrombophilia testing | NICE | uk_ground_truth | PERMISSION_REQUIRED | no | no | DVT/PE |
| SRC-NICE-NG245 | Asthma: diagnosis, monitoring and chronic asthma management (BTS, NICE, SIGN) | NICE | uk_ground_truth | PERMISSION_REQUIRED | no | no | asthma |
| SRC-NICE-NG115 | Chronic obstructive pulmonary disease in over 16s: diagnosis and management | NICE | uk_ground_truth | PERMISSION_REQUIRED | no | no | COPD |
| SRC-NICE-NG250 | Pneumonia: diagnosis and management | NICE | uk_ground_truth | PERMISSION_REQUIRED | no | no | pneumonia |
| SRC-PMC-CARD-HTN-001 | Outpatient management of essential hypertension: a review based on the latest clinical guidelines | Annals of Medicine | supporting_evidence | INGEST_ALLOWED | yes | yes | hypertension |
| SRC-PMC-CARD-HF-001 | Pharmacological Treatment of Heart Failure: Recent Advances | Current Cardiology Reviews | supporting_evidence | INGEST_ALLOWED | yes | yes | heart failure |
| SRC-PMC-CARD-ACS-001 | Pathophysiology of Acute Coronary Syndromes—Diagnostic and Treatment Considerations | Life | supporting_evidence | INGEST_ALLOWED | yes | yes | ACS/STEMI/NSTEMI/CAD |
| SRC-PMC-CARD-AORTA-001 | Changing Management of Type B Aortic Dissections | Methodist DeBakey Cardiovascular Journal | supporting_evidence | INGEST_ALLOWED | yes | yes | type B aortic dissection |
| SRC-PMC-CARD-PERICARD-001 | Diagnosis, treatment, and management of pericardial effusion-review | Annals of Medicine and Surgery | supporting_evidence | INGEST_ALLOWED | yes | yes | pericardial effusion/tamponade |
| SRC-PMC-CARD-PE-001 | Decoding Pulmonary Embolism: Pathophysiology, Diagnosis, and Treatment | Biomedicines | supporting_evidence | INGEST_ALLOWED | yes | yes | pulmonary embolism |
| SRC-PMC-RESP-ASTHMA-001 | Clinical standards for the diagnosis and management of asthma in low- and middle-income countries | The International Journal of Tuberculosis and Lung Disease | supporting_evidence | INGEST_ALLOWED | yes | yes | asthma support |
| SRC-PMC-RESP-PNA-001 | Ten Issues for Updating in Community-Acquired Pneumonia: An Expert Review | Journal of Clinical Medicine | supporting_evidence | INGEST_ALLOWED | yes | yes | pneumonia |

## Canonical URLs

### GMC

- MLA content map: https://www.gmc-uk.org/education/medical-licensing-assessment/mla-content-map
- PLAB 1 guide: https://www.gmc-uk.org/registration-and-licensing/join-our-registers/plab/plab-1-guide
- PLAB 1 sample questions: https://www.gmc-uk.org/registration-and-licensing/join-our-registers/plab/plab-1-guide/sample-questions

### NICE

- NG185: https://www.nice.org.uk/guidance/ng185
- NG106: https://www.nice.org.uk/guidance/ng106
- NG136: https://www.nice.org.uk/guidance/ng136
- NG158: https://www.nice.org.uk/guidance/ng158
- NG245: https://www.nice.org.uk/guidance/ng245
- NG115: https://www.nice.org.uk/guidance/ng115
- NG250: https://www.nice.org.uk/guidance/ng250
- NICE AI/content reuse terms: https://www.nice.org.uk/reusing-our-content/nice-uk-open-content-licence

### PMC supporting evidence

- Hypertension: https://pmc.ncbi.nlm.nih.gov/articles/PMC11011233/
- Heart failure: https://pmc.ncbi.nlm.nih.gov/articles/PMC11107472/
- ACS: https://pmc.ncbi.nlm.nih.gov/articles/PMC10381786/
- Aortic dissection: https://pmc.ncbi.nlm.nih.gov/articles/PMC10000326/
- Pericardial effusion: https://pmc.ncbi.nlm.nih.gov/articles/PMC9283797/
- Pulmonary embolism: https://pmc.ncbi.nlm.nih.gov/articles/PMC11428250/
- Asthma standards: https://pmc.ncbi.nlm.nih.gov/articles/PMC10443788/
- Pneumonia review: https://pmc.ncbi.nlm.nih.gov/articles/PMC10649000/

## Licensing outcome

| Classification | Count |
|---|---:|
| INGEST_ALLOWED | 8 |
| REFERENCE_ONLY | 2 |
| PERMISSION_REQUIRED | 7 |
| EVALUATION_ONLY | 1 |
| BLOCKED | 0 |
| NOT_VERIFIED | 0 in this selected checkpoint set |

NICE is deliberately excluded from the production RAG corpus. Current NICE reuse terms require separate permission/licensing for AI uses; MedicalPlab must not treat the demo's hard-coded NICE material as production evidence.

The eight PMC items were selected because the prior Codex acquisition pass reported their article JATS licence nodes as **CC BY 4.0**. The machine-readable registry preserves that claim and the article URL; when the local ingestion workspace becomes available again, the exact stored JATS licence node should be re-audited against the immutable raw file before release.

## Ingestion checkpoint from the previous Codex workspace

The previous Codex run reported that all eight ingestible articles were acquired as JATS XML and passed the repository's existing inspect → extract → canonical adapt → chunk → schema validate → integrity path. These `Data/` artifacts are intentionally gitignored and are not available in this remote GitHub session, so the following results are preserved as **reported checkpoint evidence, not independently rerun evidence**.

| Document | Coverage | Reported SHA-256 | Sections | Chunks | Reported validation |
|---|---|---|---:|---:|---|
| DOC-PMC-CARD-0002 | Hypertension | 9cf9c9059958dd7d1958ca447b1fe3990f23ff857ac8fc1f1b067214648eb6e2 | 22 | 144 | PASS |
| DOC-PMC-CARD-0003 | Heart failure | 6be241039a806f5f3498d54ea3666727d98a96d66be1b5791bf8ea6adca76978 | 30 | 88 | PASS |
| DOC-PMC-CARD-0004 | ACS/STEMI/NSTEMI/CAD | 0c251c8d3fd65ad18677b2a1878fb5771722bface5ce3b001ada11712f2ef43d | 16 | 34 | PASS |
| DOC-PMC-CARD-0005 | Type B aortic dissection | c8f81e8c88edd80ba8dcbf4e9757d34a977dd3826836ab519aee4c6464114b6b | 18 | 49 | PASS |
| DOC-PMC-CARD-0006 | Pericardial effusion/tamponade | ff769b7569cdeb8437280533602f814c0b6df8d4c0e790a9f7c1e5581db88ca0 | 13 | 44 | PASS |
| DOC-PMC-CARD-0007 | Pulmonary embolism | 6180930c27a8100efb629e3959ebf3857d0cec0ab01bc68229ad7d8fa5a8740a | 42 | 108 | PASS |
| DOC-PMC-RESP-0001 | Asthma | 84d74cdb3130f92acdc46e60bf763c67e97aab18f91ab030511b2852db5e2778 | 31 | 62 | PASS |
| DOC-PMC-RESP-0002 | Pneumonia | 433fd5d0e4d263d4d8eb1b19c2e4b648127abf3cbaaf22edee849eb19028eccd | 30 | 173 | PASS |

**Reported total: 702 chunks.**

## Known clinical caveats

- The hypertension review compares several guidelines and is not itself a UK prescribing authority.
- The heart-failure review is supporting evidence, not a substitute for current UK guideline verification.
- The aortic article focuses on **type B** aortic dissection; MedicalPlab must not generalise it to all dissection management without additional evidence.
- The asthma article is written for low- and middle-income-country standards; it is useful supporting evidence but must be reconciled with current UK asthma guidance before any PLAB answer is accepted.
- PMC reviews support pathophysiology/evidence, but current UK management recommendations must be reconciled against current authoritative UK sources.

## Highest-priority next acquisition wave

1. AF / atrial flutter / SVT / VT / VF / torsades
2. Bradyarrhythmias / AV block
3. Cardiac arrest / cardiorespiratory arrest
4. Syncope
5. COPD dedicated supporting evidence
6. Pneumothorax
7. Respiratory failure / ARDS
8. Shock / deteriorating patient
9. Aortic + mitral valve disease
10. Infective endocarditis

Broad Cardiorespiratory PLAB generation should not be declared complete until these P0 gaps have a defensible UK-reference + commercial-compatible evidence pairing.
