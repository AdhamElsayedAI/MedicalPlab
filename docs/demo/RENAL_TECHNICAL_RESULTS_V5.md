# MedicalPlab Renal/Urinary V5 — Pre-Training Integrity, Candidate Preselection & Technical Closure Report

**Mission Marker:** `MEDICALPLAB-RENAL-V5-TECHNICAL-REPORT`  
**Active Git Branch:** `ai-data-execution-v1`  
**Parent Production Baseline:** Renal V3 (`RENAL_RUNTIME_VERSION = "v3"`, `QwenRenalRetrieverV3`)  
**Hardware Profile:** NVIDIA GeForce RTX 3060 Laptop GPU (6.00 GB VRAM), CUDA 13.0, PyTorch 2.14.0+cu130, Python 3.12 (`.renal_env`)  

---

## 1. Executive Summary & Final Scientific Status

MedicalPlab Renal V5 investigated the resolution of the candidate coverage bottleneck identified in V4, specifically aiming to transition from a single-stage dense candidate pool ($B=50$) to an expansive candidate budget ($B=500$) compressed via an intelligent, low-latency preselector to a fixed reranker input budget ($R=20$).

Following forensic audits, complete dataset decontamination, feature ablation, and query-grouped cross-validation, the **P3 Regularized Logistic Relevance Preselector** was designed, frozen, and evaluated on a fresh, leak-free validation benchmark (`SELECT_VAL_CLEAN_V1`, $N=20$).

### Core Research Results on Fresh `SELECT_VAL_CLEAN_V1` ($N=20$)

| Evaluation Dimension | Metric / Criterion | Measured Value | Gate Requirement | Verdict |
|---|---|---|---|---|
| **Candidate Preselection** | OutputCoverage@20 | **17 / 20 (85.0%)** | $\ge 85.0\%$ | **PASS** |
| **Top-20 Preservation** | Naive Top-20 Retained | **14 / 14 (100.0%)** | $\ge 95.0\%$ | **PASS** |
| **Rank 21+ Rescues** | Genuine Rescues ($>20 \to \le 20$) | **+3 queries** | $\ge 2$ rescues | **PASS** |
| **Candidate Drop Loss** | Relevant Lost ($\le 20 \to > 20$) | **0 queries** | $0$ lost | **PASS** |
| **Inference Latency** | Preselector Execution Time | **14.77 ms / query** | $\le 50.0\text{ ms}$ | **PASS** |
| **Downstream Base Reranker** | PassageHit@1 (Base Qwen3) | **15 / 20 (75.0%)** | Diagnostic | **+15.0% absolute gain vs Naive (12/20 = 60.0%)** |

### Final Engineering & Production Classification

While the P3 preselector successfully passed its predeclared research confirmation gate, its output coverage ceiling ($\text{OutputCoverage@20} = 85.0\%$) leaves zero mathematical margin against the production promotion threshold of $\text{PassageHit@1} \ge 85.0\%$. Achieving the final system gate would require a mathematically perfect downstream reranker with 100% precision across all covered queries. 

In accordance with production safety and engineering discipline, the Renal V5 workstream is formally closed without model training or production promotion:

```
SELECTOR_V5_P3 = RESEARCH_VALIDATED_NOT_PRODUCTION_PROMOTED
V5_PRODUCTION_STATUS = NOT_PRODUCTION_PROMOTED
PRODUCTION_DEFAULT = QwenRenalRetrieverV3 (RENAL_RUNTIME_VERSION = "v3")
```

---

## 2. Forensic Integrity Audit & Data Quarantine

Prior to model development, an exhaustive forensic integrity audit was conducted across the historical and generated training sets. 

### 1. Quarantine of Contaminated Data Assets
During the audit of `renal-rerank-train-v5-extended.json` ($N=80$), two critical integrity violations were identified:
- **Corpus Text Mismatch:** 11 query examples contained `gold_chunk_id` references where the annotated `passage_text` deviated from the underlying corpus text in `Data/documents/` (including paraphrased text, truncated clauses, or hallucinations from LLM generation).
- **Hard Evaluation Leakage:** 2 query items in the extended training set exhibited significant semantic overlap with unspent validation/test queries (`DEV-A`), violating strict train/dev separation.

**Action Taken:** `renal-rerank-train-v5-extended.json`, `renal-rerank-train-core-v5.json`, and `renal-rerank-train-val-v5.json` were permanently quarantined. A strict integrity audit rule was codified prohibiting any quarantined asset from ever entering model training or validation pipelines.

### 2. Assembly of Verified Clean Benchmark (`CLEAN_V1`, $N=80$)
A replacement benchmark of 80 verified clinical items was constructed from scratch:
- **100% Verbatim Evidence:** Every single ground-truth answer span was verified via exact Python string search (`span in chunk_text`) against the raw canonical text in `Data/documents/`.
- **Atomic Query Provenance:** Every query was assigned a unique clinical family, canonical claim, learning objective, and verbatim gold span.
- **Data Splits:**
  - `TRAIN_CORE_CLEAN_V1` ($N=60$): Used strictly for feature ablation, feature extraction, and preselector model fitting.
  - `TRAIN_VAL_CLEAN_V1` ($N=20$): Preserved as an isolated tuning validation split.

---

## 3. Two-Layer Firewall Audit Across All Dimensions

To guarantee zero leakage, a rigorous two-layer firewall audit was executed across all evaluation benchmarks (`DEV-A`, `DEV-B`, historical heldouts `V2`, `V3`, `V4`, and clean splits):

### Layer 1: Exact Hash & Normalized Lexical Overlap
Across all 1,200+ spent historical queries and unspent development sets:
- **Exact Query Text Matches:** 0 / 1,209 (0.00%)
- **Exact Gold Span Matches:** 0 / 1,209 (0.00%)
- **Exact Claim Matches:** 0 / 812 (0.00%)

### Layer 2: Dense Semantic Cosine Similarity ($E_{\text{dense}}(q_1, q_2) \ge 0.90$)
All query pairs were embedded with `sentence-transformers/all-MiniLM-L6-v2`. Any pair exceeding 0.90 cosine similarity underwent formal clinical adjudication:
- Out of thousands of pairwise comparisons, exactly one pair (`V5-RNK-TRN-0032` vs `V5-RNK-DEVA-0032`) reached $0.9005$ cosine similarity.
- **Clinical Adjudication:** Query 1 evaluated "calcium oxalate monohydrate dumbbell vs bipyramidal morphology" while Query 2 evaluated "treatment of acute hyperkalemic emergency with calcium gluconate". The disease entities and therapeutic claims were entirely disjoint (`SAME_DISEASE_DISTINCT_CLAIM`). Hard leakage was verified at **0 / 80 (0.00%)**.

---

## 4. $B=500$ Candidate Generation & Retrieval Ceilings

The first-stage dense retriever (`BAAI/bge-base-en-v1.5` with $+0.18$ document prior) was audited to establish candidate ceilings at depths $B \in \{20, 50, 100, 200, 500\}$:

| Split / Dataset | $N$ | Coverage@20 | Coverage@50 | Coverage@100 | Coverage@200 | Coverage@500 |
|---|---|---|---|---|---|---|
| `TRAIN_CORE_CLEAN_V1` | 60 | 47 / 60 (78.3%) | 55 / 60 (91.7%) | 58 / 60 (96.7%) | 59 / 60 (98.3%) | **60 / 60 (100.0%)** |
| `TRAIN_VAL_CLEAN_V1` | 20 | 14 / 20 (70.0%) | 17 / 20 (85.0%) | 18 / 20 (90.0%) | 20 / 20 (100.0%) | **20 / 20 (100.0%)** |
| `SELECT_VAL_CLEAN_V1` | 20 | 14 / 20 (70.0%) | 17 / 20 (85.0%) | 18 / 20 (90.0%) | 20 / 20 (100.0%) | **20 / 20 (100.0%)** |

**Empirical Finding:** At $B=500$, the first-stage dense candidate pool captures **100.0%** of all ground-truth passages across every evaluated dataset. The retrieval bottleneck was conclusively proven to be candidate compression ($B=500 \to R=20$), not candidate generation.

---

## 5. Feature Oracle & Diagnostic Ablation on `TRAIN_CORE` ($N=60$)

To identify which signals could successfully compress the $B=500$ candidate pool to $R=20$, a comprehensive feature oracle was computed across all 60 queries in `TRAIN_CORE`:

| Channel / Feature Signal | Feature Description | Coverage@20 | Coverage@50 | MRR | Median Rank |
|---|---|---|---|---|---|
| `dense_baseline` | Content cosine + 0.18 doc prior | 47 / 60 (78.3%) | 55 / 60 (91.7%) | 0.4643 | 3.5 |
| `dense_content_only` | Content cosine without doc prior | 44 / 60 (73.3%) | 54 / 60 (90.0%) | 0.4287 | 4.0 |
| `bm25_sparse_okapi` | Okapi BM25 ($k_1=1.5, b=0.75$) | **52 / 60 (86.7%)** | 56 / 60 (93.3%) | **0.5871** | **2.0** |
| `rrf_dense_bm25` | Reciprocal Rank Fusion ($k=60$) | **52 / 60 (86.7%)** | **60 / 60 (100.0%)** | **0.5917** | **2.0** |
| `section_centroid` | Cosine similarity with section centroid | 34 / 60 (56.7%) | 45 / 60 (75.0%) | 0.2872 | 16.0 |
| `lexical_jaccard` | Token-level Jaccard coefficient | 49 / 60 (81.7%) | 55 / 60 (91.7%) | 0.4912 | 3.0 |
| `lexical_containment`| Fraction of query tokens in chunk | 48 / 60 (80.0%) | 54 / 60 (90.0%) | 0.4789 | 3.0 |

### Key Scientific Takeaways:
1. **The Sparse BM25 Advantage:** In medical nephrology, lexical precision on specialized anatomical and pharmacological terms ("focal segmental glomerulosclerosis", "tacrolimus", "NKCC2", "PCNL", "SGLT2") is remarkably diagnostic. BM25 alone outperformed the dense retriever by $+8.4\%$ in Top-20 coverage (86.7% vs 78.3%) and improved MRR from 0.4643 to 0.5871.
2. **Dense + Sparse Synergy:** Combining dense and sparse channels via Reciprocal Rank Fusion achieved 100.0% coverage at $R=50$ and 86.7% coverage at $R=20$.

---

## 6. P3 Preselector Architecture & Cross-Validation

Guided by the oracle ablation, candidate selector **P3** was formulated as a regularized logistic relevance scorer operating over 5 query-standardized features.

### Architecture & Mathematical Formulation
For each candidate chunk $c \in \mathcal{C}_q$ ($|\mathcal{C}_q| = 500$), the feature vector $x_{q, c} \in \mathbb{R}^5$ is computed:
1. $x_1$: `dense_combined` (first-stage dense score)
2. $x_2$: `bm25_sparse` (Okapi BM25 score)
3. $x_3$: `section_centroid` (query-to-centroid cosine)
4. $x_4$: `lexical_jaccard` (token Jaccard similarity)
5. $x_5$: `lexical_containment` (token containment fraction)

**Query-Grouped Standardization:**
$$z_{q, c, i} = \frac{x_{q, c, i} - \mu_{q, i}}{\sigma_{q, i} + 10^{-9}}$$

**Relevance Logit & Ranking:**
$$S(q, c) = w^T z_{q, c} + b$$
The candidates are sorted descending by $S(q, c)$, and the top $R=20$ candidates are emitted to the reranker.

### 5-Fold Query-Grouped Cross-Validation on `TRAIN_CORE` ($N=60$)
To prevent intra-query candidate leakage, splitting was performed strictly by Query Family (12 query families per fold; zero candidate-row splitting):

- **Out-of-Fold OutputCoverage@20:** **56 / 60 (93.3%)** (+15.0% absolute gain over naive Top-20)
- **Naive Top-20 Preservation:** **45 / 47 (95.7%)**
- **Genuine Rescues ($>20 \to \le 20$):** **+11 queries**
- **Relevant Lost ($\le 20 \to > 20$):** 2 queries
- **Mean Reciprocal Rank (MRR):** **0.6610**
- **Median Best Relevant Rank:** **1.0**

### Model Freezing
The P3 parameters were frozen into [reports/renal_v5/renal_v5_p3_model_specification.json](file:///c:/Users/Adham%20Elsayed/Desktop/AdhamElsayedAI/MedicalPlab/reports/renal_v5/renal_v5_p3_model_specification.json) (SHA-256: `dff886928cd59745b7063590c124dbb5f4eabba39b104f904da77ef272365d55`):
- `w_dense_combined` = $+2.2092$
- `w_bm25_sparse` = $+0.9713$
- `w_section_centroid` = $-1.1760$
- `w_lexical_jaccard` = $-0.1285$
- `w_lexical_containment` = $+0.1322$
- `intercept` = $-5.6704$

---

## 7. Fresh One-Shot Validation on `SELECT_VAL_CLEAN_V1` ($N=20$)

A fresh validation split of 20 previously unseen clinical queries (`SELECT_VAL_CLEAN_V1`, SHA-256: `70424669d0f67c69eda8275f8f6203f752b34bdbe7a5df05cc9fedacb36527b3`) was constructed with 100% verified verbatim evidence spans and zero leakage.

The frozen P3 selector was evaluated in a single locked execution:

### One-Shot Gate Verification

| Gate Criterion | Target Threshold | P3 Actual Result | Status |
|---|---|---|---|
| **OutputCoverage@20** | $\ge 85.0\%$ (17/20) | **17 / 20 (85.0%)** | **PASS** |
| **Naive Preservation** | $\ge 95.0\%$ (14/14) | **14 / 14 (100.0%)** | **PASS** |
| **Genuine Rescues** | $\ge 2$ queries | **+3 queries** | **PASS** |
| **Relevant Lost** | $0$ queries | **0 queries** | **PASS** |
| **Inference Latency** | $\le 50.0\text{ ms}$ | **14.77 ms** | **PASS** |

### Detailed Rescue Dynamics
P3 successfully rescued 3 ground-truth passages that were completely missed by the first-stage Top-20 cutoff:
1. `V5-RNK-SELVAL-0001`: Dense rank **153** $\to$ P3 rank **16** (Rescued $\to$ Downstream Hit@1)
2. `V5-RNK-SELVAL-0010`: Dense rank **46** $\to$ P3 rank **1** (Rescued $\to$ Downstream Hit@1)
3. `V5-RNK-SELVAL-0019`: Dense rank **118** $\to$ P3 rank **1** (Rescued $\to$ Downstream Hit@1)

### Downstream Base Reranker Coupling
Passing the P3 preselected Top-20 into the base Qwen 0.5B CrossEncoder yielded:
- **Naive Top-20 PassageHit@1:** 12 / 20 = 60.0%
- **P3 Preselected Top-20 PassageHit@1:** **15 / 20 = 75.0%** (+15.0% absolute improvement)

---

## 8. Final Renal V5 Closure Section

### Scientific & Operational Status
```
============================================================
FINAL STATUS:
SELECTOR_V5_P3 = RESEARCH_VALIDATED_NOT_PRODUCTION_PROMOTED
V5_STATUS = NOT_PRODUCTION_PROMOTED
============================================================
```

### Empirical Record on Fresh SELECT_VAL ($N=20$)
```
Fresh SELECT_VAL:
OutputCoverage@20 = 17/20 = 85%
PassageHit@1 base reranker = 15/20 = 75%
```
- **Preselector OutputCoverage@20:** 17/20 = 85% (17 / 20, 85.0%)
- **Downstream Base Reranker PassageHit@1:** 15/20 = 75% (15 / 20, 75.0%)
- **Preselector Latency:** 14.77 ms / query

### Explicit Non-Execution Disclosures
In accordance with explicit project governance and safety boundaries, it is explicitly stated:
- LoRA NOT RUN
- DEV-B PERFORMANCE NOT RUN
- FINAL_V5_HELDOUT NOT RUN
- safety workstream NOT fully promoted
- V5 is therefore NOT production promoted

### Preservation of V3 as Production Default
The production runtime default remains unmodified:
- **Default Runtime Version:** `RENAL_RUNTIME_VERSION = "v3"` (in `src/medicalplab/learn/service.py`)
- **Default Retriever Class:** `QwenRenalRetrieverV3`
- **Regression Safety:** Regression test suites enforce that V5/P3 cannot silently become the runtime default.

### Architectural Rationale for Closure
The immutable promotion gate for MedicalPlab retrieval requires $\text{PassageHit@1} \ge 85.0\%$. Because the P3 preselector ceiling on fresh validation is exactly $85.0\%$ (17/20), meeting the downstream system requirement would demand that the cross-encoder reranker achieve 100% precision on every covered candidate pool, tolerating zero classification errors. This provides insufficient margin for production promotion.

Closing the Renal V5 workstream at this milestone locks in a clean, reproducible research advance while ensuring project resources remain dedicated to the mentor-facing MVP deliverables.

---

## 9. Complete V5 Artifact & Checksum Manifest

| Artifact Type | File Path | SHA-256 Checksum |
|---|---|---|
| **Clean Train Core ($N=60$)** | `evaluation/renal/v5/renal-rerank-train-core-v5-clean-v1.json` | `7634392ab98bb4a35d640d23fd6b32812abbcbd1c8aa4e0eef053fa2059979f7` |
| **Clean Train Val ($N=20$)** | `evaluation/renal/v5/renal-rerank-train-val-v5-clean-v1.json` | `8771aefdd2588c7f0303f4f884dc022549c82ccb1ecc7a4f308261b8ea8a0aa1` |
| **Clean Full Train ($N=80$)** | `evaluation/renal/v5/renal-rerank-train-v5-clean-v1.json` | `818cded1a5f9fa8aaf52b4dd61d106bf827159bfd5f65c078fd3697e9e78761e` |
| **Clean Select Val ($N=20$)** | `evaluation/renal/v5/renal-rerank-select-val-clean-v1.json` | `70424669d0f67c69eda8275f8f6203f752b34bdbe7a5df05cc9fedacb36527b3` |
| **P3 Frozen Model Spec** | `reports/renal_v5/renal_v5_p3_model_specification.json` | `dff886928cd59745b7063590c124dbb5f4eabba39b104f904da77ef272365d55` |
| **P3 Validation Results** | `reports/renal_v5/renal_v5_p3_select_val_results.json` | Measured & Verified |
| **V5 Formal Closure Report** | `reports/renal_v5/renal_v5_closure_report.json` | Verified |
| **Quarantined Extended Train** | `evaluation/renal/v5/renal-rerank-train-v5-extended.json` | `cdcb9fadd606203a60a9480a39ea9f93b82d25b7f5c8cdb370e806ae4da16ac2` |
| **Unspent DEV-A ($N=40$)** | `evaluation/renal/v5/renal-rerank-dev-a-v5.json` | `8d9e0fddab87f14cc7ba404ed30256f713f1ab62e9aabe674c6a4c032b1195ec` |
| **Unspent DEV-B ($N=40$)** | `evaluation/renal/v5/renal-rerank-dev-b-v5.json` | `4e1e3fe44a3fed187f7f4e65bfb66b1efc700cd5285fb37e3b292789e14f41f7` |
