"""Adaptive Decision Engine for Phase 2A Adaptive Learning.

Evaluates learner state and identified weaknesses to select the next best
evidence-grounded educational intervention.
"""
from __future__ import annotations

import uuid
from typing import Any, Mapping, Sequence
from .models import (
    AdaptiveActionType,
    AdaptiveRecommendation,
    TopicMasteryRecord,
    WeakTopicRecord,
    WeaknessPriority,
)


class AdaptiveDecisionEngine:
    """Selects targeted pedagogical actions based on mastery gaps and question bank availability."""

    def __init__(self, consecutive_error_threshold_for_tutor: int = 2) -> None:
        self.tutor_error_threshold = consecutive_error_threshold_for_tutor

    def select_recommendations(
        self,
        weak_topics: Sequence[WeakTopicRecord],
        topic_masteries: Mapping[str, TopicMasteryRecord],
        available_questions: Sequence[dict[str, Any]] | None = None,
        attempted_question_ids: set[str] | None = None,
    ) -> list[AdaptiveRecommendation]:
        """Generate an ordered list of actionable recommendations for the learner."""
        questions = available_questions or []
        attempted_ids = attempted_question_ids or set()
        recommendations: list[AdaptiveRecommendation] = []

        # 1. Address identified weak topics first
        if weak_topics:
            for weak in weak_topics:
                # Find unattempted questions for this weak topic
                topic_questions = [
                    q for q in questions
                    if q.get("topic", "").strip().lower() == weak.topic.strip().lower()
                ]
                unattempted = [q for q in topic_questions if q.get("id") not in attempted_ids]

                # If high priority with repeated errors, prioritize Grounded Tutor intervention
                if (
                    weak.priority == WeaknessPriority.HIGH
                    or weak.consecutive_errors >= self.tutor_error_threshold
                    or weak.failure_rate >= 0.70
                ):
                    rec_id = f"REC-TUTOR-{uuid.uuid4().hex[:6].upper()}"
                    target_q = unattempted[0]["id"] if unattempted else (topic_questions[0]["id"] if topic_questions else None)
                    recommendations.append(
                        AdaptiveRecommendation(
                            recommendation_id=rec_id,
                            action=AdaptiveActionType.ASK_GROUNDED_TUTOR,
                            subject=weak.subject,
                            topic=weak.topic,
                            priority=weak.priority,
                            target_question_id=target_q,
                            tutor_mode="socratic_hint",
                            tutor_query=f"Can you guide me step-by-step through the core physiological mechanism of {weak.topic}?",
                            reason=f"Repeated errors detected in {weak.topic} ({weak.consecutive_errors} consecutive misses).",
                            explanation=(
                                f"MedicalPlab detected that you struggled with {weak.topic}. "
                                "Instead of guessing again, a Socratic dialogue will guide you through the underlying physiological mechanism."
                            ),
                        )
                    )

                # Next: offer targeted question practice if questions remain
                elif unattempted:
                    target_q = unattempted[0]
                    rec_id = f"REC-Q-{uuid.uuid4().hex[:6].upper()}"
                    recommendations.append(
                        AdaptiveRecommendation(
                            recommendation_id=rec_id,
                            action=AdaptiveActionType.SOLVE_TARGETED_QUESTION,
                            subject=weak.subject,
                            topic=weak.topic,
                            priority=weak.priority,
                            target_question_id=target_q["id"],
                            tutor_mode=None,
                            tutor_query=None,
                            reason=f"Reinforce {weak.topic} with fresh targeted practice.",
                            explanation=f"Work through question {target_q['id']} to solidify your understanding of {weak.topic}.",
                        )
                    )

                # If all questions attempted and still weak, recommend guideline review
                else:
                    rec_id = f"REC-REV-{uuid.uuid4().hex[:6].upper()}"
                    recommendations.append(
                        AdaptiveRecommendation(
                            recommendation_id=rec_id,
                            action=AdaptiveActionType.REVIEW_CONCEPT,
                            subject=weak.subject,
                            topic=weak.topic,
                            priority=weak.priority,
                            target_question_id=None,
                            tutor_mode="mechanistic_explanation",
                            tutor_query=f"Provide a mechanistic review of {weak.topic} with verified PMC citations.",
                            reason=f"All available questions for {weak.topic} have been attempted.",
                            explanation=f"Review the primary verified evidence excerpts for {weak.topic} before re-testing.",
                        )
                    )

        # 2. If no weaknesses or after addressing weaknesses, look for unattempted/developing topics
        for topic_name, m in topic_masteries.items():
            if m.total_attempts == 0:
                topic_q = [
                    q for q in questions
                    if q.get("topic", "").strip().lower() == topic_name.strip().lower()
                    and q.get("id") not in attempted_ids
                ]
                if topic_q:
                    target = topic_q[0]
                    recommendations.append(
                        AdaptiveRecommendation(
                            recommendation_id=f"REC-NEW-{uuid.uuid4().hex[:6].upper()}",
                            action=AdaptiveActionType.SOLVE_TARGETED_QUESTION,
                            subject=m.subject,
                            topic=m.topic,
                            priority=WeaknessPriority.LOW,
                            target_question_id=target["id"],
                            reason=f"Expand your preclinical knowledge into {m.topic}.",
                            explanation=f"You haven't attempted questions in {m.topic} yet. Start with this foundational question.",
                        )
                    )

        return recommendations
