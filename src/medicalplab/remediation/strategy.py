"""Socratic Strategy Engine for Medical Remediation.

Translates detected learning gaps into pedagogically tailored Socratic dialogue prompts
across the strict 3-turn lifecycle:
- Turn 1: PROBE (Neutrally probe the suspected gap)
- Turn 2: GUIDE (Provide scaffolded mechanistic guidance / clue)
- Turn 3: CONSOLIDATE (Consolidate reasoning and check readiness for independent assessment)

CRITICAL INVARIANT:
Turn 3 does NOT declare learning success or confirm concept mastery.
Only subsequent performance on an independent transfer item can supply transfer evidence.
"""
from __future__ import annotations

from typing import Tuple
from medicalplab.remediation.models import (
    DetectedLearningGap,
    ReasoningPatternCategory,
    SocraticStrategyType,
)


class SocraticStrategyEngine:
    """Generates structured pedagogical probes, guidance cues, and consolidation prompts."""

    def select_strategy(
        self,
        category: ReasoningPatternCategory,
        override_strategy: SocraticStrategyType | None = None,
    ) -> SocraticStrategyType:
        """Deterministically map a reasoning pattern category to a recommended strategy.

        Default initial strategy is GUIDED_RECALL, extensible for CONTRAST_CASE
        and STEPWISE_DECOMPOSITION.
        """
        if override_strategy:
            return override_strategy

        strategy_map = {
            ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION: SocraticStrategyType.CONTRAST_CASE,
            ReasoningPatternCategory.ENZYME_ROLE_INVERSION: SocraticStrategyType.STEPWISE_DECOMPOSITION,
            ReasoningPatternCategory.RECEPTOR_SPECIFICITY_CONFUSION: SocraticStrategyType.CONTRAST_CASE,
            ReasoningPatternCategory.PHYSIOLOGICAL_FEEDBACK_MISDIRECTION: SocraticStrategyType.COUNTEREXAMPLE_PROBE,
            ReasoningPatternCategory.ANATOMICAL_COMPARTMENT_CONFLATION: SocraticStrategyType.GUIDED_RECALL,
            ReasoningPatternCategory.CLINICAL_SYNDROME_OVERLAP: SocraticStrategyType.CONTRAST_CASE,
            ReasoningPatternCategory.GENERAL_CONCEPTUAL_GAP: SocraticStrategyType.GUIDED_RECALL,
        }
        return strategy_map.get(category, SocraticStrategyType.GUIDED_RECALL)

    def generate_turn_prompt(
        self,
        turn_number: int,
        strategy: SocraticStrategyType,
        gap: DetectedLearningGap,
        student_message: str | None = None,
    ) -> Tuple[str, str]:
        """Generate (pedagogical_intent, socratic_probe) for the given turn.

        Returns:
            Tuple[intent_description, socratic_probe_question]
        """
        if turn_number == 1:
            return self._build_turn1_probe(strategy, gap)
        elif turn_number == 2:
            return self._build_turn2_guide(strategy, gap, student_message)
        elif turn_number == 3:
            return self._build_turn3_consolidate(strategy, gap, student_message)
        else:
            raise ValueError(f"Socratic lifecycle strictly bounded to 3 turns; received turn {turn_number}")

    def _build_turn1_probe(
        self,
        strategy: SocraticStrategyType,
        gap: DetectedLearningGap,
    ) -> Tuple[str, str]:
        """Turn 1: Neutrally probe the suspected gap."""
        topic = gap.topic
        pattern = gap.reasoning_pattern

        if strategy == SocraticStrategyType.CONTRAST_CASE:
            if gap.category == ReasoningPatternCategory.RECEPTOR_SPECIFICITY_CONFUSION:
                intent = f"Probe distinction between signaling effector and target receptor in {topic}."
                probe = (
                    f"Consider the signaling cascade in {topic}. "
                    "What is the key physiological distinction between the circulating effector peptide and its specific target receptor?"
                )
            else:
                intent = f"Challenge distinction in {topic} regarding {pattern} using comparative contrast."
                probe = (
                    f"Consider how the components in {topic} interact. "
                    "What is the key physiological distinction between the upstream stimulus and the downstream product?"
                )
        elif strategy == SocraticStrategyType.STEPWISE_DECOMPOSITION:
            intent = f"Decompose chronological cascade of {topic} to highlight step order."
            probe = (
                f"In the physiological cascade for {topic}, what is the very first biochemical event, "
                "and what specific substrate must be present before any downstream conversion can occur?"
            )
        elif strategy == SocraticStrategyType.COUNTEREXAMPLE_PROBE:
            intent = f"Present physiological counterexample challenging {pattern}."
            probe = (
                f"If the mechanism operated as described in your selection, what contradictory physiological "
                f"outcome would occur in {topic}, and why does normal homeostasis prevent that?"
            )
        else:  # GUIDED_RECALL (Default)
            intent = f"Scaffold foundational anatomical/biochemical recall for {topic}."
            probe = (
                f"Before considering the entire mechanism, what is the primary anatomical structure "
                f"or cell lineage responsible for this function in {topic}?"
            )

        return intent, probe

    def _build_turn2_guide(
        self,
        strategy: SocraticStrategyType,
        gap: DetectedLearningGap,
        student_message: str | None,
    ) -> Tuple[str, str]:
        """Turn 2: Provide grounded mechanistic clue / guidance."""
        topic = gap.topic

        if strategy == SocraticStrategyType.CONTRAST_CASE:
            if gap.category == ReasoningPatternCategory.RECEPTOR_SPECIFICITY_CONFUSION:
                intent = f"Provide mechanistic clue on receptor specificity within {topic}."
                probe = (
                    "Notice how physiological actions are mediated at the cellular level. "
                    "How does the effector peptide specifically bind its target receptor to initiate the classical pathway response?"
                )
            else:
                intent = f"Provide mechanistic clue contrasting the specific roles within {topic}."
                probe = (
                    "Notice the specific role each molecule plays. "
                    "How does the upstream enzyme prepare the substrate for the subsequent step?"
                )
        elif strategy == SocraticStrategyType.STEPWISE_DECOMPOSITION:
            intent = f"Scaffold the intermediate conversion stage within {topic}."
            probe = (
                "You are tracking the cascade. "
                "Now, what happens immediately after the initial cleavage, and where does that reaction take place?"
            )
        elif strategy == SocraticStrategyType.COUNTEREXAMPLE_PROBE:
            intent = f"Clarify the regulatory barrier or feedback loop in {topic}."
            probe = (
                "Reflecting on that consequence: "
                "How does the physiological barrier actively preserve balance rather than permitting unregulated passage?"
            )
        else:  # GUIDED_RECALL
            intent = f"Connect foundational structure to the physiological mechanism in {topic}."
            probe = (
                "With that structural foundation identified: "
                "How does this specific cellular feature enable the selective physiological response?"
            )

        return intent, probe

    def _build_turn3_consolidate(
        self,
        strategy: SocraticStrategyType,
        gap: DetectedLearningGap,
        student_message: str | None,
    ) -> Tuple[str, str]:
        """Turn 3: Consolidate reasoning and check readiness for independent assessment."""
        topic = gap.topic

        intent = f"Consolidate reasoning and check readiness for independent assessment in {topic}."
        probe = (
            f"Putting it together before your independent assessment: In your own words, what is the key physiological principle for {topic}, "
            "and how does that clarify your original option choice?"
        )

        return intent, probe
