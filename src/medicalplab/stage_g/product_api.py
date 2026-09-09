"""Versioned product-facing API for MedicalPlab web/mobile clients.

This router is intentionally free of demo fixtures. Endpoints fail closed when a
real AI service has not been wired yet. Stable product contracts live here;
internal Stage-B/C/D/E/F/G/R names are not exposed to clients.
"""

from __future__ import annotations

import hmac
import os
from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from medicalplab.anatomy.commands import AnatomyAction, AnatomyCommand
from medicalplab.anatomy.ontology import MVP_STRUCTURES
from medicalplab.anatomy.validator import AnatomyCommandError, validate_anatomy_command
from medicalplab.plab.governance import REVIEW_DIMENSIONS, ReviewDecision, ReviewFinding
from medicalplab.plab.pilot import PLABPilotService, PLABProductError
from medicalplab.stage_g.runtime import runtime_metadata


router = APIRouter(prefix="/api/v1")
_plab_service: PLABPilotService | None = None


def configure_plab_service(service: PLABPilotService | None) -> None:
    """Inject a product service for application startup or isolated tests."""
    global _plab_service
    _plab_service = service


def get_plab_service() -> PLABPilotService:
    global _plab_service
    if _plab_service is None:
        preview = os.environ.get("MEDICALPLAB_PLAB_PREVIEW_QA", "").strip().lower() in {"1", "true", "yes"}
        _plab_service = PLABPilotService.load_default(preview_qa=preview)
    return _plab_service


def _product_error(exc: PLABProductError) -> HTTPException:
    return HTTPException(exc.status_code, detail={"code": exc.code, "message": str(exc)})


def _student_id(x_user_id: str | None = Header(default=None)) -> str:
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(401, detail={"code": "USER_ID_REQUIRED", "message": "X-User-Id is required."})
    return x_user_id.strip()


def _reviewer_identity(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> str:
    configured = os.environ.get("MEDICALPLAB_INTERNAL_REVIEW_TOKEN", "")
    if not configured:
        raise HTTPException(503, detail={"code": "REVIEW_AUTH_NOT_CONFIGURED", "message": "Reviewer authentication is not configured."})
    role = (x_user_role or "").strip().upper()
    if role not in {"DOCTOR", "INSTITUTION_ADMIN"}:
        raise HTTPException(403, detail={"code": "REVIEWER_ROLE_REQUIRED", "message": "A reviewer role is required."})
    supplied = (authorization or "").removeprefix("Bearer ").strip()
    if not supplied or not hmac.compare_digest(supplied, configured):
        raise HTTPException(401, detail={"code": "INVALID_REVIEW_CREDENTIAL", "message": "Reviewer credential is invalid."})
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(401, detail={"code": "REVIEWER_ID_REQUIRED", "message": "X-User-Id is required."})
    return x_user_id.strip()


class AnatomyCommandRequest(BaseModel):
    action: Literal["focus", "highlight", "isolate", "ghost", "reset"]
    structure_ids: list[str] = Field(default_factory=list, max_length=16)
    opacity: float | None = Field(default=None, ge=0.05, le=1.0)


class ClinicalReasonRequest(BaseModel):
    query: str = Field(min_length=3, max_length=4000)
    case_context: str | None = Field(default=None, max_length=8000)


class PLABQuestionRequest(BaseModel):
    specialty: str = Field(min_length=2, max_length=120)
    topic: str = Field(min_length=2, max_length=200)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    learning_objective: str | None = Field(default=None, max_length=500)


class PLABEvaluationRequest(BaseModel):
    question_id: str = Field(min_length=3, max_length=120)
    selected_option: Literal["A", "B", "C", "D", "E"]
    idempotency_key: str = Field(min_length=8, max_length=200)
    response_time_ms: int | None = Field(default=None, ge=0, le=86_400_000)


class ReviewStartRequest(BaseModel):
    reviewer_name: str | None = Field(default=None, max_length=200)


class ReviewDecisionRequest(BaseModel):
    final_decision: Literal["APPROVED", "REVISE", "REJECT"]
    clinical_correctness: Literal["pass", "edit", "fail"]
    sba_unambiguity: Literal["pass", "edit", "fail"]
    uk_alignment: Literal["pass", "edit", "fail"]
    evidence_adequacy: Literal["pass", "edit", "fail"]
    distractor_quality: Literal["pass", "edit", "fail"]
    explanation_quality: Literal["pass", "edit", "fail"]
    review_comments: str | None = Field(default=None, max_length=4000)
    revision_notes: str | None = Field(default=None, max_length=4000)


class QuestionRevisionRequest(BaseModel):
    changes: dict[str, object]
    revision_reason: str = Field(min_length=3, max_length=2000)


@router.get("/version")
def version() -> dict[str, object]:
    return {
        "service": "MedicalPlab Product API",
        "api_version": "v1",
        "contract_version": "2026-09-09",
        **runtime_metadata(),
    }


@router.get("/anatomy/structures")
def anatomy_structures() -> dict[str, object]:
    return {
        "schema_version": "anatomy-ontology-v1",
        "count": len(MVP_STRUCTURES),
        "structures": [
            {
                "structure_id": structure.structure_id,
                "name": structure.name,
                "aliases": list(structure.aliases),
                "system": structure.system,
                "parent_id": structure.parent_id,
                "related_structure_ids": list(structure.related_structure_ids),
            }
            for structure in MVP_STRUCTURES
        ],
    }


@router.post("/anatomy/command")
def anatomy_command(request: AnatomyCommandRequest) -> dict[str, object]:
    try:
        command = AnatomyCommand(
            action=AnatomyAction(request.action),
            structure_ids=tuple(request.structure_ids),
            opacity=request.opacity,
        )
        validated = validate_anatomy_command(command)
    except (ValueError, AnatomyCommandError) as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_ANATOMY_COMMAND",
                "message": str(exc),
            },
        ) from exc

    return {
        "schema_version": validated.schema_version,
        "validated": True,
        "command": {
            "action": validated.action.value,
            "structure_ids": list(validated.structure_ids),
            "opacity": validated.opacity,
        },
    }


@router.post("/clinical/reason")
def clinical_reason(_: ClinicalReasonRequest) -> None:
    raise HTTPException(
        status_code=503,
        detail={
            "code": "CLINICAL_AI_NOT_CONFIGURED",
            "message": "Real clinical reasoning service is not wired to the Product API yet; no demo response was generated.",
        },
    )


@router.post("/plab/question")
def plab_question(_: PLABQuestionRequest) -> None:
    raise HTTPException(
        status_code=503,
        detail={
            "code": "PLAB_GENERATOR_NOT_CONFIGURED",
            "message": "Evidence-grounded five-option PLAB generation is not wired to the Product API yet; no demo question was generated.",
        },
    )


@router.get("/plab/questions")
def list_plab_questions() -> dict[str, object]:
    try:
        service = get_plab_service()
        items = service.list_questions()
        return {
            "items": items,
            "count": len(items),
            "content_policy": "GOLDEN_ONLY" if not service.preview_qa else "PREVIEW_QA_EXPLICIT",
        }
    except PLABProductError as exc:
        raise _product_error(exc) from exc


@router.get("/plab/questions/{question_id}")
def get_plab_question(question_id: str) -> dict[str, object]:
    try:
        return get_plab_service().question_dto(question_id)
    except PLABProductError as exc:
        raise _product_error(exc) from exc


@router.post("/plab/evaluate")
def evaluate_plab_answer(
    request: PLABEvaluationRequest,
    x_user_id: str | None = Header(default=None),
) -> dict[str, object]:
    user_id = _student_id(x_user_id)
    try:
        return get_plab_service().evaluate(
            user_id=user_id,
            question_id=request.question_id,
            selected_option=request.selected_option,
            idempotency_key=request.idempotency_key,
            response_time_ms=request.response_time_ms,
        )
    except PLABProductError as exc:
        raise _product_error(exc) from exc


@router.get("/plab/progress")
def plab_progress(x_user_id: str | None = Header(default=None)) -> dict[str, object]:
    return get_plab_service().progress(_student_id(x_user_id))


@router.get("/internal/plab/reviews")
def list_plab_reviews(
    risk_level: str | None = None,
    reviewer_id: str = Header(alias="X-User-Id"),
    authorization: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> dict[str, object]:
    _reviewer_identity(authorization, reviewer_id, x_user_role)
    service = get_plab_service()
    items = [service.review_status(qid) for qid in service.questions]
    if risk_level:
        items = [item for item in items if item.get("risk_level") == risk_level.upper()]
    return {"items": items, "count": len(items)}


@router.get("/internal/plab/review/status/{question_id}")
def plab_review_status(
    question_id: str,
    reviewer_id: str = Header(alias="X-User-Id"),
    authorization: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> dict[str, object]:
    _reviewer_identity(authorization, reviewer_id, x_user_role)
    try:
        return get_plab_service().review_status(question_id)
    except PLABProductError as exc:
        raise _product_error(exc) from exc


@router.post("/internal/plab/review/{question_id}/start")
def start_plab_review(
    question_id: str,
    request: ReviewStartRequest,
    reviewer_id: str = Header(alias="X-User-Id"),
    authorization: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> dict[str, object]:
    actor = _reviewer_identity(authorization, reviewer_id, x_user_role)
    try:
        return get_plab_service().start_review(question_id, actor, request.reviewer_name)
    except (PLABProductError, ValueError) as exc:
        if isinstance(exc, PLABProductError):
            raise _product_error(exc) from exc
        raise HTTPException(422, detail={"code": str(exc), "message": "Review could not be started."}) from exc


@router.post("/internal/plab/review/{question_id}/decision")
def submit_plab_review(
    question_id: str,
    request: ReviewDecisionRequest,
    reviewer_id: str = Header(alias="X-User-Id"),
    authorization: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> dict[str, object]:
    actor = _reviewer_identity(authorization, reviewer_id, x_user_role)
    findings = {dimension: ReviewFinding(getattr(request, dimension)) for dimension in REVIEW_DIMENSIONS}
    try:
        return get_plab_service().submit_review(
            question_id, actor, ReviewDecision(request.final_decision), findings,
            request.review_comments, request.revision_notes,
        )
    except PLABProductError as exc:
        raise _product_error(exc) from exc


@router.patch("/internal/plab/questions/{question_id}/revision")
def revise_plab_question(
    question_id: str,
    request: QuestionRevisionRequest,
    editor_id: str = Header(alias="X-User-Id"),
    authorization: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> dict[str, object]:
    actor = _reviewer_identity(authorization, editor_id, x_user_role)
    try:
        return get_plab_service().revise_question(question_id, request.changes, request.revision_reason, actor)
    except PLABProductError as exc:
        raise _product_error(exc) from exc


@router.get("/internal/plab/telemetry")
def plab_telemetry(
    reviewer_id: str = Header(alias="X-User-Id"),
    authorization: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> dict[str, object]:
    _reviewer_identity(authorization, reviewer_id, x_user_role)
    service = get_plab_service()
    return service.telemetry.snapshot(service.governance_counts())
