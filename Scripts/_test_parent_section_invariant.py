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

queries = gold_diag["detailed_query_diagnostics"]
print(f"Total diagnostic queries: {len(queries)}")

p1_hits = 0
sec_hits_pid = 0
sec_hits_sp = 0
invariant_violations = []

for q in queries:
    qid = q["query_id"]
    gold_cids = q["gold_chunk_ids"]
    winning_cid = q["winning_chunk_id"]
    winning_ch = chunk_map.get(winning_cid)
    winning_pid = winning_ch.get("parent_section_id") if winning_ch else None
    winning_sp = winning_ch.get("section_path") if winning_ch else None
    
    gold_pids = set(chunk_map[c].get("parent_section_id") for c in gold_cids if c in chunk_map)
    gold_sps = set(tuple(chunk_map[c].get("section_path", [])[:2]) for c in gold_cids if c in chunk_map)
    
    pid_match = winning_pid in gold_pids
    sp_match = tuple(winning_sp[:2]) in gold_sps if winning_sp else False
    is_p1 = winning_cid in gold_cids
    
    if is_p1:
        p1_hits += 1
        if not pid_match:
            invariant_violations.append((qid, "pid_match is False when PassageHit@1 is True"))
        if not sp_match:
            invariant_violations.append((qid, "sp_match is False when PassageHit@1 is True"))
            
    if pid_match:
        sec_hits_pid += 1
    if sp_match:
        sec_hits_sp += 1

print(f"\nPassageHit@1: {p1_hits} / 50 ({p1_hits/50*100:.1f}%)")
print(f"ParentSectionHit@1 (by parent_section_id): {sec_hits_pid} / 50 ({sec_hits_pid/50*100:.1f}%)")
print(f"ParentSectionHit@1 (by section_path[:2]): {sec_hits_sp} / 50 ({sec_hits_sp/50*100:.1f}%)")
print(f"Invariant violations where PassageHit@1 == True but ParentSectionHit@1 == False: {len(invariant_violations)}")
if invariant_violations:
    for v in invariant_violations:
        print("  Violation:", v)
else:
    print("  PERFECT INVARIANT: For EVERY query with PassageHit@1 == True, ParentSectionHit@1 is ALSO True!")

# Compare with the previous buggy metric
print("\nPrevious buggy metric had ParentSectionHit@1 = 2 / 50 (4.0%) because it checked:")
print("  ch['section_path'][:2] == item['gold_section_path'][:2]")
print("where item['gold_section_path'] was a handwritten conceptual label, NOT the actual corpus section path!")
