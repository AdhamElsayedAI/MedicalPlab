# Architecture

## Scope

The current architecture is centered on a reliable evidence retrieval layer for medical education.

The main design decision is to avoid coupling source ingestion directly to an LLM. Source structure is preserved first, then normalized into a common retrieval contract.

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
      dense / lexical retrieval
                |
        Evaluation layer
                |
          RAG layer [next]
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

Evaluated components currently include BM25, Qwen3 dense embeddings, weighted RRF experiments, Qwen3 reranker experiments, and multi-document dense retrieval.

Current development dense model:

```text
Qwen/Qwen3-Embedding-0.6B
```

The 0.6B reranker experiments did not improve final ordering on the current development set, so reranking remains experimental.

## Source authority

Semantic similarity and evidence authority are separate concerns. A review can be highly relevant while a guideline is still the preferred source for recommendation questions.

Source authority will therefore be implemented as an explicit policy/ranking layer rather than a global embedding boost.

## Evaluation

The current multi-document evaluation is a development regression/stress set, not a final multi-source benchmark.

The next version will contain questions whose correct evidence can come from WHO, PMC, both, or neither.

## Planned online architecture

```text
Mobile / Web client
        |
        v
FastAPI service
        |
        +--> retrieval service
        |      +--> vector index
        |      +--> lexical retrieval
        |      +--> source/evidence policy
        |
        +--> generation service
               +--> evidence context
               +--> citations
               +--> confidence
               +--> abstention
```

The client should never contain model API keys, vector database credentials, or private prompts.
