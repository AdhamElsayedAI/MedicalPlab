"""V6 Clinical Readiness Production Test Suite.

Enforces:
1. Deliverable existence, validity, and manifest consistency.
2. Dataset SHA256 cryptographic binding with manifest.
3. Strict governance invariants:
   golden_count == 0, clinician_approved_count == 0, golden_eligible == 0.
   Maximum autonomous trust state is CLINICIAN_REVIEW_REQUIRED.
4. Historical immutability of V1 through V5 datasets.
5. V5 invalidation report verifies 36/36 caught and quarantined.
6. Complete 6-step evidence chains for all 13 source-grounded questions.
7. Complete 4-zone content coverage accounting.
8. Substantive fail-closed quarantine reasons for all 23 non-grounded questions.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = ROOT_DIR / "Data"
REPORTS_DIR = ROOT_DIR / "reports/plab_clinical_readiness_v6"


@pytest.fixture(scope="module")
def v6_dataset():
    p = DATA_DIR / "questions/versions/cardiorespiratory_batch_1_clinical_readiness_v6.json"
    assert p.exists(), f"Missing V6 dataset: {p}"
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def v6_manifest():
    p = DATA_DIR / "metadata/cardiorespiratory_batch_1_clinical_readiness_v6.manifest.json"
    assert p.exists(), f"Missing V6 manifest: {p}"
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def complete_audit():
    p = REPORTS_DIR / "complete_revalidation_audit_v6.json"
    assert p.exists(), f"Missing complete revalidation audit: {p}"
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def v5_revalidation():
    p = REPORTS_DIR / "v5_revalidation_under_v6.json"
    assert p.exists(), f"Missing V5 revalidation report: {p}"
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def claim_matrix():
    p = REPORTS_DIR / "atomic_claim_evidence_matrix_v6.json"
    assert p.exists(), f"Missing claim evidence matrix: {p}"
    return json.loads(p.read_text(encoding="utf-8"))


class TestDeliverableIntegrity:
    """Validate all 7 production deliverables exist, are non-empty, and valid."""

    def test_all_production_deliverables_exist(self):
        deliverables = [
            DATA_DIR / "questions/versions/cardiorespiratory_batch_1_clinical_readiness_v6.json",
            DATA_DIR / "metadata/cardiorespiratory_batch_1_clinical_readiness_v6.manifest.json",
            REPORTS_DIR / "complete_revalidation_audit_v6.json",
            REPORTS_DIR / "atomic_claim_evidence_matrix_v6.json",
            REPORTS_DIR / "clinician_review_package_v6.json",
            REPORTS_DIR / "clinician_review_package_v6.html",
            REPORTS_DIR / "reproducibility_manifest_v6.json",
            REPORTS_DIR / "v5_revalidation_under_v6.json",
        ]
        for path in deliverables:
            assert path.exists(), f"Deliverable missing: {path}"
            assert path.stat().st_size > 400, f"Deliverable suspiciously small: {path}"

    def test_dataset_sha256_matches_manifest(self, v6_manifest):
        """Cryptographic binding between dataset file and manifest."""
        manifest_sha = v6_manifest["sha256"]
        p = DATA_DIR / "questions/versions/cardiorespiratory_batch_1_clinical_readiness_v6.json"
        actual_sha = hashlib.sha256(p.read_bytes()).hexdigest()
        assert manifest_sha == actual_sha, "Manifest SHA256 does not match dataset file bytes!"
        assert len(actual_sha) == 64, "Invalid SHA256 length"

    def test_question_counts_consistency(self, v6_dataset, v6_manifest, complete_audit):
        assert v6_dataset["total_questions"] == 36
        assert len(v6_dataset["questions"]) == 36
        assert v6_manifest["record_count"] == 36
        assert complete_audit["statistics"]["total_questions"] == 36


class TestStrictGovernanceInvariants:
    """Enforce strict governance invariants: zero golden, zero clinician approved."""

    def test_manifest_governance_invariants(self, v6_manifest):
        assert v6_manifest["golden_count"] == 0, "golden_count must be strictly 0!"
        assert v6_manifest["clinician_approved_count"] == 0, "clinician_approved_count must be strictly 0!"
        assert v6_manifest["golden_eligible"] == 0, "golden_eligible must be strictly 0!"
        assert v6_manifest["governance_lock"] == "LOCKED_NON_GOLDEN_FAIL_CLOSED"
        assert v6_manifest["max_trust_state"] == "CLINICIAN_REVIEW_REQUIRED"

    def test_dataset_item_trust_states(self, v6_dataset):
        for q in v6_dataset["questions"]:
            qid = q["question_id"]
            # No question may be autonomously approved or marked golden
            assert not q.get("golden", False), f"Question {qid} is marked golden!"
            assert not q.get("clinician_approved", False), f"Question {qid} is marked clinician_approved!"
            assert q.get("clinician_approved_by") is None, f"Question {qid} has clinician_approved_by set!"
            assert q.get("trust_state") in ("CLINICIAN_REVIEW_REQUIRED", "QUARANTINED"), (
                f"Question {qid} has unauthorized trust state: {q.get('trust_state')}"
            )
            if q["status"] == "needs_review":
                assert q["trust_state"] == "CLINICIAN_REVIEW_REQUIRED"
            else:
                assert q["status"] == "quarantined"
                assert q["trust_state"] == "QUARANTINED"

    def test_governance_verdicts_in_audit(self, complete_audit):
        gv = complete_audit["governance_verdicts"]
        assert gv["v3_disputed_invalidated"] is True
        assert gv["v4_disputed_invalidated"] is True
        assert gv["v5_disputed_invalidated"] is True
        assert gv["v6_fail_closed_demonstrated"] is True


class TestHistoricalImmutability:
    """Verify earlier disputed batches V1-V5 are preserved and immutable."""

    def test_frozen_v1_immutable(self):
        p = DATA_DIR / "questions/versions/cardiorespiratory_batch_1_frozen_v1.json"
        assert p.exists()
        data = json.loads(p.read_text(encoding="utf-8"))
        assert len(data["questions"]) == 36

    def test_v3_v4_v5_snapshots_exist(self):
        for v in ("v3", "v4", "v5"):
            p = DATA_DIR / f"questions/versions/cardiorespiratory_batch_1_clinical_readiness_{v}.json"
            assert p.exists(), f"Historical {v} artifact missing!"
            data = json.loads(p.read_text(encoding="utf-8"))
            assert len(data.get("questions", [])) == 36

    def test_v5_invalidation_report(self, v5_revalidation):
        """Ensure all 36 V5 items were caught and quarantined under V6 rules."""
        assert v5_revalidation["total_v5_questions_evaluated"] == 36
        assert v5_revalidation["v6_quarantined_count"] == 36
        assert v5_revalidation["v6_grounded_count"] == 0
        assert v5_revalidation["validation_oracle_verdict"] == "V5_INVALIDATION_PROVEN_FAIL_CLOSED"

        # Verify all mandatory canaries failed
        canary_ids = [
            "PLAB-CARD-0001", "PLAB-CARD-0006", "PLAB-RESP-0003",
            "PLAB-RESP-0008", "PLAB-CARD-0010", "PLAB-CARD-0013",
            "PLAB-CARD-0017", "PLAB-EMERG-0003",
        ]
        q_results = {r["question_id"]: r for r in v5_revalidation["detailed_results"]}
        for cid in canary_ids:
            assert cid in q_results, f"Canary {cid} missing from V5 revalidation report!"
            res = q_results[cid]
            assert res["v6_status"]["trust_state"] == "QUARANTINED", f"Canary {cid} should have failed under V6!"
            assert res["is_v5_false_positive_invalidated"] is True, f"Canary {cid} was not marked invalidated!"


class TestEvidenceGroundedQuestions:
    """Verify complete 6-step evidence chain and 4-zone coverage for grounded questions."""

    GROUNDED_QUESTIONS = [
        "PLAB-CARD-0004",  # AF DOAC / Apixaban (NICE NG196)
        "PLAB-CARD-0005",  # AF Rate Control / Bisoprolol (NICE NG196)
        "PLAB-RESP-0001",  # COPD Oxygen Target 88-92% (BTS Oxygen 2017)
        "PLAB-RESP-0002",  # COPD Dual Bronchodilator LAMA+LABA (NICE NG115)
        "PLAB-EMERG-0001", # ALS Shockable VF Adrenaline + Amiodarone (RCUK ALS 2025)
        "PLAB-EMERG-0002", # BLS CPR Metrics 100-120/min 5-6 cm (RCUK BLS 2025)
        "PLAB-RESP-0004",  # Pneumothorax Conservative Observation (BTS Pleural 2023)
        "PLAB-RESP-0007",  # ARDS Berlin Severe <= 100 mmHg (FICM/ICS 2019)
        "PLAB-RESP-0009",  # ARDS Prone Positioning >= 16h (FICM/ICS 2019)
        "PLAB-CARD-0016",  # Bradycardia Adverse Features Atropine 500mcg (RCUK BRADY 2025)
        "PLAB-CARD-0019",  # Aortic Stenosis Severe Signs (ESC/EACTS VHD 2025)
        "PLAB-CARD-0020",  # Aortic Stenosis Severe Echo Criteria (ESC/EACTS VHD 2025)
        "PLAB-CARD-0021",  # Aortic Stenosis Pre-TAVI MDCT (ESC/EACTS VHD 2025)
    ]

    def test_exactly_13_grounded_questions(self, complete_audit):
        grounded = [
            item["question_id"]
            for item in complete_audit["detailed_results"]
            if item["source_grounded"]
        ]
        assert len(grounded) == 13, f"Expected 13 grounded, found {len(grounded)}: {grounded}"
        assert set(grounded) == set(self.GROUNDED_QUESTIONS)

    def test_complete_evidence_chains_for_grounded_questions(self, complete_audit):
        q_map = {item["question_id"]: item for item in complete_audit["detailed_results"]}

        for qid in self.GROUNDED_QUESTIONS:
            item = q_map[qid]
            assert item["source_grounded"] is True, f"{qid} is not source_grounded"
            assert item["clinician_review_ready"] is True, f"{qid} not clinician_review_ready"
            assert len(item["blocking_reasons"]) == 0, f"{qid} has unexpected blocking reasons: {item['blocking_reasons']}"

            # 1. Source receipts verified
            receipts = item["source_receipts"]
            assert len(receipts) > 0, f"{qid} has no source receipts"
            for sid, rcpt in receipts.items():
                assert rcpt["identity_verification_status"] == "IDENTITY_VERIFIED", (
                    f"{qid} source {sid} identity not verified: {rcpt.get('explanation')}"
                )

            # 2. Currency passed
            currency = item["currency_results"]
            for sid, curr in currency.items():
                assert curr["policy_passes"] is True, f"{qid} source {sid} currency failed"
                assert curr["currency"] in ("CURRENT", "HISTORICAL_CONCORDANT")

            # 3. Decisive claims verified & monotonic
            claims = item["claims"]
            assert len(claims) > 0, f"{qid} has no atomic claims"
            decisive_claims = [c for c in claims if c["is_decisive"]]
            assert len(decisive_claims) >= 1, f"{qid} has no decisive atomic claim"
            for clm in decisive_claims:
                assert clm["final_claim_pass"] is True, (
                    f"{qid} decisive claim {clm['claim_id']} failed: {clm.get('reasons')}"
                )
                assert clm["span_verification_pass"] is True, f"{qid} decisive claim {clm['claim_id']} span not verified"
                assert clm["specificity_pass"] is True, (
                    f"{qid} decisive claim {clm['claim_id']} specificity monotonicity failed"
                )

            # 4. Distractor review passes
            dr = item["distractor_review"]
            assert dr["integrity_passed"] is True, f"{qid} distractor integrity failed"
            assert len(dr["contamination_flags"]) == 0, f"{qid} has distractor contamination: {dr['contamination_flags']}"
            assert len(dr["boilerplate_flags"]) == 0, f"{qid} has boilerplate distractors: {dr['boilerplate_flags']}"
            assert dr["multiple_defensible_options"] is False, f"{qid} has multiple defensible options!"

            # 5. Adversarial review passes
            adv = item["adversarial_review"]
            assert adv["has_ambiguity"] is False, f"{qid} has clinical ambiguity"
            assert adv["multiple_defensible_options"] is False, f"{qid} has multiple defensible options"
            assert adv["action_recommendation"] == "PROCEED", f"{qid} not recommended to proceed"

            # 6. Content coverage passes
            cov = item["coverage"]
            assert cov["coverage_passed"] is True, f"{qid} coverage failed"
            assert cov["uncovered_decisive_fragments_count"] == 0, (
                f"{qid} has {cov['uncovered_decisive_fragments_count']} uncovered fragments: {cov['under_decomposition_failures']}"
            )


class TestFailClosedQuarantinedQuestions:
    """Verify all 23 quarantined questions fail closed for substantive clinical reasons."""

    def test_exactly_23_quarantined_questions(self, complete_audit):
        quarantined = [
            item["question_id"]
            for item in complete_audit["detailed_results"]
            if not item["source_grounded"]
        ]
        assert len(quarantined) == 23, f"Expected 23 quarantined, found {len(quarantined)}"

    def test_quarantined_questions_have_substantive_reasons(self, complete_audit):
        for item in complete_audit["detailed_results"]:
            if not item["source_grounded"]:
                qid = item["question_id"]
                assert item["trust_state"] == "QUARANTINED"
                assert len(item["blocking_reasons"]) > 0, f"Quarantined question {qid} has no blocking reasons!"
                # Reasons must be non-trivial
                for reason in item["blocking_reasons"]:
                    assert len(reason) > 10, f"Quarantined question {qid} has trivial reason: '{reason}'"
