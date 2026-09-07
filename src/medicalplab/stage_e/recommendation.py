"""Deterministic and explainable recommendation engine for Stage-E.

Translates student mastery metrics, knowledge gaps, and curriculum taxonomy into
actionable, prioritized educational directives with explicit statistical justifications.
"""

from typing import Sequence

from medicalplab.stage_b.models import require
from .knowledge_graph import get_prerequisites, get_related_topics
from .models import (
    KnowledgeGap,
    LearningRecommendation,
    MasteryLevel,
    QuestionDifficulty,
    RecommendationPriority,
    StudentProfile,
    TopicMastery,
)


def generate_recommendations(
    profile: StudentProfile,
    knowledge_gaps: Sequence[KnowledgeGap],
) -> tuple[LearningRecommendation, ...]:
    """Generate prioritized, explainable learning recommendations deterministically."""
    require(isinstance(profile, StudentProfile), "profile must be a StudentProfile instance")
    require(
        isinstance(knowledge_gaps, (list, tuple)),
        "knowledge_gaps must be a sequence of KnowledgeGap",
    )
    for g in knowledge_gaps:
        require(isinstance(g, KnowledgeGap), "Items must be KnowledgeGap instances")

    recommendations: list[LearningRecommendation] = []
    handled_topics: set[str] = set()

    # 1. High Priority: Address identified knowledge gaps / weak topics
    for gap in knowledge_gaps:
        topic_clean = gap.topic.strip()
        handled_topics.add(topic_clean.lower())

        prereqs = get_prerequisites(topic_clean)
        prereq_note = (
            f" Ensure core foundational grasp of {', '.join(prereqs)}."
            if prereqs else ""
        )

        # Match mastery for target difficulty calibration
        matched_mastery = next(
            (m for m in profile.mastery_scores if m.topic.strip().lower() == topic_clean.lower()),
            None,
        )
        target_diff = "easy" if (matched_mastery and matched_mastery.accuracy < 0.40) else "medium"

        action = (
            f"Review {topic_clean} guidelines in Stage-D Teaching mode "
            f"and practice {target_diff} questions in Stage-C.{prereq_note}"
        )

        recommendations.append(
            LearningRecommendation(
                topic=topic_clean,
                priority=RecommendationPriority.HIGH,
                reason=gap.reason,
                recommended_action=action,
                target_difficulty=target_diff,
            )
        )

    # 2. Medium Priority: Developing topics needing reinforcement
    for m in profile.mastery_scores:
        key = m.topic.strip().lower()
        if key in handled_topics or m.total_attempts == 0:
            continue

        if m.mastery_level == MasteryLevel.DEVELOPING:
            handled_topics.add(key)
            acc_pct = int(round(m.accuracy * 100))
            reason = (
                f"The student is developing competency in {m.topic} with {acc_pct}% accuracy "
                f"across {m.total_attempts} attempts."
            )
            action = (
                f"Reinforce {m.topic} concepts with medium-difficulty Stage-C practice "
                f"and targeted Stage-D question reviews."
            )
            recommendations.append(
                LearningRecommendation(
                    topic=m.topic,
                    priority=RecommendationPriority.MEDIUM,
                    reason=reason,
                    recommended_action=action,
                    target_difficulty="medium",
                )
            )

    # 3. Low Priority: Proficient or Advanced topics for advancement
    for m in profile.mastery_scores:
        key = m.topic.strip().lower()
        if key in handled_topics or m.total_attempts == 0:
            continue

        if m.mastery_level in (MasteryLevel.PROFICIENT, MasteryLevel.ADVANCED):
            handled_topics.add(key)
            acc_pct = int(round(m.accuracy * 100))
            related = get_related_topics(m.topic)
            progression_note = (
                f" Consider progressing to related topics: {', '.join(related)}."
                if related else ""
            )
            reason = (
                f"The student demonstrates strong proficiency in {m.topic} ({acc_pct}% accuracy "
                f"across {m.total_attempts} attempts)."
            )
            action = (
                f"Increase difficulty level for {m.topic} questions and advance to Stage-D "
                f"Case Discussion clinical vignettes.{progression_note}"
            )
            recommendations.append(
                LearningRecommendation(
                    topic=m.topic,
                    priority=RecommendationPriority.LOW,
                    reason=reason,
                    recommended_action=action,
                    target_difficulty="hard",
                )
            )

    # Sort recommendations deterministically: HIGH -> MEDIUM -> LOW
    priority_order = {
        RecommendationPriority.HIGH: 0,
        RecommendationPriority.MEDIUM: 1,
        RecommendationPriority.LOW: 2,
    }
    recommendations.sort(key=lambda r: priority_order[r.priority])

    return tuple(recommendations)


def compile_next_learning_actions(
    recommendations: Sequence[LearningRecommendation],
    max_actions: int = 5,
) -> tuple[str, ...]:
    """Compile the top immediate action items from recommendations."""
    actions = [f"[{r.priority.value.upper()}] {r.recommended_action}" for r in recommendations]
    return tuple(actions[:max_actions])
