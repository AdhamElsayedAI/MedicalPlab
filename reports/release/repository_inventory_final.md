# MedicalPlab — Final Repository Inventory & Structural Audit

**Audit Date:** 2026-09-14  
**Workspace:** `MedicalPlab-productized`  
**Base Commit:** `441939575736b2d985c0932d44ef62f543914329`  
**Canonical Architecture:** `MEDICALPLAB_EVIDENCE_ENGINE_V1_1`  
**Milestone Closures:** PLAB (CLOSED), University Track (CLOSED), Evidence Engine (CLOSED)  

---

## 1. Executive Summary

This inventory audit establishes the complete classification, dependency mapping, and disposal plan for all 1,138 tracked files and 39 top-level paths in the repository prior to structural cleanup.

The objective is to transform the repository from an engineering/research workspace into a clean, mentor-ready, judge-ready, startup-grade AI medical education platform repository while strictly maintaining:
1. Zero regressions in active product runtime (`src/medicalplab/`).
2. Zero regressions in automated verification tests (`tests/`).
3. Complete defense of verified scientific reproducibility claims.
4. Complete retention of governance, safety, and evidence firewall closure reports (`reports/release/`).
5. Complete adherence to the non-negotiable safety rules (no model retraining, no private publisher data import, no force pushing, no git history rewriting).

---

## 2. Directory-by-Directory Structural Audit

### `.github/`
- **Current Purpose:** CI/CD workflow automation for continuous deployment.
- **Tracked Files:** 1 (`.github/workflows/deploy-cloud-run.yml`)
- **Primary Category:** `ACTIVE_DEPLOYMENT`
- **Real Dependencies:** GitHub Actions runtime, Google Cloud Run service `medicalplab-api`.
- **Decision:** `KEEP`
- **Reason:** Provides active automated deployment pipeline for Google Cloud Run container service.
- **Risk:** Low. Removing would break automated deployment.

---

### `archive/`
- **Current Purpose:** Historical frontend components and pitch/championship demo prototypes from earlier hackathon sprint iterations (`archive/frontend/components/battle`, `archive/frontend/components/founder`, `archive/frontend/components/championship`, etc.).
- **Tracked Files:** 74 files
- **Primary Category:** `HISTORICAL` / `LEGACY`
- **Real Dependencies:** Zero. Exhaustive repository-wide dependency trace confirmed zero imports in `frontend/src/`, `src/`, `tests/`, and CI workflows.
- **Decision:** `REMOVE_FROM_ACTIVE_TREE`
- **Reason:** Clutters the repository with speculative competition/pitch UI components that do not reflect the focused two-lane product reality (University Learning & PLAB Preparation). Preserved in Git history.
- **Risk:** Zero. No runtime or test code references this directory.

---

### `configs/`
- **Current Purpose:** Declarative configuration files for domain adaptation, retrieval tuning, and safety calibration.
- **Tracked Files:** 5 (`configs/qwen4b_domain_adaptation.json`, `configs/renal_v4_retrieval_config.json`, `configs/renal_v4_safety_config.json`, and SHA256 sidecars).
- **Primary Category:** `ACTIVE_CONFIG` / `REPRODUCIBILITY_ASSET`
- **Real Dependencies:** `tests/renal/test_benchmark_integrity.py` line 112 directly loads and asserts `configs/qwen4b_domain_adaptation.json`.
- **Decision:** `KEEP`
- **Reason:** Essential for configuration reproducibility and active domain adaptation regression tests.
- **Risk:** High if removed (causes test failures in `test_benchmark_integrity.py`).

---

### `Data/`
- **Current Purpose:** Public-safe accredited medical knowledge corpus (PubMed Central open-access articles DOC-PMC-RENAL-0001 to 0016), University question banks (`Data/university/questions.json`), public-safe PLAB questions (`Data/questions/cardiorespiratory_batch_1.json`), snapshot metadata, and historical chunking experiments.
- **Tracked Files:** 175 files
- **Sub-allocations:**
  - `Data/raw/renal_v1/`: 16 XML files (PMC open access) -> `ACTIVE_PUBLIC_SAFE_EVIDENCE` -> `KEEP`
  - `Data/processed/renal_v1/`: 64 JSON files (JATS, sections, chunks, quality) -> `RAG_CANONICAL_CORPUS` -> `KEEP`
  - `Data/university/questions.json`: University track question bank -> `UNIVERSITY_CONTENT` -> `KEEP`
  - `Data/questions/`: PLAB question batches and review queues -> `PLAB_PUBLIC_SAFE_CONTENT` -> `KEEP`
  - `Data/metadata/`: Corpus snapshot manifests and license registries -> `REPRODUCIBILITY_METADATA` -> `KEEP`
  - `Data/experiments/renal/chunking/`: 48 JSON files across historical chunking sweeps (A_250, B_400, C_section_aware) -> `HISTORICAL_EXPERIMENT_DATA` -> `REMOVE_FROM_ACTIVE_TREE`
- **Real Dependencies:** Runtime evidence engine (`src/medicalplab/evidence_engine/service.py`) dynamically loads `Data/processed/renal_v1/`. University API dynamically loads `Data/university/questions.json`. PLAB pilot service loads `Data/questions/`. Tests assert corpus snapshot integrity. `Data/experiments/renal/chunking/` has zero active runtime or test dependencies.
- **Decision:** `CONSOLIDATE` (Retain all active runtime, university, PLAB, and corpus data; remove obsolete 48 historical chunking sweep files from `Data/experiments/`).
- **Reason:** Reduces active data tree clutter while keeping all active runtime and reproducibility assets 100% intact.
- **Risk:** Zero for removing `Data/experiments/renal/chunking/` (verified zero references in `src/` and `tests/`).

---

### `deploy/`
- **Current Purpose:** Operational deployment scripts (`deploy_cloud_run.ps1`, `deploy_cloud_run.sh`) for container deployment to Google Cloud Run.
- **Tracked Files:** 2 files
- **Primary Category:** `ACTIVE_DEPLOYMENT`
- **Real Dependencies:** DevOps deployment execution.
- **Decision:** `KEEP`
- **Reason:** Provides maintainable, documented deployment automation for DevOps and platform operators.
- **Risk:** Low.

---

### `docs/`
- **Current Purpose:** Architectural documentation, track specifications, clinical safety standards, and demo guides.
- **Tracked Files:** 15 files
- **Primary Category:** `USER_DOCUMENTATION` / `DEVELOPER_DOCUMENTATION`
- **Real Dependencies:** `tests/test_renal_v5_closure.py` and `tests/test_renal_v6_closure.py` assert the presence and contents of `docs/demo/RENAL_TECHNICAL_RESULTS_V5.md` and `RENAL_TECHNICAL_RESULTS_V6.md`.
- **Decision:** `CONSOLIDATE`
  - Form the 9 canonical documents:
    1. `docs/ARCHITECTURE.md` (Product architecture, system topology, Next.js/FastAPI separation)
    2. `docs/AI_SYSTEM.md` (GenAI taxonomy: generative vs retrieval vs reranking vs deterministic)
    3. `docs/RAG_ARCHITECTURE.md` (Evidence Engine V1.1 specification, routing, BM25, RRF, Qwen3-Reranker-0.6B)
    4. `docs/UNIVERSITY_TRACK.md` (Undergraduate adaptive learning, Renal Physiology MVP, mastery tracking)
    5. `docs/PLAB_EVIDENCE.md` (Licensing preparation, evidence eligibility, quarantine, provenance, human review boundary)
    6. `docs/CLINICAL_SAFETY.md` (Fail-closed abstention, claim verification, contraindicated condition interception)
    7. `docs/DEMO_GUIDE.md` (Step-by-step 3-5 minute mentor/judge walkthrough)
    8. `docs/DEVELOPMENT.md` (Setup, environment isolation, testing workflows, branch protocol)
    9. `docs/DEPLOYMENT.md` (Consolidated single-source deployment guide for Cloud Run, Render, Vercel, Docker)
  - Retain `docs/demo/` for historical closure tests.
- **Reason:** Replaces scattered, duplicate root documentation with a unified, professional docs tree.
- **Risk:** Zero (carefully maintaining required test files).

---

### `evaluation/`
- **Current Purpose:** Benchmark datasets, query-relevance judgements (qrels), calibration sets, and firewall isolation suites across RAG versions (v1-v7 and Evidence Engine V1.1).
- **Tracked Files:** 128 files
- **Sub-allocations:**
  - `evaluation/evidence_engine/`: Canonical Evidence Engine V1.1 evaluation datasets (claim_verifier_benchmark.json, final_product_test.json, product_dev_v2.json, product_dev_v3.json, pubmedqa_external_benchmark.json, safety_eval.json, and sidecars) -> `REPRODUCIBILITY_ASSET` -> `KEEP`
  - `evaluation/renal/`: DEV-1, DEV-2, and versioned datasets tested by `test_renal_v*` firewall assertions -> `REPRODUCIBILITY_ASSET` -> `KEEP`
  - `evaluation/renal/audits/preflight-invalid-v2/`: 8 files from invalid historical preflights -> `HISTORICAL` -> `REMOVE_FROM_ACTIVE_TREE`
  - `evaluation/history/`: 1 file (`gemini_availability_checkpoint.json`) -> `HISTORICAL` -> `REMOVE_FROM_ACTIVE_TREE`
  - `evaluation/audits/`: 2 files -> `HISTORICAL` -> `REMOVE_FROM_ACTIVE_TREE`
- **Real Dependencies:** `tests/test_renal_v7_closure.py`, `tests/renal/test_renal_v4_1.py`, `tests/stage_b/test_characterization.py` assert integrity of specific evaluation files.
- **Decision:** `CONSOLIDATE` (Retain all required firewall and V1.1 reproducibility datasets; prune invalid preflight and obsolete history checkpoints).
- **Reason:** Defends every public metric while stripping redundant intermediate experimental junk.
- **Risk:** Zero (verified zero references to pruned paths).

---

### `examples/`
- **Current Purpose:** Example JSON schemas and payloads for chunks, documents, questions, and sources.
- **Tracked Files:** 10 files
- **Primary Category:** `DEVELOPER_DOCUMENTATION` / `REPRODUCIBILITY_ASSET`
- **Real Dependencies:** Zero code dependencies in `src/` or `tests/`.
- **Decision:** `KEEP`
- **Reason:** Demonstrates schema compliance and data payload contracts for external contributors and judges. Minimal footprint (10 lightweight JSON/py files).
- **Risk:** None.

---

### `frontend/`
- **Current Purpose:** Canonical Next.js 16.3.4 (React 19, Turbopack, TailwindCSS v4) production client application.
- **Tracked Files:** 38 files
- **Primary Category:** `FRONTEND_RUNTIME`
- **Real Dependencies:** Node.js, Next.js build pipeline, FastAPI backend endpoints (`/api/v1/university/*`, `/ai/chat`, `/api/v1/evidence/query`, `/student/*`).
- **Decision:** `KEEP`
- **Reason:** Fully functional, verified frontend passing `npm run build` and `npm run lint` with zero errors.
- **Risk:** N/A. Core product asset.

---

### `models/`
- **Current Purpose:** Serialized historical evidence classifiers and soft fusion models.
- **Tracked Files:** 6 files
- **Primary Category:** `HISTORICAL` / `REPRODUCIBILITY_ASSET`
- **Real Dependencies:** `tests/renal/test_renal_v4_1.py` line 411 asserts `models/renal_v4_evidence_classifier.pkl` presence and SHA; `tests/renal/test_renal_v3_1.py` references `models/renal_v31_evidence_classifier.pkl`.
- **Decision:** `KEEP`
- **Reason:** Required by active frozen artifact regression tests.
- **Risk:** High if removed (breaks `test_renal_v4_1.py`).

---

### `notebooks/`
- **Current Purpose:** Stage-B Colab demonstration notebook (`notebooks/stage_b_colab.ipynb`).
- **Tracked Files:** 1 file
- **Primary Category:** `REPRODUCIBILITY_ASSET`
- **Real Dependencies:** Referenced in `docs/stage_b.md` as interactive benchmark demonstration.
- **Decision:** `KEEP`
- **Reason:** Represents minimal defensible reproducibility notebook as instructed in Section 14.
- **Risk:** None.

---

### `reports/`
- **Current Purpose:** Benchmark reports, ablation analyses, forensic post-mortems, and release closure artifacts.
- **Tracked Files:** 164 files
- **Sub-allocations:**
  - `reports/release/`: 14 files (closure reports, RAG performance, university track closure, PLAB v9 summary) -> `RELEASE_EVIDENCE` -> `KEEP`
  - `reports/evidence_engine/`: 10 files (V1.1 dev/test reports) -> `RELEASE_EVIDENCE` -> `KEEP`
  - `reports/renal_v6/`: 19 files -> `REPRODUCIBILITY_ASSET` -> `KEEP` (tested by `test_renal_v6_closure.py`)
  - `reports/renal_v7/`: 20 files -> `REPRODUCIBILITY_ASSET` -> `KEEP` (tested by `test_renal_v7_closure.py`)
  - `reports/renal_v5/`: 41 files -> `REPRODUCIBILITY_ASSET` -> `KEEP` (tested by `test_renal_v5_closure.py`)
  - `reports/renal_v4/`: 12 files -> `REPRODUCIBILITY_ASSET` -> `KEEP` (tested by `test_renal_v4_1.py`)
  - `reports/renal_v3/`: 25 files -> `REPRODUCIBILITY_ASSET` -> `KEEP`
  - Loose files in `reports/`: 23 files (v1/v2 ablations and historical JSON dumps) -> `HISTORICAL` -> `CONSOLIDATE`
- **Decision:** `CONSOLIDATE` (Preserve all release, evidence engine, and test-asserted closure reports; prune unreferenced loose historical report dumps).
- **Reason:** Defends every benchmark claim and closure invariant while maintaining report hygiene.
- **Risk:** Zero.

---

### `schemas/`
- **Current Purpose:** Formal JSON schema specifications for chunks, documents, questions, sources, and evaluation protocols.
- **Tracked Files:** 10 files
- **Primary Category:** `ACTIVE_CONFIG` / `DEVELOPER_DOCUMENTATION`
- **Real Dependencies:** Schema validation contracts.
- **Decision:** `KEEP`
- **Reason:** Enforces contract specifications across data ingestion and evaluation pipelines.
- **Risk:** Low.

---

### `Scripts/`
- **Current Purpose:** Ingestion, evaluation, calibration, and benchmarking utility scripts.
- **Tracked Files:** 281 files
- **Breakdown:**
  - Transient debug/scratch scripts (`Scripts/_*`): 88 files -> `DEBUG` / `HISTORICAL` -> `REMOVE_FROM_ACTIVE_TREE` (Zero references across codebase).
  - Unused historical one-off runners: ~120 files -> `HISTORICAL` / `OBSOLETE` -> `REMOVE_FROM_ACTIVE_TREE`.
  - Active product, evaluation, and test-dependent scripts: ~73 files -> `ACTIVE_PRODUCT` / `ACTIVE_EVALUATION` / `ACTIVE_MAINTENANCE` -> `KEEP`
- **Real Dependencies:** Tests directly import:
  - `Scripts/download_pmc_xml.py` (by `tests/test_download_pmc_xml.py`)
  - `Scripts/close_plab_v9.py` (by `tests/plab/v9/test_final_plab_closure.py`)
  - `Scripts/build_qwen4b_retrieval_train.py` (by `tests/renal/test_qwen4b_domain_adaptation.py`)
  - `Scripts/train_qwen4b_retrieval_lora.py` (by `tests/renal/test_qwen4b_domain_adaptation.py`)
  - `Scripts/validate_qwen4b_train_firewall.py` (by `tests/renal/test_qwen4b_firewall_*.py`)
  - `Scripts/qwen4b_adaptation_common.py` (by `tests/renal/test_benchmark_integrity.py`)
  - `Scripts/validate_product_dev_v3_adjudication.py` (by `tests/renal/test_benchmark_integrity.py`)
  - `Scripts/build_product_dev_v3_reconstruction_packets.py` (by `tests/renal/test_benchmark_integrity.py`)
  - Ingestion, validation, and benchmarking tools (`run_canonical_rag_benchmark.py`, `build_university_bank.py`, `validate_chunks.py`, etc.) are active maintenance utilities.
- **Decision:** `CONSOLIDATE` (Prune 88 `Scripts/_*` debug scratch scripts and unreferenced historical runners; retain all active utilities and test-imported modules).
- **Reason:** Removes dozens of scripts whose ad-hoc names make the repository look unfinished, preserving a clean, continuing-purpose toolset.
- **Risk:** Zero (confirmed zero references to pruned scripts).

---

### `src/`
- **Current Purpose:** Production source code of the MedicalPlab platform (`medicalplab/`).
- **Tracked Files:** 109 files
- **Primary Category:** `BACKEND_RUNTIME` / `AI_RUNTIME` / `UNIVERSITY_RUNTIME` / `PLAB_RUNTIME`
- **Real Dependencies:** The entire application runtime and test suite.
- **Decision:** `KEEP`
- **Reason:** The product core is closed and immutable per safety guidelines.
- **Risk:** Zero.

---

### `tests/`
- **Current Purpose:** Comprehensive automated verification suite (646 unit, integration, firewall, and contract tests).
- **Tracked Files:** 95 files
- **Primary Category:** `ACTIVE_TEST`
- **Real Dependencies:** Pytest runner, CI/CD pipeline.
- **Decision:** `KEEP`
- **Reason:** Non-negotiable safety rule: "Do NOT remove tests to make the repo smaller."
- **Risk:** Zero.

---

### Root-Level Files Audit

| File | Category | Decision | Rationale |
| :--- | :--- | :--- | :--- |
| `main.py` | `BACKEND_RUNTIME` | `KEEP` | Canonical local & demo FastAPI entrypoint (Socratic AI chat, University API, direct evidence query, Stage-G platform routing). |
| `production_main.py` | `BACKEND_RUNTIME` | `KEEP` | Strict pilot/production fail-closed entrypoint (enforces data integrity manifests, governance checks, fail-closed abstention). |
| `README.md` | `USER_DOCUMENTATION` | `KEEP` (REWRITE) | Root entrypoint document. Rebuilt from current reality to present the two product lanes, real GenAI architecture, and verified metrics. |
| `.env.example` | `ACTIVE_CONFIG` | `KEEP` | Configuration template with safe placeholders only. |
| `.gitignore` | `ACTIVE_CONFIG` | `KEEP` | Updated to ensure no caches, virtual environments, SQLite DBs, or temp files are tracked. |
| `pyproject.toml` | `ACTIVE_BUILD` | `KEEP` | Source of truth for Python build and project dependencies. |
| `requirements.txt` | `ACTIVE_BUILD` | `KEEP` | Pinned production backend requirements for Docker and Cloud Run. |
| `requirements-retrieval.txt` | `ACTIVE_BUILD` | `KEEP` | Pinned retrieval and reranker dependencies (transformers, sentence-transformers, accelerate). |
| `requirements-benchmark.txt` | `ACTIVE_BUILD` | `KEEP` | Pinned evaluation and benchmarking dependencies. |
| `uv.lock` | `ACTIVE_BUILD` | `KEEP` | Deterministic lockfile for core Python dependencies. |
| `package.json` | `FRONTEND_RUNTIME` | `KEEP` | Root npm script runner delegating `dev`, `build`, `start`, `lint` to `frontend/`. |
| `Dockerfile` | `ACTIVE_DEPLOYMENT` | `KEEP` | Multi-stage, non-root production container specification for Google Cloud Run / HF Spaces. |
| `cloudbuild.yaml` | `ACTIVE_DEPLOYMENT` | `KEEP` | Google Cloud Build pipeline specification for container image builds. |
| `render.yaml` | `ACTIVE_DEPLOYMENT` | `KEEP` | Render PaaS deployment blueprint for `production_main:app`. |
| `Procfile` | `ACTIVE_DEPLOYMENT` | `KEEP` | Heroku/PaaS web process definition. |
| `.dockerignore` | `ACTIVE_BUILD` | `KEEP` | Container build exclusion rules. |
| `.editorconfig` | `ACTIVE_CONFIG` | `KEEP` | Multi-editor formatting standards. |
| `.gitattributes` | `ACTIVE_CONFIG` | `KEEP` | Git line ending and binary normalization rules. |
| `.python-version` | `ACTIVE_CONFIG` | `KEEP` | Pinned Python 3.11/3.12 runtime version for pyenv/uv. |
| `DEPENDENCY_SETUP.md` | `DUPLICATE` | `CONSOLIDATE` -> `docs/DEVELOPMENT.md` | Overlapping setup documentation. Consolidated into `docs/DEVELOPMENT.md`. |
| `DEPLOYMENT.md` | `DUPLICATE` | `CONSOLIDATE` -> `docs/DEPLOYMENT.md` | Moved and unified with production deployment guide in `docs/DEPLOYMENT.md`. |
| `PRODUCTION_DEPLOYMENT.md` | `DUPLICATE` | `CONSOLIDATE` -> `docs/DEPLOYMENT.md` | Merged into `docs/DEPLOYMENT.md`. |
| `README_HF.md` | `DUPLICATE` | `CONSOLIDATE` -> `docs/DEPLOYMENT.md` | Merged HF Spaces deployment instructions into `docs/DEPLOYMENT.md`. |
| `CONTRIBUTING.md` | `DUPLICATE` | `CONSOLIDATE` -> `docs/DEVELOPMENT.md` | Merged contributor guidelines into `docs/DEVELOPMENT.md`. |

---

## 3. Summary Classification Matrix

| Category | Initial File Count | Planned Action | Final Retained Scope |
| :--- | :---: | :--- | :--- |
| `FRONTEND_RUNTIME` | 39 | KEEP | Canonical Next.js frontend and root npm scripts |
| `BACKEND_RUNTIME` | 111 | KEEP | Core Python engine, FastAPI entrypoints (`main.py`, `production_main.py`) |
| `ACTIVE_TEST` | 95 | KEEP | All 646 automated tests preserved 100% |
| `ACTIVE_CONFIG` | 10 | KEEP | pyproject, gitignore, env.example, configs/ |
| `ACTIVE_DEPLOYMENT` | 7 | KEEP | Dockerfile, cloudbuild, render, deploy scripts |
| `USER_DOCUMENTATION` | 15 | CONSOLIDATE | 9 intentional, high-signal documents in `docs/` + `docs/demo/` |
| `RELEASE_EVIDENCE` | 24 | KEEP | Verified closure reports in `reports/release/` and `reports/evidence_engine/` |
| `REPRODUCIBILITY_ASSET` | ~250 | PRUNE OBSOLETE | Prune unreferenced preflight mistakes; retain all verified data and sidecars |
| `HISTORICAL` / `LEGACY` | 74 | REMOVE | Prune `archive/frontend/` (zero dependencies) |
| `DEBUG` / `SCRATCH` | 88 | REMOVE | Prune `Scripts/_*` transient inspection scripts (zero dependencies) |

This inventory completes Phase 1 of the productization roadmap. Structural cleanup may proceed strictly following these decisions.
