# MedicalPlab — Repository Cleanup Manifest

**Submission branch:** `hackathon-submission-clean-v1`
**Canonical evidence branch:** `plab-evidence-final-v9 @ f62b3965c0d0f10e3c636e262365e0886c61cee8`
**Last updated:** 2026-09-13 (final documentation consistency pass)

---

## 1. Before vs After Summary

| Dimension | Before (Canonical Vault `plab-evidence-final-v9`) | After (Submission Branch `hackathon-submission-clean-v1`) | Rationale |
| :--- | :---: | :---: | :--- |
| **Branch Base** | `f62b396` (contains raw snapshots) | `c3697bb` (V7 safe ancestor) | Safe ancestor guarantees private evidence payloads are never in git history. |
| **Tracked Files** | ~1,280 | ~1,130 | Consolidated historical development noise and intermediate checkpoints. |
| **Visible PLAB Version** | V1, V2, V5, V6, V7, V8, V9 | **V9 (Single Canonical Layer)** | Clean, monitor-friendly single implementation. |
| **Private Raw Snapshots** | 9 raw files (incl. 6.4 MB PDF) | **0 (Preserved in Vault)** | Raw third-party publisher material excluded to respect copyright. |
| **Historical PLAB Test Files** | 5 files (v6: 3, v7: 1, v8: 1) | **0 (Superseded by V9)** | Preserved on historical branches; clean suite runs only current tests. |
| **Full Test Suite** | 713 passed, 1 skipped (incl. historical) | **604 passed, 1 skipped (active product)** | 100% passing; see exact reconciliation below. |
| **Historical PLAB Reports** | 28 intermediate reports | **0 (Consolidated into release/)** | Replaced with clean release-level summaries. |
| **Documentation Set** | 14 fragmented internal docs | **5 cohesive, judge-focused docs** | `ARCHITECTURE`, `AI_SYSTEM`, `CLINICAL_SAFETY`, `PLAB_EVIDENCE`, `DEMO_GUIDE`. |

---

## 2. Test Count Reconciliation: 713 → 604

### Canonical full repository (`plab-evidence-final-v9`)
- **713 passed, 1 skipped, 12 subtests passed**

### Final clean submission (`hackathon-submission-clean-v1`)
- **604 passed, 1 skipped, 12 subtests passed**

### Exact arithmetic

```
713 (canonical) − 109 (historical plab tests removed) + 0 (V9 net change) = 604 ✓
```

### Breakdown of 109 removed collected tests

These 109 tests were collected by pytest from the 5 historical plab test files
that are present in the canonical vault but intentionally excluded from the
submission branch. The count of 109 is empirically verified: it is the exact
difference between the two `pytest -q` runs.

| File | Location | Def count | Collected* | Disposition |
| :--- | :--- | :---: | :---: | :--- |
| `test_canary_oracle.py` | `tests/plab/v6/` | 13 | ~13 | Intentionally removed — V6 historical oracle |
| `test_canonical_integration.py` | `tests/plab/v6/` | 4 | ~4 | Intentionally removed — V6 integration |
| `test_clinical_readiness_v6.py` | `tests/plab/v6/` | 13† | ~31 | Intentionally removed — V6 clinical readiness (class+parametrize) |
| `test_final_closure.py` | `tests/plab/v7/` | 25 | ~25 | Intentionally removed — V7 historical oracle |
| `test_source_proof_closure.py` | `tests/plab/v8/` | 36 | ~36 | Intentionally removed — V8 source-proof closure |
| **Total removed** | | **91** | **109** | Intentionally excluded historical plab versions |

\* Collected count includes parametrize/fixture expansions in the class-based v6
  clinical readiness suite; exact per-file collected breakdown was not re-run from
  canonical to avoid side effects. The total of 109 is exact (empirically verified).

† Class-based test methods in `test_clinical_readiness_v6.py`.

### V9 test count: net zero change

The V9 test file (`tests/plab/v9/test_final_plab_closure.py`) contains **24 tests**
in both the canonical vault and the clean submission. Net contribution to the
test-count delta: **zero**.

Note: 10 of the 24 V9 tests were transiently absent from the initial clean branch
creation (the branch was cut from V7, not from V9). The acceptance patch restored
them to match the canonical V9 count. These 10 tests have always been included in
the canonical 713 and are included in the clean 604.

### Verification: Accidentally lost active-product tests = 0

All active product test suites are fully retained:
- `tests/plab/` product contracts (9 suites, 63 tests)
- `tests/plab/v9/` V9 closure oracle (24 tests)
- `tests/stage_b/` through `tests/stage_g/`, `tests/stage_r/`
- `tests/renal/` retrieval benchmark
- `tests/learn/`, `tests/anatomy/`

Only historical PLAB V6, V7, V8 test directories were removed. No active product
coverage was lost.

---

## 3. Categorization & Disposition Rationale

### A. Excluded Historical PLAB Implementations
- **`src/medicalplab/plab/v5` through `v8`**: Excluded. All V9 supersedes them.
  Evidence models, hashing algorithms, canonical organization registries, and closure
  validators are unified and self-contained in `src/medicalplab/plab/v9/`.
- **`tests/plab/v6/`, `tests/plab/v7/`, `tests/plab/v8/`**: Excluded (109 tests).
  Replaced by `tests/plab/v9/test_final_plab_closure.py` (24 tests covering all
  active invariants, including 14 negative mutation tests and 10 oracle tests).

### B. Excluded Private Evidence Material
- **`Data/sources/v8/snapshots/`**: Excluded. Contains full-text third-party publisher
  HTML and a 6.4 MB PDF from NICE, RCUK, BTS, and ICS, classified `PRIVATE_EVIDENCE_ONLY`.
  Preserved in the immutable evidence vault at
  `plab-evidence-final-v9 @ f62b3965c0d0f10e3c636e262365e0886c61cee8`.
- **`Data/sources/v8/normalized/`**: Excluded for the same reason.

### C. Excluded Intermediate Checkpoint Files
- **`Data/questions/versions/cardiorespiratory_batch_1_clinical_readiness_v3.json`
  through `v7.json`**: Intermediate iterations excluded. Retained: frozen initial
  baseline (`v1`), source-audit baseline (`v2`), and final closure (`v9`).

### D. Excluded Historical Scripts & Reports
- **`Scripts/close_plab_v1.py` through `close_plab_v7.py`**: Superseded by
  `Scripts/close_plab_v9.py`.
- Historical plab reports directories: replaced by `reports/release/`.

### E. Retained Product Core (unchanged)
- **`src/medicalplab/plab/v9/`**: Full V9 validator, hashing, identity, models.
- **`tests/plab/`**: 9 product contract suites + `tests/plab/v9/` (24 V9 tests).
- **`src/medicalplab/stage_b` through `stage_g`, `stage_r`, `learn`, `anatomy`**: Full.
- **`frontend/`**: Full (Next.js 16, React 19).
- **`Data/`**: Active runtime questions, renal evaluation datasets, metadata manifests.

---

## 4. V9 Public Reproducibility Boundary

The public submission branch contains the final V9 PLAB implementation, governance
rules, deterministic validation logic, and public-safe synthetic tests for all 24
canonical V9 test intents. Full raw-source provenance verification remains preserved
in the private canonical evidence vault at `plab-evidence-final-v9`, commit
`f62b3965c0d0f10e3c636e262365e0886c61cee8`, because full publisher snapshots are
intentionally excluded from the public submission package.

| Dimension | Status |
| :--- | :--- |
| V9 runtime/governance implementation self-contained | YES |
| Full private source-proof corpus included publicly | NO |
| Canonical private evidence vault preserved | YES |

---

## 5. Dangling Historical Reference Scan

Scan performed against all tracked source/runtime/test paths for references to
`plab/v1` through `plab/v8`.

| Reference | Files Found | Classification | Status |
| :--- | :--- | :--- | :--- |
| `plab/v1`–`v8` | `docs/PLAB_EVIDENCE.md`, `docs/ARCHITECTURE.md` | Intentional historical documentation | ALLOWED |
| Any active import, runtime dep, or test dep | None | — | CLEAN |
| `.pytest_cache/v/cache/nodeids` | Not tracked in git (covered by `.gitignore:9`) | Cache file | NOT TRACKED |

**V9 runtime/governance implementation is self-contained. No active imports, runtime
dependencies, or test dependencies reference any historical PLAB version.**

---

## 6. Public Packaging Statement

No known raw publisher snapshot redistribution blocker remains in the submission tree.
Full raw publisher PDFs/HTML and normalized full-text evidence are excluded. General
repository licensing remains subject to the licenses of individual dependencies/assets.

*This is a packaging statement, not legal advice.*

---

## 7. Security Scan

- **Live secrets detected:** None.
- **Runtime or personal database files tracked:** None (`.gitignore` covers `*.db`,
  `*.sqlite`, all local evidence directories and caches).
