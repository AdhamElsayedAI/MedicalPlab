"""Stage-E Pipeline: Adaptive Learning & Student Intelligence Orchestrator.

Integrates interaction ingestion, mastery computation, gap detection,
profile updating, and deterministic recommendation generation into a unified LearningReport.
"""

import time
from typing import Sequence
import uuid

from medicalplab.stage_b.models import require, strings
from .models import (
    KnowledgeGap,
    LearningRecommendation,
    LearningReport,
    QuestionAttempt,
    StudentProfile,
)
from .performance_tracker import detect_learning_gaps
from .recommendation import compile_next_learning_actions, generate_recommendations
from .student_profile import create_initial_profile, update_student_profile


class StageEPipeline:
    """Deterministic orchestrator for Stage-E student intelligence."""

    def __init__(
        self,
        weak_threshold: float = 0.60,
        min_gap_attempts: int = 1,
    ):
        require(0.0 < weak_threshold < 1.0, "'weak_threshold' must be between 0.0 and 1.0")
        require(min_gap_attempts >= 1, "'min_gap_attempts' must be >= 1")
        self.weak_threshold = weak_threshold
        self.min_gap_attempts = min_gap_attempts
        self.trace: list[dict] = []

    def evaluate(
        self,
        student_id: str,
        attempts: Sequence[QuestionAttempt],
        current_profile: StudentProfile | None = None,
    ) -> LearningReport:
        """Process student attempts and generate a complete, deterministic LearningReport."""
        strings(student_id)
        clean_id = student_id.strip()

        start_time = time.perf_counter()
        run_id = str(uuid.uuid4())

        # 1. Initialize or validate student profile
        if current_profile is None:
            profile = create_initial_profile(clean_id)
        else:
            require(isinstance(current_profile, StudentProfile), "current_profile must be StudentProfile instance")
            require(
                current_profile.student_id == clean_id,
                f"current_profile student_id '{current_profile.student_id}' does not match '{clean_id}'",
            )
            profile = current_profile

        # 2. Update profile with attempts
        updated_profile = update_student_profile(
            profile,
            attempts,
            weak_threshold=self.weak_threshold,
        )

        # 3. Detect learning gaps
        gaps = detect_learning_gaps(
            attempts,
            min_attempts=self.min_gap_attempts,
            threshold=self.weak_threshold,
        )

        # 4. Generate recommendations
        recommendations = generate_recommendations(updated_profile, gaps)

        # 5. Compile top actions
        next_actions = compile_next_learning_actions(recommendations)

        elapsed = time.perf_counter() - start_time

        # 6. Assemble report
        report = LearningReport(
            student_profile=updated_profile,
            knowledge_gaps=gaps,
            recommendations=recommendations,
            next_learning_actions=next_actions,
            generated_at=time.time(),
        )

        self.trace.append(
            {
                "run_id": run_id,
                "student_id": clean_id,
                "total_attempts": len(attempts),
                "weak_topics_count": len(updated_profile.weak_topics),
                "knowledge_gaps_count": len(gaps),
                "recommendations_count": len(recommendations),
                "seconds": elapsed,
            }
        )

        return report
