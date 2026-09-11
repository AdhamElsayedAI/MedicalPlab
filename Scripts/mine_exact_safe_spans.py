"""
Mine Exact Supporting Evidence Spans from Safe Unspent Chunks
============================================================
Scans safe chunks for rich educational clinical propositions across all 12 strata.
Outputs exact chunk ID, document, section, and verified text spans.
"""

import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "Scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "Scripts"))

from build_clean_train_v1 import all_chunks, safe_chunk_ids, norm_sec

# Keywords per stratum to find authentic evidence sentences
STRATUM_SEARCH = {
    "STR-01": ["glomerular filtration barrier", "fenestrated endothelium", "podocytes", "inulin", "Cockcroft", "creatinine clearance", "permeability", "permselectivity", "starling"],
    "STR-02": ["sglt2", "glucose reabsorption", "bicarbonate", "nhe3", "intercalated", "ae1", "pendrin", "urate", "proximal tubule", "thick ascending limb", "romk"],
    "STR-03": ["countercurrent", "vasa recta", "urea", "concentrating", "medullary", "aquaporin-2", "diluting segment", "hyperosmolality"],
    "STR-04": ["renin", "angiotensin", "aldosterone", "ace2", "cyp27b1", "calcitriol", "fgf23", "juxtaglomerular", "erythropoietin", "prostaglandin", "at1 receptor", "kinin"],
    "STR-05": ["hyperkalemia", "hypokalemia", "patiromer", "calcium gluconate", "peaked t", "sodium zirconium", "enac", "potassium", "electrolyte", "magnesium", "aldosterone"],
    "STR-06": ["ammoniagenesis", "acidosis", "anion gap", "carbonic anhydrase", "renal tubular acidosis", "rta", "ammonium", "bicarbonate", "alkalosis", "titratable", "glutamine", "fanconi", "hyperchloremic", "metabolic acidosis"],
    "STR-07": ["ngal", "acute kidney injury", "tubular necrosis", "aminoglycoside", "contrast", "ischemic", "hepatorenal", "prerenal", "kdigo", "creatinine", "oliguria", "muddy brown", "nephrotoxic", "intrinsic", "postrenal", "aki"],
    "STR-08": ["ckd", "albuminuria", "acr", "fibrosis", "hepcidin", "vascular calcification", "klotho", "protein restriction", "gfr", "chronic kidney disease", "esrd", "uremia", "uremic"],
    "STR-09": ["minimal change", "pla2r", "membranous", "iga nephropathy", "crescent", "anti-gbm", "acanthocyte", "dysmorphic", "nephrotic", "hematuria", "glomerulonephritis", "fsgs"],
    "STR-10": ["polycystic", "adpkd", "cftr", "upec", "recurrent uti", "hydronephrosis", "interstitial nephritis", "post-obstructive", "pyelonephritis", "cyst", "pyuria"],
    "STR-11": ["calcium oxalate", "citrate", "struvite", "uric acid", "stone", "staghorn", "hypercalciuria", "supersaturation", "calculi", "urolithiasis", "nephrolithiasis"],
    "STR-12": ["dialysis", "cvvh", "hemofiltration", "calcineurin", "ace inhibitor", "cardiorenal", "peritoneal dialysis", "hemodialysis", "ultrafiltration", "immunosuppressive", "transplant", "fistula", "tacrolimus", "cyclosporine"]
}

def mine_candidates():
    candidates_by_stratum = {}
    for strat, terms in STRATUM_SEARCH.items():
        candidates_by_stratum[strat] = []
        for cid in sorted(safe_chunk_ids):
            ch = all_chunks[cid]
            text = ch["text"]
            for term in terms:
                if re.search(r"\b" + re.escape(term) + r"\b", text, re.IGNORECASE):
                    # split sentences
                    sents = [s.strip() for s in text.replace("\n", " ").split(". ") if len(s.strip()) > 40]
                    matching_sents = [s for s in sents if term.lower() in s.lower()]
                    if matching_sents:
                        candidates_by_stratum[strat].append({
                            "chunk_id": cid,
                            "document_id": ch["document_id"],
                            "section_path": ch.get("section_path", []),
                            "term": term,
                            "span": matching_sents[0]
                        })
                        break
    return candidates_by_stratum

if __name__ == "__main__":
    cands = mine_candidates()
    for strat, items in cands.items():
        print(f"=== {strat}: {len(items)} candidate spans ===")
        for it in items[:3]:
            sec = " > ".join(it["section_path"]) if it["section_path"] else "ROOT"
            span_clean = it["span"][:100].encode("ascii", "replace").decode("ascii")
            print(f"  [{it['chunk_id']} | {it['document_id']} | {sec}] ({it['term']}): {span_clean}...")
