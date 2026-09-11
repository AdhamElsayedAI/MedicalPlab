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

import inspect
import torch
from sentence_transformers import CrossEncoder

MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
reranker = CrossEncoder(MODEL_ID, device="cuda:0", trust_remote_code=True)

# Inspect how CrossEncoder predicts
print("predict method signature:")
print(inspect.signature(reranker.predict))

# Run 1 sample prediction and inspect intermediate tensors
query = "What is the function of podocytes?"
text = "Podocytes maintain the glomerular filtration barrier."
features = reranker.tokenizer([[query, text]], padding=True, truncation=True, return_tensors="pt").to("cuda:0")

with torch.no_grad():
    out = reranker.model(**features)
    print("out keys:", out.keys() if hasattr(out, "keys") else dir(out))
    if hasattr(out, "logits"):
        print("logits shape:", out.logits.shape)
        print("logits sample:", out.logits[:, -1, :10])
