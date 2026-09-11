import json
from pathlib import Path

ROOT = Path(".")
TRAIN_EXT_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-v5-extended.json"
DEV_A_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"

train_items = json.loads(TRAIN_EXT_PATH.read_bytes())
dev_a_items = json.loads(DEV_A_PATH.read_bytes())

shared_chunk_map = {}
for t in train_items:
    t_cids = set(t.get("gold_chunk_ids", []))
    for d in dev_a_items:
        d_cids = set(d.get("gold_chunk_ids", []))
        overlap = t_cids & d_cids
        if overlap:
            for c in overlap:
                shared_chunk_map.setdefault(c, []).append((t, d))

print(f"Total distinct shared chunks between TRAIN and DEV-A: {len(shared_chunk_map)}")

# Print detailed view of first 10 shared chunk instances
for cid, pairs in list(shared_chunk_map.items())[:8]:
    print("=" * 60)
    print(f"SHARED CHUNK: {cid}")
    t, d = pairs[0]
    print(f"  TRAIN [{t['query_id']} | {t['curriculum_stratum']} | {t['query_style']}]:")
    print(f"    Query: {t['query']}")
    print(f"    Claim: {t['canonical_claim']}")
    print(f"    Objective: {t['learning_objective']}")
    print(f"  DEV-A [{d['query_id']} | {d['curriculum_stratum']} | {d['query_style']}]:")
    print(f"    Query: {d['query']}")
    print(f"    Claim: {d['canonical_claim']}")
    print(f"    Objective: {d['learning_objective']}")
