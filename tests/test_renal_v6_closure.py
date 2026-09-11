"""
Unit and Regression Tests for MedicalPlab Renal V6 Formal Closure & Audit
========================================================================
Verifies all closure invariants required by the V6 Forensic Post-Mortem:
1. Canonical metrics are strictly preserved:
   - TRAIN Raw Dense Coverage@20 = 73.75% (59/80)
   - TRAIN Selector OOF Coverage@20 = 93.75% (75/80)
   - SELECT_VAL Raw Dense Coverage@20 = 37.50% (15/40)
   - SELECT_VAL Raw Dense Coverage@500 = 90.00% (36/40)
   - SELECT_VAL Selector Coverage@20 = 45.00% (18/40)
2. Predeclared gate thresholds:
   - STRONG PASS: >= 95.0%
   - CONDITIONAL PASS: >= 92.0%
   - FAIL: < 92.0%
   - Verdict: FAIL_COVERAGE_BELOW_92
3. Benchmark interpretation:
   - VALID_AS_DIAGNOSTIC_STRESS_TEST
   - NOT_VALID_AS_A_LIKE_FOR_LIKE_ESTIMATE_OF_THE_ORIGINAL_CLINICAL_QUERY_DISTRIBUTION
4. Root cause classification:
   - Primary: BENCHMARK_CONSTRUCTION_INCONSISTENCY
   - Secondary: FIRST_STAGE_ACQUISITION_FAILURE, BENCHMARK_DISTRIBUTION_SHIFT
5. HistGB status:
   - NOT_ELIGIBLE_FOR_RETROSPECTIVE_EXECUTION
6. Production runtime preservation:
   - RENAL_RUNTIME_VERSION == 'v3'
   - Production default retriever is QwenRenalRetrieverV3
   - LoRA remains BLOCKED
   - DEV-B remains UNEXECUTED
   - Final Heldout remains UNEXECUTED
7. SHA256 integrity:
   - All report artifacts match their sha256 sidecars.
"""

import hashlib
import json
from pathlib import Path
import pytest

_ROOT = Path(__file__).resolve().parent.parent
_REPORTS_V6 = _ROOT / "reports" / "renal_v6"
_DOCS_DEMO = _ROOT / "docs" / "demo"


def _verify_sha256_sidecar(file_path: Path, sidecar_path: Path):
    assert file_path.exists(), f"File {file_path} missing!"
    assert sidecar_path.exists(), f"Sidecar {sidecar_path} missing!"
    actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
    sidecar_hash = sidecar_path.read_text(encoding="utf-8").strip().split()[0]
    assert actual_hash == sidecar_hash, (
        f"Hash mismatch for {file_path.name}: computed {actual_hash} != sidecar {sidecar_hash}"
    )


class TestRenalV6ProductionDefaultPreserved:
    """Ensure V3 remains the sole production runtime default."""

    def test_renal_runtime_version_is_v3(self):
        from medicalplab.learn.service import RENAL_RUNTIME_VERSION
        assert RENAL_RUNTIME_VERSION == "v3"

    def test_service_instantiates_v3_by_default(self):
        from medicalplab.learn.service import CourseLearningService
        from medicalplab.learn.renal_retrieval import QwenRenalRetrieverV3
        service = CourseLearningService()
        assert isinstance(service._renal_retriever, QwenRenalRetrieverV3)
        assert service._renal_runtime_version == "v3"

    def test_v6_cannot_silently_become_default(self):
        from medicalplab.learn.service import build_renal_retriever
        from medicalplab.learn.renal_retrieval import QwenRenalRetrieverV3
        default_retriever = build_renal_retriever(_ROOT / "Data")
        assert isinstance(default_retriever, QwenRenalRetrieverV3)
        fallback_retriever = build_renal_retriever(_ROOT / "Data", version="v6")
        assert isinstance(fallback_retriever, QwenRenalRetrieverV3)


class TestRenalV6CanonicalMetrics:
    """Verify exact canonical metric values across V6 forensic audit artifacts."""

    def test_forensic_audit_canonical_metrics(self):
        audit_file = _REPORTS_V6 / "renal_v6_forensic_post_mortem_audit.json"
        assert audit_file.exists()
        data = json.loads(audit_file.read_bytes())

        metrics = data["canonical_metrics"]
        assert metrics["train_n80"]["raw_dense_baseline_coverage_at_20"] == "59 / 80 = 73.75%"
        assert metrics["train_n80"]["selected_class_a_selector_oof_coverage_at_20"] == "75 / 80 = 93.75%"
        assert metrics["train_n80"]["selected_class_a_worst_fold"] == "86.67%"
        assert metrics["train_n80"]["selected_class_a_naive_preservation"] == "98.31%"

        assert metrics["frozen_select_val_n40"]["raw_dense_coverage_at_20"] == "15 / 40 = 37.50%"
        assert metrics["frozen_select_val_n40"]["raw_dense_coverage_at_50"] == "24 / 40 = 60.00%"
        assert metrics["frozen_select_val_n40"]["raw_dense_coverage_at_100"] == "26 / 40 = 65.00%"
        assert metrics["frozen_select_val_n40"]["raw_dense_coverage_at_200"] == "30 / 40 = 75.00%"
        assert metrics["frozen_select_val_n40"]["raw_dense_coverage_at_500"] == "36 / 40 = 90.00%"
        assert metrics["frozen_select_val_n40"]["frozen_class_a_selector_coverage_at_20"] == "18 / 40 = 45.00%"

    def test_distinction_between_raw_dense_and_selector(self):
        audit_file = _REPORTS_V6 / "renal_v6_forensic_post_mortem_audit.json"
        data = json.loads(audit_file.read_bytes())
        dist = data["canonical_metrics"]["explicit_distinction"]
        assert "73.75%" in dist["raw_dense_train_coverage_at_20"]
        assert "93.75%" in dist["selector_train_oof_coverage_at_20"]
        assert "37.50%" in dist["raw_dense_select_val_coverage_at_20"]
        assert "45.00%" in dist["selector_select_val_coverage_at_20"]


class TestRenalV6GovernanceAndGates:
    """Verify gate definitions, classifications, and governance rules."""

    def test_gate_language(self):
        audit_file = _REPORTS_V6 / "renal_v6_forensic_post_mortem_audit.json"
        data = json.loads(audit_file.read_bytes())
        gates = data["v6_gate_language"]["predeclared_gates"]
        assert gates["strong_pass"] == "Coverage@20 >= 95.0%"
        assert gates["conditional_pass"] == "Coverage@20 >= 92.0%"
        assert gates["fail"] == "Coverage@20 < 92.0%"
        assert data["v6_gate_language"]["gate_verdict"] == "FAIL_COVERAGE_BELOW_92"

    def test_benchmark_interpretation(self):
        audit_file = _REPORTS_V6 / "renal_v6_forensic_post_mortem_audit.json"
        data = json.loads(audit_file.read_bytes())
        classes = data["benchmark_interpretation"]["benchmark_classifications"]
        assert "VALID_AS_DIAGNOSTIC_STRESS_TEST" in classes
        assert "NOT_VALID_AS_A_LIKE_FOR_LIKE_ESTIMATE_OF_THE_ORIGINAL_CLINICAL_QUERY_DISTRIBUTION" in classes

    def test_root_cause_classification(self):
        audit_file = _REPORTS_V6 / "renal_v6_forensic_post_mortem_audit.json"
        data = json.loads(audit_file.read_bytes())
        rc = data["section_10_root_cause_classification"]
        assert rc["primary_root_cause"] == "BENCHMARK_CONSTRUCTION_INCONSISTENCY"
        sec = " ".join(rc["secondary_contributing_causes"])
        assert "FIRST_STAGE_ACQUISITION_FAILURE" in sec
        assert "BENCHMARK_DISTRIBUTION_SHIFT" in sec

    def test_histgb_governance(self):
        audit_file = _REPORTS_V6 / "renal_v6_forensic_post_mortem_audit.json"
        data = json.loads(audit_file.read_bytes())
        assert data["section_8_histgb_governance"]["HISTGB_STATUS"] == "NOT_ELIGIBLE_FOR_RETROSPECTIVE_EXECUTION"

    def test_final_status_block(self):
        audit_file = _REPORTS_V6 / "renal_v6_forensic_post_mortem_audit.json"
        data = json.loads(audit_file.read_bytes())
        status = data["section_11_final_status_and_recommendation"]
        assert status["V6_STATUS"] == "RESEARCH_DIAGNOSTIC_NOT_PRODUCTION_PROMOTED"
        assert status["LORA_STATUS"] == "BLOCKED"
        assert status["PRODUCTION_RUNTIME"] == "QwenRenalRetrieverV3"
        assert status["RENAL_RUNTIME_VERSION"] == "v3"
        assert status["DEV_B_STATUS"] == "UNEXECUTED_FOR_PERFORMANCE"
        assert status["FINAL_HELDOUT_STATUS"] == "UNEXECUTED_PRESERVED"
        assert status["FINAL_RECOMMENDATION"] == "PRESERVE_V3_AND_MOVE_TO_PLAB"
        assert status["v7_authorized"] is False


class TestRenalV6ArtifactsAndSidecars:
    """Verify bit-for-bit SHA-256 sidecars for all V6 report artifacts."""

    @pytest.mark.parametrize("filename", [
        "renal_v6_phase1_expansion_feasibility_report.json",
        "renal_v6_phase2_failure_decomposition_report.json",
        "renal_v6_phase3_feature_oracle_v2_report.json",
        "renal_v6_phase4_selector_comparison_report.json",
        "renal_v6_phase5_gating_decision_report.json",
        "renal_v6_phase6_confirmation_report.json",
        "renal_v6_fresh_validation_firewall_audit.json",
        "renal_v6_decision_package.json",
        "renal_v6_forensic_post_mortem_audit.json",
    ])
    def test_v6_report_sha256_sidecars(self, filename):
        file_path = _REPORTS_V6 / filename
        sidecar_path = _REPORTS_V6 / f"{filename}.sha256"
        _verify_sha256_sidecar(file_path, sidecar_path)

    def test_v6_technical_results_doc_exists(self):
        doc = _DOCS_DEMO / "RENAL_TECHNICAL_RESULTS_V6.md"
        assert doc.exists()
        content = doc.read_text(encoding="utf-8")
        assert "73.75%" in content
        assert "93.75%" in content
        assert "37.50%" in content
        assert "45.00%" in content
        assert "FAIL_COVERAGE_BELOW_92" in content
        assert "VALID_AS_DIAGNOSTIC_STRESS_TEST" in content
        assert "BENCHMARK_CONSTRUCTION_INCONSISTENCY" in content
        assert "PRESERVE_V3_AND_MOVE_TO_PLAB" in content
