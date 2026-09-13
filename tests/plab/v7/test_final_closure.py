"""Final PLAB closure gates and negative regression coverage."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from medicalplab.plab.v7.closure_validator import (
    validate_checkpoint,
    validate_question_record,
    validate_source_packet,
)


ROOT = Path(__file__).resolve().parents[3]
REPORTS = ROOT / "reports/plab_final_closure"
CHECKPOINT_PATH = ROOT / "Data/questions/versions/cardiorespiratory_batch_1_clinical_readiness_v7.json"
MANIFEST_PATH = ROOT / "Data/metadata/cardiorespiratory_batch_1_clinical_readiness_v7.manifest.json"


def load(name: str):
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def checkpoint():
    return json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def source_report():
    return load("final_source_identity_currentness_report.json")


@pytest.fixture
def grounded(checkpoint):
    return deepcopy(next(question for question in checkpoint["questions"] if question["source_grounded"]))


@pytest.fixture
def packets(source_report):
    return {packet["source_id"]: deepcopy(packet) for packet in source_report["sources"]}


def test_final_deliverables_exist_and_are_nonempty():
    names = [
        "final_plab_closure_audit.json",
        "quarantined_item_resolution_matrix.json",
        "final_atomic_claim_evidence_matrix.json",
        "final_question_content_coverage_report.json",
        "final_source_identity_currentness_report.json",
        "final_distractor_ambiguity_report.json",
        "final_clinician_review_package.html",
        "final_clinician_review_package.json",
        "final_blocked_items_appendix.json",
        "final_clinical_readiness_checkpoint.json",
        "final_reproducibility_manifest.json",
        "final_test_report.json",
    ]
    for name in names:
        path = REPORTS / name
        assert path.exists(), name
        assert path.stat().st_size > 100, name
    assert CHECKPOINT_PATH.exists()
    assert MANIFEST_PATH.exists()


def test_checkpoint_recomputes_cleanly(checkpoint, source_report):
    assert validate_checkpoint(checkpoint, source_report) == []
    assert checkpoint["summary"] == {
        "total_questions": 36,
        "source_grounded": 12,
        "clinician_review_required": 12,
        "quarantined": 24,
        "deferred": 0,
        "rejected": 0,
    }


def test_each_question_has_exactly_one_final_disposition(checkpoint):
    assert len({q["question_id"] for q in checkpoint["questions"]}) == 36
    assert all(q["disposition"] for q in checkpoint["questions"])
    assert sum(q["source_grounded"] for q in checkpoint["questions"]) == 12


def test_review_package_contains_only_and_all_eligible_items(checkpoint):
    package = load("final_clinician_review_package.json")
    expected = {q["question_id"] for q in checkpoint["questions"] if q["source_grounded"]}
    actual = {q["question_id"] for q in package["questions"]}
    assert actual == expected
    assert all(q["trust_state"] == "CLINICIAN_REVIEW_REQUIRED" for q in package["questions"])
    assert all(not q["clinician_approved"] and not q["golden"] for q in package["questions"])


def test_blocked_appendix_and_resolution_matrix_are_complete(checkpoint):
    appendix = load("final_blocked_items_appendix.json")
    matrix = load("quarantined_item_resolution_matrix.json")
    expected = {q["question_id"] for q in checkpoint["questions"] if not q["source_grounded"]}
    assert {q["question_id"] for q in appendix["questions"]} == expected
    assert {item["question_id"] for item in matrix["items"]} == expected
    assert len(matrix["items"]) == 24
    assert all(item["remaining_engineering_blocker"] is False for item in matrix["items"])


def test_cross_artifact_question_version_and_status_consistency(checkpoint):
    expected = {q["question_id"]: (q["question_version"], q["source_grounded"]) for q in checkpoint["questions"]}
    matrix = load("final_atomic_claim_evidence_matrix.json")["questions"]
    coverage = load("final_question_content_coverage_report.json")["questions"]
    distractors = load("final_distractor_ambiguity_report.json")["questions"]
    for collection in (matrix, coverage, distractors):
        observed = {item["question_id"]: (item["question_version"], item["source_grounded"]) for item in collection}
        assert observed == expected


def test_manifest_hashes_every_declared_output():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["checkpoint_sha256"] == hashlib.sha256(CHECKPOINT_PATH.read_bytes()).hexdigest()
    for relative, expected_hash in manifest["outputs"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected_hash


def test_reproducibility_manifest_hashes_inputs_and_outputs():
    repro = load("final_reproducibility_manifest.json")
    assert repro["deterministic"] is True
    for relative, expected_hash in repro["outputs"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected_hash


def test_historical_v1_through_v6_immutability_and_forensic_branches():
    audit = load("final_plab_closure_audit.json")
    history = audit["historical_integrity"]
    assert history["all_unchanged"] is True
    assert all(item["unchanged"] for item in history["artifacts"])
    assert history["forensic_branches"] == {
        "plab-v3-disputed": "ac6777abd8bb4b1f55fc32aa6a17a1bde5e23268",
        "plab-v4-disputed": "b2cd4537492a9169bce5502ecf7956a441e1b1c9",
        "plab-v5-disputed": "654fe652e8606114443ce1fc1ed3638e9f1c5bbf",
    }


def test_canary_confusion_matrix_has_zero_false_support():
    canary = load("final_plab_closure_audit.json")["canary"]
    assert canary["fp"] == 0
    assert canary["fn"] == 0
    assert canary["false_support_count"] == 0
    assert len(canary["fixtures"]) == 10
    assert all(item["actual_final_validator_result"] == "FAIL" for item in canary["fixtures"])


def test_v6_grounded_revalidation_and_v6_quarantine_resolution_counts():
    audit = load("final_plab_closure_audit.json")
    assert audit["original_v6_grounded"]["remained_grounded"] == 9
    assert audit["original_v6_grounded"]["downgraded"] == [
        "PLAB-CARD-0019",
        "PLAB-CARD-0020",
        "PLAB-CARD-0021",
        "PLAB-RESP-0007",
    ]
    assert audit["original_v6_quarantined"]["resolved_count"] == 3
    assert audit["original_v6_quarantined"]["resolved"] == [
        "PLAB-CARD-0008",
        "PLAB-CARD-0015",
        "PLAB-RESP-0008",
    ]


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("identity_status", "IDENTITY_MISMATCH", "identity is not verified"),
        ("edition_verification_status", "EDITION_MISMATCH", "wrong or unverified edition"),
        ("currentness_status", "STALE", "currentness is not verified"),
        ("http_status", 404, "HTTP 200"),
        ("representation_origin", "CALLER_SUPPLIED_TEXT", "synthetic representation"),
    ],
)
def test_source_identity_edition_currentness_and_origin_fail_closed(source_report, field, value, expected):
    packet = deepcopy(source_report["sources"][0])
    packet[field] = value
    assert expected in " ".join(validate_source_packet(packet))


def test_quote_not_present_fails_closed(source_report):
    packet = deepcopy(source_report["sources"][0])
    packet["evidence_spans"][0]["exact_text"] = "A quote not present in the verified representation."
    packet["evidence_spans"][0]["exact_text_sha256"] = hashlib.sha256(packet["evidence_spans"][0]["exact_text"].encode()).hexdigest()
    assert "quote not present" in " ".join(validate_source_packet(packet))


def test_wrong_source_binding_fails_closed(grounded, packets):
    claim = grounded["atomic_claims"][0]
    claim["source_id"] = next(source_id for source_id in packets if source_id != claim["source_id"])
    assert "wrong-source" in " ".join(validate_question_record(grounded, packets))


def test_topic_related_but_unsupported_claim_fails_closed(grounded, packets):
    grounded["atomic_claims"][0]["support_status"] = "TOPIC_RELATED_ONLY"
    assert "unsupported clinical claim" in " ".join(validate_question_record(grounded, packets))


def test_answer_more_specific_than_evidence_fails_closed(grounded, packets):
    grounded["answer_component_coverage"].append({"component": "unsupported extra dose", "claim_id": grounded["atomic_claims"][0]["claim_id"], "status": "UNCOVERED"})
    assert "uncovered keyed-answer component" in " ".join(validate_question_record(grounded, packets))


@pytest.mark.parametrize("dimension", ["dose", "unit", "operator", "timing", "population", "negation"])
def test_specificity_dimension_mismatches_fail_closed(grounded, packets, dimension):
    grounded["atomic_claims"][0]["specificity_dimensions"][dimension] = "MISMATCH"
    assert f"{dimension} mismatch" in " ".join(validate_question_record(grounded, packets))


def test_under_decomposition_and_uncovered_explanation_fail_closed(grounded, packets):
    grounded["content_coverage"]["uncovered_decisive_fragments"] = 1
    explanation = next(f for f in grounded["content_coverage"]["fragments"] if f["location"] == "EXPLANATION")
    explanation["mapped_claim_ids"] = []
    explanation["coverage_status"] = "UNCOVERED"
    errors = " ".join(validate_question_record(grounded, packets))
    assert "uncovered decisive fragment" in errors
    assert "decisive fragment lacks" in errors


def test_cross_question_distractor_contamination_fails_closed(grounded, packets):
    grounded["option_reviews"][0]["question_id"] = "PLAB-OTHER-9999"
    assert "cross-question rationale binding" in " ".join(validate_question_record(grounded, packets))


def test_boilerplate_distractor_rationale_fails_closed(grounded, packets):
    grounded["option_reviews"][0]["rationale"] = "Wrong choice."
    assert "boilerplate" in " ".join(validate_question_record(grounded, packets))


def test_two_defensible_options_fail_closed(grounded, packets):
    wrong = next(review for review in grounded["option_reviews"] if review["option_id"] != grounded["correct_answer"])
    wrong["is_defensible"] = True
    assert "one-best-answer adjudication failed" in " ".join(validate_question_record(grounded, packets))


@pytest.mark.parametrize("field", ["clinician_approved", "golden_eligible", "golden"])
def test_ai_clinician_approval_and_golden_promotion_fail_closed(grounded, packets, field):
    grounded[field] = True
    errors = " ".join(validate_question_record(grounded, packets))
    assert "fabricated clinician approval" in errors or "automatic Golden" in errors


def test_remaining_blockers_are_outside_autonomous_engineering(checkpoint, source_report):
    assert validate_checkpoint(checkpoint, source_report) == []
    blocked = [q for q in checkpoint["questions"] if not q["source_grounded"]]
    assert all(q["blocker_class"].startswith(("E_", "F_", "G_", "H_", "I_")) for q in blocked)
    assert all(q["remaining_engineering_blocker"] is False for q in blocked)


def test_scope_and_governance_freeze_are_explicit():
    audit = load("final_plab_closure_audit.json")
    assert audit["closure_status"] == "PASS_WITH_CLINICAL_BLOCKERS"
    assert audit["remaining_engineering_blockers"] == 0
    assert audit["scope_confirmation"] == {
        "plab_automation_closed": True,
        "new_scope_started": False,
        "rag_work": False,
        "model_training": False,
        "disputed_artifact_changed": False,
        "clinician_approval_fabricated": False,
        "golden_promotion": False,
        "push_performed": False,
    }


def test_final_test_report_is_complete_and_has_no_coverage_reduction():
    report = load("final_test_report.json")
    assert report["baseline"]["unexpected_reduction"] is False
    assert report["final"] == {
        "focused_closure": "36 passed",
        "plab": "129 passed",
        "full_repository": "646 passed, 1 skipped, 12 subtests passed",
        "deterministic_rebuild": "PASS_BYTE_IDENTICAL",
    }
    assert len(report["required_negative_classes"]) == 21
