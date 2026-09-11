import json
import re
from pathlib import Path

train = json.loads(Path("evaluation/renal/v5/renal-rerank-train-v5-extended.json").read_text(encoding="utf-8"))
dev_a = json.loads(Path("evaluation/renal/v5/renal-rerank-dev-a-v5.json").read_text(encoding="utf-8"))
dev_b = json.loads(Path("evaluation/renal/v5/renal-rerank-dev-b-v5.json").read_text(encoding="utf-8"))

dev_a_gold = set(c for it in dev_a for c in it.get("gold_chunk_ids", []))
dev_b_gold = set(c for it in dev_b for c in it.get("gold_chunk_ids", []))
all_excluded_gold = dev_a_gold | dev_b_gold

def get_num(cid):
    m = re.search(r"-C(\d+)$", cid)
    return int(m.group(1)) if m else -1

def get_pfx(cid):
    m = re.match(r"(DOC-PMC-RENAL-\d+-B)-C\d+$", cid)
    return m.group(1) if m else cid

all_excluded_window = set(all_excluded_gold)
for cid in all_excluded_gold:
    num = get_num(cid)
    pfx = get_pfx(cid)
    if num != -1:
        all_excluded_window.add(f"{pfx}-C{num-1:04d}")
        all_excluded_window.add(f"{pfx}-C{num+1:04d}")

def norm_sec(p):
    if not p:
        return ""
    if isinstance(p, list):
        return " > ".join(s.strip().lower() for s in p)
    return str(p).strip().lower()

dev_a_sec = set((it["source_document_id"], norm_sec(it.get("parent_section_path", []))) for it in dev_a)
dev_b_sec = set((it["source_document_id"], norm_sec(it.get("parent_section_path", []))) for it in dev_b)
all_excluded_sec = dev_a_sec | dev_b_sec

true_dup_ids = {
    "V5-RNK-TRAIN-0006", "V5-RNK-TRAIN-0008", "V5-RNK-TRAIN-0010", 
    "V5-RNK-TRAIN-0011", "V5-RNK-TRAIN-0012", "V5-RNK-TRAIN-0014", "V5-RNK-TRAIN-0016"
}

clean_items = []
contaminated_items = []

for it in train:
    qid = it["query_id"]
    cids = it.get("gold_chunk_ids", [])
    sec = norm_sec(it.get("parent_section_path", []))
    did = it["source_document_id"]
    
    reasons = []
    if qid in true_dup_ids:
        reasons.append("TRUE_SEMANTIC_DUPLICATE")
    if (did, sec) in all_excluded_sec:
        reasons.append("EXCLUDED_SECTION")
    overlap_gold = [c for c in cids if c in all_excluded_gold]
    if overlap_gold:
        reasons.append(f"GOLD_CHUNK_OVERLAP:{overlap_gold}")
    overlap_win = [c for c in cids if c in all_excluded_window and c not in all_excluded_gold]
    if overlap_win:
        reasons.append(f"ADJACENT_WINDOW_OVERLAP:{overlap_win}")
        
    if reasons:
        contaminated_items.append((qid, it["curriculum_stratum"], it["query"], reasons))
    else:
        clean_items.append(qid)

print(f"Completely clean items in extended train: {len(clean_items)} / 80")
print(f"Items needing replacement or chunk re-grounding: {len(contaminated_items)} / 80")
print("\nItems needing action:")
for it in contaminated_items:
    print(f"  {it[0]} ({it[1]}): {it[3]} | \"{it[2][:50]}...\"")
