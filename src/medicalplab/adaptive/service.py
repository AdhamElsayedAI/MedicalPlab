"""Core facade service for Phase 2A Adaptive Grounded Learning Engine."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from medicalplab.tutor.models import TutorChatResponse
from .learner_state import UnifiedLearnerStateManager
from .models import (
    AdaptiveRecommendation,
    AttemptRecord,
    LearnerState,
    LearningEvent,
)
from .tutor_bridge import AdaptiveTutorBridge

logger = logging.getLogger(__name__)


class AdaptiveLearningService:
    """Orchestrates learner state tracking, gap diagnosis, adaptive decisions, and grounded tutor remediation."""

    def __init__(
        self,
        state_manager: UnifiedLearnerStateManager | None = None,
        tutor_bridge: AdaptiveTutorBridge | None = None,
    ) -> None:
        self.state_manager = state_manager or UnifiedLearnerStateManager()
        self.tutor_bridge = tutor_bridge or AdaptiveTutorBridge()

    def get_learner_state(self, learner_id: str) -> LearnerState:
        """Fetch the unified learner state, including topic masteries and recommendations."""
        return self.state_manager.get_learner_state(learner_id)

    def get_top_recommendation(self, learner_id: str) -> AdaptiveRecommendation | None:
        """Return the highest priority next learning recommendation for this learner."""
        state = self.get_learner_state(learner_id)
        if state.recommendations:
            return state.recommendations[0]
        return None

    def record_learning_event(self, event: LearningEvent) -> LearnerState:
        """Ingest a learning interaction event and return the updated learner state."""
        extra_attempt: AttemptRecord | None = None
        if event.event_type == "QUESTION_ATTEMPT" and event.question_id and event.is_correct is not None:
            extra_attempt = AttemptRecord(
                attempt_key=event.attempt_key or f"evt-{uuid.uuid4().hex[:8]}",
                question_id=event.question_id,
                subject=event.subject,
                topic=event.topic,
                selected=event.selected_option or "",
                correct=event.is_correct,
                timestamp=event.timestamp,
            )

        additional = [extra_attempt] if extra_attempt else None
        return self.state_manager.get_learner_state(event.learner_id, additional_attempts=additional)

    def trigger_grounded_remediation(
        self,
        learner_id: str,
        topic: str | None = None,
        question_id: str | None = None,
        preferred_mode: str | None = None,
        custom_query: str | None = None,
        attempt_key: str | None = None,
    ) -> TutorChatResponse:
        """Trigger an evidence-grounded tutor intervention targeted at the student's active weakness."""
        # If topic is not supplied, pick from highest-priority weak topic in learner state
        target_topic = topic
        target_q = question_id
        if not target_topic:
            state = self.get_learner_state(learner_id)
            if state.weak_topics:
                target_topic = state.weak_topics[0].topic
            else:
                target_topic = "Renal physiology"

        return self.tutor_bridge.trigger_remediation(
            learner_id=learner_id,
            topic=target_topic,
            question_id=target_q,
            preferred_mode=preferred_mode,
            custom_query=custom_query,
            attempt_key=attempt_key,
        )

    def verify_loop_closure(
        self,
        learner_id: str,
        topic: str,
        initial_mastery_level: str,
    ) -> dict[str, Any]:
        """Evaluate whether student mastery improved following an educational intervention."""
        state = self.get_learner_state(learner_id)
        current = state.topic_mastery.get(topic)
        current_level = current.mastery_level.value if current else "beginner"

        ranks = {"beginner": 0, "developing": 1, "proficient": 2, "advanced": 3}
        initial_rank = ranks.get(initial_mastery_level.lower(), 0)
        current_rank = ranks.get(current_level.lower(), 0)
        improved = current_rank > initial_rank

        return {
            "learner_id": learner_id,
            "topic": topic,
            "initial_mastery": initial_mastery_level,
            "current_mastery": current_level,
            "mastery_improved": improved,
            "accuracy": current.accuracy if current else None,
            "total_attempts": current.total_attempts if current else 0,
        }
