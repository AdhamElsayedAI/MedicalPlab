# Project Status

Last updated: 2026-09-04

## Current milestone

**Multi-source retrieval evaluation foundation**

The ingestion and chunking paths for the first WHO and PMC cardiology documents are validated. Multi-document retrieval works with document-aware block identities.

The next task is to replace the current WHO-scoped regression set with a real multi-source evaluation set.

## Completed

### Data governance

- source schema;
- document schema;
- question schema;
- chunk schema;
- retrieval evaluation schema;
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

### Retrieval evaluation

Single-document dense DEV:

```text
Qwen/Qwen3-Embedding-0.6B
Hit@1    1.0000
MRR      1.0000
nDCG@10  0.9081
```

Multi-document semantic-path DEV regression:

```text
Corpus     227 chunks
Hit@1      1.0000
Recall@1   0.4697
Recall@3   0.7197
Recall@5   0.7652
Recall@10  0.8864
MRR        1.0000
nDCG@10    0.8821
```

These are development results, not final held-out claims.

## Known retrieval finding

An Arabic treatment-initiation query initially ranked PMC drug-table rows above the WHO recommendation.

The root cause was misleading semantic metadata inherited from the JATS placement of a broad drug table.

The fix kept the source-faithful JATS path intact while adding `retrieval_section_path` for semantic retrieval context. The WHO evidence returned to rank 1 without source weighting or reranker tuning.

## Current limitations

- current multi-document DEV gold evidence is still WHO-scoped;
- corpus currently covers a narrow cardiology slice;
- no independent held-out multi-source benchmark yet;
- source-authority policy is not yet implemented;
- vector database integration is not yet the active retrieval path;
- final RAG generation/citation/abstention layer is not yet integrated;
- the PMC JATS adapter v1 is validated on the current article, not claimed as a universal parser;
- PDF and XML artifact hashes are not yet represented in a dedicated multi-artifact registry.

## Active next task

Create a real multi-source retrieval evaluation with WHO-only, PMC-only, shared-evidence, unsupported, English, Arabic, mixed-language, paraphrase, clinical-style, acronym-heavy, source-selection, and hard-negative cases.
