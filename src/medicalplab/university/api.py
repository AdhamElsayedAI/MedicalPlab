"""University-only product routes. Anonymous device IDs are demo identity, not auth."""
import os
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from .service import UniversityError, UniversityService

router = APIRouter(prefix="/api/v1/university", tags=["University Learning"])
_service = None


def service():
    global _service
    if _service is None:
        try:
            db = os.environ.get("MEDICALPLAB_UNIVERSITY_DB")
            _service = UniversityService(db=Path(db) if db else None)
        except UniversityError as exc:
            raise HTTPException(exc.status, str(exc)) from exc
    return _service


def student(x_user_id: str = Header(min_length=8, max_length=120)):
    if not x_user_id.strip():
        raise HTTPException(422, "A University learner ID is required.")
    return x_user_id


def execute(fn, *args):
    try:
        return fn(*args)
    except UniversityError as exc:
        raise HTTPException(exc.status, str(exc)) from exc
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(503, "Progress storage is unavailable. Please retry.") from exc


class Answer(BaseModel):
    question_id: str = Field(min_length=5, max_length=120)
    selected_option: str = Field(pattern="^[A-E]$")
    idempotency_key: str = Field(min_length=8, max_length=120)


@router.get("/subjects")
def subjects(s=Depends(service)):
    return {"items": s.subjects()}


@router.get("/topics")
def topics(subject: str, s=Depends(service)):
    return {"items": execute(s.topics, subject)}


@router.get("/question")
def question(subject: str, topic: str, after: str | None = None, s=Depends(service)):
    return execute(s.select, subject, topic, after)


@router.post("/answer")
def answer(body: Answer, user=Depends(student), s=Depends(service)):
    res = execute(s.answer, user, body.question_id, body.selected_option, body.idempotency_key)
    try:
        import time
        import uuid
        from medicalplab.adaptive.api import get_adaptive_service
        from medicalplab.adaptive.models import LearningEvent

        evt = LearningEvent(
            event_id=f"evt-{uuid.uuid4().hex[:10]}",
            learner_id=user,
            event_type="QUESTION_ATTEMPT",
            subject=res.get("subject", "Renal physiology"),
            topic=res.get("topic", "Renal physiology"),
            question_id=body.question_id,
            selected_option=body.selected_option,
            is_correct=bool(res.get("is_correct")),
            attempt_key=body.idempotency_key,
            timestamp=time.time(),
            metadata={"source": "university"},
        )
        get_adaptive_service().record_learning_event(evt)
    except Exception:
        pass
    return res



@router.get("/progress")
def progress(user=Depends(student), s=Depends(service)):
    return execute(s.progress, user)
