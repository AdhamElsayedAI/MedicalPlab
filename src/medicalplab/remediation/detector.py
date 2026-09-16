"""Reasoning Pattern and Learning Gap Detection Engine.

Analyzes learner submissions and identifies the underlying cognitive reasoning pattern
leading to the distractor choice.

MANDATORY BEHAVIOR:
- Deterministic matching using verified taxonomy mappings.
- Epistemic uncertainty: returns a structured PatternHypothesis (POSSIBLE_PATTERN vs INSUFFICIENT_EVIDENCE).
- Single observed distractor supports POSSIBLE_PATTERN, never CONFIRMED_PATTERN.
- CONFIRMED_PATTERN requires independent multi-attempt corroboration (unreachable in MVP).
- Safe fail-closed abstention for unmapped or ambiguous distractors (INSUFFICIENT_EVIDENCE).
- Zero ungrounded LLM guessing of medical misconceptions.
"""
from __future__ import annotations

import logging
from typing import Optional
import uuid

from medicalplab.remediation.models import (
    DetectionStatus,
    DetectedLearningGap,
    EpistemicType,
    EvidenceStrength,
    PatternHypothesis,
    ReasoningPatternCategory,
    SocraticStrategyType,
)
from medicalplab.remediation.taxonomy import (
    ReasoningPatternTaxonomyRegistry,
    get_taxonomy_registry,
)

logger = logging.getLogger(__name__)

DEFAULT_MIN_CONFIDENCE = 0.65


class ReasoningPatternDetectionEngine:
    """Detects learning gaps and flawed mental models from question attempt data."""

    def __init__(
        self,
        registry: ReasoningPatternTaxonomyRegistry | None = None,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ) -> None:
        self.registry = registry or get_taxonomy_registry()
        self.min_confidence = min_confidence

    def detect_hypothesis(
        self,
        question_id: str,
        selected_option: str,
        topic: Optional[str] = None,
        attempt_id: Optional[str] = None,
    ) -> PatternHypothesis:
        """Deterministically derive an explainable PatternHypothesis from structured signals."""
        mapping = self.registry.get_mapping(question_id, selected_option)
        resolved_topic = topic or "Clinical Physiology"

        if mapping and mapping.confidence_weight >= self.min_confidence:
            pattern = self.registry.get_pattern(mapping.pattern_id)
            if pattern:
                logger.info(
                    "Detected candidate reasoning pattern %s for %s[%s] (weight=%.2f)",
                    pattern.pattern_id,
                    question_id,
                    selected_option,
                    mapping.confidence_weight,
                )
                strength = (
                    EvidenceStrength.STRONG
                    if mapping.confidence_weight >= 0.90
                    else EvidenceStrength.MODERATE
                )
                signal_desc = f"Observed distractor option '{selected_option}' for question '{question_id}'"
                if attempt_id:
                    signal_desc += f" (attempt={attempt_id})"

                # Single attempt yields POSSIBLE_PATTERN, NEVER CONFIRMED_PATTERN
                return PatternHypothesis(
                    hypothesis_id=f"HYP-{uuid.uuid4().hex[:10].upper()}",
                    epistemic_type=EpistemicType.HYPOTHESIS,
                    detection_status=DetectionStatus.POSSIBLE_PATTERN,
                    category=pattern.category,
                    pattern_id=pattern.pattern_id,
                    candidate_pattern=pattern.reasoning_pattern,
                    evidence_strength=strength,
                    detection_rationale=mapping.detection_rationale,
                    rule_version=mapping.rule_version,
                    taxonomy_version=pattern.version,
                    supporting_signals=[signal_desc],
                    ambiguity_reason=None,
                    is_fallback=False,
                )
            else:
                logger.warning(
                    "Mapping references non-existent pattern %s for %s",
                    mapping.pattern_id,
                    question_id,
                )

        # Unmapped or sub-threshold: Mandatory abstention to INSUFFICIENT_EVIDENCE
        logger.info(
            "Unmapped or sub-threshold distractor %s[%s]; abstaining to INSUFFICIENT_EVIDENCE",
            question_id,
            selected_option,
        )
        return PatternHypothesis(
            hypothesis_id=f"HYP-{uuid.uuid4().hex[:10].upper()}",
            epistemic_type=EpistemicType.HYPOTHESIS,
            detection_status=DetectionStatus.INSUFFICIENT_EVIDENCE,
            category=ReasoningPatternCategory.GENERAL_CONCEPTUAL_GAP,
            pattern_id="PATTERN-GEN-FALLBACK",
            candidate_pattern=f"General conceptual gap in {resolved_topic}",
            evidence_strength=EvidenceStrength.LOW,
            detection_rationale=(
                f"Distractor choice '{selected_option}' does not match a verified pattern rule. "
                "Abstaining from pattern detection; engaging neutral procedural guidance."
            ),
            rule_version="1.0.0",
            taxonomy_version="1.0.0",
            supporting_signals=[f"Distractor choice '{selected_option}' on question '{question_id}'"],
            ambiguity_reason="No verified taxonomy mapping for distractor choice",
            is_fallback=True,
        )

    def detect(
        self,
        question_id: str,
        selected_option: str,
        topic: Optional[str] = None,
        attempt_id: Optional[str] = None,
    ) -> DetectedLearningGap:
        """Detect the reasoning pattern behind an incorrect option choice.

        Returns a verified `DetectedLearningGap` encapsulating the `PatternHypothesis`.
        """
        hyp = self.detect_hypothesis(
            question_id=question_id,
            selected_option=selected_option,
            topic=topic,
            attempt_id=attempt_id,
        )
        resolved_topic = topic or "Clinical Physiology"

        if not hyp.is_fallback:
            pattern = self.registry.get_pattern(hyp.pattern_id)
            ev_refs = pattern.evidence_references if pattern else []
            strat = pattern.recommended_strategy if pattern else SocraticStrategyType.GUIDED_RECALL
            return DetectedLearningGap(
                pattern_id=hyp.pattern_id,
                topic=pattern.topic if pattern else resolved_topic,
                category=hyp.category,
                reasoning_pattern=hyp.candidate_pattern,
                recommended_strategy=strat,
                confidence=0.85 if hyp.evidence_strength == EvidenceStrength.STRONG else 0.70,
                detection_rationale=hyp.detection_rationale,
                evidence_references=ev_refs,
                is_fallback=False,
                hypothesis=hyp,
            )

        return DetectedLearningGap(
            pattern_id="PATTERN-GEN-FALLBACK",
            topic=resolved_topic,
            category=ReasoningPatternCategory.GENERAL_CONCEPTUAL_GAP,
            reasoning_pattern=hyp.candidate_pattern,
            recommended_strategy=SocraticStrategyType.GUIDED_RECALL,
            confidence=0.50,
            detection_rationale=hyp.detection_rationale,
            evidence_references=[],
            is_fallback=True,
            hypothesis=hyp,
        )
