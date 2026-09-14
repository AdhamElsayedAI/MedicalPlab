"""
Tests for fail-closed abstention in the Grounded Generative Tutor.

Verifies:
1. Fail-closed abstention on out-of-scope / unsupported clinical queries.
2. Fail-closed abstention when evidence retrieval fails or produces no candidates.
3. Fail-closed abstention when candidate sources are blocked by the Source Rights Gate.
4. Guaranteed zero unsupported medical output served in any abstention state.
"""

from unittest.mock import MagicMock
from medicalplab.tutor.models import TutorChatRequest
from medicalplab.tutor.service import TutorService
from medicalplab.tutor.rights import SourceRightsGate
from medicalplab.tutor.provider import StubGenerativeProvider
from medicalplab.evidence_engine.models import EvidencePacket, RetrievedCandidate, QueryRepresentation


def _make_query_rep(q: str) -> QueryRepresentation:
    return QueryRepresentation(
        original_query=q,
        canonical_query=q,
        neutral_target=q,
    )


def test_abstain_on_empty_retrieval_candidates():
    mock_engine = MagicMock()
    mock_engine.query.return_value = EvidencePacket(
        query=_make_query_rep("Random nonexistent query xyz123"),
        routed_document_ids=[],
        candidates=[],
        top_passage=None,
        abstain=True,
        abstain_reason="NO_CANDIDATES_RETRIEVED",
    )
    service = TutorService(engine=mock_engine, provider=StubGenerativeProvider())

    req = TutorChatRequest(query="Random nonexistent query xyz123")
    res = service.chat(req, x_user_id="test_user")

    assert res.abstain is True
    assert res.support_status == "ABSTAIN"
    assert res.abstain_reason == "NO_CANDIDATES_RETRIEVED"
    assert "No verified basic-science evidence was retrieved" in res.message


def test_abstain_on_source_rights_not_allowed():
    mock_engine = MagicMock()
    cand = RetrievedCandidate(
        chunk_id="nice_ng12_chunk_001",
        document_id="nice_guideline_ng12",
        text="Follow the NICE NG12 clinical pathway for colic.",
        fused_score=0.95,
    )
    mock_engine.query.return_value = EvidencePacket(
        query=_make_query_rep("What is the NICE management guideline for renal colic?"),
        routed_document_ids=["nice_guideline_ng12"],
        candidates=[cand],
        top_passage=cand,
        abstain=False,
    )
    service = TutorService(engine=mock_engine, provider=StubGenerativeProvider())

    req = TutorChatRequest(query="What is the NICE management guideline for renal colic?")
    res = service.chat(req, x_user_id="test_user")

    assert res.abstain is True
    assert res.support_status == "ABSTAIN"
    assert res.abstain_reason == "SOURCE_RIGHTS_NOT_ALLOWED"
    assert "AI_REUSE_REQUIRES_PERMISSION" in res.message


def test_unsupported_generation_triggers_safe_fallback_with_zero_leaks():
    # If the provider generates claims not entailed by the evidence, fallback is applied
    class HallucinatingProvider(StubGenerativeProvider):
        def generate_structured(self, system_prompt, user_prompt, response_schema, **kwargs):
            resp = super().generate_structured(system_prompt, user_prompt, response_schema, **kwargs)
            resp.data["mechanistic_explanation"] = (
                "The patient must immediately receive 100mg IV furosemide to cure the renal failure completely."
            )
            return resp

    service = TutorService(provider=HallucinatingProvider())
    req = TutorChatRequest(
        query="Explain the mechanism of glomerular filtration in RAAS",
        question_id="UNI-RENAL-001",
    )
    res = service.chat(req, x_user_id="test_user")

    assert res.fallback_applied is True
    # The hallucinated cure/dose assertion must NOT be served
    assert "100mg" not in (res.mechanistic_explanation or "")
    assert "cure" not in (res.mechanistic_explanation or "")
    assert "furosemide" not in (res.message or "")


def test_abstention_guarantees_empty_citations_and_safe_state():
    mock_engine = MagicMock()
    mock_engine.query.return_value = EvidencePacket(
        query=_make_query_rep("Emergency dialysis protocol"),
        routed_document_ids=[],
        candidates=[],
        top_passage=None,
        abstain=True,
        abstain_reason="LOW_RETRIEVAL_CONFIDENCE",
    )
    service = TutorService(engine=mock_engine, provider=StubGenerativeProvider())

    req = TutorChatRequest(query="Emergency dialysis protocol")
    res = service.chat(req, x_user_id="test_user")

    assert res.abstain is True
    assert len(res.citations) == 0
    assert res.socratic_question is None
    assert res.hints is None
