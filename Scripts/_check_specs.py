import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import (
    all_chunks, safe_chunk_ids, all_excluded_sec, all_excluded_window, norm_sec
)
from curate_clean_train_dataset import ITEMS_SPEC

print("Checking specifications against safe unspent registry...")
unsafe = []
for i, spec in enumerate(ITEMS_SPEC):
    cid = spec["cid"]
    did = spec["did"]
    ch = all_chunks.get(cid)
    if not ch:
        unsafe.append((i, spec, f"Chunk {cid} not found"))
        continue
    sec = norm_sec(ch.get("section_path", []))
    if cid not in safe_chunk_ids:
        unsafe.append((i, spec, "cid not in safe_chunk_ids"))
    elif cid in all_excluded_window:
        unsafe.append((i, spec, "cid in all_excluded_window"))
    elif (did, sec) in all_excluded_sec:
        unsafe.append((i, spec, f"section ({did}, {sec}) in all_excluded_sec"))

print(f"Total unsafe specs: {len(unsafe)} / {len(ITEMS_SPEC)}")
for i, spec, reason in unsafe:
    print(f"  Item {i} ({spec['stratum']} | {spec['split']}): {spec['cid']} -> {reason}")
