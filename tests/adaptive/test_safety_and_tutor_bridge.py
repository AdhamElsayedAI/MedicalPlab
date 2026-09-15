"""Tests for AdaptiveTutorBridge and safety fail-closed constraints."""
from __future__ import annotations

import pytest
from medicalplab.adaptive.service import AdaptiveLearningService
from medicalplab.adaptive.tutor_bridge import AdaptiveTutorBridge
from medicalplab.stage_g.product_api import get_tutor_service
from medicalplab.tutor.models import TutorChatResponse
from medicalplab.tutor.provider import GenerativeProvider, StubGenerativeProvider
from medicalplab.tutor.service import TutorService


def test_tutor_bridge_delegates_to_grounded_tutor():
    """Verify that AdaptiveTutorBridge routes strictly through TutorService.chat."""
    bridge = AdaptiveTutorBridge()
    resp = bridge.trigger_remediation(
        learner_id="test_student",
        topic="RAAS mechanisms",
        question_id="UNI-RENAL-001",
        preferred_mode="socratic_hint",
    )
    assert isinstance(resp, TutorChatResponse)
    assert resp.pedagogical_state == "PRE_SUBMISSION"
    # Verification summary must exist
    assert hasattr(resp, "verification")
    # Unsupported propositions served must be ZERO
    assert resp.verification.unsupported_propositions == 0


def test_adaptive_service_triggers_grounded_remediation_for_active_weakness():
    service = AdaptiveLearningService()
    resp = service.trigger_grounded_remediation(
        learner_id="test_student_adaptive",
        topic="Glomerular filtration barrier",
        preferred_mode="socratic_hint",
    )
    assert isinstance(resp, TutorChatResponse)
    assert resp.verification.unsupported_propositions == 0
    # Must not leak answer
    assert resp.support_status in {"SUPPORTED", "SAFE_FALLBACK"}


def test_unsupported_claims_trigger_safe_fallback_in_adaptive_flow():
    """Verify that if generation hallucinates, the fail-closed SAFE_FALLBACK is preserved."""
    hallucinating_draft = {
        "message": "Renin is synthesized by pulmonary endothelial cells and converts aldosterone into dopamine.",
        "socratic_question": "What receptor does dopamine bind to?",
        "hints": ["Check your pulmonary anatomy."],
        "citations": [
            {
                "ref": "PMC3997861",
                "quote": "Renin is synthesized by pulmonary endothelial cells.",
                "document_id": "DOC-PMC-RENAL-0001",
                "chunk_id": "DOC-PMC-RENAL-0001-B0003-C01",
            }
        ],
    }
    stub_provider = StubGenerativeProvider()
    stub_provider.set_custom_response("", hallucinating_draft)
    custom_tutor = TutorService(provider=stub_provider)
    bridge = AdaptiveTutorBridge(tutor_service=custom_tutor)

    resp = bridge.trigger_remediation(
        learner_id="adversarial_student",
        topic="RAAS mechanisms",
        question_id="UNI-RENAL-001",
    )

    # Must fail closed: fallback applied, zero unsupported claims served
    assert resp.fallback_applied is True
    assert resp.support_status == "SAFE_FALLBACK"
    assert resp.verification.unsupported_propositions == 0
    assert "dopamine" not in resp.message.lower()


def test_out_of_scope_topic_abstains_safely():
    """Verify that clinical or non-renal topics abstain fail-closed."""
    bridge = AdaptiveTutorBridge()
    resp = bridge.trigger_remediation(
        learner_id="student_out_of_scope",
        topic="Cardiology Advanced Oncology Staging",
    )
    assert resp.abstain is True
    assert resp.support_status == "ABSTAIN"
    assert resp.abstain_reason == "OUT_OF_SCOPE_TOPIC"
