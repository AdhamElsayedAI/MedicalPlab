"""Unified Read-Only Learner Progress Composition API.

Composes learner progress across University, PLAB, Adaptive Learning, and 3D Anatomy
into ONE single, coherent educational journey for the student.

CRITICAL INVARIANTS:
1. Strictly read-only projection; zero data ownership moved to this layer.
2. Module-owned persistence remains authoritative (university.sqlite3, pilot_store.db, anatomy.sqlite3).
3. Strictly student-facing (no educator-only cohort analytics mixed into student view).
4. No invented pseudo-clinical competency metrics or speculative numerical scoring.
5. Strict cross-learner data isolation (Learner A activity never visible to Learner B).
"""
from __future__ import annotations

import logging
from typing import Any, Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from medicalplab.identity import resolve_learner_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Unified Learner Progress"])


class UnifiedProgressResponse(BaseModel):
    learner_id: str
    university: dict[str, Any] = Field(default_factory=dict)
    plab: dict[str, Any] = Field(default_factory=dict)
    adaptive: dict[str, Any] = Field(default_factory=dict)
    anatomy: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)


def _get_unified_progress(learner_id: str) -> dict[str, Any]:
    """Compile read-only progress projection for the given authenticated learner."""
    # 1. University Progress
    uni_data: dict[str, Any] = {}
    try:
        from medicalplab.university.api import service as get_uni_service
        uni_svc = get_uni_service()
        uni_data = uni_svc.progress(learner_id)
    except Exception as exc:
        logger.debug("University progress fetch error for %s: %s", learner_id, exc)
        uni_data = {
            "track": "university",
            "attempted": 0,
            "correct": 0,
            "accuracy": None,
            "topics": [],
            "weak_topics": [],
        }

    # 2. PLAB Progress
    plab_data: dict[str, Any] = {}
    try:
        from medicalplab.stage_g.product_api import get_plab_service
        plab_svc = get_plab_service()
        if plab_svc is not None:
            plab_data = plab_svc.progress(learner_id)
    except Exception as exc:
        logger.debug("PLAB progress fetch error for %s: %s", learner_id, exc)
        plab_data = {
            "user_id": learner_id,
            "total_attempts": 0,
            "attempts_count": 0,
            "overall_accuracy": None,
            "topics": [],
        }

    # 3. Adaptive Learning State
    adaptive_data: dict[str, Any] = {}
    try:
        from medicalplab.adaptive.api import get_adaptive_service
        adapt_svc = get_adaptive_service()
        state = adapt_svc.get_learner_state(learner_id)
        adaptive_data = {
            "total_attempts": state.total_attempts,
            "correct_attempts": state.correct_attempts,
            "overall_accuracy": state.overall_accuracy,
            "mastered_topics_count": sum(
                1 for m in state.topic_mastery.values() if getattr(m.mastery_status, "value", str(m.mastery_status)) == "mastered"
            ),
            "weak_topics_count": len(state.weak_topics),
            "top_recommendation": state.recommendations[0].model_dump() if state.recommendations else None,
            "weak_topics": [w.model_dump() for w in state.weak_topics[:5]],
        }
    except Exception as exc:
        logger.debug("Adaptive state fetch error for %s: %s", learner_id, exc)

    # 4. 3D Anatomy Sessions and Challenges
    anatomy_data: dict[str, Any] = {}
    anat_sessions: list[Any] = []
    try:
        from medicalplab.anatomy.repository import AnatomyRepository
        anat_repo = AnatomyRepository()
        anat_sessions = anat_repo.list_sessions_for_learner(learner_id)
        completed = [s for s in anat_sessions if getattr(s.lesson_state, "value", str(s.lesson_state)) == "COMPLETED"]
        passed = [s for s in anat_sessions if s.challenge_state == "PASSED"]
        anatomy_data = {
            "total_sessions": len(anat_sessions),
            "completed_sessions": len(completed),
            "challenges_passed": len(passed),
            "recent_sessions": [
                {
                    "session_id": s.session_id,
                    "objective": s.learning_objective,
                    "lesson_state": getattr(s.lesson_state, "value", str(s.lesson_state)),
                    "challenge_state": s.challenge_state,
                    "challenge_result": getattr(s.challenge_result, "value", str(s.challenge_result)) if s.challenge_result else None,
                }
                for s in anat_sessions[:5]
            ],
        }
    except Exception as exc:
        logger.debug("Anatomy progress fetch error for %s: %s", learner_id, exc)

    # 5. Composed Summary
    uni_attempts = uni_data.get("attempted", 0) if isinstance(uni_data, dict) else 0
    plab_attempts = (
        plab_data.get("total_attempts", 0) or plab_data.get("attempts_count", 0)
        if isinstance(plab_data, dict)
        else 0
    )

    anat_challenges = len([s for s in anat_sessions if s.challenge_result is not None])
    total_evaluative_attempts = uni_attempts + plab_attempts + anat_challenges

    active_modules: list[str] = []
    if uni_attempts > 0:
        active_modules.append("university")
    if plab_attempts > 0:
        active_modules.append("plab")
    if anatomy_data.get("total_sessions", 0) > 0:
        active_modules.append("anatomy")
    if adaptive_data.get("total_attempts", 0) > 0:
        active_modules.append("adaptive")

    summary = {
        "total_questions_attempted": total_evaluative_attempts,
        "active_modules": active_modules,
        "cross_track_learner_id": learner_id,
    }

    return {
        "learner_id": learner_id,
        "university": uni_data,
        "plab": plab_data,
        "adaptive": adaptive_data,
        "anatomy": anatomy_data,
        "summary": summary,
    }


@router.get("/learner/progress", response_model=UnifiedProgressResponse)
def get_learner_progress(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_learner_id: Optional[str] = Header(None, alias="X-Learner-Id"),
) -> dict[str, Any]:
    """Retrieve unified read-only progress composed across all learning modes."""
    learner_id = resolve_learner_id(x_user_id=x_user_id, x_learner_id=x_learner_id, required=True)
    return _get_unified_progress(learner_id)


@router.get("/progress", response_model=UnifiedProgressResponse)
def get_progress_alias(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_learner_id: Optional[str] = Header(None, alias="X-Learner-Id"),
) -> dict[str, Any]:
    """Convenience alias for /api/v1/learner/progress."""
    learner_id = resolve_learner_id(x_user_id=x_user_id, x_learner_id=x_learner_id, required=True)
    return _get_unified_progress(learner_id)
