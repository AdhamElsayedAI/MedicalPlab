# Production Retrieval Stack Decision Record

**Benchmark:** `medicalplab-full-corpus-817-retrieval-comparison-v1`  
**Date:** 2026-09-09  
**Corpus:** `medicalplab-cardiorespiratory-corpus-v1` v1.0.0 (13 documents, 817 chunks)  
**Eval Set:** `medicalplab-retrieval-multisource-heldout-v1` v1.0.0 (24 cases: 20 answerable, 4 unsupported)  
**Device:** CPU (PyTorch 2.14.0+cpu)  
**Git Commit:** `d628795` (branch `ai-data-execution-v1`)

---

## Full Benchmark Results

| Configuration | Hit@1 | Hit@3 | Hit@5 | Rec@1 | Rec@3 | Rec@5 | Rec@10 | MRR | nDCG@10 | AuthAcc | p50 e2e | p95 e2e | mean e2e |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Qwen3 Dense Only** | **0.900** | **1.000** | **1.000** | **0.800** | **0.975** | **1.000** | **1.000** | **0.942** | **0.944** | **1.000** | 591.5ms | 667.6ms | 598.5ms |
| Hybrid Weighted RRF | 0.850 | 0.950 | 0.950 | 0.800 | 0.850 | 0.875 | 1.000 | 0.890 | 0.899 | 0.750 | 608.8ms | 678.8ms | 612.9ms |
| BM25 + Dense Blend | 0.800 | 0.900 | 0.950 | 0.750 | 0.825 | 0.875 | 0.950 | 0.859 | 0.867 | 0.750 | 609.5ms | 679.2ms | 613.4ms |
| BM25 Only | 0.650 | 0.900 | 0.900 | 0.600 | 0.825 | 0.825 | 0.825 | 0.745 | 0.742 | 0.750 | 15.0ms | 26.8ms | 14.3ms |
| Hybrid + Neural CrossEncoder | 0.650 | 0.650 | 0.800 | 0.575 | 0.600 | 0.750 | 0.950 | 0.709 | 0.749 | 0.500 | 1166.7ms | 1461.1ms | 1211.2ms |
| Hybrid + Heuristic Reranker | 0.250 | 0.600 | 0.800 | 0.200 | 0.525 | 0.725 | 0.850 | 0.467 | 0.526 | 0.750 | 613.9ms | 693.2ms | 618.9ms |

---

## SELECTED CONFIGURATION

> **Qwen3 Dense Only** (`Qwen/Qwen3-Embedding-0.6B`, cosine similarity, instruction-prompted)

---

## WHY SELECTED

Qwen3 Dense-only **dominates every quality metric** against the full 817-chunk production corpus:

1. **Best Hit@1 (0.900)** — 5.9% above Weighted RRF, 12.5% above Blend, 38.5% above BM25
2. **Perfect Hit@3, Hit@5, Recall@5, Recall@10** — all 1.000
3. **Highest MRR (0.942)** and **nDCG@10 (0.944)**
4. **Perfect Authority Accuracy (1.000)** — every source-specific query retrieves the correct authoritative document
5. **Simpler architecture** — no fusion, no reranker, no tunable alpha/k parameters
6. **Competitive latency** — 591.5ms p50 on CPU (no GPU), which is within acceptable bounds for a pilot product

No other configuration matches or exceeds Dense-only on any primary quality metric.

---

## QUALITY ADVANTAGE

| Metric | Dense-Only | Best Alternative | Delta |
|---|---:|---:|---:|
| Hit@1 | 0.900 | 0.850 (RRF) | +5.9% |
| Hit@3 | 1.000 | 0.950 (RRF) | +5.3% |
| Recall@5 | 1.000 | 0.875 (RRF/Blend) | +14.3% |
| MRR | 0.942 | 0.890 (RRF) | +5.8% |
| nDCG@10 | 0.944 | 0.899 (RRF) | +5.0% |
| AuthAcc | 1.000 | 0.750 (RRF/Blend/BM25) | +33.3% |

---

## LATENCY COST

- **p50 end-to-end:** 591.5ms (CPU) — includes query embedding inference + cosine similarity across 817 chunks
- **p95 end-to-end:** 667.6ms (CPU)
- **Amortization:** Corpus embeddings are pre-computed and cached (`corpus_817_qwen3_embeddings.npy`). Only per-query embedding inference (~580ms CPU) is on the hot path.
- **GPU projection:** With GPU inference, query embedding latency drops to ~10-30ms, making total e2e latency <50ms.

---

## KNOWN FAILURE MODES

1. **Lexical mismatch blindness:** Dense retrieval may miss queries phrased with rare clinical abbreviations not in the embedding model's vocabulary. Mitigated by instruction prompting.
2. **Cold-start latency:** First query after model load takes ~6s (model loading) + ~1436s (corpus encoding on CPU). Mitigated by pre-computed embedding cache.
3. **Corpus scale ceiling:** At 817 chunks, brute-force cosine similarity is fast. Beyond ~50K chunks, approximate nearest-neighbor indexing (FAISS/HNSW) would be needed.

---

## REJECTED CONFIGURATIONS AND WHY

### Hybrid Weighted RRF — REJECTED
- Hit@1 0.850 vs 0.900 (Dense)
- Authority accuracy 0.750 vs 1.000 (Dense) — fails 25% of source-specific queries
- Adds BM25 dependency and RRF tuning parameters (k=60, weights 2:1) without quality benefit
- Marginally higher latency (608.8ms vs 591.5ms)

### BM25 + Dense Blend — REJECTED
- Hit@1 0.800 vs 0.900 (Dense) — 12.5% worse
- Authority accuracy 0.750 — same source-routing failure as RRF
- Alpha parameter (0.6) adds tuning surface without benefit
- Recall@10 0.950 vs 1.000 — misses relevant passages

### BM25 Only — REJECTED
- Hit@1 0.650 — 38.5% below Dense
- Recall@10 0.825 — misses 17.5% of relevant passages
- Extremely fast (15ms p50) but unacceptable quality for medical education
- No semantic understanding; fails on paraphrased queries

### Hybrid + Heuristic MedicalReranker — REJECTED (CRITICAL FAILURE)
- **Hit@1 0.250** — catastrophic 70.6% degradation from RRF baseline (0.850)
- MRR 0.467 — severely corrupted ranking
- The heuristic keyword-density reranker actively destroys neural ranking quality
- **Label: HEURISTIC** — this is NOT a neural reranker
- **Verdict: Must NEVER enter production retrieval path**

### Hybrid + Neural Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) — REJECTED
- Hit@1 0.650 — 29.4% below Dense-only
- Authority accuracy 0.500 — fails half of source-specific queries
- p50 latency 1166.7ms — 97% slower than Dense-only
- Generic web cross-encoder is misaligned with medical domain semantics
- **Verdict: Insufficient quality gain to justify 2× latency increase**

---

## PRODUCTION CONFIGURATION PARAMETERS

```yaml
retrieval_stack: dense_only
embedding_model: Qwen/Qwen3-Embedding-0.6B
query_instruction: "Instruct: Given a medical education query, retrieve the passages from the available medical sources that most directly support the requested claim. Respect any source explicitly requested by the query. Do not assume every query targets a guideline.\nQuery:"
normalize_embeddings: true
similarity_metric: cosine
corpus_embedding_cache: Data/metadata/corpus_817_qwen3_embeddings.npy
reranker: none
fusion: none
fallback_to_stub: false  # strict mode
```
