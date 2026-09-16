"""Tests for Socratic Strategy Engine."""
import pytest
from medicalplab.remediation.models import (
    DetectedLearningGap,
    ReasoningPatternCategory,
    SocraticStrategyType,
)
from medicalplab.remediation.strategy import SocraticStrategyEngine


def test_strategy_selection_mapping():
    engine = SocraticStrategyEngine()

    assert (
        engine.select_strategy(ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION)
        == SocraticStrategyType.CONTRAST_CASE
    )
    assert (
        engine.select_strategy(ReasoningPatternCategory.ENZYME_ROLE_INVERSION)
        == SocraticStrategyType.STEPWISE_DECOMPOSITION
    )
    assert (
        engine.select_strategy(ReasoningPatternCategory.PHYSIOLOGICAL_FEEDBACK_MISDIRECTION)
        == SocraticStrategyType.COUNTEREXAMPLE_PROBE
    )
    assert (
        engine.select_strategy(ReasoningPatternCategory.ANATOMICAL_COMPARTMENT_CONFLATION)
        == SocraticStrategyType.GUIDED_RECALL
    )
    # Default initial strategy must be GUIDED_RECALL
    assert (
        engine.select_strategy(ReasoningPatternCategory.GENERAL_CONCEPTUAL_GAP)
        == SocraticStrategyType.GUIDED_RECALL
    )


def test_three_turn_prompt_generation():
    engine = SocraticStrategyEngine()
    gap = DetectedLearningGap(
        pattern_id="PATTERN-RAAS-SUB-01",
        topic="RAAS mechanisms",
        category=ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION,
        reasoning_pattern="Substrate versus product role inversion in enzymatic cascade",
        recommended_strategy=SocraticStrategyType.CONTRAST_CASE,
        confidence=0.95,
        detection_rationale="Selected Angiotensin II instead of Angiotensinogen",
        evidence_references=["DOC-PMC-RENAL-0001:DOC-PMC-RENAL-0001-B0003-C01"],
    )

    # Turn 1: PROBE
    intent1, probe1 = engine.generate_turn_prompt(1, SocraticStrategyType.CONTRAST_CASE, gap)
    assert "Challenge" in intent1 or "contrast" in intent1.lower()
    assert "RAAS mechanisms" in probe1
    assert "?" in probe1

    # Turn 2: GUIDE
    intent2, probe2 = engine.generate_turn_prompt(
        2, SocraticStrategyType.CONTRAST_CASE, gap, student_message="Renin is an enzyme"
    )
    assert "clue" in intent2.lower() or "mechanistic" in intent2.lower()
    assert "?" in probe2

    # Turn 3: CONSOLIDATE & CHECK READINESS
    intent3, probe3 = engine.generate_turn_prompt(
        3, SocraticStrategyType.CONTRAST_CASE, gap, student_message="It acts on angiotensinogen"
    )
    assert "consolidate" in intent3.lower() or "readiness" in intent3.lower()
    assert "In your own words" in probe3 or "assessment" in probe3.lower()


def test_turn_bound_rejection():
    """Any attempt beyond Turn 3 must raise ValueError."""
    engine = SocraticStrategyEngine()
    gap = DetectedLearningGap(
        pattern_id="PATTERN-RAAS-SUB-01",
        topic="RAAS mechanisms",
        category=ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION,
        reasoning_pattern="Substrate versus product role inversion",
        recommended_strategy=SocraticStrategyType.CONTRAST_CASE,
        confidence=0.95,
        detection_rationale="Selected Angiotensin II",
    )

    with pytest.raises(ValueError) as exc:
        engine.generate_turn_prompt(4, SocraticStrategyType.CONTRAST_CASE, gap)
    assert "strictly bounded to 3 turns" in str(exc.value)
