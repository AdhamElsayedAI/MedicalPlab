import sys
from pathlib import Path

_RENAL_ENV = Path(".renal_env")
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))

for mod in ["torch", "transformers", "sentence_transformers", "peft", "bitsandbytes", "accelerate", "trl", "optimum"]:
    try:
        m = __import__(mod)
        ver = getattr(m, "__version__", "installed")
        print(f"{mod}: {ver}")
    except ImportError as e:
        print(f"{mod}: NOT INSTALLED ({e})")
