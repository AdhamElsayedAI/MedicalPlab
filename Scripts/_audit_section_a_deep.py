import json
from pathlib import Path

ROOT = Path(".")
DEV_A_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"

dev_a = json.loads(DEV_A_PATH.read_text(encoding="utf-8"))

# Load all chunks into a dictionary by chunk_id
chunk_map = {}
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        chunk_map[ch["chunk_id"]] = ch

print("=" * 70)
print("FORENSIC AUDIT OF SECTION A: PARENT-SECTION METRIC INVARIANT")
print("=" * 70)

# 1. Inspect fields of DEV-A items
item0 = dev_a[0]
print(f"Sample DEV-A query item keys: {list(item0.keys())}")
print(f"Sample gold_chunk_ids: {item0.get('gold_chunk_ids')}")
print(f"Sample gold_section_path: {item0.get('gold_section_path')}")
print(f"Sample parent_section_path: {item0.get('parent_section_path')}")
print(f"Has 'gold_parent_section_ids'? {'gold_parent_section_ids' in item0}")

# 2. Check each gold_chunk's parent_section_id and section_path in corpus
all_gold_chunks_valid = True
chunks_with_missing_parent_id = 0
chunks_with_missing_sec_path = 0
total_gold_chunk_refs = 0

for item in dev_a:
    for cid in item["gold_chunk_ids"]:
        total_gold_chunk_refs += 1
        if cid not in chunk_map:
            all_gold_chunks_valid = False
            print(f"ERROR: Gold chunk {cid} not in corpus chunk_map!")
        else:
            ch = chunk_map[cid]
            if not ch.get("parent_section_id"):
                chunks_with_missing_parent_id += 1
            if not ch.get("section_path"):
                chunks_with_missing_sec_path += 1

print(f"\nTotal gold chunk references across 50 DEV-A queries: {total_gold_chunk_refs}")
print(f"Gold chunks valid in corpus: {all_gold_chunks_valid}")
print(f"Gold chunks missing parent_section_id: {chunks_with_missing_parent_id}")
print(f"Gold chunks missing section_path: {chunks_with_missing_sec_path}")

# 3. Compare actual section paths of gold chunks with item['gold_section_path']
print("\nComparing item['gold_section_path'] vs actual chunk['section_path']:")
diff_count = 0
for i, item in enumerate(dev_a):
    cids = item["gold_chunk_ids"]
    actual_sec_paths = [tuple(chunk_map[c].get("section_path", [])) for c in cids if c in chunk_map]
    actual_parent_ids = [chunk_map[c].get("parent_section_id") for c in cids if c in chunk_map]
    item_sec = tuple(item.get("gold_section_path", []))
    
    if item_sec not in actual_sec_paths:
        diff_count += 1

print(f"Queries where item['gold_section_path'] != any gold chunk['section_path']: {diff_count} / {len(dev_a)}")

# 4. Multi-relevance: Do multiple gold chunks for a query have multiple parent sections?
multi_sec_queries = 0
for item in dev_a:
    cids = item["gold_chunk_ids"]
    parent_ids = set(chunk_map[c].get("parent_section_id") for c in cids if c in chunk_map)
    sec_paths = set(tuple(chunk_map[c].get("section_path", [])) for c in cids if c in chunk_map)
    if len(parent_ids) > 1 or len(sec_paths) > 1:
        multi_sec_queries += 1

print(f"Queries where gold chunks span multiple parent sections / section paths: {multi_sec_queries} / {len(dev_a)}")

