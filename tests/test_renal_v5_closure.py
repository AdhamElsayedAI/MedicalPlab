"""
Unit and Regression Tests for MedicalPlab Renal V5 Formal Closure
================================================================
Verifies all closure invariants required by Phase 1:
1. Production default runtime version remains 'v3'.
2. CourseLearningService defaults to QwenRenalRetrieverV3.
3. V5 / P3 cannot silently become default.
4. Frozen V5 clean artifacts match their SHA256 sidecars bit-for-bit.
5. No DEV-B artifact was executed for performance (DEV-B remains unspent).
6. Explicit closure states:
   - SELECTOR_V5_P3 = RESEARCH_VALIDATED_NOT_PRODUCTION_PROMOTED
   - LoRA NOT RUN
   - DEV-B PERFORMANCE NOT RUN
   - FINAL_V5_HELDOUT NOT RUN
   - safety workstream NOT fully promoted
   - V5 is therefore NOT production promoted
"""

import hashlib
import json
from pathlib import Path
import pytest

_ROOT = Path(__file__).resolve().parent.parent
_EVAL_V5 = _ROOT / "evaluation" / "renal" / "v5"
_REPORTS_V5 = _ROOT / "reports" / "renal_v5"
_DOCS = _ROOT / "docs" / "demo"


def _verify_sha256_sidecar(file_path: Path, sidecar_path: Path):
    assert file_path.exists(), f"File {file_path} missing!"
    assert sidecar_path.exists(), f"Sidecar {sidecar_path} missing!"
    actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
    sidecar_hash = sidecar_path.read_text(encoding="utf-8").strip().split()[0]
    assert actual_hash == sidecar_hash, (
        f"Hash mismatch for {file_path.name}: computed {actual_hash} != sidecar {sidecar_hash}"
    )


class TestRenalV5ProductionDefaultPreserved:
    """Ensure V3 remains the sole production runtime default."""

    def test_renal_runtime_version_is_v3(self):
        from medicalplab.learn.service import RENAL_RUNTIME_VERSION
        assert RENAL_RUNTIME_VERSION == "v3", (
            f"Production default must be 'v3', found '{RENAL_RUNTIME_VERSION}'"
        )

    def test_service_instantiates_v3_by_default(self):
        from medicalplab.learn.service import CourseLearningService
        from medicalplab.learn.renal_retrieval import QwenRenalRetrieverV3
        service = CourseLearningService()
        assert isinstance(service._renal_retriever, QwenRenalRetrieverV3), (
            f"Default retriever must be QwenRenalRetrieverV3, got {type(service._renal_retriever).__name__}"
        )
        assert service._renal_runtime_version == "v3"

    def test_v5_cannot_silently_become_default(self):
        from medicalplab.learn.service import build_renal_retriever
        from medicalplab.learn.renal_retrieval import QwenRenalRetrieverV3
        # Calling factory with default version must return V3
        default_retriever = build_renal_retriever(_ROOT / "Data")
        assert isinstance(default_retriever, QwenRenalRetrieverV3)
        # Attempting unspecified or unsupported version falls back safely to V3 (never V5)
        fallback_retriever = build_renal_retriever(_ROOT / "Data", version="v5")
        assert isinstance(fallback_retriever, QwenRenalRetrieverV3)
        assert default_retriever.__class__.__name__ == "QwenRenalRetrieverV3"


class TestRenalV5ArtifactsAndSHAsPreserved:
    """Verify bit-for-bit preservation of all frozen clean V5 evaluation and specification artifacts."""

    def test_clean_train_v1_sha(self):
        _verify_sha256_sidecar(
            _EVAL_V5 / "renal-rerank-train-v5-clean-v1.json",
            _EVAL_V5 / "renal-rerank-train-v5-clean-v1.json.sha256"
        )

    def test_clean_train_core_v1_sha(self):
        _verify_sha256_sidecar(
            _EVAL_V5 / "renal-rerank-train-core-v5-clean-v1.json",
            _EVAL_V5 / "renal-rerank-train-core-v5-clean-v1.json.sha256"
        )

    def test_clean_train_val_v1_sha(self):
        _verify_sha256_sidecar(
            _EVAL_V5 / "renal-rerank-train-val-v5-clean-v1.json",
            _EVAL_V5 / "renal-rerank-train-val-v5-clean-v1.json.sha256"
        )

    def test_clean_select_val_v1_sha(self):
        _verify_sha256_sidecar(
            _EVAL_V5 / "renal-rerank-select-val-clean-v1.json",
            _EVAL_V5 / "renal-rerank-select-val-clean-v1.json.sha256"
        )

    def test_p3_model_specification_sha(self):
        _verify_sha256_sidecar(
            _REPORTS_V5 / "renal_v5_p3_model_specification.json",
            _REPORTS_V5 / "renal_v5_p3_model_specification.json.sha256"
        )

    def test_quarantined_artifacts_preserved(self):
        _verify_sha256_sidecar(
            _EVAL_V5 / "renal-rerank-train-v5-extended.json",
            _EVAL_V5 / "renal-rerank-train-v5-extended.json.sha256"
        )


class TestRenalV5DevBPerformanceUnexecuted:
    """Verify that DEV-B was never executed for retrieval or reranking performance."""

    def test_no_dev_b_performance_report_exists(self):
        # DEV-B must have zero performance evaluation reports in reports/
        reports = list(_ROOT.glob("reports/**/renal*dev_b*.json"))
        reports += list(_ROOT.glob("reports/**/renal*dev-b*.json"))
        for r in reports:
            content = json.loads(r.read_text(encoding="utf-8"))
            assert "performance" not in str(content).lower() or "unexecuted" in str(content).lower(), (
                f"Unexpected performance execution found in DEV-B report: {r}"
            )

    def test_dev_b_sha_unchanged_from_baseline(self):
        _verify_sha256_sidecar(
            _EVAL_V5 / "renal-rerank-dev-b-v5.json",
            _EVAL_V5 / "renal-rerank-dev-b-v5.json.sha256"
        )


class TestRenalV5ClosureDocumentationAndStatus:
    """Verify that P3 status, SELECT_VAL metrics, and non-promoted workstreams are recorded."""

    def test_closure_report_records_required_states(self):
        closure_file = _REPORTS_V5 / "renal_v5_closure_report.json"
        assert closure_file.exists(), "renal_v5_closure_report.json must exist"
        data = json.loads(closure_file.read_text(encoding="utf-8"))

        assert data["p3_status"] == "RESEARCH_VALIDATED_NOT_PRODUCTION_PROMOTED"
        assert data["v5_status"] == "NOT_PRODUCTION_PROMOTED"
        assert data["production_default_runtime"] == "v3"
        assert data["workstream_statuses"]["lora_reranker_training"] == "NOT_RUN"
        assert data["workstream_statuses"]["dev_b_performance_execution"] == "PERFORMANCE_NOT_RUN"
        assert data["workstream_statuses"]["final_v5_heldout_evaluation"] == "NOT_RUN"
        assert data["workstream_statuses"]["safety_workstream_promotion"] == "NOT_FULLY_PROMOTED"

        val = data["fresh_select_val_results"]
        assert val["output_coverage_at_20"] == "17/20 (85.0%)"
        assert val["base_reranker_passage_hit1"] == "15/20 (75.0%)"

    def test_v5_technical_results_document_has_closure_section(self):
        doc = _DOCS / "RENAL_TECHNICAL_RESULTS_V5.md"
        assert doc.exists(), "RENAL_TECHNICAL_RESULTS_V5.md must exist"
        text = doc.read_text(encoding="utf-8")

        assert "RESEARCH_VALIDATED_NOT_PRODUCTION_PROMOTED" in text
        assert "LoRA NOT RUN" in text
        assert "DEV-B PERFORMANCE NOT RUN" in text
        assert "FINAL_V5_HELDOUT NOT RUN" in text
        assert "safety workstream NOT fully promoted" in text
        assert "V5 is therefore NOT production promoted" in text
        assert "OutputCoverage@20 = 17/20 = 85%" in text or "17/20 (85.0%)" in text
        assert "15/20" in text and "75" in text
