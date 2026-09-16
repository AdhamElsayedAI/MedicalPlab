"""API Router for MedicalPlab Phase 2B Intelligent Socratic Remediation Engine.

Provides the complete REST API surface for bounded Socratic remediation:
1. POST /api/v1/remediation/start                        - Initiate session (Turn 1: Probe)
2. POST /api/v1/remediation/turn                         - Advance dialogue (Turn 2: Guide, Turn 3: Consolidate)
3. GET  /api/v1/remediation/session/{session_id}         - Retrieve authorized session state & timeline
4. GET  /api/v1/remediation/session/{session_id}/transfer - Fetch eligible held-out transfer item
5. POST /api/v1/remediation/session/{session_id}/transfer - Submit transfer answer & score deterministically
6. POST /api/v1/remediation/session/{session_id}/abandon  - Explicit session abandonment
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from medicalplab.remediation.config import is_remediation_enabled
from medicalplab.remediation.controller import (
    RemediationError,
    RemediationLoopController,
)
from medicalplab.remediation.models import (
    RemediationSessionResponse,
    RemediationTurnResponse,
    StartRemediationRequest,
    TransferItemDTO,
    TransferSubmissionRequest,
    TransferSubmissionResponse,
    TurnRemediationRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/remediation", tags=["Intelligent Socratic Remediation"])

_controller: Optional[RemediationLoopController] = None


def get_remediation_controller() -> RemediationLoopController:
    """Singleton getter for the RemediationLoopController."""
    global _controller
    if _controller is None:
        _controller = RemediationLoopController()
    return _controller


def configure_remediation_controller(controller: Optional[RemediationLoopController]) -> None:
    """Inject a mock or configured controller for testing."""
    global _controller
    _controller = controller


def _check_feature_enabled() -> None:
    """Ensure Phase 2B remediation is enabled before serving requests."""
    if not is_remediation_enabled():
        raise HTTPException(
            status_code=503,
            detail="Socratic remediation engine is currently disabled by feature flag.",
        )


def _resolve_user_id(x_user_id: str | None = Header(default=None)) -> str:
    """Extract authenticated or demo user identity."""
    if x_user_id and x_user_id.strip():
        return x_user_id.strip()
    return "demo-student-001"


@router.post("/start", response_model=RemediationTurnResponse)
def start_remediation(
    body: StartRemediationRequest,
    x_user_id: str | None = Header(default=None),
) -> RemediationTurnResponse:
    """Initiate a bounded 3-turn Socratic remediation session for an incorrect option.

    Endpoint: POST /api/v1/remediation/start
    """
    _check_feature_enabled()
    user_id = _resolve_user_id(x_user_id)
    controller = get_remediation_controller()
    try:
        response = controller.start_session(
            user_id=user_id,
            question_id=body.question_id,
            selected_option=body.selected_option,
            topic=body.topic,
            attempt_id=body.attempt_id,
            idempotency_key=body.idempotency_key,
        )
        return response
    except RemediationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error in /remediation/start: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal remediation failure.") from exc


@router.post("/turn", response_model=RemediationTurnResponse)
def advance_remediation_turn(
    body: TurnRemediationRequest,
    x_user_id: str | None = Header(default=None),
) -> RemediationTurnResponse:
    """Advance the Socratic dialogue through Turn 2 (Guide) or Turn 3 (Consolidate).

    Endpoint: POST /api/v1/remediation/turn
    """
    _check_feature_enabled()
    user_id = _resolve_user_id(x_user_id)
    controller = get_remediation_controller()
    try:
        response = controller.advance_turn(
            session_id=body.session_id,
            user_id=user_id,
            student_message=body.student_message,
            idempotency_key=body.idempotency_key,
        )
        return response
    except RemediationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error in /remediation/turn: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal remediation failure.") from exc


@router.get("/session/{session_id}", response_model=RemediationSessionResponse)
def get_remediation_session(
    session_id: str,
    x_user_id: str | None = Header(default=None),
) -> RemediationSessionResponse:
    """Retrieve full remediation session state and 5-stage timeline.

    Endpoint: GET /api/v1/remediation/session/{session_id}
    """
    _check_feature_enabled()
    user_id = _resolve_user_id(x_user_id)
    controller = get_remediation_controller()
    session = controller.get_session(session_id, user_id=user_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Remediation session '{session_id}' not found.")

    return RemediationSessionResponse(
        session_id=session.session_id,
        user_id=session.user_id,
        question_id=session.question_id,
        topic=session.topic,
        turn_number=session.turn_number,
        max_turns=session.max_turns,
        is_complete=session.is_complete,
        lifecycle_state=session.lifecycle_state,
        outcome=session.outcome,
        strategy=session.strategy,
        timeline=session.timeline,
        turns=session.turns,
        transfer_item=None,
        transfer_attempt=session.transfer_attempt,
    )


@router.get("/session/{session_id}/transfer", response_model=TransferItemDTO)
def get_transfer_item(
    session_id: str,
    x_user_id: str | None = Header(default=None),
) -> TransferItemDTO:
    """Retrieve the eligible held-out transfer item without answer keys.

    Endpoint: GET /api/v1/remediation/session/{session_id}/transfer
    """
    _check_feature_enabled()
    user_id = _resolve_user_id(x_user_id)
    controller = get_remediation_controller()
    try:
        item = controller.get_transfer_item(
            session_id=session_id,
            user_id=user_id,
        )
        return item
    except RemediationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error in /remediation/session/{session_id}/transfer: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal transfer assessment error.") from exc


@router.post("/session/{session_id}/transfer", response_model=TransferSubmissionResponse)
def submit_transfer_answer(
    session_id: str,
    body: TransferSubmissionRequest,
    x_user_id: str | None = Header(default=None),
) -> TransferSubmissionResponse:
    """Submit transfer item answer for deterministic server-side scoring.

    Endpoint: POST /api/v1/remediation/session/{session_id}/transfer
    """
    _check_feature_enabled()
    user_id = _resolve_user_id(x_user_id)
    controller = get_remediation_controller()
    try:
        response = controller.submit_transfer(
            session_id=session_id,
            user_id=user_id,
            question_id=body.question_id,
            selected_option=body.selected_option,
            was_assisted=body.was_assisted,
            idempotency_key=body.idempotency_key,
        )
        return response
    except RemediationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error in /remediation/session/{session_id}/transfer: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal transfer scoring error.") from exc


@router.post("/session/{session_id}/abandon", response_model=RemediationTurnResponse)
def abandon_remediation_session(
    session_id: str,
    x_user_id: str | None = Header(default=None),
) -> RemediationTurnResponse:
    """Explicitly abandon an active remediation session.

    Endpoint: POST /api/v1/remediation/session/{session_id}/abandon
    """
    _check_feature_enabled()
    user_id = _resolve_user_id(x_user_id)
    controller = get_remediation_controller()
    try:
        response = controller.abandon_session(
            session_id=session_id,
            user_id=user_id,
        )
        return response
    except RemediationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error in /remediation/abandon: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal remediation failure.") from exc
