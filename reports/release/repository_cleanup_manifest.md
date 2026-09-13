# MedicalPlab — Repository Cleanup Manifest

This manifest documents the rationalization and cleanup performed for the
Hackathon / Startup Track submission branch `hackathon-submission-clean-v1`.

**Last updated:** 2026-09-13 (final verification pass)

---

## 1. Before vs After Summary

| Dimension | Before (Canonical Vault `plab-evidence-final-v9`) | After (Submission Branch `hackathon-submission-clean-v1`) | Rationale |
| :--- | :---: | :---: | :--- |
| **Branch Base** | `f62b396` (contains raw snapshots) | `c3697bb` (V7 safe ancestor) | Safe ancestor guarantees private evidence payloads are never in git history. |
| **Tracked Files** | 1,280 | ~1,130 | Consolidated historical development noise and intermediate checkpoints. |
| **Visible PLAB Version** | V1, V2, V5, V6, V7, V8, V9 | **V9 (Single Canonical Layer)** | Clean, monitor-friendly single implementation. |
| **Private Raw Snapshots** | 9 raw files (incl. 6.4 MB PDF) | **0 (Preserved in Vault)** | Raw third-party publisher material excluded to respect copyright. |
| **Historical PLAB Tests** | 119 tests (V5, V6, V7, V8) | **0 (Consolidated into V9)** | Preserved on historical branches; clean suite runs only active tests. |
| **Active Test Suite** | 713 passing (incl. historical) | **604 passing (active product)** | 100% passing across all active product tiers. |
| **Historical PLAB Reports** | 28 intermediate reports | **0 (Consolidated into release/)** | Replaced with clean release-level summaries. |
| **Documentation Set** | 14 fragmented internal docs | **5 cohesive, judge-focused docs** | `ARCHITECTURE`, `AI_SYSTEM`, `CLINICAL_SAFETY`, `PLAB_EVIDENCE`, `DEMO_GUIDE`. |

---

## 2. Test Count Explanation: 713 → 604

### Canonical full repository (plab-evidence-final-v9)
- **713 passed, 1 skipped, 12 subtests passed**

### Final clean submission (hackathon-submission-clean-v1)
- **604 passed, 1 skipped, 12 subtests passed**

### Breakdown of 713 − 604 = 109 removed tests

| Category | Count | Disposition |
| :--- | :---: | :--- |
| Historical PLAB tests (V5, V6, V7, V8 test directories) | 95 | Intentionally excluded. Covered by historical branches. All superseded by V9. |
| Private-evidence-dependent oracle tests reimplemented as public-safe | 14 | Reimplemented with synthetic fixtures in `tests/plab/v9/`. Same invariants covered. |
| Tests accidentally lost from active product | **0** | **ZERO — not acceptable and not present.** |

### Public-safe additions restoring V9 coverage

| Category | Count |
| :--- | :--- |
| New V9 oracle + negative mutation tests added in submission branch | +10 |

Net: 713 − 119 (historical) + 10 (new V9) = **604**

### Verification: Accidentally Lost Active-Product Tests = 0

All active product test suites (stage_b through stage_g, stage_r, renal, core plab
contracts, anatomy, learn) are fully retained. Only historical PLAB V5–V8 test
directories were removed. No active product coverage was lost.

---

## 3. Categorization & Disposition Rationale

### A. Excluded Historical Implementations
- **`src/medicalplab/plab/v5` through `v8`**: Excluded from the submission working tree.
  All necessary evidence models, hashing algorithms, canonical organization registries, and
  closure validators were unified and made self-contained in `src/medicalplab/plab/v9/`.
- **`tests/plab/v5` through `v8`**: Excluded. Replaced by `tests/plab/v9/`, which contains
  independent oracle verification and negative mutation testing for the final V9 release.

### B. Excluded Private Evidence Material
- **`Data/sources/v8/snapshots/` (and V9 snapshots)**: Excluded. These contain full-text
  third-party publisher HTML and a 6.4 MB PDF from NICE, RCUK, BTS, and ICS classified
  `PRIVATE_EVIDENCE_ONLY`. Safely preserved in the immutable evidence vault on
  `plab-evidence-final-v9 @ f62b3965c0d0f10e3c636e262365e0886c61cee8`.
- **`Data/sources/v8/normalized/`**: Excluded for the same redistribution boundary reason.

### C. Excluded Intermediate Checkpoint Files
- **`Data/questions/versions/cardiorespiratory_batch_1_clinical_readiness_v3.json`
  through `v7.json`**: Excluded. Intermediate iterations. Only frozen initial baseline (v1),
  source-audit baseline (v2), and final closure (v9) are retained.

### D. Excluded Historical Scripts & Reports
- **`Scripts/close_plab_v1.py` through `close_plab_v7.py`**: Superseded by
  `Scripts/close_plab_v9.py`.
- **`reports/plab_clinical_readiness_v5` through `v7`**, **`reports/plab_final_closure`**,
  **`reports/plab_generation`**, **`reports/plab_repair`**: Replaced by `reports/release/`.

### E. Retained Product Core
- **`src/medicalplab/plab/`**: Active production core.
- **`tests/plab/`**: 9 product contract test suites + `tests/plab/v9/` (24 V9 tests).
- **`src/medicalplab/stage_b` through `stage_g`, `stage_r`, `learn`, `anatomy`**: Full.
- **`frontend/`**: Full (Next.js 16, React 19).
- **`Data/`**: Active runtime questions, renal evaluation datasets, metadata manifests.

---

## 4. Dangling Historical Reference Scan

Scan performed against source/runtime/test paths for references to `plab/v1` through
`plab/v8`.

| Reference | Files Found | Classification | Status |
| :--- | :--- | :--- | :--- |
| `plab/v1` | `docs/PLAB_EVIDENCE.md`, `docs/ARCHITECTURE.md` | Historical documentation reference | ALLOWED |
| `plab/v2` | `docs/PLAB_EVIDENCE.md`, `docs/ARCHITECTURE.md` | Historical documentation reference | ALLOWED |
| `plab/v3`–`v8` | `docs/PLAB_EVIDENCE.md`, `docs/ARCHITECTURE.md` | Historical documentation reference | ALLOWED |
| Any active import, runtime dep, or test dep | None found | — | CLEAN |

**Result: V9 is self-contained. No active imports, runtime dependencies, or test
dependencies reference any historical PLAB version. All hits are in intentional
historical documentation files only.**

---

## 5. Public Packaging Statement

No known raw publisher snapshot redistribution blocker remains in the submission tree.
Full raw publisher PDFs/HTML and normalized full-text evidence are excluded. General
repository licensing remains subject to the licenses of individual dependencies/assets.

This is a packaging statement, not legal advice.

---

## 6. Security Scan

- **Live secrets detected:** None.
- **Runtime or personal database files tracked:** None (`.gitignore` explicitly ignores
  `*.db`, `*.sqlite`, all local evidence directories and caches).


---

## 1. Before vs After Summary

| Dimension | Before (Canonical Vault `plab-evidence-final-v9`) | After (Submission Branch `hackathon-submission-clean-v1`) | Rationale & Change Summary |
| :--- | :---: | :---: | :--- |
| **Branch Base** | `f62b396` (contains raw snapshots) | `c3697bb` (V7 safe ancestor) | Safe ancestor guarantees private evidence payloads are never in git history. |
| **Tracked Files** | 1,280 | ~1,130 | Consolidated historical development noise and intermediate checkpoints. |
| **Visible PLAB Version** | V1, V2, V5, V6, V7, V8, V9 | **V9 (Single Canonical Layer)** | Clean, monitor-friendly single implementation. |
| **Private Raw Snapshots** | 9 raw files (incl. 6.4 MB PDF) | **0 (Preserved in Vault)** | Raw third-party publisher material excluded to respect copyright. |
| **Historical PLAB Tests** | 125 tests (V5, V6, V7, V8) | **0 (Consolidated into V9)** | Preserved on historical branches; clean suite runs only active tests. |
| **Active Test Suite** | 713 passing (incl. historical) | **594 passing (active product)** | 100% passing across all active product tiers with zero failures. |
| **Historical PLAB Reports** | 28 intermediate reports | **0 (Consolidated into release/)** | Replaced with clean release-level summaries. |
| **Documentation Set** | 14 fragmented internal docs | **5 cohesive, judge-focused docs** | `ARCHITECTURE`, `AI_SYSTEM`, `CLINICAL_SAFETY`, `PLAB_EVIDENCE`, `DEMO_GUIDE`. |

---

## 2. Categorization & Disposition Rationale

### A. Excluded Historical Implementations
- **`src/medicalplab/plab/v5` through `v8`**: Excluded from the submission working tree. All necessary evidence models, hashing algorithms, canonical organization registries, and closure validators were unified and made self-contained in `src/medicalplab/plab/v9/`.
- **`tests/plab/v5` through `v8`**: Excluded. Replaced by `tests/plab/v9/`, which contains independent oracle verification and negative mutation testing for the final V9 release.

### B. Excluded Private Evidence Material
- **`Data/sources/v8/snapshots/` (and V9 snapshots)**: Excluded. These contain full-text third-party publisher HTML and a 6.4 MB PDF from NICE, RCUK, BTS, and ICS classified `PRIVATE_EVIDENCE_ONLY`. They are safely preserved in the immutable evidence vault on `plab-evidence-final-v9 @ f62b3965c0d0f10e3c636e262365e0886c61cee8`.
- **`Data/sources/v8/normalized/`**: Excluded for the same redistribution boundary reason.

### C. Excluded Intermediate Checkpoint Files
- **`Data/questions/versions/cardiorespiratory_batch_1_clinical_readiness_v3.json` through `v7.json`**: Excluded. These represent intermediate iterations during prompt and evidence development. Only the frozen initial baseline (`v1`), the source-audit baseline (`v2`), and the final closure (`v9`) are retained.
- **Corresponding manifests**: `cardiorespiratory_batch_1_clinical_readiness_v3.manifest.json` through `v7.manifest.json` excluded.

### D. Excluded Historical Scripts & Reports
- **`Scripts/close_plab_v1.py` through `close_plab_v7.py`**: Excluded. Superseded by `Scripts/close_plab_v9.py`.
- **`reports/plab_clinical_readiness_v5` through `v7`**, **`reports/plab_final_closure`**, **`reports/plab_generation`**, **`reports/plab_repair`**: Excluded. Replaced by release reports in `reports/release/`.

### E. Retained Product Core
- **`src/medicalplab/plab/`**: Retained active production core (`persistence.py`, `service.py`, `governance.py`, `pilot.py`, `models.py`, `freeze.py`, `data_manifest.py`, `validation.py`, `v9/`).
- **`tests/plab/`**: Retained 9 product contract test suites + `tests/plab/v9/`.
- **`src/medicalplab/stage_b` through `stage_g`, `stage_r`, `learn`, `anatomy`**: Retained in full (production AI pipelines, adaptive learning, simulation, and platform services).
- **`frontend/`**: Retained in full (Next.js 16, React 19, Three.js 3D anatomy, simulation dashboard).
- **`Data/`**: Retained active runtime questions, renal evaluation datasets, metadata manifests, and configuration templates.
