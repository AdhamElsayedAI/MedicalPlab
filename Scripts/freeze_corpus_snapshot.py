"""Freeze Cardiorespiratory Corpus Snapshot v1.

Scans local Data/processed artifacts and generates a formal, versioned corpus freeze.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "Data" / "metadata" / "document_manifest.json"
PROCESSED_DIR = PROJECT_ROOT / "Data" / "processed"
SNAPSHOT_PATH = PROJECT_ROOT / "Data" / "metadata" / "corpus_cardiorespiratory_snapshot_v1.json"


def main():
    manifest = json.load(open(MANIFEST_PATH, encoding="utf-8"))
    corpus_docs = []
    total_chunks = 0

    for doc in manifest:
        doc_id = doc["document_id"]
        spec = (
            doc.get("medical_specialty", "Cardiology")
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
        )
        chunks_path = PROCESSED_DIR / spec / f"{doc_id}.chunks.json"
        if chunks_path.exists():
            data = json.load(open(chunks_path, encoding="utf-8"))
            chunks = data.get("chunks", []) if isinstance(data, dict) else data
            chunk_count = len(chunks)
            total_chunks += chunk_count
            h = hashlib.sha256(chunks_path.read_bytes()).hexdigest()
            corpus_docs.append({
                "document_id": doc_id,
                "specialty": spec,
                "title": doc.get("title"),
                "license_name": doc.get("license_name"),
                "license_status": doc.get("license_status"),
                "chunks_file": str(chunks_path.relative_to(PROJECT_ROOT)),
                "chunk_count": chunk_count,
                "chunks_sha256": h,
                "ingestion_status": "verified_local",
            })

    snapshot = {
        "corpus_id": "medicalplab-cardiorespiratory-corpus-v1",
        "version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "document_count": len(corpus_docs),
        "total_chunks": total_chunks,
        "documents": corpus_docs,
        "exclusions": [
            {
                "id": "DOC-PMC-CARD-0003_to_0007",
                "reason": "Wave 1 PMC artifacts missing locally in current workspace - preserved as NOT VERIFIED",
            },
            {
                "id": "DOC-PMC-RESP-0001_to_0002",
                "reason": "Wave 1 RESP artifacts missing locally in current workspace - preserved as NOT VERIFIED",
            },
            {
                "id": "SRC-NICE-*",
                "reason": "NICE guidelines excluded from production RAG ingestion per license terms - REFERENCE_ONLY",
            },
            {
                "id": "SRC-RCUK-ALS-2025",
                "reason": "RCUK guidelines excluded per licensing policy - REFERENCE_ONLY",
            },
            {
                "id": "SRC-BTS-PLEURAL-2023",
                "reason": "BTS guidelines excluded per licensing policy - REFERENCE_ONLY",
            },
        ],
    }

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    print(f"Created corpus snapshot with {len(corpus_docs)} documents and {total_chunks} total chunks at {SNAPSHOT_PATH}")
    for d in corpus_docs:
        print(f"  {d['document_id']}: {d['chunk_count']} chunks ({d['specialty']}) | SHA: {d['chunks_sha256'][:16]}...")


if __name__ == "__main__":
    main()
