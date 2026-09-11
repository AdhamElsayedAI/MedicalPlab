import json
from pathlib import Path

ROOT = Path(".")
DEV_A_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
DEPTH_DIAG_PATH = ROOT / "reports" / "renal_v5" / "renal_v5_depth_diagnostic.json"
BASE_PATH = ROOT / "reports" / "renal_v5" / "renal_v5_baseline_dev_a.json"

dev_a = json.loads(DEV_A_PATH.read_text(encoding="utf-8"))
chunk_map = {}
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        chunk_map[ch["chunk_id"]] = ch

# Let's inspect base report
base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
print("Current base report metrics:")
for k, v in base.get("metrics", {}).items():
    print(f"  {k}: {v}")
