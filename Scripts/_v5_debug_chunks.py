"""Debug gold chunk lookup issue."""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHUNKS_DIR = ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"

# Load a few chunks from DOC-PMC-RENAL-0018 to see the text format
chunks = []
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        if ch.get("document_id") == "DOC-PMC-RENAL-0018":
            chunks.append(ch)
            if len(chunks) >= 5:
                break
    if len(chunks) >= 5:
        break

print(f"Sample chunks from DOC-PMC-RENAL-0018:")
for ch in chunks:
    print(f"  chunk_id: {ch.get('chunk_id')}")
    print(f"  document_id: {ch.get('document_id')}")
    print(f"  section_path: {ch.get('section_path', [])}")
    print(f"  text[:200]: {ch.get('text', '')[:200]}")
    print()

# Now test the overlap function with a real span
evidence_span = "glomerular filtration barrier consists of the fenestrated endothelium, the glomerular basement membrane"
evidence_norm = re.sub(r"\s+", " ", evidence_span.strip().lower())
print(f"Evidence span (norm): {evidence_norm[:100]}")
print()

# Check if any chunk text contains this span
found = 0
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        ch_text = ch.get("text", "")
        ch_norm = re.sub(r"\s+", " ", ch_text.strip().lower())
        if evidence_norm[:50] in ch_norm:
            print(f"FOUND in {ch['document_id']} chunk {ch['chunk_id']}")
            print(f"  text[:300]: {ch_text[:300]}")
            found += 1
print(f"Total found: {found}")

# Also check document_id format in chunks
print("\nSample document_ids in all chunks:")
all_doc_ids = set()
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        all_doc_ids.add(ch.get("document_id"))
print(sorted(all_doc_ids)[:10])
