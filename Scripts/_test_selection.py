import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import (
    all_chunks, safe_chunk_ids, all_excluded_sec, all_excluded_window, 
    norm_sec
)
from mine_exact_safe_spans import mine_candidates
import re

QUOTAS = {
    "STR-01": 7, "STR-02": 7, "STR-03": 6, "STR-04": 6,
    "STR-05": 7, "STR-06": 6, "STR-07": 7, "STR-08": 7,
    "STR-09": 7, "STR-10": 6, "STR-11": 7, "STR-12": 7
}
assert sum(QUOTAS.values()) == 80

def get_num(cid: str) -> int:
    m = re.search(r"-C(\d+)$", cid)
    return int(m.group(1)) if m else -1

def get_pfx(cid: str) -> str:
    m = re.match(r"(DOC-PMC-RENAL-\d+-B)-C\d+$", cid)
    return m.group(1) if m else cid

def expand_cid(cid):
    pfx = get_pfx(cid)
    num = get_num(cid)
    return {f"{pfx}-C{num-1:04d}", f"{pfx}-C{num:04d}", f"{pfx}-C{num+1:04d}"}

cands = mine_candidates()

core_items = []
val_items = []
core_chunks = set()
core_win = set()
core_secs = set()
val_chunks = set()
val_win = set()
val_secs = set()

for strat, quota in QUOTAS.items():
    strat_cands = cands[strat]
    n_core = 5
    n_val = quota - n_core
    
    # Stratum candidate pool
    pool = []
    for c in strat_cands:
        cid = c["chunk_id"]
        did = c["document_id"]
        term = c["term"].lower()
        ch = all_chunks[cid]
        sec = norm_sec(ch.get("section_path", []))
        if cid not in safe_chunk_ids or cid in all_excluded_window or (did, sec) in all_excluded_sec:
            continue
        text = ch["text"]
        pos = text.lower().find(term)
        if pos == -1: continue
        start = text.rfind(". ", 0, pos)
        start = start + 2 if start != -1 else 0
        end = text.find(". ", pos)
        end = end + 1 if end != -1 else len(text)
        span = text[start:end].strip()
        if len(span) < 30:
            span = text[max(0, pos-40):min(len(text), pos+140)].strip()
        if span not in text: continue
        pool.append((c, span, did, sec, term, cid))

    # Pick 5 for core, n_val for val such that terms, sections, and windows are disjoint
    sel_core = []
    sel_core_terms = set()
    for c, span, did, sec, term, cid in pool:
        if term in sel_core_terms: continue
        if cid in core_chunks or cid in core_win or cid in val_chunks or cid in val_win: continue
        if (did, sec) in val_secs: continue
        
        sel_core.append((c, span, did, sec, term, cid))
        sel_core_terms.add(term)
        core_chunks.add(cid)
        core_win.update(expand_cid(cid))
        core_secs.add((did, sec))
        if len(sel_core) == n_core:
            break
            
    assert len(sel_core) == n_core, f"Failed core for {strat}: got {len(sel_core)}"
    
    sel_val = []
    sel_val_terms = set()
    for c, span, did, sec, term, cid in pool:
        if term in sel_core_terms or term in sel_val_terms: continue
        if cid in core_chunks or cid in core_win or cid in val_chunks or cid in val_win: continue
        if (did, sec) in core_secs: continue
        
        sel_val.append((c, span, did, sec, term, cid))
        sel_val_terms.add(term)
        val_chunks.add(cid)
        val_win.update(expand_cid(cid))
        val_secs.add((did, sec))
        if len(sel_val) == n_val:
            break
            
    assert len(sel_val) == n_val, f"Failed val for {strat}: got {len(sel_val)}"
    core_items.extend(sel_core)
    val_items.extend(sel_val)

print(f"SUCCESS: Core N={len(core_items)}, Val N={len(val_items)}")
print(f"Core/Val Section Overlap: {len(core_secs & val_secs)}")
print(f"Core/Val Chunk Overlap:   {len(core_chunks & val_chunks)}")
print(f"Core Win / Val Overlap:   {len(core_win & val_chunks)}")
print(f"Val Win / Core Overlap:   {len(val_win & core_chunks)}")
