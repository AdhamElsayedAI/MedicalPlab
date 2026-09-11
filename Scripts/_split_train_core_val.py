import hashlib
import json
from pathlib import Path

ROOT = Path(".")
EXTENDED_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-v5-extended.json"

train_items = json.loads(EXTENDED_PATH.read_bytes())
assert len(train_items) == 80, f"Expected 80 items, got {len(train_items)}"

# Stratify by stratum
by_stratum = {}
for it in train_items:
    strat = it["curriculum_stratum"]
    by_stratum.setdefault(strat, []).append(it)

train_core = []
train_val = []

for strat in sorted(by_stratum.keys()):
    items = by_stratum[strat]
    # Deterministcally: first 5 items go to TRAIN_CORE, remaining (1 or 2) go to TRAIN_VAL
    core_subset = items[:5]
    val_subset = items[5:]
    assert len(core_subset) == 5
    assert len(val_subset) in [1, 2]
    train_core.extend(core_subset)
    train_val.extend(val_subset)

assert len(train_core) == 60, f"Expected 60 core items, got {len(train_core)}"
assert len(train_val) == 20, f"Expected 20 val items, got {len(train_val)}"

# Check stratum representation
for strat in sorted(by_stratum.keys()):
    c_count = sum(1 for it in train_core if it["curriculum_stratum"] == strat)
    v_count = sum(1 for it in train_val if it["curriculum_stratum"] == strat)
    assert c_count == 5, f"Stratum {strat} core count {c_count} != 5"
    assert v_count >= 1, f"Stratum {strat} val count {v_count} < 1"

# Save TRAIN_CORE
core_path = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-core-v5.json"
core_bytes = json.dumps(train_core, indent=2, ensure_ascii=False).encode("utf-8")
core_path.write_bytes(core_bytes)
core_sha = hashlib.sha256(core_bytes).hexdigest()

# Save TRAIN_VAL
val_path = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-val-v5.json"
val_bytes = json.dumps(train_val, indent=2, ensure_ascii=False).encode("utf-8")
val_path.write_bytes(val_bytes)
val_sha = hashlib.sha256(val_bytes).hexdigest()

print("=" * 60)
print("TRAIN_CORE / TRAIN_VAL SPLIT COMPLETE")
print("=" * 60)
print(f"TRAIN_CORE: N={len(train_core)} queries")
print(f"  Path:   {core_path}")
print(f"  SHA256: {core_sha}")
print(f"TRAIN_VAL:  N={len(train_val)} queries")
print(f"  Path:   {val_path}")
print(f"  SHA256: {val_sha}")

# Check query disjointness
core_qids = set(it["query_id"] for it in train_core)
val_qids = set(it["query_id"] for it in train_val)
assert len(core_qids & val_qids) == 0, "Query ID overlap between CORE and VAL!"
print("Disjointness check: PASS (0 overlapping queries)")
