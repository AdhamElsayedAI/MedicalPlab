"""
MedicalPlab Shared Evidence Engine V2 — Automated Test Suite
============================================================
Validates:
- Query representation transforms and neutral target extraction
- Extractive document cards and deterministic document routing
- Three-route reciprocal rank fusion candidate retrieval
- CentralClaimVerifier 4-state grounding and deterministic vetoes
- PLAB question schemas and verification flags
"""

import pytest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

from medicalplab.evidence_engine.claim_verifier import CentralClaimVerifier
from medicalplab.evidence_engine.document_router import DeterministicDocumentRouter
from medicalplab.evidence_engine.models import (
    DocumentCard,
    QueryRepresentation,
    RetrievedCandidate,
    VerificationState,
)
from medicalplab.evidence_engine.query_representation import ClinicalQueryProcessor


class TestQueryRepresentation:
    def test_clinical_query_processor(self):
        processor = ClinicalQueryProcessor()
        q = "Which cell types constitute the trilaminar glomerular filtration barrier?"
        rep = processor.process_query(q)

        assert isinstance(rep, QueryRepresentation)
        assert rep.original_query == q
        assert len(rep.canonical_query) > 0
        assert len(rep.neutral_target) > 0
        assert rep.has_negation is False

    def test_negation_detection(self):
        processor = ClinicalQueryProcessor()
        q = "Why is inulin not reabsorbed or secreted by the renal tubules?"
        rep = processor.process_query(q)
        assert rep.has_negation is True


class TestDocumentRouting:
    def test_document_cards_are_extractive(self):
        router = DeterministicDocumentRouter(data_root=_ROOT / "Data")
        cards = router.build_or_load_cards()

        assert len(cards) >= 16
        for doc_id, card in cards.items():
            assert isinstance(card, DocumentCard)
            assert card.document_id == doc_id
            assert card.title != ""
            assert card.authority != ""
            assert len(card.section_headings) > 0
            text = card.render_routing_text()
            assert "Title:" in text
            assert "Overview:" in text

    def test_routing_without_models(self):
        router = DeterministicDocumentRouter(data_root=_ROOT / "Data")
        router.build_or_load_cards()
        # Default lexical / fallback routing
        routed = router.route_documents("hyperkalemia cardiac arrest", top_k=5)
        assert len(routed) == 5
        assert all(isinstance(d, str) for d in routed)


class TestCentralClaimVerifier:
    def test_supported_claim(self):
        verifier = CentralClaimVerifier()
        claim = "Intravenous calcium gluconate restores resting myocardial threshold potential."
        evidence = (
            "In severe hyperkalemia, intravenous calcium gluconate restores resting membrane "
            "threshold potential to prevent lethal ventricular arrhythmias without lowering serum potassium."
        )
        res = verifier.verify_claim(
            claim_id="TEST-01",
            claim_text=claim,
            evidence_text=evidence,
            cited_chunk_id="CHUNK-01",
            cited_document_id="DOC-01"
        )
        assert res.state == VerificationState.SUPPORTED
        assert res.confidence >= 0.85
        assert len(res.veto_flags) == 0

    def test_negation_veto(self):
        verifier = CentralClaimVerifier()
        claim = "Spironolactone does not cause hyperkalemia in chronic kidney disease."
        evidence = "Spironolactone promotes hyperkalemia in patients with reduced renal clearance."
        res = verifier.verify_claim(
            claim_id="TEST-02",
            claim_text=claim,
            evidence_text=evidence
        )
        assert res.state in (VerificationState.CONTRADICTED, VerificationState.NOT_SUPPORTED)
        assert "POLARITY_MISMATCH" in res.veto_flags or "POLARITY_CONTRADICTION" in res.veto_flags

    def test_numeric_discrepancy_veto(self):
        verifier = CentralClaimVerifier()
        claim = "Normal serum potassium concentration is 12.5 mmol/L."
        evidence = "Normal serum potassium is maintained strictly between 3.5 and 5.0 mmol/L."
        res = verifier.verify_claim(
            claim_id="TEST-03",
            claim_text=claim,
            evidence_text=evidence
        )
        assert res.state != VerificationState.SUPPORTED
        assert "NUMERIC_MISMATCH" in res.veto_flags

    def test_high_risk_claim_fail_closed(self):
        verifier = CentralClaimVerifier()
        claim = "The recommended starting dose is 500 mg every 4 hours."
        evidence = "Dosing depends upon clinical severity and kidney function."
        res = verifier.verify_claim(
            claim_id="TEST-04",
            claim_text=claim,
            evidence_text=evidence
        )
        assert res.is_high_risk is True
        assert res.state != VerificationState.SUPPORTED


class TestRetrievedCandidateContract:
    def test_candidate_rendering(self):
        cand = RetrievedCandidate(
            chunk_id="TEST-CHUNK-01",
            document_id="TEST-DOC-01",
            section_path=["Pathophysiology", "Tubular Transport"],
            heading="Proximal Tubule NBCe1",
            text="NBCe1-A mediates basolateral bicarbonate efflux.",
            doc_title="Renal Acid-Base Physiology",
            fused_score=0.88,
        )
        rendered = cand.render_structured_passage()
        assert "Title: Renal Acid-Base Physiology" in rendered
        assert "Section Path: Pathophysiology > Tubular Transport" in rendered
        assert "Evidence: NBCe1-A mediates basolateral bicarbonate efflux." in rendered


class TestSharedEvidenceEngineV2:
    def test_engine_initialization_and_packet_contract(self):
        from medicalplab.evidence_engine.service import SharedEvidenceEngineV2
        from medicalplab.evidence_engine.models import EvidencePacket

        engine = SharedEvidenceEngineV2(data_root=_ROOT / "Data")
        assert engine.router is not None
        assert len(engine.router.cards) >= 16

        # Query without deep models loaded (uses BM25 + deterministic routing)
        packet = engine.query(
            query="What causes hypokalemia in Bartter syndrome?",
            claims_to_verify=[
                "Bartter syndrome involves impaired loop of Henle sodium-potassium-chloride cotransport."
            ],
            top_candidates=50,
            rerank_top_k=25,
        )
        assert isinstance(packet, EvidencePacket)
        assert packet.query.original_query == "What causes hypokalemia in Bartter syndrome?"
        assert len(packet.routed_document_ids) > 0
        assert len(packet.candidates) > 0
        assert packet.top_passage is not None
        assert len(packet.claim_verifications) == 1
        assert packet.abstain is True
        assert packet.abstain_reason in {
            "CLAIM_NOT_DIRECTLY_SUPPORTED",
            "HIGH_RISK_CLAIM_UNSUPPORTED",
            "LOW_RETRIEVAL_CONFIDENCE",
        }
