# MedicalPlab Renal/Urinary V3 — Forensic Recovery Audit

**Audit Date**: 2026-09-10  
**Auditor**: Antigravity Principal IR / AI Safety Engineer  
**Status**: VERIFIED & REPRODUCIBLE  

---

## 1. Repository State

| Field | Value | Verification Command / Result |
|---|---|---|
| **Local Workspace** | `C:\Users\Adham Elsayed\Desktop\AdhamElsayedAI\MedicalPlab` | Valid, single authorized workspace |
| **Active Branch** | `ai-data-execution-v1` | `git branch --show-current` -> `ai-data-execution-v1` |
| **Tracking Remote** | `origin/ai-data-execution-v1` | `git status -sb` -> Up to date |
| **Current HEAD SHA** | `70f5bb92d948c1c61c0078784d4a77563aa77d1f` | `git rev-parse HEAD` verified |
| **Working Tree Status** | Clean | `git status` -> nothing to commit, working tree clean |
| **Whitespace / Diff Check**| Clean | `git diff --check` -> code 0 (no errors) |

### Recent Commit Lineage (Confirmed Linear Descendant)
- `70f5bb9` — `feat(renal-v2): Phase 18-27 safety evaluation, single final heldout run, and technical report`
- `64abd4e` — `feat(renal-v2): Phase 8-17 corpus repair, evidence-span ground truth, and frozen heldout`
- `78433b1` — `feat(renal-v2): Phase 1-7 recovery, audit, and diagnostic reports`
- `622e955` — `test(renal): enforce frozen artifact integrity`
- `5742c62` — `feat(learn): integrate fail-closed renal dense retrieval`

---

## 2. Immutable V2 Historical Benchmark & Firewall Verification

Per Section 2 of the V3 Specification, `RENAL-HELDOUT-V2-FINAL` is **immutable historical evidence**.
It will NOT be modified, rerun, tuned on, or inspected for V3 architecture design.

### V2 Final Historical Metrics (Frozen Record)
- **Dataset**: `evaluation/renal/renal-heldout-v2-final.json` (SHA256: `8885b21bc1174ea62aa4840d58ba2562d5138fc6dc9e933eb92461feff5d90ee`)
- **Total Queries**: 100 (52 Answerable, 48 Unsupported)
- **PassageHit@1**: 9 / 52 = 0.1731 (17.31%)
- **PassageHit@5**: 25 / 52 = 0.4808 (48.08%)
- **PassageHit@10**: 32 / 52 = 0.6154 (61.54%)
- **DocumentRecall@10**: 48 / 52 = 0.9231 (92.31%)
- **Authority Accuracy**: 13 / 14 = 0.9286 (92.86%)
- **Safety Classification**:
  - Unsafe Accept: 2 / 50 = 0.0400 (4.00% <= 5.0% target PASSED)
  - Precision: 2 / 4 = 0.5000 (50.00%)
  - Recall: 2 / 16 = 0.1250 (12.50%)
  - False Refusal: 14 / 16 = 0.8750 (87.50%)
  - AUROC: 0.8462, AUPRC: 0.6107
- **SBA Generation Gate**: **BLOCKED** (Hit@1 < 85%, Precision < 90%; 0 questions generated)

---

## 3. Verified Hardware & ML Environment

| Component | Verified Specification | Status |
|---|---|---|
| **Python Executable** | `C:\Users\Adham Elsayed\AppData\Local\Programs\Python\Python312\python.exe` (v3.12.10) | Confirmed |
| **PyTorch Version** | `2.14.0+cu130` | Confirmed |
| **CUDA Runtime** | `13.0` | Confirmed |
| **CUDA Available** | `True` (`torch.cuda.is_available()`) | Hard Gate PASSED |
| **GPU Device** | `NVIDIA GeForce RTX 3060 Laptop GPU` | Confirmed |
| **Total Dedicated VRAM**| `6143.5 MiB` | Confirmed |
| **Embedding Model** | `Qwen/Qwen3-Embedding-0.6B` | Confirmed |
| **Embedding Revision** | `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` | Confirmed |
| **Local Cache Directory** | `Data/experiments/renal_v2/cache` | 164.8 MB (JSON + NPY) verified |
| **Execution Script** | `Scripts/run_gpu.ps1` | Ready for V3 extensions |

---

## 4. Local Codebase & Production Runtime Inventory

### Core Production Code
- `src/medicalplab/learn/renal_retrieval.py`: `QwenRenalRetrieverV2` with exact dot-product dense ranking, score caching, and query normalization.
- `src/medicalplab/learn/renal_evidence_classifier.py`: `RenalEvidenceClassifier` (20-feature extractor, logistic regression classifier, threshold 0.7900).
- `src/medicalplab/learn/service.py`: `CourseLearningService` product integration with fail-closed medical safety statuses (`GROUNDED`, `INSUFFICIENT_EVIDENCE`, `UNSUPPORTED`).
- `src/medicalplab/learn/renal_bm25.py`: BM25 tokenizer and inverted index.
- `src/medicalplab/learn/renal_normalization.py`: UK medical query synonym expander and acronym resolver.

### Corpus Status
- **Active Documents**: 23 PMC open-access clinical review and guideline sources.
- **Licenses**: 100% CC BY (CC BY 2.0, CC BY 3.0, CC BY 4.0), commercially permissive.
- **Curriculum Topics**: 43 undergraduate topics (0 missing, 11 strong, 19 adequate, 13 thin).
- **Snapshot SHA256**: `7b29423c910b96ef68f056d682ddb03d6d54fb4a45a336fc3f31920efecdd9bb` in `Data/metadata/corpus_renal_snapshot_v2.json`.

---

## 5. Repository-Consistent Directory Conventions for V3

To strictly adhere to repository structure without creating arbitrary top-level directories:
- **Datasets**: `evaluation/renal/v3/`
- **Reports**: `reports/renal_v3/`
- **Experimental Artifacts & Caches**: `Data/experiments/renal_v3/`
- **Scripts**: `Scripts/` (prefixed with `v3_` or `run_renal_v3_`)
- **Production Models**: `models/`
- **Tests**: `tests/renal/test_renal_v3.py`

---

## 6. Audit Sign-Off
Phase 1 and Phase 2 requirements are satisfied. The codebase is clean, reproducible, and ready for Stage 3 (V3 TRAIN/DEV split discipline) and Stage 4/5 (Relevance audit).
