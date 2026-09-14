# MEDICALPLAB — REPOSITORY ARCHITECTURE V2 AUDIT & IMPLEMENTATION PLAN
**Document ID:** `reports/release/repository_architecture_v2_plan.md`  
**Milestone:** Gate 1 Architecture Audit & Refactor Blueprint  
**Branch:** `repo-architecture-v2`  
**Base Commit:** `f0db2716222a6a0aef559658620e79dc617cb581`  
**Release Tag:** `v1.0.0-hackathon` (Frozen & Immutable)  
**Status:** `GATE_1_COMPLETE — PENDING_HUMAN_APPROVAL`  
**Required Approval Phrase:** `PROCEED WITH ARCHITECTURE V2`

---

## EXECUTIVE SUMMARY

MedicalPlab is an evidence-grounded medical education platform combining adaptive undergraduate learning (University track) with fail-closed licensing preparation (PLAB track), powered by a shared Canonical Evidence Engine (V1.1).

This architectural audit was conducted under a strict **Zero-Regression** mandate following closed productization and independent QA verification. A senior engineer, technical judge, or mentor reviewing this repository should immediately comprehend its architectural boundaries within approximately 10 seconds.

Our empirical investigation yields three foundational conclusions:
1. **Hypothetical `research/` Consolidation Rejected**: Moving `evaluation/`, `models/`, or `notebooks/` into a nested `research/` directory would directly break active governance tests (e.g. `tests/renal/test_renal_v4_1.py:398-413` asserting `rel_path` from root for `FROZEN_ARTIFACTS`), invalidate immutable cryptographic SHA-256 sidecars (e.g. `configs/renal_v4_safety_config.json.sha256`), and violate sealed historical milestones. Therefore, `evaluation/`, `models/`, and `notebooks/` **must remain at repository root**.
2. **Hypothetical `tools/` Rename Rejected**: `Scripts/` is directly imported as a Python package and module by active test suites (`tests/plab/v9/test_final_plab_closure.py` importing `from Scripts.close_plab_v9 import ...`, `tests/test_download_pmc_xml.py` importing `from Scripts import download_pmc_xml`, and multiple `tests/renal/test_*.py` configuring `sys.path.insert(0, ... / "Scripts")`). Renaming or fragmenting `Scripts/` into `tools/` introduces immediate import breakage and high regression risk. Therefore, `Scripts/` **must remain at repository root**.
3. **Dual Entrypoints Justified (`KEEP_BOTH`)**: `main.py` (local development and permissive demo platform) and `production_main.py` (strict fail-closed pilot/production gateway with manifest integrity enforcement) serve strictly decoupled environments and lifecycles. Consolidating them would compromise fail-closed pilot isolation. Both entrypoints **must be retained**.

---

## A. CURRENT ROOT INVENTORY

The repository contains exactly **34** root-level entries (excluding the `.git` directory), consisting of **15 directories** and **19 files**. Every item was inspected and audited for its operational role, consumers, and root necessity.

| # | Item Name | Type | Purpose | Major Consumers | Root Placement Necessity |
|---|---|---|---|---|---|
| 1 | `.github/` | Directory | GitHub Actions workflows and platform automation | GitHub Actions CI/CD runner | **MUST** (GitHub platform requirement) |
| 2 | `configs/` | Directory | Executable configurations and cryptographic SHA sidecars | RAG engine, evaluation pipelines, governance tests | **MUST** (Referenced by tests and SHA sidecars) |
| 3 | `Data/` | Directory | Active public-safe runtime data (chunks, manifests, questions) | Evidence Engine, University, PLAB, Docker image | **MUST** (Active runtime data root) |
| 4 | `deploy/` | Directory | Cloud Run deployment helper scripts | DevOps engineers, local shell/Cloud Shell runners | **YES** (Properly isolated deployment root) |
| 5 | `docs/` | Directory | Product, architecture, clinical safety, and dev docs | Developers, technical judges, mentors | **MUST** (Standard documentation root) |
| 6 | `evaluation/` | Directory | Ground truth datasets, split records, heldout benchmarks | RAG benchmark suite, governance tests | **MUST** (Hardcoded in tests & SHA sidecars) |
| 7 | `examples/` | Directory | Formal schema payload examples and integration tests | Integration developers, schema validation tools | **YES** (Referenced by `validate_chunks.py`) |
| 8 | `frontend/` | Directory | Next.js 16 / React 19 web application | Vercel deployment, frontend engineers | **MUST** (Canonical web application workspace) |
| 9 | `models/` | Directory | Frozen classifier models and SHA-256 sidecars | `test_renal_v4_1.py`, runtime classifiers | **MUST** (Asserted bit-for-bit by test suite) |
| 10 | `notebooks/` | Directory | Stage-B Colab demonstration notebook | `prepare_stage_b_bundle.py`, researchers | **YES** (Standard reproducible notebook location) |
| 11 | `reports/` | Directory | Benchmark reports, release evidence, milestone audits | Mentors, judges, compliance, CI verification | **MUST** (Release evidence must be discoverable) |
| 12 | `schemas/` | Directory | Formal JSON Schema contracts for data objects | Data ingestion, chunk validators, Dockerfile | **MUST** (Referenced by Dockerfile & validators) |
| 13 | `Scripts/` | Directory | Data build, ingestion, validation, and closure tools | Test suites, pipeline runners, developers | **MUST** (Directly imported by Python test suites) |
| 14 | `src/` | Directory | Primary Python application code (`medicalplab`) | FastAPI gateways, test suites, Docker image | **MUST** (Standard Python `src` layout) |
| 15 | `tests/` | Directory | Automated regression, safety, governance test suite | Pytest, CI runners, QA engineers | **MUST** (Standard test discovery root) |
| 16 | `.dockerignore` | File | File exclusion patterns for Docker container builds | Docker CLI, Cloud Build | **MUST** (Docker build context requirement) |
| 17 | `.editorconfig` | File | Consistent IDE formatting and indentation rules | Developer IDEs (VS Code, Antigravity, Cursor) | **MUST** (Standard editorconfig convention) |
| 18 | `.env.example` | File | Template configuration for developer environment vars | Local developers, onboarding engineers | **MUST** (Standard environment template) |
| 19 | `.gitattributes` | File | Git line ending and binary file handling rules | Git client | **MUST** (Git repository requirement) |
| 20 | `.gitignore` | File | Git untracked and excluded file patterns | Git client | **MUST** (Git repository requirement) |
| 21 | `.python-version`| File | Pyenv / toolchain Python version pinning (`3.11`) | Pyenv, asdf, uv, developer tooling | **MUST** (Toolchain version pinning convention) |
| 22 | `cloudbuild.yaml`| File | Google Cloud Build CI/CD pipeline definition | Google Cloud Build, GCP triggers | **MUST** (`gcloud builds submit` root default) |
| 23 | `Dockerfile` | File | Multi-stage container definition for Cloud Run | Docker CLI, Google Cloud Run, Cloud Build | **MUST** (Standard container build root) |
| 24 | `main.py` | File | Local development and demo FastAPI gateway | Developer local uvicorn, `Procfile` | **MUST** (Canonical local dev entrypoint) |
| 25 | `package.json` | File | Root npm script runner forwarding to frontend | Node.js developers (`npm run dev`) | **YES** (Root command wrapper convenience) |
| 26 | `Procfile` | File | Heroku/Dokku process runner declaration | Legacy PaaS platforms | **NO** (Obsolete; zero active dependencies) |
| 27 | `production_main.py`| File| Strict fail-closed pilot/production FastAPI gateway | Dockerfile, Cloud Run, `render.yaml`, tests | **MUST** (Canonical production entrypoint) |
| 28 | `pyproject.toml`| File | Canonical Python packaging, dependencies, tool config | `pip`, `uv`, `pytest`, `setuptools` | **MUST** (Standard Python project metadata) |
| 29 | `README.md` | File | Primary repository overview and architecture guide | Public viewers, mentors, judges, developers | **MUST** (Standard repository landing document) |
| 30 | `render.yaml` | File | Render PaaS infrastructure-as-code blueprint | Render platform automated deployment | **MUST** (Render repository blueprint requirement) |
| 31 | `requirements-benchmark.txt`| File| Colab/Linux benchmark pinned dependencies | Benchmark runners, Colab environments | **YES** (Isolated benchmark environment) |
| 32 | `requirements-retrieval.txt`| File| Local GPU/CUDA retrieval stack dependencies | Retrieval researchers, GPU workstations | **YES** (Isolated GPU environment) |
| 33 | `requirements.txt`| File | Production container and deployment dependencies | `Dockerfile`, `render.yaml`, CI environments | **MUST** (Standard Python deployment dependency) |
| 34 | `uv.lock` | File | Deterministic dependency lockfile | `uv` package manager | **MUST** (Standard uv lockfile convention) |

---

## B. CLASSIFICATION

Every root-level item is assigned exactly one primary classification. There are **0 UNKNOWN** items.

| Primary Classification | Count | Items Included |
|---|---|---|
| **CORE_PRODUCT** | 4 | `src/`, `frontend/`, `docs/`, `README.md` |
| **ACTIVE_RUNTIME** | 2 | `main.py`, `production_main.py` |
| **ACTIVE_DATA** | 1 | `Data/` |
| **ACTIVE_TEST** | 1 | `tests/` |
| **ACTIVE_CONFIG** | 5 | `pyproject.toml`, `requirements.txt`, `uv.lock`, `configs/`, `schemas/` |
| **ACTIVE_DEPLOYMENT** | 3 | `cloudbuild.yaml`, `Dockerfile`, `deploy/` |
| **DEVELOPER_TOOLING** | 6 | `Scripts/`, `examples/`, `package.json`, `.editorconfig`, `.env.example`, `.python-version` |
| **RESEARCH_REPRODUCIBILITY** | 4 | `evaluation/`, `models/`, `notebooks/`, `requirements-benchmark.txt` |
| **RELEASE_EVIDENCE** | 1 | `reports/` |
| **FRAMEWORK_REQUIRED_ROOT** | 4 | `.github/`, `.dockerignore`, `.gitattributes`, `.gitignore` |
| **OPTIONAL_DEPLOYMENT** | 2 | `render.yaml`, `requirements-retrieval.txt` |
| **LEGACY** | 1 | `Procfile` |
| **REDUNDANT** | 0 | None |
| **UNKNOWN** | **0** | **None (Fully Resolved)** |

---

## C. DEPENDENCY GRAPH

For each candidate structural change or move, the full downstream dependency graph was traced across the entire codebase:

### 1. `evaluation/` & `models/` (Candidate for `research/`)
- **Runtime Consumers:**
  - `src/medicalplab/stage_b/evidence_loader.py` (references schema and data paths).
  - `configs/renal_v4_safety_config.json` (explicitly points to `models/renal_v4_evidence_classifier.pkl`).
- **Test Consumers:**
  - `tests/renal/test_renal_v4_1.py:398-413` asserts exact paths and SHA-256 hashes of:
    - `evaluation/renal/renal-heldout-v2-final.json`
    - `evaluation/renal/v3/renal-heldout-v3-final.json`
    - `evaluation/renal/v3/renal-v3-safety-test-2.json`
    - `evaluation/renal/v4/renal-heldout-v4-final.json`
    - `evaluation/renal/v4/renal-safety-test-v4.json`
    - `models/renal_v4_evidence_classifier.pkl`
  - `tests/test_renal_v5_reranker_objective.py:32-36` asserts `_ROOT / "evaluation/renal/v5/..."`.
  - `tests/test_renal_v7_closure.py:34-38` asserts `_ROOT / "evaluation/renal/v7/..."`.
  - `tests/stage_b/test_characterization.py:49-62` asserts `evaluation/evidence_sufficiency_calibration_v1.json` and `evaluation/results/evidence_sufficiency_retrieval_only_baseline_v1.json`.
  - `tests/renal/test_qwen4b_firewall_known_training.py:29-56` asserts `evaluation/renal/v7/renal-train-dev-v7.json` and `evaluation/renal/v5/renal-rerank-dev-a-v5.json`.
- **Cryptographic SHA Sidecars:**
  - `configs/renal_v4_safety_config.json.sha256` (seals `configs/renal_v4_safety_config.json` which embeds `models/renal_v4_evidence_classifier.pkl`).
  - `models/renal_v4_evidence_classifier.pkl.sha256`.
- **Verdict:** Moving `evaluation/` or `models/` breaks active test suites and invalidates cryptographic security firewalls.

### 2. `Scripts/` (Candidate for `tools/`)
- **Python Import Consumers:**
  - `tests/plab/v9/test_final_plab_closure.py:151-158`: `from Scripts.close_plab_v9 import build_v9_sources, SOURCE_SPECS`
  - `tests/test_download_pmc_xml.py:7`: `from Scripts import download_pmc_xml`
  - `tests/renal/test_benchmark_integrity.py:9`: `sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Scripts"))`
  - `tests/renal/test_qwen4b_domain_adaptation.py:5`: `sys.path.insert(0, str(ROOT / 'Scripts'))`
  - `tests/renal/test_qwen4b_firewall_empty.py:8`: `SCRIPTS = ROOT / "Scripts"`
  - `tests/renal/test_qwen4b_firewall_known_training.py:8`: `SCRIPTS = ROOT / "Scripts"`
  - `tests/renal/test_qwen4b_firewall_regression.py:5`: `SCRIPTS = ROOT / "Scripts"`
  - `Scripts/assemble_product_dev_v3_clean.py`: `import Scripts.assemble_product_dev_v2 as v2_asm`, `import Scripts.construct_product_dev_v3 as v3_const`
- **Subprocess Invocation Consumers:**
  - `Scripts/ingest_wave2_batch.py`: executes `Scripts/download_pmc_xml.py`, `Scripts/extract_pmc_jats.py`, `Scripts/adapt_pmc_to_canonical.py`, `Scripts/chunk_sections.py`, `Scripts/validate_chunks.py`, `Scripts/validate_chunk_integrity.py`.
- **Verdict:** Renaming or restructuring `Scripts/` into `tools/` causes immediate Python import failures in active PLAB, Renal, and PMC XML test suites.

### 3. `main.py` & `production_main.py` (Candidate for Entrypoint Consolidation)
- **`main.py` Consumers:**
  - `Procfile:1`: `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
  - `docs/DEVELOPMENT.md:63`: `uvicorn main:app --host 127.0.0.1 --port 8000 --reload`
  - `frontend/.env.example:11`: points to `localhost:8000` (`main:app`)
  - Permissive demo mode (`create_demo_platform()`)
- **`production_main.py` Consumers:**
  - `Dockerfile:31,48`: `COPY main.py production_main.py ./` and `CMD ["sh", "-c", "uvicorn production_main:app --host 0.0.0.0 --port ${PORT:-8080}"]`
  - `render.yaml:8`: `startCommand: uvicorn production_main:app --host 0.0.0.0 --port $PORT`
  - `tests/plab/test_pilot_acceptance.py:104-105`: dynamically loads `production_main` and verifies strict fail-closed enforcement
  - `docs/DEPLOYMENT.md`, `docs/ARCHITECTURE.md`, `README.md`
- **Verdict:** Both entrypoints are actively load-bearing and serve completely separate operational domains. Consolidation carries regression risk for Cloud Run and acceptance tests without tangible benefit.

### 4. `Procfile` (Candidate for Removal)
- **Runtime Consumers:** None (Cloud Run uses `Dockerfile`; Render uses `render.yaml`; local dev uses `uvicorn main:app`).
- **Test Consumers:** None.
- **CI Consumers:** None.
- **Documentation Consumers:** None (`docs/DEPLOYMENT.md` does not mention it).
- **Verdict:** Proved genuinely obsolete. Safe to remove in Gate 2.

---

## D. ROOT NECESSITY ANALYSIS

| Item | Distinction | Explicit Operational Justification |
|---|---|---|
| `src/` | **MUST LIVE AT ROOT** | Standard Python packaging root configured in `pyproject.toml` (`tool.setuptools.packages.find`). |
| `frontend/` | **MUST LIVE AT ROOT** | Standard monorepo workspace for Next.js 16 / Vercel web client. |
| `Data/` | **MUST LIVE AT ROOT** | Active runtime data root copied by `Dockerfile` (`COPY Data/ Data/`) and loaded by Evidence Engine. |
| `tests/` | **MUST LIVE AT ROOT** | Standard Pytest root discovery path (`testpaths = ["tests"]` in `pyproject.toml`). |
| `docs/` | **MUST LIVE AT ROOT** | Standard root documentation directory expected by GitHub and developers. |
| `reports/` | **MUST LIVE AT ROOT** | Release evidence and benchmark audits must remain easily discoverable at root. |
| `configs/` | **MUST LIVE AT ROOT** | Houses executable configs tied to cryptographic SHA-256 sidecars. |
| `schemas/` | **MUST LIVE AT ROOT** | Formal data contracts copied into production container (`COPY schemas/ schemas/`). |
| `Scripts/` | **MUST LIVE AT ROOT** | Directly imported as a top-level package by active test suites (`from Scripts...`). |
| `evaluation/`| **MUST LIVE AT ROOT** | Asserted by relative path from root in immutable test suites (`test_renal_v4_1.py`). |
| `models/` | **MUST LIVE AT ROOT** | Asserted by relative path and SHA-256 in immutable test suites (`test_renal_v4_1.py`). |
| `notebooks/` | **IMPORTANT** | Standard notebook location; referenced by `docs/stage_b.md` and `.dockerignore`. |
| `deploy/` | **IMPORTANT** | Cleanly isolates Cloud Run deployment scripts away from root. |
| `examples/` | **IMPORTANT** | Houses schema examples and test loader referenced by `validate_chunks.py`. |
| `.github/` | **MUST LIVE AT ROOT** | Platform-required root for GitHub Actions workflows. |
| `Dockerfile` | **MUST LIVE AT ROOT** | Default container context for `docker build` and `gcloud run deploy --source .`. |
| `cloudbuild.yaml`| **MUST LIVE AT ROOT**| Default pipeline file for Google Cloud Build (`gcloud builds submit`). |
| `production_main.py`| **MUST LIVE AT ROOT**| Referenced by `Dockerfile` (`uvicorn production_main:app`) and Cloud Run container. |
| `main.py` | **MUST LIVE AT ROOT** | Canonical local development entrypoint referenced in development guides. |
| `pyproject.toml`| **MUST LIVE AT ROOT**| Canonical packaging standard for Python builds (PEP 518/621). |
| `requirements.txt`| **MUST LIVE AT ROOT**| Consumed directly by `Dockerfile` and `render.yaml`. |
| `uv.lock` | **MUST LIVE AT ROOT** | Deterministic lockfile for `uv` package manager at repository root. |
| `render.yaml` | **MUST LIVE AT ROOT** | Render PaaS specification requires `render.yaml` at repository root. |
| `README.md` | **MUST LIVE AT ROOT** | Standard repository homepage across all Git platforms. |
| `package.json` | **IMPORTANT** | Convenience script runner for root-level npm operations (`npm run dev --prefix frontend`). |
| `Procfile` | **NEITHER** | Obsolete Heroku process definition with zero active consumers. |

---

## E. PROPOSED TARGET TREE

The proposed architecture prioritizes technical integrity, zero regressions, and senior-engineer clarity over artificial consolidation.

```
MedicalPlab-architecture-v2/
├── .github/                       # GitHub Actions CI/CD workflows (Cloud Run deployment)
├── configs/                       # Executable RAG configs with cryptographic SHA-256 sidecars
├── Data/                          # Active public-safe runtime data (chunks, manifests, questions)
├── deploy/                        # Cloud Run deployment automation scripts (Bash, PowerShell)
├── docs/                          # Architecture, clinical safety, deployment, and developer guides
├── evaluation/                    # Ground truth datasets & benchmarks asserted by governance tests
├── examples/                      # Formal schema payload examples and integration test scripts
├── frontend/                      # Next.js 16 / React 19 web application (deployed to Vercel)
├── models/                        # Frozen classifier artifacts with cryptographic SHA-256 sidecars
├── notebooks/                     # Stage-B Colab demonstration notebook
├── reports/                       # Benchmark reports, release evidence, and milestone closure audits
│   └── release/                   # Formal release audits, QA verifications, and architectural plans
├── schemas/                       # Formal JSON Schema data contracts (chunks, questions, sources)
├── Scripts/                       # Active engineering utilities, ingestion, and test-imported tools
├── src/                           # Core product runtime library (medicalplab backend & AI engine)
│   └── medicalplab/               # Evidence Engine, University track, PLAB service, Stage-G platform
├── tests/                         # Comprehensive automated test suite (Pytest)
├── .dockerignore                  # Docker container build exclusion rules
├── .editorconfig                  # Code formatting and indentation standards
├── .env.example                   # Local developer environment variables template
├── .gitattributes                 # Git line endings and attribute normalization
├── .gitignore                     # Git repository exclusion rules
├── .python-version                # Python runtime version pinning (3.11)
├── cloudbuild.yaml                # Google Cloud Build pipeline for Google Cloud Run
├── Dockerfile                     # Multi-stage production container build (Google Cloud Run)
├── main.py                        # Local development & demo FastAPI gateway
├── package.json                   # Root developer convenience script runner (updated metadata)
├── production_main.py             # Strict fail-closed pilot/production FastAPI gateway
├── pyproject.toml                 # Canonical Python package specification and tool configurations
├── README.md                      # Primary repository overview and architectural guide
├── render.yaml                    # Render PaaS blueprint for production_main:app
├── requirements-benchmark.txt     # Pinned dependencies for Colab/benchmarking environment
├── requirements-retrieval.txt     # Pinned dependencies for local GPU/CUDA retrieval stack
├── requirements.txt               # Pinned deployment dependencies for Docker and Cloud Run
└── uv.lock                        # Deterministic dependency lockfile for reproducible resolution
```

---

## F. EXACT MOVE MATRIX

In accordance with Section 44 (*"Challenge Default Assumptions"*, *"Technically superior beats cosmetically smaller. Every time."*), zero file moves are proposed.

| Source | Destination | Rationale | Runtime Dependencies | Import Dependencies | Test Dependencies | CI Dependencies | Deployment Dependencies | Doc Dependencies | Path Updates Required | Files Affected | Risk | Required Test Gate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *None* | *None* | Empirical investigation proved that moving `evaluation/`, `models/`, or `Scripts/` breaks active test assertions and cryptographic SHA sidecars. | N/A | N/A | N/A | N/A | N/A | N/A | None | 0 | None | N/A |

---

## G. KEEP MATRIX

| Item | Why It Stays | Root Requirement or Justification | Dependencies |
|---|---|---|---|
| `src/` | Core product code | Required by `pyproject.toml` and Python packaging | Used by all FastAPI gateways, tests, Docker |
| `frontend/` | Web product code | Canonical Next.js workspace for Vercel deployment | Decoupled web client |
| `Data/` | Active runtime data | Required by Evidence Engine and Docker container | `COPY Data/ Data/` in Dockerfile; RAG runtime |
| `tests/` | Verification suite | Standard Pytest root discovery (`testpaths = ["tests"]`) | Active regression, safety, governance suites |
| `docs/` | Project documentation | Primary documentation root for developers & judges | Referenced by README and developer workflows |
| `reports/` | Release evidence | Release evidence and audits must remain visible at root | Referenced by compliance and release tags |
| `configs/` | Executable configs | Houses configs with cryptographic SHA-256 sidecars | Referenced by RAG engine and test assertions |
| `schemas/` | Formal data contracts | Formal JSON Schemas copied into production container | `COPY schemas/ schemas/` in Dockerfile |
| `Scripts/` | Engineering utilities | Directly imported as a package by active test suites | `tests/plab/v9/`, `tests/test_download_pmc_xml.py` |
| `evaluation/`| Benchmark datasets | Asserted by relative path from root in test suites | `tests/renal/test_renal_v4_1.py:398-413` |
| `models/` | Frozen classifiers | Asserted by relative path and SHA-256 in test suites | `tests/renal/test_renal_v4_1.py:411` |
| `notebooks/` | Interactive demos | Stage-B Colab demonstration notebook location | `docs/stage_b.md`, `.dockerignore` |
| `deploy/` | Deployment scripts | Isolates Cloud Run PowerShell and Bash scripts | Local developers and DevOps engineers |
| `examples/` | Schema examples | Referenced by `Scripts/validate_chunks.py` | Schema validation and integration tooling |
| `Dockerfile` | Container build | Required at root by `docker build` and Cloud Run | Google Cloud Run, Cloud Build, Docker |
| `cloudbuild.yaml`| Cloud Build CI/CD | Expected at root by `gcloud builds submit` | Google Cloud Build automated deployment |
| `production_main.py`| Production gateway | Fail-closed pilot gateway required by Dockerfile | Dockerfile, Cloud Run, Render, acceptance tests |
| `main.py` | Development gateway | Local development and demo platform gateway | Local uvicorn development, demo exploration |
| `pyproject.toml`| Packaging spec | Standard Python packaging root (PEP 518/621) | Python build system, setuptools, pytest, uv |
| `requirements.txt`| Deployment deps | Consumed by `Dockerfile` and `render.yaml` | Cloud Run container build, Render PaaS |
| `requirements-retrieval.txt`| GPU stack | Isolated GPU retrieval dependencies | Local CUDA workstations |
| `requirements-benchmark.txt`| Colab stack | Isolated Linux/Colab benchmark dependencies | Colab and benchmark runners |
| `uv.lock` | Lockfile | Deterministic lockfile for `uv` package manager | Reproducible Python environments |
| `render.yaml` | PaaS blueprint | Render looks for `render.yaml` at repository root | Render PaaS deployment |
| `package.json`| Command wrapper | Convenience script runner for root npm commands | Node.js developers (`npm run dev`) |
| `README.md` | Homepage | Standard landing page across Git platforms | All users, mentors, judges |
| `.github/` | CI/CD workflows | GitHub platform requirement | GitHub Actions |
| `.dockerignore`| Build exclusion | Docker platform requirement | Docker CLI, Cloud Build |
| `.editorconfig`| Style rules | IDE toolchain standard | Developer IDEs |
| `.env.example` | Env template | Local onboarding standard | Local developers |
| `.gitattributes`| Git attributes | Git platform requirement | Git client |
| `.gitignore` | Git exclusions | Git platform requirement | Git client |
| `.python-version`| Python pinning | Pyenv/toolchain standard | Pyenv, asdf, uv |

---

## H. REMOVE MATRIX

Only one genuinely obsolete file was identified after rigorous dependency tracing.

| Item | Proof of Zero Runtime Dependencies | Proof of Zero Test Dependencies | Proof of Zero Deployment Dependencies | Proof of Zero Reproducibility Requirement | Proof of Zero Release-Evidence Requirement | Proof of Zero Documentation Requirement | Recommendation |
|---|---|---|---|---|---|---|---|
| `Procfile` | Cloud Run uses `Dockerfile` (`production_main:app`); Render uses `render.yaml`; local dev uses direct `uvicorn main:app`. | `git grep -n "Procfile"` across `tests/` yields 0 matches. | Not referenced in `.github/workflows/deploy-cloud-run.yml` or `cloudbuild.yaml`. | No benchmark or scientific audit references `Procfile`. | Not referenced in `reports/release/rag_final_benchmark.json` or milestone reports. | Not mentioned in `docs/` (`docs/DEPLOYMENT.md` omits it completely). | **REMOVE** in Gate 2 (or retain as `LEGACY` if zero-file-deletion policy strictly enforced). |

---

## I. DEPLOYMENT MATRIX

| Deployment Asset | Classification | Deployment Target | Evidence & Operational Role |
|---|---|---|---|
| `Dockerfile` | **CANONICAL** | Google Cloud Run (and local container) | Multi-stage production container build copying `src/`, `schemas/`, `Data/`, `production_main.py`. Starts `uvicorn production_main:app --host 0.0.0.0 --port ${PORT:-8080}` with unprivileged `appuser`. |
| `cloudbuild.yaml` | **CANONICAL** | Google Cloud Run | GCP Cloud Build pipeline definition. Builds image, pushes with `$COMMIT_SHA` and `latest` tags, and executes `gcloud run deploy medicalplab-api` with production env vars. |
| `.github/workflows/deploy-cloud-run.yml` | **CANONICAL** | Google Cloud Run | Automated GitHub Actions workflow triggering on push to `main` for runtime paths. Authenticates via GCP SA key and deploys container to Cloud Run. |
| `frontend/vercel.json` | **CANONICAL FRONTEND** | Vercel | Vercel platform configuration for Next.js 16 Turbopack deployment. |
| `deploy/deploy_cloud_run.sh` / `.ps1` | **SUPPORTED_OPTIONAL** | Google Cloud Run | Workstation and Cloud Shell automation scripts enabling one-command Cloud Run deployment via `gcloud run deploy --source .`. |
| `render.yaml` | **SUPPORTED_OPTIONAL** | Render PaaS | Blueprint deploying `medicalplab-api` using `production_main:app` with automated `/health` checking. |
| `Procfile` | **LEGACY** | Heroku / Dokku | Obsolete 51-byte file specifying `web: uvicorn main:app`. Zero active consumers in current infrastructure. |

---

## J. DEPENDENCY MANAGEMENT MATRIX

| File | Canonical / Role | Target Environment | Key Packages / Notes |
|---|---|---|---|
| `pyproject.toml` | **CANONICAL PYTHON SPEC** | Modern Python (3.11) dev & package builds | Core runtime: `jsonschema==4.26.0`, `pdfplumber==0.11.10`, `requests==2.34.2`. Optional groups: `renal-ml` (PyTorch, sentence-transformers, scikit-learn), `qwen4b-adaptation` (transformers, accelerate, peft, bitsandbytes). Configures `pytest` local caching. |
| `uv.lock` | **CANONICAL LOCKFILE** | Deterministic resolution | Pinned cross-platform lockfile for `uv` or modern pip-tools resolution. |
| `requirements.txt` | **CONTAINER & PROD COMPATIBILITY** | Docker container, Render PaaS, local pip | Pinned FastAPI web gateway stack: `fastapi>=0.110.0`, `uvicorn>=0.28.0`, `pydantic>=2.0.0`, `httpx>=0.27.0`, `pytest>=8.0.0`, `-e .`. |
| `requirements-retrieval.txt` | **OPTIONAL LOCAL GPU STACK** | Local CUDA workstations (cu128) | Validated stack for neural reranking: `accelerate==1.14.0`, `numpy==2.4.6`, `sentence-transformers==6.0.1`, `transformers==5.16.1`. |
| `requirements-benchmark.txt` | **BENCHMARK-ONLY STACK** | Dedicated Linux/Colab environment | Specific dependencies for Qwen AWQ benchmark reproduction: `transformers==4.51.3`, `accelerate==1.10.1`, `autoawq==0.2.9`, `numpy==1.26.4`. |
| `root package.json` | **COMMAND-WRAPPER** | Root-level developer tooling | Convenience scripts forwarding to frontend (`npm run dev --prefix frontend`, `build`, `lint`). Contains package description metadata. |
| `frontend/package.json` | **CANONICAL FRONTEND DEPS** | Next.js web application (Vercel) | Production dependencies: `next@16.3.4`, `react@19.2.8`, `lucide-react`, `tailwindcss@4`, `three`, `canvas-confetti`. |

---

## K. VERSIONING POLICY

The repository maintains three intentionally decoupled versioning tiers:

```
+-------------------------------------------------------------+
|  PRODUCT_RELEASE_VERSION: 1.0.0                             |
|  - Git Tag: v1.0.0-hackathon                                |
|  - Root package.json: "version": "1.0.0"                    |
|  - Release Evidence: MedicalPlab v1.0.0 Hackathon Release   |
+-------------------------------------------------------------+
         |                                           |
         v                                           v
+-------------------------------+   +-------------------------------+
| BACKEND_PACKAGE_VERSION: 0.2.0|   | FRONTEND_PACKAGE_VERSION:     |
| - pyproject.toml: "0.2.0"     |   |   0.1.0                       |
| - Library semver for package  |   | - frontend/package.json:      |
| - FastAPI Gateway: 1.1.0      |   |   "0.1.0"                     |
|   (production_main.py)        |   | - Independent Next.js UI      |
+-------------------------------+   +-------------------------------+
```

1. **`PRODUCT_RELEASE_VERSION` (`1.0.0`)**: Represents the unified product milestone frozen at Git tag `v1.0.0-hackathon`. Used in release documentation, public announcements, and the root `package.json` wrapper.
2. **`BACKEND_PACKAGE_VERSION` (`0.2.0`)**: Independent semantic version for the core Python library defined in `pyproject.toml`. Reflects library API stability across internal iterations. The FastAPI HTTP service layer in `production_main.py` separately reports API version `1.1.0`, corresponding to the Evidence Engine V1.1 and PLAB V9 production gateway.
3. **`FRONTEND_PACKAGE_VERSION` (`0.1.0`)**: Independent version for the Next.js web client defined in `frontend/package.json`. Follows modern web application continuous deployment cadences decoupled from backend library releases.

These versions are **intentionally independent** and must not be blindly synchronized.

---

## L. ENTRYPOINT DECISION

**Decision: `KEEP_BOTH`**

| Attribute | `main.py` | `production_main.py` |
|---|---|---|
| **Intended Environment** | Local Development & Interactive Demo | Strict Pilot & Production Cloud Run Gateway |
| **Runtime Enforcement** | Permissive (`create_demo_platform()`) | Strict fail-closed (`strict_runtime_enabled()`, requires `pilot` or `production`) |
| **CORS Policy** | Permissive (`allow_origins=["*"]`) | Strict whitelist from `ALLOWED_ORIGINS` environment variable |
| **Data Integrity Verification** | Lazy initialization on first evidence call | Eager startup validation via `verify_production_data_manifest()` |
| **Readiness Probe (`/ready`)** | Basic uptime check | Comprehensive checks for manifests, governance counts, golden questions |
| **Consumers** | Local developers, `Procfile`, `docs/DEVELOPMENT.md` | `Dockerfile`, `render.yaml`, `cloudbuild.yaml`, `test_pilot_acceptance.py` |

**Architectural Rationale:**
Consolidating `main.py` and `production_main.py` into a single module or app factory would merge conflicting lifecycles (permissive dev/demo vs. strict fail-closed pilot). It would introduce unnecessary abstraction and create regression risk for Cloud Run deployment and automated acceptance tests (`tests/plab/test_pilot_acceptance.py`). Maintaining both entrypoints provides clean, robust operational isolation.

---

## M. SCRIPTS / TOOLING PLAN

The retained 177 files in `Scripts/` represent active engineering tools, data builders, and evaluation pipelines. They are classified into 10 functional domains:

1. **INGESTION (13 scripts):** Handles PMC XML retrieval, JATS extraction, section chunking, and document registration (`download_pmc_xml.py`, `extract_pmc_jats.py`, `chunk_sections.py`, `clean_document.py`, `enrich_sections.py`, `parse_sections.py`, `register_document.py`, `ingest_urinary_track.py`, `ingest_wave2_batch.py`, etc.).
2. **DATA_BUILD (25 scripts):** Builds clean datasets, splits, and curriculum packages (`build_clean_train_dataset.py`, `build_university_bank.py`, `construct_product_dev_v3.py`, `curate_clean_train_dataset.py`, `assemble_product_dev_v3_clean.py`, `v4_generate_safety_splits.py`, etc.).
3. **EVALUATION (20 scripts):** Model evaluation harnesses and diagnostic tools (`evaluate_claim_verifier.py`, `evaluate_neural_reranker.py`, `evaluate_pubmedqa_external_benchmark.py`, `evaluate_stage8_reranker.py`, `evaluate_evidence_sufficiency.py`, etc.).
4. **BENCHMARK (45 scripts):** Benchmark runners across historical and current milestones (`run_canonical_rag_benchmark.py`, `run_final_product_test.py`, `run_heldout_benchmark_suite.py`, `run_renal_v2_*`, `run_renal_v3_*`, `run_renal_v4_*`, `run_renal_v5_*`, `run_renal_v6_*`, `run_renal_v7_*`).
5. **MAINTENANCE (18 scripts):** Data integrity checkers and contract validators (`validate_chunks.py`, `validate_chunk_integrity.py`, `validate_documents.py`, `validate_sections.py`, `validate_sources.py`, `validate_question.py`, `audit_batch1_duplicates.py`, etc.).
6. **RELEASE (9 scripts):** Milestone closure pipelines and freeze tools (`close_plab_v9.py`, `promote_golden.py`, `import_clinician_reviews.py`, `freeze_corpus_snapshot.py`, `freeze_retrieval_config.py`, etc.).
7. **MIGRATION (8 scripts):** Format and curriculum migrators (`repair_plab_cardiorespiratory.py`, `adapt_pmc_to_canonical.py`, etc.).
8. **REPRODUCIBILITY (15 scripts):** Threshold calibration and diagnostic scripts (`calibrate_abstention_threshold.py`, `recalibrate_evidence_sufficiency.py`, `run_forensic_diagnostics.py`, etc.).
9. **TRAINING_LEGACY (10 scripts):** Historical LoRA and adapter training runners (`train_qwen4b_retrieval_lora.py`, `run_qwen4b_domain_adaptation.py`, `qwen4b_adaptation_common.py`, etc.).
10. **RUNTIME_SUPPORT (4 scripts):** Platform generation and core initialization helpers (`generate_core_files.py`, `scale_plab_candidate_generation.py`, etc.).

**Directly Imported Scripts & Consumers:**
- `Scripts/close_plab_v9.py` -> imported by `tests/plab/v9/test_final_plab_closure.py`
- `Scripts/download_pmc_xml.py` -> imported by `tests/test_download_pmc_xml.py`
- `Scripts/build_qwen4b_retrieval_train.py` -> imported by `tests/renal/test_qwen4b_domain_adaptation.py`
- `Scripts/train_qwen4b_retrieval_lora.py` -> imported by `tests/renal/test_qwen4b_domain_adaptation.py`
- `Scripts/validate_qwen4b_train_firewall.py` -> imported by `tests/renal/test_qwen4b_firewall_*.py`
- `Scripts/qwen4b_adaptation_common.py` -> imported by `tests/renal/test_benchmark_integrity.py`
- `Scripts/validate_product_dev_v3_adjudication.py` -> imported by `tests/renal/test_benchmark_integrity.py`
- `Scripts/build_product_dev_v3_reconstruction_packets.py` -> imported by `tests/renal/test_benchmark_integrity.py`
- `Scripts/assemble_product_dev_v2.py` & `construct_product_dev_v3.py` -> imported by `Scripts/assemble_product_dev_v3_clean.py`

**Scripts/ Decision:**
`Scripts/` **must remain at root** with its current structure preserved. Renaming to `tools/` or moving files into nested subdirectories breaks active test suites and subprocess pipelines.

---

## N. RESEARCH STRUCTURE DECISION

**Decision: REJECT `research/` CONSOLIDATION; RETAIN `evaluation/`, `models/`, AND `notebooks/` AT ROOT**

| Evaluation Criterion | Assessment | Finding |
|---|---|---|
| **Runtime Usage** | Moderate | `configs/renal_v4_safety_config.json` hardcodes `models/renal_v4_evidence_classifier.pkl`. |
| **Test Usage** | Critical | Multiple test files assert exact paths from repository root (`tests/renal/test_renal_v4_1.py`, `tests/test_renal_v5_reranker_objective.py`, `tests/test_renal_v7_closure.py`). |
| **SHA/Path Assertions** | Immutable | `tests/renal/test_renal_v4_1.py:398-413` iterates over `FROZEN_ARTIFACTS` with hardcoded relative paths starting with `evaluation/` and `models/`. Any path change immediately triggers `IMMUTABLE FIREWALL VIOLATION`. |
| **Cryptographic Sidecars** | Immutable | `configs/renal_v4_safety_config.json.sha256` and `models/renal_v4_evidence_classifier.pkl.sha256` lock contents bit-for-bit. Editing the config path invalidates the hash. |
| **Scientific Reproducibility** | High | Preserves exact, auditable provenance matching historical publication reports (`reports/renal_v4/`, `reports/renal_v5/`). |
| **Judge Readability** | Superior | Clear, unhidden root directories allow technical judges to verify data and models immediately without digging through nested directories. |
| **Developer Discoverability** | High | Standard ML/AI layout familiar to practitioners. |

Creating a `research/` directory would introduce catastrophic regressions across the test suite for purely cosmetic folder symmetry. The existing root placement is technically superior.

---

## O. RISK REGISTER

| Structural Group | Proposed Actions | Risk Level | Potential Failure Mode | Blast Radius | Mitigation Strategy |
|---|---|---|---|---|---|
| **GROUP A: Docs & Metadata** | Clean `package.json` positioning; update `docs/` and `README.md` | **LOW** | Broken internal Markdown links or JSON syntax errors | Documentation & root metadata | Run JSON validator and comprehensive Markdown link scanner. |
| **GROUP B: Deployment** | Remove obsolete `Procfile`; document canonical deployments | **LOW** | Accidental deletion of active deployment file | Deployment pipelines | Verify 0 references across CI, Docker, and runtime before removal. |
| **GROUP C: Research Structure** | **SKIPPED** (Retain at root) | **NONE** | N/A | N/A | Zero changes made to `evaluation/`, `models/`, or `notebooks/`. |
| **GROUP D: Scripts/Tooling** | **SKIPPED** (Retain at root) | **NONE** | N/A | N/A | Zero changes made to `Scripts/`. |
| **GROUP E: Dependency Metadata**| Align docs with dependency tiers; preserve compatibility files | **LOW** | Inaccurate installation instructions | Developer experience | Cross-reference all dependency files against active environments. |
| **GROUP F: Entrypoints** | **SKIPPED** (Retain both `main.py` & `production_main.py`) | **NONE** | N/A | N/A | Zero code changes to entrypoint logic or signatures. |

---

## P. ROLLBACK STRATEGY

Because this refactoring plan strictly avoids risky structural moves, the blast radius is minimal.

1. **Isolated Branching:** All operations are strictly confined to branch `repo-architecture-v2` based on commit `f0db2716222a6a0aef559658620e79dc617cb581`. Main branch and frozen release tag `v1.0.0-hackathon` remain untouched.
2. **Standard Git Reversion:** If any unexpected discrepancy occurs during Gate 2 execution:
   - Specific file edits can be restored via `git checkout HEAD -- <path>`.
   - The entire implementation can be cleanly reverted using standard Git history.
3. **Prohibited Destructive Commands:** Under no circumstances will `git reset --hard`, `git clean -f`, force pushes, or history rewrites be executed.

---

## Q. TEST PLAN

The Gate 2 execution will be verified across eight distinct validation gates:

| Gate # | Verification Area | Target Files / Commands | Expected Outcome |
|---|---|---|---|
| **T1** | **Canonical RAG Engine** | `pytest tests/test_canonical_rag.py tests/test_evidence_engine_v2.py -v` | 100% pass; fail-closed abstention and claim verification verified. |
| **T2** | **University Track** | `pytest tests/university/ -v` | 100% pass; 0 answer key leakage, BKT tracking verified. |
| **T3** | **PLAB V9 Governance** | `pytest tests/plab/v9/ -v` | 100% pass; immutable oracle and span hashes intact. |
| **T4** | **Pilot Acceptance** | `pytest tests/plab/test_pilot_acceptance.py -v` | 100% pass; fail-closed production gateway verified. |
| **T5** | **Historical Firewalls** | `pytest tests/renal/test_renal_v4_1.py tests/test_renal_v7_closure.py -v` | 100% pass; all SHA-256 sidecars and relative paths match. |
| **T6** | **Path & Link Integrity** | Automated grep for stale references; Markdown link audit across `docs/` and `README.md` | 0 broken internal links; 0 unintended stale references. |
| **T7** | **Security Audit** | Scan for accidental secrets, `.env`, tokens, runtime DBs, HF caches | 0 sensitive or machine-specific artifacts. |
| **T8** | **Working Tree Hygiene** | `git status --short` | Exactly 1 atomic commit with clean working tree. |

---

## R. ROOT BEFORE / AFTER

### Current Root Tree (34 entries excluding `.git`)
```
MedicalPlab-architecture-v2/
├── .github/
├── configs/
├── Data/
├── deploy/
├── docs/
├── evaluation/
├── examples/
├── frontend/
├── models/
├── notebooks/
├── reports/
├── schemas/
├── Scripts/
├── src/
├── tests/
├── .dockerignore
├── .editorconfig
├── .env.example
├── .gitattributes
├── .gitignore
├── .python-version
├── cloudbuild.yaml
├── Dockerfile
├── main.py
├── package.json
├── Procfile
├── production_main.py
├── pyproject.toml
├── README.md
├── render.yaml
├── requirements-benchmark.txt
├── requirements-retrieval.txt
├── requirements.txt
└── uv.lock
```

### Proposed Root Tree (33 entries excluding `.git`)
*(Reflects removal of obsolete `Procfile` and metadata hygiene in `package.json`)*
```
MedicalPlab-architecture-v2/
├── .github/
├── configs/
├── Data/
├── deploy/
├── docs/
├── evaluation/
├── examples/
├── frontend/
├── models/
├── notebooks/
├── reports/
├── schemas/
├── Scripts/
├── src/
├── tests/
├── .dockerignore
├── .editorconfig
├── .env.example
├── .gitattributes
├── .gitignore
├── .python-version
├── cloudbuild.yaml
├── Dockerfile
├── main.py
├── package.json               # (Positioning metadata updated)
├── production_main.py
├── pyproject.toml
├── README.md                  # (High-level architectural map aligned)
├── render.yaml
├── requirements-benchmark.txt
├── requirements-retrieval.txt
├── requirements.txt
└── uv.lock
```

- **Root Entry Count Before:** 34 entries (15 directories, 19 files)
- **Root Entry Count After:** 33 entries (15 directories, 18 files)
- **Tracked Files Delta:** -1 file (`Procfile` removed)
- **Architectural Clarity:** Maximum senior-engineer discoverability, 100% test compatibility, zero regression risk.

---

## GATE 1 EXIT VERIFICATION CHECKLIST

- [x] Every root item has an exact classification.
- [x] Every UNKNOWN has been resolved (0 remaining).
- [x] Every root item has a keep/move/remove justification.
- [x] Every proposed move has a complete Move Matrix row.
- [x] Every move has a defined test gate.
- [x] Deployment Matrix is complete.
- [x] Dependency Matrix is complete.
- [x] Versioning Policy is defined.
- [x] Entrypoint decision is defined.
- [x] Scripts/tooling decision is defined.
- [x] Research structure decision is defined.
- [x] Risk Register is complete.
- [x] Rollback strategy is complete.
- [x] Before/after trees are present.

---
**END OF GATE 1 PLAN ARTIFACT**
