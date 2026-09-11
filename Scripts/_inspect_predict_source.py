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
from sentence_transformers import CrossEncoder

MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
reranker = CrossEncoder(MODEL_ID, device="cuda:0", trust_remote_code=True)

# Print source code of predict
src = inspect.getsource(reranker.predict)
print(src[:2000])
