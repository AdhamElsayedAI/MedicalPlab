import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import all_chunks, safe_chunk_ids, all_excluded_sec, all_excluded_window, norm_sec
from curate_clean_train_dataset import ITEMS_SPEC

unsafe_indices = [6, 16, 22, 23, 26, 28, 30, 34, 40, 46, 50, 51, 53, 55, 57, 60, 61, 62, 66, 67, 69, 77]

for idx in unsafe_indices:
    spec = ITEMS_SPEC[idx]
    did = spec["did"]
    strat = spec["stratum"]
    split = spec["split"]
    
    # Find safe chunks in the same document
    doc_safe = []
    for cid in sorted(safe_chunk_ids):
        if cid in all_excluded_window: continue
        ch = all_chunks[cid]
        if ch["document_id"] != did: continue
        sec = norm_sec(ch.get("section_path", []))
        if (did, sec) in all_excluded_sec: continue
        text = ch["text"].strip()
        if len(text) < 200 or text.startswith("Table") or text.startswith("Fig"): continue
        doc_safe.append((cid, sec, text))
        
    print(f"\nItem {idx} ({strat} | {split} | {did}): found {len(doc_safe)} safe replacement chunks in {did}")
    for cid, sec, text in doc_safe[:2]:
        clean_s = text[:150].encode('ascii', 'replace').decode('ascii').replace('\n', ' ')
        print(f"   [{cid} | {sec}]: {clean_s}...")
