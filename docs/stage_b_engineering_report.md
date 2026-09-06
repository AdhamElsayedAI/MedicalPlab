# Stage-B engineering report — 2026-09-06

Repository: `C:\Users\Adham Elsayed\Downloads\MedicalPlab-dev\MedicalPlab-dev`.
This is an implemented and locally tested candidate, not a validated production
model. Full GPU calibration, candidate selection and the later independent frozen
test remain pending. No new model metrics are claimed.

## A. Cleanup and safety

Pre-refactor SHA: `920dc9e647ba4e70cf93a53b0fc0b4e1fb13ddd3`.
Tracked work was clean. All seven untracked artifacts were backed up, hashed and
verified before removing them from the active tree:

- `pilot_external_evidence_verifier_gemini_v1.py`
- `pilot_external_evidence_verifier_gemini_v1_1.py`
- `pilot_external_evidence_verifier_gemini_v1_2.py`
- `Scripts/run_evidence_verifier_gemini_3_8_flash_v1.py`
- `prepare_medicalplab_colab_bundle.py`
- `medicalplab_stage_b_colab_bundle.zip`
- `evaluation/results/evidence_verifier_gemini_3_8_flash_v1.checkpoint.json`

Original bytes remain in sibling `stage-b-safety-920dc9e`, including tracked HEAD
archive and manifest. The historical checkpoint is also preserved in the repository
at `evaluation/history/gemini_availability_checkpoint.json`. No corpus files,
environments or unrelated retrieval experiments were deleted. Full classification:
`docs/stage_b_pre_refactor_inventory.json`.

Frozen calibration SHA: `4ece4e35de1f46888f75f4dcae624e34b8e8f2696959f162a5f434615b021ad5`.
Frozen retrieval SHA: `019a7098e3364782a5599ee570915d06bada01eb6af31d2f8dd6d1f212408cc8`.
Both match original Git blobs and working files. Top-10 source-aware retrieval is unchanged.

## B–C. Architecture and files

All paths below are relative to the repository above.

| Path | Purpose |
|---|---|
| `src/medicalplab/stage_b/models.py` | Immutable typed contracts, strict JSON |
| `src/medicalplab/stage_b/prompts.py` | Single planner/verifier prompt source |
| `src/medicalplab/stage_b/claim_planner.py` | Validate fixed claims, origins and query spans |
| `src/medicalplab/stage_b/verifier.py` | Strict per-claim output parser |
| `src/medicalplab/stage_b/evidence_policy.py` | Reference, quote, source and quantitative vetoes |
| `src/medicalplab/stage_b/aggregator.py` | Deterministic overall verdict |
| `src/medicalplab/stage_b/pipeline.py` | Two-pass orchestration and telemetry |
| `src/medicalplab/stage_b/backend.py` | Explicit Qwen AWQ configuration and GPU preflight |
| `evaluation/stage_b_inputs.py` | Frozen hash verification and gold-free packets |
| `evaluation/stage_b_metrics.py` | Counts, rates, Wilson intervals, breakdowns and taxonomy |
| `evaluation/run_stage_b_calibration.py` | Canonical calibration/regression, atomic checkpoint/resume |
| `evaluation/prepare_stage_b_bundle.py` | Explicit allowlist Colab bundle |
| `tests/stage_b/` | Deterministic, characterization and opt-in actual model regression tests |
| `notebooks/stage_b_colab.ipynb` | Thin isolated GPU setup/run wrapper |
| `docs/stage_b.md` | Contracts, commands, limitations and selection protocol |
| `docs/stage_b_experiment_history.md` | Consolidated historical evidence and decisions |
| `docs/stage_b_final_test_protocol.md` | Independent test creation after candidate lock |
| `docs/stage_b_validation.json` | Exact local commands and outcomes |
| `requirements-benchmark.txt` | Isolated benchmark requirements |
| `pyproject.toml` | Installable canonical src package; unchanged core dependencies |
| `.gitignore`, `README.md`, `DEPENDENCY_SETUP.md` | Local artifact exclusion and entry-point documentation |

The model interprets material requests and judges semantic entailment. Python
excludes marked personal context, freezes claim text, validates citations, applies
conservative binding vetoes and computes the verdict. Two passes prevent the
verifier from silently rewriting claims. This is an architectural hypothesis to
calibrate, not a demonstrated reliability improvement.

## D. Tests

Working validation interpreter: bundled Python 3.12.14. The old `.venv` points to a
missing Python 3.11 installation. Isolated dependencies are in ignored
`.stage_b/validation-deps`; no core environment was overwritten.

`python -m unittest discover -s tests -t . -v`: 50 tests, 49 passed, 1 explicitly
skipped (actual Qwen model regression). This includes separate snapshots for all
12 requested calibration/debug cases. Three pre-replacement characterization
tests ran before implementation changes.

Also passed:

- `python evaluation/run_stage_b_calibration.py --audit-inputs` (48 Top-10 packets).
- `python Scripts/validate_evidence_sufficiency_set.py`.
- `python Scripts/validate_retrieval_eval.py --eval-path evaluation/retrieval_eval_v1.json`.
- `python Scripts/validate_retrieval_eval.py --eval-path evaluation/retrieval_eval_multidoc_dev_v1.json`.
- `python Scripts/validate_chunks.py --file Data/processed/cardiology/DOC-WHO-CARD-0001.chunks.json`.
- `python Scripts/validate_chunks.py --file Data/processed/cardiology/DOC-PMC-CARD-0002.chunks.json`.
- `python Scripts/validate_chunk_integrity.py DOC-WHO-CARD-0001`.
- `python Scripts/validate_chunk_integrity.py DOC-PMC-CARD-0002`.
- Python syntax validation of 55 files and notebook code cells.
- Ruff F checks of new runtime/evaluation code, formatting, wheel build, and Git whitespace checks.

GPU preflight failed explicitly because CUDA PyTorch is absent from the working
runtime. Separately, `nvidia-smi` reports RTX 3060 Laptop / 6144 MiB, below the
configured 14 GiB total / 12 GiB free gate. No model was downloaded or substituted.

## E–F. Benchmark and scientific status

New Qwen calibration: **not run**. New unsafe-accept rate, F1, precision, coverage
and inference latency: **unavailable**, not zero. Candidate-selection targets are
unverified. AWQ 4-bit Qwen/Qwen3-8B-AWQ is the explicit candidate; GPU install and
inference need the Colab run. The notebook saves an immutable model revision.

The master prompt's historical Qwen baseline (45/48 valid, macro-F1 0.8225,
unsafe-accept rate 7.41%) has no raw result in this checkout and was not recomputed.
See experiment history for all supplied historical metrics and their provenance.
The saved Gemini checkpoint has 25 attempted cases, 22 API errors and 3 valid
responses. It is preserved as incomplete provider-availability evidence.

The existing retrieval baseline's documented zero-observed-unsafe operating point
accepts 3/48, with 0/28 unsafe accepts and 17/20 false refusals. These retrieval-only
calibration observations are not new verifier results or a safety guarantee.

Calibration and the twelve-case regression subset remain development data. The
new final test is deferred until architecture/model selection is actually complete;
its protocol is written, but no prematurely exposed final test is called frozen.

## G. Dependencies

Core declarations unchanged: jsonschema, pdfplumber, requests remain used by the
data pipeline. Stage-B deterministic runtime adds no third-party dependency.
Gemini was not a declared core dependency, so none was removed. Benchmark pins:
transformers 4.51.3, accelerate 1.10.1, autoawq 0.2.9, numpy 1.26.4; notebook installs
CUDA torch 2.6.0. These are separate from the existing retrieval stack.
Setuptools is the explicit package build backend. Validation/formatting tools were
installed only under ignored local tooling. `uv.lock` core resolution is unchanged.

## H. Git

Branch: `codex/stage-b-canonical`, created from the recorded safety SHA. Local
logical commits preserve history/characterization, then canonical implementation,
then final validation documentation. No push, merge or history rewrite requested
or performed. Final commit identifiers and clean status are reported in the task.

## I. Remaining technical work

- Execute GPU calibration, inspect failures and select/lock the candidate.
- Planner omissions, omitted source/exact flags, same-sentence relation errors and
  Arabic semantic mismatches remain possible. Local quote checks are not semantic
  proof; neither zero unsafe accepts nor low false refusal has been demonstrated.
- Validate actual AWQ package installation, full-packet memory use and latency.
- Create, independently adjudicate and freeze a genuinely new test after selection.
- Recover the historical Qwen raw output if an exact baseline comparison is needed.

## J. One next workflow

Open `notebooks/stage_b_colab.ipynb` in Colab, select a T4 or larger GPU, run all
cells, and upload `.stage_b/medicalplab.stage-b.zip` when prompted. The notebook
installs its isolated environment, verifies bundle hashes, runs tests/preflight,
pins the model revision, and checkpoints calibration to Drive.
