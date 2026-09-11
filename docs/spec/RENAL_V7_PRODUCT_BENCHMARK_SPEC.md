# MedicalPlab Renal V7 — Product Retrieval Benchmark Specification

**Specification Version**: 1.0.0  
**Status**: FROZEN / MANDATORY GOVERNANCE  
**Target Domain**: Undergraduate Medical Education (Renal Medicine & Nephrology)  
**Corpus**: Frozen Renal Snapshot v2 (`Data/metadata/corpus_renal_snapshot_v2.json`, 23 accepted documents, 2,691 chunks)  

---

## 1. Background & Core First Principle

Historical analysis of Renal V6 established that its fresh validation benchmark (`SELECT_VAL`, $N=40$) collapsed not due to an engineering fault in the indexing infrastructure, but due to a fundamental **benchmark construction inconsistency**: queries were synthesized using template patterns referencing document headings and section titles (e.g., *"What clinical or physiological evidence regarding [section] is documented in [heading]?"*).

Under governance:
1. **The V6 $N=40$ benchmark is classified as an out-of-distribution (OOD) section-anchored stress test**. It is **NOT** the target product distribution.
2. The product retrieval system must be evaluated on queries that reflect **authentic undergraduate medical education and clinical reasoning**.
3. **No section-heading-template questions are permitted** in any V7 product benchmark.

---

## 2. Product Query Clinical Strata & Taxonomy

Every query in the Renal V7 product distribution must address a genuine clinical or educational proposition belonging to one of the following eight clinical strata:

1. **CLINICAL_PRESENTATION**: Symptoms, physical exam signs, characteristic clinical vignettes, patient presentation (e.g., macroscopic hematuria after upper respiratory infection, painless gross hematuria, triphasic Raynaud phenomenon, periorbital edema).
2. **PATHOPHYSIOLOGY_MECHANISM**: Molecular, cellular, and physiologic mechanisms (e.g., podocyte effacement, nephrin mutation, circulating anti-PLA2R antibodies, C3 nephritic factor activation of alternative pathway, endothelin-1 vasoconstriction).
3. **DIAGNOSIS_CLASSIFICATION**: Diagnostic criteria, histological classifications, biopsy findings (e.g., linear IgG immunofluorescence along GBM, "spike and dome" subepithelial deposits, crescent formation in $>50\%$ of glomeruli).
4. **INVESTIGATION_INTERPRETATION**: Laboratory studies, urinary microscopy, serologies, imaging (e.g., muddy brown granular casts, dysmorphic red cells, elevated serum free light chains, renal ultrasound echogenicity, fractional excretion of sodium $<1\%$).
5. **MANAGEMENT_INTERVENTION**: Acute and chronic clinical interventions, treatment sequencing (e.g., high-dose IV methylprednisolone pulse therapy, fluid resuscitation, urgent dialysis indications, blood pressure targets).
6. **RENAL_PHARMACOLOGY**: Drug mechanisms of action, nephrotoxicity, dose adjustments, pharmacokinetics (e.g., SGLT2 inhibitor renal hemodynamic effects, calcineurin inhibitor afferent arteriolar vasoconstriction, ACEi/ARB efferent vasodilation).
7. **THRESHOLDS_CUTOFFS**: Naturally occurring clinical and diagnostic thresholds (e.g., eGFR $< 15$ mL/min/1.73m$^2$ for Stage 5 CKD, urine protein-to-creatinine ratio $> 300$ mg/mmol for nephrotic-range proteinuria, serum potassium $> 6.5$ mmol/L).
8. **ANATOMICAL_TOPOGRAPHY**: Functional nephron segments, vascular supply, microanatomy (e.g., thick ascending limb NKCC2 cotransporter, macula densa tubuloglomerular feedback, juxtaglomerular apparatus).

---

## 3. Dataset Partitioning & Firewall Governance

To prevent data leakage, overfitting, and invalid evaluation, the V7 benchmark suite is strictly divided into three distinct partitions:

```text
+-------------------------------------------------------------------------------+
|                             RENAL CORPUS (23 Docs)                            |
+-------------------------------------------------------------------------------+
         |                                     |                         |
         v                                     v                         v
+------------------+                 +--------------------+    +------------------+
|    TRAIN_DEV     |                 | FROZEN_PRODUCT_TEST|    |   OOD_V6_STRESS  |
|   Optimization   |                 |    (Held-out >=100)|    |      (N=40)      |
| & Model Bake-off |                 |   Zero-Leakage     |    |   Diagnostic     |
+------------------+                 +--------------------+    +------------------+
```

### 3.1. TRAIN_DEV Partition
* **Purpose**: Used for query canonicalization rule development, multi-channel retrieval tuning, feature fusion parameter optimization, and model candidate bake-off.
* **Content**: Ground-truth clinical queries covering the 23 documents, verified against exact evidence spans.
* **Governance**: Must achieve pre-test engineering gates on this set before unblinding the frozen test set.

### 3.2. FROZEN_PRODUCT_TEST Partition
* **Purpose**: One-shot, definitive evaluation of the selected, frozen V7 retriever.
* **Target Size**: $\ge 100$ genuinely independent clinical queries mined across all 23 documents without duplication.
* **Strict Firewall**:
  * Zero overlap with `TRAIN_DEV` at the query, claim, or specific evidence proposition level.
  * No model parameters, selector weights, thresholds, or query canonicalizer vocabulary may be tuned or derived from this set.
  * Must remain completely unblinded until the architecture is frozen and SHA-recorded.

### 3.3. OOD_V6_STRESS Partition
* **Purpose**: Evaluate retriever resilience against section-anchored, low-entity-specificity stress queries.
* **Content**: The immutable V6 $N=40$ validation set (`evaluation/renal/v6/renal-selector-validation-v6-clean.json`).
* **Governance**: Executed strictly after product test evaluation to document robustness delta without altering model weights.

---

## 4. Query Authoring & Quality Invariants

Every query included in V7 must satisfy the following invariants:

1. **Answerability**: The exact gold chunk must contain the direct proposition required to answer the query completely.
2. **Entity Density**: Queries must contain specific clinical, biological, pharmacological, or physiological entities rather than abstract meta-language.
3. **No Template Framing**: Queries such as *"What is discussed in section X?"* or *"What clinical findings are documented in section Y?"* are strictly prohibited.
4. **Verbatim Evidence Grounding**: The cited gold evidence span must be a verbatim substring of the target chunk text.
5. **Zero Neighbor Dependency**: The target chunk must stand alone as sufficient evidence without requiring adjacent text blocks.
