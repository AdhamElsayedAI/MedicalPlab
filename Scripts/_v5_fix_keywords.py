"""Fix missing keywords — inspect chunks for correct search terms."""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHUNKS_DIR = ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"

def load_chunks_by_doc():
    chunks_by_doc = {}
    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_bytes())
        for ch in payload.get("chunks", []):
            did = ch.get("document_id")
            if did not in chunks_by_doc:
                chunks_by_doc[did] = []
            chunks_by_doc[did].append(ch)
    return chunks_by_doc

def search(cbd, doc_id, kw):
    results = []
    for ch in cbd.get(doc_id, []):
        t = ch.get("text", "")
        if kw.lower() in t.lower():
            results.append(ch.get("chunk_id"))
    return results

cbd = load_chunks_by_doc()

# Test alternate keywords for HUMAN_REVIEW_REQUIRED items
tests = [
    # (doc_id, original_kw, [alternates])
    ("DOC-PMC-RENAL-0001", "aldosterone excess", ["excess", "mineralocorticoid receptor", "mineralocorticoid"]),
    ("DOC-PMC-RENAL-0009", "hyperkalaemia", ["hyperkalemia", "serum potassium", "potassium > 6", "K+", "peaked T"]),
    ("DOC-PMC-RENAL-0005", "anion gap", ["unmeasured anion", "AG", "chloride", "metabolic acidosis"]),
    ("DOC-PMC-RENAL-0011", "cranberry", ["proanthocyanidin", "PAC", "fimbriae", "fimbriated", "uroepithelial"]),
    ("DOC-PMC-RENAL-0025", "haematuria", ["hematuria", "macroscopic", "red blood cell", "RBC", "urology"]),
    ("DOC-PMC-RENAL-0006", "hyperphosphataemia", ["phosphate", "hyperphosphatemia", "phosphorus"]),
    ("DOC-PMC-RENAL-0004", "ammonium", ["NH4", "ammonia", "glutaminase", "glutamine", "net acid"]),
    ("DOC-PMC-RENAL-0016", "cystatin", ["cystatin C", "Cystatin"]),
    ("DOC-PMC-RENAL-0002", "tubuloglomerular feedback", ["macula densa", "afferent arteriole", "TGF", "juxtaglomerular"]),
    ("DOC-PMC-RENAL-0007", "stage 5", ["end-stage", "ESRD", "eGFR < 15", "eGFR <15", "dialysis", "kidney failure"]),
    ("DOC-PMC-RENAL-0025", "red cell casts", ["red cell casts", "red blood cell cast", "RBC cast", "dysmorphic"]),
    ("DOC-PMC-RENAL-0008", "nephritic", ["nephritic syndrome", "haematuria", "hematuria", "red cell", "glomerulonephritis"]),
    ("DOC-PMC-RENAL-0019", "renal threshold", ["glucose threshold", "glucosuria", "transport maximum", "Tm", "tubular maximum"]),
    ("DOC-PMC-RENAL-0011", "urine culture", ["culture", "CFU", "colony-forming", "bacteriuria"]),
    ("DOC-PMC-RENAL-0015", "continuous renal replacement", ["CRRT", "continuous", "renal replacement", "haemodialysis", "intermittent"]),
    ("DOC-PMC-RENAL-0024", "PTH", ["parathyroid hormone", "parathyroid", "PTH"]),
    ("DOC-PMC-RENAL-0015", "cardiovascular", ["cardiac", "heart", "cardiovascular"]),
    ("DOC-PMC-RENAL-0011", "Escherichia coli", ["E. coli", "Escherichia", "uropathogen"]),
    ("DOC-PMC-RENAL-0007", "protein-to-creatinine ratio", ["protein-to-creatinine", "PCR", "albumin", "proteinuria", "urine protein"]),
    ("DOC-PMC-RENAL-0004", "ammoniagenesis", ["ammonia", "ammoniagenesis", "NH4", "glutamine", "net acid"]),
    ("DOC-PMC-RENAL-0007", "albumin-to-creatinine ratio", ["albumin-to-creatinine", "ACR", "albuminuria"]),
    ("DOC-PMC-RENAL-0023", "diabetes insipidus", ["diabetes insipidus", "DI", "vasopressin resistance", "nephrogenic"]),
    ("DOC-PMC-RENAL-0001", "juxtaglomerular", ["juxtaglomerular", "macula densa", "renin-secreting", "granular cell"]),
    ("DOC-PMC-RENAL-0011", "cranberry", ["proanthocyanidin", "PAC", "fimbriae"]),
]

for doc_id, orig_kw, alts in tests:
    orig_hits = search(cbd, doc_id, orig_kw)
    print(f"\n{doc_id} | '{orig_kw}' -> hits: {orig_hits}")
    for alt in alts:
        hits = search(cbd, doc_id, alt)
        if hits:
            print(f"  FOUND alt '{alt}': {hits[:3]}")
