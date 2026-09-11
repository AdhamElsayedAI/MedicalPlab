import json
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "Scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import all_chunks, safe_chunk_ids, norm_sec

# Find safe chunks for specific clinical terms
def find_spans(query_term, max_results=3):
    term_l = query_term.lower()
    results = []
    for cid in sorted(safe_chunk_ids):
        ch = all_chunks[cid]
        text = ch["text"]
        if term_l in text.lower():
            # find sentence containing term
            sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if term_l in s.lower()]
            results.append({
                "chunk_id": cid,
                "document_id": ch["document_id"],
                "section_path": ch.get("section_path", []),
                "snippet": sentences[0][:180] if sentences else text[:180]
            })
            if len(results) >= max_results:
                break
    return results

if __name__ == "__main__":
    test_terms = [
        "podocyte", "fenestrated", "filtration coefficient", "inulin", "Cockcroft",
        "sglt2", "glucose reabsorption", "bicarbonate reabsorption", "fanconi",
        "countercurrent", "vasa recta", "aquaporin-2", "urea transporter",
        "renin secretion", "angiotensin", "aldosterone synthase", "calcitriol",
        "hyperkalemia", "hypokalemia", "potassium excretion", "romk",
        "metabolic acidosis", "anion gap", "carbonic anhydrase", "renal tubular acidosis",
        "acute kidney injury", "kdigo", "prerenal", "acute tubular necrosis",
        "ckd staging", "microalbuminuria", "fibrosis", "hemodialysis",
        "glomerulonephritis", "nephrotic", "minimal change", "iga nephropathy",
        "polycystic", "urinary tract infection", "hydronephrosis", "pyelonephritis",
        "calcium oxalate", "urolithiasis", "uric acid stone", "citrate",
        "peritoneal dialysis", "calcineurin", "transplantation"
    ]
    for t in test_terms:
        res = find_spans(t, max_results=1)
        if res:
            r = res[0]
            print(f"[{t}] -> {r['chunk_id']} ({r['document_id']}): {r['snippet']}...")
        else:
            print(f"[{t}] -> NOT FOUND")
