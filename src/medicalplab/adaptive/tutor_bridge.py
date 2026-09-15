"""Bridge connecting the Adaptive Engine to the Phase 1 Grounded Socratic Tutor.

MANDATORY SAFETY INVARIANT:
The Adaptive Engine never invokes an LLM directly. All educational interventions
must route through TutorService, guaranteeing that evidence retrieval, rights gating,
claim segmentation, proposition verification, and fail-closed fallbacks execute in full.
"""
from __future__ import annotations

import logging
from typing import Any

from medicalplab.tutor.models import TutorChatRequest, TutorChatResponse, TutorMode
from medicalplab.tutor.service import TutorService

logger = logging.getLogger(__name__)


class AdaptiveTutorBridge:
    """Delegates pedagogical remediations to the Phase 1 Grounded Tutor."""

    def __init__(self, tutor_service: TutorService | None = None) -> None:
        self._tutor_service = tutor_service

    @property
    def tutor_service(self) -> TutorService:
        if self._tutor_service is None:
            from medicalplab.stage_g.product_api import get_tutor_service
            self._tutor_service = get_tutor_service()
        return self._tutor_service

    def trigger_remediation(
        self,
        learner_id: str,
        topic: str,
        question_id: str | None = None,
        preferred_mode: str | None = None,
        custom_query: str | None = None,
        attempt_key: str | None = None,
    ) -> TutorChatResponse:
        """Trigger an evidence-grounded Socratic remediation dialogue turn."""
        mode: TutorMode = (preferred_mode or "socratic_hint") if preferred_mode in [
            "auto",
            "socratic_hint",
            "mechanistic_explanation",
            "misconception_diagnosis",
            "distractor_explanation",
            "concept_comparison",
            "revision_summary",
        ] else "socratic_hint"

        query_text = (
            custom_query.strip()
            if custom_query and custom_query.strip()
            else f"I am having difficulty understanding {topic}. Can you guide me through this concept step-by-step?"
        )

        req = TutorChatRequest(
            query=query_text,
            mode=mode,
            topic=topic,
            question_id=question_id,
            attempt_key=attempt_key,
            learner_id=learner_id,
            hint_level=1,
        )

        logger.info(
            "AdaptiveTutorBridge invoking Phase 1 TutorService for learner=%s topic=%s mode=%s",
            learner_id,
            topic,
            mode,
        )

        # Delegate exclusively to the frozen Phase 1 Tutor Service
        response = self.tutor_service.chat(req, x_user_id=learner_id)
        return response
