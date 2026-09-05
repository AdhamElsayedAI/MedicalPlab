# Architecture

## Scope

The current architecture is centered on reliable, provenance-preserving evidence retrieval for medical education.

The main design decision is to avoid coupling source ingestion directly to an LLM. Source structure is preserved first, normalized into a common retrieval contract, evaluated independently, and only then passed toward evidence sufficiency and grounded generation.

## High-level flow

```text
Source governance
      |
      +------------------+
      |                  |
   WHO PDF            PMC JATS
      |                  |
extract/audit       structured XML
safe cleaning        extraction
structure parsing       |
      |            canonical adapter
      +---------+--------+
                |
        Canonical blocks
                |
        hierarchy metadata
                |
        Retrieval chunks
                |
        source-aware dense retrieval
                |
        Candidate evidence
                |
        +-----------------------+
        |                       |
 source / authority       evidence sufficiency
      policy                    |
        +-----------+-----------+
                    |
              grounded RAG
```

## WHO ingestion

```text
PDF
-> extraction
-> extraction audit
-> safe deterministic cleaning
-> structure inspection
-> section parsing
-> hierarchy enrichment
-> canonical sections
-> chunks
```

## PMC ingestion

The PMC article PDF is retained as an archival artifact, while official PMC JATS XML is used for machine ingestion.

```text
PMC OAI-PMH
-> JATS XML
-> structure inspection
-> structured extraction
-> canonical adapter
-> semantic table context
-> canonical sections
-> chunks
```

PMC chunks use XML element provenance rather than invented page numbers.

## Canonical representation

Important fields include:

```text
document_id
source_id
block_index
block_type
section_number
section_level
section_path
heading
text
content_sha256
provenance_type
source_locator
source_format
```

When source layout and retrieval semantics differ, `retrieval_section_path` can carry semantic context while `section_path` remains source-faithful.

## Retrieval identity

Local block indexes are not globally unique.

Retrieval/evaluation uses:

```text
(document_id, source_block_index)
```

Example:

```text
DOC-WHO-CARD-0001:B0012
DOC-PMC-CARD-0002:B0079
```

## Retrieval

Evaluated components include BM25, Qwen3 dense embeddings, weighted RRF experiments, Qwen3 reranker experiments, multi-document dense retrieval, and source-aware dense retrieval.

Selected current dense model:

```text
Qwen/Qwen3-Embedding-0.6B
```

Selected current representation:

```text
Source-aware dense retrieval
```

The retrieval representation contains explicit source-document identity in addition to semantic metadata and chunk content.

The 0.6B reranker experiments did not improve final ordering on the earlier development set, so reranking is not part of the selected baseline.

## Source authority

Semantic similarity and evidence authority are separate concerns.

A review can be semantically relevant while a primary guideline is still the preferred source for a recommendation question.

Source identity improved preferred-document selection in both DEV and frozen held-out evaluation, but it did not fully solve exact evidence selection.

Therefore the architecture separates:

```text
semantic retrieval
+
source / authority policy
+
evidence sufficiency
```

Explicit requests such as:

```text
according to WHO
from the primary guideline
compare the guideline with the review
```

should be handled by source-aware metadata and a dedicated policy layer rather than by a blind global score boost.

## Evaluation

The current evaluation stack contains two separate roles.

### DEV v2

```text
medicalplab-retrieval-multisource-dev-v2
30 cases
26 answerable
4 unsupported
```

Used for development analysis and representation experiments.

### Frozen held-out v1

```text
medicalplab-retrieval-multisource-heldout-v1
24 cases
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
Recall@10  0.9750
MRR        0.9563
nDCG@10    0.9357
PreferredDoc@1 1.0000
```

These are retrieval metrics only. They are not clinical-accuracy metrics.

Unsupported cases remain diagnostic until evidence-sufficiency calibration is completed.

## Current retrieval architecture

```text
User Query
   |
   v
Query Understanding
   |
   v
Source-Aware Dense Retrieval
Qwen3-Embedding-0.6B
   |
   v
Candidate Evidence
   |
   +--> Source / Authority Policy
   |
   +--> Evidence Sufficiency
   |
   v
Grounded RAG Generation
```

## Next architecture milestone

**Evidence Sufficiency Calibration v1**

Goal:

Determine whether the retrieved evidence is strong enough to support an answer.

```text
Candidate Evidence
      |
      v
Evidence Sufficiency
   |           |
sufficient   insufficient
   |           |
   v           v
answer       abstain
```

This layer should be calibrated separately rather than inferred from an arbitrary similarity threshold.

## Planned online architecture

```text
Mobile / Web client
        |
        v
FastAPI service
        |
        +--> retrieval service
        |      +--> dense index
        |      +--> lexical retrieval where useful
        |      +--> source / authority policy
        |      +--> evidence sufficiency
        |      +--> retrieval traces
        |
        +--> generation service
               +--> evidence context
               +--> citations
               +--> citation verification
               +--> abstention
```

The client should never contain model API keys, vector database credentials, or private prompts.
