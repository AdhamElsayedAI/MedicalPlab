# Data Pipeline

## Principles

1. raw artifacts are immutable;
2. processed artifacts are separate;
3. cleaning is deterministic and non-generative;
4. source structure is preserved where useful;
5. every retrieval chunk must be traceable;
6. evaluation data is not mixed into the retrieval corpus.

## Local data layout

`Data/` is intentionally ignored by Git.

```text
Data/
+-- metadata/
+-- raw/
|   +-- cardiology/
+-- processed/
    +-- cardiology/
```

## WHO PDF path

```text
download_document.py
-> extract_document.py
-> inspect_extraction.py
-> clean_document.py
-> inspect_structure.py
-> parse_sections.py
-> validate_sections.py
-> enrich_sections.py
-> chunk_sections.py
-> validate_chunks.py
-> validate_chunk_integrity.py
```

## PMC JATS path

```text
download_pmc_xml.py
-> inspect_pmc_jats.py
-> extract_pmc_jats.py
-> inspect_pmc_extraction.py
-> adapt_pmc_to_canonical.py
-> chunk_sections.py
-> validate_chunks.py
-> validate_chunk_integrity.py
```

The PMC PDF is retained as an archival artifact. Official PMC JATS XML is the canonical machine-ingestion source.

## Tables

The adapter identifies table headers and semantic group rows, carries the group into data rows, skips structural header/group rows as standalone evidence, and renders labeled semantic rows.

`section_path` remains source-faithful.

`retrieval_section_path` can carry the semantic retrieval hierarchy when a broad table is physically located under a narrower JATS subsection.

## Provenance

PDF-derived chunks can use page provenance.

PMC JATS chunks use:

```text
provenance_type = xml_element
source_format = pmc_jats_xml
source_locator = <JATS block locator>
```

The pipeline does not invent page numbers for XML-derived content.

## Current chunk counts

```text
WHO: 83
PMC: 144
Combined: 227
```

Natural short chunks are allowed when they correspond to atomic source units such as table rows.

## Do not commit

- `Data/`;
- downloaded PDFs or XML;
- extracted/cleaned local artifacts;
- local databases;
- model caches;
- `.env` files;
- API keys or tokens.
