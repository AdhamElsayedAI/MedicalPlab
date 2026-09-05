# MedicalPlab Held-Out Retrieval Benchmark v1

## Purpose

This is the independent held-out benchmark used after DEV v2.

It was designed after the DEV A/B experiments but before any held-out model run.

## Composition

- Total cases: 24
- Answerable: 20
- Unsupported: 4
- Single-source: 12
- Multi-source: 4
- Authority-sensitive: 4
- Unsupported: 4
- English: 14
- Arabic: 6
- Mixed Arabic/English: 4

## Freeze hash

`retrieval_eval_multisource_heldout_v1.json`

SHA-256:

```text
59956d5179f62795d1a1b28384090c2170959641ed555053dec81e5218afcdfe
```

## Rules

1. Validate the JSON against `schemas/retrieval_eval_v2.schema.json` and the local canonical document blocks.
2. Verify the SHA-256 before the first model run.
3. Do not edit the held-out set after seeing any held-out result.
4. Run Baseline A and Baseline B with the exact retrieval code already evaluated on DEV v2.
5. Do not tune model instructions, source labels, weights, reranking, thresholds, or chunk representation between A and B.
6. Use held-out results only to choose between the already-defined A and B representations.
7. Unsupported cases remain diagnostic until evidence-sufficiency calibration is built separately.

## Validation command

```bat
".venv\Scripts\python.exe" Scripts\validate_retrieval_eval.py --eval-path "evaluation\retrieval_eval_multisource_heldout_v1.json" --schema-path "schemas\retrieval_eval_v2.schema.json"
```

## Hash verification command

```bat
certutil -hashfile "evaluation\retrieval_eval_multisource_heldout_v1.json" SHA256
```

The printed SHA-256 must match the freeze hash above.

## Benchmark protocol

Only after validation and hash verification pass, run both predefined variants without changing code between them.

### Baseline A — content-only

```bat
".venv\Scripts\python.exe" Scripts\benchmark_qwen3_embedding_multisource_v2.py --eval-path "evaluation\retrieval_eval_multisource_heldout_v1.json" --results-name "qwen3_embedding_0.6b_multisource_heldout_v1_content_only.json"
```

### Baseline B — explicit source identity

```bat
".venv\Scripts\python.exe" Scripts\benchmark_qwen3_embedding_multisource_v2.py --eval-path "evaluation\retrieval_eval_multisource_heldout_v1.json" --include-source-labels --results-name "qwen3_embedding_0.6b_multisource_heldout_v1_source_labels.json"
```
