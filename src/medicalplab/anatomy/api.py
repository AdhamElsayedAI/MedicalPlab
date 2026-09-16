"""FastAPI router for MedicalPlab Generative 3D Anatomy Lab."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from .config import is_anatomy_enabled
from .manifest import get_renal_manifest
from .models import (
    AnatomyManifestResponse,
    AnatomySession,
    ChallengeSubmitRequest,
    ChallengeSubmitResponse,
    InteractSessionRequest,
    InteractSessionResponse,
    StartSessionRequest,
    StartSessionResponse,
)
from .service import AnatomyOwnershipError, AnatomyService, AnatomyServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/anatomy", tags=["Generative 3D Anatomy"])

_service: Optional[AnatomyService] = None


def get_anatomy_service() -> AnatomyService:
    """Singleton getter for the AnatomyService."""
    global _service
    if _service is None:
        _service = AnatomyService()
    return _service


def configure_anatomy_service(service: Optional[AnatomyService]) -> None:
    """Inject a configured or mock service for unit testing."""
    global _service
    _service = service


def _check_feature_enabled() -> None:
    """Enforce feature flag guardrail."""
    if not is_anatomy_enabled():
        raise HTTPException(
            status_code=503,
            detail="MedicalPlab 3D Anatomy Engine is currently disabled by feature flag.",
        )


@router.get("/manifest", response_model=AnatomyManifestResponse)
def get_anatomy_manifest():
    """Retrieve verified anatomical structure manifest and attribution provenance."""
    _check_feature_enabled()
    structures = list(get_renal_manifest())
    provenance = {
        "dataset": "HuBMAP Human Reference Atlas (HRA) CCF 3D Reference Object Library",
        "license": "CC BY 4.0",
        "attribution": "HuBMAP Human Reference Atlas (HRA) CCF 3D Reference Object Library, NIH HuBMAP Consortium (CC BY 4.0)",
        "version": "CCF v1.3 / v2.0",
        "coordinate_framework": "Common Coordinate Framework (CCF)",
        "verified_assets": [
            "VH_M_Kidney_L.glb",
            "VH_M_Ureter_L.glb",
            "VH_M_Blood_Vasculature_Kidney.glb",
        ],
    }
    objectives = [
        "RENAL_BLOOD_FLOW_AND_HILUM",
        "RENAL_INTERNAL_ORGANIZATION",
    ]
    return AnatomyManifestResponse(
        structures=structures,
        provenance=provenance,
        learning_objectives=objectives,
    )


@router.post("/session/start", response_model=StartSessionResponse)
def start_anatomy_session(request: StartSessionRequest):
    """Start or resume an anatomy learning session."""
    _check_feature_enabled()
    if not request.learner_id or not request.learner_id.strip():
        raise HTTPException(status_code=400, detail="learner_id must not be empty.")
    service = get_anatomy_service()
    return service.start_session(request)


@router.get("/session/{session_id}", response_model=AnatomySession)
def get_anatomy_session(session_id: str, x_learner_id: Optional[str] = Header(None)):
    """Retrieve session state with ownership enforcement."""
    _check_feature_enabled()
    service = get_anatomy_service()
    try:
        return service.get_session(session_id, learner_id=x_learner_id)
    except AnatomyOwnershipError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except AnatomyServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/session/{session_id}/interact", response_model=InteractSessionResponse)
def interact_with_anatomy_session(session_id: str, request: InteractSessionRequest):
    """Advance dialogue or process physical 3D mesh interaction."""
    _check_feature_enabled()
    service = get_anatomy_service()
    try:
        return service.interact(session_id, request)
    except AnatomyOwnershipError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except AnatomyServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/session/{session_id}/challenge", response_model=ChallengeSubmitResponse)
def submit_anatomy_challenge(session_id: str, request: ChallengeSubmitRequest):
    """Submit learner 3D mesh selection for deterministic challenge evaluation."""
    _check_feature_enabled()
    service = get_anatomy_service()
    try:
        return service.submit_challenge(session_id, request)
    except AnatomyOwnershipError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except AnatomyServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
