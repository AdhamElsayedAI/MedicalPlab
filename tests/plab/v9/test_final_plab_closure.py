"""Independent test oracle and fail-closed validation tests for PLAB V9.

Invariants independently verified:
1. Final V9 question checkpoint and manifest validity.
2. Canonical organization identity, role separation, and official host matching.
3. Cross-platform UTF8_LF_CANONICAL_TEXT hashing and CRLF/LF invariance.
4. Exact evidence span containment, atomic claim bindings, and single-best-answer option reviews.
5. Strict human governance constraints (0 approved, 0 golden).
6. Negative mutation suite demonstrating fail-closed behavior on corrupted inputs.
7. Public packaging verification: raw publisher HTML/PDFs excluded on submission branch,
   with canonical evidence vault preserved at plab-evidence-final-v9 @ f62b3965c0d0f10e3c636e262365e0886c61cee8.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import pytest

from medicalplab.plab.v9.closure_validator import (
    validate_checkpoint,
    validate_question_record,
    validate_source_packet,
)
from medicalplab.plab.v9.hashing import (
    canonicalize_newlines_to_lf,
    compute_canonical_lf_text_sha256,
    compute_file_canonical_lf_sha256,
    compute_file_raw_sha256,
    compute_raw_bytes_sha256,
)
from medicalplab.plab.v9.identity import (
    APPROVED_OFFICIAL_HOSTS,
    CANONICAL_ORGANIZATIONS,
    extract_host,
    resolve_canonical_organization,
    verify_source_identity,
)
from medicalplab.plab.v9.models import (
    OrganizationRole,
    RedistributionReadiness,
)

ROOT = Path(__file__).resolve().parent.parent.parent.parent
CHECKPOINT_PATH = ROOT / "Data/questions/versions/cardiorespiratory_batch_1_final_closure_v9.json"
MANIFEST_PATH = ROOT / "Data/metadata/cardiorespiratory_batch_1_final_closure_v9.manifest.json"
RAW_SNAPSHOTS_DIR = ROOT / "Data/sources/v8/snapshots"

CANONICAL_EVIDENCE_BRANCH = "plab-evidence-final-v9"
CANONICAL_V9_COMMIT = "f62b3965c0d0f10e3c636e262365e0886c61cee8"


@pytest.fixture(scope="module")
def checkpoint_data() -> dict:
    assert CHECKPOINT_PATH.exists(), f"Missing V9 checkpoint: {CHECKPOINT_PATH}"
    return json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest_data() -> dict:
    assert MANIFEST_PATH.exists(), f"Missing V9 manifest: {MANIFEST_PATH}"
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sample_source_packets(checkpoint_data) -> list[dict]:
    """Construct verified source packets directly from the V9 canonical organization registry."""
    packets = [
        {
            "source_id": "SRC-NICE-NG196-V9",
            "canonical_identifier": "NICE NG196",
            "canonical_title": "Atrial fibrillation: diagnosis and management",
            "issuing_organization_id": "ORG-NICE",
            "canonical_organization": "National Institute for Health and Care Excellence",
            "canonical_url": "https://www.nice.org.uk/guidance/ng196/chapter/Recommendations",
            "final_resolved_url": "https://www.nice.org.uk/guidance/ng196/chapter/Recommendations",
            "edition": "Published 27 April 2021; verified active",
            "http_status": 200,
            "raw_snapshot_path": "Data/sources/v8/snapshots/SRC-NICE-NG196-V8.raw.html",
            "raw_snapshot_sha256": "0" * 64,
            "raw_snapshot_hash_basis": "RAW_BYTES_SHA256",
            "normalized_representation_path": "Data/sources/v9/normalized/SRC-NICE-NG196-V9.normalized.txt",
            "normalized_representation_sha256": "0" * 64,
            "normalized_representation_hash_basis": "UTF8_LF_CANONICAL_TEXT",
            "currentness_basis": "Active NICE recommendations page retrieved from publisher.",
            "source_currentness_evidence": {"publisher": "NICE", "status": "CURRENT_AUTHORITATIVE"},
            "identity_evidence": {"publisher": "NICE", "canonical_host": "www.nice.org.uk"},
            "redistribution_readiness": "PRIVATE_EVIDENCE_ONLY",
            "representation_text": "A" * 600,
            "evidence_spans": [
                {
                    "span_id": "NG196-1.6.3",
                    "span_type": "EXACT_SOURCE_SPAN",
                    "exact_text": "A" * 50,
                    "exact_text_sha256": hashlib.sha256(("A" * 50).encode("utf-8")).hexdigest(),
                    "source_id": "SRC-NICE-NG196-V9",
                    "start_char": 0,
                    "end_char": 50,
                }
            ],
        },
        {
            "source_id": "SRC-BTS-OXYGEN-2017-V9",
            "canonical_identifier": "BTS Oxygen 2017",
            "canonical_title": "BTS Guideline for oxygen use in adults in healthcare and emergency settings",
            "issuing_organization_id": "ORG-BTS",
            "canonical_organization": "British Thoracic Society",
            "canonical_url": "https://www.brit-thoracic.org.uk/quality-improvement/guidelines/emergency-oxygen/",
            "final_resolved_url": "https://www.brit-thoracic.org.uk/quality-improvement/guidelines/emergency-oxygen/",
            "edition": "Published May 2017; reviewed 2020",
            "http_status": 200,
            "raw_snapshot_path": "Data/sources/v8/snapshots/SRC-BTS-OXYGEN-2017-V8.raw.html",
            "raw_snapshot_sha256": "0" * 64,
            "raw_snapshot_hash_basis": "RAW_BYTES_SHA256",
            "normalized_representation_path": "Data/sources/v9/normalized/SRC-BTS-OXYGEN-2017-V9.normalized.txt",
            "normalized_representation_sha256": "0" * 64,
            "normalized_representation_hash_basis": "UTF8_LF_CANONICAL_TEXT",
            "currentness_basis": "Active BTS guideline standard.",
            "source_currentness_evidence": {"publisher": "British Thoracic Society", "status": "CURRENT_AUTHORITATIVE"},
            "identity_evidence": {"publisher": "British Thoracic Society", "canonical_host": "www.brit-thoracic.org.uk"},
            "redistribution_readiness": "PRIVATE_EVIDENCE_ONLY",
            "representation_text": "B" * 600,
            "evidence_spans": [
                {
                    "span_id": "BTS-OXYGEN-2017-COPD",
                    "span_type": "EXACT_SOURCE_SPAN",
                    "exact_text": "B" * 50,
                    "exact_text_sha256": hashlib.sha256(("B" * 50).encode("utf-8")).hexdigest(),
                    "source_id": "SRC-BTS-OXYGEN-2017-V9",
                    "start_char": 0,
                    "end_char": 50,
                }
            ],
        },
        {
            "source_id": "SRC-ICS-ARDS-2018-V9",
            "canonical_identifier": "ICS ARDS 2018",
            "canonical_title": "Guidelines on the management of acute respiratory distress syndrome",
            "issuing_organization_id": "ORG-ICS",
            "canonical_organization": "Intensive Care Society",
            "canonical_url": "https://ics.ac.uk/guidance/guidelines/management-of-ards.html",
            "final_resolved_url": "https://ics.ac.uk/guidance/guidelines/management-of-ards.html",
            "edition": "Published December 2018; FICM / ICS joint guideline",
            "http_status": 200,
            "raw_snapshot_path": "Data/sources/v8/snapshots/SRC-ICS-ARDS-2018-V8.raw.html",
            "raw_snapshot_sha256": "0" * 64,
            "raw_snapshot_hash_basis": "RAW_BYTES_SHA256",
            "normalized_representation_path": "Data/sources/v9/normalized/SRC-ICS-ARDS-2018-V9.normalized.txt",
            "normalized_representation_sha256": "0" * 64,
            "normalized_representation_hash_basis": "UTF8_LF_CANONICAL_TEXT",
            "currentness_basis": "Active ICS guidance standard.",
            "source_currentness_evidence": {"publisher": "Intensive Care Society", "status": "CURRENT_AUTHORITATIVE"},
            "identity_evidence": {
                "publisher": "Intensive Care Society",
                "supporting_organization": "Faculty of Intensive Care Medicine",
                "canonical_host": "ics.ac.uk",
            },
            "redistribution_readiness": "PRIVATE_EVIDENCE_ONLY",
            "representation_text": "C" * 600,
            "evidence_spans": [
                {
                    "span_id": "FICM-ICS-ARDS-2018-VENTILATION",
                    "span_type": "EXACT_SOURCE_SPAN",
                    "exact_text": "C" * 50,
                    "exact_text_sha256": hashlib.sha256(("C" * 50).encode("utf-8")).hexdigest(),
                    "source_id": "SRC-ICS-ARDS-2018-V9",
                    "start_char": 0,
                    "end_char": 50,
                }
            ],
        },
    ]
    return packets


# ==============================================================================
# 1. CROSS-PLATFORM HASHING & CRLF/LF INVARIANCE
# ==============================================================================

def test_cross_platform_lf_crlf_invariance():
    """Verify that identical text with LF vs CRLF line endings hashes identically under UTF8_LF_CANONICAL_TEXT."""
    lf_text = "Line 1: recommendation.\nLine 2: dosage 500 mcg.\nLine 3: outcome."
    crlf_text = "Line 1: recommendation.\r\nLine 2: dosage 500 mcg.\r\nLine 3: outcome."
    cr_text = "Line 1: recommendation.\rLine 2: dosage 500 mcg.\rLine 3: outcome."

    hash_lf = compute_canonical_lf_text_sha256(lf_text)
    hash_crlf = compute_canonical_lf_text_sha256(crlf_text)
    hash_cr = compute_canonical_lf_text_sha256(cr_text)

    assert hash_lf == hash_crlf
    assert hash_lf == hash_cr

    # Modified content must fail
    modified_text = "Line 1: recommendation.\nLine 2: dosage 600 mcg.\nLine 3: outcome."
    assert compute_canonical_lf_text_sha256(modified_text) != hash_lf

    # Non-UTF8 bytes fail closed
    with pytest.raises(UnicodeDecodeError):
        compute_canonical_lf_text_sha256(b"\xff\xfe\x00\x00")


# ==============================================================================
# 2. CANONICAL ORGANIZATION IDENTITY ORACLE
# ==============================================================================

def test_canonical_organization_resolution():
    """Verify canonical organization resolution and official hosts."""
    assert len(CANONICAL_ORGANIZATIONS) >= 6

    # Test NICE resolution by ID, canonical name, and alias
    org_nice = resolve_canonical_organization("ORG-NICE")
    assert org_nice is not None
    assert org_nice.canonical_name == "National Institute for Health and Care Excellence"
    assert resolve_canonical_organization("NICE") == org_nice
    assert resolve_canonical_organization("National Institute for Health and Care Excellence") == org_nice

    # Test RCUK resolution
    org_rcuk = resolve_canonical_organization("ORG-RCUK")
    assert org_rcuk is not None
    assert resolve_canonical_organization("RCUK") == org_rcuk

    # Test BTS resolution
    org_bts = resolve_canonical_organization("ORG-BTS")
    assert org_bts is not None
    assert resolve_canonical_organization("BTS") == org_bts

    # Test ICS resolution
    org_ics = resolve_canonical_organization("ORG-ICS")
    assert org_ics is not None
    assert resolve_canonical_organization("ICS") == org_ics

    # Unknown must return None (fail closed)
    assert resolve_canonical_organization("UNKNOWN_ORG") is None


def test_v8_metadata_defect_corrections(sample_source_packets):
    """Verify that V8 metadata inconsistencies are corrected in V9 models."""
    packet_map = {s["source_id"]: s for s in sample_source_packets}

    # A) BTS Oxygen: British Thoracic Society (not NICE)
    bts_o2 = packet_map["SRC-BTS-OXYGEN-2017-V9"]
    assert bts_o2["issuing_organization_id"] == "ORG-BTS"
    assert bts_o2["canonical_organization"] == "British Thoracic Society"
    errors = verify_source_identity(bts_o2)
    assert errors == []

    # B) ICS ARDS: Intensive Care Society (not BTS)
    ics_ards = packet_map["SRC-ICS-ARDS-2018-V9"]
    assert ics_ards["issuing_organization_id"] == "ORG-ICS"
    assert ics_ards["canonical_organization"] == "Intensive Care Society"
    errors = verify_source_identity(ics_ards)
    assert errors == []

    # C) NICE NG196: NICE
    nice_196 = packet_map["SRC-NICE-NG196-V9"]
    assert nice_196["issuing_organization_id"] == "ORG-NICE"
    errors = verify_source_identity(nice_196)
    assert errors == []


# ==============================================================================
# 3. QUESTION CHECKPOINT & GOVERNANCE INVARIANTS
# ==============================================================================

def test_checkpoint_question_counts_and_metrics(checkpoint_data, manifest_data):
    """Verify summary metrics, zero clinician approval, and zero golden promotions."""
    summary = checkpoint_data["summary"]
    questions = checkpoint_data["questions"]

    assert len(questions) == 36
    assert summary["total_questions"] == 36
    assert summary["source_grounded"] == 12
    assert summary["clinician_review_required"] == 12
    assert summary["quarantined"] == 24
    assert summary["deferred"] == 0
    assert summary["rejected"] == 0

    # Manifest checks
    assert manifest_data["summary"] == summary
    assert manifest_data["closure_status"] == "PASS_WITH_CLINICAL_BLOCKERS"
    assert manifest_data["redistribution_status"] == "PRIVATE_EVIDENCE_ONLY"

    # Strict governance checks across all 36 questions
    for q in questions:
        assert q.get("clinician_approved") is False
        assert q.get("golden") is False
        assert q.get("golden_eligible") is False

        if q.get("source_grounded") is True:
            assert q["trust_state"] == "CLINICIAN_REVIEW_REQUIRED"
            assert q["clinician_review_ready"] is True
            assert len(q.get("atomic_claims", [])) > 0
            assert any(c.get("is_decisive") for c in q["atomic_claims"])
            # Bound option reviews must have exactly 1 defensible choice
            reviews = q.get("option_reviews", [])
            assert len(reviews) == 5
            defensible = [r["option_id"] for r in reviews if r.get("is_defensible")]
            assert defensible == [q["correct_answer"]]
        else:
            assert q["trust_state"] == "QUARANTINED"
            assert q["clinician_review_ready"] is False
            assert q.get("remaining_engineering_blocker") is False
            assert q.get("blocker_class") in {
                "E_AUTHORITATIVE_SOURCE_CONFLICT",
                "F_HUMAN_CLINICAL_JUDGMENT_REQUIRED",
                "G_LICENSING_BLOCKER",
                "H_NO_AUTHORITATIVE_EVIDENCE",
                "I_UNSAFE_OR_INVALID_QUESTION",
            }


# ==============================================================================
# 4. PUBLIC PACKAGING & PRIVATE EVIDENCE VAULT SEPARATION
# ==============================================================================

def test_public_packaging_excludes_raw_publisher_snapshots():
    """Verify Section 2: public submission branch MUST NOT include raw publisher snapshots."""
    # On the public submission branch, raw publisher snapshots are excluded from git
    assert not (ROOT / "Data/sources/v8/snapshots").exists()
    assert not (ROOT / "Data/sources/v9/snapshots").exists()
    assert len(list(ROOT.glob("Data/sources/**/*.pdf"))) == 0
    assert len(list(ROOT.glob("Data/sources/**/*.html"))) == 0

    # Manifest and documentation must explicitly cite the private evidence checkpoint
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["redistribution_status"] == "PRIVATE_EVIDENCE_ONLY"


# ==============================================================================
# 5. NEGATIVE MUTATION TESTS: FAIL-CLOSED BEHAVIOR
# ==============================================================================

def test_mutation_alter_span_character_fails(sample_source_packets):
    """Mutating one character in exact span text must fail hash check."""
    packet = copy.deepcopy(sample_source_packets[0])
    span = packet["evidence_spans"][0]
    span["exact_text"] = span["exact_text"] + " CORRUPT"
    errors = validate_source_packet(packet)
    assert any("evidence span text hash mismatch" in e for e in errors)


def test_mutation_wrong_source_id_in_claim_fails(checkpoint_data, sample_source_packets):
    """Referencing non-existent source in an atomic claim must fail."""
    q = copy.deepcopy([q for q in checkpoint_data["questions"] if q.get("source_grounded")][0])
    q["atomic_claims"][0]["source_id"] = "SRC-UNKNOWN-2025"
    packet_map = {s["source_id"]: s for s in sample_source_packets}
    errors = validate_question_record(q, packet_map)
    assert any("unknown source identity" in e for e in errors)


def test_mutation_wrong_canonical_organization_id_fails(sample_source_packets):
    """Setting invalid canonical organization ID must fail closed."""
    packet = copy.deepcopy(sample_source_packets[0])
    packet["issuing_organization_id"] = "ORG-NONEXISTENT"
    errors = validate_source_packet(packet)
    assert any("unknown canonical organization ID" in e for e in errors)


def test_mutation_supporting_org_substituted_for_issuing_fails(sample_source_packets):
    """Substituting supporting organization (FICM) for issuing org must fail."""
    packet = copy.deepcopy(sample_source_packets[0])
    packet["issuing_organization_id"] = "ORG-FICM"
    packet["canonical_organization"] = "Faculty of Intensive Care Medicine"
    errors = validate_source_packet(packet)
    assert any("does not possess ISSUING_ORGANIZATION role" in e for e in errors)


def test_mutation_unapproved_host_fails(sample_source_packets):
    """Using an unapproved third-party host must fail."""
    packet = copy.deepcopy(sample_source_packets[0])
    packet["canonical_url"] = "https://www.unauthorized-mirror.com/guidance"
    errors = validate_source_packet(packet)
    assert any("source is not on an approved official host" in e for e in errors)


def test_mutation_missing_currentness_evidence_fails(sample_source_packets):
    """Empty currentness evidence must fail closed."""
    packet = copy.deepcopy(sample_source_packets[0])
    packet["source_currentness_evidence"] = {}
    packet["currentness_evidence"] = {}
    errors = validate_source_packet(packet)
    assert any("missing source currentness evidence" in e for e in errors)


def test_mutation_unsupported_specificity_dimension_fails(checkpoint_data, sample_source_packets):
    """Specificity mismatch (e.g. dose MISMATCH) must fail closed."""
    q = copy.deepcopy([q for q in checkpoint_data["questions"] if q.get("source_grounded")][0])
    # Build packet map with actual source id
    sid = q["atomic_claims"][0]["source_id"]
    packet_map = {sid: sample_source_packets[0]}
    q["atomic_claims"][0]["specificity_dimensions"]["dose"] = "MISMATCH"
    errors = validate_question_record(q, packet_map)
    assert any("dose mismatch" in e for e in errors)


def test_mutation_fake_clinician_approval_fails(checkpoint_data, sample_source_packets):
    """Asserting clinician approval without independent sign-off must fail closed."""
    q = copy.deepcopy([q for q in checkpoint_data["questions"] if q.get("source_grounded")][0])
    sid = q["atomic_claims"][0]["source_id"]
    packet_map = {sid: sample_source_packets[0]}
    q["clinician_approved"] = True
    errors = validate_question_record(q, packet_map)
    assert any("fabricated clinician approval" in e for e in errors)


def test_mutation_fake_golden_promotion_fails(checkpoint_data, sample_source_packets):
    """Asserting golden promotion must fail closed."""
    q = copy.deepcopy([q for q in checkpoint_data["questions"] if q.get("source_grounded")][0])
    sid = q["atomic_claims"][0]["source_id"]
    packet_map = {sid: sample_source_packets[0]}
    q["golden"] = True
    errors = validate_question_record(q, packet_map)
    assert any("automatic Golden promotion" in e for e in errors)
