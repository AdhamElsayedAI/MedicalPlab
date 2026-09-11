"""Inspect actual corpus text for key topics to build correct evidence spans."""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHUNKS_DIR = ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"

# Load all chunks indexed by doc_id
chunks_by_doc = {}
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        did = ch.get("document_id")
        if did not in chunks_by_doc:
            chunks_by_doc[did] = []
        chunks_by_doc[did].append(ch)

def search_chunks(doc_id, keyword, max_results=3):
    """Find chunks in a document containing a keyword."""
    results = []
    for ch in chunks_by_doc.get(doc_id, []):
        text = ch.get("text", "")
        if keyword.lower() in text.lower():
            results.append((ch.get("chunk_id"), ch.get("section_path", []), text[:400]))
    return results[:max_results]

# Key topics we need evidence spans for
queries_to_check = [
    ("DOC-PMC-RENAL-0018", "filtration barrier", "Glomerular filtration barrier structure"),
    ("DOC-PMC-RENAL-0018", "podocyte", "Podocyte slit diaphragm"),
    ("DOC-PMC-RENAL-0019", "SGLT2", "SGLT2 glucose reabsorption"),
    ("DOC-PMC-RENAL-0020", "aldosterone", "Aldosterone sodium regulation"),
    ("DOC-PMC-RENAL-0021", "AE4", "AE4 transporter"),
    ("DOC-PMC-RENAL-0023", "vasa recta", "Vasa recta countercurrent"),
    ("DOC-PMC-RENAL-0001", "renin", "Renin release triggers"),
    ("DOC-PMC-RENAL-0024", "erythropoietin", "EPO in CKD"),
    ("DOC-PMC-RENAL-0009", "hyperkalaemia", "ECG hyperkalaemia"),
    ("DOC-PMC-RENAL-0003", "acidosis", "Acidosis K shift"),
    ("DOC-PMC-RENAL-0004", "bicarbonate", "Proximal tubule bicarbonate"),
    ("DOC-PMC-RENAL-0006", "creatinine", "AKI creatinine definition"),
    ("DOC-PMC-RENAL-0007", "eGFR", "CKD staging eGFR"),
    ("DOC-PMC-RENAL-0008", "prednisolone", "Nephrotic syndrome treatment"),
    ("DOC-PMC-RENAL-0011", "gut", "Gut microbiome UTI"),
    ("DOC-PMC-RENAL-0012", "calcium oxalate", "Stone composition"),
    ("DOC-PMC-RENAL-0025", "glomerular haematuria", "Haematuria distinction"),
    ("DOC-PMC-RENAL-0023", "thick ascending limb", "TAL solute reabsorption"),
    ("DOC-PMC-RENAL-0010", "potassium", "TTKG diagnosis"),
    ("DOC-PMC-RENAL-0019", "SGLT2 inhibitor", "SGLT2i nephroprotection"),
]

for doc_id, keyword, topic in queries_to_check:
    results = search_chunks(doc_id, keyword)
    print(f"\n=== {topic} ({doc_id}) - keyword: '{keyword}' ===")
    if not results:
        print(f"  [NOT FOUND - try alternate]")
        # Try alternate search
        alt = keyword.split()[0]
        alt_results = search_chunks(doc_id, alt)
        for cid, sec, text in alt_results:
            print(f"  chunk: {cid} | sec: {sec}")
            print(f"  text: {text[:300]}")
    else:
        for cid, sec, text in results:
            print(f"  chunk: {cid} | sec: {sec}")
            print(f"  text: {text[:300]}")
