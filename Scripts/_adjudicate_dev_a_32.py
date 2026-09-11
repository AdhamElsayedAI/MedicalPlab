import json
from pathlib import Path

ROOT = Path(".")
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"

# 1. Inspect DOC-PMC-RENAL-0016
doc16_file = CHUNKS_DIR / "DOC-PMC-RENAL-0016.chunks.json"
data = json.loads(doc16_file.read_bytes())
chunks16 = data.get("chunks", [])

print("=" * 60)
print(f"SEARCHING DOC-PMC-RENAL-0016 ({len(chunks16)} chunks)")
print("=" * 60)

keywords = [
    "fractional", "fena", "fe_na", "pre-renal", "prerenal", "intrinsic",
    "tubular function", "tubular necrosis", "sodium excretion", "<1%", ">2%",
    "fractional excretion"
]

matches_doc16 = []
for ch in chunks16:
    text_lower = ch["text"].lower()
    for kw in keywords:
        if kw in text_lower:
            idx = text_lower.find(kw)
            snippet = ch["text"][max(0, idx - 60):min(len(ch["text"]), idx + 100)].replace("\n", " ")
            matches_doc16.append((ch["chunk_id"], ch.get("section_path"), kw, snippet))

print(f"Found {len(matches_doc16)} keyword hits in DOC-PMC-RENAL-0016:")
for cid, sec, kw, snip in matches_doc16:
    print(f"  [{cid}] {sec} keyword='{kw}': ...{snip}...")

# 2. Inspect entire 23-document corpus for FENa / fractional excretion / pre-renal vs intrinsic
print("\n" + "=" * 60)
print("SEARCHING ENTIRE 23-DOCUMENT CORPUS")
print("=" * 60)

all_corpus_matches = []
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        text_lower = ch["text"].lower()
        if "fractional" in text_lower or "fena" in text_lower or "fractional excretion" in text_lower:
            all_corpus_matches.append((ch["chunk_id"], ch["document_id"], ch.get("section_path"), ch["text"]))

print(f"Total chunks in corpus mentioning 'fractional' or 'fena': {len(all_corpus_matches)}")
for cid, did, sec, text in all_corpus_matches:
    print(f"\n--- Chunk: {cid} in {did} {sec} ---")
    # print the relevant sentence
    for line in text.split("."):
        l_low = line.lower()
        if any(k in l_low for k in ["fractional", "fena", "sodium", "tubular"]):
            print(f"   {line.strip()}")
