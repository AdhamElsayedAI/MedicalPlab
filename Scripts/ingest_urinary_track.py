"""Run the governed Renal v1 JATS extraction and chunking lifecycle."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "Data" / "metadata"
REGISTRY = META / "renal_source_registry_v1.json"
DOCUMENT_MANIFEST = META / "document_manifest.json"
PROCESSED = ROOT / "Data" / "processed" / "renal_v1"
EXPERIMENTS = ROOT / "Data" / "experiments" / "renal" / "chunking"


def _ensure_document_manifest(documents: list[dict[str, object]]) -> None:
    current = json.loads(DOCUMENT_MANIFEST.read_text(encoding="utf-8")) if DOCUMENT_MANIFEST.exists() else []
    items = current["documents"] if isinstance(current, dict) else current
    by_id = {item["document_id"]: item for item in items}
    for document in documents:
        by_id[document["document_id"]] = {
            "document_id": document["document_id"], "source_id": f"SRC-PMC-{document['pmcid']}",
            "title": document["title"], "medical_specialty": "Renal Medicine",
            "topics": document["topic_tags"], "document_type": document["evidence_type"],
            "evidence_level": "moderate", "publication_date": str(document["publication_year"]),
            "version": "1", "url": document["official_source_url"], "doi": document["doi"],
            "license_name": document["license_name"], "license_status": "approved",
            "rag_allowed": True, "question_generation_allowed": True,
            "retrieved_at": document["retrieved_at"], "sha256": document["sha256"], "ingestion_status": "downloaded",
            "notes": "Renal v1; article-level JATS license verified.",
        }
    DOCUMENT_MANIFEST.write_text(json.dumps(list(by_id.values()), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _window_chunks(document: dict[str, object], size: int, overlap: int, label: str) -> dict[str, object]:
    chunks = []
    for block in document["sections"]:
        words = re.findall(r"\S+", block["text"])
        step = size - overlap
        for start in range(0, len(words), step):
            part = words[start:start + size]
            if not part:
                continue
            chunks.append({
                "chunk_id": f"{document['document_id']}-{label}-C{len(chunks)+1:04d}",
                "document_id": document["document_id"], "text": " ".join(part),
                "heading": block.get("heading", ""), "section_path": block.get("section_path", []),
                "source_block_index": block["block_index"], "foundational_or_clinical": "mixed",
            })
            if start + size >= len(words):
                break
    return {"document_id": document["document_id"], "configuration": label, "token_target": size, "token_overlap": overlap, "chunks": chunks}


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    documents = [item for item in registry["documents"] if item["status"] == "accepted"]
    if len(documents) < 12:
        raise RuntimeError(f"At least 12 license-approved documents are required; found {len(documents)}")
    _ensure_document_manifest(documents)
    for document in documents:
        doc_id = document["document_id"]
        for script, extra in (
            ("extract_pmc_jats.py", []),
            ("adapt_pmc_to_canonical.py", []),
            ("chunk_sections.py", ["--target-chars", "1600", "--max-chars", "2200", "--min-chars", "250"]),
        ):
            child_env = {**os.environ, "PYTHONUTF8": "1"}
            subprocess.run([sys.executable, str(ROOT / "Scripts" / script), doc_id, "--specialty", "renal_v1", *extra], cwd=ROOT, env=child_env, check=True)
        enriched = json.loads((PROCESSED / f"{doc_id}.sections.enriched.json").read_text(encoding="utf-8"))
        final_chunks = json.loads((PROCESSED / f"{doc_id}.chunks.json").read_text(encoding="utf-8"))
        variants = {
            "A_250_minimal_overlap": _window_chunks(enriched, 250, 0, "A"),
            "B_400_10pct_overlap": _window_chunks(enriched, 400, 40, "B"),
            "C_section_aware": {**final_chunks, "configuration": "C", "token_target": "section-aware <=2200 characters"},
        }
        for name, payload in variants.items():
            target = EXPERIMENTS / name / f"{doc_id}.chunks.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    counts = {}
    for folder in EXPERIMENTS.iterdir():
        counts[folder.name] = sum(len(json.loads(path.read_text(encoding="utf-8"))["chunks"]) for path in folder.glob("*.json"))
    print(json.dumps({"documents": len(documents), "chunk_counts": counts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
