"""Tests for Source Rights Gate."""
from __future__ import annotations

import pytest
from medicalplab.evidence_engine.models import RetrievedCandidate
from medicalplab.tutor.rights import (
    AIReuseStatus,
    DisplayQuotationStatus,
    SourceRightsGate,
)


def test_16_renal_documents_cleared_for_ai_reuse():
    gate = SourceRightsGate()
    for i in range(1, 17):
        doc_id = f"DOC-PMC-RENAL-{i:04d}"
        ai_stat, disp_stat, reason = gate.check_document(doc_id)
        assert ai_stat == AIReuseStatus.AI_REUSE_ALLOWED, f"{doc_id} should be AI_REUSE_ALLOWED"
        assert disp_stat == DisplayQuotationStatus.DISPLAY_ALLOWED
        assert gate.is_ai_reuse_allowed(doc_id) is True


def test_cardiorespiratory_and_guidelines_fail_closed():
    gate = SourceRightsGate()
    blocked_docs = [
        "NICE-NG136",
        "BNF-RENAL-01",
        "RCUK-ALS-2021",
        "DOC-PMC-CARDIO-0001",
        "UNKNOWN-SOURCE-999",
    ]
    for doc_id in blocked_docs:
        ai_stat, disp_stat, reason = gate.check_document(doc_id)
        assert ai_stat in {AIReuseStatus.AI_REUSE_REQUIRES_PERMISSION, AIReuseStatus.AI_REUSE_UNKNOWN}
        assert gate.is_ai_reuse_allowed(doc_id) is False


def test_filter_candidates_removes_unauthorized_sources():
    gate = SourceRightsGate()
    cands = [
        RetrievedCandidate(chunk_id="c1", document_id="DOC-PMC-RENAL-0001", text="Renal text"),
        RetrievedCandidate(chunk_id="c2", document_id="NICE-NG136", text="NICE guideline text"),
        RetrievedCandidate(chunk_id="c3", document_id="DOC-PMC-RENAL-0002", text="Glomerular text"),
        RetrievedCandidate(chunk_id="c4", document_id="RCUK-ALS", text="Resuscitation text"),
    ]
    filtered = gate.filter_candidates(cands)
    assert len(filtered) == 2
    assert [c.document_id for c in filtered] == ["DOC-PMC-RENAL-0001", "DOC-PMC-RENAL-0002"]


def test_export_manifest_creates_valid_json(tmp_path):
    gate = SourceRightsGate()
    out_file = tmp_path / "tutor_rights.json"
    gate.export_tutor_rights_manifest(out_file)
    assert out_file.exists()
    assert "DOC-PMC-RENAL-0001" in out_file.read_text(encoding="utf-8")
