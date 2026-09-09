"""Extract candidate anchor passages for all 12 Cardiorespiratory PLAB topics."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
snapshot = json.load(open(PROJECT_ROOT / "Data/metadata/corpus_cardiorespiratory_snapshot_v1.json", encoding="utf-8"))
doc_map = {d["document_id"]: PROJECT_ROOT / d["chunks_file"] for d in snapshot["documents"]}

def get_chunks(doc_id):
    p = doc_map[doc_id]
    return json.load(open(p, encoding="utf-8"))["chunks"]

topic_configs = [
    # Topic 1: Hypertension
    ("T1_HTN", "DOC-WHO-CARD-0001", ["threshold", "monotherapy", "combination", "calcium", "ace", "angiotensin"]),
    ("T1_HTN_PMC", "DOC-PMC-CARD-0002", ["primary aldosteronism", "renin", "screen", "pheochromocytoma", "secondary"]),
    # Topic 2: AF
    ("T2_AF", "DOC-PMC-CARD-0008", ["cha2ds2-vasc", "rate", "rhythm", "beta-blocker", "catheter", "doac", "anticoagulation"]),
    # Topic 3: Syncope
    ("T3_Syncope", "DOC-PMC-CARD-0009", ["carotid sinus", "orthostatic", "reflex", "vasovagal", "tilt", "ecg"]),
    # Topic 4: COPD
    ("T4_COPD", "DOC-PMC-RESP-0003", ["lama", "laba", "exacerbation", "eosinophil", "corticosteroid", "inhaler"]),
    # Topic 5: Cardiac Arrest
    ("T5_Arrest", "DOC-PMC-EMERG-0001", ["cpr", "compression", "defibrillation", "quality", "ventilation", "arrest"]),
    # Topic 6: Pneumothorax
    ("T6_Pneumothorax", "DOC-PMC-RESP-0004", ["spontaneous", "observation", "aspiration", "chest tube", "drain", "conservative"]),
    # Topic 7: ARDS
    ("T7_ARDS", "DOC-PMC-RESP-0005", ["berlin", "tidal", "peep", "protective", "prone", "hypoxemia", "plateau"]),
    # Topic 8: Cardiogenic Shock
    ("T8_Shock", "DOC-PMC-CARD-0010", ["norepinephrine", "dobutamine", "vasopressor", "inotropic", "dopamine", "revascularization"]),
    # Topic 9: Infective Endocarditis
    ("T9_Endocarditis", "DOC-PMC-CARD-0011", ["duke", "blood culture", "echocardiography", "staphylococcus", "enterococcus", "vegetation"]),
    # Topic 10: Bradyarrhythmias
    ("T10_Brady", "DOC-PMC-CARD-0012", ["pacemaker", "atrioventricular", "block", "conduction", "sinus node", "his bundle"]),
    # Topic 11: Aortic Stenosis
    ("T11_AS", "DOC-PMC-CARD-0013", ["aortic stenosis", "velocity", "mean gradient", "valve area", "tavi", "savr"]),
    # Topic 12: Mitral Regurgitation
    ("T12_MR", "DOC-PMC-CARD-0014", ["mitral regurgitation", "annuloplasty", "repair", "replacement", "functional", "heart failure"]),
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
            # Print a 200 char snippet
            print(f"  Snippet: {c['text'][:200]}...\n")
            found += 1
            if found >= 4:
                break
