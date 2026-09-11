import json
from pathlib import Path

ROOT = Path(".")
CHUNKS_DIR = ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"

chunks = []
doc_chunks = {}
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        chunks.append(ch)
        did = ch["document_id"]
        doc_chunks.setdefault(did, []).append(ch)

# Check search terms for the 16 unresolved
queries_to_fix = [
    (21, "DOC-PMC-RENAL-0018", ["actin", "cytoskeleton", "foot process", "podocyte"]),
    (23, "DOC-PMC-RENAL-0002", ["pressure", "filtration", "shear", "capillary", "perfusion"]),
    (24, "DOC-PMC-RENAL-0001", ["arteriole", "angiotensin", "at1", "vasoconstrict"]),
    (27, "DOC-PMC-RENAL-0006", ["phosphate", "pth", "mineral", "calcium", "tubular"]),
    (30, "DOC-PMC-RENAL-0019", ["sglt1", "sglt2", "capacity", "glucose", "transport"]),
    (34, "DOC-PMC-RENAL-0023", ["nkcc2", "furosemide", "thick ascending", "loop", "transport"]),
    (36, "DOC-PMC-RENAL-0001", ["renin", "juxtaglomerular", "secretion", "macula densa"]),
    (41, "DOC-PMC-RENAL-0001", ["anp", "peptide", "sodium", "atrial", "blood pressure"]),
    (42, "DOC-PMC-RENAL-0009", ["sodium", "volume", "hyperkalemia", "electrolyte", "plasma"]),
    (44, "DOC-PMC-RENAL-0009", ["acidosis", "potassium", "shift", "insulin", "ph"]),
    (45, "DOC-PMC-RENAL-0001", ["liver", "edema", "volume", "vasodilation", "arterial"]),
    (47, "DOC-PMC-RENAL-0004", ["carbonic", "ca", "bicarbonate", "anhydrase", "proximal"]),
    (54, "DOC-PMC-RENAL-0016", ["creatinine", "delay", "steady", "lag", "accumulation"]),
    (65, "DOC-PMC-RENAL-0025", ["glomerulonephritis", "rapid", "crescent", "rpgn", "hematuria"]),
    (68, "DOC-PMC-RENAL-0006", ["nephritis", "allergic", "nsaid", "drug", "acute interstitial"]),
    (73, "DOC-PMC-RENAL-0012", ["uric acid", "ph", "stone", "crystallization", "acidic"]),
]

print("Searching candidate keywords:")
for qn, did, candidates in queries_to_fix:
    ch_list = doc_chunks.get(did, [])
    found = {}
    for cand in candidates:
        matching = [c["chunk_id"] for c in ch_list if cand.lower() in c.get("text", "").lower()]
        if matching:
            found[cand] = len(matching)
    print(f"Query {qn} ({did}): found {found}")
