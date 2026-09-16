"""MedicalPlab AI Anatomy command, ontology, and 3D tutor layer."""
from __future__ import annotations

from .api import router as anatomy_router
from .commands import AnatomyAction, AnatomyCommand
from .config import is_anatomy_enabled
from .manifest import (
    RENAL_STRUCTURES,
    get_renal_manifest,
    get_structure_by_id,
    resolve_mesh_node,
    resolve_query_to_structure,
    valid_structure_ids as valid_renal_structure_ids,
)
from .models import (
    AnatomyActionType,
    AnatomyAgentResponse,
    AnatomySession,
    AnatomyStructure,
    ChallengeResult,
    InteractionRequest,
    InteractionRequestType,
    LessonState,
    SceneAction,
)
from .ontology import (
    MVP_STRUCTURES,
    AnatomyStructure as LegacyAnatomyStructure,
    get_structure,
    resolve_structure,
)
from .service import AnatomyService
from .agent import StructuredAnatomyAgent

__all__ = [
    "AnatomyAction",
    "AnatomyCommand",
    "AnatomyActionType",
    "AnatomyAgentResponse",
    "AnatomySession",
    "AnatomyStructure",
    "ChallengeResult",
    "InteractionRequest",
    "InteractionRequestType",
    "LessonState",
    "SceneAction",
    "StructuredAnatomyAgent",
    "AnatomyService",
    "anatomy_router",
    "is_anatomy_enabled",
    "RENAL_STRUCTURES",
    "get_renal_manifest",
    "get_structure_by_id",
    "resolve_mesh_node",
    "resolve_query_to_structure",
    "valid_renal_structure_ids",
    "MVP_STRUCTURES",
    "get_structure",
    "resolve_structure",
]
