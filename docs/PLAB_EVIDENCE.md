# PLAB V9 Evidence & Safety Layer

## 1. Executive Summary

The **MedicalPlab PLAB V9 Evidence Layer** provides a deterministic, mathematically verifiable, and fail-closed evidence foundation for UK General Medical Council (GMC) PLAB 1 / MLA medical licensing exam questions. 

Medical questions cannot rely on generic LLM pre-training recall or hallucinated citations. Every question in the curriculum must be anchored to verified, authoritative UK clinical guidelines with exact cryptographic provenance.

### Accepted V9 Status & Metrics
| Metric | Value | Verification Status | Meaning |
| :--- | :--- | :--- | :--- |
| **Total Questions Evaluated** | **36** | `[Verified]` | Cardiorespiratory Batch 1 exam blueprint |
| **Source Grounded** | **12** | `[Verified]` | Passed all strict technical provenance gates |
| **Clinician Review Required** | **12** | `[Verified]` | Technical gates clear; awaiting GMC clinician sign-off |
| **Quarantined Items** | **24** | `[Verified]` | Locked down due to evidence/currency/ambiguity blockers |
| **Clinician Approved** | **0** | `[Verified]` | Software cannot self-approve clinical validity |
| **Golden Eligible** | **0** | `[Verified]` | Requires un-quarantined status + clinician sign-off |
| **Golden Questions** | **0** | `[Verified]` | Zero unapproved questions served to live learners |
| **Remaining Engineering Blockers** | **0** | `[Verified]` | Zero parser, hash, or schema integrity faults |
| **Exact-Span Integrity Errors** | **0** | `[Verified]` | 100% character-exact string containment in sources |
| **Canonical Private Evidence SHA** | `f62b3965c0d0f10e3c636e262365e0886c61cee8` | `[Verified]` | Immutable evidence vault on `plab-evidence-final-v9` |

---

## 2. Why Quarantine is a Strength, Not a Failure

In consumer software, 12 out of 36 items might appear to be an incomplete test run. **In clinical AI and medical licensing, a 66.7% quarantine rate is a critical safety feature.**

1. **Fail-Closed Safety Contract**: If an authoritative guideline is updated, if a source license changes, or if an option has ambiguous distractor support, the system immediately quarantines the question. It does not attempt to "smooth over" gaps with generative guesswork.
2. **Protection Against Medical Hallucinations**: Medical students studying for licensing exams must never learn obsolete drug dosages, discontinued clinical pathways, or ambiguous triage thresholds.
3. **Auditability**: Quarantined questions remain fully documented in the evidence matrix with explicit machine-readable blockers (e.g., `CURRENCY_OUTDATED`, `DISTRACTOR_AMBIGUITY`, `INSUFFICIENT_SPAN_CONFIDENCE`), enabling targeted human clinical resolution.

---

## 3. Source-Grounded Methodology & Verification Pipeline

Every active question undergoes multi-tier automated validation before it can enter the clinician review queue:

```text
Draft Question & Options
         │
         ▼
[1. Source Identity Verification]
   • Verification against authoritative UK registry (NICE, BTS, RCUK, SIGN, FICM)
   • Strict URL / DOI / ISBN metadata cross-checks
         │
         ▼
[2. Currency & Guideline Validity]
   • Publication date & withdrawal checks against GMC MLA content map
   • Quarantine if superseded by newer guidance
         │
         ▼
[3. Exact-Span Validation]
   • Exact character-sequence matching in authoritative normalized text
   • Zero tolerance for fuzzy matching, paraphrasing, or synthetic spans
         │
         ▼
[4. Atomic Claim Decomposition]
   • Every decisive clinical explanation is broken into atomic assertions
   • Each assertion must map to an independently verified source span
         │
         ▼
[5. Deterministic Hash Integrity]
   • Content SHA-256 computation over question text, options, explanations, and citations
   • Prevents tampering or undetected regression across pipeline stages
         │
         ▼
[6. Fail-Closed Gate]
   ├── Any blocker detected ──────► QUARANTINED (24 items)
   └── All gates passed ──────────► CLINICIAN_REVIEW_REQUIRED (12 items)
                                          │
                                          ▼
                                   [Human Clinician Sign-Off]
                                          │ (Pending human audit)
                                          ▼
                                    GOLDEN (0 items)
```

---

## 4. Technical Closure vs. Human Clinical Approval

MedicalPlab maintains an uncompromised ethical and regulatory boundary: **AI does not and cannot clinically approve medical content.**

- **Technical Evidence Closure (`PASS_WITH_CLINICAL_BLOCKERS`)**: Confirms that software-level verification is 100% complete—sources are identified, text spans exist verbatim, hashing is deterministic, and distractors meet non-ambiguity thresholds.
- **Human Clinical Approval (`CLINICIAN_APPROVED = 0`)**: Clinical validity requires practicing GMC-registered physicians to review the clinical reasoning, edge cases, and exam appropriateness.
- **Serving Policy**: In production runtime, the system serves exclusively Golden questions (`golden = true`). In demo mode, quarantined questions can be viewed in the review console with explicit warning banners explaining why they are quarantined.

---

## 5. Private Evidence Vault & Public Packaging

The authoritative evidence records for PLAB V9 are secured in an immutable Git branch:

- **Canonical Branch**: `plab-evidence-final-v9`
- **Canonical V9 Commit**: `f62b3965c0d0f10e3c636e262365e0886c61cee8`
- **Canonical Parent (V8)**: `230dd671df4cd9ea7138872770613ea2302f78d4`

### Public Redistribution Safeguards
To comply with copyright and database rights for publisher guidelines (NICE, BTS, BMJ, Resuscitation Council UK), **full raw publisher HTML/PDF snapshots and full normalized text caches are classified as `PRIVATE_EVIDENCE_ONLY`** and are retained exclusively in the private vault branch.

The public submission repository contains:
1. The deterministic validator engine (`src/medicalplab/plab/v9/`).
2. The closed question dataset with exact spans, cryptographic hashes, and blocker metadata (`Data/questions/versions/cardiorespiratory_batch_1_final_closure_v9.json`).
3. The cryptographic manifest verifying dataset integrity (`Data/metadata/cardiorespiratory_batch_1_final_closure_v9.manifest.json`).
4. Full automated test suite proving zero hash or span faults (`tests/plab/v9/`).
