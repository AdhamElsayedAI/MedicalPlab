# MedicalPlab Renal Retrieval Technical Results — V6 Forensic Post-Mortem & Closure

**Document Version**: 1.0.0  
**Date**: 2026-09-11  
**Status**: CLOSED / RESEARCH DIAGNOSTIC ONLY  
**Production Runtime**: `QwenRenalRetrieverV3` (`RENAL_RUNTIME_VERSION = "v3"`)  
**LoRA Status**: BLOCKED  
**Final Decision**: `PRESERVE_V3_AND_MOVE_TO_PLAB`  

---

## Executive Summary

The Renal V6 engineering campaign evaluated whether an expanded training curriculum ($N=80$), enhanced multi-signal feature engineering (Feature Oracle v2), and regularized passage selector families could achieve sufficient candidate coverage to authorize downstream LoRA fine-tuning and production promotion.

On the frozen, unspent fresh validation benchmark ($N=40$, zero-leakage firewalled), the selected Class A regularized logistic selector achieved **$45.00\%$ Coverage@20 ($18/40$)**, failing the mandatory pre-registered feasibility gate of $\ge 92.0\%$ (`FAIL_COVERAGE_BELOW_92`). 

Consequently:
1. **LoRA Fine-Tuning is BLOCKED**.
2. **DEV-B and Final Held-out benchmarks remain completely UNEXECUTED and unspent**.
3. **Production runtime remains frozen at `QwenRenalRetrieverV3`**.
4. **Renal V6 is permanently closed as a diagnostic benchmark**. No V7 is authorized.

---

## 1. Canonical Metrics

The empirical retrieval metrics across training and validation stages are frozen and verified:

### TRAIN Benchmark ($N=80$, 12 Curriculum Strata, 11 Source Documents)
* **Raw Dense Baseline Coverage@20**: 59 / 80 = **73.75%**
* **Selected Class A Selector OOF Coverage@20**: 75 / 80 = **93.75%**
* **Selected Class A Worst Fold Coverage**: **86.67%**
* **Selected Class A Naive Preservation**: **98.31%** (58/59)
* **Rank >= 21 Rescues**: 17 queries

### Frozen SELECT_VAL Benchmark ($N=40$, 14 Curriculum Strata, 14 Source Documents)
* **Raw Dense Coverage@20**: 15 / 40 = **37.50%**
* **Raw Dense Coverage@50**: 24 / 40 = **60.00%**
* **Raw Dense Coverage@100**: 26 / 40 = **65.00%**
* **Raw Dense Coverage@200**: 30 / 40 = **75.00%**
* **Raw Dense Coverage@500**: 36 / 40 = **90.00%**
* **Frozen Class A Selector Coverage@20**: 18 / 40 = **45.00%**

### Explicit Distinction Between Raw Dense and Selector
* **RAW DENSE TRAIN**: 73.75%
* **SELECTOR TRAIN OOF**: 93.75%
* **RAW DENSE SELECT_VAL**: 37.50%
* **SELECTOR SELECT_VAL**: 45.00%

---

## 2. Predeclared V6 Gate Language & Evaluation

The pre-registered Phase 6 fresh selector confirmation gate thresholds were:

* **STRONG PASS**: Coverage@20 $\ge 95.0\%$
* **CONDITIONAL PASS**: Coverage@20 $\ge 92.0\%$
* **FAIL**: Coverage@20 $< 92.0\%$

### Evaluation Verdict
```text
GATE_VERDICT = FAIL_COVERAGE_BELOW_92
```

### Threshold Clarification
The $\ge 85.0\%$ figure in historical documentation refers to the downstream end-to-end `PassageHit@1` production service objective. Achieving $\ge 85.0\%$ `PassageHit@1` from a $45.0\%$ selector output would require a conditional reranker accuracy of:
$$\text{Required Reranker Accuracy} = \frac{0.85}{0.45} = 188.89\%$$
which is mathematically impossible ($> 100\%$). The operative authorization threshold for the fresh selector was $\ge 92.0\%$, which failed decisively.

---

## 3. Benchmark Interpretation & Diagnostic Value

The frozen $N=40$ SELECT_VAL benchmark is classified under governance as:

```text
VALID_AS_DIAGNOSTIC_STRESS_TEST
NOT_VALID_AS_A_LIKE_FOR_LIKE_ESTIMATE_OF_THE_ORIGINAL_CLINICAL_QUERY_DISTRIBUTION
```

### Forensic Justification
1. **Query Authoring Discrepancy**:
   * **TRAIN ($N=80$)**: Queries were clinical, biomedical entity, and claim-driven (e.g., specific histopathology, lab cutoffs, diagnostic criteria).
   * **SELECT_VAL ($N=40$)**: Queries were synthesized via section and heading templates (e.g., *"What clinical or physiological evidence regarding [section] is documented in [heading]?"*).
2. **Prohibited Descriptions**:
   The $45.0\%$ selector validation result must **NOT** be described as:
   * MedicalPlab Renal system accuracy;
   * Production user accuracy;
   * Expected clinical performance;
   * A like-for-like estimate of the original intended clinical query distribution.
3. **Authorized 4-Point Interpretation**:
   * The benchmark exposed a genuine retrieval robustness weakness for section-anchored, low-entity-specific queries.
   * It revealed first-stage intra-document discrimination weakness under that stress-test distribution.
   * It is NOT an equivalent replacement for the intended clinical/mechanistic query benchmark.
   * It remains valid for governance purposes and correctly blocks V6 promotion.

---

## 4. Root Cause Classification

### Primary Root Cause
```text
PRIMARY_ROOT_CAUSE = BENCHMARK_CONSTRUCTION_INCONSISTENCY
```
* **Mechanism**: The shift from granular biomedical entity tokens in TRAIN to high-level section names in SELECT_VAL caused the first-stage dense embedder to identify the overall document accurately ($70.0\%$ DocumentHit@1), but failed to prioritize the specific gold passage among competing intra-document paragraphs ($40.9\%$ of misses were same-document wrong-section distractors).

### Secondary Contributing Causes
1. **`FIRST_STAGE_ACQUISITION_FAILURE`** (under the section-anchored stress-test distribution):
   * First-stage dense retrieval dropped from $73.75\%$ Top-20 in TRAIN to $37.50\%$ in SELECT_VAL.
   * $10.0\%$ ($4/40$) of gold passages were ranked outside the entire candidate acquisition window of $500$ chunks ($>500$).
2. **`BENCHMARK_DISTRIBUTION_SHIFT`**:
   * Complete absence of numeric threshold or cutoff queries in SELECT_VAL ($0.0\%$) compared to TRAIN ($18.8\%$), eliminating an informative feature signal.

---

## 5. Hierarchical Depth Diagnostics

Hit rates evaluated across Document, Parent Section, and Passage levels confirm the invariant $PassageHit@K \le ParentSectionHit@K \le DocumentHit@K$ with zero violations:

| Depth ($K$) | Document Hit@K | Parent Section Hit@K | Passage Hit@K | Invariant Status |
| :---: | :---: | :---: | :---: | :---: |
| **@1** | 28 / 40 (**70.0%**) | 7 / 40 (**17.5%**) | 5 / 40 (**12.5%**) | **PASSED** |
| **@3** | 32 / 40 (**80.0%**) | 15 / 40 (**37.5%**) | — | — |
| **@5** | 33 / 40 (**82.5%**) | 16 / 40 (**40.0%**) | 8 / 40 (**20.0%**) | **PASSED** |
| **@10** | 35 / 40 (**87.5%**) | 24 / 40 (**60.0%**) | 11 / 40 (**27.5%**) | **PASSED** |
| **@20** | — | — | 15 / 40 (**37.5%**) | — |
| **@50** | — | — | 24 / 40 (**60.0%**) | — |
| **@100** | — | — | 26 / 40 (**65.0%**) | — |
| **@200** | — | — | 30 / 40 (**75.0%**) | — |
| **@500** | — | — | 36 / 40 (**90.0%**) | — |

* **Analysis**: Document identification remains robust ($70\%$ Hit@1, $87.5\%$ Hit@10), but discrimination degrades steeply at section ($17.5\%$ Hit@1) and passage levels ($12.5\%$ Hit@1, $37.5\%$ Hit@20).

---

## 6. HistGB Governance

During Phase 4 CV exploration on TRAIN $N=80$:
* Class C (`HistGradientBoostingClassifier`) achieved $93.75\%$ OOF Coverage@20 with $100\%$ naive preservation.
* Class C was **not** included in Phase 6 validation execution because Class A was predeclared and frozen as the sole primary candidate prior to unblinding validation data, owing to zero variance under small samples.
* Post-hoc model substitution is strictly prohibited under audit protocol.

```text
HISTGB_STATUS = NOT_ELIGIBLE_FOR_RETROSPECTIVE_EXECUTION
```

---

## 7. Final Governance Closure State

```text
V6_STATUS = RESEARCH_DIAGNOSTIC_NOT_PRODUCTION_PROMOTED
LORA_STATUS = BLOCKED
PRODUCTION_RUNTIME = QwenRenalRetrieverV3
RENAL_RUNTIME_VERSION = "v3"
DEV_B_STATUS = UNEXECUTED_FOR_PERFORMANCE
FINAL_HELDOUT_STATUS = UNEXECUTED_PRESERVED
FINAL_RECOMMENDATION = PRESERVE_V3_AND_MOVE_TO_PLAB
V7_STATUS = NOT_AUTHORIZED
```

The Renal retrieval campaign is closed. All development advances to the PLAB benchmark suite.
