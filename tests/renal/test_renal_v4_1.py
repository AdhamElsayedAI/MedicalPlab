"""
Tests for Renal V4.1 Post-Hoc Production & Methodology Audit Corrections.
==========================================================================
Verifies all six corrective findings from the V4.1 audit:

1.  Explicit Renal runtime version selection (V3 default, V4 available for research).
2.  V4 is NOT silently promoted as production winner despite V3 empirical superiority.
3.  V4 remains selectable for research/historical reproducibility.
4.  Fail-closed safety behavior maintained.
5.  PARTIALLY_SUPPORTED operational mapping (treated as negative/fail-closed).
6.  Safety denominator metadata corrected in config (n_negative_operational=70).
7.  Runtime availability detection uses V2 assets (B_400_overlap) as primary.
8.  API/mobile contract compatibility (renal_runtime_version parameter accepted).
9.  SBA gate remains BLOCKED.
10. Technical report does NOT contain the banned overclaim phrase.
"""

import hashlib
import json
import re
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
EVAL_V4_DIR = ROOT / "evaluation" / "renal" / "v4"
CONFIGS_DIR = ROOT / "configs"
REPORTS_V4_DIR = ROOT / "reports" / "renal_v4"
MODELS_DIR = ROOT / "models"
DOCS_DIR = ROOT / "docs" / "demo"

REPORT_PATH = DOCS_DIR / "RENAL_TECHNICAL_RESULTS_V4.md"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Finding 1: Banned overclaim phrase removed from report
# ---------------------------------------------------------------------------

class TestV41ReportCorrectionFinding1:
    """Verifies that the banned overclaim statement is no longer present."""

    def test_banned_nli_conclusive_phrase_absent(self):
        """The phrase 'conclusively verifies' + NLI-required wording must not appear
        in substantive report claims (ignores quoted/retracted text in the audit section).
        """
        assert REPORT_PATH.exists(), "Technical report must exist"
        content = REPORT_PATH.read_text(encoding="utf-8")
        # Filter out blockquote lines (lines starting with '>') which contain
        # quoted/retracted text in the audit section
        non_quote_lines = [
            line for line in content.splitlines()
            if not line.strip().startswith(">")
        ]
        substantive = "\n".join(non_quote_lines).lower()
        assert "conclusively verifies the foundational hypothesis" not in substantive, (
            "Banned overclaim 'conclusively verifies the foundational hypothesis' "
            "still present in substantive (non-quoted) report text"
        )

    def test_defensible_replacement_claim_present(self):
        """The defensible replacement claim must be in the report."""
        assert REPORT_PATH.exists()
        content = REPORT_PATH.read_text(encoding="utf-8")
        assert "observed cross-dataset failure provides strong evidence" in content, (
            "Defensible replacement claim about cross-dataset failure must be present"
        )

    def test_posthoc_audit_section_exists(self):
        """Section '## 15. POST-HOC V4.1 PRODUCTION & METHODOLOGY AUDIT' must be present."""
        assert REPORT_PATH.exists()
        content = REPORT_PATH.read_text(encoding="utf-8")
        assert "POST-HOC V4.1 PRODUCTION" in content, (
            "POST-HOC V4.1 PRODUCTION & METHODOLOGY AUDIT section missing from report"
        )

    def test_five_findings_documented(self):
        """All 5 audit findings must be documented."""
        content = REPORT_PATH.read_text(encoding="utf-8")
        for i in range(1, 6):
            assert f"Finding {i}" in content, f"Audit Finding {i} missing from report"


# ---------------------------------------------------------------------------
# Finding 2 & 3: Explicit runtime version selection
# ---------------------------------------------------------------------------

class TestV41RuntimeVersionSelection:
    """Verifies explicit Renal retriever version selection in CourseLearningService."""

    def test_build_renal_retriever_factory_importable(self):
        """build_renal_retriever factory must be importable."""
        from medicalplab.learn.service import build_renal_retriever
        assert callable(build_renal_retriever)

    def test_renal_runtime_version_constant_is_v3(self):
        """Default runtime version must be 'v3' (conservative production choice)."""
        from medicalplab.learn.service import RENAL_RUNTIME_VERSION
        assert RENAL_RUNTIME_VERSION == "v3", (
            f"Production default must be 'v3', got '{RENAL_RUNTIME_VERSION}'. "
            "V4 was not statistically superior on FINAL_V4_HELDOUT (McNemar p=0.5000)."
        )

    def test_service_default_is_v3_retriever(self):
        """CourseLearningService must default to QwenRenalRetrieverV3."""
        from medicalplab.learn.service import CourseLearningService
        from medicalplab.learn.renal_retrieval import QwenRenalRetrieverV3
        service = CourseLearningService()
        assert isinstance(service._renal_retriever, QwenRenalRetrieverV3), (
            f"Default retriever must be QwenRenalRetrieverV3, got {type(service._renal_retriever).__name__}"
        )

    def test_service_default_is_not_v4(self):
        """CourseLearningService default must NOT be QwenRenalRetrieverV4."""
        from medicalplab.learn.service import CourseLearningService
        from medicalplab.learn.renal_retrieval import QwenRenalRetrieverV4
        service = CourseLearningService()
        assert not isinstance(service._renal_retriever, QwenRenalRetrieverV4), (
            "Default retriever must not be V4: V4 did not show statistically significant "
            "superiority over V3 (PassageHit@1 V3=62%, V4=58%, McNemar p=0.5000)"
        )

    def test_v4_selectable_for_research(self):
        """V4 retriever must remain selectable for research/historical use."""
        from medicalplab.learn.service import CourseLearningService, build_renal_retriever
        from medicalplab.learn.renal_retrieval import QwenRenalRetrieverV4
        retriever = build_renal_retriever(ROOT / "Data", version="v4")
        assert isinstance(retriever, QwenRenalRetrieverV4), (
            "build_renal_retriever('v4') must return QwenRenalRetrieverV4"
        )
        # Can inject directly
        service = CourseLearningService(renal_retriever=retriever)
        assert isinstance(service._renal_retriever, QwenRenalRetrieverV4)

    def test_explicit_v4_version_param(self):
        """CourseLearningService(renal_runtime_version='v4') must use V4."""
        from medicalplab.learn.service import CourseLearningService
        from medicalplab.learn.renal_retrieval import QwenRenalRetrieverV4
        service = CourseLearningService(renal_runtime_version="v4")
        assert isinstance(service._renal_retriever, QwenRenalRetrieverV4)

    def test_explicit_v3_version_param(self):
        """CourseLearningService(renal_runtime_version='v3') must use V3."""
        from medicalplab.learn.service import CourseLearningService
        from medicalplab.learn.renal_retrieval import QwenRenalRetrieverV3
        service = CourseLearningService(renal_runtime_version="v3")
        assert isinstance(service._renal_retriever, QwenRenalRetrieverV3)

    def test_runtime_version_attribute_stored(self):
        """Service must expose the selected runtime version."""
        from medicalplab.learn.service import CourseLearningService
        service = CourseLearningService(renal_runtime_version="v3")
        assert hasattr(service, "_renal_runtime_version")
        assert service._renal_runtime_version == "v3"


# ---------------------------------------------------------------------------
# Finding 4 (Safety): Fail-closed behavior
# ---------------------------------------------------------------------------

class TestV41FailClosedSafety:
    """Verifies fail-closed safety behavior is maintained."""

    def test_empty_query_returns_unsupported_fail_closed(self):
        """Empty renal query must return UNSUPPORTED (fail-closed), not grounded."""
        from medicalplab.learn.service import CourseLearningService
        from medicalplab.learn.models import CourseQueryRequest, GroundingStatus
        service = CourseLearningService()
        res = service.query(CourseQueryRequest(course_id="urinary_renal", query=""))
        assert res.grounding_status == GroundingStatus.UNSUPPORTED
        assert res.answer is None

    def test_safety_remains_experimental_not_production_gate(self):
        """Technical report must characterize safety classifier as EXPERIMENTAL."""
        content = REPORT_PATH.read_text(encoding="utf-8")
        assert "experimental" in content.lower(), (
            "Safety classifier must be described as experimental in the report"
        )

    def test_sba_gate_remains_blocked(self):
        """SBA technical gate verdict must remain SBA_GATE_FAIL with 0 generated."""
        heldout_rep = REPORTS_V4_DIR / "renal_v4_paired_final_heldout.json"
        assert heldout_rep.exists()
        report = json.loads(heldout_rep.read_text(encoding="utf-8"))
        sba = report["sba_technical_gate"]
        assert sba["verdict"] == "SBA_GATE_FAIL"
        assert sba["generated"] == 0


# ---------------------------------------------------------------------------
# Finding 3 (Safety config): PARTIALLY_SUPPORTED operational mapping & denominator
# ---------------------------------------------------------------------------

class TestV41SafetyDenominatorDocumentation:
    """Verifies safety denominator documentation corrected in config."""

    def test_safety_config_has_operational_negative_count(self):
        """Safety config must document n_negative_operational=70."""
        safe_cfg = CONFIGS_DIR / "renal_v4_safety_config.json"
        assert safe_cfg.exists()
        data = json.loads(safe_cfg.read_text(encoding="utf-8"))
        sizing = data["statistical_sizing"]
        assert "n_negative_operational" in sizing, (
            "Safety config must have n_negative_operational field"
        )
        assert sizing["n_negative_operational"] == 70, (
            f"Operational negative denominator must be 70 (50 SUPPORTED only as pos; "
            f"10 PARTIALLY_SUPPORTED + 60 others as neg), got {sizing['n_negative_operational']}"
        )

    def test_safety_config_has_operational_positive_count(self):
        """Safety config must document n_positive_operational=50 (SUPPORTED only)."""
        safe_cfg = CONFIGS_DIR / "renal_v4_safety_config.json"
        data = json.loads(safe_cfg.read_text(encoding="utf-8"))
        sizing = data["statistical_sizing"]
        assert "n_positive_operational" in sizing, (
            "Safety config must have n_positive_operational field (SUPPORTED only)"
        )
        assert sizing["n_positive_operational"] == 50

    def test_partially_supported_in_negative_breakdown(self):
        """PARTIALLY_SUPPORTED must appear in negative_breakdown (operational negatives)."""
        safe_cfg = CONFIGS_DIR / "renal_v4_safety_config.json"
        data = json.loads(safe_cfg.read_text(encoding="utf-8"))
        breakdown = data["statistical_sizing"]["negative_breakdown"]
        assert "partially_supported" in breakdown, (
            "PARTIALLY_SUPPORTED must be listed in negative_breakdown "
            "since it maps operationally to INSUFFICIENT_EVIDENCE (negative)"
        )
        assert breakdown["partially_supported"] == 10

    def test_partially_supported_policy_documented(self):
        """PARTIALLY_SUPPORTED operational policy must be documented in config."""
        safe_cfg = CONFIGS_DIR / "renal_v4_safety_config.json"
        data = json.loads(safe_cfg.read_text(encoding="utf-8"))
        sizing = data["statistical_sizing"]
        assert "partially_supported_operational_policy" in sizing, (
            "Config must document PARTIALLY_SUPPORTED operational policy"
        )
        policy = sizing["partially_supported_operational_policy"].lower()
        assert "fail-closed" in policy or "insufficient_evidence" in policy.upper() or "insufficient" in policy

    def test_label_action_mapping_includes_partially_supported(self):
        """label_action_mapping must show PARTIALLY_SUPPORTED → INSUFFICIENT_EVIDENCE."""
        safe_cfg = CONFIGS_DIR / "renal_v4_safety_config.json"
        data = json.loads(safe_cfg.read_text(encoding="utf-8"))
        mapping = data["label_action_mapping"]
        assert "PARTIALLY_SUPPORTED" in mapping, (
            "label_action_mapping must include PARTIALLY_SUPPORTED"
        )
        assert mapping["PARTIALLY_SUPPORTED"] == "INSUFFICIENT_EVIDENCE", (
            "PARTIALLY_SUPPORTED must map to INSUFFICIENT_EVIDENCE (fail-closed)"
        )

    def test_unsafe_accept_ci_denominator_correct_in_claim(self):
        """Config claim must reference the operational denominator n=70."""
        safe_cfg = CONFIGS_DIR / "renal_v4_safety_config.json"
        data = json.loads(safe_cfg.read_text(encoding="utf-8"))
        claim = data["statistical_sizing"]["claim"]
        assert "70" in claim, (
            "CI denominator claim must reference operational n=70, not n=60"
        )
        assert "4.19" in claim, (
            "CI UB must be 4.19% (k=0, n=70 Clopper-Pearson), not 4.88% (k=0, n=60)"
        )


# ---------------------------------------------------------------------------
# Finding 4 (Retrieval config): B=50 diagnostic-only description
# ---------------------------------------------------------------------------

class TestV41CandidateCoverageArchitectureDescription:
    """Verifies B=50 is labeled as diagnostic-only in config, not an active filter."""

    def test_retrieval_config_labels_b50_as_diagnostic(self):
        """superset_budget_B_note must exist and describe B=50 as diagnostic."""
        ret_cfg = CONFIGS_DIR / "renal_v4_retrieval_config.json"
        assert ret_cfg.exists()
        data = json.loads(ret_cfg.read_text(encoding="utf-8"))
        sel = data["candidate_selection"]
        assert "superset_budget_B_note" in sel, (
            "retrieval config must have superset_budget_B_note labeling it as diagnostic"
        )
        note = sel["superset_budget_B_note"].upper()
        assert "DIAGNOSTIC" in note, (
            "superset_budget_B_note must indicate this is diagnostic-only"
        )

    def test_retrieval_config_selection_policy_is_direct_top20(self):
        """selection_policy must not imply an active 50→20 filter."""
        ret_cfg = CONFIGS_DIR / "renal_v4_retrieval_config.json"
        data = json.loads(ret_cfg.read_text(encoding="utf-8"))
        sel = data["candidate_selection"]
        policy = sel["selection_policy"]
        assert "direct" in policy.lower() or "top20" in policy.lower().replace("_", ""), (
            f"selection_policy should reflect direct top-20 retrieval, got: '{policy}'"
        )

    def test_retrieval_config_r20_is_authoritative_metric(self):
        """RerankerInputHit@20 must be documented as authoritative metric."""
        ret_cfg = CONFIGS_DIR / "renal_v4_retrieval_config.json"
        data = json.loads(ret_cfg.read_text(encoding="utf-8"))
        note = data["candidate_selection"].get("reranker_input_budget_R_note", "").lower()
        assert "authoritative" in note, (
            "reranker_input_budget_R_note must indicate R=20 is the authoritative metric"
        )


# ---------------------------------------------------------------------------
# Finding 5: Urinary availability detection
# ---------------------------------------------------------------------------

class TestV41UrinaryAvailabilityDetection:
    """Verifies urinary_available is set based on V2 runtime assets as primary."""

    def test_urinary_available_from_v2_assets(self):
        """urinary_available should be True when V2 registry + B_400_overlap chunks exist."""
        from medicalplab.learn.service import CourseLearningService
        service = CourseLearningService()
        # The V2 assets exist in this repo (B_400_overlap chunks are present)
        v2_registry = service.data_root / "metadata" / "renal_source_registry_v2.json"
        v2_chunks = service.data_root / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
        if v2_registry.exists() and v2_chunks.exists() and any(v2_chunks.glob("*.chunks.json")):
            assert service.urinary_available is True, (
                "urinary_available must be True when V2 assets present "
                "(B_400_overlap chunks + renal_source_registry_v2.json)"
            )

    def test_v1_legacy_does_not_override_v2_availability(self):
        """If V2 assets are present, V1 legacy absence must not set urinary_available=False."""
        from medicalplab.learn.service import CourseLearningService
        service = CourseLearningService()
        v2_registry = service.data_root / "metadata" / "renal_source_registry_v2.json"
        v2_chunks = service.data_root / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
        if v2_registry.exists() and v2_chunks.exists() and any(v2_chunks.glob("*.chunks.json")):
            # V2 assets present → urinary_available must be True regardless of V1 state
            assert service.urinary_available is True


# ---------------------------------------------------------------------------
# API/Mobile contract compatibility
# ---------------------------------------------------------------------------

class TestV41APIContractCompatibility:
    """Verifies API contract compatibility is maintained after the corrective changes."""

    def test_course_learning_service_api_accepts_runtime_version_param(self):
        """CourseLearningService must accept renal_runtime_version kwarg without error."""
        from medicalplab.learn.service import CourseLearningService
        # Must not raise
        for version in ["v3", "v4", "v1"]:
            service = CourseLearningService(renal_runtime_version=version)
            assert service is not None

    def test_course_query_request_api_unchanged(self):
        """CourseQueryRequest API must be unchanged (backwards compatible)."""
        from medicalplab.learn.models import CourseQueryRequest
        req = CourseQueryRequest(course_id="urinary_renal", query="test query")
        assert req.course_id == "urinary_renal"
        assert req.query == "test query"

    def test_grounding_status_values_unchanged(self):
        """GroundingStatus enum values must be unchanged."""
        from medicalplab.learn.models import GroundingStatus
        assert hasattr(GroundingStatus, "GROUNDED")
        assert hasattr(GroundingStatus, "INSUFFICIENT_EVIDENCE")
        assert hasattr(GroundingStatus, "UNSUPPORTED")
        assert hasattr(GroundingStatus, "DATA_SOURCE_MISSING")

    def test_sba_gate_thresholds_immutable(self):
        """SBA gate verdict and generated counts must be immutable."""
        heldout_rep = REPORTS_V4_DIR / "renal_v4_paired_final_heldout.json"
        assert heldout_rep.exists()
        report = json.loads(heldout_rep.read_text(encoding="utf-8"))
        sba = report["sba_technical_gate"]
        assert sba["verdict"] == "SBA_GATE_FAIL"
        assert sba["generated"] == 0
        assert sba["human_reviewed"].startswith("0/")
        assert sba["golden"].startswith("0/")

    def test_no_sba_questions_generated(self):
        """Absolutely no SBA questions must have been generated."""
        heldout_rep = REPORTS_V4_DIR / "renal_v4_paired_final_heldout.json"
        report = json.loads(heldout_rep.read_text(encoding="utf-8"))
        sba = report["sba_technical_gate"]
        assert int(sba["generated"]) == 0, "SBA generation is BLOCKED; must remain 0"


# ---------------------------------------------------------------------------
# Historical heldout firewall (unchanged from original V4 tests)
# ---------------------------------------------------------------------------

class TestV41HistoricalFirewallIntact:
    """Verifies frozen heldout artifacts were NOT modified during the V4.1 audit."""

    FROZEN_ARTIFACTS = {
        "evaluation/renal/renal-heldout-v2-final.json":
            "8885b21bc1174ea6a05028c03813d4aa1e72cfb5ecbd254a7e08c56bf8c29b92",
        "evaluation/renal/v3/renal-heldout-v3-final.json":
            "40c96f46be1c6547f2ffbdc29f90fb3444d48e66dfcfaae769cd3b8413082d32",
        "evaluation/renal/v3/renal-v3-safety-test-2.json":
            "3fe59bb6011c5ab4c526cbcc092b8dc087709b67d3f2aaa7318acd6679dcf8eb",
        "evaluation/renal/v4/renal-heldout-v4-final.json":
            "0368761712c91b068f913fef3760a2a331dfe0de735eb2ac5a77bcdef920a8c6",
        "evaluation/renal/v4/renal-safety-test-v4.json":
            "7d2069b5a1216f096b246c0c95033ef74118bc7c00d244f4debbf3c36eb6d2ad",
        "reports/renal_v4/renal_v4_safety_test_results.json":
            "e1c58c5c1c759f0dd4052ea17f4589b256b438b6d80afc7c67a3bd27af238f39",
        "models/renal_v4_evidence_classifier.pkl":
            "54f42677b4776354740001bb35b69ecd9b7cc9851c17dacb540f046229e864de",
    }

    def test_all_frozen_artifacts_unmodified(self):
        """Every frozen artifact's SHA-256 must exactly match the V4 mission-end value."""
        for rel_path, expected_sha in self.FROZEN_ARTIFACTS.items():
            p = ROOT / rel_path
            assert p.exists(), f"Frozen artifact missing: {rel_path}"
            actual = sha256_file(p)
            assert actual == expected_sha, (
                f"IMMUTABLE FIREWALL VIOLATION: {rel_path} was modified!\n"
                f"  Expected SHA: {expected_sha}\n"
                f"  Actual  SHA: {actual}"
            )
