"""Session intelligence manager for Stage-F.

Maintains state, context, active topics, learning objectives, and sequential interaction histories.
"""

import time
from typing import Any
import uuid

from medicalplab.stage_b.models import require, strings
from .models import (
    PlatformDifficulty,
    PlatformIntent,
    SessionContext,
)


class SessionIntelligenceManager:
    """Stateful manager tracking multi-turn student learning sessions."""

    def __init__(self):
        self._sessions: dict[str, SessionContext] = {}
        self._histories: dict[str, list[dict[str, Any]]] = {}

    def create_session(
        self,
        student_id: str,
        topic: str = "General Medicine",
        objective: str = "PLAB Clinical Preparation",
        difficulty: PlatformDifficulty = PlatformDifficulty.MEDIUM,
        created_at: float | None = None,
    ) -> SessionContext:
        """Initialize a new learning session."""
        strings(student_id)
        now = created_at if created_at is not None else time.time()
        session_id = str(uuid.uuid4())

        ctx = SessionContext(
            session_id=session_id,
            student_id=student_id.strip(),
            current_topic=topic.strip() or "General Medicine",
            learning_objective=objective.strip() or "PLAB Clinical Preparation",
            difficulty_context=difficulty,
            interactions_count=0,
            created_at=now,
            last_active_at=now,
        )
        self._sessions[session_id] = ctx
        self._histories[session_id] = []
        return ctx

    def get_session(self, session_id: str) -> SessionContext | None:
        """Retrieve an active session by session_id."""
        return self._sessions.get(session_id.strip())

    def record_interaction(
        self,
        session_id: str,
        intent: PlatformIntent,
        query: str,
        response_summary: str,
        topic_update: str | None = None,
    ) -> SessionContext:
        """Record a completed interaction and return the updated session context."""
        ctx = self.get_session(session_id)
        require(ctx is not None, f"Session '{session_id}' not found")

        now = time.time()
        interaction = {
            "timestamp": now,
            "intent": intent.value,
            "query": query.strip(),
            "summary": response_summary.strip(),
        }
        self._histories[session_id].append(interaction)

        updated_topic = topic_update.strip() if topic_update and topic_update.strip() else ctx.current_topic

        updated_ctx = SessionContext(
            session_id=ctx.session_id,
            student_id=ctx.student_id,
            current_topic=updated_topic,
            learning_objective=ctx.learning_objective,
            difficulty_context=ctx.difficulty_context,
            interactions_count=ctx.interactions_count + 1,
            created_at=ctx.created_at,
            last_active_at=now,
        )
        self._sessions[session_id] = updated_ctx
        return updated_ctx

    def update_difficulty(
        self,
        session_id: str,
        new_difficulty: PlatformDifficulty,
    ) -> SessionContext:
        """Update difficulty context for an active session."""
        ctx = self.get_session(session_id)
        require(ctx is not None, f"Session '{session_id}' not found")
        require(isinstance(new_difficulty, PlatformDifficulty), f"Invalid difficulty: {new_difficulty}")

        updated_ctx = SessionContext(
            session_id=ctx.session_id,
            student_id=ctx.student_id,
            current_topic=ctx.current_topic,
            learning_objective=ctx.learning_objective,
            difficulty_context=new_difficulty,
            interactions_count=ctx.interactions_count,
            created_at=ctx.created_at,
            last_active_at=time.time(),
        )
        self._sessions[session_id] = updated_ctx
        return updated_ctx

    def get_history(self, session_id: str) -> tuple[dict[str, Any], ...]:
        """Retrieve sequential interaction history for a session."""
        return tuple(self._histories.get(session_id.strip(), []))
