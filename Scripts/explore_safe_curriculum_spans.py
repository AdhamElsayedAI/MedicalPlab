import json
import re
from pathlib import Path

chunks_dir = Path("Data/experiments/renal_v2/chunking/B_400_overlap")
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
    if not p: return ""
    if isinstance(p, list): return " > ".join(s.strip().lower() for s in p)
    return str(p).strip().lower()

dev_a_sec = set((it["source_document_id"], norm_sec(it.get("parent_section_path", []))) for it in dev_a)
dev_b_sec = set((it["source_document_id"], norm_sec(it.get("parent_section_path", []))) for it in dev_b)
all_excluded_sec = dev_a_sec | dev_b_sec

safe_chunks = []
for p in sorted(chunks_dir.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        cid = ch["chunk_id"]
        did = ch["document_id"]
        sec = norm_sec(ch.get("section_path", []))
        if cid in all_excluded_window or (did, sec) in all_excluded_sec:
            continue
        safe_chunks.append(ch)

print(f"Total safe chunks: {len(safe_chunks)}")

def search_safe(term, doc_id=None, limit=5):
    term_l = term.lower()
    matches = []
    for ch in safe_chunks:
        if doc_id and ch["document_id"] != doc_id:
            continue
        if term_l in ch["text"].lower():
            matches.append(ch)
            if len(matches) >= limit:
                break
    return matches

# Test search
m = search_safe("patiromer", limit=2)
for ch in m:
    print(ch["chunk_id"], ch["document_id"], ch.get("section_path"))
    print(ch["text"][:150].replace("\n", " "))
    print("-" * 40)
