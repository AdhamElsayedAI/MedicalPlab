import json
import re
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "Scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import all_chunks, safe_chunk_ids, all_excluded_sec, all_excluded_window
from generate_clean_train_items import SPEC_ITEMS

print(f"Checking {len(SPEC_ITEMS)} items for exact span matches...")

mismatches = []
for item in SPEC_ITEMS:
    idx, q_text, strat, style, obj, claim, doc_id, chunk_id, span_text, rationale = item
    ch = all_chunks[chunk_id]
    text = ch["text"]
    
    # check if span is in text
    span_norm = re.sub(r"\s+", " ", span_text).strip().lower()
    text_norm = re.sub(r"\s+", " ", text).strip().lower()
    
    if span_norm not in text_norm:
        # find approximate match or print sentences
        words = span_text.split()[:4]
        search_prefix = " ".join(words).lower()
        sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if any(w.lower() in s.lower() for w in words[:2])]
        mismatches.append({
            "idx": idx,
            "chunk_id": chunk_id,
            "span_text": span_text,
            "sample_sentences": sentences[:3]
        })

print(f"Total mismatches: {len(mismatches)} / {len(SPEC_ITEMS)}")
for m in mismatches:
    print(f"\n--- Item {m['idx']} ({m['chunk_id']}) ---")
    print(f"Target span: {m['span_text']}")
    print("Available sentences:")
    for s in m["sample_sentences"]:
        print(f"  * {s}")
