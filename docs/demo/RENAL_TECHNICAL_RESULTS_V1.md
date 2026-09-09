# MedicalPlab Renal / Urinary Pipeline v1 — Technical Results

Status: frozen retrieval benchmark; engineering validation only. These measurements are not clinical-accuracy claims.

## Corpus and licensing

The deterministic discovery artifact contains 479 unique candidates. Sixteen were selected and acquired from Europe PMC as article-level JATS; 463 remain explicitly not selected. All 16 passed PMCID, SHA-256, extraction, canonical-structure, and commercial-use license gates.

| Document | PMCID | Title | Article JATS license |
|---|---|---|---|
| DOC-PMC-RENAL-0001 | PMC3997861 | The Renin-Angiotensin-aldosterone system in vascular inflammation and remodeling. | CC BY 3.0 |
| DOC-PMC-RENAL-0002 | PMC6692336 | A glomerulus-on-a-chip to recapitulate the human glomerular filtration barrier. | CC BY 4.0 |
| DOC-PMC-RENAL-0003 | PMC9395506 | Potassium and the kidney: a reciprocal relationship with clinical relevance. | CC BY 4.0 |
| DOC-PMC-RENAL-0004 | PMC4058521 | Roles of renal proximal tubule transport in acid/base balance and blood pressure regulation. | CC BY 3.0 |
| DOC-PMC-RENAL-0005 | PMC11064853 | Mechanisms and physiological relevance of acid-base exchange in functional units of the kidney. | CC BY (version unspecified in JATS) |
| DOC-PMC-RENAL-0006 | PMC6154171 | The Japanese clinical practice guideline for acute kidney injury 2016. | CC BY 4.0 |
| DOC-PMC-RENAL-0007 | PMC11116248 | Essential points from evidence-based clinical practice guideline for chronic kidney disease 2023. | CC BY 4.0 |
| DOC-PMC-RENAL-0008 | PMC7316686 | IPNA clinical practice recommendations for steroid-resistant nephrotic syndrome. | CC BY 4.0 |
| DOC-PMC-RENAL-0009 | PMC6892421 | Hyperkalemia: pathophysiology, risk factors and consequences. | CC BY 4.0 |
| DOC-PMC-RENAL-0010 | PMC6588653 | Management of hyperkalemia in patients with kidney disease. | CC BY 4.0 |
| DOC-PMC-RENAL-0011 | PMC8188986 | Recurrent Urinary Tract Infection: A Mystery in Search of Better Model Systems. | CC BY (version unspecified in JATS) |
| DOC-PMC-RENAL-0012 | PMC10889283 | Urological Guidelines for Kidney Stones: Overview and Comprehensive Update. | CC BY 4.0 |
| DOC-PMC-RENAL-0013 | PMC9492590 | Association of Kidney Stones and Recurrent UTIs. | CC BY 4.0 |
| DOC-PMC-RENAL-0014 | PMC7481370 | Grading of Hydronephrosis: An Ongoing Challenge. | CC BY (version unspecified in JATS) |
| DOC-PMC-RENAL-0015 | PMC4056317 | AKI due to rhabdomyolysis and renal replacement therapy. | CC BY 2.0 |
| DOC-PMC-RENAL-0016 | PMC4056314 | Assessing GFR in critically ill patients with AKI. | CC BY 2.0 |

The three measured chunk sets contain 2,251 (250-token), 2,175 (400-token with overlap), and 2,192 (section-aware) chunks. The frozen corpus is the 2,192-chunk section-aware set.

## Configuration selection on DEV only

DEV N=48 answerable queries. BM25 selected section-aware chunks by MRR (0.3766). Dense retrieval then compared representations on those chunks:

| Representation | Hit@1 | Hit@5 | Hit@10 | MRR | nDCG@10 | Gold source @10 |
|---|---:|---:|---:|---:|---:|---:|
| content-only | 15/48 | 28/48 | 31/48 | 0.4213 | 0.4579 | 43/48 |
| source-aware | 18/48 | 27/48 | 32/48 | 0.4471 | 0.4849 | 40/48 |
| metadata-aware | 25/48 | 35/48 | 39/48 | 0.6094 | 0.6461 | 46/48 |

Final frozen configuration: `Qwen/Qwen3-Embedding-0.6B`, 1,024 dimensions, metadata-aware representation, section-aware chunks, maximum retrieval sequence length 512.

DEV failure counts for the selected representation were 23/48 misses at rank 1, 13/48 at rank 5, and 9/48 at rank 10. The original benchmark did not persist per-query rankings, so this report does not invent a per-query failure list.

## Single frozen HELDOUT run

The held-out file was frozen before final selection. SHA-256: `cd7483673d8eb3aa6f85ced541a7eaad8b7c1d003b857ff1e43b6146609c26c5`.

N=56 total: 48 answerable, 8 unsupported, 18 foundational, 36 clinical, and 6 authority-sensitive answerable queries.

| Metric | Result |
|---|---:|
| Hit/Recall@1 | 30/48 (0.6250) |
| Hit/Recall@3 | 35/48 (0.7292) |
| Hit/Recall@5 | 37/48 (0.7708) |
| Hit/Recall@10 | 39/48 (0.8125) |
| GoldSourceRecall@1 | 39/48 (0.8125) |
| GoldSourceRecall@3 | 40/48 (0.8333) |
| GoldSourceRecall@5 | 42/48 (0.8750) |
| GoldSourceRecall@10 | 44/48 (0.9167) |
| MRR | 0.6816 |
| nDCG@10 | 0.7048 |
| Authority-sensitive accuracy@5 | 4/6 (0.6667) |

No target was retrofitted and held-out was not rerun for optimization.

## Evidence sufficiency and citation integrity

Calibration N=40: TP=2, TN=24, FP=0, FN=14 at threshold 0.8199287653. Precision=2/2=1.0000, recall=2/16=0.1250, F1=0.2222, specificity=24/24=1.0000, AUROC=0.7318, AUPRC=0.6126, unsafe accept rate=0/24=0, and false-refusal rate=14/16=0.8750.

All 128/128 frozen evaluation citations resolve. All 2,192/2,192 chunks resolve to their accepted registry source and have a matching document/chunk citation pair. Frozen held-out evidence support at k=5 is 37/48 (0.7708). Resolution proves referential integrity, not clinical correctness.

Query embedding/retrieval latency on the RTX 3060 Laptop GPU was p50 44.08 ms and p95 81.37 ms (N=56). Evidence-decision latency was not separately instrumented.

## Release gate and limitations

The retrieval and evidence targets were not met. Therefore Renal SBA generation is blocked: generated 0, human reviewed 0, Golden 0. The CourseLearningService supports extractive GROUNDED responses only above the frozen threshold and otherwise returns INSUFFICIENT_EVIDENCE or UNSUPPORTED. Optional dense-runtime failure also fails closed.

The strongest defensible claim is: MedicalPlab has a reproducible, license-gated 16-document/2,192-chunk Renal v1 corpus, a frozen one-run evaluation, complete citation resolution, and an integrated fail-closed learning-service boundary. It is not ready for clinical-performance or question-quality claims.
