"""
Regression tests for the PHASE 1 live-veto forensic audit reporting-fidelity fix.

Verifies:
1. Requested vs actual generation provider/model are recorded correctly, and a
   fallback model never silently masquerades as the primary/requested one.
2. Automatic provider failover is recorded explicitly (provider_failover_applied,
   primary_provider_error), without altering CentralClaimVerifier semantics.
3. Rejected-draft proposition/veto metrics (`draft_verification`) remain fully
   separate from served-response metrics (`verification`).
4. When SAFE_FALLBACK replaces a rejected draft, `verification` is recomputed
   against the ACTUAL served fallback content, never reused from the draft.
5. Zero unsupported substantive propositions are ever served, and fail-closed
   behavior is unchanged.
"""
from __future__ import annotations

import json

from medicalplab.tutor.models import TutorChatRequest
from medicalplab.tutor.provider import ProviderResponse, StubGenerativeProvider
from medicalplab.tutor.service import TutorService


class FailoverHallucinatingProvider:
    """Simulates: requested primary model 429s, an automatic failover model succeeds,
    but the generated content contains an unauthorized clinical claim that must be
    rejected by post-generation safety/verification checks."""

    provider_name = "google_gemini"
    model_name = "gemini-3.8-flash"  # requested/primary model

    def generate_structured(self, system_prompt, user_prompt, response_schema, **kwargs):
        data = {
            "message": "Consider the mechanism of diuresis in this scenario.",
            "socratic_question": "What is the function of loop diuretics here?",
            "hints": ["Recall the site of action along the nephron."],
            "mechanistic_explanation": (
                "The patient must immediately receive 100mg IV furosemide to cure the "
                "renal failure completely."
            ),
            "citations": [],
        }
        return ProviderResponse(
            raw_text=json.dumps(data),
            structured_data=data,
            input_tokens=142,
            output_tokens=63,
            model="gemini-3.5-flash",  # ACTUAL model that produced this generation
            provider="google_gemini",
            requested_model="gemini-3.8-flash",
            provider_failover_applied=True,
            primary_provider_error="Gemini API (gemini-3.8-flash) error 429: Quota exceeded for model.",
        )


class NoFailoverProvider:
    """Simulates the common case: the requested/primary model succeeds directly,
    no failover occurs."""

    provider_name = "google_gemini"
    model_name = "gemini-3.8-flash"

    def generate_structured(self, system_prompt, user_prompt, response_schema, **kwargs):
        data = {
            "message": "Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I.",
            "socratic_question": "What substrate does active renin act upon?",
            "hints": ["Recall the substrate of active renin."],
            "revision_summary": "Active renin cleaves angiotensinogen to generate angiotensin I.",
            "citations": [
                {
                    "ref": "DOC-PMC-RENAL-0001:C001",
                    "quote": "Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I (Ang I).",
                    "document_id": "DOC-PMC-RENAL-0001",
                    "chunk_id": "DOC-PMC-RENAL-0001-B0003-C01",
                }
            ],
        }
        return ProviderResponse(
            raw_text=json.dumps(data),
            structured_data=data,
            input_tokens=100,
            output_tokens=80,
            model="gemini-3.8-flash",
            provider="google_gemini",
            requested_model="gemini-3.8-flash",
            provider_failover_applied=False,
            primary_provider_error=None,
        )


def test_requested_and_actual_model_attribution_recorded_on_failover():
    service = TutorService(provider=FailoverHallucinatingProvider())
    req = TutorChatRequest(
        query="Explain diuretic mechanisms in renal physiology",
        question_id="UNI-RENAL-001",
    )
    res = service.chat(req, x_user_id="test_user")

    # Requested model must remain the originally configured primary model.
    assert res.requested_provider == "google_gemini"
    assert res.requested_model == "gemini-3.8-flash"

    # Actual generation model must reflect what really ran (post-failover), never the requested one.
    assert res.actual_generation_provider == "google_gemini"
    assert res.actual_generation_model == "gemini-3.5-flash"

    # Backward-compatible fields must reflect the ACTUAL model, not the requested one -
    # a fallback model must never silently masquerade as the primary.
    assert res.model == "gemini-3.5-flash"
    assert res.model != res.requested_model

    # Failover must be recorded explicitly, with the primary error preserved.
    assert res.provider_failover_applied is True
    assert res.primary_provider_error is not None
    assert "429" in res.primary_provider_error


def test_no_failover_case_requested_equals_actual():
    service = TutorService(provider=NoFailoverProvider())
    req = TutorChatRequest(
        query="In the renin-angiotensin pathway, what substrate does active renin cleave?",
        question_id="UNI-RENAL-001",
        mode="socratic_hint",
    )
    res = service.chat(req, x_user_id="test_user")

    assert res.provider_failover_applied is False
    assert res.primary_provider_error is None
    assert res.requested_model == res.actual_generation_model == "gemini-3.8-flash"
    assert res.model == "gemini-3.8-flash"


def test_rejected_draft_metrics_kept_separate_from_served_fallback_metrics():
    service = TutorService(provider=FailoverHallucinatingProvider())
    req = TutorChatRequest(
        query="Explain diuretic mechanisms in renal physiology",
        question_id="UNI-RENAL-001",
    )
    res = service.chat(req, x_user_id="test_user")

    # Fail-closed behavior is unchanged: unauthorized clinical content is never served.
    assert res.fallback_applied is True
    assert res.support_status == "SAFE_FALLBACK"
    assert "furosemide" not in res.message
    assert "100mg" not in res.message
    assert "cure" not in res.message.lower()

    # The REJECTED draft's own verification result must be preserved separately...
    assert res.draft_verification is not None
    assert res.draft_verification.veto_flags, "Rejected draft must carry the safety veto flags that caused rejection"

    # ...and must never be confused with what was actually served.
    served = res.verification
    assert served.veto_flags == [], "Served SAFE_FALLBACK content must carry zero veto flags of its own"
    assert served.unsupported_propositions == 0
    assert served.supported_propositions == 0
    assert served.total_propositions == served.non_factual_statements
    assert served.total_propositions > 0


def test_served_fallback_verification_is_recomputed_from_actual_served_text():
    """The served verification counts must match segmenting the ACTUAL fallback
    content that was returned to the learner, not stale counts from the rejected draft."""
    from medicalplab.tutor.claim_segmenter import PropositionSegmenter

    service = TutorService(provider=FailoverHallucinatingProvider())
    req = TutorChatRequest(
        query="Explain diuretic mechanisms in renal physiology",
        question_id="UNI-RENAL-001",
    )
    res = service.chat(req, x_user_id="test_user")

    # Independently re-segment the actual served fields and confirm the counts line up.
    segmenter = PropositionSegmenter()
    served_dict = {
        "message": res.message,
        "socratic_question": res.socratic_question,
        "hints": res.hints,
        "misconception": res.misconception,
        "mechanistic_explanation": res.mechanistic_explanation,
        "revision_summary": res.revision_summary,
    }
    recomputed_props = segmenter.segment_all_fields(served_dict)

    assert res.verification.total_propositions == len(recomputed_props)
    assert all(p.classification == "NON_FACTUAL_PEDAGOGICAL_LANGUAGE" for p in recomputed_props)

    # The rejected draft had a strictly larger/different footprint (its own message,
    # mechanistic_explanation, etc.) - served counts must not silently equal it by coincidence
    # of stale reuse. Confirm the draft's own total is tracked independently.
    assert res.draft_verification is not None
    assert res.draft_verification.total_propositions >= 1


def test_zero_unsupported_propositions_served_and_fail_closed_preserved():
    """Standing regression: the hard safety invariant is unaffected by the reporting fix."""
    service = TutorService(provider=FailoverHallucinatingProvider())
    req = TutorChatRequest(
        query="Explain diuretic mechanisms in renal physiology",
        question_id="UNI-RENAL-001",
    )
    res = service.chat(req, x_user_id="test_user")

    assert res.verification.unsupported_propositions == 0
    assert res.support_status != "PARTIALLY_SUPPORTED"
    assert res.abstain is False
    assert res.fallback_applied is True


def test_stub_provider_still_reports_consistent_requested_and_actual_model():
    """Baseline regression: the default StubGenerativeProvider (used throughout the rest
    of the Tutor test suite) must still populate the new attribution fields consistently."""
    service = TutorService(provider=StubGenerativeProvider())
    req = TutorChatRequest(
        query="In the renin-angiotensin pathway, what substrate does active renin cleave?",
        question_id="UNI-RENAL-001",
        mode="socratic_hint",
    )
    res = service.chat(req, x_user_id="test_student_01")

    assert res.provider_failover_applied is False
    assert res.primary_provider_error is None
    assert res.requested_model == res.actual_generation_model
    assert res.requested_provider == res.actual_generation_provider == "stub"


def test_forensic_capture_on_rejected_substantive_proposition():
    """Verify that when a generated substantive proposition is rejected/vetoed:
    - proposition_id is captured
    - generated proposition text or approved hash is captured
    - evidence document_id is captured
    - evidence chunk/passage identifier is captured
    - verifier/veto result is captured
    - requested model is captured
    - actual generation model is captured
    - provider failover state is captured
    - reached_learner = false
    """
    class PolarityVetoProvider:
        provider_name = "google_gemini"
        model_name = "gemini-3.8-flash"

        def generate_structured(self, system_prompt, user_prompt, response_schema, **kwargs):
            data = {
                "message": "Active renin does not cleave angiotensinogen in the circulation.",
                "socratic_question": "Why does renin fail to act upon its substrate?",
                "hints": ["Think about the cleavage of angiotensinogen."],
                "citations": [],
            }
            return ProviderResponse(
                raw_text=json.dumps(data),
                structured_data=data,
                input_tokens=150,
                output_tokens=60,
                model="gemini-3.5-flash",
                provider="google_gemini",
                requested_model="gemini-3.8-flash",
                provider_failover_applied=True,
                primary_provider_error="Gemini API (gemini-3.8-flash) error 429: Quota exceeded for model.",
            )

    service = TutorService(provider=PolarityVetoProvider())
    req = TutorChatRequest(
        query="In the renin-angiotensin pathway, what substrate does active renin cleave?",
        question_id="UNI-RENAL-001",
        mode="socratic_hint",
    )
    res = service.chat(req, x_user_id="test_user")

    # Safety invariant: rejected draft was NOT served
    assert res.fallback_applied is True
    assert res.support_status == "SAFE_FALLBACK"

    records = service.forensics.get_records()
    assert len(records) > 0

    # Locate the rejected substantive proposition record that triggered the veto
    vetoed_records = [r for r in records if "POLARITY_MISMATCH" in r.veto_flags]
    assert len(vetoed_records) >= 1
    record = vetoed_records[0]

    # Explicit check of the 9 forensic capture requirements:
    # 1. proposition_id is captured
    assert record.proposition_id is not None
    assert record.proposition_id.startswith("PROP-")

    # 2. generated proposition text or approved hash is captured
    assert record.proposition_text == "Active renin does not cleave angiotensinogen in the circulation"
    assert record.proposition_text_hash is not None and len(record.proposition_text_hash) == 16

    # 3. evidence document_id is captured
    assert record.evidence_document_id is not None
    assert record.evidence_document_id.startswith("DOC-")

    # 4. evidence chunk/passage identifier is captured
    assert record.evidence_chunk_id is not None
    assert record.evidence_document_id in record.evidence_chunk_id

    # 5. verifier/veto result is captured
    assert record.verifier_state == "CONTRADICTED"
    assert "POLARITY_MISMATCH" in record.veto_flags
    assert record.is_supported is False

    # 6. requested model is captured
    assert record.requested_model == "gemini-3.8-flash"

    # 7. actual generation model is captured
    assert record.actual_generation_model == "gemini-3.5-flash"

    # 8. provider failover state is captured
    assert record.provider_failover_applied is True

    # 9. reached_learner = false
    assert record.reached_learner is False
