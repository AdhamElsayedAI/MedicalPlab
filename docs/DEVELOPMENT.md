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

---

## 3. Optional GPU / Retrieval Environment

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

## 4. Testing & Quality Verification

All automated tests run via standard `pytest`:

```bash
# Run canonical RAG & Evidence Engine V1.1 tests
pytest tests/test_canonical_rag.py tests/test_evidence_engine_v2.py -v

# Run University Learning Track tests
pytest tests/university/ -v

# Run PLAB V9 Evidence Closure & Governance tests
pytest tests/plab/v9/ -v

# Run full active test suite
pytest -q
```

Frontend validation:
```bash
cd frontend
npm run build
npm run lint
```

---

## 5. Development Workflow & Git Etiquette

```
Issue / Task
     │
     ▼
Feature Branch (e.g., feature/topic-expansion, fix/routing-edge-case)
     │
     ▼
Implementation
     │
     ▼
Focused Tests (pytest tests/...)
     │
     ▼
Regression & Smoke Tests (frontend build + backend smoke)
     │
     ▼
Code Review & Approval
     │
     ▼
Merge to Main
```

### Commit Guidelines
- Use conventional commit prefixes: `feat:`, `fix:`, `docs:`, `chore:`, `test:`, `perf:`.
- Maintain test and governance invariants. Never delete tests to reduce repo size.
- Never commit live secrets, model weights, local cache files, or private patient/publisher data.
