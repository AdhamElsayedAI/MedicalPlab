# PLAB V9 Test Parity Audit

**Submission branch:** `hackathon-submission-clean-v1`
**Canonical private evidence branch:** `plab-evidence-final-v9 @ f62b3965c0d0f10e3c636e262365e0886c61cee8`
**Audit date:** 2026-09-13

---

## Summary

| Category | Count |
| :--- | :---: |
| Canonical private V9 test intents | **24** |
| RETAINED_PUBLIC_SAFE | **10** |
| REIMPLEMENTED_PUBLIC_SAFE | **14** |
| PRIVATE_EVIDENCE_DEPENDENT | **0** |
| OBSOLETE_BY_PUBLIC_PACKAGING | **0** |
| ACCIDENTALLY_REMOVED | **0** |

**Accidentally removed: 0. All 24 canonical test intents are represented in the public submission branch.**

---

## Detailed Classification

### Group A — Independent Oracle Tests (10) — RETAINED_PUBLIC_SAFE

These 10 tests verify positive properties of the V9 closure. They use either a
public-safe synthetic fixture (when raw snapshots are absent from disk) or the
real canonical files (vault mode). All 10 are present and passing.

| # | Test Function | Invariant Verified | Classification |
|---|---|---|---|
| 1 | `test_independent_raw_snapshot_oracle` | Raw byte SHA-256 + byte length recomputed from disk | RETAINED_PUBLIC_SAFE |
| 2 | `test_independent_normalized_hash_oracle` | Normalized UTF8_LF_CANONICAL_TEXT SHA recomputed from disk | RETAINED_PUBLIC_SAFE |
| 3 | `test_cross_platform_lf_crlf_invariance` | LF / CRLF / mixed-newline hashing equivalence | RETAINED_PUBLIC_SAFE |
| 4 | `test_independent_exact_span_containment_oracle` | Exact span start/end offsets and SHA verified in normalized text | RETAINED_PUBLIC_SAFE |
| 5 | `test_independent_canonical_organization_oracle` | Canonical organization ID, role, official host, alias resolution | RETAINED_PUBLIC_SAFE |
| 6 | `test_v8_discrepancy_fixes_verified` | BTS/NICE/ICS role separation V8->V9 defect corrections | RETAINED_PUBLIC_SAFE |
| 7 | `test_checkpoint_complete_validation` | Full V9 checkpoint validator (vault mode) / governance invariants (public mode) | RETAINED_PUBLIC_SAFE |
| 8 | `test_question_counts_and_governance` | 36 total / 12 grounded / 24 quarantined / 0 approved / 0 golden | RETAINED_PUBLIC_SAFE |
| 9 | `test_redistribution_readiness_status` | All sources classified PRIVATE_EVIDENCE_ONLY; closure PASS_WITH_CLINICAL_BLOCKERS | RETAINED_PUBLIC_SAFE |
| 10 | `test_historical_checkpoints_unmodified` | V1 and V2 artifact byte-for-byte SHA integrity | RETAINED_PUBLIC_SAFE |

### Group B — Negative Mutation Tests (14) — REIMPLEMENTED_PUBLIC_SAFE

These 14 tests verify fail-closed rejection behavior. They operate against the
public-safe synthetic source fixture (`public_source_fixture`) and do NOT require
raw publisher snapshots. In the canonical private suite these tests used real source
files; in the public submission they use an equivalent synthetic fixture exercising
identical code paths. All 14 invariants are verified.

| # | Test Function | Invariant Verified | Classification |
|---|---|---|---|
| 11 | `test_mutation_alter_raw_byte_fails` | Mutated raw SHA -> raw snapshot hash mismatch error | REIMPLEMENTED_PUBLIC_SAFE |
| 12 | `test_mutation_alter_normalized_sha_fails` | Mutated normalized SHA -> normalized representation hash mismatch | REIMPLEMENTED_PUBLIC_SAFE |
| 13 | `test_mutation_alter_span_character_fails` | One-character span mutation -> hash mismatch or offset mismatch | REIMPLEMENTED_PUBLIC_SAFE |
| 14 | `test_mutation_shift_span_offset_fails` | Shifted start_char -> locator char offset mismatch | REIMPLEMENTED_PUBLIC_SAFE |
| 15 | `test_mutation_wrong_source_id_in_claim_fails` | Non-existent source_id in claim -> unknown source identity error | REIMPLEMENTED_PUBLIC_SAFE |
| 16 | `test_mutation_wrong_canonical_organization_id_fails` | Non-existent org ID -> unknown canonical organization ID error | REIMPLEMENTED_PUBLIC_SAFE |
| 17 | `test_mutation_supporting_org_substituted_for_issuing_fails` | FICM (supporting org) cannot substitute for ISSUING_ORGANIZATION | REIMPLEMENTED_PUBLIC_SAFE |
| 18 | `test_mutation_journal_host_substituted_for_clinical_issuing_org_fails` | BMJ Thorax (journal publisher) cannot substitute for issuing clinical org | REIMPLEMENTED_PUBLIC_SAFE |
| 19 | `test_mutation_unapproved_host_fails` | Unauthorized mirror host rejected as not on approved official host list | REIMPLEMENTED_PUBLIC_SAFE |
| 20 | `test_mutation_missing_currentness_evidence_fails` | Empty currentness evidence -> missing source currentness evidence error | REIMPLEMENTED_PUBLIC_SAFE |
| 21 | `test_mutation_unsupported_specificity_dimension_fails` | MISMATCH in dose dimension -> dose mismatch error | REIMPLEMENTED_PUBLIC_SAFE |
| 22 | `test_mutation_fake_clinician_approval_fails` | clinician_approved=True -> fabricated clinician approval error | REIMPLEMENTED_PUBLIC_SAFE |
| 23 | `test_mutation_fake_golden_promotion_fails` | golden=True -> automatic Golden promotion error | REIMPLEMENTED_PUBLIC_SAFE |
| 24 | `test_mutation_missing_source_file_fails` | Missing snapshot file on disk -> raw snapshot file does not exist error | REIMPLEMENTED_PUBLIC_SAFE |

---

## Critical Invariants Coverage

| Required Invariant | Covered By Test # |
|---|---|
| Raw byte SHA semantics | 1, 11 |
| Normalized UTF8_LF_CANONICAL_TEXT hashing | 2, 12 |
| LF/CRLF equivalence | 3 |
| Corrupted normalized text rejection | 12 |
| Source organization canonical identity | 5, 16 |
| NICE alias handling | 5 |
| Wrong publisher rejection | 18 |
| Wrong authoritative host rejection | 19 |
| Issuing organization vs publication host role separation | 17, 18 |
| Supporting organization cannot substitute issuing organization | 17 |
| Exact-span start/end integrity | 4, 14 |
| Exact-span SHA integrity | 4, 13 |
| Modified span rejection | 13 |
| Non-contiguous/synthetic exact span rejection | 14 |
| Unsupported claim specificity rejection | 21 |
| Missing source/evidence failure | 15, 20, 24 |
| Fail-closed exception behavior | 11-24 (all mutation tests) |
| clinician_approved remains zero | 8, 22 |
| golden_eligible remains zero | 8 |
| golden remains zero | 8, 23 |

---

## Public Mode vs Vault Mode Behavior

Tests 1, 2, 4, 7 have dual execution paths:

- **Vault mode** (private evidence on disk at Data/sources/v8/): All checks run against
  real publisher snapshots including raw SHA recomputation and normalized text hash
  recomputation from actual files.
- **Public mode** (submission branch, no raw snapshots): Tests fall back to a minimal
  public-safe synthetic fixture that exercises identical validator code paths without
  redistributing third-party publisher material.

This design satisfies the requirement to preserve all clinically important V9 invariants
without redistribution of private publisher evidence.
