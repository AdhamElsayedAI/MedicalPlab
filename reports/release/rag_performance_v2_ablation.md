# RAG V2 DEV-only ablation

Status: `ACCEPTED_WITH_METRIC_GAP`  
Architecture selected: `MEDICALPLAB_EVIDENCE_ENGINE_V1_1`  
Final evaluation status: `NO_UNSPENT_UNBIASED_FINAL_HOLDOUT_AVAILABLE`

## Protocol

Selection used only `renal-dev-v1` and `renal-dev-v2`. Ranking metrics use the 99 answerable queries whose gold documents exist in the current 16-document corpus (48 DEV-v1 + 51 DEV-v2). The 18 answerable DEV-v2 source gaps were retained and reported, but excluded from ranking metrics because success is impossible against the current corpus. The 19 explicitly unsupported DEV-v2 items and 18 source gaps form the 37-case DEV safety set.

The same top-25 Qwen3-Reranker-0.6B scores were shared across each candidate-list ablation. Latency columns below are measured ablation-harness time (variant retrieval plus shared union scoring); the actual selected production-path latency is reported separately.

| Variant | H@1 | H@3 | H@5 | H@10 | MRR | nDCG@10 | Recall@20 | Recall@50 | DocH@1 | p50 ms | p95 ms | Served unsafe |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Exact V1 | .6768 | .7879 | .7879 | .8485 | .7476 | .6417 | .8485 | .9495 | .8283 | 1167.93 | 1459.58 | 1/37 |
| V1 + BM25F (1/2/1) | .6869 | .7778 | .7980 | .8485 | .7513 | .6475 | .8586 | .9495 | .8182 | 1185.63 | 1473.83 | 1/37 |
| V1 + bounded RRF (1/1.4/1.2/1.2) | .7273 | .8384 | .8384 | .8788 | .7944 | .6738 | .8788 | .9697 | .8384 | 1168.55 | 1460.13 | 1/37 |
| V1 + full section path | .6768 | .7778 | .7778 | .8384 | .7493 | .6429 | .8485 | .9596 | .8182 | 1169.85 | 1460.93 | 1/37 |
| V1 + 0.95 section-noise penalty | .6768 | .7879 | .7879 | .8485 | .7476 | .6411 | .8485 | .9495 | .8182 | 1169.01 | 1460.31 | 1/37 |
| **V1.1 BM25F + balanced RRF** | **.7576** | **.8384** | **.8485** | **.9091** | **.8144** | **.7061** | **.9192** | **.9697** | **.8586** | **1185.32** | **1480.25** | **0/37** |

The gate-replay column applies the frozen direct-support score threshold (7.0) and two-channel agreement rule to cached DEV signals. The selected configuration was then independently exercised through the actual production engine path and again served 0/37 unservable cases.

## Cross-fold stability

| Fold | N | V1 MRR | V1.1 MRR | V1 H@5 | V1.1 H@5 |
|---:|---:|---:|---:|---:|---:|
| 0 | 22 | .7610 | .7927 | .8182 | .8636 |
| 1 | 14 | .6951 | .7406 | .7857 | .7857 |
| 2 | 21 | .8895 | .9294 | .9048 | .9524 |
| 3 | 20 | .6364 | .7624 | .7000 | .8500 |
| 4 | 22 | .7333 | .8207 | .7273 | .7727 |

MRR improved in all five deterministic folds. Hit@5 improved in four and tied in one. The combined change is therefore not supported by only one or two lucky queries.

## Residual DEV root causes

The selected system has 24 Hit@1 misses in the 99-query in-corpus pool. A deterministic case-level classification first identifies a Methods/Results top passage, then separates wrong-document tops from right-document/wrong-passage tops.

| Category | Hit@1 loss | Hit@5 loss | Hit@10 loss | MRR loss sum | nDCG loss sum | Wrong top doc |
|---|---:|---:|---:|---:|---:|---:|
| DOCUMENT_ROUTING_MISS | 13 | 8 | 4 | 9.8805 | 9.5547 | 13 |
| SECTION_HEADING_AMBIGUITY | 9 | 6 | 4 | 7.0744 | 4.3452 | 0 |
| METHODS_RESULTS_NOISE | 2 | 1 | 1 | 1.4167 | 1.1108 | 1 |
| **Total** | **24** | **15** | **9** | **18.3716** | **15.0107** | **14** |

In addition, 18 answerable DEV-v2 cases are `SOURCE_GAP` because their gold documents are outside the current corpus. They are excluded from ranking metrics and included in safety evaluation; none was served. The small residual noise category does not justify a global section penalty because the tested penalty failed to improve post-rerank metrics and could suppress legitimate Methods/Results evidence.

## Candidate-depth decision

| Depth | Candidate recall |
|---:|---:|
| 10 | .8384 |
| 20 | .9192 |
| 30 | .9394 |
| 50 | .9697 |
| 75 | .9798 |
| 100 | .9798 |

Candidate depth 50 is retained. Moving from 50 to 75 recovers one additional query (1.01 percentage points), and 75 to 100 adds nothing. Reranker depth remains 25 for runtime practicality.

## Decisions

- Kept true field-aware BM25 with title/heading/body weights 1.0/2.0/1.0.
- Kept the small RRF rebalance to A/B/C/D weights 1.0/1.3/1.1/1.3.
- Rejected full section-path scoring: no stable post-rerank benefit and lower Hit@5/Hit@10 in isolation.
- Rejected section-noise penalties: no MRR gain and slightly lower nDCG@10; relevant evidence can occur in Methods/Results.
- Rejected the older 3.0 heading boost and 0.70 noise penalty as overly aggressive.
- Kept the existing structured reranker input; no prompt variant had independent DEV justification.
- Stopped after three defensible additions (section path, noise penalty, and the larger combined heuristic) failed to add stable value beyond BM25F + bounded RRF.

## Actual selected runtime

On CUDA, the selected end-to-end production path measured 951.18 ms p50 and 1160.31 ms p95 over 99 warm DEV queries. Cold model startup was 10829.38 ms and is reported separately. These values include candidate retrieval, top-25 reranking, and the serving gate.
