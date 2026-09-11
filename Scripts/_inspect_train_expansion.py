import json
from pathlib import Path

ROOT = Path(".")
REG_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
DEV_A_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
DEV_B_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-b-v5.json"
TRAIN_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-v5.json"

reg = json.loads(REG_PATH.read_text(encoding="utf-8"))
docs = [d for d in reg["documents"] if d.get("status") == "accepted"]

print(f"Total accepted documents: {len(docs)}")
for d in docs:
    did = d["document_id"]
    title = d.get("title", "")[:60]
    tags = d.get("topic_tags", [])
    print(f"  {did}: {title} | {tags}")

dev_a = json.loads(DEV_A_PATH.read_text(encoding="utf-8"))
dev_b = json.loads(DEV_B_PATH.read_text(encoding="utf-8"))
train = json.loads(TRAIN_PATH.read_text(encoding="utf-8"))

print(f"\nCurrent counts: TRAIN={len(train)}, DEV-A={len(dev_a)}, DEV-B={len(dev_b)}")

# Let's see stratum distribution in TRAIN
from collections import Counter
print("Current TRAIN strata:", Counter(i["curriculum_stratum"] for i in train))
