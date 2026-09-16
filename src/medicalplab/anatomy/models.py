"""Data models and action schemas for MedicalPlab Generative 3D Anatomy."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class AnatomyActionType(str, Enum):
    """Deterministic 3D scene actions recognized by the frontend Scene Controller."""
    FOCUS_STRUCTURE = "FOCUS_STRUCTURE"
    HIGHLIGHT_STRUCTURE = "HIGHLIGHT_STRUCTURE"
    ISOLATE_STRUCTURE = "ISOLATE_STRUCTURE"
    SHOW_STRUCTURE = "SHOW_STRUCTURE"
    HIDE_STRUCTURE = "HIDE_STRUCTURE"
    SHOW_RELATION = "SHOW_RELATION"
    SET_STRUCTURE_OPACITY = "SET_STRUCTURE_OPACITY"
    RESET_SCENE = "RESET_SCENE"


class InteractionRequestType(str, Enum):
    """Types of physical interactions requested from the student."""
    IDENTIFY_STRUCTURE = "IDENTIFY_STRUCTURE"
    EXPLORE_SCENE = "EXPLORE_SCENE"


class LessonState(str, Enum):
    """State machine progression for the guided anatomy lesson."""
    INTRO = "INTRO"
    GUIDED_VESSELS = "GUIDED_VESSELS"
    GUIDED_IDENTIFICATION = "GUIDED_IDENTIFICATION"
    CHALLENGE_READY = "CHALLENGE_READY"
    CHALLENGE_ACTIVE = "CHALLENGE_ACTIVE"
    COMPLETED = "COMPLETED"


class ChallengeResult(str, Enum):
    """Deterministic outcome of the independent 3D identification challenge."""
    PENDING = "PENDING"
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"


class SceneAction(BaseModel):
    """Validated structured action dispatched to the Three.js Scene Controller."""
    action: AnatomyActionType
    structure_id: Optional[str] = None
    opacity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    duration_ms: Optional[int] = Field(default=None, ge=0, le=5000)


class InteractionRequest(BaseModel):
    """Request from AI tutor for the student to physically interact with the 3D model."""
    type: InteractionRequestType = InteractionRequestType.IDENTIFY_STRUCTURE
    target_structure_id: Optional[str] = None
    prompt: str


class AnatomyStructure(BaseModel):
    """Deterministic anatomical structure metadata grounded in verified ontologies."""
    structure_id: str
    display_name: str
    source_system: str = "HRA"
    source_structure_id: str
    ontology_id: str
    mesh_node_names: list[str]
    aliases: list[str] = Field(default_factory=list)
    region: str = "renal"
    relationships: list[dict[str, str]] = Field(default_factory=list)
    learning_objectives: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    fma_crosswalk: Optional[str] = None


class AnatomyAgentResponse(BaseModel):
    """Strict schema emitted by the Structured AI Anatomy Tutor Agent."""
    tutor_message: str
    scene_actions: list[SceneAction] = Field(default_factory=list)
    interaction_request: Optional[InteractionRequest] = None
    fallback_applied: bool = False


class AnatomySession(BaseModel):
    """Persistent anatomy learning session."""
    session_id: str
    learner_id: str
    learning_objective: str
    lesson_state: LessonState = LessonState.INTRO
    current_target_structure_id: Optional[str] = None
    selected_structure_ids: list[str] = Field(default_factory=list)
    hint_level: int = 0
    challenge_state: str = "NOT_STARTED"
    challenge_result: Optional[ChallengeResult] = None
    created_at: float
    updated_at: float


# --- API Request & Response DTOs ---

class StartSessionRequest(BaseModel):
    learner_id: str
    learning_objective: Optional[str] = "RENAL_BLOOD_FLOW_AND_HILUM"


class StartSessionResponse(BaseModel):
    session: AnatomySession
    initial_tutor_response: AnatomyAgentResponse
    active_structures: list[AnatomyStructure]


class InteractSessionRequest(BaseModel):
    learner_id: str
    message: Optional[str] = None
    selected_structure_id: Optional[str] = None


class InteractSessionResponse(BaseModel):
    session: AnatomySession
    tutor_response: AnatomyAgentResponse
    deterministic_feedback: Optional[dict[str, Any]] = None


class ChallengeSubmitRequest(BaseModel):
    learner_id: str
    selected_structure_id: str


class ChallengeSubmitResponse(BaseModel):
    session: AnatomySession
    is_correct: bool
    target_structure_id: str
    selected_structure_id: str
    tutor_feedback: str
    scene_actions: list[SceneAction] = Field(default_factory=list)


class AnatomyManifestResponse(BaseModel):
    structures: list[AnatomyStructure]
    provenance: dict[str, Any]
    learning_objectives: list[str]
