"""
Search unspent chunks for clean clinical propositions to complete N=100.
"""

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = _ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"

corpus_chunks = {}
for f in sorted(CORPUS_DIR.glob("*.chunks.json")):
    d = json.loads(f.read_bytes())
    for ch in d.get("chunks", []):
        corpus_chunks[ch["chunk_id"]] = ch

train_path = _ROOT / "evaluation" / "renal" / "v7" / "renal-train-dev-v7.json"
train_items = json.loads(train_path.read_bytes())
train_cids = {cid for item in train_items for cid in item.get("gold_chunk_ids", [])}

pt_path = _ROOT / "evaluation" / "renal" / "v7" / "renal-product-test-v7.json"
pt_items = json.loads(pt_path.read_bytes())
pt_cids = {cid for item in pt_items for cid in item.get("gold_chunk_ids", [])}

used_cids = train_cids.union(pt_cids)
print(f"Used chunks: {len(used_cids)}, Remaining unspent: {len(corpus_chunks) - len(used_cids)}")

# Let's inspect some unspent chunks with interesting clinical terms
clinical_keywords = [
    "proteinuria", "hematuria", "glomerular", "tubular", "potassium", 
    "sodium", "acidosis", "alkalosis", "biopsy", "creatinine", 
    "dialysis", "erythropoietin", "calcium", "phosphate", "hypertension",
    "nephrotic", "nephritic", "interstitial", "cyst", "transplantation"
]

found = []
for cid, ch in corpus_chunks.items():
    if cid in used_cids:
        continue
    text = ch["text"]
    for kw in clinical_keywords:
        if kw in text.lower():
            # Find a sentence with this kw
            sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 40 and kw in s.lower()]
            if sentences:
                found.append((ch["document_id"], cid, kw, sentences[0]))
                used_cids.add(cid)
                break
    if len(found) >= 40:
        break

print(f"Found {len(found)} candidate unspent factual chunks with clinical sentences.")
for doc_id, cid, kw, sent in found[:10]:
    print(f"[{doc_id} / {cid}] ({kw}): {sent[:100]}...")
