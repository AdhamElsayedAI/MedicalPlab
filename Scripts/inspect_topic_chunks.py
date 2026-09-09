"""Inspect chunk details across all 13 documents to prepare ground-truth question batch."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
snapshot = json.load(open(PROJECT_ROOT / "Data/metadata/corpus_cardiorespiratory_snapshot_v1.json", encoding="utf-8"))
doc_map = {d["document_id"]: PROJECT_ROOT / d["chunks_file"] for d in snapshot["documents"]}

def search_chunks(doc_id, keywords, max_matches=5):
    p = doc_map[doc_id]
    chunks = json.load(open(p, encoding="utf-8"))["chunks"]
    matches = []
    for c in chunks:
        text_lower = c["text"].lower()
        if all(kw.lower() in text_lower for kw in keywords):
            matches.append(c)
            if len(matches) >= max_matches:
                break
    return matches

if __name__ == "__main__":
    queries = [
        ("DOC-WHO-CARD-0001", ["recommendation", "blood pressure"]),
        ("DOC-PMC-CARD-0002", ["aldosterone", "screening"]),
        ("DOC-PMC-CARD-0008", ["cha2ds2", "stroke"]),
        ("DOC-PMC-CARD-0009", ["carotid sinus", "massage"]),
        ("DOC-PMC-RESP-0003", ["eosinophil", "inhalation"]),
        ("DOC-PMC-EMERG-0001", ["defibrillation", "cardiac"]),
        ("DOC-PMC-RESP-0004", ["conservative", "chest tube"]),
        ("DOC-PMC-RESP-0005", ["prone", "paO2"]),
        ("DOC-PMC-CARD-0010", ["norepinephrine", "vasopressor"]),
        ("DOC-PMC-CARD-0011", ["blood culture", "endocarditis"]),
        ("DOC-PMC-CARD-0012", ["atropine", "pacing"]),
        ("DOC-PMC-CARD-0013", ["gradient", "severe"]),
        ("DOC-PMC-CARD-0014", ["regurgitation", "surgical"]),
    ]
    for doc_id, kws in queries:
        m = search_chunks(doc_id, kws, max_matches=2)
        print(f"=== {doc_id} {kws}: {len(m)} matches ===")
        for c in m:
            print(f"  ID: {c['chunk_id']}")
            print(f"  Heading: {c.get('heading')}")
            print(f"  Snippet: {c['text'][:250]}...\n")
