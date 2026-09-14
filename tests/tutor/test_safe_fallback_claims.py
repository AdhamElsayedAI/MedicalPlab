"""
Regression tests for the PHASE 1 SAFE_FALLBACK claim-classification safety fix.

Background (see PHASE_1_PRE_LIVE_AUDIT / PHASE_1_FALLBACK_SAFETY_FIX):
`_build_safe_fallback` is served with zero citations, so it can never satisfy
SUPPORTED_BY_EVIDENCE. The hard invariant therefore requires the fallback
template to contain ZERO substantive medical/basic-science factual claims of
its own - every sentence must be legitimately non-factual/procedural.

Verifies:
1. The rewritten SAFE_FALLBACK template (PRE_SUBMISSION / GENERAL_STUDY) contains
   zero SUBSTANTIVE_FACTUAL propositions.
2. Running the rewritten fallback through the full segment + verify pipeline
   reports supported_propositions == 0 and unsupported_propositions == 0, with
   every proposition legitimately NON_FACTUAL_PEDAGOGICAL_LANGUAGE.
3. A standing guard that fails if any future SAFE_FALLBACK template edit
   introduces an unverifiable substantive claim.
"""
from __future__ import annotations

from medicalplab.tutor.claim_segmenter import PropositionSegmenter
from medicalplab.tutor.service import TutorService
from medicalplab.tutor.verifier import TutorPostVerifier


def _fallback_drafts() -> dict[str, dict]:
    service = TutorService()
    return {
        "PRE_SUBMISSION": service._build_safe_fallback(
            state="PRE_SUBMISSION",
            question=None,
            topic="Renal Physiology",
            query="irrelevant",
            reason="TEST",
        ),
        "GENERAL_STUDY": service._build_safe_fallback(
            state="GENERAL_STUDY",
            question=None,
            topic="Renal Physiology",
            query="irrelevant",
            reason="TEST",
        ),
    }


def test_safe_fallback_carries_zero_citations():
    # A response with zero citations can never satisfy SUPPORTED_BY_EVIDENCE, which is
    # exactly why the fallback template must never assert a substantive medical claim.
    for state, draft in _fallback_drafts().items():
        assert draft["citations"] == [], f"{state} fallback must carry zero citations"


def test_rewritten_safe_fallback_contains_zero_substantive_propositions():
    segmenter = PropositionSegmenter()
    for state, draft in _fallback_drafts().items():
        props = segmenter.segment_all_fields(draft)
        assert len(props) > 0, f"{state} fallback produced no propositions to check"

        substantive = [p for p in props if p.classification == "SUBSTANTIVE_FACTUAL"]
        assert substantive == [], (
            f"{state} SAFE_FALLBACK must contain zero substantive medical/basic-science "
            f"claims (it is served with zero citations and can never be evidence-verified). "
            f"Found: {[p.text for p in substantive]}"
        )
        assert all(p.classification == "NON_FACTUAL_PEDAGOGICAL_LANGUAGE" for p in props)


def test_safe_fallback_verification_reports_zero_supported_zero_unsupported():
    segmenter = PropositionSegmenter()
    verifier = TutorPostVerifier()

    for state, draft in _fallback_drafts().items():
        props = segmenter.segment_all_fields(draft)
        summary, all_supported = verifier.verify_propositions(props, candidates=[])

        assert all_supported is True
        assert summary.supported_propositions == 0
        assert summary.unsupported_propositions == 0
        assert summary.total_propositions > 0
        assert summary.non_factual_statements == summary.total_propositions


def test_standing_guard_safe_fallback_never_introduces_unverifiable_substantive_claim():
    """Standing guard: fails the build if a future SAFE_FALLBACK template edit introduces
    a substantive factual proposition. The fallback path never attaches citations, so any
    substantive claim it contains can never legitimately resolve to SUPPORTED_BY_EVIDENCE."""
    segmenter = PropositionSegmenter()
    verifier = TutorPostVerifier()

    for state, draft in _fallback_drafts().items():
        assert not draft.get("citations"), (
            f"{state} SAFE_FALLBACK unexpectedly carries citations; the zero-evidence "
            "assumption behind this guard no longer holds and must be re-audited."
        )
        props = segmenter.segment_all_fields(draft)
        _, all_supported = verifier.verify_propositions(props, candidates=[])
        assert all_supported, (
            f"{state} SAFE_FALLBACK now contains an unverifiable substantive claim. "
            "Rewrite the template to remove the declarative medical/basic-science "
            "assertion, or attach a verified citation - see PHASE_1 pre-live audit."
        )
