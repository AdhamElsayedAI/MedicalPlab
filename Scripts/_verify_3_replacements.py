import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import all_chunks, safe_chunk_ids, all_excluded_sec, all_excluded_window, norm_sec

candidates = [
    ("DOC-PMC-RENAL-0002-B-C0043", "STR-01 | val"),
    ("DOC-PMC-RENAL-0023-B-C0008", "STR-03 | core"),
    ("DOC-PMC-RENAL-0009-B-C0009", "STR-05 | core")
]

for cid, note in candidates:
    ch = all_chunks[cid]
    did = ch["document_id"]
    sec = norm_sec(ch.get("section_path", []))
    is_safe = (cid in safe_chunk_ids and cid not in all_excluded_window and (did, sec) not in all_excluded_sec)
    print(f"[{cid} | {note}] Safe: {is_safe}")
    print(f"  Sec: {sec}")
    print(f"  Text: {ch['text'][:140]}...\n")
