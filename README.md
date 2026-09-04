# MedicalPlab

MedicalPlab is an evidence-grounded medical learning platform focused on reliable retrieval before generation.

The current codebase is building the data and retrieval foundation for an adaptive medical education system: governed source acquisition, structure-aware extraction, canonical medical content, provenance-preserving chunking, multilingual retrieval, and document-aware evaluation.

The generation layer is intentionally not the center of the project yet. Retrieval quality, source traceability, and evaluation are being validated first.

## Current status

The active retrieval corpus currently contains two independently processed cardiology sources:

| Source | Ingestion path | Validated chunks |
| --- | --- | ---: |
| WHO hypertension guideline | PDF -> extraction -> cleaning -> structure parsing | 83 |
| PMC hypertension review | PMC JATS XML -> structured extraction -> canonical adapter | 144 |
| **Combined corpus** | Multi-document retrieval | **227** |

Current dense retriever: `Qwen/Qwen3-Embedding-0.6B`

Latest multi-document DEV regression:

| Metric | Score |
| --- | ---: |
| Hit@1 | 1.0000 |
| Recall@1 | 0.4697 |
| Recall@3 | 0.7197 |
| Recall@5 | 0.7652 |
| Recall@10 | 0.8864 |
| MRR | 1.0000 |
| nDCG@10 | 0.8821 |

> These numbers are from a development regression set, not a held-out final benchmark. The current multi-document DEV set keeps WHO-scoped gold evidence while the PMC review acts as a semantically similar hard distractor.

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
        Dense / hybrid retrieval
                |
                v
        Document-aware evaluation
                |
                v
        RAG generation  [next]
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
+-- main.py
+-- streamlit_app.py
+-- pyproject.toml
+-- requirements.txt
```

`main.py`, `streamlit_app.py`, and the older Plabable/University retrieval scripts belong to the original prototype layer. They are retained for continuity while the active engineering work moves toward the governed retrieval and RAG architecture.

## Environment

Recommended:

- Python 3.11
- Windows, Linux, or macOS for the data pipeline
- NVIDIA CUDA-capable GPU for the current Qwen3 dense benchmark script

Windows setup:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
```

Verify CUDA before running the dense benchmark:

```bat
python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

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

python Scripts\validate_retrieval_eval.py --eval-path "evaluation\retrieval_eval_v1.json"
python Scripts\validate_retrieval_eval.py --eval-path "evaluation\retrieval_eval_multidoc_dev_v1.json"
```

Current multi-document dense regression:

```bat
python Scripts\benchmark_qwen3_embedding_multidoc.py ^
  --documents DOC-WHO-CARD-0001 DOC-PMC-CARD-0002 ^
  --eval-path "evaluation\retrieval_eval_multidoc_dev_v1.json" ^
  --results-name "qwen3_embedding_0.6b_multidoc_semantic_paths_v2.json"
```

## Engineering principles

- Raw source artifacts are immutable.
- Cleaning is deterministic and non-generative.
- Provenance is preserved from retrieval chunks back to source elements.
- PDF page provenance and XML element provenance are represented separately.
- Retrieval metadata may be semantic without overwriting source-faithful structure.
- Evaluation data stays separate from the retrieval corpus.
- Development benchmarks are labeled as development benchmarks.
- Source authority and semantic relevance are treated as separate concerns.
- Unsupported questions should eventually be abstained from rather than forced into an answer.

## Next milestone

Build a real multi-source evaluation set containing WHO-targeted, PMC-targeted, shared-evidence, Arabic, English, mixed-language, source-selection, hard-negative, and unsupported cases.

After that: held-out evaluation, larger corpus ingestion, source-authority policy, vector indexing, retrieval service, evidence-grounded generation, citations, confidence/abstention, and API integration.

See `docs/` for the working engineering notes.

## Project stage

Active development. This repository currently represents the validated data and retrieval foundation, not a finished clinical product.

MedicalPlab is an educational system. It is not intended to provide patient-specific diagnosis or treatment decisions.
