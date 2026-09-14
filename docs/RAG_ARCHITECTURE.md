# MedicalPlab Canonical RAG / Evidence Engine Architecture

**Canonical engine:** `MEDICALPLAB_EVIDENCE_ENGINE_V1_1`

**Base architecture commit:** `40b1efa52a3c66b273bc9a162d0023eed26d4102`

**Status:** frozen after DEV-only V2 optimization and product safety closure

**Final-holdout status:** `NO_UNSPENT_UNBIASED_FINAL_HOLDOUT_AVAILABLE`

## Runtime contract

The canonical path is:

`ClinicalQueryProcessor -> DeterministicDocumentRouter -> CandidateRetriever -> EvidenceReranker -> serving/claim gate -> EvidencePacket`

Both `POST /ai/chat` and `POST /api/v1/evidence/query` use this engine. `/ai/chat` returns only the single top passage that passed the serving gate. It has no hard-coded NICE evidence map or specialty-specific prose bypass. The direct evidence endpoint exposes the packet for inspection; it is not an assertion that every candidate is supported.

## Frozen corpus

| Field | Frozen value |
|---|---|
| Corpus | 16 public-safe PMC open-access renal documents |
| Chunk directory | `Data/experiments/renal/chunking/B_400_10pct_overlap` |
| Chunking | approximately 400-token chunks, 10% overlap |
| Chunk count | 2,175 |
| Corpus SHA-256 | `edbd4e13f56120b9fdb53a100de1b3777ac99e025f8edb739b8a2dc17989c5be` |
| Hash definition | SHA-256 over the sorted stream of chunk filenames and bytes, NUL-delimited |
| Private sources | prohibited |

## Query and retrieval configuration

`ClinicalQueryProcessor` preserves negation and clinically material context while applying deterministic spelling/acronym normalization and producing original, canonical, and neutral-target representations.

The candidate stage supports four route types. In the default product construction no embedding model is injected, so global-dense scoring is inactive; this is recorded explicitly rather than claiming a model that the canonical service does not load. The active runtime signals are deterministic document-local routing, heading-local section matching, and field-aware BM25. The optional embedding hook remains available for a separately evaluated caller configuration.

| Setting | V1.1 value |
|---|---:|
| Embedding model/revision in default runtime | none / not applicable |
| BM25 title weight | 1.0 |
| BM25 heading weight | 2.0 |
| BM25 body weight | 1.0 |
| BM25 `k1` / `b` | 1.5 / 0.75 |
| Full section-path scoring | disabled |
| Heading overlap bonus | 0.05 |
| Methods/Results/References penalty | 1.0 (no penalty) |
| RRF `k` | 60 |
| RRF A/B/C/D weights | 1.0 / 1.3 / 1.1 / 1.3 |
| Candidate depth | 50 |
| Reranker depth | 25 |

Candidate recall on the 99-query in-corpus DEV pool was 0.8384, 0.9192, 0.9394, 0.9697, 0.9798, and 0.9798 at depths 10, 20, 30, 50, 75, and 100. Depth 50 is the smallest operational point before the final one-point gain and the complete plateau from 75 to 100.

## Reranker

| Field | Frozen value |
|---|---|
| Model | `Qwen/Qwen3-Reranker-0.6B` |
| Revision | `e61197ed45024b0ed8a2d74b80b4d909f1255473` |
| Input | canonical query paired with title, section path, heading, and evidence text |
| Instruction | require direct support for the exact proposition; topical relevance alone is non-support |
| 4B model | rejected; not reconsidered or loaded |

The DEV ablation reused the same structured reranker input for all configurations. No prompt change had independent DEV justification.

## Fail-closed product-serving gate

A query-only response is eligible only when all of the following hold:

1. The top document and chunk exist in the public corpus and their stored provenance agrees.
2. Neural reranker direct-support score is at least 7.0.
3. The top passage appears in at least two distinct retrieval channels.
4. The neural reranker is available. Degraded query-only operation abstains with `CLAIM_SUPPORT_UNAVAILABLE`.

When explicit answer claims are supplied, every claim must be `SUPPORTED`. `PARTIALLY_SUPPORTED`, `NOT_SUPPORTED`, contradiction, numeric mismatch, polarity mismatch, and unsupported high-risk claims all fail closed. Typical reasons include `LOW_RETRIEVAL_CONFIDENCE`, `INELIGIBLE_EVIDENCE_SOURCE`, `CLAIM_NOT_DIRECTLY_SUPPORTED`, `CLAIM_CONTRADICTED_BY_EVIDENCE`, and `HIGH_RISK_CLAIM_UNSUPPORTED`.

The production-path DEV safety run served 0/37 deliberately unservable cases (19 labeled unsupported plus 18 current-corpus source gaps). This is `PRODUCT_SERVED_FALSE_SUPPORT = 0`, distinct from historical retrieval-ranking errors. The same run served a known supported RAAS query from an eligible source.

## DEV-only evaluation and limitations

Selection used `renal-dev-v1` plus `renal-dev-v2` only. Of 69 answerable DEV-v2 queries, 51 have gold documents in the current 16-document corpus; the other 18 are reported as `SOURCE_GAP` and excluded from ranking metrics, never deleted or relabeled. Five deterministic SHA-256 query-ID folds were used to check stability.

On the comparable 99-query pool, V1.1 improved over the exact V1 retrieval configuration:

| Configuration | Hit@1 | Hit@5 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|
| Exact V1 | 0.6768 | 0.7879 | 0.7476 | 0.6417 |
| V1.1 BM25F + bounded RRF | 0.7576 | 0.8485 | 0.8144 | 0.7061 |

MRR improved in every deterministic fold. Full section-path scoring and soft section-noise penalties were rejected because they did not add stable post-rerank value. The DEV stretch targets were not all met, so release status is `ACCEPTED_WITH_METRIC_GAP`.

All V2 holdout and safety-v2 datasets are spent. Any score on them must be labeled `DIAGNOSTIC_REEVALUATION_ONLY`; none was rerun for this closure. This release therefore makes no fresh unbiased final-holdout claim.
