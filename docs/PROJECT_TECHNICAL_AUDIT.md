# MedicalPlab technical audit — 2026-09-12

Starting commit: `2e080aa` on `ai-data-execution-v1`. Origin matched HEAD after
fetch. Historical checkpoint `a29d691cce0821cdb95624c5fcbb239e5569e144` is an
ancestor. No pre-existing working-tree changes were present.

## Runtime traced from code

Docker launches `production_main:app` in production mode. This loads the
versioned product router and PLAB pilot service. `main.py` remains a separate
demo entry point. Course learning lazily creates `CourseLearningService`, whose
renal default is `QwenRenalRetrieverV3`; the experimental 4B adapter is not
promoted. SharedEvidenceEngineV2 is a separate research orchestration path with
query processing, document routing, candidate fusion, reranking and verification.

PLAB content is loaded from the 36-question cardiorespiratory batch, review queue
and 13-document/817-chunk snapshot. SQLite stores reviews, revisions and attempts.
Student delivery checks Golden status, except when explicit preview QA is enabled.
Clinical reasoning currently returns a structured 503 because it is not wired.

## Initial validation

`py -3.12 -m pytest -q`: **545 passed, 2 failed, 1 skipped**, 12 subtests passed.
Failures: PLAB frozen batch SHA mismatch, and the production data manifest check
which detects that same mismatch. These are pre-existing failures, not passes.
The installed Python is only visible outside this session's filesystem sandbox.

The locked renal corpus contains **2,175 distinct chunks**. Its measured tree
SHA256 is `d2ffac4ed60302b0e3e1d2e1236d69382bda838e9f105c25e7d0011407f9a010`.

## Findings and fixes in progress

| Severity | Finding | Disposition |
|---|---|---|
| P0 | Adjudication accepted editable original IDs/qrels from CSV | Bind IDs, query, claim and qrels to immutable V3 bytes |
| P0 | Span containment accepted fabricated extensions and stripped comparison symbols | Directional, whitespace-only literal matching |
| P0 | Reconstruction deleted existing review decisions | Refuse existing output directories |
| P0 | Duplicate corpus IDs silently overwrite records | Reject duplicate IDs and empty records; verify corpus hash |
| P0 | PLAB batch changed after its freeze | Investigating versioned repair; historical manifest retained |
| P0 | SQLite revision serializer references nonexistent fields; service swallows errors | Repair pending |
| P1 | Historical adapted evaluator computes ideal DCG only from retrieved hits | Correct shared metric implementation pending |

The new adversarial benchmark tests pass: **20 passed**. Validation confirms
literal provenance and structural consistency, not clinical truth. Reviewer
identity in a CSV is not authentication or proof of clinical credentials.

## Scientific gates

PRODUCT_DEV_V3 is historical and non-authoritative. Do not mutate it or compare
its historical baseline with a successor benchmark. V4 is not frozen. No second
adaptation, reranker optimization, NLI tuning or final independent evaluation has
been run in this session. Recall@20 >= 95% and Recall@50 >= 98% remain unchanged.

Clinical content approval and Golden promotion require actual clinician review.
AI/source audits must remain distinct from that approval.
