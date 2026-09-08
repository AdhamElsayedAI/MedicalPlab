# PLAB 2026 Cardiorespiratory Data Foundation — Execution Report

**Branch:** `ai-data-execution-v1`  
**Baseline commit:** `79c4f261f86bdbf61dd576577f1ab2d707d6bce2`  
**Report date:** 2026-09-09  

## Executive status

The first defensible PLAB-oriented Cardiorespiratory source foundation is now documented in-repository. The task deliberately separates official exam scope, UK clinical ground truth, commercial-compatible supporting evidence, and evaluation material.

The previous Codex workspace reported successful local ingestion of eight CC BY supporting documents producing **702 validated chunks**. Because `Data/` is intentionally gitignored, those raw/processed artifacts are not visible through the connected GitHub repository and were **not independently re-executed in this remote continuation session**. They are preserved as an explicit checkpoint rather than being silently upgraded to independently verified evidence.

## Repository deliverables created in this continuation

- `docs/plab/PLAB_2026_CARDIORESPIRATORY_COVERAGE_MATRIX.md`
- `docs/plab/PLAB_2026_CARDIORESPIRATORY_SOURCES.md`
- `docs/plab/PLAB_2026_CARDIORESPIRATORY_EXECUTION_REPORT.md`
- `examples/plab_cardiorespiratory_coverage.example.json`
- `examples/plab_cardiorespiratory_sources.example.json`

No frozen evaluation artifact was modified. No stable ingestion schema was rewritten. No new pipeline stage was introduced.

## Source corpus checkpoint

Selected sources: **18**

- 3 GMC official blueprint/evaluation sources
- 7 NICE UK ground-truth references
- 8 PMC commercial-compatible supporting evidence documents

Licence classes:

- `INGEST_ALLOWED`: 8
- `REFERENCE_ONLY`: 2
- `PERMISSION_REQUIRED`: 7
- `EVALUATION_ONLY`: 1
- `BLOCKED`: 0

### Important licence boundary

NICE is not a production RAG ingestion source under the currently verified permission state. The current NICE reuse terms exclude AI use from the ordinary open-content permission path and require separate permission/licensing. NICE therefore remains an external UK clinical verification layer until that status changes.

Official GMC sample questions remain evaluation/style-calibration material only; they are not copied into the MedicalPlab question bank.

## Previous Codex local ingestion checkpoint

| Document ID | Coverage | Sections | Chunks | Status |
|---|---|---:|---:|---|
| DOC-PMC-CARD-0002 | Hypertension | 22 | 144 | LOCAL PASS REPORTED |
| DOC-PMC-CARD-0003 | Heart failure | 30 | 88 | LOCAL PASS REPORTED |
| DOC-PMC-CARD-0004 | ACS/STEMI/NSTEMI/CAD | 16 | 34 | LOCAL PASS REPORTED |
| DOC-PMC-CARD-0005 | Type B aortic dissection | 18 | 49 | LOCAL PASS REPORTED |
| DOC-PMC-CARD-0006 | Pericardial effusion/tamponade | 13 | 44 | LOCAL PASS REPORTED |
| DOC-PMC-CARD-0007 | Pulmonary embolism | 42 | 108 | LOCAL PASS REPORTED |
| DOC-PMC-RESP-0001 | Asthma | 31 | 62 | LOCAL PASS REPORTED |
| DOC-PMC-RESP-0002 | Pneumonia | 30 | 173 | LOCAL PASS REPORTED |

**Reported total: 702 chunks.**

The SHA-256 values for all eight are retained in the source dossier and machine-readable registry.

## Strongest currently covered P0 topics

The current reported supporting corpus is sufficient to proceed to controlled question-generation experiments for:

- Acute coronary syndromes / STEMI / NSTEMI
- Hypertension
- Heart failure
- Aortic dissection (with the explicit limitation that the selected review is type-B focused)
- Pericardial effusion / cardiac tamponade
- Pulmonary embolism
- Asthma (supporting evidence only; UK reconciliation required)
- Pneumonia

This does **not** mean Cardiorespiratory PLAB coverage is complete.

## Highest-priority remaining P0 gaps

1. Tachyarrhythmias: AF, atrial flutter, SVT, torsades, VT, VF
2. Bradyarrhythmias / AV block
3. Cardiac arrest / cardiorespiratory arrest
4. Syncope
5. COPD dedicated evidence
6. Pneumothorax
7. Respiratory failure / ARDS
8. Shock / deteriorating patient
9. Aortic and mitral valve disease
10. Infective endocarditis

The next acquisition wave should pair each P0 topic with:

- at least one current authoritative UK reference, and
- at least one commercial-compatible supporting document suitable for AI/RAG use.

## PLAB readiness

### Five-option product contract

The existing `src/medicalplab/plab/*` layer already establishes the product-specific five-option A–E contract without rewriting Stage-C core.

### Question generation

**Status: READY FOR A SMALL CONTROLLED CARDIORESPIRATORY BATCH, NOT FOR BROAD RELEASE.**

Recommended first generation wave:

- 5–8 ACS/IHD questions
- 4–5 hypertension questions
- 4–5 heart-failure questions
- 3–4 PE questions
- 3–4 pericardial/tamponade questions
- 3–4 aortic-dissection questions
- 3–4 asthma questions
- 3–4 pneumonia questions

Target: approximately **30–40 original questions** after evidence reconciliation and validation.

Every accepted question must have:

- five options A–E
- one single best answer
- exact evidence citation(s)
- source provenance
- explanation
- distractor review
- UK-ground-truth reconciliation where management is involved
- validator pass
- human-review status that remains truthful (`pending` until actually reviewed)

## Verification status

| Check | Status | Notes |
|---|---|---|
| Current GMC MLA 2026 applicability | PASS | Current map applies from September 2026 onward |
| Cardiorespiratory official topic extraction | PASS | Matrix derived from current GMC Domain 5/6 content |
| NICE AI reuse boundary | PASS | Permission/licensing required; not treated as ingestible RAG evidence |
| Source-role separation | PASS | blueprint / ground truth / supporting evidence / evaluation separated |
| Machine-readable source registry created | PASS | example registry added without rewriting canonical schema |
| Machine-readable coverage representation created | PASS | example coverage map added |
| Frozen evaluation artifacts unchanged | PASS by change scope | continuation did not modify them |
| 8-document local raw-file hashes | NOT INDEPENDENTLY RE-VERIFIED | values retained from previous Codex workspace report |
| 702 local chunks | NOT INDEPENDENTLY RE-EXECUTED | `Data/` artifacts are gitignored/unavailable in this remote session |
| Full repository unit-test suite | NOT EXECUTED IN THIS REMOTE SESSION | GitHub connector does not provide a local Python checkout/runtime |

## Exact local verification required when the Codex/Data workspace is available

Run the repository's existing document and chunk validators against the eight local documents. Do not regenerate them unless hashes or validators fail.

Minimum checks:

1. compare each immutable raw JATS file SHA-256 against the recorded hash;
2. run document/section/chunk schema validators;
3. run chunk-integrity validation;
4. confirm total chunk count = 702 only if all eight pass;
5. confirm each article's stored JATS licence node states the recorded licence;
6. freeze the validated corpus snapshot/version before question generation.

If any discrepancy appears, update the registry and report the real value rather than preserving the checkpoint claim.

## Next execution milestone

The next highest-value work is **not** another architecture rewrite. It is:

1. close the remaining P0 Cardiorespiratory evidence gaps;
2. re-verify/freeze the reported 702-chunk local corpus;
3. wire the real Stage-R retrieval path to the product PLAB service;
4. generate and validate the first 30–40 original PLAB Cardiorespiratory questions;
5. build a held-out PLAB/RAG evaluation set separate from the production question bank.

This keeps MedicalPlab PLAB-first, UK-grounded, licence-conscious, and evaluation-ready.
