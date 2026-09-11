import json
from pathlib import Path

ROOT = Path(".")
DEV_A_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
GOLD_DIAG_PATH = ROOT / "reports" / "renal_v5" / "renal_v5_gold_rank_diagnostic.json"

dev_a = json.loads(DEV_A_PATH.read_text(encoding="utf-8"))
gold_diag = json.loads(GOLD_DIAG_PATH.read_text(encoding="utf-8"))

chunk_map = {}
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        chunk_map[ch["chunk_id"]] = ch

# In gold_diag, we have winning_chunk_id for each query
diag_queries = gold_diag["detailed_query_diagnostics"]

# Compare ParentSectionHit@1 under 3 definitions:
# Def 1: parent_section_id match
# Def 2: section_path[:2] match
# Def 3: full section_path match

p1_count = 0
d1_count = 0
s1_def1 = 0
s1_def2 = 0
s1_def3 = 0

for q in diag_queries:
    qid = q["query_id"]
    gold_cids = q["gold_chunk_ids"]
    gold_did = q["gold_doc_id"]
    winning_cid = q["winning_chunk_id"]
    winning_ch = chunk_map.get(winning_cid)
    
    is_p1 = winning_cid in gold_cids
    is_d1 = winning_ch.get("document_id") == gold_did if winning_ch else False
    if is_p1: p1_count += 1
    if is_d1: d1_count += 1
    
    gold_pids = set(chunk_map[c].get("parent_section_id") for c in gold_cids if c in chunk_map)
    gold_sp_l2 = set(tuple(chunk_map[c].get("section_path", [])[:2]) for c in gold_cids if c in chunk_map)
    gold_sp_full = set(tuple(chunk_map[c].get("section_path", [])) for c in gold_cids if c in chunk_map)
    
    w_pid = winning_ch.get("parent_section_id") if winning_ch else None
    w_sp = winning_ch.get("section_path", []) if winning_ch else []
    w_did = winning_ch.get("document_id") if winning_ch else None
    
    hit_def1 = (w_pid in gold_pids)
    hit_def2 = (w_did == gold_did and tuple(w_sp[:2]) in gold_sp_l2)
    hit_def3 = (w_did == gold_did and tuple(w_sp) in gold_sp_full)
    
    if hit_def1: s1_def1 += 1
    if hit_def2: s1_def2 += 1
    if hit_def3: s1_def3 += 1

print(f"PassageHit@1:  {p1_count} / 50 ({p1_count/50*100:.1f}%)")
print(f"ParentSectionHit@1 (Def 1: parent_section_id): {s1_def1} / 50 ({s1_def1/50*100:.1f}%)")
print(f"ParentSectionHit@1 (Def 2: section_path[:2]):   {s1_def2} / 50 ({s1_def2/50*100:.1f}%)")
print(f"ParentSectionHit@1 (Def 3: exact section_path): {s1_def3} / 50 ({s1_def3/50*100:.1f}%)")
print(f"DocumentHit@1: {d1_count} / 50 ({d1_count/50*100:.1f}%)")
