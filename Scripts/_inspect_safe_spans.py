import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import all_chunks, safe_chunk_ids, norm_sec, all_excluded_sec, all_excluded_window

cids = sorted(list(safe_chunk_ids))
print(f"Total safe chunks: {len(cids)}")

NON_CONTENT_PATTERNS = [
    "acknowledgement", "author contribution", "competing interest", "conflict of interest",
    "data availability", "footnote", "supplementary", "contributor information", "reference",
    "funding", "ethics", "consent"
]

def is_content_section(sec: str) -> bool:
    sec_lower = sec.lower()
    return not any(p in sec_lower for p in NON_CONTENT_PATTERNS)

valid_cids = [cid for cid in cids if is_content_section(norm_sec(all_chunks[cid].get("section_path", [])))]
print(f"Total safe medical content chunks: {len(valid_cids)} / {len(cids)}")

for cid in valid_cids[20:35]:
    ch = all_chunks[cid]
    did = ch["document_id"]
    sec = norm_sec(ch.get("section_path", []))
    text = ch["text"].replace("\n", " ")
    sents = [s.strip() for s in text.split(". ") if 40 < len(s.strip()) < 180]
    if sents:
        print(f"[{cid} | {did} | {sec}]")
        print(f"  Sentence: {sents[0]}.")
