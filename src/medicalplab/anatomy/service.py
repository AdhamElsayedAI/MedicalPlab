"""Domain service orchestrating anatomy sessions, Socratic tutoring, and deterministic challenge scoring."""
from __future__ import annotations

import time
import uuid
from typing import Optional

from .agent import StructuredAnatomyAgent
from .manifest import get_renal_manifest, get_structure_by_id, resolve_mesh_node
from .models import (
    AnatomyActionType,
    AnatomyAgentResponse,
    AnatomySession,
    ChallengeResult,
    ChallengeSubmitRequest,
    ChallengeSubmitResponse,
    InteractSessionRequest,
    InteractSessionResponse,
    LessonState,
    SceneAction,
    StartSessionRequest,
    StartSessionResponse,
)
from .repository import AnatomyRepository


class AnatomyServiceError(RuntimeError):
    pass


class AnatomyOwnershipError(PermissionError):
    pass


class AnatomyService:
    """Core domain service for 3D Anatomy learning interactions."""

    def __init__(
        self,
        repository: Optional[AnatomyRepository] = None,
        agent: Optional[StructuredAnatomyAgent] = None,
    ):
        self.repository = repository or AnatomyRepository()
        self.agent = agent or StructuredAnatomyAgent()

    def start_session(self, request: StartSessionRequest) -> StartSessionResponse:
        """Start a new anatomy learning session or resume existing session."""
        learner_id = request.learner_id.strip()
        objective = request.learning_objective or "RENAL_BLOOD_FLOW_AND_HILUM"

        # Check existing active session for learner
        existing_sessions = self.repository.list_sessions_for_learner(learner_id)
        for s in existing_sessions:
            if s.learning_objective == objective and s.lesson_state != LessonState.COMPLETED:
                # Resume existing active session
                initial_tutor = self.agent.plan_interaction(
                    user_query=None,
                    lesson_state=s.lesson_state,
                    selected_structure_id=s.selected_structure_ids[-1] if s.selected_structure_ids else None,
                    target_structure_id=s.current_target_structure_id,
                    hint_level=s.hint_level,
                )
                return StartSessionResponse(
                    session=s,
                    initial_tutor_response=initial_tutor,
                    active_structures=list(get_renal_manifest()),
                )

        # Create new session
        session_id = f"anat_{uuid.uuid4().hex[:12]}"
        now = time.time()
        new_session = AnatomySession(
            session_id=session_id,
            learner_id=learner_id,
            learning_objective=objective,
            lesson_state=LessonState.INTRO,
            current_target_structure_id="renal_vein_left",
            selected_structure_ids=[],
            hint_level=0,
            challenge_state="NOT_STARTED",
            challenge_result=None,
            created_at=now,
            updated_at=now,
        )

        initial_tutor = self.agent.plan_interaction(
            user_query=None,
            lesson_state=LessonState.INTRO,
            selected_structure_id=None,
            target_structure_id="renal_vein_left",
            hint_level=0,
        )

        self.repository.save_session(new_session)

        return StartSessionResponse(
            session=new_session,
            initial_tutor_response=initial_tutor,
            active_structures=list(get_renal_manifest()),
        )

    def get_session(self, session_id: str, learner_id: Optional[str] = None) -> AnatomySession:
        """Retrieve authorized session state."""
        session = self.repository.get_session(session_id)
        if not session:
            raise AnatomyServiceError(f"Anatomy session '{session_id}' not found.")
        if learner_id and session.learner_id != learner_id:
            raise AnatomyOwnershipError(f"Learner '{learner_id}' is not authorized for session '{session_id}'.")
        return session

    def interact(self, session_id: str, request: InteractSessionRequest) -> InteractSessionResponse:
        """Handle learner dialogue or 3D physical mesh click."""
        session = self.get_session(session_id, request.learner_id)

        selected_id = request.selected_structure_id
        if selected_id:
            # Map mesh node name to canonical structure_id if necessary
            resolved = resolve_mesh_node(selected_id) or get_structure_by_id(selected_id)
            canonical_id = resolved.structure_id if resolved else selected_id.strip().casefold()
            session.selected_structure_ids.append(canonical_id)
        else:
            canonical_id = None

        # Socratic Progression Logic
        if session.lesson_state in (LessonState.INTRO, LessonState.GUIDED_VESSELS, LessonState.GUIDED_IDENTIFICATION):
            if canonical_id:
                if canonical_id == session.current_target_structure_id:
                    # Correct identification in guided phase
                    session.lesson_state = LessonState.CHALLENGE_ACTIVE
                    session.current_target_structure_id = "renal_artery_left"  # target for independent challenge
                    session.hint_level = 0
                else:
                    # Incorrect identification -> trigger Socratic hint
                    session.lesson_state = LessonState.GUIDED_IDENTIFICATION
                    session.hint_level = min(session.hint_level + 1, 3)

        tutor_response = self.agent.plan_interaction(
            user_query=request.message,
            lesson_state=session.lesson_state,
            selected_structure_id=canonical_id,
            target_structure_id=session.current_target_structure_id,
            hint_level=session.hint_level,
        )

        session.updated_at = time.time()
        self.repository.save_session(session)

        deterministic_feedback = None
        if canonical_id:
            s_obj = get_structure_by_id(canonical_id)
            deterministic_feedback = {
                "selected_structure_id": canonical_id,
                "display_name": s_obj.display_name if s_obj else canonical_id,
                "ontology_id": s_obj.ontology_id if s_obj else "UNKNOWN",
                "is_guided_target": canonical_id == session.current_target_structure_id,
            }

        return InteractSessionResponse(
            session=session,
            tutor_response=tutor_response,
            deterministic_feedback=deterministic_feedback,
        )

    def submit_challenge(self, session_id: str, request: ChallengeSubmitRequest) -> ChallengeSubmitResponse:
        """Evaluate learner 3D mesh selection for the independent challenge.

        CRITICAL ARCHITECTURAL RULE: Correctness is evaluated DETERMINISTICALLY by
        comparing selected_structure_id to current_target_structure_id.
        The LLM is NEVER permitted to decide or override correctness.
        """
        session = self.get_session(session_id, request.learner_id)

        target_id = session.current_target_structure_id or "renal_artery_left"
        selected_raw = request.selected_structure_id.strip().casefold()

        # Resolve selected mesh name if needed
        resolved = resolve_mesh_node(selected_raw) or get_structure_by_id(selected_raw)
        selected_id = resolved.structure_id if resolved else selected_raw

        # Deterministic scoring
        is_correct = (selected_id == target_id)

        if is_correct:
            session.challenge_result = ChallengeResult.CORRECT
            session.challenge_state = "PASSED"
            session.lesson_state = LessonState.COMPLETED
            tutor_msg = (
                f"Challenge Complete! You correctly identified the {get_structure_by_id(target_id).display_name}. "
                "You have successfully mastered the spatial orientation and arterial supply of the renal hilum."
            )
            actions = [
                SceneAction(action=AnatomyActionType.HIGHLIGHT_STRUCTURE, structure_id=target_id),
                SceneAction(action=AnatomyActionType.FOCUS_STRUCTURE, structure_id=target_id),
            ]
        else:
            session.challenge_result = ChallengeResult.INCORRECT
            session.challenge_state = "FAILED"
            tutor_msg = (
                f"Incorrect. You selected {get_structure_by_id(selected_id).display_name if get_structure_by_id(selected_id) else selected_id}. "
                f"The correct target was the {get_structure_by_id(target_id).display_name}, "
                "which originates from the abdominal aorta and lies intermediate between the anterior renal vein and the posterior renal pelvis."
            )
            actions = [
                SceneAction(action=AnatomyActionType.HIGHLIGHT_STRUCTURE, structure_id=target_id),
                SceneAction(action=AnatomyActionType.FOCUS_STRUCTURE, structure_id=target_id),
            ]

        session.updated_at = time.time()
        self.repository.save_session(session)

        return ChallengeSubmitResponse(
            session=session,
            is_correct=is_correct,
            target_structure_id=target_id,
            selected_structure_id=selected_id,
            tutor_feedback=tutor_msg,
            scene_actions=actions,
        )
