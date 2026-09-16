"""Tests for Reasoning Pattern Detection Engine and Epistemic Hypotheses."""
import pytest
from medicalplab.remediation.detector import ReasoningPatternDetectionEngine
from medicalplab.remediation.models import (
    DetectionStatus,
    DetectedLearningGap,
    EpistemicType,
    EvidenceStrength,
    ReasoningPatternCategory,
    SocraticStrategyType,
)


def test_detector_identifies_known_distractor_as_possible_pattern():
    detector = ReasoningPatternDetectionEngine()

    hyp = detector.detect_hypothesis(
        question_id="UNI-RENAL-001",
        selected_option="B",
        topic="RAAS mechanisms",
        attempt_id="ATTEMPT-001",
    )

    # Must be HYPOTHESIS epistemic type
    assert hyp.epistemic_type == EpistemicType.HYPOTHESIS
    # Single distractor MUST be POSSIBLE_PATTERN, NEVER CONFIRMED_PATTERN
    assert hyp.detection_status == DetectionStatus.POSSIBLE_PATTERN
    assert hyp.pattern_id == "PATTERN-RAAS-SUB-01"
    assert hyp.category == ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION
    assert hyp.evidence_strength in (EvidenceStrength.STRONG, EvidenceStrength.MODERATE)
    assert hyp.is_fallback is False
    assert len(hyp.supporting_signals) > 0
    assert "ATTEMPT-001" in hyp.supporting_signals[0]


def test_detector_abstention_for_unmapped_distractor():
    """Unmapped distractor must produce INSUFFICIENT_EVIDENCE abstention without guessing."""
    detector = ReasoningPatternDetectionEngine()

    hyp = detector.detect_hypothesis(
        question_id="UNKNOWN-Q-999",
        selected_option="E",
        topic="Renal physiology",
    )

    assert hyp.epistemic_type == EpistemicType.HYPOTHESIS
    assert hyp.detection_status == DetectionStatus.INSUFFICIENT_EVIDENCE
    assert hyp.pattern_id == "PATTERN-GEN-FALLBACK"
    assert hyp.category == ReasoningPatternCategory.GENERAL_CONCEPTUAL_GAP
    assert hyp.evidence_strength == EvidenceStrength.LOW
    assert hyp.is_fallback is True
    assert hyp.ambiguity_reason is not None
    assert "Abstaining" in hyp.detection_rationale


def test_detector_legacy_detect_wrapper():
    detector = ReasoningPatternDetectionEngine()

    gap = detector.detect(
        question_id="UNI-RENAL-002",
        selected_option="A",
        topic="RAAS mechanisms",
    )

    assert isinstance(gap, DetectedLearningGap)
    assert gap.pattern_id == "PATTERN-RAAS-ENZ-01"
    assert gap.category == ReasoningPatternCategory.ENZYME_ROLE_INVERSION
    assert gap.recommended_strategy == SocraticStrategyType.STEPWISE_DECOMPOSITION
    assert gap.is_fallback is False
    assert gap.hypothesis is not None
    assert gap.hypothesis.detection_status == DetectionStatus.POSSIBLE_PATTERN
