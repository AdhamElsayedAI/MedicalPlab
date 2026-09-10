"""Analyze gold chunk IDs in ablation failures vs current B_400_overlap chunks."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

abl = json.loads((ROOT / "reports/renal_v2_ablation.json").read_text())
failures = abl.get("final_failures", [])

B_dir = ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
chunk_map = {}
for f in sorted(B_dir.glob("*.chunks.json")):
    for ch in json.loads(f.read_text())["chunks"]:
        chunk_map[ch["chunk_id"]] = ch

C_dir = ROOT / "Data/experiments/renal_v2/chunking/C_section_aware"
section_map = {}
for f in sorted(C_dir.glob("*.chunks.json")):
    for ch in json.loads(f.read_text())["chunks"]:
        section_map[ch["chunk_id"]] = ch

dev = json.loads((ROOT / "evaluation/renal/renal-dev-v2.json").read_text())
queries = {q["query_id"]: q for q in dev["queries"] if q.get("answerable")}

print("GOLD CHUNK ID vs B_400_OVERLAP CHUNK MATCH ANALYSIS")
print("=" * 60)
print()

found_count = 0
not_found = 0
gold_chunk_id_formats = []
b_chunk_id_formats = []

for failure in failures[:5]:
    qid = failure["query_id"]
    q = queries.get(qid, {})
    gold_chunk_ids = q.get("gold_child_chunk_ids", [])
    gold_parent_ids = q.get("gold_parent_section_ids", [])
    print(f"Query: {qid}")
    print(f"  gold_child_chunk_ids: {gold_chunk_ids}")
    for gid in gold_chunk_ids:
        if gid in chunk_map:
            print(f"  FOUND in B_400: {gid} ({len(chunk_map[gid].get('text','').split())} words)")
            found_count += 1
        elif gid in section_map:
            print(f"  FOUND in C_section: {gid} ({len(section_map[gid].get('text','').split())} words)")
            found_count += 1
        else:
            print(f"  NOT FOUND: {gid}")
            not_found += 1
    top1 = failure["top_10"][0] if failure["top_10"] else {}
    print(f"  top_retrieved: {top1.get('chunk_id','?')} parent={top1.get('parent_section_id','?')}")
    print(f"  gold_parent_section_ids: {gold_parent_ids}")
    print()

# Look at all gold chunk ID formats
print()
print("GOLD CHUNK ID FORMAT ANALYSIS (all failures):")
all_gold_ids = []
for failure in failures:
    qid = failure["query_id"]
    q = queries.get(qid, {})
    gold_ids = q.get("gold_child_chunk_ids", [])
    all_gold_ids.extend(gold_ids)
    for gid in gold_ids:
        if gid in chunk_map:
            found_count += 1
        else:
            not_found += 1

print(f"Total gold chunk IDs in failures: {len(all_gold_ids)}")
print(f"Found in B_400_overlap: {found_count - (found_count - len(all_gold_ids))}")
print(f"NOT FOUND in B_400_overlap: {not_found}")
if all_gold_ids:
    print(f"Sample gold IDs: {all_gold_ids[:5]}")
    print(f"Sample B_400 IDs: {list(chunk_map.keys())[:5]}")
