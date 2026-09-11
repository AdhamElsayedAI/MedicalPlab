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
from sentence_transformers import CrossEncoder

MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
reranker = CrossEncoder(MODEL_ID, device="cuda:0", trust_remote_code=True)

print(f"Reranker type: {type(reranker)}")
print(f"Underlying model: {type(reranker.model)}")
print(f"Tokenizer: {type(reranker.tokenizer)}")

# Check modules in underlying model
named_modules = list(reranker.model.named_modules())
print(f"Total named modules: {len(named_modules)}")
for name, mod in named_modules[:15]:
    print(f"  {name}: {type(mod).__name__}")

# Check parameters
total_params = sum(p.numel() for p in reranker.model.parameters())
trainable_params = sum(p.numel() for p in reranker.model.parameters() if p.requires_grad)
print(f"Total params: {total_params:,}")
print(f"Trainable params: {trainable_params:,}")
