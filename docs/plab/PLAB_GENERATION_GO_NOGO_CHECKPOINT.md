# MedicalPlab PLAB Generation GO / NO-GO Checkpoint

**Date:** 2026-09-09  
**Branch:** `ai-data-execution-v1`  
**Status:** **GO** ✅

---

## Checklist

| Gate | Status | Evidence |
|---|---|---|
| Corpus v1 frozen | ✅ PASS | `Data/metadata/corpus_cardiorespiratory_snapshot_v1.json` — 13 documents, 817 chunks |
| Retrieval stack selected using 817-chunk benchmark | ✅ PASS | **Qwen3 Dense-only** selected. Hit@1=0.900, MRR=0.942, nDCG@10=0.944, AuthAcc=1.000 |
| Production runtime uses real retriever correctly | ✅ PASS | Strict fail-closed enforced in `Qwen3DenseRetriever`, `HybridRetriever`, `StageRPipeline`. 5 targeted tests PASS. |
| Evidence sufficiency calibrated | ✅ PASS | AUROC=0.8464, AUPRC=0.8253 on 817 chunks. Balanced τ=0.7223: Precision=87.5%, Recall=70.0%, UnsafeAccept=7.1% |
| UK reference mapping verified | ✅ PASS | 12-topic UK ground-truth gate verified (NICE×7, RCUK×2, BTS×1, FICM/ICS×1, BSAC/NICE×1) |
| Evidence exists for intended topics | ✅ PASS | All 12 mapped topics have locally verified supporting evidence (817 chunks) |
| PLAB five-option contract works | ✅ PASS | `PLABQuestion` enforces exactly 5 choices (A-E), unique texts, valid answer key |
| Citation/evidence validators work | ✅ PASS | `validate_plab_question()` checks quote presence in evidence corpus |
| Current automated tests pass | ✅ PASS | **276 passed, 1 skipped** (including 5 new strict-runtime tests) |

---

## Retrieval Benchmark Summary (817 chunks, 20 answerable queries)

| Configuration | Hit@1 | MRR | nDCG@10 | AuthAcc | p50 e2e |
|---|---:|---:|---:|---:|---:|
| **Qwen3 Dense Only (SELECTED)** | **0.900** | **0.942** | **0.944** | **1.000** | 591.5ms |
| Hybrid Weighted RRF | 0.850 | 0.890 | 0.899 | 0.750 | 608.8ms |
| BM25 + Dense Blend | 0.800 | 0.859 | 0.867 | 0.750 | 609.5ms |
| BM25 Only | 0.650 | 0.745 | 0.742 | 0.750 | 15.0ms |
| Hybrid + Neural CrossEncoder | 0.650 | 0.709 | 0.749 | 0.500 | 1166.7ms |
| Hybrid + Heuristic Reranker | 0.250 | 0.467 | 0.526 | 0.750 | 613.9ms |

---

## Evidence Sufficiency Calibration (48 cases on 817 chunks)

| Profile | Threshold τ | Coverage | Precision | Recall | Unsafe Accept | False Refusal | Confusion |
|---|---:|---:|---:|---:|---:|---:|---|
| Zero-Unsafe (Cautious) | 0.7736 | 10.4% | 100.0% | 25.0% | 0.0% | 75.0% | TP=5, FP=0, FN=15, TN=28 |
| **Balanced (PILOT)** | **0.7223** | **33.3%** | **87.5%** | **70.0%** | **7.1%** | **30.0%** | **TP=14, FP=2, FN=6, TN=26** |
| High-Coverage | 0.6709 | 60.4% | 58.6% | 85.0% | 42.9% | 15.0% | TP=17, FP=12, FN=3, TN=16 |

**Selected Pilot Operating Point:** τ = 0.7223 (Balanced)
- Accepts 87.5% precision with 70% recall
- 7.1% unsafe acceptance rate on calibration set (2/28 non-supported cases)
- This does NOT guarantee clinical safety — it is a calibration-set operating point

---

## Decision

**GO FOR CONTROLLED PLAB QUESTION GENERATION**

All 9 gate items pass. Proceed with 30-40 original Cardiorespiratory PLAB 1 SBA questions across the 12 verified topics.
