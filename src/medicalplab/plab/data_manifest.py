"""Data integrity and verification manifest for production runtime datasets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ACTIVE_BATCH_PATH = "questions/versions/cardiorespiratory_batch_1_source_audit_v2.json"
EXPECTED_BATCH_HASH = "3351e9b7a70c0dfc83eb3927f0258f80efb273c3e37a08ab9714419f5239eeca"
EXPECTED_QUEUE_HASH = "11a9c20dd80209243ac791f41b3d2a07f76e8f64fed82e9e1e52024cdef39a26"
EXPECTED_SNAPSHOT_HASH = "ff9497c744fe5c31813281a042ce30cc4bfa51aee59d3ed0adcede03ea971db5"
EXPECTED_DOCUMENT_COUNT = 13
EXPECTED_CHUNK_COUNT = 817


def compute_file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class DataIntegrityReport:
    is_valid: bool
    data_root: str
    blockers: tuple[str, ...]
    batch_version: str | None
    snapshot_id: str | None
    document_count: int
    chunk_count: int
    question_count: int
    queue_count: int
    hashes: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def verify_production_data_manifest(data_root: Path | str | None = None) -> DataIntegrityReport:
    """Strictly verify that MEDICALPLAB_DATA_ROOT satisfies production integrity requirements."""
    if data_root is None:
        import os
        project_root = Path(__file__).resolve().parents[3]
        data_root = os.environ.get("MEDICALPLAB_DATA_ROOT", str(project_root / "Data"))

    root = Path(data_root)
    blockers: list[str] = []
    hashes: dict[str, str] = {}
    doc_count = 0
    total_chunks = 0
    question_count = 0
    queue_count = 0
    batch_version: str | None = None
    snapshot_id: str | None = None

    if not root.exists() or not root.is_dir():
        return DataIntegrityReport(
            is_valid=False,
            data_root=str(root),
            blockers=("DATA_ROOT_UNAVAILABLE",),
            batch_version=None,
            snapshot_id=None,
            document_count=0,
            chunk_count=0,
            question_count=0,
            queue_count=0,
            hashes={},
        )

    snapshot_file = root / "metadata" / "corpus_cardiorespiratory_snapshot_v1.json"
    if not snapshot_file.exists():
        blockers.append("CORPUS_SNAPSHOT_MISSING")
    else:
        actual_hash = compute_file_sha256(snapshot_file)
        hashes["corpus_snapshot_sha256"] = actual_hash
        if actual_hash != EXPECTED_SNAPSHOT_HASH:
            blockers.append("CORPUS_SNAPSHOT_HASH_MISMATCH")
        try:
            snap_data = json.loads(snapshot_file.read_text(encoding="utf-8"))
            snapshot_id = snap_data.get("snapshot_id") or snap_data.get("corpus_id")
            documents = snap_data.get("documents", [])
            doc_count = len(documents)
            if doc_count != EXPECTED_DOCUMENT_COUNT:
                blockers.append(f"DOCUMENT_COUNT_MISMATCH: expected {EXPECTED_DOCUMENT_COUNT}, found {doc_count}")

            for doc in documents:
                rel = Path(str(doc.get("chunks_file", "")))
                chunk_path = root / Path(*rel.parts[1:]) if rel.parts and rel.parts[0].lower() == "data" else root / rel
                if not chunk_path.exists():
                    blockers.append(f"CHUNK_FILE_MISSING: {doc.get('document_id')}")
                else:
                    try:
                        c_data = json.loads(chunk_path.read_text(encoding="utf-8"))
                        chunks = c_data.get("chunks", [])
                        total_chunks += len(chunks)
                    except Exception as e:
                        blockers.append(f"CHUNK_FILE_INVALID: {doc.get('document_id')} ({e})")
        except Exception as exc:
            blockers.append(f"CORPUS_SNAPSHOT_INVALID: {exc}")

    batch_file = root / ACTIVE_BATCH_PATH
    if not batch_file.exists():
        blockers.append("QUESTION_BATCH_MISSING")
    else:
        actual_hash = compute_file_sha256(batch_file)
        hashes["question_batch_sha256"] = actual_hash
        if actual_hash != EXPECTED_BATCH_HASH:
            blockers.append("QUESTION_BATCH_HASH_MISMATCH")
        try:
            b_data = json.loads(batch_file.read_text(encoding="utf-8"))
            batch_version = b_data.get("batch_version") or b_data.get("batch_id")
            question_count = len(b_data.get("questions", []))
        except Exception as exc:
            blockers.append(f"QUESTION_BATCH_INVALID: {exc}")

    queue_file = root / "questions" / "cardiorespiratory_batch_1_review_queue.json"
    if not queue_file.exists():
        blockers.append("REVIEW_QUEUE_MISSING")
    else:
        actual_hash = compute_file_sha256(queue_file)
        hashes["review_queue_sha256"] = actual_hash
        if actual_hash != EXPECTED_QUEUE_HASH:
            blockers.append("REVIEW_QUEUE_HASH_MISMATCH")
        try:
            q_data = json.loads(queue_file.read_text(encoding="utf-8"))
            queue_count = len(q_data.get("queue", []))
        except Exception as exc:
            blockers.append(f"REVIEW_QUEUE_INVALID: {exc}")

    if total_chunks != EXPECTED_CHUNK_COUNT and "CORPUS_SNAPSHOT_MISSING" not in blockers:
        blockers.append(f"CHUNK_COUNT_MISMATCH: expected {EXPECTED_CHUNK_COUNT}, got {total_chunks}")

    is_valid = len(blockers) == 0

    return DataIntegrityReport(
        is_valid=is_valid,
        data_root=str(root),
        blockers=tuple(dict.fromkeys(blockers)),
        batch_version=batch_version,
        snapshot_id=snapshot_id,
        document_count=doc_count,
        chunk_count=total_chunks,
        question_count=question_count,
        queue_count=queue_count,
        hashes=hashes,
    )
