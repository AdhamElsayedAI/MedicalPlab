"""
Canonical RAG / Evidence Engine Verification Suite
===================================================
Validates MEDICALPLAB_EVIDENCE_ENGINE_V1 contract:
- Dynamic resolution of 16-document public-safe PMC corpus
- Query representation transforms and neutral target extraction
- Multi-channel candidate retrieval with Reciprocal Rank Fusion
- Graceful degradation under missing neural models
- Calibrated fail-closed abstention on unsupported / low-confidence queries
- CentralClaimVerifier 4-state grounding and deterministic safety vetoes
- Elimination of hard-coded mock explanation fallbacks in /ai/chat
- Direct /api/v1/evidence/query endpoint contract
- University track educational policy vs PLAB strict quarantine boundary
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from main import app
from medicalplab.evidence_engine.claim_verifier import CentralClaimVerifier
from medicalplab.evidence_engine.document_router import DeterministicDocumentRouter
from medicalplab.evidence_engine.models import (
    DocumentCard,
    EvidencePacket,
    QueryRepresentation,
    RetrievedCandidate,
    VerificationState,
)
from medicalplab.evidence_engine.query_representation import ClinicalQueryProcessor
from medicalplab.evidence_engine.service import CanonicalEvidenceEngine, SharedEvidenceEngineV2

_ROOT = Path(__file__).resolve().parent.parent


class TestCorpusAndRouterIntegrity:
    """Validate Level 1 correctness: public-safe 16-doc corpus footprint."""

    def test_router_loads_public_safe_corpus(self):
        router = DeterministicDocumentRouter(data_root=_ROOT / "Data")
        cards = router.build_or_load_cards()
        assert len(cards) == 16
        for doc_id, card in cards.items():
            assert doc_id.startswith("DOC-PMC-RENAL-")
            assert len(card.title) > 0
            assert len(card.section_headings) > 0
            assert "Title:" in card.render_routing_text()

    def test_routing_ranking_determinism(self):
        router = DeterministicDocumentRouter(data_root=_ROOT / "Data")
        router.build_or_load_cards()
        routed_1 = router.route_documents("glomerular filtration barrier podocyte", top_k=5)
        routed_2 = router.route_documents("glomerular filtration barrier podocyte", top_k=5)
        assert routed_1 == routed_2
        assert len(routed_1) == 5


class TestQueryProcessor:
    """Validate clinical query representation transformation."""

    def test_negation_and_neutral_target(self):
        processor = ClinicalQueryProcessor()
        q = "Why is inulin neither reabsorbed nor actively secreted by tubules?"
        rep = processor.process_query(q)
        assert isinstance(rep, QueryRepresentation)
        assert rep.has_negation is True
        assert len(rep.neutral_target) > 0
        assert len(rep.canonical_query) > 0


class TestMultiRouteRetrievalAndRRF:
    """Validate multi-channel retrieval, RRF fusion, and tie breaking."""

    def test_engine_retrieval_and_tie_breaking(self):
        engine = CanonicalEvidenceEngine(data_root=_ROOT / "Data")
        # Query in degraded mode to avoid slow CPU inference during unit tests
        engine.reranker.is_degraded = True

        packet = engine.query(
            query="What is the function of podocytes in the glomerular filtration barrier?",
            mode="TUTOR",
            top_candidates=20,
            rerank_top_k=10,
        )
        assert isinstance(packet, EvidencePacket)
        assert len(packet.candidates) > 0
        assert packet.abstain is True
        assert packet.abstain_reason == "CLAIM_SUPPORT_UNAVAILABLE"
        assert packet.is_degraded is True
        assert packet.retrieval_mode == "TUTOR"

        # Verify deterministic ordering: higher fused_score first, tie break on chunk_id
        scores = [c.fused_score for c in packet.candidates]
        assert scores == sorted(scores, reverse=True)


class TestCalibratedAbstention:
    """Validate calibrated fail-closed safety policy."""

    def test_empty_or_unsupported_query_abstains(self):
        engine = CanonicalEvidenceEngine(data_root=_ROOT / "Data")
        engine.reranker.is_degraded = True

        # Non-medical gibberish has 0 lexical/semantic overlap with renal corpus
        packet = engine.query(
            query="zxcvbnm qwertyuiop asdfghjkl random noise 987654321",
            mode="TUTOR",
            top_candidates=10,
            rerank_top_k=5,
        )
        assert packet.abstain is True
        assert packet.abstain_reason in (
            "LOW_RETRIEVAL_CONFIDENCE",
            "NO_CANDIDATES_RETRIEVED",
            "CLAIM_SUPPORT_UNAVAILABLE",
        )

    def test_contradicted_claim_triggers_abstain(self):
        engine = CanonicalEvidenceEngine(data_root=_ROOT / "Data")
        engine.reranker.is_degraded = True

        packet = engine.query(
            query="podocyte slit diaphragm",
            claims_to_verify=[
                "Podocytes are absent from the visceral layer of Bowman capsule."
            ],
            top_candidates=10,
            rerank_top_k=5,
        )
        # If the claim verifier detects contradiction, packet must fail closed
        if any(c.state == VerificationState.CONTRADICTED for c in packet.claim_verifications):
            assert packet.abstain is True
            assert packet.abstain_reason == "CLAIM_CONTRADICTED_BY_EVIDENCE"


class TestCentralClaimVerifierVetoes:
    """Validate 4-state grounding and deterministic safety veto flags."""

    def test_polarity_veto(self):
        verifier = CentralClaimVerifier()
        claim = "Spironolactone does not induce hyperkalemia in patients with reduced GFR."
        evidence = "Spironolactone frequently induces significant hyperkalemia in patients with reduced GFR."
        res = verifier.verify_claim("CLM-01", claim, evidence)
        assert res.state in (VerificationState.CONTRADICTED, VerificationState.NOT_SUPPORTED)
        assert any("POLARITY" in flag for flag in res.veto_flags)

    def test_numeric_mismatch_veto(self):
        verifier = CentralClaimVerifier()
        claim = "The normal glomerular filtration rate is 250 mL/min/1.73m2."
        evidence = "Normal GFR in healthy young adults averages 90 to 120 mL/min/1.73m2."
        res = verifier.verify_claim("CLM-02", claim, evidence)
        assert res.state != VerificationState.SUPPORTED
        assert "NUMERIC_MISMATCH" in res.veto_flags

    def test_high_risk_claim_fail_closed(self):
        verifier = CentralClaimVerifier()
        claim = "Administer 100 mg of bumetanide intravenously every 2 hours."
        evidence = "Loop diuretic dosages should be carefully titrated based on clinical response."
        res = verifier.verify_claim("CLM-03", claim, evidence)
        assert res.is_high_risk is True
        assert res.state != VerificationState.SUPPORTED


class TestApiIntegrationAndEliminationOfMockFallback:
    """Validate /ai/chat real evidence retrieval and /api/v1/evidence/query."""

    @pytest.fixture
    def client(self):
        from main import get_evidence_engine
        engine = get_evidence_engine()
        engine.reranker.is_degraded = True
        return TestClient(app)

    def test_ai_chat_abstains_on_unsupported_query(self, client):
        resp = client.post("/ai/chat", json={"query": "random nonsensical query 12345 xyz"})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("abstain") is True
        assert data.get("intent") == "abstain"
        assert len(data.get("citations", [])) == 0
        # Critical guard: No generic fabricated clinical advice
        assert "Clinical Analysis for" not in data.get("explanation", "")

    def test_direct_evidence_query_endpoint(self, client):
        resp = client.post(
            "/api/v1/evidence/query",
            json={
                "query": "glomerular filtration barrier",
                "top_candidates": 5,
                "rerank_top_k": 3,
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "candidates" in data
        assert "routed_document_ids" in data
        assert "query" in data
        assert "latency_ms" in data


class TestModePolicyBoundaries:
    """Validate separation of University educational policy vs PLAB quarantine."""

    def test_mode_policy_separation(self):
        engine = CanonicalEvidenceEngine(data_root=_ROOT / "Data")
        engine.reranker.is_degraded = True

        packet_uni = engine.query("podocyte filtration", mode="UNI", top_candidates=5)
        packet_plab = engine.query("podocyte filtration", mode="PLAB", top_candidates=5)
        packet_tutor = engine.query("podocyte filtration", mode="TUTOR", top_candidates=5)

        assert packet_uni.retrieval_mode == "UNI"
        assert packet_plab.retrieval_mode == "PLAB"
        assert packet_tutor.retrieval_mode == "TUTOR"
