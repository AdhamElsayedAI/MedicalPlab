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
| P0 | PLAB batch changed after its freeze | Original bytes archived against unchanged v1 manifest; source-audit v2 has a separate hash and manifest |
| P0 | SQLite revision serializer references nonexistent fields; service swallows errors | Transactional revision/review writes; failures propagate; restart and rollback tests added |
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

## PLAB persistence/versioning milestone

Targeted validation: **72 passed** across PLAB and mobile contract tests before
the final added restart/audit-event checks. The original freeze SHA remains
`7fbf3183de74df9490c9a2ce5f7b837099b536d76a2365e73abe0c0809104879`.
The separate active AI source-audit v2 checkpoint SHA is
`3351e9b7a70c0dfc83eb3927f0258f80efb273c3e37a08ab9714419f5239eeca`.
All 36 questions remain present. Historical AI classification is 7 verified,
29 needing source repair, zero rejected; these are not new measurements or
clinician approvals. Golden remains zero. See [PLAB workflow](PLAB_PIPELINE.md).

Clinical approval no longer automatically publishes a question. Persistence
retains retry keys and complete progress metadata, uses append-only revision
records and review events, and commits edited content with approval invalidation
atomically. The initial two failing hash tests are addressed by versioning the
already-existing repair checkpoint, not changing a clinical label or relaxing
the integrity check. The original mutable-path batch and historical manifest
have not been edited.

Full offline regression after the PLAB changes: **580 passed, 1 skipped**, 12
subtests passed. The final targeted durability suite passed **12 tests** (75 targeted
PLAB and mobile contract tests passed). The skipped test is not counted as passing.

Milestone `ba0a16a4c5b613a5479bba96dc824380426bf29f` was pushed after **43 passing**
benchmark/adaptation regressions. No model weights were changed.
