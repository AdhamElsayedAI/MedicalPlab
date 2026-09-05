# MedicalPlab Real Multi-Source Evaluation v2

## Purpose

This DEV set replaces the previous WHO-scoped multi-document stress test with a genuinely document-aware evaluation design.

The gold labels were manually designed from the validated WHO + PMC evidence catalog, not from retriever rankings.

## Corpus

- `DOC-WHO-CARD-0001`
- `DOC-PMC-CARD-0002`
- 227 validated retrieval chunks in the current corpus.

## Case count

Total: **30**

### Evidence scope

- Single-source: **18**
- Multi-source: **4**
- Authority-sensitive: **4**
- Unsupported: **4**

### Language

- English: **17**
- Arabic: **8**
- Mixed Arabic/English: **5**

### Difficulty

- Easy: **1**
- Medium: **15**
- Hard: **14**

## New v2 semantics

Each case includes:

- `evidence_scope`
- `target_document_ids`
- `preferred_document_id`

### `single_source`

The answer is supported by one target document.

### `multi_source`

Relevant evidence is intentionally expected from both documents.

### `authority_sensitive`

The query explicitly requires a preferred or primary source. Semantically similar secondary evidence can act as a hard distractor.

### `unsupported`

The current corpus does not contain sufficient evidence for the requested claim. These cases are intended to support future abstention/evidence-sufficiency evaluation.

## Important evaluation rule

This is still a **development set**.

Do not:

- fine-tune on it and then report it as an independent test;
- tune source weights repeatedly against it and call the final score generalization;
- describe retrieval metrics as clinical accuracy.

After the retrieval strategy stabilizes on DEV v2, create and freeze a separate held-out benchmark.

## Next command

Validate the set against the v2 schema and canonical local documents:

```bat
".venv\Scripts\python.exe" Scripts\validate_retrieval_eval.py ^
  --eval-path "evaluation\retrieval_eval_multisource_dev_v2.json" ^
  --schema-path "schemas\retrieval_eval_v2.schema.json"
```

Do not run model tuning before this validation passes.
