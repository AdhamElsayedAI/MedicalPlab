"""
MedicalPlab Shared Evidence Engine V2 — Stage 15: External Benchmark Assembly
=============================================================================
Fetches and structures official PubMedQA benchmark items (ori_pqal):
- Preserves original PubMed IDs (PMIDs) and provenance
- Preserves official questions, contexts, labels, and decisions
- Strictly firewalled against internal MedicalPlab benchmarks
- Saves to evaluation/evidence_engine/pubmedqa_external_benchmark.json
"""

import hashlib
import json
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = _ROOT / "evaluation" / "evidence_engine"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "pubmedqa_external_benchmark.json"

PUBMEDQA_URL = "https://raw.githubusercontent.com/pubmedqa/pubmedqa/master/data/ori_pqal.json"


def fetch_pubmedqa():
    print(f"Fetching official PubMedQA benchmark from {PUBMEDQA_URL}...")
    req = urllib.request.Request(
        PUBMEDQA_URL,
        headers={"User-Agent": "MedicalPlab-EvidenceEngineV2-Benchmark/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    print(f"Loaded {len(data)} raw PubMedQA items.")

    items = []
    for pmid, raw in data.items():
        contexts = raw.get("CONTEXTS", [])
        labels = raw.get("LABELS", [])
        full_context = "\n\n".join(
            f"[{label}] {text}" for label, text in zip(labels, contexts)
        ) if labels and contexts else "\n\n".join(contexts)

        items.append({
            "external_id": f"PUBMEDQA-{pmid}",
            "pmid": pmid,
            "benchmark": "PubMedQA",
            "benchmark_subset": "pqa_labeled",
            "question": raw.get("QUESTION", "").strip(),
            "context_passages": contexts,
            "context_labels": labels,
            "full_context": full_context,
            "gold_decision": raw.get("final_decision", "").strip().lower(),  # yes / no / maybe
            "long_answer": raw.get("LONG_ANSWER", "").strip(),
            "mesh_terms": raw.get("MESHES", []),
            "year": raw.get("YEAR")
        })

    # Sort deterministically by PMID
    items.sort(key=lambda x: x["pmid"])

    payload = {
        "benchmark": "PubMedQA (Official pqa_labeled)",
        "provenance_url": PUBMEDQA_URL,
        "n_items": len(items),
        "license": "MIT",
        "description": "Public biomedical QA benchmark using original PMIDs and contexts for external verification lane.",
        "items": items
    }

    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    sha = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()
    (OUT_PATH.with_suffix(".json.sha256")).write_text(f"{sha}  {OUT_PATH.name}\n", encoding="utf-8")

    print(f"Successfully wrote {len(items)} PubMedQA items to {OUT_PATH.name}")
    print(f"SHA-256: {sha}")


if __name__ == "__main__":
    fetch_pubmedqa()
