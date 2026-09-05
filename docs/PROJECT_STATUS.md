# Project Status

Last updated: 2026-09-05

## Current milestone

**Retrieval evaluation foundation completed for the current two-source corpus**

The first WHO and PMC cardiology ingestion paths are validated, the combined retrieval corpus contains 227 chunks, and multi-source retrieval has been evaluated on both DEV and a frozen held-out benchmark.

The selected retrieval representation is source-aware dense retrieval using `Qwen/Qwen3-Embedding-0.6B`.

The active next task is **Evidence Sufficiency Calibration v1**.

## Completed

### Data governance

- source schema;
- document schema;
- question schema;
- chunk schema;
- retrieval evaluation schemas;
- source/license policy foundation;
- separation of corpus data from evaluation data.

### WHO pipeline

- governed acquisition;
- PDF integrity validation;
- extraction audit;
- deterministic safe cleaning;
- verified structure parsing;
- hierarchy enrichment;
- chunk generation;
- schema validation;
- chunk integrity validation.

Current output:

```text
83 validated chunks
```

### PMC pipeline

- official PMC JATS acquisition;
- JATS structure inspection;
- structured section/table/reference extraction;
- canonical adaptation;
- semantic table-row rendering;
- XML provenance;
- separate retrieval semantic hierarchy where required;
- chunk generation;
- schema validation;
- chunk integrity validation.

Current output:

```text
143 canonical source blocks
144 validated chunks
1 split source block
0 integrity errors
```

### Multi-source retrieval evaluation

Current corpus:

```text
2 documents
227 chunks
192 unique source blocks
```

DEV v2:

```text
30 total cases
26 answerable
4 unsupported
```

Source-aware DEV result:

```text
Hit@1      0.9231
Recall@5   0.9872
MRR        0.9500
nDCG@10    0.9302
PreferredDoc@1 1.0000
```

Frozen held-out v1:

```text
24 total cases
20 answerable
4 unsupported
```

Frozen SHA-256:

```text
59956d5179f62795d1a1b28384090c2170959641ed555053dec81e5218afcdfe
```

Source-aware held-out result:

```text
Hit@1      0.9500
Recall@1   0.8500
Recall@3   0.8750
Recall@5   0.9250
Recall@10  0.9750
MRR        0.9563
nDCG@10    0.9357
GoldSourceRecall@10 0.9750
PreferredDoc@1      1.0000
```

These are retrieval results, not clinical accuracy claims.

## Retrieval architecture decision

Source-aware dense retrieval was selected over the content-only representation for the current startup MVP.

The main reason is that explicit source identity improved preferred-source selection on both DEV and frozen held-out evaluation without reducing overall held-out Hit@1.

Source identity does not fully solve exact passage selection. Authority policy and evidence sufficiency remain separate layers.

See:

```text
docs/RETRIEVAL_ARCHITECTURE_DECISION_V1.md
```

## Important known retrieval finding

`HOLD-018` remains a difficult authority-sensitive case.

Source-aware retrieval improved document-family selection and moved the exact WHO gold evidence closer to the top results, but the exact evidence was still not Top-5.

This supports the architecture decision to separate:

1. semantic passage relevance;
2. source authority / source constraints;
3. evidence sufficiency.

## Current limitations

- corpus currently covers a narrow cardiology slice with two source documents;
- evidence-sufficiency / abstention calibration is not yet implemented;
- explicit source-authority policy is not yet implemented as a production layer;
- vector database integration is not yet the active retrieval path;
- final RAG generation and citation verification are not yet integrated;
- the PMC JATS adapter v1 is validated on the current article, not claimed as a universal parser;
- PDF and XML artifact hashes are not yet represented in a dedicated multi-artifact registry;
- held-out results are based on the current small corpus and should not be generalized to large-corpus production performance.

## Active next task

Build **Evidence Sufficiency Calibration v1** using a dedicated calibration set rather than changing the frozen held-out benchmark.

The goal is to distinguish:

```text
sufficient evidence -> answer
insufficient evidence -> abstain
```

before integrating grounded generation.
