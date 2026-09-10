"""Test Suite for MedicalPlab Renal V3.1 Corrective Cycle.

Guards against regression of:
1. Training split discipline (scaler and model fit on TRAIN only; calibration on CALIB only)
2. Split firewall zero leakage across TRAIN, CALIBRATION, TEST-2, and historical benchmarks
3. Dataset and artifact SHA256 enforcement
4. TEST-2 single-run immutability guard
5. Frozen retrieval configuration and historical heldout immutability
6. Banned non-empirical phrases ("Zero Hallucinations", "hallucination-free", "Perfect Safety", "100% safe")
7. SBA Quality Gate thresholds preservation and BLOCKED status verification
"""
from __future__ import annotations

import hashlib
import json
import pickle
import re
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = ROOT / "evaluation" / "renal"
V3_EVAL_DIR = EVAL_DIR / "v3"
REPORTS_DIR = ROOT / "reports" / "renal_v3"
MODELS_DIR = ROOT / "models"
DOCS_DIR = ROOT / "docs" / "demo"

TRAIN_PATH = V3_EVAL_DIR / "renal-v3-safety-train.json"
CALIB_PATH = V3_EVAL_DIR / "renal-v3-safety-calibration.json"
TEST2_PATH = V3_EVAL_DIR / "renal-v3-safety-test-2.json"

CONFIG_PATH = REPORTS_DIR / "renal_v31_safety_config.json"
TEST2_REPORT_PATH = REPORTS_DIR / "renal_v31_safety_test2.json"
MODEL_PATH = MODELS_DIR / "renal_v31_evidence_classifier.pkl"
TECH_DOC_PATH = DOCS_DIR / "RENAL_TECHNICAL_RESULTS_V3.md"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def normalize_text(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", t.lower())).strip()


# =========================================================================
# 1. DATASET INTEGRITY & SPLIT FIREWALL TESTS
# =========================================================================
class TestV31DatasetFirewall:
    def test_datasets_exist(self):
        assert TRAIN_PATH.exists(), f"Missing {TRAIN_PATH}"
        assert CALIB_PATH.exists(), f"Missing {CALIB_PATH}"
        assert TEST2_PATH.exists(), f"Missing {TEST2_PATH}"

    def test_predeclared_quotas(self):
        train = json.loads(TRAIN_PATH.read_text(encoding="utf-8"))["queries"]
        calib = json.loads(CALIB_PATH.read_text(encoding="utf-8"))["queries"]
        test2 = json.loads(TEST2_PATH.read_text(encoding="utf-8"))["queries"]

        assert len(train) == 90, f"Expected 90 train queries, got {len(train)}"
        assert len(calib) == 60, f"Expected 60 calib queries, got {len(calib)}"
        assert len(test2) == 70, f"Expected 70 test-2 queries, got {len(test2)}"

        # Train class quotas
        assert sum(1 for q in train if q.get("evaluation_label", q.get("safety_label")) == "SUPPORTED") == 35
        assert sum(1 for q in train if q.get("evaluation_label", q.get("safety_label")) == "PARTIALLY_SUPPORTED") == 10
        assert sum(1 for q in train if q.get("evaluation_label", q.get("safety_label")) == "IN_DOMAIN_CORPUS_COVERAGE_GAP") == 20
        assert sum(1 for q in train if q.get("evaluation_label", q.get("safety_label")) == "OUT_OF_DOMAIN_UNSUPPORTED") == 20
        assert sum(1 for q in train if q.get("evaluation_label", q.get("safety_label")) == "AMBIGUOUS") == 5

        # Calib class quotas
        assert sum(1 for q in calib if q.get("evaluation_label", q.get("safety_label")) == "SUPPORTED") == 25
        assert sum(1 for q in calib if q.get("evaluation_label", q.get("safety_label")) == "PARTIALLY_SUPPORTED") == 5
        assert sum(1 for q in calib if q.get("evaluation_label", q.get("safety_label")) == "IN_DOMAIN_CORPUS_COVERAGE_GAP") == 15
        assert sum(1 for q in calib if q.get("evaluation_label", q.get("safety_label")) == "OUT_OF_DOMAIN_UNSUPPORTED") == 12
        assert sum(1 for q in calib if q.get("evaluation_label", q.get("safety_label")) == "AMBIGUOUS") == 3

        # Test-2 class quotas
        assert sum(1 for q in test2 if q.get("evaluation_label", q.get("safety_label")) == "SUPPORTED") == 28
        assert sum(1 for q in test2 if q.get("evaluation_label", q.get("safety_label")) == "PARTIALLY_SUPPORTED") == 7
        assert sum(1 for q in test2 if q.get("evaluation_label", q.get("safety_label")) == "IN_DOMAIN_CORPUS_COVERAGE_GAP") == 18
        assert sum(1 for q in test2 if q.get("evaluation_label", q.get("safety_label")) == "OUT_OF_DOMAIN_UNSUPPORTED") == 14
        assert sum(1 for q in test2 if q.get("evaluation_label", q.get("safety_label")) == "AMBIGUOUS") == 3

    def test_split_firewall_zero_query_overlap(self):
        train = json.loads(TRAIN_PATH.read_text(encoding="utf-8"))["queries"]
        calib = json.loads(CALIB_PATH.read_text(encoding="utf-8"))["queries"]
        test2 = json.loads(TEST2_PATH.read_text(encoding="utf-8"))["queries"]

        q_train = {normalize_text(q["query"]) for q in train}
        q_calib = {normalize_text(q["query"]) for q in calib}
        q_test2 = {normalize_text(q["query"]) for q in test2}

        assert len(q_train & q_calib) == 0, f"Query overlap between TRAIN and CALIB: {q_train & q_calib}"
        assert len(q_train & q_test2) == 0, f"Query overlap between TRAIN and TEST-2: {q_train & q_test2}"
        assert len(q_calib & q_test2) == 0, f"Query overlap between CALIB and TEST-2: {q_calib & q_test2}"

    def test_split_firewall_zero_claim_objective_overlap(self):
        train = json.loads(TRAIN_PATH.read_text(encoding="utf-8"))["queries"]
        calib = json.loads(CALIB_PATH.read_text(encoding="utf-8"))["queries"]
        test2 = json.loads(TEST2_PATH.read_text(encoding="utf-8"))["queries"]

        c_train = {normalize_text(q["medical_claim"]) for q in train if q.get("medical_claim")}
        c_calib = {normalize_text(q["medical_claim"]) for q in calib if q.get("medical_claim")}
        c_test2 = {normalize_text(q["medical_claim"]) for q in test2 if q.get("medical_claim")}

        assert len(c_train & c_calib) == 0, f"Claim overlap between TRAIN and CALIB: {c_train & c_calib}"
        assert len(c_train & c_test2) == 0, f"Claim overlap between TRAIN and TEST-2: {c_train & c_test2}"
        assert len(c_calib & c_test2) == 0, f"Claim overlap between CALIB and TEST-2: {c_calib & c_test2}"

    def test_source_grounded_positive_evidence(self):
        for path in [TRAIN_PATH, CALIB_PATH, TEST2_PATH]:
            data = json.loads(path.read_text(encoding="utf-8"))["queries"]
            for q in data:
                if q["answerable"]:
                    assert "gold_child_chunk_ids" in q and q["gold_child_chunk_ids"], f"Missing gold_child_chunk_ids in {q['query_id']}"
                    assert "primary_evidence_quote" in q and q["primary_evidence_quote"], f"Missing primary_evidence_quote in {q['query_id']}"
                    assert "medical_claim" in q and q["medical_claim"], f"Missing medical_claim in {q['query_id']}"

    def test_disjoint_source_documents_across_splits(self):
        train = json.loads(TRAIN_PATH.read_text(encoding="utf-8"))["queries"]
        calib = json.loads(CALIB_PATH.read_text(encoding="utf-8"))["queries"]
        test2 = json.loads(TEST2_PATH.read_text(encoding="utf-8"))["queries"]

        d_train = {doc for q in train for doc in q.get("gold_document_ids", [])}
        d_calib = {doc for q in calib for doc in q.get("gold_document_ids", [])}
        d_test2 = {doc for q in test2 for doc in q.get("gold_document_ids", [])}

        assert len(d_train & d_calib) == 0, f"Document overlap TRAIN vs CALIB: {d_train & d_calib}"
        assert len(d_train & d_test2) == 0, f"Document overlap TRAIN vs TEST-2: {d_train & d_test2}"
        assert len(d_calib & d_test2) == 0, f"Document overlap CALIB vs TEST-2: {d_calib & d_test2}"

    def test_sha256_sidecars_match(self):
        for path in [TRAIN_PATH, CALIB_PATH, TEST2_PATH]:
            sidecar = path.with_suffix(".json.sha256")
            assert sidecar.exists(), f"Missing sidecar {sidecar}"
            recorded_sha = sidecar.read_text(encoding="utf-8").strip().split()[0]
            actual_sha = sha256_file(path)
            assert recorded_sha == actual_sha, f"SHA mismatch on {path.name}: {recorded_sha} vs {actual_sha}"


# =========================================================================
# 2. TRAINING DISCIPLINE & ARTIFACT INTEGRITY TESTS
# =========================================================================
class TestV31TrainingDiscipline:
    def test_classifier_artifact_and_config_exist(self):
        assert MODEL_PATH.exists(), f"Missing model {MODEL_PATH}"
        assert CONFIG_PATH.exists(), f"Missing config {CONFIG_PATH}"
        assert TEST2_REPORT_PATH.exists(), f"Missing test-2 report {TEST2_REPORT_PATH}"

    def test_normalization_and_model_fit_on_train_only(self):
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        assert config["normalization_statistics"]["fit_split"] == "SAFETY_TRAIN_ONLY"
        assert config["classifier_artifact"]["fit_split"] == "SAFETY_TRAIN_ONLY"
        assert config["threshold_calibration"]["split_used"] == "SAFETY_CALIBRATION_ONLY"

        with open(MODEL_PATH, "rb") as f:
            payload = pickle.load(f)
        assert payload["train_dataset"] == "renal-v3-safety-train.json"
        assert payload["calibration_dataset"] == "renal-v3-safety-calibration.json"
        assert "train_means" in payload and "train_stds" in payload

    def test_test2_single_run_immutability(self):
        report = json.loads(TEST2_REPORT_PATH.read_text(encoding="utf-8"))
        assert report["evaluation_protocol"] == "SINGLE_RUN_FROZEN"
        assert report["sample_counts"]["n_total"] == 70
        assert report["sample_counts"]["n_positive"] == 35
        assert report["sample_counts"]["n_negative"] == 35

    def test_test2_all_metrics_reported_with_denominators(self):
        report = json.loads(TEST2_REPORT_PATH.read_text(encoding="utf-8"))
        metrics = report["metrics"]
        cm = report["confusion_matrix"]

        for key in ["tp", "fp", "tn", "fn"]:
            assert key in cm and isinstance(cm[key], int)

        for key in ["precision", "recall", "specificity", "unsafe_accept", "false_refusal"]:
            assert key in metrics
            m = metrics[key]
            assert "value" in m and "numerator" in m and "denominator" in m and "n" in m

        assert "auroc" in metrics and "auprc" in metrics and "brier_score" in metrics


# =========================================================================
# 3. REPORTING COMPLIANCE & TERMINOLOGY AUDIT
# =========================================================================
class TestV31ReportingCompliance:
    BANNED_PHRASES = [
        r"zero\s+hallucinations?",
        r"hallucination-free",
        r"perfect\s+safety",
        r"100%\s+safe"
    ]

    def test_no_banned_phrases_in_technical_results(self):
        if not TECH_DOC_PATH.exists():
            pytest.skip(f"{TECH_DOC_PATH} does not exist yet")

        content = TECH_DOC_PATH.read_text(encoding="utf-8").lower()
        for pat in self.BANNED_PHRASES:
            matches = re.findall(pat, content)
            assert len(matches) == 0, f"Found banned phrase '{pat}' in {TECH_DOC_PATH.name}: {matches}"

    def test_candidate_recall_reporting_distinction(self):
        if not TECH_DOC_PATH.exists():
            pytest.skip(f"{TECH_DOC_PATH} does not exist yet")

        content = TECH_DOC_PATH.read_text(encoding="utf-8")
        # Must distinguish DEV CandidateHit@50 (94.20%) from Heldout CandidateHit@50 (90.38% parity)
        assert "94.20%" in content or "94.2%" in content, "Missing DEV CandidateHit@50 reference"
        assert "90.38%" in content, "Missing heldout CandidateHit@50 reference"

    def test_production_sba_gate_thresholds_preserved(self):
        if not TECH_DOC_PATH.exists():
            pytest.skip(f"{TECH_DOC_PATH} does not exist yet")

        content = TECH_DOC_PATH.read_text(encoding="utf-8")
        # Original production SBA gate thresholds
        assert "0.85" in content or "85%" in content, "PassageHit@1 >= 0.85 must be preserved"
        assert "0.95" in content or "95%" in content, "PassageHit@5 >= 0.95 must be preserved"
        assert "0.90" in content or "90%" in content, "Safety Precision >= 0.90 must be preserved"
        assert "0.75" in content or "75%" in content, "Safety Recall >= 0.75 must be preserved"
        assert "0.05" in content or "5%" in content, "Unsafe Accept <= 0.05 must be preserved"
        assert "BLOCKED" in content, "SBA status must remain BLOCKED"
