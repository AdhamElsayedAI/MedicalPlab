"""Personalized study plan and learning path generator for Stage-F.

Transforms diagnostic outputs from Stage-E (LearningReport, KnowledgeGaps, Recommendations)
into a structured, prioritized, and explainable curriculum of StudyMilestones.
"""

import time
from typing import Any, Sequence
import uuid

from medicalplab.stage_b.models import require, strings
from .models import (
    PersonalizedStudyPlan,
    PlatformDifficulty,
    StudyMilestone,
    UserGoal,
)


class LearningPathGenerator:
    """Deterministic generator for student personalized medical study plans."""

    def generate_study_plan(
        self,
        student_id: str,
        learning_report: Any,
        user_goal: UserGoal | None = None,
    ) -> PersonalizedStudyPlan:
        """Construct a personalized, milestone-driven study plan."""
        strings(student_id)
        require(learning_report is not None, "learning_report is required")

        plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"
        now = time.time()

        # Extract Stage-E profile attributes
        profile = getattr(learning_report, "student_profile", None)
        overall_level = str(getattr(profile, "learning_level", "beginner")).capitalize()
        gaps = getattr(learning_report, "knowledge_gaps", ())
        recommendations = getattr(learning_report, "recommendations", ())

        milestones: list[StudyMilestone] = []

        # 1. Milestone: Remediation of Critical Knowledge Gaps (High Priority)
        for i, gap in enumerate(gaps[:3], 1):
            topic = getattr(gap, "topic", "Cardiology")
            reason = getattr(gap, "reason", "Deficit detected")
            milestones.append(
                StudyMilestone(
                    milestone_id=f"M{i}-REMEDIATION",
                    topic=topic,
                    target_difficulty=PlatformDifficulty.EASY,
                    objective=f"Close foundational knowledge gap in {topic}.",
                    priority="HIGH",
                    recommended_actions=(
                        f"Review {topic} guidelines in Stage-D Teaching mode.",
                        f"Complete 10 easy-to-medium practice questions in Stage-C.",
                        f"Justification: {reason}",
                    ),
                )
            )

        # 2. Milestone: Targeted User Goal (if provided)
        if user_goal:
            milestones.append(
                StudyMilestone(
                    milestone_id="M-USER-GOAL",
                    topic=user_goal.target_topic,
                    target_difficulty=PlatformDifficulty.MEDIUM,
                    objective=f"Attain {user_goal.target_mastery} mastery in {user_goal.target_topic} (Target accuracy: {int(user_goal.target_accuracy * 100)}%).",
                    priority="HIGH",
                    recommended_actions=(
                        f"Daily practice questions on {user_goal.target_topic}.",
                        "Participate in timed clinical mock exams.",
                    ),
                )
            )

        # 3. Milestone: Reinforcement and Advanced Mastery
        if not milestones:
            # Student has no weak areas detected
            milestones.append(
                StudyMilestone(
                    milestone_id="M1-ADVANCED",
                    topic="Comprehensive Clinical Medicine",
                    target_difficulty=PlatformDifficulty.HARD,
                    objective="Advance clinical judgment with multi-system case simulations and mock exams.",
                    priority="MEDIUM",
                    recommended_actions=(
                        "Engage with Stage-D Case Discussion vignettes.",
                        "Attempt timed exam mode sessions.",
                    ),
                )
            )

        summary = (
            f"Personalized PLAB Study Plan for Student '{student_id}'. Current curriculum tier: "
            f"{overall_level}. The plan prioritizes {len(milestones)} milestone(s) targeting "
            f"identified deficits and progressive clinical readiness."
        )

        return PersonalizedStudyPlan(
            plan_id=plan_id,
            student_id=student_id.strip(),
            created_at=now,
            overall_learning_level=overall_level,
            milestones=tuple(milestones),
            summary=summary,
        )
