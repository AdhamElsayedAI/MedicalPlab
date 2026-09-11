import json
from pathlib import Path

ROOT = Path(".")
DEV_A_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"

dev_a = json.loads(DEV_A_PATH.read_text(encoding="utf-8"))

# Load all chunks
chunk_map = {}
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        chunk_map[ch["chunk_id"]] = ch

print(f"Total dev_a queries: {len(dev_a)}")
print(f"Total corpus chunks: {len(chunk_map)}")

matches = 0
mismatches = 0

for i, item in enumerate(dev_a):
    gold_cids = item["gold_chunk_ids"]
    gold_sec_in_item = item.get("gold_section_path")
    # check the section_path in the actual chunks
    chunk_sec_paths = [chunk_map[cid].get("section_path") for cid in gold_cids if cid in chunk_map]
    
    # Are they equal?
    eq = all(sp == gold_sec_in_item for sp in chunk_sec_paths)
    if eq:
        matches += 1
    else:
        mismatches += 1
        if mismatches <= 5:
            print(f"\n--- Item {i} ({item['query_id']}) ---")
            print(f"  gold_doc_id in item: {item['gold_doc_id']}")
            print(f"  gold_section_path in item: {gold_sec_in_item}")
            print(f"  gold_chunk_ids: {gold_cids}")
            for cid in gold_cids:
                if cid in chunk_map:
                    ch = chunk_map[cid]
                    print(f"    chunk {cid} doc_id: {ch.get('document_id')}, sec_path: {ch.get('section_path')}")

print(f"\nSummary across {len(dev_a)} queries:")
print(f"  Matches between item['gold_section_path'] and chunk['section_path']: {matches}")
print(f"  Mismatches: {mismatches}")
