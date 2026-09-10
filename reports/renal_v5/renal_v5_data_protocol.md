# MedicalPlab Renal V5 — Predeclared Data Protocol

**Version:** V5-DATA-PROTOCOL-FROZEN  
**Date Declared:** 2026-09-11  
**Status:** PREDECLARED AND FROZEN — must not be modified after first commit  
**Governs:** All V5 ranking splits, verifier splits, safety splits, and final heldout

> [!IMPORTANT]
> This document is frozen at the point of first commit. No split composition,
> quota, label, or DEV-B axis may be changed after this point. DEV-B
> distributions are declared here before any DEV-A data is generated or evaluated.

---

## 1. Corpus Scope

**Corpus:** Frozen 23-document Renal corpus  
**Chunking:** `B_400_overlap` (2,691 chunks, 629 sections)  
**Registry:** `Data/metadata/renal_source_registry_v2.json`  
**Expansion policy:** No new documents unless an independent a-priori undergraduate curriculum audit (not driven by evaluation failures) identifies a genuine missing educational area. No such audit was performed before V5. Corpus is fixed.

---

## 2. Curriculum Strata

All V5 queries must be tagged with a curriculum stratum from this predeclared list:

| Stratum ID | Label | Primary Documents |
|---|---|---|
| STR-01 | Glomerular structure & filtration | 0002, 0016, 0018 |
| STR-02 | Tubular reabsorption & secretion | 0003, 0004, 0005, 0019, 0020, 0021 |
| STR-03 | Urine concentration & dilution | 0023 |
| STR-04 | RAAS & renal endocrine | 0001, 0024 |
| STR-05 | Electrolyte disorders | 0003, 0009, 0010, 0020 |
| STR-06 | Acid-base physiology | 0004, 0005, 0021 |
| STR-07 | Acute kidney injury | 0006, 0015, 0016 |
| STR-08 | Chronic kidney disease | 0007 |
| STR-09 | Glomerular disease & nephrotic syndrome | 0008, 0018 |
| STR-10 | Urinary tract infection | 0011, 0013 |
| STR-11 | Nephrolithiasis & obstruction | 0012, 0013, 0014 |
| STR-12 | Haematuria & urological investigation | 0025 |

A query may span two strata if the learning objective is genuinely multi-topic. Primary stratum assignment is required.

**Stratum distribution target for RERANK_DEV_A and RERANK_DEV_B:** At least 2 queries per stratum (where corpus permits evidence), no stratum > 35% of total.

---

## 3. Query Generation Rules

### 3.1 Answerability Classification
Every query is pre-classified as:
- **ANSWERABLE:** The corpus contains a passage that directly and sufficiently answers the query.
- **UNANSWERABLE_COVERAGE_GAP:** The query is a plausible renal query but the corpus lacks direct evidence.
- **UNANSWERABLE_OOD:** The query is outside the scope of the 23 renal documents.

For retrieval splits (RERANK_*), only ANSWERABLE queries are included.  
For safety splits (SAFETY_*, VERIFIER_*), all answerability types are included.

### 3.2 Query Style Families (predeclared)

| Style ID | Description | Example form |
|---|---|---|
| QS-A | Mechanism WH-question | "What is the mechanism by which...?" |
| QS-B | Clinical management question | "How is [condition] managed in...?" |
| QS-C | Comparative question | "What distinguishes X from Y in...?" |
| QS-D | Threshold / quantitative question | "What GFR threshold defines...?" |
| QS-E | Enumeration question | "What are the main causes of...?" |
| QS-F | Consequence / outcome question | "What happens to [parameter] when...?" |
| QS-G | Conditional / contextual question | "In the setting of [condition], how does...?" |

**DEV-A quota:** Mix of QS-A through QS-G. No single style > 40%.  
**DEV-B quota:** See Section 10 (predeclared robustness axis).

### 3.3 Transformation Families (for negatives and safety)

| Transform ID | Description |
|---|---|
| TF-01 | Wrong entity (wrong drug, ion, transporter) |
| TF-02 | Wrong nephron segment |
| TF-03 | Wrong direction of effect (increase ↔ decrease) |
| TF-04 | Causal inversion |
| TF-05 | Numeric threshold perturbation (adjacent plausible value) |
| TF-06 | Indication inversion |
| TF-07 | Temporal mismatch (acute vs chronic context) |
| TF-08 | Severity mismatch (mild vs severe) |
| TF-09 | Conditional → universal overclaim |
| TF-10 | Correlation → causation overclaim |
| TF-11 | Same-topic non-answer (on-topic passage, wrong specific claim) |
| TF-12 | Partial support (only one of two required components answered) |
| TF-13 | Guideline overclaim |
| TF-14 | Contraindication inversion |

---

## 4. Evidence-Span Rules

For every ANSWERABLE query:

```
QUERY → LEARNING_OBJECTIVE → CANONICAL_CLAIM
  → SOURCE_DOCUMENT_ID
  → PRIMARY_EVIDENCE_SPAN (verbatim or near-verbatim text from corpus)
  → PARENT_SECTION_PATH (list of section headings)
  → RELEVANT_CHUNK_IDS (derived from evidence-span overlap with B_400 chunks)
```

### Gold chunk derivation rule
A chunk is relevant if **any part of the primary evidence span overlaps with that chunk's text** under a normalized character-overlap criterion (minimum 50-character matching overlap, or full sentence containment).

Multiple relevant chunks are allowed when the same claim is directly supported across overlapping windows. All such chunks are listed in `gold_chunk_ids`.

**A passage that contains background context but not the specific claim answering the query is NOT a relevant passage.**

If automated adjudication of chunk relevance is uncertain (overlap exists but claim entailment is ambiguous): label `HUMAN_REVIEW_REQUIRED`. Exclude from gold metrics and training. Do NOT label as automated review.

### Multi-relevance protection
No chunk that is labeled relevant for query A may be used as a hard negative for query A. This applies even if the chunk is irrelevant for a different query B.

---

## 5. Qrel / Label Schema

### Retrieval split labels
Each item in RERANK_TRAIN, RERANK_DEV_A, RERANK_DEV_B carries:

```json
{
  "query_id": "V5-RNK-TRAIN-0001",
  "query": "...",
  "curriculum_stratum": "STR-02",
  "query_style": "QS-A",
  "learning_objective": "...",
  "canonical_claim": "...",
  "source_document_id": "DOC-PMC-RENAL-XXXX",
  "primary_evidence_span": "...",
  "parent_section_path": ["...", "..."],
  "gold_chunk_ids": ["DOC-...-XXXX#chunk_N", ...],
  "gold_doc_id": "DOC-PMC-RENAL-XXXX",
  "gold_section_path": ["...", "..."],
  "review_status": "AUTO_VERIFIED | HUMAN_REVIEW_REQUIRED",
  "verification_method": "SOURCE_GROUNDED_SPAN_OVERLAP",
  "query_family": "QF-XXX",
  "split_group_key": "DOC_SEC_FAMILY_KEY"
}
```

### Verifier split labels
Each item in VERIFIER_TRAIN, VERIFIER_DEV_A, VERIFIER_DEV_B carries:

```json
{
  "item_id": "V5-VRF-TRAIN-0001",
  "query": "...",
  "candidate_passage": "...",
  "source_document_id": "...",
  "source_chunk_id": "...",
  "parent_section_path": ["..."],
  "label": "DIRECT_SUPPORT | PARTIAL_SUPPORT | DOES_NOT_ANSWER",
  "transformation_family": "TF-XX | NONE",
  "label_rationale": "...",
  "verification_method": "SOURCE_GROUNDED_SPAN_OVERLAP | MANUAL_ANNOTATION",
  "canonical_claim_for_annotation": "...",
  "confidence": "HIGH | MEDIUM | UNCERTAIN",
  "review_status": "AUTO_VERIFIED | HUMAN_REVIEW_REQUIRED"
}
```

**Runtime note:** `canonical_claim_for_annotation` is ONLY for annotation/evaluation. It is not available at inference time. The verifier must operate on `(query, candidate_passage)` only.

### Safety split labels

```json
{
  "item_id": "V5-SAF-TRAIN-0001",
  "query": "...",
  "curriculum_stratum": "STR-XX",
  "query_style": "QS-X",
  "label": "SUPPORTED | PARTIALLY_SUPPORTED | IN_DOMAIN_CORPUS_COVERAGE_GAP | OUT_OF_DOMAIN_UNSUPPORTED | DIFFICULT_PERTURBATION_NEGATIVE",
  "operational_class": "POSITIVE | NEGATIVE",
  "transformation_family": "TF-XX | NONE",
  "source_document_id": "...",
  "evidence_span": "...",
  "label_rationale": "...",
  "verification_method": "SOURCE_GROUNDED",
  "review_status": "AUTO_VERIFIED | HUMAN_REVIEW_REQUIRED"
}
```

### Operational binary mapping (fail-closed, predeclared)

| Label | Operational Class | Product Action |
|---|---|---|
| `SUPPORTED` | POSITIVE (1) | Eligible for GROUNDED |
| `PARTIALLY_SUPPORTED` | **NEGATIVE (0)** | INSUFFICIENT_EVIDENCE |
| `IN_DOMAIN_CORPUS_COVERAGE_GAP` | NEGATIVE (0) | INSUFFICIENT_EVIDENCE |
| `OUT_OF_DOMAIN_UNSUPPORTED` | NEGATIVE (0) | INSUFFICIENT_EVIDENCE |
| `DIFFICULT_PERTURBATION_NEGATIVE` | NEGATIVE (0) | INSUFFICIENT_EVIDENCE |

**PARTIALLY_SUPPORTED is fail-closed.** It is an operational negative even though it represents a plausible medical claim. This policy is predeclared and immutable for V5.

---

## 6. Split Firewall

### Isolation keys
Two items are in the same "family" (cannot be split across TRAIN and DEV) if they share:
1. Exact query string (case-folded)
2. Normalized query (remove punctuation, casefold, sort tokens)
3. Primary evidence span (≥80% character overlap)
4. `(source_document_id, parent_section_path)` pair
5. `(learning_objective, query_family_tag)` pair
6. Transformation family applied to the same base claim

### Near-duplicate detection
Within each split: cosine similarity ≥ 0.92 between Qwen3-Embedding-0.6B embeddings of query strings flags as potential near-duplicates for manual review.

Between TRAIN and DEV-A: same threshold applied.  
Between TRAIN and DEV-B: same threshold applied.  
Between DEV-A and DEV-B: items CAN overlap in topic but must differ in section-family to ensure meaningful robustness variation.

### Source-section exclusivity (TRAIN vs DEV)
If a specific `(document_id, section_path[0:2])` pair appears in RERANK_DEV_A, no RERANK_TRAIN item may share the same primary section. This prevents the model from memorizing section representations.

**Note:** Because the corpus has only 23 documents and 629 sections, complete source-section separation across all splits is not achievable. Where source-document overlap is unavoidable, it must be explicitly reported in the split audit, and section-level separation must still hold.

---

## 7. Split Sizes and Quotas

### Ranking Splits

| Split | Size | Purpose |
|---|---|---|
| `RERANK_TRAIN_V5` | ≥ 80 ANSWERABLE queries | Reranker hard-negative training |
| `RERANK_DEV_A_V5` | ≥ 50 ANSWERABLE queries | Retrieval architecture selection, diagnostic |
| `RERANK_DEV_B_V5` | ≥ 40 ANSWERABLE queries | One-time robustness confirmation |

All DEV-A and DEV-B queries/qrels must be generated and SHA-frozen **BEFORE** any reranker training begins.

**Note on reuse of V3/V4 train data:** Prior V3 train (60 items) and V4 retrieval DEV (70 items) may be incorporated as RERANK_TRAIN material ONLY IF:
- Each item passes the split firewall (no section-family overlap with V5 DEV-A or DEV-B)
- Items are explicitly labeled `source: reused_v3_train` or `source: reused_v4_dev_as_train`
- The split audit documents which items were reused

**Reuse of any spent DEV or heldout as V5 DEV or heldout is strictly prohibited.**

### Verifier Splits

| Split | Size | Purpose |
|---|---|---|
| `VERIFIER_TRAIN_V5` | ≥ 150 items | Verifier training (if fine-tuning triggered) |
| `VERIFIER_DEV_A_V5` | ≥ 60 items | Verifier architecture selection |
| `VERIFIER_DEV_B_V5` | ≥ 40 items | One-time verifier confirmation |

Negative quota within each verifier split: ≥ 30% PARTIAL_SUPPORT, ≥ 20% DOES_NOT_ANSWER. Transformation families must be spread across TF-01 through TF-14.

### Safety Splits

| Split | Size | Purpose |
|---|---|---|
| `SAFETY_TRAIN_V5` | ≥ 100 items | Safety model training |
| `SAFETY_DEV_A_V5` | ≥ 80 items | Safety architecture selection |
| `SAFETY_DEV_B_V5` | ≥ 60 items | One-time safety confirmation |
| `SAFETY_CALIBRATION_V5` | ≥ 60 items | Threshold selection ONLY |
| `SAFETY_TEST_V5` | TBD (see §8) | Single-execution safety gate |

SAFETY_TEST_V5 is built LAST, after all model freezes. Not predeclared here — only sizing rationale (§8).

---

## 8. Safety Test Statistical Sizing (to be computed in Phase 27)

**Operational constraint:** Observed Unsafe Accept ≤ 5%

**Stronger statistical statement (CI):** One-sided 95% Clopper-Pearson upper bound ≤ 5%

Reference sizing (to be recomputed exactly in Phase 27 via code):
- k=0 failures: need ≈ 59 operational negatives for one-sided 95% UB ≤ 5%
- k=1 failure: need ≈ 93 negatives
- k=2 failures: need ≈ 127 negatives

**V5 target:** Size for k=0 constraint (≈ 59 negative operational slots minimum), with additional margin for stratum coverage. Negative strata:
- In-domain corpus coverage gap
- Out-of-domain unsupported
- Difficult same-topic perturbation (semantic hard negatives, TF-01 through TF-14)
- Partial support (fail-closed)
- Contradiction / proposition error (where applicable)

Per-stratum N must be large enough to report stratum-level rates. **Do NOT claim ≤5% population unsafe accept for an individual stratum unless that stratum is individually sized (≥59 negatives) to support that claim.**

The difficult-semantic-negative stratum must be ≥ 15 items.

---

## 9. DEV-A Purpose

`RERANK_DEV_A_V5` purpose:
- Fresh V3 baseline measurement (Phase 5)
- Gold-rank movement diagnostic (Phase 6)
- Depth diagnostic (Phase 7)
- Reranker architecture selection (Phase 13)
- **NOT** for DEV-B or final heldout decisions

`VERIFIER_DEV_A_V5` purpose:
- Off-the-shelf verifier baseline comparison (Phase 20)
- Verifier fine-tuning selection if triggered (Phase 21)
- **NOT** for threshold selection or DEV-B

`SAFETY_DEV_A_V5` purpose:
- Safety architecture comparison A/B/C/D (Phase 24)
- **NOT** for threshold selection or DEV-B

---

## 10. DEV-B Robustness Axes (Predeclared — Fixed Before DEV-A Evaluation)

### RERANK_DEV_B_V5 — Predeclared Robustness Axis
**Axis:** Concise factual / enumeration style questions (QS-D, QS-E, QS-F dominant) with independently generated phrasing, covering curriculum strata with different primary source-section families than DEV-A.

This tests whether reranker improvements generalize across question formulation style, not just topic. DEV-B is not adversarial — it represents a real undergraduate learning interaction style.

**DEV-B must NOT be:**
- Deliberately made adversarial or out-of-distribution relative to the product
- Chosen based on DEV-A failure patterns
- A copy of DEV-A with minor paraphrasing

### VERIFIER_DEV_B_V5 — Predeclared Robustness Axis
**Axis:** Higher proportion of PARTIAL_SUPPORT items (≥40%) and a broader transformation family mix (each of TF-01 through TF-10 represented at least once), independently generated from different source sections than VERIFIER_DEV_A.

### SAFETY_DEV_B_V5 — Predeclared Robustness Axis
**Axis:** Elevated difficult-perturbation-negative stratum (≥40% of negatives), representing subtle semantic confusions (TF-01 through TF-07 dominant), independently generated from different source sections than SAFETY_DEV_A.

---

## 11. Paired Retrieval Evaluation Method

For each DEV/heldout query, evaluate:
- **System A:** Frozen QwenRenalRetrieverV3 (production baseline)
- **System B:** V5 candidate system (if applicable)

Both evaluated on the SAME query set, in a single logical run with checkpoint/resume.

**Metrics:**
- DocumentHit@1/3/5/10
- ParentSectionHit@1/3/5/10
- PassageHit@1/3/5/10
- CandidateCoverage@20/30/50 (diagnostic)
- RerankerInputHit@20 (authoritative production metric)
- MRR
- nDCG@10
- Wins/Losses/Ties (query-level paired)
- McNemar exact p-value

**Practical effect predeclaration (for DEV-A ranking candidate selection):**
A candidate SHOULD show ≥ +4 PassageHit@1 queries improvement over V3 on DEV-A (≥8% on N=50 scale) with no material Hit@5 regression (defined as ≥ -3 queries). This is a practical threshold, not a statistical test. Paired confidence intervals are reported for context.

**McNemar for FINAL_V5_HELDOUT:**
Uses paired discordant pairs. Expected discordant pair rate estimated from DEV-B prior to construction. The heldout is sized for adequate power.

---

## 12. FINAL_V5_HELDOUT Sampling Protocol (to be finalized in Phase 32)

Predeclared composition:
- ANSWERABLE subset: ≥ 60 queries (for V3 vs V5 paired retrieval comparison)
- UNSUPPORTED / OOD subset: ≥ 30 queries (for safety evaluation)
- Balanced across curriculum strata (≥ 2 per stratum)
- Unspent claim families — must not overlap with any prior TRAIN, DEV, or calibration set

**Query protocol:** Same generation rules as retrieval splits. Section-family exclusivity from all prior spent sets must hold.

**Paired evaluation:** V3 and V5 candidate evaluated on the SAME heldout in a single locked run with checkpoint/resume.

---

## 13. Query Family Key Scheme

Each query is assigned a `query_family_id` from the pattern:
```
QF-{STRATUM_ID}-{DOC_ID}-{SEC_HASH_4HEX}
```
Where `SEC_HASH_4HEX` is the first 4 hex characters of SHA-256 of the `parent_section_path` joined string.

Two queries with the same `query_family_id` are in the same family and must be in the same split.

---

## 14. Hard Negative Protocol for Reranker Training

### Positive set
All chunks in `gold_chunk_ids` for a training query.

### Hard-negative candidate source
1. **Stage 1:** Top-20 candidates from frozen V3 retrieval on that query (actual runtime candidates)
2. **From stage 1:** Exclude all `gold_chunk_ids` — these are NOT hard negatives
3. **Remaining candidates:** Subject to source-grounded verification to confirm they do NOT directly answer the query
4. **Classification:**
   - Same document, different section → hard negative type `SAME_DOC_DIFF_SECTION`
   - Different document, same topic → hard negative type `SAME_TOPIC_DIFF_DOC`
   - Partially relevant (background but not answer) → hard negative type `PARTIAL_CONTEXT`
   - High-scoring semantic confuser → hard negative type `SEMANTIC_CONFUSER`

### Exclusion rule
Any chunk that MIGHT be relevant (ambiguous adjudication) is excluded from the hard-negative pool. `HUMAN_REVIEW_REQUIRED` items are excluded from training until resolved.

### Persisted provenance per hard negative
```json
{
  "query_id": "V5-RNK-TRAIN-0001",
  "negative_chunk_id": "DOC-...-XXXX#chunk_N",
  "negative_type": "SAME_DOC_DIFF_SECTION",
  "candidate_source": "V3_RETRIEVAL_TOP20",
  "verification_method": "SOURCE_GROUNDED_EXCLUSION",
  "rationale": "Chunk discusses [X], not [Y] as required by the query",
  "pre_reranker_rank": 3,
  "pre_reranker_score": 0.812
}
```

**Retrieval scores are diagnostics only. Source-grounded verification determines the label.**

---

## 15. File Naming and Location Conventions

```
evaluation/renal/v5/
  renal-rerank-train-v5.json          RERANK_TRAIN_V5
  renal-rerank-dev-a-v5.json          RERANK_DEV_A_V5
  renal-rerank-dev-b-v5.json          RERANK_DEV_B_V5
  renal-verifier-train-v5.json        VERIFIER_TRAIN_V5
  renal-verifier-dev-a-v5.json        VERIFIER_DEV_A_V5
  renal-verifier-dev-b-v5.json        VERIFIER_DEV_B_V5
  renal-safety-train-v5.json          SAFETY_TRAIN_V5
  renal-safety-dev-a-v5.json          SAFETY_DEV_A_V5
  renal-safety-dev-b-v5.json          SAFETY_DEV_B_V5
  renal-safety-calibration-v5.json    SAFETY_CALIBRATION_V5
  renal-safety-test-v5.json           SAFETY_TEST_V5 (built last)
  renal-heldout-v5-final.json         FINAL_V5_HELDOUT (built last)
  [all files get .sha256 sidecars]

reports/renal_v5/
  renal_v5_recovery_audit.md
  renal_v5_split_audit.json           leakage audit
  renal_v5_hard_negative_provenance.json
  renal_v5_baseline_dev_a.json        Phase 5 fresh V3 baseline
  renal_v5_gold_rank_diagnostic.json  Phase 6
  renal_v5_depth_diagnostic.json      Phase 7
  renal_v5_reranker_dev_a.json        Phase 13
  renal_v5_reranker_dev_b.json        Phase 14 (one-time)
  renal_v5_verifier_baseline.json     Phase 20
  renal_v5_verifier_dev_b.json        Phase 22 (one-time)
  renal_v5_safety_dev_a.json          Phase 24
  renal_v5_safety_dev_b.json          Phase 25 (one-time)
  renal_v5_safety_test_results.json   Phase 29 (one-time)
  renal_v5_paired_final_heldout.json  Phase 34 (one-time)
  renal_v5_sizing_rationale.json      Phase 27

Data/experiments/renal_v5/
  cache/                              V5 embedding caches
  reranker_adapters/                  LoRA/adapter weights
  verifier_models/                    verifier checkpoints

models/
  renal_v5_reranker_adapter.{safetensors|pkl}  (+ .sha256)
  renal_v5_verifier_classifier.pkl             (+ .sha256)

configs/
  renal_v5_retrieval_config.json    (+ .sha256)
  renal_v5_safety_config.json       (+ .sha256)
  renal_v5_verifier_config.json     (+ .sha256)

docs/demo/
  RENAL_TECHNICAL_RESULTS_V5.md
```

---

## 16. Single-Run Guards

| Guard | Rule |
|---|---|
| RERANK_DEV_B | Run once after DEV-A candidate frozen. No retune after. |
| VERIFIER_DEV_B | Run once after verifier candidate frozen. No retune after. |
| SAFETY_DEV_B | Run once after safety architecture frozen. No retune after. |
| SAFETY_TEST_V5 | Run once after FULL SYSTEM FROZEN. No retune, relabeling, or regeneration. |
| FINAL_V5_HELDOUT | Run once after FULL SYSTEM FROZEN. No retune after. |

---

*Protocol version: V5-DATA-PROTOCOL-V1*  
*This file must not be modified after the commit that introduces it.*  
*Protocol SHA will be recorded in the split audit.*
