"""
Unit tests for proposition extraction, classification, and claim coverage.

Verifies:
1. Extraction across all tutor draft fields (socratic_question, hints, mechanistic_explanation, next_step, distractors).
2. Distinction between substantive medical/physiological propositions and non-factual pedagogical framing.
3. extract_declarative_core accurately isolates verifiable medical assertions from interrogative and imperative syntax.
"""

from medicalplab.tutor.claim_segmenter import PropositionSegmenter
from medicalplab.tutor.models import TutorDraftOutput


def test_segmenter_extracts_from_all_fields():
    segmenter = PropositionSegmenter()
    draft = TutorDraftOutput(
        message="Let's analyze this physiological mechanism.",
        socratic_question="Why does constriction of the efferent arteriole increase glomerular hydrostatic pressure?",
        hints=["Consider the hydraulic resistance downstream of the glomerular capillary bed."],
        mechanistic_explanation="Efferent arteriolar vasoconstriction increases resistance to outflow, raising capillary hydrostatic pressure.",
        distractor_analysis=[
            {
                "option": "A",
                "text": "Afferent arteriole constriction",
                "why_incorrect": "Afferent arteriole constriction would reduce capillary pressure, not increase it.",
                "supported_by_ref": "E1",
            }
        ],
        revision_summary="Glomerular filtration depends on Starling forces.",
    )

    propositions = segmenter.extract_propositions(draft)
    assert len(propositions) >= 4

    fields_represented = {p.source_field for p in propositions}
    assert "message" in fields_represented
    assert "socratic_question" in fields_represented
    assert "hints" in fields_represented
    assert "mechanistic_explanation" in fields_represented
    assert "distractor_analysis" in fields_represented
    assert "revision_summary" in fields_represented


def test_segmenter_separates_factual_from_non_factual():
    segmenter = PropositionSegmenter()

    # Pure conversational encouragements or generic meta-statements without physiological claims
    non_factual_statements = [
        "Great work on that question!",
        "Let us explore this concept step by step.",
        "Hello learner, welcome.",
        "What do you think?",
    ]

    for stmt in non_factual_statements:
        props = segmenter.segment_field("greeting", stmt)
        for p in props:
            assert p.classification == "NON_FACTUAL_PEDAGOGICAL_LANGUAGE", (
                f"Expected non-factual claim for '{stmt}', got: {p.classification}"
            )

    # Assertive physiological statements
    factual_statements = [
        "Renin is synthesized and stored in the juxtaglomerular cells.",
        "Angiotensin II acts on AT1 receptors to stimulate aldosterone release.",
        "Podocyte foot processes form filtration slits bridged by nephrin.",
    ]

    for stmt in factual_statements:
        props = segmenter.segment_field("explanation", stmt)
        assert len(props) >= 1
        assert any(p.classification == "SUBSTANTIVE_FACTUAL" for p in props), (
            f"Expected substantive factual claim for '{stmt}'"
        )


def test_extract_declarative_core():
    segmenter = PropositionSegmenter()

    interrogative = "How does active renin cleave angiotensinogen to generate angiotensin I in plasma?"
    core = segmenter.extract_declarative_core(interrogative)
    assert "angiotensinogen" in core.lower() or "renin" in core.lower()

    imperative = "Think about how podocyte foot processes form filtration slits bridged by nephrin."
    core_imp = segmenter.extract_declarative_core(imperative)
    assert "podocyte foot processes form filtration slits" in core_imp.lower()


def test_classifier_detects_generic_but_substantive_physiological_claims():
    """PHASE_1 pre-live audit regression: a sentence must not be classified
    NON_FACTUAL_PEDAGOGICAL_LANGUAGE merely because it is generic or Socratic.
    These two exact sentences were found embedded in the old SAFE_FALLBACK
    template and were incorrectly treated as non-factual."""
    segmenter = PropositionSegmenter()

    generic_claim = "Renal Physiology operates via tightly regulated feedback mechanisms."
    props = segmenter.segment_field("revision_summary", generic_claim)
    assert len(props) == 1
    assert props[0].classification == "SUBSTANTIVE_FACTUAL"

    socratic_hint = (
        "Consider how renal hemodynamics, cellular barriers, and biochemical "
        "pathways interact in this setting."
    )
    props2 = segmenter.segment_field("message", socratic_hint)
    assert len(props2) == 1
    assert props2[0].classification == "SUBSTANTIVE_FACTUAL"


def test_classifier_recognizes_plural_and_inflected_medical_terms():
    """Plural forms (e.g. 'barriers' vs the stored keyword 'barrier') and inflected
    mechanistic verb forms (regulated, interacted, increased, maintained, etc.) must
    be recognized, not just their bare singular/present-tense forms."""
    segmenter = PropositionSegmenter()

    # Plural noun form of a known keyword, with no other keyword present.
    plural_stmt = "The cellular barriers restrict passage of large plasma proteins."
    props = segmenter.segment_field("mechanistic_explanation", plural_stmt)
    assert any(p.classification == "SUBSTANTIVE_FACTUAL" for p in props), plural_stmt

    # Inflected mechanistic verb forms, several with no PHYSIOLOGICAL_KEYWORDS term present.
    inflected_statements = [
        "Aldosterone release is regulated by circulating potassium.",
        "The two systems interacted to maintain a stable internal state.",
        "Renal blood flow increased sharply after the intervention.",
        "Tubular sodium reabsorption is maintained across a range of pressures.",
    ]
    for stmt in inflected_statements:
        props = segmenter.segment_field("mechanistic_explanation", stmt)
        assert any(p.classification == "SUBSTANTIVE_FACTUAL" for p in props), (
            f"Expected substantive classification for inflected verb form in: {stmt!r}"
        )


def test_factual_premise_inside_socratic_question_or_hint_is_still_substantive():
    """A question mark, or 'Consider'/'Level N:' hint framing, must not exempt an
    embedded physiological assertion from verification."""
    segmenter = PropositionSegmenter()

    question_with_premise = (
        "Given that increased angiotensin II stimulates aldosterone release, "
        "what happens to serum potassium?"
    )
    props = segmenter.segment_field("socratic_question", question_with_premise)
    assert any(p.classification == "SUBSTANTIVE_FACTUAL" for p in props)

    hint_with_premise = (
        "Level 2: Recall that angiotensin II directly stimulates aldosterone "
        "secretion from the adrenal cortex."
    )
    props2 = segmenter.segment_field("hints", [hint_with_premise])
    assert any(p.classification == "SUBSTANTIVE_FACTUAL" for p in props2)

    # A genuinely open, content-free Socratic question with no embedded claim
    # (the current SAFE_FALLBACK socratic_question) legitimately remains non-factual.
    open_question = "What do you already know that might help you approach this question?"
    props3 = segmenter.segment_field("socratic_question", open_question)
    assert all(p.classification == "NON_FACTUAL_PEDAGOGICAL_LANGUAGE" for p in props3)


def test_empty_and_whitespace_fields_handled_safely():
    segmenter = PropositionSegmenter()
    draft = TutorDraftOutput(
        message="Juxtaglomerular cells secrete renin.",
        socratic_question="   ",
        hints=[],
        mechanistic_explanation="   \n\t ",
        distractor_analysis=[],
        revision_summary=None,
    )

    propositions = segmenter.extract_propositions(draft)
    assert len(propositions) >= 1
    assert all(p.text.strip() != "" for p in propositions)
