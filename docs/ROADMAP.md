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

Status: **in progress**

Completed:

- BM25 baseline;
- Qwen3 dense benchmark;
- hybrid RRF experiments;
- 0.6B reranker experiments;
- document-aware multi-document retrieval;
- semantic retrieval hierarchy for structured table rows;
- multi-document DEV regression.

Current:

- real multi-source evaluation v2.

Next:

- WHO-targeted cases;
- PMC-targeted cases;
- shared-evidence cases;
- source-authority cases;
- unsupported cases;
- Arabic / English / mixed queries;
- harder paraphrases and clinical-style queries.

## Phase 3 - Independent model evaluation

- freeze held-out benchmark before further tuning;
- compare embedding model sizes on the same benchmark;
- compare latency, VRAM, recall, MRR, and nDCG;
- evaluate larger rerankers only if needed;
- record deployment cost/constraints.

## Phase 4 - Retrieval service

- vector database integration;
- deterministic index build;
- document/source/provenance payload;
- lexical + dense candidates;
- source/evidence policy;
- stable retrieval API;
- retrieval traces.

## Phase 5 - Evidence-grounded generation

- generation from retrieved evidence only;
- citations;
- evidence sufficiency;
- confidence/abstention;
- refusal on unsupported evidence;
- prompt/version tracking;
- answer-level evaluation.

## Phase 6 - Adaptive learning

- learner profile;
- misconception tracking;
- weak-concept detection;
- adaptive next-question selection;
- spaced review;
- progress analytics;
- educator question/case generation.

## Phase 7 - Product integration

- FastAPI production service;
- authentication;
- mobile integration;
- observability;
- deployment;
- performance/cost monitoring.
