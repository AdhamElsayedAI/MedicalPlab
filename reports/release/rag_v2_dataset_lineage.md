# RAG V2 dataset lineage and evaluation firewall

Final finding: `NO_UNSPENT_UNBIASED_FINAL_HOLDOUT_AVAILABLE`.

No existing V2 holdout or safety-v2 dataset is treated as unspent. No new final holdout was manufactured from evaluated data. Any future result on a spent set must be labeled `DIAGNOSTIC_REEVALUATION_ONLY`.

## Frozen statuses

| Dataset | N | Answerable | Status | Worktree SHA-256 | Sidecar |
|---|---:|---:|---|---|---|
| `renal-dev-v1.json` | 48 | 48 | DEV optimization allowed | `8fd8b3a6df6054447cfd82768f94226217179c329db809edc3d16ca3043b61af` | matches |
| `renal-dev-v2.json` | 88 | 69 | DEV optimization allowed | `7cc0e89b49c1c8f9cbe5b3c4fcf55efa408a2ade3133f99e6de270da6ffaaa27` | stale |
| `renal-heldout-v1.json` | 56 | 48 | CONSUMED_DIAGNOSTIC_ONLY | `cd7483673d8eb3aa6f85ced541a7eaad8b7c1d003b857ff1e43b6146609c26c5` | matches |
| `renal-heldout-v2.json` | 100 | 43 | SPENT | `63f3c3e1cf31d3a77cb48e7dfd5b10ef96ada02de0d39b63854bfb99c7d09815` | stale |
| `renal-heldout-v2-final.json` | 100 | 52 | SPENT | `9492d654336302ce2260a53ca421b842c3646d7cc69c1746ba24467349906515` | stale |
| `renal-safety-test-v2.json` | 66 | 32 | SPENT | `ef33cf32419baf599aac5c7c297ecdb794e5fef87f11273c7850e1aafb614c49` | stale |

The stale sidecars are integrity defects to be reported, not evidence that the worktree datasets became fresh or unspent. The datasets were not modified during this closure.

Repository and history evidence includes commit `70f5bb9` (V2 safety evaluation and single final heldout run), `64abd4e` (frozen heldout/evidence work), `78433b1` (recovery/audit), `reports/renal_v2_final_heldout_rankings.json`, and `reports/renal_v2_safety.json`. These establish that both V2 holdouts and safety-v2 influenced prior evaluation and are spent.

## Overlap audit

Near duplicates use normalized token-set similarity of at least 0.85. Source overlap is expected in a shared-corpus evaluation and is not alone treated as leakage; exact query/evidence overlaps and prior use are decisive.

| Pair | Query ID | Exact normalized text | Evidence ID | Evidence text hash | Shared source docs | Near-duplicate pairs |
|---|---:|---:|---:|---:|---:|---:|
| DEV-v2 vs heldout-v2 | 0 | 0 | 15 | 7 | 19 | 0 |
| DEV-v2 vs heldout-v2-final | 0 | 0 | 15 | 13 | 20 | 1 |
| DEV-v2 vs safety-v2 | 0 | 0 | 7 | 3 | 14 | 0 |
| heldout-v2 vs heldout-v2-final | 0 | 23 | 11 | 8 | 19 | 2 |
| heldout-v2 vs safety-v2 | 0 | 22 | 30 | 15 | 14 | 12 |
| heldout-v2-final vs safety-v2 | 0 | 6 | 3 | 2 | 14 | 1 |

The two V2 holdouts are not independent: they contain 23 exact normalized query overlaps, 11 evidence-ID overlaps, 8 evidence-text overlaps, and 2 additional near-duplicate query pairs. Safety-v2 also materially overlaps heldout-v2. They cannot serve as independent fresh evaluations.

## DEV-only protocol used for V1.1

- Optimization and selection: `renal-dev-v1` + `renal-dev-v2` only.
- Ranking pool: 99 current-corpus answerable queries (48 + 51).
- Safety pool: all 19 DEV-v2 unsupported cases plus all 18 answerable DEV-v2 current-corpus source gaps.
- Generalization check: five deterministic SHA-256 query-ID folds.
- Heldout/safety-v2 reruns during closure: none.
- New final set assembled from old data: none.

All final ranking results are DEV results. The release status is therefore based on reproducibility, cross-fold DEV improvement, regression safety, and zero product-served false support—not on a claimed unbiased final benchmark.
