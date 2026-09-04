# Dependency setup

MedicalPlab keeps the core data pipeline and the retrieval stack separated so the repository stays reproducible without forcing a platform-specific GPU package set into the core lockfile.

## Core data pipeline

Create a Python 3.11 environment and install the core project:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
```

Core versions are locked through `pyproject.toml`:

```text
jsonschema 4.26.0
pdfplumber 0.11.10
requests 2.34.2
```

`uv.lock` represents this core project.

## Retrieval environment

The current validated retrieval environment additionally uses:

```text
numpy 2.4.6
sentence-transformers 6.0.1
transformers 5.16.1
accelerate 1.14.0
PyTorch 2.11.0+cu128
```

PyTorch is intentionally not pinned in `pyproject.toml` because the correct build depends on the target hardware and CUDA platform.

Install a PyTorch build appropriate for the machine first, then:

```bat
pip install -r requirements-retrieval.txt
```

Before running GPU benchmarks:

```bat
python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

## Reproducibility notes

- `pyproject.toml` is the source of truth for the core project.
- `uv.lock` locks the core environment.
- `requirements-retrieval.txt` pins the validated retrieval stack.
- GPU-specific PyTorch installation remains platform dependent.
- Raw and processed medical data under `Data/` are intentionally excluded from Git.
