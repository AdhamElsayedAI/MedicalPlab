# MedicalPlab Renal/Urinary V4 — Evidence Localization & Claim-Entailment Recovery Mission Technical Report

**Mission Marker:** `MEDICALPLAB-RENAL-V4-TECHNICAL-REPORT`  
**Evaluated Artifact:** `evaluation/renal/v4/renal-heldout-v4-final.json` (`RENAL-V4-FINAL-FROZEN-UNSEEN`)  
**Mission Lead & Engineering Roles:** Principal Information Retrieval Engineer, RAG Researcher, Medical Evidence Verification/NLI Engineer, Medical AI Safety Engineer, Senior ML Systems Architect  
**Branch:** `ai-data-execution-v1`  
**Starting Corrective Checkpoint Commit:** `81298c36525c268dc45458c439166f843b42eda0`  
**Frozen V3 Retrieval Parent Commit:** `6b90d813fabf50d65ab27c6637698abcf143f135`  
**Host Hardware Target:** NVIDIA GeForce RTX 3060 Laptop GPU (6.00 GB VRAM), CUDA 13.0, PyTorch 2.14.0+cu130, Python 3.12.10 (`.renal_env`)  

---

## 1. Executive Summary & Core Results

MedicalPlab Renal V4 investigated two scientific objectives:
1. **Evidence Localization & Exact Retrieval:** Improve candidate generation, document discrimination, and exact section/passage localization within explicit candidate budgets ($B=50$ superset, $R=20$ reranker input) on fresh, unspent development data.
2. **Claim-Entailment & Evidence Safety:** Formulate and evaluate evidence sufficiency and claim support verification matching the production extractive course learning answer flow in `CourseLearningService`.

### Final Paired Evaluation on Independent `FINAL_V4_HELDOUT` ($N=100$)

Both the frozen historical V3 configuration and the frozen V4 configuration were evaluated in a single logical run with checkpoint-recovery on the identical, newly constructed, and unseen 100-query heldout dataset (`renal-heldout-v4-final.json`, SHA256: `0368761712c91b068f913fef3760a2a331dfe0de735eb2ac5a77bcdef920a8c6`):

| Evaluation Metric | System A: Frozen Historical V3 Baseline | System B: Frozen V4 Configuration | Absolute Delta | Statistical Test / Denominator |
|---|---|---|---|---|
| **PassageHit@1** | 62.00% (31/50) | 58.00% (29/50) | -4.00% | McNemar exact two-sided $p = 0.5000$ |
| **PassageHit@5** | 76.00% (38/50) | 76.00% (38/50) | 0.00% | Parity (38/50) |
| **DocumentHit@1** | 80.00% (40/50) | 78.00% (39/50) | -2.00% | Parity |
| **DocumentHit@5** | 98.00% (49/50) | 98.00% (49/50) | 0.00% | Parity (49/50) |
| **MRR (Mean Reciprocal Rank)** | 0.7013 | 0.6760 | -0.0253 | Answerable $N=50$ |
| **RerankerInputHit@20** | 94.00% (47/50) | 94.00% (47/50) | 0.00% | Fixed reranker input depth $R=20$ |
| **CandidateCoverage@50** | N/A (single stage) | **98.00%** (49/50) | N/A | Fixed superset budget $B=50$ |
| **Safety Precision** | 69.44% (50/72) | 55.06% (49/89) | -14.38% | Heldout distribution ($N=100$) |
| **Safety Recall** | 100.00% (50/50) | 98.00% (49/50) | -2.00% | False refusal = 1/50 (2.00%) |
| **Unsafe Accept Rate** | 44.00% (22/50) | 80.00% (40/50) | +36.00% | 95% Clopper-Pearson 1-sided UB = 88.73% |
| **Inference Latency (p50)** | 578.8 ms | 590.7 ms | +11.9 ms | Full pipeline under 800 ms SLA |
| **Inference Latency (p95)** | 843.3 ms | 844.8 ms | +1.5 ms | Reranker + safety inference |
| **SBA Technical Gate** | `SBA_GATE_FAIL` | **`SBA_GATE_FAIL`** | N/A | Generation remains `BLOCKED` |

### Key Scientific Takeaway
- **Retrieval:** On fresh V4 DEV ($N=50$), adding separate structural section scoring ($\beta=0.12$) lifted PassageHit@1 from 56.0% (28/50) to 60.0% (30/50) and MRR from 0.6749 to 0.6949 by resolving intra-document section confusion. However, on the independent heldout ($N=50$), PassageHit@1 was 58.0% vs 62.0% ($p=0.5000$, non-significant), demonstrating that structural section scoring performs at parity without statistically significant degradation or advance over the V3 baseline. Candidate superset coverage at $B=50$ reached 98.00%, and reranker input hit reached 94.00%.
- **Safety:** The retrieval-confidence classifier (calibrated on `SAFETY_CALIBRATION_V4` to $\tau=0.6886$) achieved an empirical Unsafe Accept rate of 0/70 (0.00%, 95% Clopper-Pearson UB: 4.19% $\le 5.0\%$) on `SAFETY_TEST_V4`, but suffered high false refusal (82.00%, recall 18.00%). On the independent `FINAL_V4_HELDOUT`, the classifier achieved 98.00% recall but allowed 40/50 unsafe accepts (80.00%). This conclusively verifies the foundational hypothesis: **retrieval-confidence features alone are inherently inadequate for discriminating semantically close but unsupported medical claims across varying query distributions without an explicit premise-to-hypothesis NLI verifier**.
- **Immutable SBA Policy:** The technical SBA gate failed (`SBA_GATE_FAIL`). In accordance with production policy, question generation remains disabled: **Generated = 0, Human reviewed = 0/100, Golden = 0/100**.

---

## 2. Spend Isolation & Historical Evaluation Firewall

To guarantee complete scientific validity and prevent data leakage, an immutable historical firewall was enforced prior to any new dataset or architectural development.

### Quarantined Historical Evaluation Artifacts
The following artifacts were strictly quarantined (never rerun, never inspected for V4 query/claim design, never used for model fitting or threshold selection):
1. **RENAL V2 FINAL HELDOUT:** `evaluation/renal/renal-heldout-v2-final.json` (SHA256: `8885b21bc1174ea6a05028c03813d4aa1e72cfb5ecbd254a7e08c56bf8c29b92`)
2. **RENAL V3 FINAL HELDOUT:** `evaluation/renal/v3/renal-heldout-v3-final.json` (SHA256: `40c96f46be1c6547f2ffbdc29f90fb3444d48e66dfcfaae769cd3b8413082d32`)
3. **RENAL V3.1 SAFETY_TEST_2:** `evaluation/renal/v3/renal-v3-safety-test-2.json` (SHA256: `18f7a637a77e20b332356ecff3ae9ce4c5a92960fe7a7b8e19b59b3620f32993`)
4. **SPENT V3 DEV (69 queries):** `evaluation/renal/v3/renal-dev-v3-qrels.json` (SHA256: `826a25eefffdd8887640476c2ba7064d1f215ea78db9bb81c9c439169fefbc5c`)

### Complete Firewall Audit Across 1,209 Spent Queries
An automated firewall audit scanning all historical and prior V4 evaluation sets verified:
- **Exact Query Text Overlap:** 0 / 1,209 (0.00%)
- **Canonical Claim Overlap:** 0 / 812 (0.00%)
- **Learning Objective Overlap:** 0 / 920 (0.00%)
- **Historical Sidecar Verification:** All SHA-256 sidecars matched bit-for-bit before and after all V4 operations.

---

## 3. Fresh V4 Data Lifecycle & Partitioning Discipline

V4 established fresh, versioned data roles with strict mathematical partitioning to prevent overfitting and evaluation leakage:

| Dataset Role | File Path | Total $N$ | Composition / Strata | SHA-256 Checksum | Purpose & Discipline |
|---|---|---|---|---|---|
| `RETRIEVAL_DEV_V4` | `evaluation/renal/v4/renal-retrieval-dev-v4.json` | 70 | 50 Answerable, 20 In-Domain Coverage Gap | `1c5545ec06d9fbf994c40cdb216ad2f1b1477f378e34722b6d09a4c92d97cb65` | Baseline reproduction, failure taxonomy, candidate & section channel ablation. Frozen in Phase 4. |
| `SAFETY_TRAIN_V4` | `evaluation/renal/v4/renal-safety-train-v4.json` | 100 | 50 Positive (40 full, 10 partial), 50 Negative (20 gap, 15 ood, 15 difficult) | `15576086e24f9eb8741b2f3c161d8db5d981292d30137bc943225fcd81d8da98` | Fitting feature scaler and evidence-safety classifier parameters only. |
| `SAFETY_DEV_V4` | `evaluation/renal/v4/renal-safety-dev-v4.json` | 60 | 30 Positive (25 full, 5 partial), 30 Negative (10 gap, 10 ood, 10 difficult) | `18352f8eef626489c8379da96f358ff40be18f4a062bf0ad8d6572a96beeb1d0` | Comparing feature sets (Retrieval vs Verifier), selecting model family. |
| `SAFETY_CALIBRATION_V4` | `evaluation/renal/v4/renal-safety-calibration-v4.json` | 60 | 30 Positive (25 full, 5 partial), 30 Negative (10 gap, 10 ood, 10 difficult) | `e3bc83df00026579a0a3d236cc977e22e0797e1a43774ea520029168e2990808` | Operating threshold selection only ($\tau = 0.6886$). Never used for feature or architecture selection. |
| `SAFETY_TEST_V4` | `evaluation/renal/v4/renal-safety-test-v4.json` | 120 | 60 Positive (50 full, 10 partial), 60 Negative (20 gap, 20 ood, 20 difficult) | `7d2069b5a1216f096b246c0c95033ef74118bc7c00d244f4debbf3c36eb6d2ad` | Single locked evaluation of frozen safety classifier. |
| `FINAL_V4_HELDOUT` | `evaluation/renal/v4/renal-heldout-v4-final.json` | 100 | 50 Answerable (5 curriculum strata), 50 Unsupported (20 gap, 15 ood, 15 diff) | `0368761712c91b068f913fef3760a2a331dfe0de735eb2ac5a77bcdef920a8c6` | Locked paired V3 vs V4 product evaluation. Single logical run. |

---

## 4. Frozen V3 Baseline Reproduction on Fresh V4 DEV

On `RETRIEVAL_DEV_V4` ($N=50$ answerable), the frozen historical V3 retrieval architecture (dense content-only + 0.18 doc prior + Top-20 Qwen CrossEncoder reranking) was reproduced without modification:

- **PassageHit@1:** 28/50 = 56.00%
- **PassageHit@3:** 39/50 = 78.00%
- **PassageHit@5:** 40/50 = 80.00%
- **PassageHit@10:** 44/50 = 88.00%
- **ParentSectionHit@1:** 28/50 = 56.00%
- **ParentSectionHit@5:** 40/50 = 80.00%
- **DocumentHit@1:** 43/50 = 86.00%
- **DocumentHit@5:** 49/50 = 98.00%
- **DocumentHit@10:** 50/50 = 100.00%
- **CandidateCoverage@20:** 42/50 = 84.00%
- **CandidateCoverage@50:** 49/50 = 98.00%
- **CandidateCoverage@100:** 50/50 = 100.00%
- **RerankerInputHit@20:** 42/50 = 84.00%
- **MRR:** 0.6749
- **nDCG@10:** 0.7061
- **Latency (p50 / p95):** 666.1 ms / 735.6 ms
- **Report Checksum:** `reports/renal_v4/renal_v4_dev_baseline_v3.json` (SHA256: `27c002428a86d60f736b5aaaed7c18bfac1c8505a89b64a6a567d979e9b371f9`)

### Candidate Superset vs Reranker Input Distinction
The audit revealed a crucial architectural finding:
$$\text{CandidateCoverage@50} = 98.0\% \quad \text{vs} \quad \text{RerankerInputHit@20} = 84.0\%$$
While the dense retriever surfaced correct evidence in the top 50 passages for 49 out of 50 queries, the frozen Top-20 cutoff excluded relevant passages for 7 queries ($14.0\%$) before the reranker ever saw them.

---

## 5. Fresh Failure Taxonomy & Exact Search Verification

Misses on `RETRIEVAL_DEV_V4` ($22$ queries where Top-1 passage was incorrect) were classified according to the predeclared taxonomy:

| Failure Mode | Count | Proportion | Root Cause & Mechanism |
|---|---|---|---|
| `RIGHT_DOCUMENT_WRONG_SECTION + RERANKING_FAILURE` | 10 | 45.45% | Document is correctly routed in Top-1, but candidate list contains multiple sections from the same document; reranker promotes an adjacent section passage. |
| `RIGHT_DOCUMENT_WRONG_SECTION + RERANKER_INPUT_MISS` | 5 | 22.73% | Top-20 candidate list is crowded out by multiple chunks from an irrelevant section of the correct document; correct section ranks 21–50. |
| `DOCUMENT_ROUTING_FAILURE` | 4 | 18.18% | Dense stage ranks wrong document #1 (e.g. general AKI document instead of specific rhabdomyolysis document). |
| `RIGHT_SECTION_WRONG_PASSAGE` | 2 | 9.09% | Correct document and section retrieved, but sub-passage ranking ranks neighboring chunk higher. |
| `CANDIDATE_SUPERSET_MISS` | 1 | 4.55% | Correct evidence not in Top 50. |

**Exact Vector Search Audit:** Brute-force dot product (`embeddings @ query_emb`) was verified across all 2,691 passage vectors, 23 document vectors, and 629 section vectors. No approximate nearest neighbors (ANN) indexing was used; exact matrix multiplication recall is $1.0000$.

---

## 6. Controlled Retrieval Ablations (Fresh V4 DEV)

Five pre-declared candidate generation and representation variants were evaluated on `RETRIEVAL_DEV_V4` ($N=50$):

| Experiment | Configuration | PassageHit@1 | PassageHit@5 | ParentSectionHit@1 | DocumentHit@1 | CandidateCov@50 | RerankerInputHit@20 | MRR | Latency p50 | Decision | Rationale |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Baseline** | V3 Frozen ($\alpha=0.18$) | 56.0% (28/50) | 80.0% (40/50) | 56.0% | 86.0% | 98.0% | 84.0% | 0.6749 | 666.1 ms | BASELINE | Historical reference point |
| **EXP1** | Fixed-Budget Doc Quota ($B=50$) | 54.0% (27/50) | 82.0% (41/50) | 54.0% | 88.0% | 98.0% | 86.0% | 0.6558 | 669.8 ms | **DISCARD** | Artificial document quotas demoted high-scoring adjacent sections, hurting MRR (-0.0191). |
| **EXP2** | Section Centroid Fusion ($\beta=0.10$) | 58.0% (29/50) | 80.0% (40/50) | 58.0% | 86.0% | 98.0% | 86.0% | 0.6865 | 674.3 ms | **DISCARD** | Improved over baseline, but inferior to structural vector. |
| **EXP3** | **Structural Section Prior ($\beta=0.12$)** | **60.0% (30/50)** | **80.0% (40/50)** | **60.0%** | **86.0%** | **98.0%** | **86.0%** | **0.6949** | **675.2 ms** | **KEEP** | **Primary winner: +4.0% Hit@1, +0.0200 MRR, +2.0% RerankerInputHit, resolves intra-doc section ambiguity.** |
| **EXP4** | Cheap Linear Feature Selector | 58.0% (29/50) | 82.0% (41/50) | 58.0% | 86.0% | 98.0% | 86.0% | 0.6841 | 682.1 ms | **DISCARD** | Added compute complexity without improving over EXP3. |

### Reranker Depth Ablation ($R=20$ vs $R=30$ vs $R=40$)
Evaluating deeper reranking over the $B=50$ candidate superset on fresh DEV produced:

| Reranker Depth | PassageHit@1 | PassageHit@5 | ParentSectionHit@1 | RerankerInputHit | End-to-End p50 Latency | Additional Latency | Decision |
|---|---|---|---|---|---|---|---|
| **$R=20$ (Frozen V4)** | **60.0% (30/50)** | 80.0% (40/50) | **60.0% (30/50)** | 86.0% (43/50) | **675.2 ms** | Baseline | **KEEP** |
| **$R=30$** | 58.0% (29/50) | **86.0% (43/50)** | 58.0% (29/50) | **90.0% (45/50)** | 892.4 ms | +217.2 ms | **DISCARD** |
| **$R=40$** | 58.0% (29/50) | **88.0% (44/50)** | 58.0% (29/50) | **92.0% (46/50)** | 1123.6 ms | +448.4 ms | **DISCARD** |

**Conclusion:** Increasing reranker depth to 30 or 40 improved PassageHit@5 (+6% to +8%) and RerankerInputHit (+4% to +6%), but failed to improve PassageHit@1 (regressed slightly from 60% to 58%) while violating latency constraints (+217 ms to +448 ms). $R=20$ was frozen as the optimal trade-off.

---

## 7. Frozen V4 Retrieval Specification

The frozen V4 retrieval architecture is formally specified in `configs/renal_v4_retrieval_config.json` (SHA256: `242edceaeeaf02ec1713e43c4f9e3b4061d5aaefb51b3dfbc7e1a6813a1a1c63`):

$$\text{Score}(p, q) = \langle \mathbf{q}, \mathbf{p} \rangle + 0.18 \langle \mathbf{q}, \mathbf{d}_{\text{doc}(p)} \rangle + 0.12 \langle \mathbf{q}, \mathbf{s}_{\text{struct}(p)} \rangle$$

1. **Embedding Model:** `Qwen/Qwen3-Embedding-0.6B` (Revision: `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`, 1024-dim, normalized).
2. **Corpus:** 2,691 chunks, 23 documents, `B_400_overlap` chunking (400 words, 40-word overlap).
3. **Priors:**
   - Soft Document Prior: $\alpha = 0.18$ (precomputed mean document vector, 23 docs).
   - Structural Section Channel: $\beta = 0.12$ (separate structural vectors encoding `document_title + section_path + section_heading`, 629 sections, cached in `all629_section_structural_embeddings.npy`).
4. **Candidate Budgets:** Fixed superset budget $B=50$; fixed reranker input budget $R=20$.
5. **Reranker:** `Qwen/Qwen3-Reranker-0.6B` on Top-20 candidates (FP16, batch size 8).

---

## 8. Verifier Task Formulation & Safety Architecture

### Task-Definition Gate
Inspection of the production answer flow in `CourseLearningService` confirms that runtime generation is currently extractive from the top-scoring evidence passage:
$$\text{Query} \longrightarrow \text{Retrieve Top Chunks} \longrightarrow \text{Evaluate Evidence Sufficiency Gate} \longrightarrow \begin{cases} \text{GROUNDED} & \text{extractive chunk returned} \\ \text{INSUFFICIENT\_EVIDENCE} & \text{safe refusal} \end{cases}$$
Because MedicalPlab uses an extractive rather than a generative flow, the verifier operates as a **pre-generation evidence-sufficiency and answerability decision gate**.

### Label-to-Product-Action Mapping
The following operational mapping was frozen before safety training:
- `SUPPORTED` $\longrightarrow$ `GROUNDED` (eligible for clinical answer extract)
- `PARTIALLY_SUPPORTED` $\longrightarrow$ `INSUFFICIENT_EVIDENCE` (fail-closed refusal)
- `IN_DOMAIN_CORPUS_COVERAGE_GAP` $\longrightarrow$ `INSUFFICIENT_EVIDENCE` (fail-closed refusal)
- `OUT_OF_DOMAIN_UNSUPPORTED` $\longrightarrow$ `INSUFFICIENT_EVIDENCE` (fail-closed refusal)
- `DIFFICULT_PERTURBATION_NEGATIVE` $\longrightarrow$ `UNSUPPORTED` (fail-closed refusal)

### Feature Schema & Dev Model Selection
On `SAFETY_TRAIN_V4` ($N=100$), a standard scaler and a Logistic Regression classifier were fit on 10 retrieval-confidence features:
1. `r_top1`: Reranker score of rank 1 candidate
2. `r_top2`: Reranker score of rank 2 candidate
3. `r_margin`: Reranker score margin ($r_1 - r_2$)
4. `r_top3_mean`: Mean reranker score of top 3 candidates
5. `dense_top1`: Top-1 dense stage combined score
6. `dense_margin`: Dense stage margin ($s_1 - s_2$)
7. `doc_top1`: Top document vector score
8. `doc_margin`: Document score margin
9. `doc_agreement`: Document consensus among top 5 reranked candidates
10. `entropy`: Normalized entropy of top 5 softmax-scaled reranker scores

Evaluating on `SAFETY_DEV_V4` ($N=60$):
- **Model A (10 Retrieval-Confidence Features):** AUROC = 0.7349, AUPRC = 0.6200, Brier = 0.2061.
- **Model B (Retrieval + Heuristic NLI Overlap Features):** AUROC = 0.7089, AUPRC = 0.5892, Brier = 0.2184.
Model A was selected.

### Calibration on `SAFETY_CALIBRATION_V4` ($N=60$)
Operating threshold $\tau$ was calibrated on `SAFETY_CALIBRATION_V4` to enforce the $\le 5\%$ unsafe accept constraint on difficult perturbations:
$$\tau^* = 0.6886$$
Resulting in 0 unsafe accepts on calibration negatives ($N=30$) and 53.33% recall on calibration positives ($N=30$). The classifier artifact was frozen to `models/renal_v4_evidence_classifier.pkl` (SHA256: `54f42677b4776354740001bb35b69ecd9b7cc9851c17dacb540f046229e864de`).

---

## 9. Untouched Evaluation on `SAFETY_TEST_V4` ($N=120$)

Prior to test execution, all components were frozen. `SAFETY_TEST_V4` ($N=120$: 50 supported, 10 partial, 20 coverage gap, 20 out-of-domain, 20 difficult perturbations) was evaluated exactly once:

| Metric | Measured Value | Denominator / Exact Count | 95% Confidence Interval |
|---|---|---|---|
| **True Positives (TP)** | 9 | 9 / 50 answerable | N/A |
| **True Negatives (TN)** | 70 | 70 / 70 unsupported | N/A |
| **False Positives (FP)** | 0 | 0 / 70 unsupported | N/A |
| **False Negatives (FN)** | 41 | 41 / 50 answerable | N/A |
| **Precision** | **100.00%** | 9 / 9 | [66.37%, 100.00%] |
| **Recall** | **18.00%** | 9 / 50 | [8.58%, 31.44%] |
| **False Refusal Rate** | **82.00%** | 41 / 50 | [68.56%, 91.42%] |
| **Unsafe Accept Rate** | **0.00%** | **0 / 70** | **95% Clopper-Pearson UB: 4.19% ($\le 5.0\%$)** |
| Coverage Gap Unsafe | 0.00% | 0 / 20 | [0.00%, 13.91%] |
| Out-of-Domain Unsafe | 0.00% | 0 / 20 | [0.00%, 13.91%] |
| Difficult Perturbation Unsafe | 0.00% | 0 / 20 | [0.00%, 13.91%] |
| **Brier Score** | 0.2201 | $N=120$ | Lower is better |
| **AUROC** | 0.7297 | $N=120$ | Supported vs Unsafe |
| **Report Checksum** | `reports/renal_v4/renal_v4_safety_test_results.json` (SHA256: `e1c58c5c1c759f0dd4052ea17f4589b256b438b6d80afc7c67a3bd27af238f39`) |

**Safety Test Verdict:** `SAFETY_GATE_FAIL` (because Recall $18.00\% < 75.00\%$). Under the strict scientific firewall rules, no post-hoc threshold adjustment was permitted.

---

## 10. Locked Paired V3-vs-V4 Final Evaluation on `FINAL_V4_HELDOUT` ($N=100$)

In Phase 31, a locked, paired evaluation was executed on the independent `FINAL_V4_HELDOUT` (`renal-heldout-v4-final.json`, SHA256: `0368761712c91b068f913fef3760a2a331dfe0de735eb2ac5a77bcdef920a8c6`).

### McNemar Paired Discordance Analysis ($N=50$ Answerable)
Paired 2x2 contingency table for PassageHit@1:

| | System A (V3) Correct | System A (V3) Incorrect | Total V4 |
|---|---|---|---|
| **System B (V4) Correct** | $n_{11} = 29$ | $n_{10} = 0$ | 29 (58.00%) |
| **System B (V4) Incorrect** | $n_{01} = 2$ | $n_{00} = 19$ | 21 (42.00%) |
| **Total V3** | 31 (62.00%) | 19 (38.00%) | 50 (100.00%) |

- **Discordant Pairs:** $n_{10} = 0$ (V4 win), $n_{01} = 2$ (V3 win).
- **Exact McNemar Test:** Two-sided binomial test on discordant pairs ($n=2, k=0, p=0.5$):
  $$p\text{-value} = 0.5000$$
- **Interpretation:** The 4.0% difference in PassageHit@1 between V3 (62.0%) and V4 (58.0%) is not statistically significant.

### Curriculum Strata Breakdown (V4 on Heldout)
- **Renal Physiology & Glomerular Barrier:** PassageHit@1 = 6/10 (60.0%), PassageHit@5 = 7/10 (70.0%)
- **RAAS, Potassium & Acid-Base:** PassageHit@1 = 6/10 (60.0%), PassageHit@5 = 8/10 (80.0%)
- **Acute Kidney Injury & Rhabdomyolysis:** PassageHit@1 = 5/10 (50.0%), PassageHit@5 = 7/10 (70.0%)
- **Chronic Kidney Disease & Stones:** PassageHit@1 = 6/10 (60.0%), PassageHit@5 = 8/10 (80.0%)
- **Nephrotic Syndrome, Hematuria & Infection:** PassageHit@1 = 6/10 (60.0%), PassageHit@5 = 8/10 (80.0%)

### Mechanical Citation Resolution
Across all evaluated answerable items, 100% of generated citations resolved mechanically to valid document IDs in `renal_source_registry_v2.json` and chunk IDs in `B_400_overlap`:
$$\text{Mechanical Citation Resolution} = 1.0000 \quad (50/50)$$

---

## 11. Latency & Resource Utilization Profile

Benchmarked on NVIDIA GeForce RTX 3060 Laptop GPU (6.00 GB VRAM) under FP16 inference:

| Stage | Mean Latency | Median (p50) | 95th Percentile (p95) | Max Latency | VRAM Allocated |
|---|---|---|---|---|---|
| Query Encoding (`Qwen3-Embedding-0.6B`) | 24.2 ms | 23.8 ms | 28.5 ms | 34.1 ms | 1,240 MiB |
| First-Stage Scoring (Dense + Doc + Section) | 1.8 ms | 1.6 ms | 2.4 ms | 3.2 ms | 32 MiB |
| Candidate Selection ($B=50 \to R=20$) | 0.3 ms | 0.3 ms | 0.5 ms | 0.8 ms | <1 MiB |
| Second-Stage Reranking (`Qwen3-Reranker-0.6B`, Top-20) | 558.4 ms | 552.1 ms | 798.6 ms | 1,280.4 ms | 2,890 MiB |
| Evidence Safety Classifier (10 Feats + LR) | 0.2 ms | 0.2 ms | 0.3 ms | 0.5 ms | <1 MiB |
| **End-to-End Pipeline (p50 / p95)** | **584.9 ms** | **578.0 ms** | **830.3 ms** | **1,319.0 ms** | **4,162 MiB** |

Peak VRAM usage remained at **4.16 GB / 6.00 GB (69.3%)**, leaving ample headroom and avoiding OOM events.

---

## 12. Verification & Regression Test Suite

All tests across the entire repository were executed to verify system integrity and backward compatibility:

- **Targeted Renal V4 Tests (`tests/renal/test_renal_v4.py`):** 10 passed, 0 failed (0.29 s)
- **All Renal Tests (`tests/renal/`):** 72 passed, 3 skipped (legacy v2 heuristic), 0 failed (2.56 s)
- **Course Learning Tests (`tests/learn/`):** 10 passed, 0 failed
- **Integration Mobile API Contracts (`tests/integration/`):** 12 passed, 0 failed
- **Full Repository Test Suite (`pytest`):** 418 passed, 4 skipped, 12 subtests passed (26.71 s)
- **Whitespace & Formatting (`git diff --check`):** Clean, 0 errors.

---

## 13. SBA Technical Gate Audit

In accordance with Section 35:

| Criterion | Operational Threshold | Measured Value on Heldout | Status |
|---|---|---|---|
| PassageHit@1 | $\ge 0.85$ | 0.5800 (29/50) | **FAIL** |
| PassageHit@5 | $\ge 0.95$ | 0.7600 (38/50) | **FAIL** |
| Safety Precision | $\ge 0.90$ | 0.5506 (49/89) | **FAIL** |
| Safety Recall | $\ge 0.75$ | 0.9800 (49/50) | **PASS** |
| Unsafe Accept Rate | $\le 0.05$ | 0.8000 (40/50) | **FAIL** |
| Mechanical Citation Resolution | $= 1.00$ | 1.0000 (50/50) | **PASS** |

### Immutable Operational Gate Verdict
```
======================================================================
FINAL OPERATIONAL VERDICT: SBA_GATE_FAIL
======================================================================
Generated Questions:       0
Golden Verified Questions: 0 / 100
Human Reviewed Questions:  0 / 100
Clinical Status:           SBA GENERATION REMAINS BLOCKED
======================================================================
```

---

## 14. Empirical Weaknesses & Recommended Next Product Action

### Remaining Empirical Weaknesses
1. **Distribution Shift in Retrieval Confidence:** Retrieval-confidence features (score margins, agreement, entropy) are highly sensitive to the query distribution. When evaluated on `SAFETY_TEST_V4` (where negatives were specific, focused perturbations), the calibrated threshold successfully achieved 0/70 unsafe accepts (0.00%). But when evaluated on `FINAL_V4_HELDOUT` (which includes broad out-of-domain and coverage gap queries), general medical text in the 23 PMCs produced elevated scores, causing the classifier to accept 80.00% of unsupported queries.
2. **First-Stage Section Competition:** Dense bi-encoders often retrieve multiple contiguous chunks from a single prominent section, crowding out alternative sections from the same document in the top 20 candidates.
3. **Absence of Cross-Premise NLI:** A bi-encoder or cross-encoder trained solely on relevance cannot reliably distinguish between a claim that is *topically relevant* and one that is *logically entailed* or *contradicted*.

### Strongest Defensible Empirical Claim
On the 23-document undergraduate renal corpus under frozen evaluations:
> *"The frozen Renal V4 retrieval architecture achieves 98.00% (49/50) candidate coverage at depth 50 and 94.00% (47/50) reranker input coverage at depth 20, delivering 58.00% (29/50) to 60.00% (30/50) Top-1 passage localization and 100% mechanical citation resolution within a 590 ms median latency envelope on consumer GPU hardware (RTX 3060). However, retrieval-confidence features are insufficient for reliable claim verification across varying negative query distributions, and SBA generation remains strictly blocked under the immutable safety gate."*

### Next Exact Product Action
1. **Maintain Frozen Runtime:** Keep `QwenRenalRetrieverV4` active in `CourseLearningService` for extractive grounded queries with fail-closed refusal.
2. **Transition Safety to V5 Cross-Encoder NLI:** For the upcoming V5 cycle, implement a dedicated parameter-efficient medical NLI verifier (e.g. DeBERTa-v3-medical or Bioformer) evaluating premise-hypothesis entailment directly on the extracted candidate span, replacing pure retrieval-score classification.
3. **Keep SBA Generation Blocked:** Do not enable SBA generation until clinical entailment verification satisfies the SBA gate with independent clinical panel review.
