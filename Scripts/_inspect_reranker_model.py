import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
from transformers import AutoConfig, AutoTokenizer, AutoModelForSequenceClassification

MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"

config = AutoConfig.from_pretrained(MODEL_ID, local_files_only=True)
print(f"Model type: {config.model_type}")
print(f"Architectures: {config.architectures}")
print(f"num_labels: {getattr(config, 'num_labels', None)}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
print(f"Tokenizer class: {type(tokenizer).__name__}")
print(f"Max length: {tokenizer.model_max_length}")

# Check PEFT availability
try:
    import peft
    print(f"PEFT version: {peft.__version__}")
except ImportError as e:
    print(f"PEFT not installed: {e}")
