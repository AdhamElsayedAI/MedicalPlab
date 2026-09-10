# MedicalPlab Renal V5 — Forensic Audit Report

**Audit Date:** 2026-09-11  
**Mission:** RENAL V5 — Hard-Negative Evidence Ranking & Semantic Claim Verification  
**Starting Commit:** `73bb51b0347aec5c3a31668d12adc4f7d7b27966`  
**Branch:** `ai-data-execution-v1`  
**Auditor:** Phase 1 automated forensic inspection

---

## 1. Pre-Flight Git State

| Field | Value |
|---|---|
| Branch | `ai-data-execution-v1` |
| Local HEAD | `73bb51b0347aec5c3a31668d12adc4f7d7b27966` |
| Remote HEAD | `73bb51b0347aec5c3a31668d12adc4f7d7b27966` |
| `git diff` | **Clean (empty)** |
| `git diff --check` | **Exit 0** |
| Working tree | **Clean** |

---

## 2. Historical Firewall Verification

All frozen historical artifacts verified byte-for-byte intact:

| Artifact | SHA-256 | Status |
|---|---|---|
| `evaluation/renal/renal-heldout-v2-final.json` | `8885b21bc1174ea6...` | ✅ OK |
| `evaluation/renal/v3/renal-heldout-v3-final.json` | `40c96f46be1c6547...` | ✅ OK |
| `evaluation/renal/v3/renal-v3-safety-test-2.json` | `3fe59bb6011c5ab4...` | ✅ OK |
| `evaluation/renal/v4/renal-safety-test-v4.json` | `7d2069b5a1216f09...` | ✅ OK |
| `evaluation/renal/v4/renal-heldout-v4-final.json` | `0368761712c91b06...` | ✅ OK |
| `models/renal_v4_evidence_classifier.pkl` | `54f42677b4776354...` | ✅ OK |
| `reports/renal_v4/renal_v4_safety_test_results.json` | `e1c58c5c1c759f0d...` | ✅ OK |

**Firewall status: ALL HISTORICAL ARTIFACTS INTACT**

---

## 3. Corpus Inventory

**Chunking strategy in production use:** `B_400_overlap` (target ~400 tokens, overlapping windows)

| Metric | Value |
|---|---|
| Active documents | 23 (all `status=accepted` in `renal_source_registry_v2.json`) |
| Total chunks (B_400_overlap) | 2,691 |
| Min chunks/doc | 21 |
| Max chunks/doc | 357 |
| Mean chunks/doc | 117.0 |
| Section count (V4 metadata) | 629 |
| Chunk-to-section mapping | 2,691 entries |

### Document Topic Coverage (23 docs)

| Document ID | Topic Tags |
|---|---|
| DOC-PMC-RENAL-0001 | RAAS, aldosterone, renal endocrine function |
| DOC-PMC-RENAL-0002 | glomerulus, filtration barrier, GFR |
| DOC-PMC-RENAL-0003 | potassium handling, tubular transport, hyperkalaemia |
| DOC-PMC-RENAL-0004 | proximal tubule, tubular reabsorption, acid-base |
| DOC-PMC-RENAL-0005 | acid-base physiology, tubular secretion, functional nephron units |
| DOC-PMC-RENAL-0006 | AKI, diagnosis, management principles |
| DOC-PMC-RENAL-0007 | CKD, evaluation, management principles |
| DOC-PMC-RENAL-0008 | nephrotic syndrome, glomerular disease, proteinuria |
| DOC-PMC-RENAL-0009 | hyperkalaemia, electrolyte disturbance, potassium |
| DOC-PMC-RENAL-0010 | hyperkalaemia, kidney disease, management |
| DOC-PMC-RENAL-0011 | UTI, recurrent UTI, urinary tract |
| DOC-PMC-RENAL-0012 | nephrolithiasis, renal colic, urinary obstruction |
| DOC-PMC-RENAL-0013 | kidney stones, recurrent UTI, infected obstruction |
| DOC-PMC-RENAL-0014 | hydronephrosis, urinary obstruction, grading |
| DOC-PMC-RENAL-0015 | renal replacement therapy, dialysis basics, AKI |
| DOC-PMC-RENAL-0016 | GFR, creatinine clearance, AKI assessment |
| DOC-PMC-RENAL-0018 | glomerular filtration barrier, glomerulus |
| DOC-PMC-RENAL-0019 | glucose handling, proximal tubule, SGLT |
| DOC-PMC-RENAL-0020 | tubular transport, sodium handling, potassium handling |
| DOC-PMC-RENAL-0021 | acid-base physiology, bicarbonate transport, renal sensing |
| DOC-PMC-RENAL-0023 | urine concentration, countercurrent mechanism, renal medulla |
| DOC-PMC-RENAL-0024 | renal endocrine, erythropoietin, calcitriol, vitamin D |
| DOC-PMC-RENAL-0025 | haematuria, differential diagnosis, glomerular vs non-glomerular |

**Corpus gap note:** No document with ID `-0017` or `-0022` — these were not ingested (presumably not available under required license). This is not a V5 concern unless a curriculum audit independently identifies missing educational areas.

---

## 4. Embedding and Cache Assets

### V3 Production Caches (used by QwenRenalRetrieverV3)

| File | Purpose | SHA-256 |
|---|---|---|
| `renal_v3/cache/all23_corpus_embeddings.npy` | Passage embeddings (2,691 × dim) | `3d48cea24334b82d...` |
| `renal_v3/cache/all23_doc_embeddings.npy` | Document embeddings (23 × dim) | `7ba614b166056c9d...` |
| `renal_v3/cache/b400_contextual_193cdd7389ca1445.npy` | Contextual variant cache | `2cf279402ae8ed64...` |
| `renal_v3/cache/f180_content_955d4177bf22ad09.npy` | F180-content variant cache | `77fd0af774344...` |

### V4 Additional Caches

| File | Purpose | SHA-256 |
|---|---|---|
| `renal_v4/cache/all629_section_centroid_embeddings.npy` | Section centroid embeddings | (from sections_metadata SHA) |
| `renal_v4/cache/all629_section_structural_embeddings.npy` | Section structural embeddings | (from sections_metadata SHA) |
| `renal_v4/cache/sections_metadata.json` | Chunk-to-section mapping | centroid+structural SHAs embedded |

---

## 5. Runtime Flow — Exact Production Path (Source-Verified)

### Entry Point: `CourseLearningService.query(request)`

```
CourseQueryRequest(course_id, query, intent)
    → course_id normalised → "urinary_renal" branch
    → urinary_available check (V2 registry + B_400_overlap chunks)
    → _query_renal(query, intent, trace_id)
        → empty query → UNSUPPORTED immediately
        → RenalRetriever.retrieve(query, top_k=5)
            [currently: QwenRenalRetrieverV3 (production default)]
        → no hits → UNSUPPORTED
        → hits[0] = top hit
        → citations built from hits[:3]
        → safety decision:
            if hit.is_grounded is not None:   ← V4 path (classifier active)
                is_sufficient = hit.is_grounded
                evidence_score = hit.evidence_sufficiency_score
            else:                              ← V3 path (raw score)
                is_sufficient = score >= RENAL_SUFFICIENCY_THRESHOLD (0.8199)
                evidence_score = score
        → NOT sufficient → INSUFFICIENT_EVIDENCE, answer=None
        → sufficient → GROUNDED, answer=hits[0].chunk["text"]
```

### QwenRenalRetrieverV3.retrieve(query, top_k=5) — Verified Exact Code Path

```
1. Encode query: Qwen3-Embedding-0.6B, instruction-prefixed, normalized
2. p_scores = corpus_embeddings @ query_emb          [2691 scores]
3. d_scores = doc_embeddings @ query_emb              [23 scores]
4. combined_scores[i] = p_scores[i] + 0.18 * d_scores[doc_id_to_idx[chunk[i].doc]]
5. cand_indices = top-20 by combined_scores           [candidate_depth=20]
6. pairs = [[query, chunk.text] for chunk in candidates]
7. r_scores = CrossEncoder(Qwen3-Reranker-0.6B).predict(pairs, batch_size=8)
8. rerank_order = r_scores.argsort()[::-1][:top_k]   [top_k=5]
9. return RenalRetrievalHit(chunk, r_score)            [is_grounded=None → V3]
```

**Safety decision in V3 path:** Raw reranker score vs `RENAL_SUFFICIENCY_THRESHOLD = 0.8199`. No classifier. No `is_grounded` flag.

### QwenRenalRetrieverV4.retrieve(query, top_k=5) — Research/Historical Only

Same as V3 PLUS:
- Stage 1 adds section structural channel: `+ 0.12 * s_scores[chunk_to_section[i]]`
- Stage 3: Evidence-sufficiency classifier (LogisticRegression, 10 features, τ=0.6886)
- `is_grounded` and `evidence_sufficiency_score` set on top hit

---

## 6. Spent Evaluation Inventory

### V1/V2 Evaluation Sets (Spent)
| Set | N | Status |
|---|---|---|
| `renal-dev-v1.json` | 48 | SPENT — V1 architecture selection |
| `renal-heldout-v1.json` | 56 | SPENT — V1 final heldout |
| `renal-dev-v2.json` | 88 | SPENT — V2 architecture selection |
| `renal-calibration-v1.json` | 40 | SPENT |
| `renal-calibration-v2.json` | 66 | SPENT |
| `renal-heldout-v2-final.json` | 100 | SPENT — V2 final heldout (FROZEN) |
| `renal-safety-test-v2.json` | 66 | SPENT — V2 safety test |
| `renal-dev-evidence-spans-v2.json` | 88 | SPENT — V2 evidence span development |

### V3 Evaluation Sets (Spent)
| Set | N | Status |
|---|---|---|
| `renal-train-v3.json` | 60 | SPENT — V3 safety train |
| `renal-dev-v3-qrels.json` | 69 | SPENT — V3 retrieval DEV |
| `renal-v3-safety-train.json` | 90 | SPENT — V3 safety train |
| `renal-v3-safety-calibration.json` | 60 | SPENT — V3 safety calibration |
| `renal-v3-safety-test-2.json` | 70 | SPENT / FROZEN — V3.1 safety test |
| `renal-heldout-v3-final.json` | 100 | SPENT / FROZEN — V3 final heldout |

### V4 Evaluation Sets (Spent)
| Set | N | Status |
|---|---|---|
| `renal-retrieval-dev-v4.json` | 70 | SPENT — V4 retrieval DEV |
| `renal-safety-train-v4.json` | 100 | SPENT — V4 safety train |
| `renal-safety-dev-v4.json` | 60 | SPENT — V4 safety DEV |
| `renal-safety-calibration-v4.json` | 60 | SPENT — V4 calibration |
| `renal-safety-test-v4.json` | 120 | SPENT / FROZEN — V4 safety test |
| `renal-heldout-v4-final.json` | 100 | SPENT / FROZEN — V4 final heldout |

**Total spent across all versions:** approximately 1,173 query/item slots. However many slots represent safety/verifier items (negative examples, partial support) rather than retrieval-grounded queries, and the renal corpus contains 2,691 chunks from 23 documents — meaning a large fraction of evidence space remains unexploited for fresh V5 development.

---

## 7. V4 Classifier Bundle Inspection

| Field | Value |
|---|---|
| Bundle keys | `model_version`, `model`, `scaler`, `feature_indices`, `feature_names`, `calibrated_threshold`, `winning_architecture`, `frozen_retrieval_config`, `calibrated_at`, `calibration_metrics` |
| Model type | `LogisticRegression` |
| Scaler type | `StandardScaler` |
| Calibrated τ | `0.6885976627712855` |
| Feature indices used | `[0, 1, 2, 3, 4, 5, 6, 7, 10, 11]` (10 features) |
| Feature names | `r_top1, r_top2, r_margin, r_top3_mean, dense_top1, dense_margin, doc_top1, doc_margin, doc_agreement, entropy` |
| Architecture | `MODEL_A_RETRIEVAL_10_FEATS` (pure retrieval-confidence features) |
| Operational denominator | 70 negatives (50 SUPPORTED positives; PARTIALLY_SUPPORTED treated as negative) |
| Empirical unsafe accept | 0/70 on SAFETY_TEST_V4 (CI UB: 4.19%) |

**V4.1 Audit Finding confirmed:** Classifier uses ONLY retrieval-confidence features. No semantic verifier. Cross-dataset failure on FINAL_V4_HELDOUT (80% unsafe accept among the 50 heldout negatives) confirms distributional fragility. This motivates the V5 semantic verifier workstream.

---

## 8. Identified Issues and V5 Research Hypotheses

### Issue 1: Ranking Failure Mode (requires fresh V5 data to confirm)
- Historical FINAL_V4_HELDOUT: V3 PassageHit@1 = 62%, V4 = 58% (non-significant).
- 38% of queries fail at PassageHit@1 under V3.
- **Hypothesis to test on fresh V5 DEV-A:** Are most remaining failures due to (a) relevant passage not in Top-20 candidate set (candidate retrieval miss), or (b) relevant passage in Top-20 but reranked below non-supporting passage (reranking failure)?
- **Gates before reranker training:** Confirm a substantial RERANKING_FAILURE population on fresh V5 DEV-A.

### Issue 2: Safety / Semantic Sufficiency Failure
- V4 classifier used retrieval-confidence features → failed on FINAL_V4_HELDOUT (80% unsafe accept).
- **Hypothesis:** A question → passage **direct-support** verifier will be more stable than retrieval-confidence features.
- **Task framing (from runtime code):** Extractive path: `question + candidate passage → DIRECT_SUPPORT / PARTIAL_SUPPORT / DOES_NOT_ANSWER`. NOT classical hypothesis-entailment NLI (no generated hypothesis at runtime).

### Issue 3: Section Structural Scoring (V4 beta=0.12)
- V4 added section structural embeddings but showed no significant improvement on heldout.
- **V5 approach:** Do NOT re-introduce by default. Test only as a controlled ablation after core reranker experiment.

### Issue 4: Safety Denominator Discipline
- V4 had `n_negative_designed=60` vs `n_negative_operational=70` (PARTIALLY_SUPPORTED operationally treated as negative).
- V5 must pre-declare the operational binary mapping BEFORE generating the safety test.
- Fail-closed: PARTIAL_SUPPORT → INSUFFICIENT_EVIDENCE.

---

## 9. V5 Architecture Baseline

**Production default entering V5:**

```
QwenRenalRetrieverV3:
  Stage 1: Qwen3-Embedding-0.6B dense retrieval + 0.18 × document prior
  Candidate depth: Top-20 direct
  Stage 2: Qwen3-Reranker-0.6B cross-encoder (batch=8)
  Safety: raw reranker score ≥ 0.8199 → GROUNDED
           raw reranker score < 0.8199 → INSUFFICIENT_EVIDENCE
  No semantic verifier component
```

**V5 Target System (both workstreams independent):**

```
RANKING WORKSTREAM:
  Hypothesis: hard-negative fine-tuned Qwen3-Reranker-0.6B improves PassageHit@1
  Gate: substantial RERANKING_FAILURE population on fresh DEV-A
  DEV-B one-time confirmation before promotion

EVIDENCE-SAFETY WORKSTREAM:
  Task: question + passage → DIRECT_SUPPORT / PARTIAL_SUPPORT / DOES_NOT_ANSWER
  NOT: claim entailment (no generated hypothesis at inference time)
  Gate: off-the-shelf baseline first; fine-tune only if material failure
  DEV-B one-time confirmation
```

---

## 10. V5 Data Protocol Requirements (to be predeclared in Phase 2)

### Corpus constraints
- Fixed 23-document corpus (B_400_overlap, 2,691 chunks, 629 sections)
- No corpus expansion unless independent curriculum audit triggers it

### Split firewall requirements
All V5 DEV queries must be completely isolated from TRAIN on:
1. Exact query string
2. Normalized query (casefold, punct-strip)
3. Canonical medical claim
4. Learning objective
5. Primary evidence span
6. Parent source section (section_path)
7. Query family / template family
8. Transformation family

### Spent family identification
The following structural topic families are **partially spent** (used in V1-V4 train/dev/test):
- RAAS / aldosterone mechanism
- Glomerular filtration / GFR measurement
- Potassium handling / hyperkalaemia management
- Proximal tubule reabsorption / acid-base
- AKI diagnosis / management
- CKD management
- Nephrotic syndrome / proteinuria
- UTI / recurrent UTI
- Nephrolithiasis / stone management
- Hydronephrosis / obstruction grading
- Renal replacement therapy
- Urine concentration / countercurrent mechanism
- Erythropoietin / calcitriol / vitamin D renal role
- Haematuria differential diagnosis

**All 23 document topic families have been used** to some extent in prior development. V5 must generate fresh queries that represent different sub-claims, different granularities, or different query styles within the same topic families. **Source-section separation** is the primary firewall, not topic exclusion.

### Recommended V5 robustness axis for DEV-B
- DEV-A: Standard question style (WH-questions, mechanism, management)  
- DEV-B: Concise factual / enumeration style + independently generated phrasing  
  (e.g., "List the..." / "What is the..." phrasing rather than clinical scenario questions)  
  This tests whether reranker generalizes across question formulations, not just topics.

---

## 11. Key Structural Observations for V5 Implementation

### What the V3/V4 code actually does (confirmed from source)

1. **Reranker scoring interface:** `CrossEncoder.predict(pairs)` — returns raw float scores (not probability). Feature `r_top1` in the classifier IS the raw reranker score. This is important for V5: any reranker adaptation must preserve this scoring interface OR update downstream consumers.

2. **Document prior:** `alpha=0.18 × d_scores[doc_idx]` — aggregated per-document dense score, NOT per-section. V3 and V4 both use this.

3. **Section structural (V4 only):** `beta=0.12 × s_scores[section_idx]` — separate structural embedding per section. NOT in V3 production path.

4. **Reranker input representation:** `[[query, chunk.text], ...]` — plain text only. No title, section path, or metadata prepended in V3. V4 uses the same plain-text format. Section metadata ablation is a predeclared V5 optional experiment.

5. **Cache keys:** V3 uses `all23_corpus_embeddings.npy` (2,691 × dim). Any V5 reranker change does NOT invalidate the dense embedding cache — only the reranker weights change.

6. **Safety gate position:** Safety decision happens in `_query_renal` based on `hit.is_grounded` (V4) or raw score vs threshold (V3). A V5 verifier would slot into this decision point, not into the retrieval ranking.

7. **Extractive answer:** `answer = hits[0].chunk["text"]` — literally the raw passage text. No generation. This confirms the V5 verifier task is question→passage direct-support, not post-generation NLI.

### Qwen3-Reranker-0.6B compatibility notes (to verify in Phase 9 pilot)
- Used via `sentence_transformers.CrossEncoder` with `trust_remote_code=True`
- `predict()` returns raw floats (likely logit or score, not probability)
- LoRA compatibility with CrossEncoder interface must be verified before training
- VRAM budget: 6GB RTX 3060. CrossEncoder-0.6B forward/backward pilot MUST be run before choosing LoRA vs QLoRA

---

## 12. Open Questions for V5 Data Protocol (to be resolved in Phase 2)

1. **Predeclared KEEP/DISCARD threshold for ranking:** What is "meaningful" on N≈50 DEV-A? For McNemar to be interpretable we need ≥3–4 discordant pairs.
2. **Verifier label space:** DIRECT_SUPPORT / PARTIAL_SUPPORT / DOES_NOT_ANSWER — is CONTRADICTS_QUERY_PREMISE needed for V5 given many queries are open-ended (not proposition-checking)?
3. **Hard negative source for reranker:** Primary source = actual Top-20 candidate passages from fresh TRAIN queries. Must use source-grounded adjudication to confirm negativity.
4. **DEV-B robustness axis predeclaration:** Confirmed above (concise factual / enumeration style vs standard WH). Must be locked before DEV-A results seen.

---

## 13. Audit Conclusion

**The forensic audit is complete.** No V5 model has been touched or modified. All historical artifacts verified intact.

**V5 can proceed with Phase 2: Predeclare and freeze the V5 data protocol.**

Key facts confirmed from source code:
- Production default is `QwenRenalRetrieverV3` ✅
- Runtime is extractive (no generation) ✅  
- V3 safety uses raw score ≥ 0.8199 ✅  
- V4 classifier uses retrieval-confidence features only ✅  
- No semantic verifier currently exists ✅  
- 2,691 chunks / 23 documents / 629 sections available ✅  
- All historical evaluation sets confirmed spent ✅  
- Historical firewall: ALL GREEN ✅

---

*Persisted: `reports/renal_v5/renal_v5_recovery_audit.md`*  
*Commit: to follow with Phase 2 data protocol (single logical commit)*
