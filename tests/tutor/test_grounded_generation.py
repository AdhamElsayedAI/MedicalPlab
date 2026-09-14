"""Tests for Grounded Generation end-to-end execution."""
from __future__ import annotations

import pytest
from medicalplab.tutor.models import TutorChatRequest
from medicalplab.tutor.service import TutorService


def test_grounded_generation_raas_pre_submission():
    service = TutorService()
    req = TutorChatRequest(
        query="In the renin-angiotensin pathway, what substrate does active renin cleave?",
        question_id="UNI-RENAL-001",
        mode="socratic_hint",
    )
    resp = service.chat(req, x_user_id="test_student_01")

    assert resp.pedagogical_state == "PRE_SUBMISSION"
    assert resp.abstain is False
    assert resp.support_status == "SUPPORTED"
    assert resp.fallback_applied is False
    assert len(resp.citations) >= 1
    assert resp.citations[0].document_id == "DOC-PMC-RENAL-0001"
    assert resp.citations[0].pmcid == "PMC3997861"
    assert resp.distractor_analysis is None  # Pre-submission must not have distractor giveaway
    assert resp.verification.unsupported_propositions == 0


def test_grounded_generation_filtration_barrier():
    service = TutorService()
    req = TutorChatRequest(
        query="What layers comprise the glomerular filtration barrier?",
        mode="mechanistic_explanation",
    )
    resp = service.chat(req, x_user_id="test_student_01")

    assert resp.pedagogical_state == "GENERAL_STUDY"
    assert resp.abstain is False
    assert resp.support_status in {"SUPPORTED", "SAFE_FALLBACK"}
    assert resp.support_status != "PARTIALLY_SUPPORTED"
    assert resp.message != ""


def test_no_partially_supported_substantive_response_served():
    """Prove that:
    1. All substantive propositions supported -> SERVE + SUPPORTED
    2. Any substantive proposition partially/not supported -> ABSTAIN/FALLBACK
    3. No PARTIALLY_SUPPORTED substantive medical response may be served
    """
    from medicalplab.tutor.provider import StubGenerativeProvider

    service = TutorService(provider=StubGenerativeProvider())

    # 1. All substantive propositions supported -> SERVE + SUPPORTED
    req_valid = TutorChatRequest(
        query="In the renin-angiotensin pathway, what substrate does active renin cleave?",
        question_id="UNI-RENAL-001",
        mode="socratic_hint",
    )
    resp_valid = service.chat(req_valid, x_user_id="test_student_01")
    assert resp_valid.support_status == "SUPPORTED"
    assert resp_valid.fallback_applied is False
    assert resp_valid.verification.unsupported_propositions == 0
    assert resp_valid.verification.supported_propositions > 0
    assert resp_valid.support_status != "PARTIALLY_SUPPORTED"

    # 2. Substantive proposition partially/not supported -> Transitions to SAFE_FALLBACK
    stub_partial = StubGenerativeProvider()
    stub_partial.set_custom_response(
        "ungrounded_claim",
        {
            "message": "Renin directly converts aldosterone into cortisol in the renal collecting duct.",
            "socratic_question": "What is the function of cortisol in the kidney?",
            "hints": ["Consider glucocorticoid effects on renal vasculature."],
            "citations": [
                {
                    "ref": "DOC-PMC-RENAL-0001:C001",
                    "quote": "Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I (Ang I).",
                    "document_id": "DOC-PMC-RENAL-0001",
                    "chunk_id": "DOC-PMC-RENAL-0001-B0003-C01",
                }
            ],
        },
    )
    service_partial = TutorService(provider=stub_partial)
    req_unverified = TutorChatRequest(
        query="ungrounded_claim: In the renin-angiotensin pathway, what substrate does active renin cleave?",
        question_id="UNI-RENAL-001",
        mode="socratic_hint",
    )
    resp_unverified = service_partial.chat(req_unverified, x_user_id="test_student_01")

    # Invariant: Must transition to SAFE_FALLBACK, never served as PARTIALLY_SUPPORTED
    assert resp_unverified.fallback_applied is True
    assert resp_unverified.support_status == "SAFE_FALLBACK"
    assert resp_unverified.support_status != "PARTIALLY_SUPPORTED"
    # Invariant: The ungrounded medical claim was NOT served
    assert "cortisol" not in resp_unverified.message.lower()
    assert "aldosterone into cortisol" not in resp_unverified.message.lower()

    # 3. Universal invariant: No PARTIALLY_SUPPORTED response may ever be served
    assert resp_valid.support_status != "PARTIALLY_SUPPORTED"
    assert resp_unverified.support_status != "PARTIALLY_SUPPORTED"
