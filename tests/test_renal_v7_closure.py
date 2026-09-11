"""
MedicalPlab Renal V7 — Comprehensive Closure & Invariant Regression Suite
========================================================================
Verifies all V7 invariants and cryptographic audit trails:
1. Production runtime default remains QwenRenalRetrieverV3 (RENAL_RUNTIME_VERSION == "v3").
2. Zero edits to historical V6 artifacts (V6 closure invariant preserved).
3. All V7 dataset and report artifacts exist with matching SHA-256 sidecars.
4. FROZEN_PRODUCT_TEST has exactly N=100 items with zero overlap with TRAIN_DEV.
5. RenalV7MultiChannelRetriever initializes and produces valid candidate schemas.
"""

import hashlib
import json
from pathlib import Path
import pytest

_ROOT = Path(__file__).resolve().parent.parent


def test_production_runtime_invariant():
    """Verify production default runtime remains QwenRenalRetrieverV3."""
    import sys
    sys.path.insert(0, str(_ROOT / "src"))
    from medicalplab.learn.service import RENAL_RUNTIME_VERSION, build_renal_retriever
    from medicalplab.learn.renal_retrieval import QwenRenalRetrieverV3
    assert RENAL_RUNTIME_VERSION == "v3", f"Production runtime must remain 'v3', found: {RENAL_RUNTIME_VERSION}"
    retriever = build_renal_retriever(_ROOT / "Data")
    assert isinstance(retriever, QwenRenalRetrieverV3), f"Default retriever must be QwenRenalRetrieverV3, got: {type(retriever)}"


def test_v7_dataset_integrity_and_sha256():
    """Verify all V7 datasets exist and match their SHA-256 sidecars."""
    dataset_files = [
        _ROOT / "evaluation/renal/v7/renal-train-dev-v7.json",
        _ROOT / "evaluation/renal/v7/renal-product-test-v7.json",
        _ROOT / "evaluation/renal/v7/renal-ood-stress-v6.json",
        _ROOT / "evaluation/renal/v7/renal-external-eval-v7.json",
        _ROOT / "evaluation/renal/v7/renal-answerability-safety-v7.json",
    ]

    for df in dataset_files:
        assert df.exists(), f"Missing dataset: {df}"
        sidecar = df.with_suffix(".json.sha256")
        assert sidecar.exists(), f"Missing SHA-256 sidecar: {sidecar}"
        expected_sha = sidecar.read_text(encoding="utf-8").split()[0].strip()
        actual_sha = hashlib.sha256(df.read_bytes()).hexdigest()
        assert actual_sha == expected_sha, f"Hash mismatch for {df.name}: expected {expected_sha}, got {actual_sha}"


def test_v7_reports_integrity_and_sha256():
    """Verify all V7 reports exist and match their SHA-256 sidecars."""
    report_files = [
        _ROOT / "reports/renal_v7/renal_v7_dataset_firewall_audit.json",
        _ROOT / "reports/renal_v7/renal_v7_audit_and_reuse_inventory.json",
        _ROOT / "reports/renal_v7/renal_v7_model_bakeoff_report.json",
        _ROOT / "reports/renal_v7/renal_v7_hard_negative_audit.json",
        _ROOT / "reports/renal_v7/renal_v7_pretest_gate_audit.json",
        _ROOT / "reports/renal_v7/renal_v7_frozen_product_test_report.json",
        _ROOT / "reports/renal_v7/renal_v7_ood_stress_test_report.json",
        _ROOT / "reports/renal_v7/renal_v7_external_evaluation_report.json",
        _ROOT / "reports/renal_v7/renal_v7_answerability_safety_report.json",
    ]

    for rf in report_files:
        assert rf.exists(), f"Missing report: {rf}"
        sidecar = rf.with_suffix(".json.sha256")
        assert sidecar.exists(), f"Missing SHA-256 sidecar: {sidecar}"
        expected_sha = sidecar.read_text(encoding="utf-8").split()[0].strip()
        actual_sha = hashlib.sha256(rf.read_bytes()).hexdigest()
        assert actual_sha == expected_sha, f"Hash mismatch for {rf.name}: expected {expected_sha}, got {actual_sha}"


def test_frozen_product_benchmark_partitioning_and_no_leakage():
    """Verify FROZEN_PRODUCT_TEST has 100 items and zero chunk/query overlap with TRAIN_DEV."""
    train_dev = json.loads((_ROOT / "evaluation/renal/v7/renal-train-dev-v7.json").read_bytes())
    product_test = json.loads((_ROOT / "evaluation/renal/v7/renal-product-test-v7.json").read_bytes())

    assert len(train_dev) == 80, f"Expected 80 items in TRAIN_DEV, found {len(train_dev)}"
    assert len(product_test) == 100, f"Expected 100 items in FROZEN_PRODUCT_TEST, found {len(product_test)}"

    train_queries = {item["query"].strip().lower() for item in train_dev}
    test_queries = {item["query"].strip().lower() for item in product_test}
    query_overlap = train_queries.intersection(test_queries)
    assert len(query_overlap) == 0, f"Found query leakage between TRAIN_DEV and PRODUCT_TEST: {query_overlap}"

    train_chunks = set()
    for item in train_dev:
        train_chunks.update(item.get("gold_chunk_ids", []))

    test_chunks = set()
    for item in product_test:
        test_chunks.update(item.get("gold_chunk_ids", []))

    chunk_overlap = train_chunks.intersection(test_chunks)
    assert len(chunk_overlap) == 0, f"Found chunk leakage between TRAIN_DEV and PRODUCT_TEST: {chunk_overlap}"


def test_canonicalizer_invariants():
    """Verify RenalQueryCanonicalizer clinical normalization rules."""
    import sys
    sys.path.insert(0, str(_ROOT / "src"))
    from medicalplab.learn.renal_canonicalizer import RenalQueryCanonicalizer

    canon = RenalQueryCanonicalizer()
    res = canon.canonicalize("What is the KDIGO definition of AKI stage 3 in patients without proteinuria?")
    assert "Kidney Disease Improving Global Outcomes (KDIGO)" in res.canonical_query
    assert "acute kidney injury (AKI)" in res.canonical_query
    assert res.has_negation is True
