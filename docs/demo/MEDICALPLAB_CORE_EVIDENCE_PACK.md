# MedicalPlab Core AI — Measurement Integrity, Benchmark Recovery & Evidence Grounding Pack

> **Document Status**: Canonical, Cryptographically Sealed & Auditor-Defensible
> **Campaign**: MedicalPlab Core AI Measurement Integrity & Grounding Authority
> **Production Runtime Invariant**: Unchanged — Production Runtime remains `QwenRenalRetrieverV3` (`RENAL_RUNTIME_VERSION = "v3"`)
> **Repository HEAD**: Checked out at `ai-data-execution-v1` (Research Checkpoint `3f0faf88421c97a29955ea5df691a539097d7ee4`)
> **Primary Scientific Rule**: Measurement Correction $\ne$ Model Improvement.

---

## 0. Metric Taxonomy & Methodological Boundary

To eliminate the scientific ambiguity that previously impeded research progress, all metrics across the lifecycle of MedicalPlab are strictly categorized into five mutually exclusive tiers:

```
[ Tier A: Historical Diagnostic Metrics ] -> Preserved as immutable historical diagnostic record (V1–V7)
[ Tier B: Invalidated / Superseded Metrics ] -> Formally classified as invalid due to measurement/lineage defects
[ Tier C: Current Trustworthy Clean Metrics ] -> Derived from audited, firewalled benchmarks with multi-positive QRELs
[ Tier D: Task-Definition / Measurement Correction Delta ] -> Delta from repairing benchmarks & fixing measurement bugs (NOT model improvement)
[ Tier E: Model Improvement Delta ] -> Performance delta between two models on the EXACT SAME valid benchmark
```

### A. Historical Metrics (Preserved Diagnostic Record)
- **Renal V7 Multi-Route (Stack A)** on `TRAIN_DEV` ($N=80$): CandidateRecall@20 = 98.75% (79/80), PassageHit@1 = 76.25% (61/80), PassageHit@5 = 91.25% (73/80).
- **Renal V7 on V6 OOD Stress Benchmark** ($N=40$): CandidateRecall@20 = 90.00% (36/40), DocumentHit@1 = 97.50% (39/40).
- **Historical Stage 8 Exhaustive BGE-M3** on `PRODUCT_DEV_V2` ($N=120$): Recall@20 = 79.17% (95/120), Recall@50 = 85.00% (102/120), Recall@100 = 88.33% (106/120).

### B. Invalidated / Superseded Metrics (Defects Formally Classified)
1. **Stage 8 Qwen3-Reranker-4B on PRODUCT_DEV_V2**:
   - *Reported*: Hit@1 = 20.00%, Hit@5 = 51.67%, Eligible Positives = 86/120.
   - *Classification*: `RERANKER_EVALUATION_INVALIDATED_BY_IMPLEMENTATION_ARTIFACT`.
   - *Forensic Cause*: Used raw passage without document title, section path, or clinical target, and evaluated only Top-25 candidates from a 4-route candidate retriever rather than the Top-100 BGE-M3 pool.
2. **Historical DocHit@1 (10.83%) vs SectionHit@1 (58.33%)**:
   - *Classification*: `CROSS_UNIVERSE_METRIC_CONFLATION`.
   - *Forensic Cause*: DocHit was measured on standalone DocumentRouter cards (ranking 23 documents); SectionHit was measured from a fused passage retrieval pool. They did not share the same ranking candidate list.
3. **`final_product_test.json` (Unexecuted N=100)**:
   - *Classification*: `FINAL_PRODUCT_TEST_STATUS = INVALIDATED_UNEXECUTED_BY_CONSTRUCTION_METHOD`.
   - *Forensic Cause*: Construction methodology used mechanical heading concatenation (`q = f"In undergraduate renal medicine, what clinical principles and evidence guide {clean_h} in {title}?"`) and sibling-chunk heuristics. Remains sealed and unconsumed.

### C. Current Trustworthy Metrics (Audited on PRODUCT_DEV_V3, N=100)
- **Reference Exhaustive BGE-M3 Retrieval**:
  - Semantic Recall@20: **58.00%** (58/100) [95% CI: 48.21%, 67.20%]
  - Semantic Recall@50: **63.00%** (63/100) [95% CI: 53.22%, 71.82%]
  - Semantic Recall@100: **69.00%** (69/100) [95% CI: 59.37%, 77.22%]
  - Exact-Gold Recall@20: **55.00%** (55/100) [95% CI: 45.24%, 64.39%]
  - Exact-Gold Recall@50: **60.00%** (60/100) [95% CI: 50.20%, 69.06%]
  - Passage DocHit@1: **56.00%** | DocHit@5: **74.00%**
  - Passage SectionHit@1: **31.00%** | SectionHit@5: **51.00%**
  - MRR: **0.2946** | nDCG@10: **0.3316**
- **Frozen Recovery Retrieval: Qwen3-Embedding-4B + BM25 -> Fixed RRF (k=60)**:
  - Semantic Recall@20: **54.00%** (54/100) [95% CI: 44.26%, 63.44%]
  - Semantic Recall@50: **64.00%** (64/100) [95% CI: 54.24%, 72.73%]
  - Semantic Recall@100: **68.00%** (68/100) [95% CI: 58.35%, 76.33%]
  - Exact-Gold Recall@20: **53.00%** (53/100) | Exact-Gold Recall@50: **62.00%** (62/100)
  - Passage DocHit@1: **57.00%** | DocHit@5: **77.00%**
  - Passage SectionHit@1: **57.00%** | SectionHit@5: **77.00%**
  - MRR: **0.2699** | nDCG@10: **0.3069**
- **Corrected Qwen3-Reranker-4B (4-bit NF4, Structured Medical Prompt)**:
  - Semantic Hit@1: **24.00%** (24/100) [95% CI: 16.71%, 33.24%]
  - Semantic Hit@3: **32.00%** (32/100) [95% CI: 23.68%, 41.69%]
  - Semantic Hit@5: **41.00%** (41/100) [95% CI: 31.91%, 50.77%]
  - Semantic Hit@10: **51.00%** (51/100) [95% CI: 41.35%, 60.58%]
  - Exact Hit@1: **19.00%** | Exact Hit@5: **35.00%**
  - MRR: **0.3198** | nDCG@10: **0.3469**
  - Movement: **23 improved, 19 unchanged, 21 degraded** (out of 63 eligible positives, degradation rate = 33.33%)
- **Stage-B CentralClaimVerifier on Held-Out Benchmark ($N=60$)**:
  - Macro-F1: **0.4697**
  - SUPPORTED Precision: **100.00%** (2/2) [95% CI: 34.24%, 100.00%]
  - CONTRADICTED Precision: **87.50%** (7/8) [95% CI: 52.91%, 97.76%]
  - High-Risk Clinical Safety Fail-Closed Rate: **100.00%** (0/10 unsafe support)
- **Legacy PLAB Cardiorespiratory 36 Questions**:
  - `EVIDENCE_VERIFIED`: **7 / 36 (19.44%)**
  - `NEEDS_SOURCE_REPAIR`: **29 / 36 (80.56%)**
  - `REJECTED`: **0 / 36 (0.00%)**
  - `Golden`: **0 / 36** (Strict requirement: Golden requires real qualified clinician review only).

### D. Measurement Correction Delta (NOT Model Improvement)
- On `PRODUCT_DEV_V2`, BGE-M3 Recall@50 was **85.00%** because 34.17% of queries leaked section headings and editorial tokens (e.g. `...in . Commentary?`, `...in . Discussion?`).
- On clean `PRODUCT_DEV_V3`, BGE-M3 Recall@50 is **63.00%**.
- This $-22.00\%$ delta represents **TASK_DEFINITION_CORRECTION_DELTA** (removing synthetic leakage), **NOT** model degradation.

---

## 1. Shared Evidence Engine Architecture

The unified Evidence Engine V2 (`src/medicalplab/evidence_engine/`) serves Course Learning, PLAB question authoring, Clinical Reasoning, and the Socratic Tutor:

```
[ Clinical Query / PLAB Proposition ]
                 │
                 ▼
     [ ClinicalQueryProcessor ]
       ├── Original Clinical Question
       ├── Canonical Query Formulation
       └── Neutral Retrieval Target
                 │
                 ▼
   [ BGEM3ExhaustiveRetriever ]
       ├── Dense Representation (1024-dim, Mode B)
       ├── Lexical Representation (Multi-lingual Sparse)
       └── Exhaustive Scoring across 2,691 Renal Chunks
                 │
                 ▼
  [ Top-50 Candidates with Provenance ]
                 │
                 ▼
      [ EvidenceReranker ] (Qwen/Qwen3-Reranker-4B, 4-bit NF4)
       ├── Structured Prompt: Instruction + Original Question + Neutral Target
       └── Hierarchical Passage: Title + Section Path + Heading + Passage
                 │
                 ▼
    [ CentralClaimVerifier (Stage-B) ]
       ├── Deterministic Veto Layer:
       │    ├── Provenance Check (Chunk in Verified Corpus)
       │    ├── Negation / Polarity Reversal Veto
       │    ├── Numeric / Threshold / Unit Veto
       │    ├── Guideline Authority Veto (NICE vs WHO)
       │    └── High-Risk Clinical Fail-Closed Gate
       └── Discrete 4-State Output:
            ├── SUPPORTED
            ├── PARTIALLY_SUPPORTED
            ├── CONTRADICTED
            └── NOT_SUPPORTED
```

---

## 2. Forensic Measurement-Integrity Findings

### 2.1 The "106 vs 86" Contradiction Resolved
- **Discrepancy**: Prior summary reports cited BGE-M3 Top-100 Semantic Recall as $106/120$ ($88.33\%$), but stated that the reranker had only $86/120$ eligible positives in its candidate input pool.
- **Root Cause**: Two different candidate artifacts at two different candidate depths were conflated:
  - $86/120$ was the semantic hit count inside the **Top-25 candidate pool** produced by the 4-route `CandidateRetriever` (Qwen-0.6B Dense + BM25).
  - $106/120$ was the semantic hit count inside the **Top-100 candidate pool** produced by the exhaustive BGE-M3 retriever.
- **Resolution**: Canonical candidate lineage artifact generated and persisted: `reports/evidence_engine/canonical_candidate_lineage.json` (SHA-256: `f0e00e4e7c50f5d22e2ae645474814bf467ab7e0d5c1cca3337ba1d9da1f371e`).

### 2.2 DocHit vs SectionHit Hierarchy Restored
- **Discrepancy**: Stage 8 reported `DocHit@1 = 10.83%` while `SectionHit@1 = 58.33%`, appearing to violate the logical hierarchy that a section hit implies a document hit.
- **Root Cause**: The two metrics were evaluated across different candidate universes:
  - `DocHit` was evaluated on the **DocumentRouter** (which ranked 23 document cards).
  - `SectionHit` was evaluated on the **Passage Retriever** (which ranked passages from the 4-route candidate pool).
- **Resolution**: Evaluated from the **same ranked passage list** on `PRODUCT_DEV_V3`, the hierarchical invariant holds strictly across all depths:
  - $DocHit@1 = 56.00\% \ge SectionHit@1 = 31.00\%$
  - $DocHit@5 = 74.00\% \ge SectionHit@5 = 51.00\%$
  - $DocHit@10 = 80.00\% \ge SectionHit@10 = 62.00\%$

---

## 3. Benchmark Repair: From PRODUCT_DEV_V2 to PRODUCT_DEV_V3

### 3.1 Blinded All-Query Audit of PRODUCT_DEV_V2 ($N=120$)
All 120 items in `PRODUCT_DEV_V2` were audited blindly (without access to retrieval ranks or model identities):

| Classification | Count | Percentage | Primary Defect / Characteristics |
| :--- | :---: | :---: | :--- |
| **VALID_PRODUCT_QUERY** | 77 | 64.17% | Authentic undergraduate clinical questions (only 46 distinct non-templated queries) |
| **EDITORIAL_STRUCTURE_QUERY** | 41 | 34.17% | Artificial queries targeting publication structure (`...in . Commentary?`, `...in . Discussion?`) |
| **QUERY_EVIDENCE_MISMATCH** | 2 | 1.67% | Query premise disconnected from cited evidence chunk |
| **Total Audited** | **120** | **100.0%** | Audit artifact: `reports/evidence_engine/product_dev_v2_blinded_audit.json` |

### 3.2 PRODUCT_DEV_V3 Construction & Cryptographic Freeze
- **Curriculum Blueprint**: 20 pre-declared clinical categories (Physiology, AKI, CKD, Glomerulonephritis, Transplantation, Electrolytes, Acid-Base, Urinalysis, Imaging, Pharmacology, etc.) with 5 items each.
- **Multi-System Blinded QREL Pool**: Candidates pooled across BGE-M3 Top-100, Qwen Dense Top-100, BM25 Top-100, and structural siblings, adjudicated without retriever rank or score visibility.
- **Cryptographic Firewall**: Strict bitwise check against `renal-train-dev-v7`, `renal-product-test-v7`, `renal-ood-stress-v6`, and `final_product_test.json`: **0 leaks detected**.
- **Benchmark Artifact**: `evaluation/evidence_engine/product_dev_v3.json` ($N=100$)
- **SHA-256 Digest**: `dfed4a3c3ddeaa3b854317089747ce5bd2ad482867195cb0ce14c68620578746`

---

## 4. Clean Reference & Frozen Recovery Retrieval on PRODUCT_DEV_V3 ($N=100$)

Conducted across all 100 queries of `PRODUCT_DEV_V3` against the 2,691 Renal corpus chunks.

### 4.1 Comparative Retrieval Performance
| Configuration | Semantic Recall@20 | Semantic Recall@50 | Semantic Recall@100 | Exact-Gold Recall@20 | MRR | nDCG@10 | Median Rank | Max Rank |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BGE-M3 Exhaustive (Baseline)** | **58.00%** (58/100) | **63.00%** (63/100) | **69.00%** (69/100) | 55.00% | **0.2946** | **0.3316** | **10.0** | **2470** |
| **Qwen3-Embedding-4B (Dense Only)** | 55.00% (55/100) | 64.00% (64/100) | 68.00% (68/100) | 51.00% | 0.3007 | 0.3346 | 11.0 | 2692 |
| **Okapi BM25 (Lexical Only)** | 52.00% (52/100) | 60.00% (60/100) | 67.00% (67/100) | 51.00% | 0.2224 | 0.2607 | 17.0 | 2692 |
| **Fixed RRF (Qwen-4B + BM25, k=60)** | **54.00%** (54/100) | **64.00%** (64/100) | **68.00%** (68/100) | **53.00%** | **0.2699** | **0.3069** | **11.0** | **2692** |

### 4.2 Detailed Depth Metrics: Frozen Fixed RRF (Qwen-4B + BM25)
- **Semantic Recall@1**: 15.00% (15/100) [95% CI: 9.32%, 23.28%]
- **Semantic Recall@5**: 32.00% (32/100) [95% CI: 23.68%, 41.69%]
- **Semantic Recall@10**: 46.00% (46/100) [95% CI: 36.63%, 55.74%]
- **Semantic Recall@20**: **54.00%** (54/100) [95% CI: 44.26%, 63.44%]
- **Semantic Recall@50**: **64.00%** (64/100) [95% CI: 54.24%, 72.73%]
- **Semantic Recall@100**: **68.00%** (68/100) [95% CI: 58.35%, 76.33%]
- **Semantic Recall@200**: **72.00%** (72/100) [95% CI: 62.50%, 79.88%]
- **Exact-Gold Recall@20**: 53.00% | **Exact-Gold Recall@50**: 62.00%
- **Passage DocHit@1**: 57.00% | **DocHit@5**: 77.00%
- **Passage SectionHit@1**: 57.00% | **SectionHit@5**: 77.00%
- **Predefined Retrieval Gates Assessment**:
  - Target Recall@20 >= 95.0%: Observed = **54.00%** -> **FAILED**
  - Target Recall@50 >= 98.0%: Observed = **64.00%** -> **FAILED**
- **Decision Tree Verdict**: `GENUINE_RETRIEVAL_GAP_CONFIRMED`
- **Artifacts**:
  - BGE-M3 Report: `reports/evidence_engine/product_dev_v3_bge_m3_baseline_report.json` (SHA-256: `bdc0c9662c41c932e3a2751e49c3c67c50abfe5878d9c863ea250d09365d2aef`)
  - Qwen-4B RRF Report: `reports/evidence_engine/product_dev_v3_qwen4b_rrf_report.json` (SHA-256: `1ba758566a267a72617cacb96ef1009fa1a04d3abbc038885dd110c2a7757511`)

---

## 5. Corrected Qwen3-Reranker-4B Evaluation on Clean PRODUCT_DEV_V3

Evaluated `Qwen/Qwen3-Reranker-4B` (4-bit NF4, revision `22e683669bc0f0bd69640a1354a6d0aebcfeede5`) using the verified structured medical relevance prompt across candidate depth $K=50$:

| Metric | Value (N=100) | 95% Wilson Confidence Interval | Description |
| :--- | :---: | :---: | :--- |
| **Semantic Hit@1** | **24.00%** (24/100) | [16.71%, 33.24%] | At least one semantic positive ranked at rank 1 |
| **Semantic Hit@3** | **32.00%** (32/100) | [23.68%, 41.69%] | At least one semantic positive ranked in top 3 |
| **Semantic Hit@5** | **41.00%** (41/100) | [31.91%, 50.77%] | At least one semantic positive ranked in top 5 |
| **Semantic Hit@10** | **51.00%** (51/100) | [41.35%, 60.58%] | At least one semantic positive ranked in top 10 |
| **Exact Hit@1** | **19.00%** (19/100) | [12.48%, 27.79%] | Exact-gold chunk placed at rank 1 |
| **Exact Hit@5** | **35.00%** (35/100) | [26.35%, 44.82%] | Exact-gold chunk placed in top 5 |
| **MRR** | **0.3198** | — | Mean Reciprocal Rank across 100 queries |
| **nDCG@10** | **0.3469** | — | Normalized Discounted Cumulative Gain at 10 |

### Rank Movement Analysis (Eligible Positives = 63/100)
- **Eligible Positives**: 63 queries contained at least one semantic positive in the Top-50 candidate pool.
- **Improved**: **23 / 63 (36.51%)** queries had their positive rank promoted.
- **Unchanged**: **19 / 63 (30.16%)** queries maintained their initial rank.
- **Degraded**: **21 / 63 (33.33%)** queries had their positive rank demoted.
- **Degraded Rate Gate**: Observed 33.33% > 10.0% threshold -> **Degradation gate failed**.
- **Artifact**: `reports/evidence_engine/product_dev_v3_reranker_report.json` (SHA-256: `d56d68fe5b36dac5679299fb546e06d043217bed689643a3da9d9c9a06988544`)

---

## 5. Stage-B Central Claim-Verifier Authority & Benchmark Evaluation

Evaluated on the held-out `claim_verifier_benchmark.json` ($N=60$ balanced across 4 discrete states, including 14 mandatory clinical hard cases):

### 5.1 Multi-Class Grounding Confusion Matrix
| Ground Truth \ Predicted | SUPPORTED | PARTIALLY_SUPPORTED | CONTRADICTED | NOT_SUPPORTED | Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **SUPPORTED** | **2** | 6 | 0 | 7 | 15 |
| **PARTIALLY_SUPPORTED** | 0 | **8** | 1 | 6 | 15 |
| **CONTRADICTED** | 0 | 5 | **7** | 3 | 15 |
| **NOT_SUPPORTED** | 0 | 1 | 1 | **13** | 15 |
| **Total Predicted** | 2 | 20 | 9 | 29 | **60** |

### 5.2 Performance Metrics
- **Macro-F1**: **0.4697**
- **SUPPORTED**: Precision = **100.00%** (2/2), Recall = **13.33%** (2/15), F1 = **0.2353**
- **PARTIALLY_SUPPORTED**: Precision = **40.00%** (8/20), Recall = **53.33%** (8/15), F1 = **0.4571**
- **CONTRADICTED**: Precision = **87.50%** (7/8), Recall = **46.67%** (7/15), F1 = **0.6087**
- **NOT_SUPPORTED**: Precision = **43.33%** (13/29), Recall = **86.67%** (13/15), F1 = **0.5778**
- **Safety Integrity**:
  - False Support Rate (unsafe accept on unsupported/contradicted): **20.00% (6/30)** [95% CI: 9.50%, 37.31%]
  - High-Risk Clinical Safety Fail-Closed Rate: **100.00%** (0 / 10 unsafe supports on high-risk claims)
- **Artifact**: `reports/evidence_engine/claim_verifier_evaluation_report.json` (SHA-256: `827a52f429b03bc412932f6bb1885f38e24c7471514bdb8d923d3e5f2cb1a88a`)

---

## 6. Legacy PLAB Cardiorespiratory Question Bank Re-Adjudication

All 36 legacy questions in `Data/questions/cardiorespiratory_batch_1.json` were audited against the shared Stage-B evidence verification layer:

| Metric / Dimension | Value | Methodological Standard |
| :--- | :---: | :--- |
| **Total Legacy Questions** | 36 | `cardiorespiratory_batch_1_v1` |
| **EVIDENCE_VERIFIED** | **7 / 36 (19.44%)** | Cited evidence strictly entails why the correct option is medically correct |
| **NEEDS_SOURCE_REPAIR** | **29 / 36 (80.56%)** | Clinically sound questions requiring replacement citations / specific authority bindings |
| **REJECTED** | **0 / 36 (0.00%)** | Zero medically invalid or unrepairable questions |
| **False-Positive Citations Detected** | 18 | Quotes defining general context without mentioning correct clinical option |
| **Authority Mismatches Detected** | 2 | Stem citing NICE guidelines while evidence was drawn from non-NICE corpus documents |
| **Human-Reviewed / Golden** | **0 / 36 (0.00%)** | **Invariant**: Golden = 0 until actual qualified UK clinician review is completed |
| **Scale-to-200 Gate Status** | **LOCKED** | Stopped at 36; scaling to 200 questions requires explicit owner authorization |

---

## 7. Safety, Clinical Reasoning & Tutor Evaluation Specifications

### 7.1 Safety Evaluation Framework
- **Adversarial Check ($N=40$)**: Formally designated as `ADVERSARIAL_UNSAFE_ACCEPT_CHECK` (not full safety validation).
- **Answerability & Safety Benchmark ($N=80$)**: Evaluated on `evaluation/renal/v7/renal-answerability-safety-v7.json`:
  - Answerability Precision: **96.15% (25/26)** [95% CI: 80.36%, 99.90%]
  - Answerability Recall: **62.50% (25/40)** [95% CI: 45.88%, 77.27%]
  - Safe Abstention Rate on Unsupported: **97.50% (39/40)**
  - Unsafe Acceptance Rate: **2.50% (1/40)**
  - Overall Safety Gate: **FAILED (Recall 62.5% < 75% threshold)** due to overly conservative abstention.

### 7.2 Clinical Reasoning Evaluation Framework (Frozen 9-Dimensional Rubric)
Future Clinical Reasoning evaluations must report each dimension independently:
1. *Problem Representation* (synthesis of patient presentation)
2. *Differential Diagnosis* (plausible options ranked by likelihood)
3. *Dangerous Diagnosis Omissions* (exclusion of lethal conditions)
4. *Investigation Selection* (evidence-based diagnostic choices)
5. *Investigation Sequencing* (appropriate escalation from bedside to invasive)
6. *Management Formulation* (guideline-concordant therapy)
7. *Evidence Support* (citations binding to verified corpus)
8. *Unsafe Recommendations* (contraindicated drugs/dosages)
9. *Schema Validity* (strict JSON contract compliance)

### 7.3 Socratic Tutor Evaluation Framework (Frozen 6-Dimensional Rubric)
1. *Pedagogical Progression* (stepwise guidance rather than immediate lecture)
2. *Hint Usefulness* (scaffolding tailored to user misunderstanding)
3. *Misconception Correction* (identifying and correcting specific diagnostic flaws)
4. *Premature Answer Disclosure Prevention* (zero answer leakage before student reasoning)
5. *Evidence Grounding* (feedback verified against Stage-B corpus)
6. *Clinical Safety* (zero endorsement of hazardous medical actions)

---

## 8. Hardware Footprint & Operational Safety

All evaluations executed strictly on local hardware (NVIDIA GeForce RTX 3060 Laptop GPU, 6GB VRAM, 16GB Host RAM):
- **Sequential Model Loading**: BGE-M3 representations fully flushed from VRAM before loading Qwen models.
- **Quantization Integrity**: 4-bit NF4 with FP16 compute via `BitsAndBytesConfig`.
- **Peak VRAM**: 5.85 GB (0 OOM events).
- **Host Memory**: Paged virtual memory managed under 12 GB commit limit.
- **Inference Mode**: `torch.inference_mode()` enabled for all evaluation loops.

---

## 9. Primary Scientific Status & Next Owner Decision

### Final Primary Scientific State:
$$\mathbf{GENUINE\_RETRIEVAL\_GAP\_CONFIRMED}$$

### Scientific Justification:
1. **Measurement Integrity Established**: The historical 106-vs-86 lineage contradiction and DocHit-vs-SectionHit hierarchy inversion were proven to be reporting artifacts and resolved via canonical lineage artifact `reports/evidence_engine/canonical_candidate_lineage.json` (SHA-256: `f0e00e4e...`).
2. **Benchmark Validity Established**: Blinded all-query audit of `PRODUCT_DEV_V2` revealed 34.17% editorial heading contamination. The clean, firewalled `PRODUCT_DEV_V3` ($N=100$) establishes an unpolluted developmental evaluation standard.
3. **Retrieval Stage Evaluated on PRODUCT_DEV_V3**:
   - The frozen recovery architecture (`Qwen3-Embedding-4B + BM25 -> Fixed RRF, k=60`) achieves:
     - Semantic Recall@20 = **54.00%** (Predefined Gate: $\ge 95.0\%$ -> **FAILED**)
     - Semantic Recall@50 = **64.00%** (Predefined Gate: $\ge 98.0\%$ -> **FAILED**)
     - Semantic Recall@100 = **68.00%**
   - Reference `BGE-M3` Exhaustive Hybrid achieves:
     - Semantic Recall@20 = **58.00%**
     - Semantic Recall@50 = **63.00%**
     - Semantic Recall@100 = **69.00%**
4. **Diagnosis**: Both reference embedding architectures (`BGE-M3` and `Qwen3-Embedding-4B`) hit a genuine zero-shot semantic ceiling around ~54–58% Recall@20 and ~63–64% Recall@50 when evaluated on authentic clinical queries without synthetic heading leakage. The gap to aspirational gates (95% @20, 98% @50) is real and confirmed.
5. **Reranking Bottleneck**: `Qwen3-Reranker-4B` evaluated across depth $K=50$ candidates achieves Hit@1 = 24.00%, Hit@5 = 41.00%, but degrades 33.33% (21/63) of eligible positives, failing the $<10\%$ degradation tolerance gate.
6. **Decision Tree Execution (Case C)**: Since measurement is trustworthy, benchmark is valid, but retrieval falls short of predefined gates, the system halts autonomously at Gate C without inventing new model variants or bake-offs.

### Recommended Next Milestone:
$$\mathbf{NEXT\_OWNER\_DECISION: M1\_DOMAIN\_SPECIFIC\_EVIDENCE\_FINE\_TUNING\_OR\_BM25\_EXPANSION}$$
- To bridge the confirmed retrieval gap from 64% Recall@50 toward product targets, the single highest-leverage intervention is domain-adapted bi-encoder fine-tuning (e.g. contrastive fine-tuning on medical evidence pairs) or clinical query expansion targeting medical terminology.
- **Explicit Boundary**: Do **NOT** train new retrieval models, fine-tune weights, swap embeddings, tune RRF weights, scale PLAB beyond 36, or unseal the final product test without explicit owner authorization.
