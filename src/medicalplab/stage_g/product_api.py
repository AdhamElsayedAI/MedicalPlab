"""Versioned product-facing API for MedicalPlab web/mobile clients.

This router is intentionally free of demo fixtures. Endpoints fail closed when a
real AI service has not been wired yet. Stable product contracts live here;
internal Stage-B/C/D/E/F/G/R names are not exposed to clients.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from medicalplab.anatomy.commands import AnatomyAction, AnatomyCommand
from medicalplab.anatomy.ontology import MVP_STRUCTURES
from medicalplab.anatomy.validator import AnatomyCommandError, validate_anatomy_command
from medicalplab.stage_g.runtime import runtime_metadata


router = APIRouter(prefix="/api/v1")


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
