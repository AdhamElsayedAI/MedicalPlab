# MedicalPlab — Developer Guide & Setup

This guide provides local development setup, environment isolation guidelines, dependency management, testing workflows, and engineering quality gates for the MedicalPlab repository.

---

## 1. Environment Architecture

MedicalPlab separates its core data pipeline, application runtime, and retrieval/neural evaluation stacks so that the repository stays reproducible across platforms without forcing hardware-specific GPU binaries into the core dependencies.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Local Development Setup                         │
│                                                                        │
│  [ Core Project ]           [ Retrieval / Reranker ]   [ Frontend ]    │
│  • pyproject.toml / uv.lock • requirements-retrieval   • Node.js 20+   │
│  • FastAPI / Pydantic       • transformers / sentence- • Next.js 16.3  │
│  • Core Data Pipeline       • PyTorch (CUDA/CPU)       • React 19      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Quick Start: Local Development

### 2.1 Backend Setup

1. **Prerequisites**: Python 3.11 or 3.12 (pinned in `.python-version`).
2. **Virtual Environment**:
   ```bash
   # Create and activate virtual environment
   python -m venv .venv
   
   # Linux / macOS:
   source .venv/bin/activate
   
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```bash
   # Upgrade pip
   python -m pip install --upgrade pip

   # Install core package in editable mode
   pip install -e .

   # Install production runtime dependencies
   pip install -r requirements.txt
   ```

4. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```

5. **Start API**:
   ```bash
   # Development / Demo server (with Socratic chat, University API, evidence engine)
   python main.py
   # Or with live reload:
   uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

   *Verify backend:*
   ```bash
   curl http://localhost:8000/health
   ```

### 2.2 Frontend Setup

1. **Prerequisites**: Node.js 20+ and npm.
2. **Install & Run**:
   ```bash
   cd frontend
   npm ci
   npm run dev
   ```
   *The web application will be accessible at `http://localhost:3000`.*
   *Alternatively, from the repository root, run `npm run dev`.*

---

## 3. Dependency Management & Roles

The repository maintains an explicit dependency strategy tailored to distinct environments:

| File | Role | Primary Environment | Purpose & Contents |
| :--- | :--- | :--- | :--- |
| **`pyproject.toml`** | Canonical Python Spec | Modern Python (3.11/3.12) | Core runtime (`jsonschema`, `pdfplumber`, `requests`), optional ML groups (`renal-ml`, `qwen4b-adaptation`), and Pytest testpaths. |
| **`uv.lock`** | Deterministic Lockfile | `uv` / pip-tools | Cross-platform pinned lockfile ensuring reproducible dependency resolution. |
| **`requirements.txt`** | Container & Deployment | Docker / Cloud Run / PaaS | Production web server stack (`fastapi`, `uvicorn`, `pydantic`, `httpx`, `pytest`, `-e .`). |
| **`requirements-retrieval.txt`** | GPU Retrieval Stack | Local CUDA Workstations | Validated versions of `accelerate`, `numpy`, `sentence-transformers`, `transformers` for local inference. |
| **`requirements-benchmark.txt`** | Dedicated Benchmark | Colab / Linux Runners | Specific dependencies (`transformers==4.51.3`, `autoawq`, `accelerate`) for Qwen AWQ benchmark reproduction. |
| **`package.json`** | Command Wrapper | Root Workstation | Convenience script runner forwarding `npm run dev`, `build`, and `lint` to `frontend/`. |
| **`frontend/package.json`** | Canonical Frontend | Next.js Web Client | Web dependencies (`next@16.3.4`, `react@19.2.8`, `lucide-react`, `tailwindcss@4`, `three`). |

---

## 4. Optional GPU / Retrieval Environment

The canonical RAG Evidence Engine (V1.1) uses `Qwen/Qwen3-Reranker-0.6B` and field-aware BM25. In the default runtime, the engine runs on CPU/CUDA seamlessly.

To install the full neural retrieval and reranking dependencies:

```bash
# 1. Install appropriate PyTorch build for your CUDA platform first:
# e.g., for CUDA 12.1+:
pip install torch --index-url https://download.pytorch.org/whl/cu121

# 2. Install retrieval and evaluation packages:
pip install -r requirements-retrieval.txt
pip install -r requirements-benchmark.txt
```

Verify GPU availability:
```bash
python -c "import torch; print('PyTorch:', torch.__version__, '| CUDA:', torch.cuda.is_available())"
```

---

## 5. Engineering Utilities & Tool Locations

Engineering utilities and automation scripts are organized into dedicated locations:

- **`Scripts/`**: Top-level engineering and pipeline tools retained at root for direct Python imports and automation:
  - `Scripts/download_pmc_xml.py`, `extract_pmc_jats.py`, `chunk_sections.py`: Literature ingestion and JATS XML processing.
  - `Scripts/build_clean_train_dataset.py`, `build_university_bank.py`: Dataset and question bank builders.
  - `Scripts/run_canonical_rag_benchmark.py`, `run_final_product_test.py`: Benchmark evaluation suites.
  - `Scripts/validate_chunks.py`, `validate_documents.py`: Data contract validation tools.
  - `Scripts/close_plab_v9.py`: PLAB V9 milestone closure and governance freeze pipeline.
- **`examples/`**: Schema contract examples and developer integration testing:
  - `examples/chunk.example.json`, `question.example.json`: Valid payload contract references.
  - `examples/test_loader.py`, `test_pipeline.py`: Developer smoke tests for evidence loading.
- **`deploy/`**: Automated deployment scripts for Google Cloud Run:
  - `deploy/deploy_cloud_run.sh` (Bash / Cloud Shell)
  - `deploy/deploy_cloud_run.ps1` (PowerShell)

---

## 6. Testing Tiers & Quality Verification

Automated testing is structured into progressive tiers:

```
[ Tier 1: Canonical RAG ] ──► [ Tier 2: University Track ] ──► [ Tier 3: PLAB V9 Governance ]
                                                                             │
[ Tier 5: Historical Firewalls ] ◄── [ Tier 4: Pilot Acceptance ] ◄──────────┘
```

Execute tests by tier via `pytest`:

```bash
# Tier 1: Canonical RAG & Evidence Engine V1.1
pytest tests/test_canonical_rag.py tests/test_evidence_engine_v2.py -v

# Tier 2: University Preclinical Track (Contract, Mastery, Zero-Leakage)
pytest tests/university/ -v

# Tier 3: PLAB V9 Licensing Governance & Cryptographic Oracle
pytest tests/plab/v9/ -v

# Tier 4: Pilot Acceptance & Fail-Closed Production Gateway
pytest tests/plab/test_pilot_acceptance.py -v

# Tier 5: Historical Milestone Firewalls (Bit-for-Bit SHA-256 Sidecars)
pytest tests/renal/test_renal_v4_1.py tests/test_renal_v7_closure.py -v

# Full active public-safe test suite
pytest -q
```

Frontend validation:
```bash
cd frontend
npm run build
npm run lint
```

---

## 7. Branch Expectations & Git Workflow

- **`main`**: Protected production branch. Represents the verified, released codebase (`v1.0.0-hackathon`). Never work directly on `main` or rewrite its history.
- **Feature / Architecture Branches**: All refactors and feature explorations occur on isolated branches (e.g., `repo-architecture-v2`, `feature/...`).
- **Zero Regression Rule**: No change may alter RAG ranking, University pedagogy, BKT algorithms, or PLAB governance without explicit milestone charter.
- **Commit Integrity**: Commits must be atomic, conventional (`feat:`, `fix:`, `docs:`, `chore:`), and accompanied by green test gates.

