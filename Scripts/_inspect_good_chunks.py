import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))
from build_clean_train_v1 import all_chunks, safe_chunk_ids, norm_sec

NON_CONTENT = ["acknowledg", "author", "competing", "conflict", "data avail", "footnote", "supplement", "contributor", "reference", "funding", "ethics", "consent"]

def is_good_chunk(ch):
    sec = norm_sec(ch.get("section_path", []))
    if any(nc in sec for nc in NON_CONTENT): return False
    text = ch["text"].strip()
    if len(text) < 250: return False
    if "Table " in text[:30] or "Fig. " in text[:30]: return False
    return True

good_safe_cids = [cid for cid in sorted(safe_chunk_ids) if is_good_chunk(all_chunks[cid])]
print(f"Total high-quality medical safe chunks: {len(good_safe_cids)}")

for cid in good_safe_cids[:10]:
    ch = all_chunks[cid]
    clean_txt = ch['text'][:250].encode('ascii', 'replace').decode('ascii').replace('\n', ' ')
    print(f"[{cid} | {ch['document_id']} | {norm_sec(ch.get('section_path', []))}]")
    print(f"  {clean_txt}...\n")
