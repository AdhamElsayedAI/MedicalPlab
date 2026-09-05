# Roadmap

## Phase 1 - Data foundation

Status: **completed for the first validated documents**

- source governance;
- canonical contracts;
- WHO PDF processing;
- PMC JATS processing;
- structure-aware canonical blocks;
- provenance-preserving chunks;
- schema and integrity validation.

## Phase 2 - Retrieval foundation

Status: **completed for the current two-source corpus**

Completed:

- BM25 baseline;
- Qwen3 dense benchmark;
- hybrid RRF experiments;
- 0.6B reranker experiments;
- document-aware multi-document retrieval;
- semantic retrieval hierarchy for structured table rows;
- real multi-source DEV v2;
- source-aware retrieval representation;
- language, evidence-scope, and authority-sensitive slices.

Selected dense model:

```text
Qwen/Qwen3-Embedding-0.6B
```

Selected current representation:

```text
Source-aware dense retrieval
```

## Phase 3 - Independent retrieval evaluation

Status: **completed v1**

Completed:

- frozen held-out benchmark created before model runs;
- held-out validation and SHA-256 freeze manifest;
- content-only vs source-aware comparison;
- authority-sensitive and multi-source analysis;
- retrieval architecture decision record;
- documented trade-offs and failure cases.

The frozen held-out set is not to be edited in response to benchmark results.

## Phase 4 - Evidence Sufficiency and Source Policy

Status: **next**

- create a dedicated calibration set;
- measure answerable vs unsupported retrieval-score distributions;
- evaluate Top-1 score, margins, Top-k structure, and source constraints;
- define evidence-sufficiency decision logic;
- calibrate abstention behavior;
- keep source authority separate from semantic similarity;
- define explicit-source request handling;
- log evidence decisions for later evaluation.

## Phase 5 - Retrieval service

- deterministic index build;
- vector database integration if justified;
- document/source/provenance payload;
- dense candidates;
- lexical candidates where useful;
- source/evidence policy;
- stable retrieval API;
- retrieval traces;
- latency and cost measurement.

## Phase 6 - Evidence-grounded generation

- generation from retrieved evidence only;
- citations;
- citation verification;
- refusal on unsupported evidence;
- prompt/version tracking;
- answer-level evaluation;
- safety-oriented educational framing.

## Phase 7 - Adaptive learning

- learner profile;
- misconception tracking;
- weak-concept detection;
- adaptive next-question selection;
- spaced review;
- progress analytics;
- educator question/case generation.

## Phase 8 - Product integration

- FastAPI production service;
- authentication and tenant-aware product boundaries where needed;
- mobile integration;
- observability;
- deployment;
- performance/cost monitoring;
- pilot feedback and product analytics.
