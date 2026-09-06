# Stage-B experiment history

## Evidence available in this checkout

Pre-refactor SHA: `920dc9e647ba4e70cf93a53b0fc0b4e1fb13ddd3`.
Original branch: `stage-b-verifier-v1`; tracked/staged diffs were empty.
Seven untracked artifacts were preserved byte-for-byte with a SHA manifest in
`../stage-b-safety-920dc9e`. That sibling backup also contains a Git archive of HEAD.
`stage_b_pre_refactor_inventory.json` classifies all tracked/untracked files.
Data and virtual environments remain ignored and untouched. No destructive Git cleanup.

The Gemini v1, v1.1 and v1.2 pilots and full Gemini runner duplicated prompts,
schemas, packet construction and reference validation. v1.2 added provider schema
constraints and retries. Their shared useful behavior is consolidated into canonical
Python; the originals are retained in the safety backup, outside the active tree.
The old bundle builder and generated zip are preserved there too. A new allowlist
builder replaces them. The Gemini checkpoint is retained under evaluation/history.
No unrelated retrieval scripts were removed merely for having version suffixes.

The saved Gemini checkpoint contains 25 attempted cases:
22 API errors and 3 valid responses. Provider 503
availability failures dominate. It is incomplete, not a 48-case benchmark.
Characterization fixtures retain available raw historical outputs, with null for
unavailable cases. Historical missing responses are not replaced with invented outputs.

## User-supplied history without raw Qwen artifacts here

The master prompt reports a Qwen3-8B-AWQ v1.1 calibration baseline: 48 total,
45 valid, 3 contract failures, contract pass 93.75%, strict end-to-end correctness
79.17%, valid 3-way accuracy 84.44%, macro-F1 0.8225, unsafe accepts 7.41%, false
refusal 5.56%, supported accept precision 89.47%, coverage 42.22%.
These numbers are transcribed historical claims, not independently recomputed
results. The raw output is absent from the inspected checkout and input bundle.
They imply about 2/27 valid negative unsafe accepts, but raw counts must be verified
from the original artifact before official comparison.

The prompt also reports Qwen3-1.7B local runtime infeasibility, multi-pass claim
decomposition trials, quote grounding trials and overly brittle binding heuristics.
Their exact scripts/results are absent, so no run details are invented.

## Retained and rejected decisions

Retain query interpretation -> fixed material claims -> verification -> deterministic
aggregation. Retain source-premise/request separation, personal-context exclusion,
quote/reference validation, Unicode normalization and structured row provenance.
Reject model-authored final verdicts, parametric medical knowledge as evidence,
cross-stitching facts, similarity as entailment, and case-ID production exceptions.

Regression diagnostics from the supplied prompt: 012 must not infer HbA1c/ECG repeat
intervals from baseline tests and general follow-up; 041 categorical medication
preference must not be mistaken for a numeric threshold; 043 allows a single
labetalol row to bind its dose. Intervals are not visit counts and generic doses
are not dose conversions. The twelve requested cases remain calibration/debug data.

The new quantitative checks are conservative vetoes, not a complete entailment
engine. Model calibration is required to measure unsafe accepts and false refusals.
No candidate-selection targets have yet been established by execution.
