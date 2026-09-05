# MedicalPlab Evidence Sufficiency Negative-Label Adjudication v1

**Status:** manual full-corpus adjudication complete

- Calibration SHA-256: `4ece4e35de1f46888f75f4dcae624e34b8e8f2696959f162a5f434615b021ad5`
- Candidate JSON SHA-256: `0b2e3a225829a6c2774e03c633aba200e0cb98377a833491c524d60a978be6ff`
- Candidate Markdown SHA-256: `50f6e20c2264d0c01c4ec560c6defb34d0d4f74a889d95ae393a677c51908d08`
- Corpus reviewed: `227` chunks / `192` unique source blocks
- Cases reviewed: `28` (`12` partial + `16` unsupported)

## Final outcome

- `28/28` final labels confirmed.
- `27/28` confirmed without change.
- `ESCAL-V1-042` was rewritten during round-1 adjudication and then confirmed.
- Final relabels: `0`.
- Final removals: `0`.

The calibration set is now suitable for retrieval-only evidence-sufficiency baseline experiments. It remains a **calibration set**, not an independent frozen test set.

## Review method

Each partial/unsupported case was reviewed against semantic candidates, lexical candidates, required-source candidates, and the complete full-corpus block appendix. Embedding similarity was used only to surface evidence and was not treated as proof of support or absence.

## Case adjudications

### ESCAL-V1-002 — partial / multi_claim_partial

**Verdict:** `CONFIRMED`

**Query:** إزاي WHO قسمت درجات أهمية الـoutcomes من 1 لـ9، وكمان إيه الـmean score المحدد للـmortality في Annex 3؟

**Rationale:** CONFIRMED partial after manual full-corpus review. The labeled supporting block(s) DOC-WHO-CARD-0001:B0005 support the available part of the request, while the material missing component remains unsupported: The evidence catalog does not provide the exact Annex 3 mean score assigned to mortality.

### ESCAL-V1-003 — unsupported / exact_fact_absent

**Verdict:** `CONFIRMED`

**Query:** What exact mean importance score did the WHO guideline assign to mortality in Annex 3?

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: The catalog says mean scores are in Annex 3 but does not expose the exact mortality mean score.

### ESCAL-V1-005 — partial / multi_claim_partial

**Verdict:** `CONFIRMED`

**Query:** Which organizations funded development of the WHO hypertension guideline, and what percentage of the budget came from each one?

**Rationale:** CONFIRMED partial after manual full-corpus review. The labeled supporting block(s) DOC-WHO-CARD-0001:B0009 support the available part of the request, while the material missing component remains unsupported: The catalog does not provide the percentage or amount contributed by either funder.

### ESCAL-V1-006 — unsupported / exact_fact_absent

**Verdict:** `CONFIRMED`

**Query:** What exact percentage of the guideline-development budget was paid by the US CDC versus WHO?

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: No funding-share percentages or amounts are present in the evidence catalog.

### ESCAL-V1-008 — partial / multi_claim_partial

**Verdict:** `CONFIRMED`

**Query:** WHO بتقول نبدأ علاج الضغط خلال 4 أسابيع، لكن لو الضغط عالي جدًا أو فيه end-organ damage فإيه العدد الدقيق للساعات المسموح بيها قبل أول جرعة؟

**Rationale:** CONFIRMED partial after manual full-corpus review. The labeled supporting block(s) DOC-WHO-CARD-0001:B0013 support the available part of the request, while the material missing component remains unsupported: WHO says 'without delay' but the catalog does not specify an exact hour limit to first dose.

### ESCAL-V1-009 — unsupported / exact_fact_absent

**Verdict:** `CONFIRMED`

**Query:** What exact maximum number of hours does WHO allow between diagnosis and the first antihypertensive dose when end-organ damage is present?

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: The catalog contains the qualitative instruction 'without delay' but no exact number of hours.

### ESCAL-V1-011 — partial / multi_claim_partial

**Verdict:** `CONFIRMED`

**Query:** WHO suggests electrolytes, creatinine, lipids, glucose/HbA1c, urine dipstick and ECG؛ طيب إيه الـrepeat interval المحدد لكل test بعد بدء العلاج؟

**Rationale:** CONFIRMED partial after manual full-corpus review. The labeled supporting block(s) DOC-WHO-CARD-0001:B0018 support the available part of the request, while the material missing component remains unsupported: The catalog does not specify an exact repeat interval for each listed test after treatment starts.

### ESCAL-V1-012 — unsupported / exact_fact_absent

**Verdict:** `CONFIRMED`

**Query:** ما الجدول الزمني الدقيق الذي تحدده WHO لإعادة HbA1c وECG بعد بدء علاج ارتفاع الضغط؟

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: No exact post-initiation repeat schedule for HbA1c or ECG is provided in the catalog.

### ESCAL-V1-014 — partial / multi_claim_partial

**Verdict:** `CONFIRMED`

**Query:** WHO allows CVD risk assessment at or after treatment starts; what numeric coefficient does its risk equation assign to smoking?

**Rationale:** CONFIRMED partial after manual full-corpus review. The labeled supporting block(s) DOC-WHO-CARD-0001:B0022, DOC-WHO-CARD-0001:B0023 support the available part of the request, while the material missing component remains unsupported: No numeric smoking coefficient for a WHO risk equation is present in the catalog.

### ESCAL-V1-015 — unsupported / exact_fact_absent

**Verdict:** `CONFIRMED`

**Query:** In the WHO CVD risk equation, smoking بياخد coefficient رقمه كام بالضبط؟

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: The evidence catalog discusses risk assessment but provides no equation coefficient for smoking.

### ESCAL-V1-017 — partial / source_constraint_miss

**Verdict:** `CONFIRMED`

**Query:** إيه الـ3 first-line classes في WHO، وكمان إيه الـmaximum daily dose للـlisinopril حسب recommendation 3.4 نفسها؟

**Rationale:** CONFIRMED partial after manual full-corpus review. The labeled supporting block(s) DOC-WHO-CARD-0001:B0027 support the available part of the request, while the material missing component remains unsupported: The WHO recommendation block does not provide an exact lisinopril maximum daily dose; the catalog's lisinopril dose information is from the PMC review instead.

### ESCAL-V1-018 — unsupported / source_constraint_miss

**Verdict:** `CONFIRMED`

**Query:** According to WHO recommendation 3.4 specifically, what is the exact maximum daily lisinopril dose?

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: The requested source-specific dose is absent from the WHO recommendation evidence in the catalog; dose-table support belongs to the PMC review.

### ESCAL-V1-020 — partial / multi_claim_partial

**Verdict:** `CONFIRMED`

**Query:** WHO prefers a single-pill combination for many patients; which exact commercial brand and manufacturer does the guideline recommend?

**Rationale:** CONFIRMED partial after manual full-corpus review. The labeled supporting block(s) DOC-WHO-CARD-0001:B0032 support the available part of the request, while the material missing component remains unsupported: The evidence catalog does not name a preferred commercial brand or manufacturer.

### ESCAL-V1-021 — unsupported / out_of_corpus

**Verdict:** `CONFIRMED`

**Query:** ما الاسم التجاري والشركة المصنعة للـsingle-pill combination التي تختارها WHO كمنتج مفضل؟

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: No commercial brand or manufacturer is named in the evidence catalog.

### ESCAL-V1-023 — partial / multi_claim_partial

**Verdict:** `CONFIRMED`

**Query:** WHO says high-risk HTN with CKD should target SBP below 130؛ what exact DBP target does the same recommendation give for that high-risk group?

**Rationale:** CONFIRMED partial after manual full-corpus review. The labeled supporting block(s) DOC-WHO-CARD-0001:B0037 support the available part of the request, while the material missing component remains unsupported: The catalog does not provide an exact diastolic target for the high-risk group in the WHO recommendation.

### ESCAL-V1-024 — unsupported / wrong_population

**Verdict:** `CONFIRMED`

**Query:** According to this WHO adult hypertension guideline, what exact blood-pressure target is recommended for a 10-year-old child with chronic kidney disease?

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: The WHO corpus guideline is scoped to pharmacological treatment of hypertension in adults and does not provide a BP target for a 10-year-old child with chronic kidney disease.

### ESCAL-V1-026 — partial / multi_claim_partial

**Verdict:** `CONFIRMED`

**Query:** WHO بتقول monthly follow-up لحد ما المريض يوصل للـtarget؛ كام زيارة متتالية لازم يكون فيها controlled قبل التحويل لـ3–6 months؟

**Rationale:** CONFIRMED partial after manual full-corpus review. The labeled supporting block(s) DOC-WHO-CARD-0001:B0041 support the available part of the request, while the material missing component remains unsupported: The catalog does not define a required number of consecutive controlled visits before changing the interval.

### ESCAL-V1-027 — unsupported / exact_fact_absent

**Verdict:** `CONFIRMED`

**Query:** WHO requires كام consecutive controlled visits before switching from monthly follow-up to every 3–6 months?

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: No required count of consecutive controlled visits is provided in the catalog.

### ESCAL-V1-029 — partial / multi_claim_partial

**Verdict:** `CONFIRMED`

**Query:** WHO allows trained pharmacists and nurses to manage hypertension under defined conditions; what exact minimum number of training hours is required?

**Rationale:** CONFIRMED partial after manual full-corpus review. The labeled supporting block(s) DOC-WHO-CARD-0001:B0044 support the available part of the request, while the material missing component remains unsupported: No minimum number of training hours is specified in the evidence catalog.

### ESCAL-V1-030 — unsupported / exact_fact_absent

**Verdict:** `CONFIRMED`

**Query:** WHO specifies إيه exact minimum training hours المطلوبة للـnurse قبل ما يعالج hypertension pharmacologically؟

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: The catalog requires proper training but provides no numeric training-hour threshold.

### ESCAL-V1-032 — partial / multi_claim_partial

**Verdict:** `CONFIRMED`

**Query:** المراجعة بتذكر انخفاض الضغط مع فقدان 10 kg؛ طيب إيه النسبة الدقيقة لانخفاض all-cause mortality الناتجة عن نفس فقدان الوزن؟

**Rationale:** CONFIRMED partial after manual full-corpus review. The labeled supporting block(s) DOC-PMC-CARD-0002:B0036 support the available part of the request, while the material missing component remains unsupported: The catalog does not provide an all-cause mortality reduction percentage attributable to 10 kg weight loss.

### ESCAL-V1-033 — unsupported / semantically_related_but_unsupported

**Verdict:** `CONFIRMED`

**Query:** For hypertensive adults, 10 kg weight loss lowers all-cause mortality by كام percent exactly according to this review?

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: The review catalog supports BP reduction but contains no exact all-cause mortality percentage from this weight loss.

### ESCAL-V1-035 — partial / multi_claim_partial

**Verdict:** `CONFIRMED`

**Query:** The review says ABPM usually measures every 30 minutes by day and hourly during sleep؛ what exact manufacturer and device model was used for that schedule?

**Rationale:** CONFIRMED partial after manual full-corpus review. The labeled supporting block(s) DOC-PMC-CARD-0002:B0019 support the available part of the request, while the material missing component remains unsupported: The catalog does not identify an ABPM manufacturer or device model for this schedule.

### ESCAL-V1-036 — unsupported / out_of_corpus

**Verdict:** `CONFIRMED`

**Query:** Which exact ABPM manufacturer and device model does the review specify for its daytime and nighttime measurement schedule?

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: No ABPM manufacturer or model is named in the evidence catalog.

### ESCAL-V1-038 — unsupported / temporal_out_of_scope

**Verdict:** `CONFIRMED`

**Query:** في 2026، إيه نتائج الـphase III النهائية لـzilebesiran ونسبة تقليل stroke اللي أثبتتها الدراسة؟

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: The current corpus review reports early zilebesiran evidence but does not contain 2026 phase-III results or a proven stroke-reduction percentage.

### ESCAL-V1-040 — unsupported / wrong_condition

**Verdict:** `CONFIRMED`

**Query:** What exact starting dose of losartan does this review recommend for treating portal hypertension?

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: The current PMC review covers essential systemic hypertension and provides losartan dosing in that context; it does not provide a losartan starting-dose recommendation for portal hypertension.

### ESCAL-V1-042 — unsupported / patient_specific

**Verdict:** `CONFIRMED`

**Query:** My eGFR is 22 mL/min and I'm taking hydrochlorothiazide 25 mg; according to this review, what exact furosemide dose is equivalent to my current hydrochlorothiazide dose?

**Rationale:** CONFIRMED after rewrite. The full-corpus review contains generic low-eGFR guidance favoring loop diuretics over thiazides (DOC-PMC-CARD-0002:B0120) and a generic furosemide dosing row (DOC-PMC-CARD-0002:B0076), but it does not provide a hydrochlorothiazide-to-furosemide dose-equivalence or conversion rule. The rewritten query therefore tests evidence sufficiency rather than a separate treatment-timing policy.

### ESCAL-V1-044 — unsupported / exact_fact_absent

**Verdict:** `CONFIRMED`

**Query:** المراجعة بتحدد إيه النسبة المئوية الدقيقة من جرعة labetalol اللي توصل للرضيع عبر breast milk أثناء lactation؟

**Rationale:** CONFIRMED unsupported after manual full-corpus review. Retrieved candidates are semantically related but do not provide the requested material claim. Missing support: The catalog discusses pregnancy/lactation generally and gives pregnancy dosing, but no breast-milk infant-exposure percentage for labetalol.

## Calibration decision

**PASS — ready for retrieval-only evidence-sufficiency baseline calibration.**

This does not imply clinical accuracy, diagnostic safety, or final RAG quality.
