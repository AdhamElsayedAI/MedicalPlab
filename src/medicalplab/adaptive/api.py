"""API router for Phase 2A Adaptive Grounded Learning Engine."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Header, HTTPException, Query

from medicalplab.identity import resolve_learner_id
from medicalplab.tutor.models import TutorChatResponse
from .models import (
    AdaptiveRecommendation,
    LearnerState,
    LearningEvent,
    RemediationRequest,
)
from .service import AdaptiveLearningService

router = APIRouter(prefix="/api/v1/adaptive", tags=["Adaptive Learning Engine"])
_service: AdaptiveLearningService | None = None


def get_adaptive_service() -> AdaptiveLearningService:
    global _service
    if _service is None:
        _service = AdaptiveLearningService()
    return _service


def configure_adaptive_service(service: AdaptiveLearningService | None) -> None:
    global _service
    _service = service


def _resolve_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_learner_id: str | None = Header(default=None, alias="X-Learner-Id"),
    query_user: str | None = None,
) -> str:
    return resolve_learner_id(
        x_user_id=x_user_id,
        x_learner_id=x_learner_id,
        fallback_id=query_user,
        required=True,
    )


@router.get("/state", response_model=LearnerState)
def get_learner_state(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_learner_id: str | None = Header(default=None, alias="X-Learner-Id"),
    learner_id: str | None = Query(default=None),
) -> LearnerState:
    """Retrieve the unified learner state, topic mastery, weaknesses, and recommendations.

    Endpoint: GET /api/v1/adaptive/state
    Purpose: Retrieve unified learner state.
    Input: Header X-User-Id or Query learner_id.
    Output: LearnerState.
    Reason: Single unified source of truth on student educational progress.
    """
    uid = _resolve_user_id(x_user_id, x_learner_id, learner_id)
    service = get_adaptive_service()
    return service.get_learner_state(uid)


@router.get("/recommendation", response_model=AdaptiveRecommendation | None)
def get_recommendation(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_learner_id: str | None = Header(default=None, alias="X-Learner-Id"),
    learner_id: str | None = Query(default=None),
) -> AdaptiveRecommendation | None:
    """Retrieve the highest priority next learning action chosen by the Adaptive Decision Engine.

    Endpoint: GET /api/v1/adaptive/recommendation
    Purpose: Next best learning action.
    Input: Header X-User-Id or Query learner_id.
    Output: AdaptiveRecommendation or null.
    Reason: Guides student directly to their next intervention.
    """
    uid = _resolve_user_id(x_user_id, x_learner_id, learner_id)
    service = get_adaptive_service()
    return service.get_top_recommendation(uid)


@router.post("/event", response_model=LearnerState)
def record_learning_event(
    event: LearningEvent,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_learner_id: str | None = Header(default=None, alias="X-Learner-Id"),
) -> LearnerState:
    """Ingest a learning interaction event and return the updated learner state.

    Endpoint: POST /api/v1/adaptive/event
    Purpose: Ingest learning interaction event.
    Input: LearningEvent JSON body.
    Output: Updated LearnerState.
    Reason: Enables real-time mastery recalculation following practice or review.
    """
    uid = resolve_learner_id(
        x_user_id=x_user_id,
        x_learner_id=x_learner_id,
        fallback_id=event.learner_id,
        required=True,
    )
    event.learner_id = uid
    service = get_adaptive_service()
    return service.record_learning_event(event)


@router.post("/remediate", response_model=TutorChatResponse)
def trigger_remediation(
    request: RemediationRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_learner_id: str | None = Header(default=None, alias="X-Learner-Id"),
) -> TutorChatResponse:
    """Trigger an evidence-grounded Socratic tutor intervention targeted at student weakness.

    Endpoint: POST /api/v1/adaptive/remediate
    Purpose: Trigger Grounded Tutor remediation for active weakness.
    Input: RemediationRequest JSON body.
    Output: TutorChatResponse (verified by Phase 1 verifier).
    Reason: Connects adaptive gap detection to verified Socratic tutor safely.
    """
    uid = _resolve_user_id(x_user_id, x_learner_id)
    service = get_adaptive_service()
    return service.trigger_grounded_remediation(
        learner_id=uid,
        topic=request.topic,
        question_id=request.question_id,
        preferred_mode=request.preferred_mode,
        custom_query=request.custom_query,
    )


@router.get("/loop-status")
def get_loop_status(
    topic: str = Query(...),
    baseline_mastery: str = Query(...),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_learner_id: str | None = Header(default=None, alias="X-Learner-Id"),
) -> dict[str, Any]:
    """Check whether mastery has improved following an intervention.

    Endpoint: GET /api/v1/adaptive/loop-status
    Purpose: Evaluate learning loop closure.
    Input: Query params topic, baseline_mastery, Header X-User-Id.
    Output: JSON summary of initial vs current mastery.
    Reason: Closes feedback loop across diagnostic assessment and re-evaluation.
    """
    uid = _resolve_user_id(x_user_id, x_learner_id)
    service = get_adaptive_service()
    return service.verify_loop_closure(uid, topic, baseline_mastery)
