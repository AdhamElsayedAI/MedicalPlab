# Contributing

MedicalPlab is being developed as an evaluation-first medical retrieval and learning system. Changes should preserve reproducibility, provenance, and the distinction between development results and final evaluation.

## Branches

Use `main` for stable, validated work.

Examples:

```text
eval/multisource-v2
retrieval/qdrant-index
rag/generation-v1
api/retrieval-service
```

## Data contracts

Schemas under `schemas/` are part of the project contract.

When changing one:

1. keep backward compatibility when practical;
2. update the matching validator;
3. run regression validation on existing artifacts;
4. document the semantic change;
5. do not silently reinterpret provenance fields.

## Medical source handling

Do not commit files under `Data/`.

New sources should be registered, license-reviewed, hashed at acquisition, kept immutable in raw storage, and processed into separate canonical artifacts.

Evaluation datasets must stay separate from retrieval corpus data.

## Retrieval changes

Report corpus scope, model/configuration, query set, Hit@K, Recall@K, MRR, nDCG when applicable, and whether the benchmark is DEV or held-out.

Do not tune on a benchmark and later describe that same benchmark as held-out performance.

## Before commit

```bat
python -m py_compile Scripts\*.py
python Scripts\validate_retrieval_eval.py --eval-path "evaluation\retrieval_eval_v1.json"
python Scripts\validate_retrieval_eval.py --eval-path "evaluation\retrieval_eval_multidoc_dev_v1.json"
git diff --check
git status
```

When local processed data is available, also run both chunk validators.

## Commit style

Prefer short engineering-focused messages:

```text
Add document-aware retrieval evaluation
Preserve semantic table context in PMC chunks
Add held-out multilingual retrieval cases
Introduce source authority metadata
```

Avoid vague messages such as `update` or `fix stuff`.

## Results

Committed benchmark outputs should be reproducible and clearly labeled.

Do not commit temporary debug output, model caches, raw medical artifacts, secrets, local environments, or one-off migration scripts that are no longer maintained.
