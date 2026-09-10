# MedicalPlab Renal V4 — Forensic Audit & Baseline Architecture Report

**Audit Timestamp:** 2026-09-10T13:35:00Z  
**Author:** Antigravity (Principal IR Engineer & Medical Safety Lead)  
**Target Mission:** MedicalPlab Renal V4 — Evidence Localization & Claim-Entailment Recovery Mission  

---

## 1. Repository & Workspace State Verification

| Parameter | Measured State | Verification Status |
|---|---|---|
| **Local Workspace** | `C:\Users\Adham Elsayed\Desktop\AdhamElsayedAI\MedicalPlab` | Verified valid single repository root |
| **Active Branch** | `ai-data-execution-v1` | Verified active branch |
| **Local HEAD SHA** | `81298c36525c268dc45458c439166f843b42eda0` | Matches origin/ai-data-execution-v1 |
| **Remote HEAD SHA** | `81298c36525c268dc45458c439166f843b42eda0` | In exact synchronization |
| **Parent Commit** | `6b90d813fabf50d65ab27c6637698abcf143f135` | Frozen V3 retrieval parent preserved |
| **Working Tree State** | Clean (`git status -sb`: 0 untracked, 0 modified) | Pass |
| **Whitespace / Diff Check** | `git diff --check` returned 0 errors | Pass |

---

## 2. Historical Evaluation Firewall Verification

The following evaluation artifacts are permanently classified as **SPENT HISTORICAL EVIDENCE**. In accordance with Section 2 of the V4 Mission Protocol, they are sealed under strict isolation:
- No rerunning of these sets.
- No inspection of individual queries, failures, or gold passages for V4 architecture design.
- No hard-negative mining or query rewriting derived from these items.

| Artifact | Path | N | Role | Firewall Status |
|---|---|---|---|---|
| **RENAL-HELDOUT-V2-FINAL** | `evaluation/renal/renal-heldout-v2-final.json` | 80 | Historical V2 Heldout | **SEALED** (SHA256: `8885b21bc1174ea6...`) |
| **RENAL-HELDOUT-V3-FINAL** | `evaluation/renal/v3/renal-heldout-v3-final.json` | 100 | Historical V3 Heldout | **SEALED** (SHA256: `40c96f46be1c6547...`) |
| **RENAL-V3-SAFETY-TEST-2** | `evaluation/renal/v3/renal-v3-safety-test-2.json` | 70 | Historical V3.1 Test | **SEALED** (SHA256: `3fe59bb6011c5ab4...`) |
| **V3 DEV QRELS (69 Qs)** | `evaluation/renal/v3/renal-dev-v3-qrels.json` | 88 (69 ans) | Historical V3 DEV | **SPENT_FOR_MODEL_SELECTION** |

---

## 3. Production Service & Answer Generation Flow Audit

### Route: `POST /api/v1/learn/query`
- Defined in `src/medicalplab/stage_g/product_api.py` (lines 233–244).
- Invokes `CourseLearningService.query(req)` from `src/medicalplab/learn/service.py`.

### Service Logic: `CourseLearningService`
- For urinary/renal course tracks (`course_id in ["urinary", "renal", "urinary_renal"]`), execution routes to `_query_renal(query, intent, trace_id)`.
- Retrieval call: `hits = self._renal_retriever.retrieve(query, top_k=5)`.
- Sufficiency gate: If `hits[0].score < RENAL_SUFFICIENCY_THRESHOLD`, service returns `GroundingStatus.INSUFFICIENT_EVIDENCE` with structured student citations and refuses to answer.
- Answer generation: If sufficient, service returns `GroundingStatus.GROUNDED` with `answer = str(top.chunk.get("text", "")).strip()`, an **extractive grounded answer** directly from the top-ranked passage, alongside verified citations (`document_id#chunk_id`).
- Production Implication for Verifier: There is no free-form hallucinating generator in production; the system is fundamentally an **evidence-sufficiency and passage-entailment pipeline**. The verifier must assess whether candidate evidence directly supports or contradicts the required clinical learning objective/claim.

---

## 4. Search Implementation & Exact vs. ANN Retrieval Audit

- Inspected `src/medicalplab/learn/renal_retrieval.py` (`QwenRenalRetrieverV3.retrieve`):
  ```python
  p_scores = self._embeddings @ query_emb
  d_scores = self._doc_embeddings @ query_emb
  combined_scores[i] = p_scores[i] + self.alpha_doc_prior * doc_boost
  cand_indices = combined_scores.argsort()[::-1][:self.candidate_depth]
  ```
- **Finding:** The retrieval pipeline uses **exact brute-force vector dot product** (matrix multiplication over 2,691 chunks and 23 document vectors).
- **ANN Status:** No Approximate Nearest Neighbor (ANN) indexing (Faiss, HNSW, Annoy, etc.) is in use. Vector recall is 100% exact brute-force.
- **Action:** No time will be wasted tuning ANN hyper-parameters or index structures.

---

## 5. Hardware Accelerator & Runtime Environment Audit

Logged strictly per Section 6 Hard Gate requirements:

| Environment Variable | Value | Status |
|---|---|---|
| **Python Version** | `3.12.10` (64-bit AMD64) | Production Python 3.12 |
| **Python Executable** | `C:\Users\Adham Elsayed\AppData\Local\Programs\Python\Python312\python.exe` | Verified |
| **PyTorch Version** | `2.14.0+cu130` | Verified |
| **CUDA Driver / Runtime** | `CUDA 13.0` | Verified |
| **Hardware Accelerator** | `NVIDIA GeForce RTX 3060 Laptop GPU` | Verified |
| **Available VRAM** | `6.44 GB` (6,441,926,656 bytes) | Hard Gate Passed (`torch.cuda.is_available() == True`) |
| **Transformers Version** | `5.16.1` | Verified |
| **Base Embedding Model** | `Qwen/Qwen3-Embedding-0.6B` (Revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`) | Offline verified |
| **Cross-Encoder Reranker** | `Qwen/Qwen3-Reranker-0.6B` | Offline verified |

---

## 6. Cache, Corpus & Checkpoint Infrastructure

- **Corpus Registry:** `Data/metadata/renal_source_registry_v2.json` (23 accepted PMC renal documents).
- **Active Chunking:** `Data/experiments/renal_v2/chunking/B_400_overlap` (2,691 chunks, 400 words, 40-word overlap).
- **Existing Embedding Cache:**
  - `Data/experiments/renal_v3/cache/all23_corpus_embeddings.npy` (2691x1024, float32)
  - `Data/experiments/renal_v3/cache/all23_doc_embeddings.npy` (23x1024, float32)
- **V4 Workspace Directories:**
  - Evaluation: `evaluation/renal/v4/`
  - Reports: `reports/renal_v4/`
  - Cache: `Data/experiments/renal_v4/cache/`
  - Checkpoints: `Data/experiments/renal_v4/checkpoints/`
- **Existing V4 Artifacts:** None found in repository prior to this audit.

---

## 7. Audit Conclusion & Approval to Proceed

The codebase is clean, synchronized with remote branch `origin/ai-data-execution-v1`, and fully isolated from historical heldouts. The GPU accelerator is operational.

We proceed immediately to **PHASE 3 & 4: V4 Data Lifecycle, Split Definition, and Fresh RETRIEVAL_DEV_V4 Construction**.
