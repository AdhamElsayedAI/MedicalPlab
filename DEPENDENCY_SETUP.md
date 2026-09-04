# Dependency setup

MedicalPlab currently contains two generations of the project:

1. the active governed data/retrieval pipeline;
2. the original FastAPI/Streamlit prototype.

They are intentionally not locked into the same environment.

## Why they are separated

The current pipeline uses:

```text
pdfplumber 0.11.10
```

which requires:

```text
Pillow >=12.2.0
```

The original prototype used:

```text
streamlit 1.47.0
```

which requires:

```text
Pillow <12
```

Those constraints are incompatible. Keeping the legacy UI in the main
`pyproject.toml` would make the project lock unsatisfiable.

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

## Retrieval environment

The current validated retrieval environment additionally uses:

```text
numpy 2.4.6
sentence-transformers 6.0.1
transformers 5.16.1
accelerate 1.14.0
PyTorch 2.11.0+cu128
```

PyTorch is intentionally not pinned in `pyproject.toml` because the correct
build depends on the target hardware and CUDA platform.

Install a PyTorch build appropriate for the machine first, then:

```bat
pip install -r requirements-retrieval.txt
```

Before running GPU benchmarks:

```bat
python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

## Legacy prototype

If the old FastAPI/Streamlit prototype is needed, create a separate
environment:

```bat
py -3.11 -m venv .venv-legacy
.venv-legacy\Scripts\activate
pip install -r requirements-legacy.txt
```

Do not install `requirements-legacy.txt` into the active retrieval/data
environment.

## uv.lock

`uv.lock` represents the core project declared in `pyproject.toml`.

GPU-specific retrieval packages and the legacy UI are documented and pinned
separately because they have platform-specific or mutually incompatible
constraints.
