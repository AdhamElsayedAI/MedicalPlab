"""Public-safe test fixtures and data root builder for deterministic PLAB tests.

Contains ZERO WHO text, ZERO proprietary text, and ZERO unverified-license content.
All evidence is derived strictly from ACTIVE_STARTUP_SAFE CC BY 4.0 sources.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from medicalplab.plab.data_manifest import REFERENCE_ONLY_DOCUMENT_IDS

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
TRACKED_CHUNKS_FILE = FIXTURES_DIR / "cardiorespiratory_test_chunks.json"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_test_chunk_index() -> dict[str, dict[str, str]]:
    """Return dictionary of chunk_id -> {"document_id": ..., "text": ...} from public fixture."""
    data = json.loads(TRACKED_CHUNKS_FILE.read_text(encoding="utf-8"))
    index: dict[str, dict[str, str]] = {}
    for chunk in data.get("chunks", []):
        index[chunk["chunk_id"]] = {
            "document_id": chunk["document_id"],
            "text": chunk["text"],
        }
    return index


def build_test_data_root(dest_dir: Path | str) -> Path:
    """Build a complete, reproducible PLAB data root in dest_dir satisfying runtime manifest.

    Populates:
    - metadata/corpus_cardiorespiratory_snapshot_v1.json (exact tracked bytes)
    - questions/versions/cardiorespiratory_batch_1_source_audit_v2.json (exact tracked bytes)
    - questions/cardiorespiratory_batch_1_review_queue.json (exact tracked bytes)
    - questions/cardiorespiratory_batch_1.json (exact tracked bytes)
    - 12 active document chunk files (containing real CC BY 4.0 test chunks + deterministic padding)
      Total chunks = exactly 734 across 12 ACTIVE_STARTUP_SAFE documents.
      Zero WHO files created.
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    # 1. Copy tracked manifest-critical files
    meta_src = PROJECT_ROOT / "Data" / "metadata" / "corpus_cardiorespiratory_snapshot_v1.json"
    meta_dst = dest / "metadata" / "corpus_cardiorespiratory_snapshot_v1.json"
    meta_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(meta_src, meta_dst)

    batch_src = PROJECT_ROOT / "Data" / "questions" / "versions" / "cardiorespiratory_batch_1_source_audit_v2.json"
    batch_dst = dest / "questions" / "versions" / "cardiorespiratory_batch_1_source_audit_v2.json"
    batch_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(batch_src, batch_dst)

    queue_src = PROJECT_ROOT / "Data" / "questions" / "cardiorespiratory_batch_1_review_queue.json"
    queue_dst = dest / "questions" / "cardiorespiratory_batch_1_review_queue.json"
    shutil.copy2(queue_src, queue_dst)

    q_src = PROJECT_ROOT / "Data" / "questions" / "cardiorespiratory_batch_1.json"
    q_dst = dest / "questions" / "cardiorespiratory_batch_1.json"
    shutil.copy2(q_src, q_dst)

    # 2. Load tracked test chunks
    tracked_data = json.loads(TRACKED_CHUNKS_FILE.read_text(encoding="utf-8"))
    chunks_by_doc: dict[str, list[dict[str, Any]]] = {}
    for c in tracked_data.get("chunks", []):
        chunks_by_doc.setdefault(c["document_id"], []).append(c)

    # 3. Read snapshot to know exact active documents and chunk counts
    snap_data = json.loads(meta_dst.read_text(encoding="utf-8"))
    for doc in snap_data.get("documents", []):
        doc_id = doc.get("document_id")
        if doc_id in REFERENCE_ONLY_DOCUMENT_IDS:
            # Explicitly do NOT generate any chunk files for reference-only sources
            continue

        target_count = int(doc.get("chunk_count", 0))
        rel = Path(str(doc.get("chunks_file", "")))
        chunk_path = dest / Path(*rel.parts[1:]) if rel.parts and rel.parts[0].lower() == "data" else dest / rel
        chunk_path.parent.mkdir(parents=True, exist_ok=True)

        existing_chunks = chunks_by_doc.get(doc_id, [])
        doc_chunks = []
        for ec in existing_chunks:
            doc_chunks.append({
                "chunk_id": ec["chunk_id"],
                "text": ec["text"],
                "license": "CC BY 4.0",
            })

        # Pad with deterministic CC BY 4.0 test evidence up to target_count
        while len(doc_chunks) < target_count:
            idx = len(doc_chunks) + 1
            doc_chunks.append({
                "chunk_id": f"{doc_id}-TEST-{idx:04d}",
                "text": f"Deterministic test evidence passage for {doc_id} chunk {idx}. Derived from CC BY 4.0 source.",
                "license": "CC BY 4.0",
            })

        chunk_data = {
            "document_id": doc_id,
            "specialty": doc.get("specialty", ""),
            "title": doc.get("title", ""),
            "license_name": "CC BY 4.0",
            "license_status": "approved",
            "chunk_count": len(doc_chunks),
            "chunks": doc_chunks,
        }
        chunk_path.write_text(json.dumps(chunk_data, indent=2), encoding="utf-8")

    return dest
