"""Freeze independently authored, source-verifiable renal retrieval datasets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "Data" / "metadata" / "renal_source_registry_v1.json"
CHUNKS = ROOT / "Data" / "experiments" / "renal" / "chunking" / "C_section_aware"
OUT = ROOT / "evaluation" / "renal"

EXCLUDED_HEADINGS = {"methods", "results", "discussion", "conclusion", "abstract", "references"}
UNSUPPORTED = [
    "How is acute appendicitis diagnosed?", "Explain the visual pathway from retina to cortex.",
    "What are the stages of labour?", "Compare ulcerative colitis and Crohn disease.",
    "Describe insulin synthesis in pancreatic beta cells.", "How is a fractured clavicle managed?",
    "Explain the coagulation cascade.", "What are the causes of neonatal jaundice?",
]


def _anchors(path: Path) -> list[dict[str, object]]:
    chunks = json.loads(path.read_text(encoding="utf-8"))["chunks"]
    useful = []
    seen = set()
    for chunk in chunks:
        heading = str(chunk.get("heading") or "").strip()
        normalized = heading.casefold().strip(" .:0123456789")
        if len(str(chunk.get("text", ""))) < 300 or normalized in EXCLUDED_HEADINGS or not heading or heading in seen:
            continue
        seen.add(heading)
        useful.append(chunk)
    if len(useful) < 6:
        useful = [chunk for chunk in chunks if len(str(chunk.get("text", ""))) >= 300]
    return useful[:6]


def _query(qid: str, document: dict[str, object], chunk: dict[str, object], template: int) -> dict[str, object]:
    topic = document["topic_tags"][template % len(document["topic_tags"])]
    heading = str(chunk.get("heading") or topic)
    prompts = [
        f"Explain {topic} with emphasis on {heading}.",
        f"What evidence describes {heading} in relation to {topic}?",
        f"For a medical student, summarize the renal principles of {topic} covered under {heading}.",
    ]
    return {
        "query_id": qid, "query": prompts[template % 3], "topic": topic,
        "difficulty": ["easy", "medium", "hard"][template % 3], "query_type": ["explain", "evidence", "summarize"][template % 3],
        "foundational_or_clinical": document["medical_domain"], "gold_document_ids": [document["document_id"]],
        "gold_section_ids": chunk.get("section_path", []), "gold_chunk_ids": [chunk["chunk_id"]],
        "answerable": True, "authority_sensitive": "high_risk" in document["medical_domain"], "multi_source": False,
    }


def _write(name: str, items: list[dict[str, object]]) -> str:
    payload = {"dataset_id": name, "frozen": True, "authoring_method": "explicit source-section anchors; no retrieval output used as ground truth", "queries": items}
    raw = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode()
    path = OUT / f"{name.lower()}.json"
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    (path.with_suffix(path.suffix + ".sha256")).write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return digest


def main() -> int:
    documents = [item for item in json.loads(REGISTRY.read_text(encoding="utf-8"))["documents"] if item["status"] == "accepted"]
    OUT.mkdir(parents=True, exist_ok=True)
    dev, heldout, calibration = [], [], []
    for doc_index, document in enumerate(documents, 1):
        anchors = _anchors(CHUNKS / f"{document['document_id']}.chunks.json")
        for i in range(3):
            dev.append(_query(f"RENAL-DEV-{doc_index:02d}-{i+1}", document, anchors[i], i))
            heldout.append(_query(f"RENAL-HO-{doc_index:02d}-{i+1}", document, anchors[i+3], i + 1))
        calibration.append({**_query(f"RENAL-CAL-S-{doc_index:02d}", document, anchors[0], 0), "support_label": "SUPPORTED"})
        calibration.append({**_query(f"RENAL-CAL-P-{doc_index:02d}", document, anchors[1], 1), "query": f"{_query('x', document, anchors[1], 1)['query']} Also provide an unrelated treatment threshold not contained in this source.", "support_label": "PARTIALLY_SUPPORTED"})
    for index, text in enumerate(UNSUPPORTED, 1):
        heldout.append({"query_id": f"RENAL-HO-U-{index:02d}", "query": text, "topic": "out_of_domain", "difficulty": "medium", "query_type": "unsupported", "foundational_or_clinical": "outside_renal", "gold_document_ids": [], "gold_section_ids": [], "gold_chunk_ids": [], "answerable": False, "authority_sensitive": False, "multi_source": False})
        calibration.append({"query_id": f"RENAL-CAL-U-{index:02d}", "query": text, "topic": "out_of_domain", "difficulty": "medium", "query_type": "unsupported", "foundational_or_clinical": "outside_renal", "gold_document_ids": [], "gold_section_ids": [], "gold_chunk_ids": [], "answerable": False, "authority_sensitive": False, "multi_source": False, "support_label": "UNSUPPORTED"})
    hashes = {"dev": _write("RENAL-DEV-v1", dev), "calibration": _write("RENAL-CALIBRATION-v1", calibration), "heldout": _write("RENAL-HELDOUT-v1", heldout)}
    print(json.dumps({"counts": {"dev": len(dev), "calibration": len(calibration), "heldout": len(heldout)}, "sha256": hashes}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
