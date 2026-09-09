"""Search and display precise candidate text snippets for all 36 questions."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
snapshot = json.load(open(PROJECT_ROOT / "Data/metadata/corpus_cardiorespiratory_snapshot_v1.json", encoding="utf-8"))
doc_map = {d["document_id"]: PROJECT_ROOT / d["chunks_file"] for d in snapshot["documents"]}

def get_chunks(doc_id):
    return json.load(open(doc_map[doc_id], encoding="utf-8"))["chunks"]

searches = [
    # T1
    ("DOC-WHO-CARD-0001", "pharmacological", ["monotherapy", "combination"]),
    ("DOC-PMC-CARD-0002", "secondary", ["aldosteronism", "endocrine"]),
    ("DOC-WHO-CARD-0001", "monitoring", ["target", "blood pressure"]),
    # T2
    ("DOC-PMC-CARD-0008", "stroke", ["cha2ds2-vasc"]),
    ("DOC-PMC-CARD-0008", "rate control", ["beta-blocker", "diltiazem", "digoxin"]),
    ("DOC-PMC-CARD-0008", "ablation", ["catheter ablation", "symptomatic"]),
    # T3
    ("DOC-PMC-CARD-0009", "reflex", ["vasovagal", "trigger", "prodrome"]),
    ("DOC-PMC-CARD-0009", "orthostatic", ["standing", "blood pressure", "fall"]),
    ("DOC-PMC-CARD-0009", "cardiac", ["structural", "ecg", "arrhythmia"]),
    # T4
    ("DOC-PMC-RESP-0003", "exacerbation", ["corticosteroid", "bronchodilator", "oxygen"]),
    ("DOC-PMC-RESP-0003", "stable", ["lama", "laba", "eosinophil"]),
    ("DOC-PMC-RESP-0003", "rehabilitation", ["smoking", "cessation", "exercise"]),
    # T5
    ("DOC-PMC-EMERG-0001", "als", ["defibrillation", "shock", "cardiac arrest"]),
    ("DOC-PMC-EMERG-0001", "quality", ["compression", "rate", "depth"]),
    ("DOC-PMC-EMERG-0001", "outcome", ["cpr", "survival", "resuscitation"]),
    # T6
    ("DOC-PMC-RESP-0004", "tension", ["decompression", "tension", "needle"]),
    ("DOC-PMC-RESP-0004", "observation", ["conservative", "spontaneous", "failure"]),
    ("DOC-PMC-RESP-0004", "chest tube", ["drain", "intervention", "aspiration"]),
    # T7
    ("DOC-PMC-RESP-0005", "definition", ["berlin", "pao2", "fio2"]),
    ("DOC-PMC-RESP-0005", "ventilation", ["protective", "tidal", "plateau"]),
    ("DOC-PMC-RESP-0005", "prone", ["positioning", "prone", "hours"]),
    # T8
    ("DOC-PMC-CARD-0010", "vasopressor", ["norepinephrine", "first-line"]),
    ("DOC-PMC-CARD-0010", "inotropic", ["dobutamine", "inotropic", "shock"]),
    ("DOC-PMC-CARD-0010", "revascularization", ["pci", "coronary", "revascularization"]),
    # T9
    ("DOC-PMC-CARD-0011", "duke", ["criteria", "blood culture"]),
    ("DOC-PMC-CARD-0011", "tee", ["transesophageal", "transthoracic", "sensitivity"]),
    ("DOC-PMC-CARD-0011", "biofilm", ["staphylococcus", "antibiotic", "infective"]),
    # T10
    ("DOC-PMC-CARD-0012", "av block", ["atrioventricular", "block", "pacemaker"]),
    ("DOC-PMC-CARD-0012", "pacing", ["right ventricular", "conduction", "desynchrony"]),
    ("DOC-PMC-CARD-0012", "his bundle", ["hbp", "bundle", "pacing"]),
    # T11
    ("DOC-PMC-CARD-0013", "gradient", ["mean gradient", "velocity", "severe"]),
    ("DOC-PMC-CARD-0013", "parameters", ["aortic valve area", "continuity", "vmax"]),
    ("DOC-PMC-CARD-0013", "intervention", ["tavi", "savr", "surgical", "transcatheter"]),
    # T12
    ("DOC-PMC-CARD-0014", "mechanism", ["functional", "mitral regurgitation", "annuloplasty"]),
    ("DOC-PMC-CARD-0014", "surgery", ["repair", "replacement", "mortality"]),
    ("DOC-PMC-CARD-0014", "outcome", ["survival", "recurrence", "regurgitation"]),
]

for doc_id, label, kws in searches:
    chunks = get_chunks(doc_id)
    best = None
    for c in chunks:
        t_low = c["text"].lower()
        cnt = sum(1 for kw in kws if kw in t_low)
        if cnt > 0:
            if best is None or cnt > best[0]:
                best = (cnt, c["chunk_id"], c.get("heading"), c["text"])
    if best:
        print(f"[{label}] {doc_id} -> {best[1]} (score {best[0]}): {best[2]}")
        print(f"   Snippet: {best[3][:180]}...\n")
    else:
        print(f"[{label}] {doc_id} -> NO MATCH\n")
