"""Inspect chunks for T1-T6."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
snapshot = json.load(open(PROJECT_ROOT / "Data/metadata/corpus_cardiorespiratory_snapshot_v1.json", encoding="utf-8"))
doc_map = {d["document_id"]: PROJECT_ROOT / d["chunks_file"] for d in snapshot["documents"]}

def get_chunks(doc_id):
    p = doc_map[doc_id]
    return json.load(open(p, encoding="utf-8"))["chunks"]

topic_configs = [
    ("T1_HTN_WHO", "DOC-WHO-CARD-0001", ["recommendation", "treatment", "monotherapy", "combination", "blood pressure"]),
    ("T1_HTN_PMC", "DOC-PMC-CARD-0002", ["hypertension", "blood pressure", "screening", "primary", "secondary", "resistant"]),
    ("T2_AF", "DOC-PMC-CARD-0008", ["cha2ds2", "stroke", "anticoagulation", "rate", "rhythm", "ablation"]),
    ("T3_Syncope", "DOC-PMC-CARD-0009", ["syncope", "vasovagal", "orthostatic", "reflex", "carotid sinus"]),
    ("T4_COPD", "DOC-PMC-RESP-0003", ["copd", "exacerbation", "lama", "laba", "inhaler", "eosinophil"]),
    ("T5_Arrest", "DOC-PMC-EMERG-0001", ["cpr", "compression", "defibrillation", "cardiac arrest", "resuscitation"]),
    ("T6_Pneumothorax", "DOC-PMC-RESP-0004", ["pneumothorax", "observation", "aspiration", "chest tube", "drain"]),
]

for label, doc_id, kws in topic_configs:
    chunks = get_chunks(doc_id)
    print(f"=== {label} ({doc_id}) ===")
    found = 0
    for c in chunks:
        t_low = c["text"].lower()
        matched = [k for k in kws if k in t_low]
        if len(matched) >= 2:
            print(f"  [{c['chunk_id']}] matches: {matched}")
            print(f"  Heading: {c.get('heading')}")
            print(f"  Snippet: {c['text'][:200]}...\n")
            found += 1
            if found >= 3:
                break
