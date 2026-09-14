# MEDICALPLAB — REPOSITORY ARCHITECTURE V2 FINAL REPORT
**Document ID:** `reports/release/repository_architecture_v2_report.md`  
**Milestone:** Repository Architecture V2 Refactor  
**Branch:** `repo-architecture-v2`  
**Base Commit:** `f0db2716222a6a0aef559658620e79dc617cb581`  
**Release Tag:** `v1.0.0-hackathon` (Frozen & Immutable)  
**Status:** `ARCHITECTURE_V2_READY`  

---

## 1. Executive Summary

This safe structural engineering refactor was executed under a strict **Two-Gate, Release-Safe, Zero-Regression** protocol on an already released, independently QA-verified medical education platform (`MedicalPlab`).

Following comprehensive empirical audit in Gate 1 and explicit human authorization for Gate 2, the repository architecture was refined to optimize developer experience, mentor and judge discoverability, and deployment clarity without compromising cryptographic integrity, runtime performance, or behavioral invariants.

Key outcomes include:
- **Zero Behavioral Regressions:** 100% of active Canonical RAG, University learning, and PLAB V9 governance tests pass without modification.
- **Cryptographic Firewall Protection:** Retained `evaluation/`, `models/`, and `notebooks/` at root, preventing breakage of frozen test assertions (`tests/renal/test_renal_v4_1.py:398-413`) and immutable SHA-256 sidecars.
- **Import Stability:** Retained `Scripts/` at root, preserving critical direct Python imports in `tests/plab/v9/test_final_plab_closure.py`, `tests/test_download_pmc_xml.py`, and `tests/renal/test_*.py`.
- **Dual Entrypoint Isolation:** Maintained operational separation between local development/demo (`main.py`) and strict fail-closed pilot/production (`production_main.py`).
- **Pruned Dead Assets:** Removed obsolete Heroku process runner `Procfile` after proving zero runtime, test, CI, or documentation dependencies.
- **Positioning Alignment:** Corrected root `package.json` description to match approved product positioning.
- **Documentation Alignment:** Enhanced `docs/ARCHITECTURE.md` with a dedicated Repository Architecture section, updated `docs/DEVELOPMENT.md` with dependency and tooling maps, and clarified deployment tiers in `docs/DEPLOYMENT.md`.

---

## 2. Before & After Root Tree

### Root Tree Before Refactor (34 entries excluding `.git`)
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

### Root Tree After Refactor (33 entries excluding `.git`)
```
MedicalPlab-architecture-v2/
├── .github/                       # GitHub Actions CI/CD workflows (Cloud Run deployment)
├── configs/                       # Executable configs with cryptographic SHA-256 sidecars
├── Data/                          # Active public-safe runtime data (chunks, manifests, questions)
├── deploy/                        # Cloud Run deployment automation scripts (Bash, PowerShell)
├── docs/                          # Architecture, clinical safety, deployment, and developer guides
├── evaluation/                    # Ground truth datasets & benchmarks asserted by governance tests
├── examples/                      # Formal schema payload examples and integration test scripts
├── frontend/                      # Next.js 16.3.4 / React 19 web application (deployed to Vercel)
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

## 3. Structural Decisions & Rationale

### Files Moved
- **None**: In accordance with the mandate (*"Technically superior beats cosmetically smaller. Every time."*), zero files were moved. Moving `evaluation/`, `models/`, or `Scripts/` would break cryptographic SHA-256 sidecars, immutable test suites, or direct Python package imports.

### Files Removed
- **`Procfile`**: Removed via `git rm`. Proved to have:
  - Zero runtime dependencies (Cloud Run uses `Dockerfile`; Render uses `render.yaml`; local dev uses direct `uvicorn main:app`).
  - Zero test dependencies (`git grep` yields 0 matches in `tests/`).
  - Zero CI dependencies (`.github/workflows/deploy-cloud-run.yml` and `cloudbuild.yaml` omit it).
  - Zero documentation requirements (`docs/DEPLOYMENT.md` does not reference it).
  - Zero reproducibility or release-evidence role.

### Files Retained at Root & Retention Rationale
- **`src/` & `frontend/`**: Standard Python packaging root (`src/`) and Next.js monorepo workspace (`frontend/`).
- **`Data/`**: Public-safe active runtime data copied by `Dockerfile` (`COPY Data/ Data/`) and loaded by Evidence Engine.
- **`tests/`**: Pytest standard test discovery root (`testpaths = ["tests"]`).
- **`docs/` & `reports/`**: Documentation and compliance evidence; must remain easily accessible at root for mentors and judges.
- **`evaluation/` & `models/`**: Hardcoded in immutable historical tests (`tests/renal/test_renal_v4_1.py:398-413`) and sealed by cryptographic SHA-256 sidecars (`configs/renal_v4_safety_config.json.sha256`, `models/renal_v4_evidence_classifier.pkl.sha256`).
- **`Scripts/`**: Directly imported by active test suites (`tests/plab/v9/test_final_plab_closure.py`, `tests/test_download_pmc_xml.py`, `tests/renal/test_*.py`) and invoked via subprocesses in `ingest_wave2_batch.py`.
- **`configs/` & `schemas/`**: Executable configurations and formal JSON data contracts copied into production container.
- **`Dockerfile`, `cloudbuild.yaml`, `render.yaml`**: Expected at repository root by their respective build systems (Docker CLI, `gcloud builds submit`, Render platform).
- **`main.py` & `production_main.py`**: Essential runtime gateways serving decoupled operational lifecycles.
- **`pyproject.toml`, `requirements*.txt`, `uv.lock`**: Standard packaging, lockfile, and environment isolation specs.

### Research Structure Decision
- **Hypothesis**: Consolidate `evaluation/`, `models/`, `notebooks/` into `research/`.
- **Evaluation**: Rejected. Test file `tests/renal/test_renal_v4_1.py` tests exact relative paths (`evaluation/...`, `models/...`) and verifies SHA-256 digests against `FROZEN_ARTIFACTS`. Moving files breaks the immutable firewall. Retaining at root is technically superior.

### Tools / Scripts Structure Decision
- **Hypothesis**: Rename `Scripts/` to `tools/` with nested subfolders.
- **Evaluation**: Rejected. Multiple test files import from `Scripts` directly (`from Scripts.close_plab_v9 import ...`, `from Scripts import download_pmc_xml`, `sys.path.insert(0, ... / "Scripts")`). Moving or renaming scripts causes immediate Python import failures. Retained at root; internal 10-domain functional breakdown documented in `docs/DEVELOPMENT.md`.

### Entrypoint Decision
- **Hypothesis**: Consolidate `main.py` and `production_main.py` into an app factory.
- **Evaluation**: Rejected (`KEEP_BOTH`). `main.py` serves local interactive development, demo exploration, and Socratic chat. `production_main.py` enforces strict startup data manifests, fail-closed abstention, and PLAB golden question governance. Merging them would compromise fail-closed pilot isolation.

### Dependency Management Decision
- Defined clear environment tiers in `docs/DEVELOPMENT.md`:
  - `pyproject.toml` + `uv.lock`: Canonical modern Python package specification and lockfile.
  - `requirements.txt`: Pinned web runtime dependencies for Docker and production PaaS.
  - `requirements-retrieval.txt`: Validated CUDA/GPU retrieval stack.
  - `requirements-benchmark.txt`: Pinned Colab/Linux benchmark environment.
  - `package.json` (root) & `frontend/package.json`: Root command runner and Next.js client dependencies.

### Versioning Policy
- **`PRODUCT_RELEASE_VERSION` (`1.0.0`)**: Overall platform release tag `v1.0.0-hackathon` and root `package.json`.
- **`BACKEND_PACKAGE_VERSION` (`0.2.0`)**: Core Python library package version in `pyproject.toml` (API gateway reporting `1.1.0`).
- **`FRONTEND_PACKAGE_VERSION` (`0.1.0`)**: Next.js client application version in `frontend/package.json`.
- Confirmed intentionally independent and decoupled.

---

## 4. Documentation & Metadata Updates

1. **`package.json`**:
   - Replaced exaggerated positioning (`"MedicalPlab: The Intelligence Infrastructure Layer of Global Medicine"`) with approved product positioning:
     `"Evidence-grounded medical education platform combining adaptive undergraduate learning with fail-closed licensing preparation."`
2. **`README.md`**:
   - Aligned repository tree diagram to cleanly present high-level architecture (`deploy/`, `configs/`, `schemas/`, `evaluation/`, `models/`, `Dockerfile`, `production_main.py`).
3. **`docs/ARCHITECTURE.md`**:
   - Added dedicated `## 6. Repository Architecture` section distinguishing repository structural tiers from runtime system architecture.
4. **`docs/DEVELOPMENT.md`**:
   - Added Section 3 (Dependency Management & Roles), Section 5 (Engineering Utilities & Tool Locations), Section 6 (Testing Tiers), and Section 7 (Branch Expectations).
5. **`docs/DEPLOYMENT.md`**:
   - Added Section 3 (Deployment Classification Matrix) categorizing deployments into Canonical (Cloud Run + Vercel), Supported Optional (Docker standalone + Render), and Legacy/Retired (Procfile).

---

## 5. Verification Results

| Gate | Area | Target / Command | Result | Details |
|---|---|---|:---:|---|
| **V1** | **Focused RAG** | `pytest tests/test_canonical_rag.py tests/test_evidence_engine_v2.py -v` | **PASS** | 22 / 22 tests passed in 1.4s. Fail-closed abstention, routing, verifier intact. |
| **V2** | **University Track** | `pytest tests/university/ -v` | **PASS** | 36 / 36 tests passed in 1.2s. Zero answer key leakage, BKT tracking verified. |
| **V3** | **PLAB V9 Governance** | `pytest tests/plab/v9/ -v` | **PASS** | 24 / 24 tests passed in 0.6s. Independent oracle, exact spans, mutation tests green. |
| **V4** | **Backend Smoke** | `python tests/verify_endpoints.py` | **PASS** | Health (200), latency header (5.36 ms), evidence query (200), chat abstention (200), university subjects (200), student attempts (201), CORS (200). |
| **V5** | **Production Gateway** | `production_main.py` test client | **PASS** | Strict mode enforced (fail-closed on non-pilot), health (200), readiness (200). |
| **V6** | **Link Integrity** | Automated Markdown link checker | **PASS** | 0 broken internal links across `README.md` and `docs/*.md`. |
| **V7** | **Security Audit** | Automated secret and credential scan | **PASS** | 0 live secrets, 0 API keys, 0 private credentials, 0 tracked runtime DBs. |
| **V8** | **Path Integrity** | Stale reference search | **PASS** | 0 active code or documentation references to deleted `Procfile`. |

### Known Public Packaging Limitations
- `tests/renal/test_renal_v4_1.py:421` and `tests/test_renal_v7_closure.py:47,70`: Historical research milestone checkpoints (`V7_RESEARCH_COMPLETE_PRODUCT_GENERALIZATION_FAILED` committed in earlier research iterations prior to productization) have pre-existing SHA differences. Per Section 6, these are correctly classified as `KNOWN_PUBLIC_PACKAGING_LIMITATION` and are not regressions from this refactor.

---

## 6. Before / After Metrics

| Metric | Before | After | Delta |
|---|:---:|:---:|:---:|
| **Root Total Entries** | 34 | 33 | **-1** |
| **Root Directories** | 15 | 15 | 0 |
| **Root Files** | 19 | 18 | **-1** (`Procfile` removed) |
| **Tracked Files** | 903 | 904 | +1 (Plan and Report artifacts added, `Procfile` removed) |
| **Broken Internal Links** | 0 | 0 | 0 |
| **Unintended Stale References** | 0 | 0 | 0 |
| **Passing Focused Tests** | 82 / 82 | 82 / 82 | 100% PASS |

---

## 7. Conclusion

MedicalPlab Repository Architecture V2 successfully achieves senior-engineer clarity, robust deployment organization, and metadata hygiene with **zero behavioral regression**. The repository is ready to be committed.
