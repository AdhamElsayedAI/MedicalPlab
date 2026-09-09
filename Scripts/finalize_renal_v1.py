"""Freeze Renal v1 manifests and annotate the single-run benchmark honestly."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data"
EVAL = ROOT / "evaluation" / "renal"
REPORT_PATH = ROOT / "reports" / "renal_benchmark_v1.json"
SNAPSHOT_PATH = DATA / "metadata" / "corpus_renal_snapshot_v1.json"
EXPECTED_HELDOUT_SHA = "cd7483673d8eb3aa6f85ced541a7eaad8b7c1d003b857ff1e43b6146609c26c5"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_chunks(folder: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    chunks: list[dict[str, object]] = []
    files: list[dict[str, object]] = []
    for path in sorted(folder.glob("*.chunks.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        file_chunks = payload.get("chunks", [])
        chunks.extend(file_chunks)
        files.append({
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256(path),
            "chunk_count": len(file_chunks),
        })
    return chunks, files


def main() -> None:
    heldout_path = EVAL / "renal-heldout-v1.json"
    actual_sha = sha256(heldout_path)
    recorded_sha = (EVAL / "renal-heldout-v1.json.sha256").read_text(encoding="utf-8").split()[0]
    if actual_sha != EXPECTED_HELDOUT_SHA or recorded_sha != EXPECTED_HELDOUT_SHA:
        raise SystemExit(f"HELDOUT_INTEGRITY_FAILURE: actual={actual_sha} recorded={recorded_sha}")

    registry = json.loads((DATA / "metadata" / "renal_source_registry_v1.json").read_text(encoding="utf-8"))
    license_manifest = json.loads((DATA / "metadata" / "renal_source_license_manifest_v1.json").read_text(encoding="utf-8"))
    documents = [item for item in registry["documents"] if item.get("status") == "accepted"]
    accepted_ids = {str(item["document_id"]) for item in documents}
    chunks, chunk_files = load_chunks(DATA / "experiments" / "renal" / "chunking" / "C_section_aware")
    chunk_ids = {str(item["chunk_id"]) for item in chunks}

    registry_resolved = sum(str(item.get("document_id")) in accepted_ids for item in chunks)
    citation_pairs_resolved = sum(
        str(item.get("chunk_id")) in chunk_ids and str(item.get("document_id")) in accepted_ids
        for item in chunks
    )
    gold_ids: list[str] = []
    for name in ("renal-dev-v1.json", "renal-calibration-v1.json", "renal-heldout-v1.json"):
        payload = json.loads((EVAL / name).read_text(encoding="utf-8"))
        for query in payload["queries"]:
            gold_ids.extend(str(value) for value in query.get("gold_chunk_ids", []))
    gold_resolved = sum(value in chunk_ids for value in gold_ids)

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    report["measurement_status"] = "FROZEN_SINGLE_HELDOUT_RUN"
    report["heldout_run_count"] = 1
    report["metric_definitions"] = {
        "hit_at_k": "answerable queries with at least one gold-document and gold-section match in top k",
        "recall_at_k": "query-level gold-evidence recall; identical to Hit@k for this one-anchor-per-query set",
        "gold_source_recall_at_k": "answerable queries with at least one gold document in top k",
        "evidence_support_rate": "frozen heldout answerable queries with gold evidence in top 5",
    }
    for k in (1, 3, 5, 10):
        report["heldout"][f"recall_at_{k}"] = dict(report["heldout"][f"hit_at_{k}"])
        for variant in report["chunking_dev"].values():
            variant[f"recall_at_{k}"] = dict(variant[f"hit_at_{k}"])
        for variant in report["dense_dev"].values():
            variant[f"recall_at_{k}"] = dict(variant[f"hit_at_{k}"])
    authority = report["heldout"]["authority_sensitive_accuracy"]
    authority["numerator"] = round(authority["value"] * authority["denominator"])
    report["citation_integrity"] = {
        "citation_resolution_rate": {"value": gold_resolved / len(gold_ids), "numerator": gold_resolved, "denominator": len(gold_ids)},
        "citation_source_match": {"value": citation_pairs_resolved / len(chunks), "numerator": citation_pairs_resolved, "denominator": len(chunks)},
        "registry_resolution_rate": {"value": registry_resolved / len(chunks), "numerator": registry_resolved, "denominator": len(chunks)},
        "evidence_support_rate_at_5": dict(report["heldout"]["hit_at_5"]),
    }
    report["dev_failure_analysis"] = {
        "selected_configuration": "metadata_aware",
        "answerable_n": 48,
        "misses_at_1": 48 - report["dense_dev"]["metadata_aware"]["hit_at_1"]["numerator"],
        "misses_at_5": 48 - report["dense_dev"]["metadata_aware"]["hit_at_5"]["numerator"],
        "misses_at_10": 48 - report["dense_dev"]["metadata_aware"]["hit_at_10"]["numerator"],
        "finding": "Metadata improved MRR and Hit@1 over content/source representations, but section-level localization remained the dominant measured failure.",
        "limitation": "The first benchmark did not persist per-query rankings; no per-query failure list is reconstructed or fabricated.",
    }
    report["latency"]["evidence_decision_p50_ms"] = None
    report["latency"]["evidence_decision_p95_ms"] = None
    report["latency"]["evidence_decision_note"] = "Not separately instrumented in the frozen run."
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    license_by_doc = {str(item["document_id"]): item for item in license_manifest["entries"]}
    snapshot = {
        "corpus_id": "medicalplab-renal-corpus-v1",
        "version": "1.0.0",
        "state": "FROZEN",
        "starting_repository_commit": "070325a",
        "document_count": len(documents),
        "total_chunks": len(chunks),
        "chunking": "C_section_aware",
        "representation": "metadata_aware",
        "embedding_model": "Qwen/Qwen3-Embedding-0.6B",
        "embedding_dimensions": 1024,
        "max_sequence_length": 512,
        "evidence_sufficiency_threshold": report["evidence_sufficiency"]["threshold"],
        "heldout_sha256": actual_sha,
        "benchmark_report": REPORT_PATH.relative_to(ROOT).as_posix(),
        "benchmark_report_sha256": sha256(REPORT_PATH),
        "documents": [
            {
                "document_id": item["document_id"],
                "pmcid": item["pmcid"],
                "title": item["title"],
                "license": license_by_doc[str(item["document_id"])]["license"],
                "raw_sha256": license_by_doc[str(item["document_id"])]["sha256"],
            }
            for item in documents
        ],
        "chunk_files": chunk_files,
        "quality_gate": {
            "retrieval_targets_met": False,
            "evidence_targets_met": False,
            "renal_sba_generation_allowed": False,
            "human_reviewed": 0,
            "golden": 0,
        },
    }
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"heldout_sha256": actual_sha, "documents": len(documents), "chunks": len(chunks), "citations": report["citation_integrity"]}, indent=2))


if __name__ == "__main__":
    main()
