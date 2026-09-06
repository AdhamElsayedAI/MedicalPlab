# MedicalPlab

MedicalPlab is an evidence-grounded medical learning platform focused on reliable retrieval before generation.

The current codebase is building the data, retrieval, and evidence-safety foundation for an adaptive medical education system: governed source acquisition, structure-aware extraction, canonical medical content, provenance-preserving chunking, multilingual retrieval, source-aware evaluation, and evidence sufficiency before grounded generation.

The generation layer is intentionally not the center of the project yet. Retrieval quality, source traceability, source selection, and evaluation are validated first.

## Current status

The active retrieval corpus currently contains two independently processed cardiology sources:

| Source | Ingestion path | Validated chunks |
| --- | --- | ---: |
| WHO hypertension guideline | PDF -> extraction -> cleaning -> structure parsing | 83 |
| PMC hypertension review | PMC JATS XML -> structured extraction -> canonical adapter | 144 |
| **Combined corpus** | Multi-document retrieval | **227** |

Current dense retriever:

```text
Qwen/Qwen3-Embedding-0.6B
```

Current retrieval representation:

```text
Source-aware dense retrieval
```

The selected representation includes explicit source-document identity in addition to semantic metadata and content. The decision was made after comparing content-only and source-aware retrieval on both DEV and a frozen held-out benchmark.

### Frozen held-out retrieval result

Evaluation set:

```text
medicalplab-retrieval-multisource-heldout-v1
```

Composition:

```text
24 total cases
20 answerable
4 unsupported
```

Source-aware dense retrieval:

| Metric | Score |
| --- | ---: |
| Hit@1 | 0.9500 |
| Recall@1 | 0.8500 |
| Recall@3 | 0.8750 |
| Recall@5 | 0.9250 |
| Recall@10 | 0.9750 |
| MRR | 0.9563 |
| nDCG@10 | 0.9357 |
| GoldSourceRecall@10 | 0.9750 |
| PreferredDoc@1 | 1.0000 |

The frozen benchmark was validated and hashed before model evaluation. Unsupported questions are still diagnostic only because evidence-sufficiency calibration has not yet been completed.

## Architecture

```text
Medical sources
    |
    +-- WHO PDF
    |     -> extraction
    |     -> audit
    |     -> safe cleaning
    |     -> structure parsing
    |
    +-- PMC JATS XML
          -> structured extraction
          -> canonical adapter
                |
                v
        Canonical source blocks
                |
                v
        Structure-aware chunks
                |
                v
        Source-aware dense retrieval
                |
                v
        Candidate evidence
                |
                +--> source / authority policy
                |
                +--> evidence sufficiency
                |
                v
        Grounded RAG generation [next after sufficiency]
```

Raw and processed medical data live under `Data/` and are intentionally excluded from Git.

## Repository map

```text
MedicalPlab/
+-- Scripts/
+-- schemas/
+-- examples/
+-- evaluation/
+-- docs/
+-- pyproject.toml
+-- requirements.txt
+-- requirements-retrieval.txt
+-- uv.lock
```

## Environment

Recommended:

- Python 3.11
- Windows, Linux, or macOS for the data pipeline
- NVIDIA CUDA-capable GPU for the current Qwen3 dense benchmark script

Windows core setup:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
```

For retrieval benchmarks, install a PyTorch build appropriate for the target machine first, then install the validated retrieval stack:

```bat
pip install -r requirements-retrieval.txt
```

Verify CUDA before running the dense benchmark:

```bat
python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

See `DEPENDENCY_SETUP.md` for the validated local versions and environment notes.

## Data setup

`Data/` is not committed. Start from the example metadata files:

```bat
mkdir Data\metadata 2>nul
copy examples\document_manifest.example.json Data\metadata\document_manifest.json
copy examples\source_registry.example.json Data\metadata\source_registry.json
```

Typical local layout:

```text
Data/
+-- metadata/
+-- raw/
|   +-- cardiology/
+-- processed/
    +-- cardiology/
```

## Core validation commands

```bat
python Scripts\validate_chunks.py --file "Data\processed\cardiology\DOC-WHO-CARD-0001.chunks.json"
python Scripts\validate_chunks.py --file "Data\processed\cardiology\DOC-PMC-CARD-0002.chunks.json"

python Scripts\validate_retrieval_eval.py ^
  --eval-path "evaluation\retrieval_eval_multisource_dev_v2.json" ^
  --schema-path "schemas\retrieval_eval_v2.schema.json"

python Scripts\validate_retrieval_eval.py ^
  --eval-path "evaluation\retrieval_eval_multisource_heldout_v1.json" ^
  --schema-path "schemas\retrieval_eval_v2.schema.json"
```

Current source-aware held-out benchmark:

```bat
python Scripts\benchmark_qwen3_embedding_multisource_v2.py ^
  --eval-path "evaluation\retrieval_eval_multisource_heldout_v1.json" ^
  --include-source-labels ^
  --results-name "qwen3_embedding_0.6b_multisource_heldout_v1_source_labels.json"
```

## Engineering principles

- Raw source artifacts are immutable.
- Cleaning is deterministic and non-generative.
- Provenance is preserved from retrieval chunks back to source elements.
- PDF page provenance and XML element provenance are represented separately.
- Retrieval metadata may be semantic without overwriting source-faithful structure.
- Evaluation data stays separate from the retrieval corpus.
- Development and held-out benchmarks remain clearly separated.
- Frozen held-out data is not edited in response to benchmark results.
- Source authority and semantic relevance are treated as separate concerns.
- Unsupported questions should be abstained from rather than forced into an answer.
- Retrieval metrics are not presented as clinical accuracy.

## Next milestone

**Evidence Sufficiency Calibration v1**

The next task is to determine when the retrieved corpus contains enough evidence to support an answer and when MedicalPlab should abstain.

After that:

```text
evidence sufficiency
-> source / authority policy
-> retrieval service
-> grounded generation
-> citation verification
-> adaptive learning
-> API and product integration
```

See `docs/` for the engineering notes and architecture decisions.

## Project stage

Active development. This repository currently represents the validated data and retrieval foundation plus independent retrieval evaluation, not a finished clinical product.

MedicalPlab is an educational system. It is not intended to provide patient-specific diagnosis or treatment decisions.

## Canonical Stage-B candidate

The active verifier is `src/medicalplab/stage_b/`. See [Stage-B](docs/stage_b.md)
for its contracts, limitations, deterministic tests and Colab calibration workflow.
The candidate awaits GPU calibration; historical metrics are not its results.
Use `evaluation/run_stage_b_calibration.py` for both regression and calibration.
