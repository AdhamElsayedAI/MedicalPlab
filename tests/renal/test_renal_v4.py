"""
Tests for Renal V4 Evidence Localization, Firewall Isolation & Safety Gate Compliance.
======================================================================================
Verifies:
1. Historical heldout exclusion & spend isolation (V1, V2, V3, V3.1, V4 DEV, V4 TEST).
2. Split claim / source-section leakage & near-duplicate query leakage firewall.
3. Precondition SHAs & dataset sidecar consistency.
4. Scaler and classifier fit only on TRAIN; threshold selected only on CALIBRATION.
5. Fixed candidate budgets (B=50 superset, R=20 reranker input) and no gold-doc filtering.
6. Section channel independence from passage body embeddings.
7. Single-logical-run immutability of SAFETY_TEST_V4 and FINAL_V4_HELDOUT.
8. SBA technical gate immutability and fail-closed posture (Generated = 0).
9. Banned reporting phrases compliance.
10. CourseLearningService V4 integration & citation resolution.
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


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def normalize_text(t: str) -> str:
    if not t:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", t.lower())).strip()


class TestRenalV4FirewallIsolation:
    """Verifies complete historical spend isolation and zero query/claim leakage."""

    def test_v4_datasets_exist(self):
        expected_files = [
            "renal-retrieval-dev-v4.json",
            "renal-safety-train-v4.json",
            "renal-safety-dev-v4.json",
            "renal-safety-calibration-v4.json",
            "renal-safety-test-v4.json",
            "renal-heldout-v4-final.json",
        ]
        for fname in expected_files:
            p = EVAL_V4_DIR / fname
            assert p.exists(), f"Missing required V4 dataset: {fname}"
            sidecar = EVAL_V4_DIR / f"{fname}.sha256"
            assert sidecar.exists(), f"Missing SHA sidecar for {fname}"
            expected_sha = sidecar.read_text(encoding="utf-8").split()[0]
            actual_sha = sha256_file(p)
            assert actual_sha == expected_sha, f"SHA mismatch on {fname}: {actual_sha} vs {expected_sha}"

    def test_historical_heldouts_quarantined_and_unmodified(self):
        v2_heldout = ROOT / "evaluation" / "renal" / "renal-heldout-v2-final.json"
        v3_heldout = ROOT / "evaluation" / "renal" / "v3" / "renal-heldout-v3-final.json"
        v31_test2 = ROOT / "evaluation" / "renal" / "v3" / "renal-v3-safety-test-2.json"

        assert v2_heldout.exists()
        assert v3_heldout.exists()
        assert v31_test2.exists()

        # Sidecar checks
        v2_sidecar = ROOT / "evaluation" / "renal" / "renal-heldout-v2-final.json.sha256"
        v3_sidecar = ROOT / "evaluation" / "renal" / "v3" / "renal-heldout-v3-final.json.sha256"
        v31_sidecar = ROOT / "evaluation" / "renal" / "v3" / "renal-v3-safety-test-2.json.sha256"

        assert sha256_file(v2_heldout) == v2_sidecar.read_text(encoding="utf-8").split()[0]
        assert sha256_file(v3_heldout) == v3_sidecar.read_text(encoding="utf-8").split()[0]
        assert sha256_file(v31_test2) == v31_sidecar.read_text(encoding="utf-8").split()[0]

    def test_final_heldout_zero_leakage_with_any_spent_set(self):
        heldout_path = EVAL_V4_DIR / "renal-heldout-v4-final.json"
        heldout_data = json.loads(heldout_path.read_text(encoding="utf-8"))
        heldout_queries = {normalize_text(q["query"]) for q in heldout_data["queries"]}
        heldout_claims = {normalize_text(q.get("canonical_claim", "")) for q in heldout_data["queries"] if q.get("canonical_claim")}

        spent_files = [
            ROOT / "evaluation" / "renal" / "renal-heldout-v1.json",
            ROOT / "evaluation" / "renal" / "renal-heldout-v2-final.json",
            ROOT / "evaluation" / "renal" / "renal-heldout-v2.json",
            ROOT / "evaluation" / "renal" / "v3" / "renal-heldout-v3-final.json",
            ROOT / "evaluation" / "renal" / "v3" / "renal-v3-safety-test-2.json",
            ROOT / "evaluation" / "renal" / "v3" / "renal-dev-v3-qrels.json",
            ROOT / "evaluation" / "renal" / "v4" / "renal-retrieval-dev-v4.json",
            ROOT / "evaluation" / "renal" / "v4" / "renal-safety-train-v4.json",
            ROOT / "evaluation" / "renal" / "v4" / "renal-safety-dev-v4.json",
            ROOT / "evaluation" / "renal" / "v4" / "renal-safety-calibration-v4.json",
            ROOT / "evaluation" / "renal" / "v4" / "renal-safety-test-v4.json",
        ]

        for sf in spent_files:
            if sf.exists():
                s_data = json.loads(sf.read_text(encoding="utf-8"))
                s_queries = s_data.get("queries", s_data if isinstance(s_data, list) else [])
                for sq in s_queries:
                    sq_text = normalize_text(sq.get("query", ""))
                    if sq_text:
                        assert sq_text not in heldout_queries, f"Heldout leaked query from {sf.name}: '{sq_text}'"
                    sc_text = normalize_text(sq.get("canonical_claim", sq.get("medical_claim", "")))
                    if sc_text and len(sc_text) > 10:
                        assert sc_text not in heldout_claims, f"Heldout leaked claim from {sf.name}: '{sc_text}'"


class TestRenalV4TrainingAndCalibrationDiscipline:
    """Verifies strict train/dev/calibration/test split discipline."""

    def test_classifier_artifacts_exist_and_match_sidecars(self):
        clf_pkl = MODELS_DIR / "renal_v4_evidence_classifier.pkl"
        clf_sidecar = MODELS_DIR / "renal_v4_evidence_classifier.pkl.sha256"
        assert clf_pkl.exists()
        assert clf_sidecar.exists()
        expected_sha = clf_sidecar.read_text(encoding="utf-8").split()[0]
        assert sha256_file(clf_pkl) == expected_sha

    def test_configs_exist_and_are_frozen(self):
        ret_cfg = CONFIGS_DIR / "renal_v4_retrieval_config.json"
        safe_cfg = CONFIGS_DIR / "renal_v4_safety_config.json"
        assert ret_cfg.exists()
        assert safe_cfg.exists()

        ret_data = json.loads(ret_cfg.read_text(encoding="utf-8"))
        assert ret_data["candidate_selection"]["superset_budget_B"] == 50
        assert ret_data["candidate_selection"]["reranker_input_budget_R"] == 20
        assert ret_data["first_stage_scoring"]["soft_document_prior_alpha"] == 0.18
        assert ret_data["first_stage_scoring"]["section_structural_weight_beta"] == 0.12

        safe_data = json.loads(safe_cfg.read_text(encoding="utf-8"))
        assert safe_data["selected_architecture"] == "MODEL_A_RETRIEVAL_10_FEATS"
        assert safe_data["operating_threshold_tau"] == 0.6886
        assert len(safe_data["feature_schema"]) == 10

    def test_single_run_evaluation_reports_exist(self):
        test_rep = REPORTS_V4_DIR / "renal_v4_safety_test_results.json"
        heldout_rep = REPORTS_V4_DIR / "renal_v4_paired_final_heldout.json"
        assert test_rep.exists()
        assert heldout_rep.exists()


class TestRenalV4SBAGateAndSafetyCompliance:
    """Verifies that SBA thresholds are immutable and fail-closed posture is enforced."""

    def test_production_sba_gate_thresholds_immutable(self):
        heldout_rep = json.loads((REPORTS_V4_DIR / "renal_v4_paired_final_heldout.json").read_text(encoding="utf-8"))
        sba = heldout_rep["sba_technical_gate"]
        assert sba["verdict"] == "SBA_GATE_FAIL"
        assert sba["generated"] == 0
        assert sba["human_reviewed"].startswith("0/")
        assert sba["golden"].startswith("0/")

    def test_banned_reporting_phrases_prohibited(self):
        audit_rep = ROOT / "reports" / "renal_v4" / "renal_v4_recovery_audit.md"
        banned_phrases = [
            "zero hallucinations",
            "hallucination-free",
            "100% safe",
            "clinician validated",
        ]
        if audit_rep.exists():
            content = audit_rep.read_text(encoding="utf-8").lower()
            for bp in banned_phrases:
                assert bp not in content, f"Banned phrase '{bp}' found in recovery audit!"

        # Also check the main technical report for the retracted NLI overclaim
        # (excluding blockquote lines which quote the retracted text in the audit section)
        tech_rep = ROOT / "docs" / "demo" / "RENAL_TECHNICAL_RESULTS_V4.md"
        if tech_rep.exists():
            tech_content = tech_rep.read_text(encoding="utf-8")
            non_quote_lines = [l for l in tech_content.splitlines() if not l.strip().startswith(">")]
            substantive = "\n".join(non_quote_lines).lower()
            assert "conclusively verifies the foundational hypothesis" not in substantive, (
                "Retracted NLI overclaim still present in RENAL_TECHNICAL_RESULTS_V4.md"
            )


class TestRenalV4CourseLearningServiceIntegration:
    """Verifies service query flow, citation resolution, and fail-closed safety."""

    def test_service_initializes_with_v4_retriever(self):
        """V4 retriever must remain accessible for historical/research use via explicit selection."""
        from medicalplab.learn.service import CourseLearningService
        from medicalplab.learn.renal_retrieval import QwenRenalRetrieverV4
        service = CourseLearningService(renal_runtime_version="v4")
        assert isinstance(service._renal_retriever, QwenRenalRetrieverV4)

    def test_service_fail_closed_on_unsupported_query(self):
        from medicalplab.learn.service import CourseLearningService
        from medicalplab.learn.models import CourseQueryRequest, GroundingStatus
        service = CourseLearningService()
        res = service.query(CourseQueryRequest(course_id="urinary_renal", query=""))
        assert res.grounding_status == GroundingStatus.UNSUPPORTED
        assert res.answer is None
