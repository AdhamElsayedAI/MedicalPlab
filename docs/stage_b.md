# Stage-B evidence sufficiency

Status: canonical engineering candidate, awaiting Qwen GPU calibration. This is
corpus-grounded evidence sufficiency, not clinical accuracy or final RAG quality.

## Runtime

`src/medicalplab/stage_b/` is the only active implementation. `StageBPipeline.run`
accepts a query and exactly ten unique `EvidenceBlock` values. It never accepts
labels, supporting blocks, missing-support notes, case IDs or evaluation categories.
The evaluation bridge replays the frozen source-aware Qwen3-Embedding-0.6B Top-10
ranking; it does not re-embed queries or change retrieval.

1. A query-only planner separates source premises, requested facts and personal
   context. The contract removes personal context and retains requested open slots.
2. A verifier sees fixed claims plus the full evidence packet, with no gold fields.
3. Python enforces unchanged claim text/IDs, cited block membership, quote integrity,
   explicit source constraints and conservative quantitative binding checks.
4. Python aggregates: all supported -> supported; mix -> partial; none -> unsupported.

Prompts live in `prompts.py`; immutable contracts and strict JSON parsing in
`models.py`; generation settings in `backend.py`. No model-authored overall verdict
is accepted. The old v1 JSON schema is a historical contract, not the runtime schema.
Malformed output is recorded, never silently repaired or counted as a valid refusal.

Two model calls freeze interpretation independently of evidence. This may improve
consistency but has not yet been compared on latency or reliability. The planner
can still omit/misinterpret a claim, source constraint or exact flag. Citation and
binding checks cannot prove semantic entailment. In particular, same-sentence
co-occurrence is not a proof of relation, and multilingual semantic binding remains
model-dependent. The candidate must not be described as eliminating unsafe accepts.
ASCII/Arabic digits and harmless quote/dash typography normalize for provenance;
original evidence remains intact. Table support requires a literal local row.

## Local validation

From the repository root, use Python 3.11 or 3.12 with `PYTHONPATH=src`:

```sh
python -m unittest discover -s tests -t . -v
python evaluation/run_stage_b_calibration.py --audit-inputs
```

Unit and characterization tests load no LLM. The twelve requested calibration
cases are regression/debug fixtures, never held-out evidence. Historical outputs
exist for only three of those cases. Model regression uses the same runner with
`--regression`; full calibration omits that switch.

## GPU workflow

Open `notebooks/stage_b_colab.ipynb`, upload the generated local Stage-B bundle,
select a T4 or larger GPU, and run its cells. The notebook contains setup and calls
only; all verification and evaluation logic stays in canonical Python.

The backend is Qwen/Qwen3-8B-AWQ, 4-bit, float16 execution, eager attention,
non-thinking chat template, greedy generation, seed 42, 2048 maximum output tokens.
It refuses packet truncation and GPU offload. Preflight requires >=14 GiB total
and >=12 GiB free VRAM, plus the requested package versions. These conservative
limits do not guarantee every packet will fit. The 6 GiB laptop is not eligible.

The model revision must be a 40-character immutable HF commit SHA. The notebook
resolves and saves it before the first run; resume reuses that SHA. Source:
[Qwen model card](https://huggingface.co/Qwen/Qwen3-8B-AWQ).
Greedy decoding is an explicit experimental choice; it must be calibrated.

Results store raw outputs, token counts, planner/verifier/total latency, peak VRAM,
hardware/software, code/corpus/model fingerprints, per-case failures and policy
downgrades. Safe resume requires an identical configuration and an ordered prefix
of completed cases. Completed outputs cannot be overwritten. An exclusive lock
prevents simultaneous writers. After a process crash, verify it has stopped before
removing only its `.lock` file. Run again with `--resume`; failed cases remain
recorded, and retries require a distinct output/run.

Classification and safety metrics use valid predictions, with raw denominators.
Strict end-to-end correctness includes model/contract failures. Zero-denominator
rates are null. Wilson intervals are descriptive and do not correct for calibration
selection. Contrastive reversals compare unequal gold ranks; ties are separate.
Do not compare partial checkpoints as though they were 48-case results.

## Selection and final test

Targets: 100% contract pass, zero observed unsafe accepts, macro-F1 >=0.90,
supported-accept precision >=0.95. Inspect failure taxonomy before model changes.
No targets have been verified for this candidate. Final architecture/model selection
is pending, so a final test has deliberately not been authored or exposed yet.
After selection, follow `docs/stage_b_final_test_protocol.md`, freeze a genuinely new
set and its evidence packets, then evaluate without tuning on it.
