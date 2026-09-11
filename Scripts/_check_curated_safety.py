import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import safe_chunk_ids, all_excluded_window, all_excluded_sec, norm_sec, all_chunks
from build_clean_train_v1_verified import CURATED_ITEMS

print("Checking CURATED_ITEMS safety...")
unsafe = []
for i, it in enumerate(CURATED_ITEMS):
    cid = it["cid"]
    did = it["did"]
    ch = all_chunks.get(cid)
    sec = norm_sec(ch.get("section_path", [])) if ch else "UNKNOWN"
    if cid not in safe_chunk_ids:
        unsafe.append((i, it, "NOT in safe_chunk_ids"))
    elif cid in all_excluded_window:
        unsafe.append((i, it, "in all_excluded_window"))
    elif (did, sec) in all_excluded_sec:
        unsafe.append((i, it, f"({did}, {sec}) in all_excluded_sec"))

print(f"Total unsafe: {len(unsafe)} / {len(CURATED_ITEMS)}")
for i, it, reason in unsafe:
    print(f"  Item {i} ({it['stratum']} | {it['split']}): {it['cid']} -> {reason}")
