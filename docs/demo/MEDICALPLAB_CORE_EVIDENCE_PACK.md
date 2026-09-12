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

## 4. Clean Reference Retrieval Re-Baseline on PRODUCT_DEV_V3

Conducted across all 100 queries of `PRODUCT_DEV_V3` against the 2,691 Renal corpus chunks (`BAAI/bge-m3`, revision `5617a9f61b028005a4858fdac845db406aefb181`):

| Depth ($K$) | Semantic Recall ($K$) | Exact-Gold Recall ($K$) | Passage DocHit ($K$) | Passage SectionHit ($K$) |
| :---: | :---: | :---: | :---: | :---: |
| **@1** | 20.00% (20/100) | 18.00% (18/100) | 56.00% (56/100) | 31.00% (31/100) |
| **@5** | 38.00% (38/100) | 36.00% (36/100) | 74.00% (74/100) | 51.00% (51/100) |
| **@10** | 51.00% (51/100) | 48.00% (48/100) | 80.00% (80/100) | 62.00% (62/100) |
| **@20** | **58.00%** (58/100) [48.2%, 67.2%] | **55.00%** (55/100) [45.2%, 64.4%] | 83.00% (83/100) | 68.00% (68/100) |
| **@50** | **63.00%** (63/100) [53.2%, 71.8%] | **60.00%** (60/100) [50.2%, 69.1%] | 86.00% (86/100) | 71.00% (71/100) |
| **@100** | **69.00%** (69/100) [59.4%, 77.2%] | **66.00%** (66/100) [56.3%, 74.5%] | 90.00% (90/100) | 75.00% (75/100) |
| **@200** | **73.00%** (73/100) | **69.00%** (69/100) | 92.00% (92/100) | 76.00% (76/100) |

- **Summary Ranking Metrics**:
  - MRR: **0.2946**
  - nDCG@10: **0.3316**
  - Rank Distribution: Median = 10.0, p75 = 204.0, p90 = 835.0, Max = 2470
- **Artifact**: `reports/evidence_engine/product_dev_v3_bge_m3_baseline_report.json` (SHA-256: `bdc0c9662c41c932e3a2751e49c3c67c50abfe5878d9c863ea250d09365d2aef`)

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
$$\mathbf{BENCHMARK\_REPAIR\_RESOLVED\_PRIMARY\_FAILURE}$$

### Scientific Justification:
1. Historical reports of "model semantic failure" were an artifact of benchmark contamination: 34.17% of `PRODUCT_DEV_V2` items contained artificial editorial heading concatenation rather than genuine clinical inquiries.
2. The hierarchical metric conflict (`DocHit@1 < SectionHit@1`) and candidate discrepancy (`106 vs 86`) were implementation and cross-universe reporting defects, not model failures.
3. On the clean, firewalled `PRODUCT_DEV_V3`, reference BGE-M3 retrieval achieves a baseline of 58.0% Recall@20 and 63.0% Recall@50 without any fine-tuning.
4. Stage-B CentralClaimVerifier provides 100% fail-closed protection on high-risk medical contraindications, but lexical heuristics limit general semantic recall (13.33%), establishing the need for an independent semantic NLI verification signal.

### Recommended Next Milestone:
$$\mathbf{NEXT\_OWNER\_DECISION: M1\_INDEPENDENT\_BIOMEDICAL\_NLI\_VERIFICATION}$$
- Evaluate at most **one** off-the-shelf biomedical NLI model (e.g. `BioLinkBERT-NLI` or `MedNLI`) strictly within the Stage-B evidence verifier on `claim_verifier_benchmark.json` to test whether it improves SUPPORTED recall beyond lexical heuristics while preserving zero high-risk false-support.
- **Do NOT** train new retrieval models, swap embeddings, tune RRF weights, or scale PLAB beyond 36 without explicit owner authorization.
