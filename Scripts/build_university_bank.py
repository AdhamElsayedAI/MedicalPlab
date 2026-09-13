"""Reproduce the six-question bank from existing public renal sources.

Questions/explanations are original educational adaptations; no clinical advice.
This script does not read or write PLAB content or private evidence.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / "Data/metadata/renal_source_registry_v1.json").read_text(encoding="utf-8"))


def evidence(doc, chunk, excerpt):
    source = next(d for d in registry["documents"] if d["document_id"] == doc)
    chunks = json.loads((ROOT / f"Data/processed/renal_v1/{doc}.chunks.json").read_text(encoding="utf-8"))
    text = next(c["text"] for c in chunks["chunks"] if c["chunk_id"] == chunk)
    assert excerpt in text, "Evidence excerpt must exactly match public source"
    return {"document_id": doc, "chunk_id": chunk, "title": source["title"],
            "authors": source["authors"], "url": source["official_source_url"],
            "license": source["license_name"], "license_url": source["license_url"],
            "excerpt": excerpt, "excerpt_sha256": hashlib.sha256(excerpt.encode()).hexdigest()}


raas = evidence("DOC-PMC-RENAL-0001", "DOC-PMC-RENAL-0001-B0003-C01",
                "Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I (Ang I). Ang I is cleaved by angiotensin-converting enzyme (ACE) resulting in physiologically active angiotensin II (Ang II). Ang II, the main effector of the RAAS, mediates its effects via type 1 Ang II receptor (AT1R).")
barrier = evidence("DOC-PMC-RENAL-0002", "DOC-PMC-RENAL-0002-B0004-C01",
                   "The main function of the glomeruli is to filter fluids and electrolytes from the blood, while retaining plasma proteins 3 . This activity happens at the level of the glomerular filtration barrier (GFB) and is coordinated by the interaction of two highly specialized glomerular cells (the fenestrated endothelium and the podocytes), which are separated by a thin layer of glomerular basement membrane (GBM 4 ).")

items = [
    ("RAAS mechanisms", "In the renin-angiotensin pathway, which substrate does active renin cleave to form angiotensin I?",
     ["Angiotensinogen", "Angiotensin II", "Aldosterone", "Albumin"], "A",
     "Renin acts on angiotensinogen to form angiotensin I. ACE then converts angiotensin I to angiotensin II; these are distinct steps in the pathway.", raas),
    ("RAAS mechanisms", "Which enzyme converts angiotensin I into angiotensin II?",
     ["Renin", "Angiotensin-converting enzyme (ACE)", "Pepsin", "Amylase"], "B",
     "ACE cleaves angiotensin I to produce angiotensin II. Renin acts earlier, on angiotensinogen.", raas),
    ("RAAS mechanisms", "Which receptor mediates the main classical effects of angiotensin II in the RAAS pathway described here?",
     ["Insulin receptor", "Nicotinic acetylcholine receptor", "Type 1 angiotensin II receptor (AT1R)", "Thyroid hormone receptor"], "C",
     "The classical RAAS pathway links angiotensin II to AT1R. This question concerns that pathway; it does not imply that angiotensin II has no other receptor interactions.", raas),
    ("Glomerular filtration barrier", "Which pair of cell types forms the two cellular sides of the glomerular filtration barrier?",
     ["Hepatocytes and cholangiocytes", "Osteoblasts and osteoclasts", "Neurons and astrocytes", "Fenestrated endothelial cells and podocytes"], "D",
     "The filtration barrier includes fenestrated glomerular endothelium and podocytes. A glomerular basement membrane separates these cellular layers.", barrier),
    ("Glomerular filtration barrier", "What lies between the fenestrated endothelium and podocytes in the glomerular filtration barrier?",
     ["Glomerular basement membrane", "Articular cartilage", "Myelin sheath", "Epidermal keratin layer"], "A",
     "The glomerular basement membrane lies between the endothelial cells and podocytes. Together these components form the filtration barrier.", barrier),
    ("Glomerular filtration barrier", "Which statement best describes normal glomerular filtration at a foundational level?",
     ["It selectively empties plasma proteins into urine", "It filters fluid and electrolytes while retaining plasma proteins", "It produces bile from circulating lipids", "It converts urea into red blood cells"], "B",
     "Glomeruli filter fluid and electrolytes from blood while retaining plasma proteins. The filtration barrier supports this selective function.", barrier),
]
rows = []
for i, (topic, stem, options, answer, explanation, source) in enumerate(items, 1):
    rows.append({"id": f"UNI-RENAL-{i:03}", "track": "university", "subject": "Renal physiology",
                 "topic": topic, "stem": stem, "options": dict(zip("ABCD", options)),
                 "correct_answer": answer, "explanation": explanation, "difficulty": "easy",
                 "content_kind": "EDUCATIONAL_BASIC_SCIENCE", "status": "VERIFIED_EDUCATIONAL",
                 "review_reason": "Structurally audited and answer/explanation checked against the attached public source passage. Educational verification only; no human clinician approval.",
                 "evidence": source})
destination = ROOT / "Data/university/questions.json"
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {len(rows)} educational questions")
