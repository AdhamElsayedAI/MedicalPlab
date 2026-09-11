"""
Mine Rich Safe Curriculum Items across all 12 Strata
=====================================================
Finds genuine medical/clinical evidence paragraphs from safe unspent chunks
across all 12 strata, excluding administrative sections, tables, and figure captions.
"""

import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import (
    all_chunks, safe_chunk_ids, all_excluded_sec, all_excluded_window, norm_sec
)

NON_CONTENT = [
    "acknowledg", "author", "competing", "conflict", "data avail",
    "footnote", "supplement", "contributor", "reference", "funding", "ethics", "consent"
]

STRATA_DOC_AFFINITY = {
    "STR-01": ["DOC-PMC-RENAL-0002", "DOC-PMC-RENAL-0018", "DOC-PMC-RENAL-0016"],
    "STR-02": ["DOC-PMC-RENAL-0004", "DOC-PMC-RENAL-0019", "DOC-PMC-RENAL-0020"],
    "STR-03": ["DOC-PMC-RENAL-0023", "DOC-PMC-RENAL-0003"],
    "STR-04": ["DOC-PMC-RENAL-0001", "DOC-PMC-RENAL-0024"],
    "STR-05": ["DOC-PMC-RENAL-0003", "DOC-PMC-RENAL-0009", "DOC-PMC-RENAL-0010"],
    "STR-06": ["DOC-PMC-RENAL-0004", "DOC-PMC-RENAL-0005", "DOC-PMC-RENAL-0021"],
    "STR-07": ["DOC-PMC-RENAL-0006", "DOC-PMC-RENAL-0015", "DOC-PMC-RENAL-0016"],
    "STR-08": ["DOC-PMC-RENAL-0007", "DOC-PMC-RENAL-0001"],
    "STR-09": ["DOC-PMC-RENAL-0008", "DOC-PMC-RENAL-0025", "DOC-PMC-RENAL-0002"],
    "STR-10": ["DOC-PMC-RENAL-0011", "DOC-PMC-RENAL-0014"],
    "STR-11": ["DOC-PMC-RENAL-0012", "DOC-PMC-RENAL-0013"],
    "STR-12": ["DOC-PMC-RENAL-0006", "DOC-PMC-RENAL-0007", "DOC-PMC-RENAL-0016", "DOC-PMC-RENAL-0024"]
}

def is_good_clinical_chunk(ch):
    sec = norm_sec(ch.get("section_path", []))
    if any(nc in sec for nc in NON_CONTENT):
        return False
    text = ch["text"].strip()
    if len(text) < 200:
        return False
    if text.startswith("Table ") or text.startswith("Fig. ") or text.startswith("Figure "):
        return False
    return True

def get_candidates():
    strat_pools = {s: [] for s in STRATA_DOC_AFFINITY}
    for cid in sorted(safe_chunk_ids):
        if cid in all_excluded_window:
            continue
        ch = all_chunks[cid]
        did = ch["document_id"]
        sec = norm_sec(ch.get("section_path", []))
        if (did, sec) in all_excluded_sec:
            continue
        if not is_good_clinical_chunk(ch):
            continue

        for strat, doc_list in STRATA_DOC_AFFINITY.items():
            if did in doc_list:
                strat_pools[strat].append({
                    "chunk_id": cid,
                    "document_id": did,
                    "section_path": ch.get("section_path", []),
                    "text": ch["text"]
                })
    return strat_pools

if __name__ == "__main__":
    pools = get_candidates()
    for s, cands in pools.items():
        print(f"Stratum {s}: {len(cands)} high-quality safe clinical chunks")
