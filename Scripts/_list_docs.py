from pathlib import Path
import json
p = Path("Data/experiments/renal_v2/chunking/B_400_overlap")
for f in sorted(p.glob("*.chunks.json")):
    data = json.loads(f.read_bytes())
    ch0 = data["chunks"][0]
    did = ch0["document_id"]
    t = ch0["text"].replace("\n", " ")[:120]
    print(f"[{did}]: {t}...")
