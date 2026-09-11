import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import all_chunks, safe_chunk_ids, all_excluded_sec, all_excluded_window, norm_sec

def get_candidates_for_doc(did, min_len=200):
    res = []
    for cid in sorted(safe_chunk_ids):
        if cid in all_excluded_window: continue
        ch = all_chunks[cid]
        if ch["document_id"] != did: continue
        sec = norm_sec(ch.get("section_path", []))
        if (did, sec) in all_excluded_sec: continue
        t = ch["text"].strip()
        if len(t) < min_len or t.startswith("Table") or t.startswith("Fig"): continue
        res.append((cid, sec, t))
    return res

docs_needed = [
    ("STR-01", "DOC-PMC-RENAL-0002"),
    ("STR-03", "DOC-PMC-RENAL-0023"),
    ("STR-04", "DOC-PMC-RENAL-0024"),
    ("STR-05", "DOC-PMC-RENAL-0003"),
    ("STR-05", "DOC-PMC-RENAL-0010"),
    ("STR-05", "DOC-PMC-RENAL-0009"),
    ("STR-06", "DOC-PMC-RENAL-0005"),
    ("STR-07", "DOC-PMC-RENAL-0015"),
    ("STR-08", "DOC-PMC-RENAL-0007"),
    ("STR-09", "DOC-PMC-RENAL-0008"),
    ("STR-09", "DOC-PMC-RENAL-0025"),
    ("STR-10", "DOC-PMC-RENAL-0011"),
    ("STR-10", "DOC-PMC-RENAL-0014"),
    ("STR-11", "DOC-PMC-RENAL-0012"),
    ("STR-11", "DOC-PMC-RENAL-0013"),
]

for strat, did in docs_needed:
    cands = get_candidates_for_doc(did)
    print(f"\n=== {strat} | {did} ({len(cands)} safe chunks) ===")
    for cid, sec, t in cands[2:4]:
        clean_t = t[:180].encode('ascii', 'replace').decode('ascii').replace('\n', ' ')
        print(f"  [{cid} | {sec}]: {clean_t}...")
