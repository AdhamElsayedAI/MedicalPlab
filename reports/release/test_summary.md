# MedicalPlab — Release Test Suite Summary

## Overview

The MedicalPlab repository verification suite is organized into modular tiers across evidence verification, product contracts, clinical simulation, adaptive learning, and domain adaptation benchmarks.

All tests run via standard `pytest`:
```bash
python -m pytest -q
```

---

## Active Test Suite Breakdown

| Test Suite | Path | Test Count | Status | Description |
| :--- | :--- | :---: | :---: | :--- |
| **PLAB V9 Evidence Closure** | `tests/plab/v9/` | 14 | **PASS** | Independent oracle tests for UTF8 LF canonical hashing, canonical organization identity resolution, exact span containment, and 9 negative mutation tests proving fail-closed rejection. |
| **PLAB Product Core** | `tests/plab/` | 63 | **PASS** | Product contracts, durable lifecycle, governance state machine, persistence, adversarial inputs, and pilot acceptance. |
| **Renal Domain Adaptation** | `tests/renal/` | 150 | **PASS** | Qwen-4B LoRA domain adaptation, benchmark integrity, lexical/semantic firewall tests, hard negative mining, and retrieval ablations. |
| **Stage-B Retrieval** | `tests/stage_b/` | 44 | **PASS** | Dense & sparse hybrid retrieval, multi-source recall, characterization, and contract checks. |
| **Stage-C Evidence Pipeline** | `tests/stage_c/` | 27 | **PASS** | Evidence extraction, span binding, claim decomposition, and contract validators. |
| **Stage-D Intent & Routing** | `tests/stage_d/` | 24 | **PASS** | Clinical question intent classification, specialty routing, and query decomposition. |
| **Stage-E Learning & Profile** | `tests/stage_e/` | 31 | **PASS** | Bayesian Knowledge Tracing (BKT), student mastery tracking, and spaced repetition recommendations. |
| **Stage-F Simulation & Exam** | `tests/stage_f/` | 48 | **PASS** | Emergency room hemodynamics simulation, adaptive difficulty, study plan generation, and exam orchestrator. |
| **Stage-G Platform & API** | `tests/stage_g/` | 68 | **PASS** | Multi-tenancy, rate limiting, security middleware, analytics, audit logging, and runtime modes. |
| **Stage-R Strict Retrieval** | `tests/stage_r/` | 52 | **PASS** | Strict runtime guarantees, dense embeddings, reranker scoring, and compression pipeline. |
| **Learn & Integration** | `tests/learn/`, `tests/integration/` | 73 | **PASS** | Course learning flows and mobile API contract verification. |
| **Total Passing** | | **594** | **100% PASS** | Zero regressions, 1 skipped (optional live GPU test), 12 subtests passed. |

---

## Fast Verification Commands

```bash
# 1. Verify PLAB V9 evidence closure
python -m pytest tests/plab/v9 -v

# 2. Verify all active PLAB tests
python -m pytest tests/plab -q

# 3. Verify entire repository
python -m pytest -q

# 4. Verify cloud API health endpoint
python -c "from main import app; from fastapi.testclient import TestClient; c = TestClient(app); r = c.get('/health'); assert r.status_code == 200; print('OK:', r.json())"
```
