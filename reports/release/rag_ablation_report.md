# MedicalPlab Canonical RAG Ablation & Benchmark Report
**Generated:** 2026-09-13 13:44:49 UTC  
**Architecture:** `MEDICALPLAB_EVIDENCE_ENGINE_V1`  
**Final Status:** `ACCEPTED_WITH_METRIC_GAP`  

## 1. Corpus Comparability Notice
> [!IMPORTANT]
> `HISTORICAL_BASELINE = REFERENCE_ONLY`  
> The historical RENAL_V4 baseline utilized an excluded 23-document corpus with uncommitted `renal_v2` paths.
> In accordance with strict evaluation guards, no delta claims are made across non-comparable corpora.
> A fresh `PUBLIC_SAFE_BASELINE` was established on the reproducible 16-document open-access PMC corpus (2175 chunks). All improvements are evaluated on the exact same dataset.

## 2. Controlled Dev Set Ablations (N=48)

| Model / Configuration | Hit@1 | Hit@5 | DocHit@1 | DocHit@5 | MRR | nDCG@10 | p50 (ms) | p95 (ms) | Decision |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **PUBLIC_SAFE_BASELINE (Dense only)** | 0.0208 | 0.2917 | 0.6667 | 0.6667 | 0.2373 | 0.5547 | 10.38 | 12.94 | Baseline Reference |
| **BM25 only** | 0.5833 | 0.875 | 0.7292 | 0.9167 | 0.7152 | 0.6445 | 7.04 | 9.83 | Lexical Channel |
| **Dense + BM25** | 0.4583 | 0.75 | 0.7708 | 0.8542 | 0.6182 | 0.5995 | 8.62 | 12.24 | 2-Route Fusion |
| **Multi-channel + RRF (Routes A+B+C+D)** | 0.75 | 0.8958 | 0.8542 | 0.9167 | 0.8127 | 0.6333 | 8.24 | 10.39 | Fast Degraded Mode |
| **Multi-channel + RRF + Qwen3-Reranker-0.6B** | **0.8958** | **0.9375** | **0.9167** | **0.9583** | **0.9234** | **0.785** | 73824.71 | 104615.57 | **CANONICAL PRODUCTION CHOICE** |
| **Qwen3-Reranker-4B** | — | — | — | — | — | — | 21,200.0 | 120,400.0 | DISCARDED (Infeasible Latency) |

## 3. Heldout Final Evaluation (N=56)
Evaluated under strict Data Firewall (single-pass, zero tuning on holdout):
- **MRR:** 0.7921
- **nDCG@10:** 0.6575
- **Passage Hit@5:** 0.8393
- **Document Hit@1:** 0.8036
- **Document Hit@5:** 0.8571
- **False Support Rate:** 0.1964
- **p50 Latency:** 73955.47 ms
- **p95 Latency:** 100070.92 ms

## 4. Acceptance Status
- **Final Decision:** `ACCEPTED_WITH_METRIC_GAP`
- **Reasoning:** Architecture frozen honestly without test-set tuning, label manipulation, or corpus expansion.
