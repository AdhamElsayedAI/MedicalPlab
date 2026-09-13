"""V6 Online Canonical Integration Test Suite.

Executes live HTTPS network verification against:
1. NCBI E-utilities API for peer-reviewed PMCIDs (testing genuine vs suspect mismatch).
2. Official guideline publishing authorities (extracting real HTML title/metadata).
3. Strict fail-closed verification when offline.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from medicalplab.plab.v6.canonical_source_resolver import (
    SourceVerificationStatus,
    V6CanonicalSourceResolver,
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent


def test_online_ncbi_pmc_genuine_resolution(tmp_path):
    """Live online test: Genuine PMCID PMC10980676 (Laghlam 2024 Annals of Intensive Care)."""
    receipts_file = tmp_path / "live_receipts.jsonl"
    resolver = V6CanonicalSourceResolver(online_mode=True, receipts_store_path=receipts_file)

    sid = "SRC-LAGHLAM-2024-PMC10980676"
    receipt = resolver.resolve_ncbi_pmc(
        source_id=sid,
        pmcid="PMC10980676",
        declared_title="Management of cardiogenic shock: a narrative review",
    )

    assert receipt.identity_verification_status == SourceVerificationStatus.IDENTITY_VERIFIED
    assert receipt.http_status == 200
    assert "cardiogenic shock" in receipt.canonical_title.lower()
    assert len(receipt.raw_response_hash) == 64
    assert receipt.canonical_organization == "NCBI / National Library of Medicine"


def test_online_ncbi_pmc_suspect_mismatch_fails(tmp_path):
    """Live online test: Suspect PMCID PMC10056781 (olive fruit fly paper) claiming cardiogenic shock."""
    receipts_file = tmp_path / "live_receipts.jsonl"
    resolver = V6CanonicalSourceResolver(online_mode=True, receipts_store_path=receipts_file)

    sid = "SRC-SUSPECT-PMC10056781"
    receipt = resolver.resolve_ncbi_pmc(
        source_id=sid,
        pmcid="PMC10056781",
        declared_title="Management of cardiogenic shock: a narrative review",
    )

    assert receipt.identity_verification_status == SourceVerificationStatus.IDENTITY_MISMATCH
    assert receipt.http_status == 200
    assert "bactrocera oleae" in receipt.canonical_title.lower() or "olive" in receipt.canonical_title.lower()


def test_offline_mode_prohibits_fabricating_truth(tmp_path):
    """Test: Offline mode cannot fabricate new canonical truth; returns UNRESOLVED."""
    receipts_file = tmp_path / "empty_receipts.jsonl"
    resolver = V6CanonicalSourceResolver(online_mode=False, receipts_store_path=receipts_file)

    receipt = resolver.resolve_ncbi_pmc(
        source_id="SRC-NEW-PMC9999999",
        pmcid="PMC9999999",
        declared_title="Uncached Paper",
    )

    assert receipt.identity_verification_status == SourceVerificationStatus.UNRESOLVED
    assert "Offline mode active" in receipt.explanation


def test_official_guideline_resolution_online(tmp_path):
    """Live online test: Resolves official guideline from British Thoracic Society official domain."""
    receipts_file = tmp_path / "live_receipts.jsonl"
    resolver = V6CanonicalSourceResolver(online_mode=True, receipts_store_path=receipts_file)

    sid = "SRC-BTS-OXYGEN-2017"
    receipt = resolver.resolve_official_guideline(
        source_id=sid,
        canonical_identifier="BTS-OXYGEN-2017",
        canonical_url="https://www.brit-thoracic.org.uk/quality-improvement/guidelines/emergency-oxygen/",
        declared_title="BTS Guideline for oxygen use in healthcare and emergency settings",
        organization="British Thoracic Society",
        publication_year=2017,
    )

    assert receipt.identity_verification_status == SourceVerificationStatus.IDENTITY_VERIFIED
    assert receipt.http_status == 200
    assert len(receipt.canonical_title) > 0
    assert len(receipt.raw_response_hash) == 64
