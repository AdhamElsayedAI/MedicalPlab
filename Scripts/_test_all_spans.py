import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import all_chunks
from build_clean_train_v1_verified import CURATED_ITEMS

failed = []
for i, it in enumerate(CURATED_ITEMS):
    cid = it["cid"]
    term = it["span_term"]
    text = all_chunks[cid]["text"]
    
    pos = text.lower().find(term.lower())
    if pos != -1:
        start = text.rfind(". ", 0, pos)
        start = start + 2 if start != -1 else 0
        end = text.find(". ", pos + len(term))
        end = end + 1 if end != -1 else len(text)
        span = text[start:end].strip()
    else:
        span = text.split(". ")[0].strip() + "."
        
    if span not in text:
        failed.append((i, cid, term, "span not in text"))
    elif len(span) < 30:
        failed.append((i, cid, term, f"span too short: {len(span)}"))

print(f"Total span failures: {len(failed)} / {len(CURATED_ITEMS)}")
for i, cid, term, reason in failed:
    print(f"  Item {i} ({cid}): term='{term}' -> {reason}")
    print(f"    Chunk text snippet: {repr(all_chunks[cid]['text'][:150])}")
