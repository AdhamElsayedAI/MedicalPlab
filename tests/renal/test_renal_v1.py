"""Integrity and safety gates for the frozen Renal / Urinary v1 release."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Data"
EVAL = ROOT / "evaluation" / "renal"
EXPECTED_HELDOUT_SHA = "cd7483673d8eb3aa6f85ced541a7eaad8b7c1d003b857ff1e43b6146609c26c5"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_frozen_heldout_integrity_and_counts():
    path = EVAL / "renal-heldout-v1.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED_HELDOUT_SHA
    assert (EVAL / "renal-heldout-v1.json.sha256").read_text().split()[0] == EXPECTED_HELDOUT_SHA
    queries = load(path)["queries"]
    assert len(queries) == 56
    assert sum(bool(query["answerable"]) for query in queries) == 48
    assert sum(not query["answerable"] for query in queries) == 8


def test_frozen_corpus_and_licenses_resolve():
    snapshot = load(DATA / "metadata" / "corpus_renal_snapshot_v1.json")
    licenses = load(DATA / "metadata" / "renal_source_license_manifest_v1.json")["entries"]
    assert snapshot["state"] == "FROZEN"
    assert snapshot["document_count"] == 16
    assert snapshot["total_chunks"] == 2192
    assert len(licenses) == 16
    assert all(item["rag_ingestion_decision"] is True for item in licenses)
    assert all(item["commercial_use"] is True for item in licenses)
    assert all(item["license"].startswith("CC BY") for item in licenses)


def test_benchmark_is_single_run_and_sba_gate_is_closed():
    report = load(ROOT / "reports" / "renal_benchmark_v1.json")
    snapshot = load(DATA / "metadata" / "corpus_renal_snapshot_v1.json")
    assert report["measurement_status"] == "FROZEN_SINGLE_HELDOUT_RUN"
    assert report["heldout_run_count"] == 1
    assert report["heldout_sha256"] == EXPECTED_HELDOUT_SHA
    assert report["heldout"]["hit_at_1"] == {"value": 0.625, "numerator": 30, "denominator": 48}
    assert report["evidence_sufficiency"]["confusion_matrix"] == {"tp": 2, "tn": 24, "fp": 0, "fn": 14}
    assert snapshot["quality_gate"] == {
        "retrieval_targets_met": False,
        "evidence_targets_met": False,
        "renal_sba_generation_allowed": False,
        "human_reviewed": 0,
        "golden": 0,
    }


def test_all_eval_citations_resolve_to_selected_chunks():
    chunk_ids = set()
    for path in (DATA / "experiments" / "renal" / "chunking" / "C_section_aware").glob("*.chunks.json"):
        chunk_ids.update(item["chunk_id"] for item in load(path)["chunks"])
    expected = []
    for name in ("renal-dev-v1.json", "renal-calibration-v1.json", "renal-heldout-v1.json"):
        for query in load(EVAL / name)["queries"]:
            expected.extend(query.get("gold_chunk_ids", []))
    assert len(expected) == 128
    assert all(chunk_id in chunk_ids for chunk_id in expected)
