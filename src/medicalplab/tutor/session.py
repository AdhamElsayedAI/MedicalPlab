"""In-memory bounded session management and attempt-key bound submission verification."""
from __future__ import annotations

import logging
import sqlite3
import time
import uuid
from collections import OrderedDict
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from medicalplab.tutor.models import PedagogicalState

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_UNIVERSITY_DB = ROOT_DIR / "Data/persistence/university.sqlite3"


@dataclass
class TutorSession:
    session_id: str
    user_id: str | None = None
    question_id: str | None = None
    history: list[dict[str, str]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def add_turn(self, role: str, content: str, max_turns: int = 3) -> None:
        self.history.append({"role": role, "content": content.strip()})
        # Bounded context window: keep strictly the last max_turns turns
        if len(self.history) > max_turns:
            self.history = self.history[-max_turns:]
        self.last_active = time.time()


class TutorSessionManager:
    """In-memory LRU session store with time-to-live expiration."""

    def __init__(self, ttl_seconds: float = 3600.0, max_sessions: int = 1000) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self._sessions: OrderedDict[str, TutorSession] = OrderedDict()

    def get_or_create(self, session_id: str | None = None, user_id: str | None = None) -> TutorSession:
        self.prune_expired()

        sid = session_id or str(uuid.uuid4())
        if sid in self._sessions:
            sess = self._sessions[sid]
            sess.last_active = time.time()
            self._sessions.move_to_end(sid)
            return sess

        # Enforce max sessions LRU
        if len(self._sessions) >= self.max_sessions:
            self._sessions.popitem(last=False)

        new_sess = TutorSession(session_id=sid, user_id=user_id)
        self._sessions[sid] = new_sess
        return new_sess

    def prune_expired(self) -> None:
        now = time.time()
        expired = [sid for sid, sess in self._sessions.items() if now - sess.last_active > self.ttl_seconds]
        for sid in expired:
            del self._sessions[sid]


def verify_submission_proof(
    user_id: str | None,
    question_id: str | None,
    attempt_key: str | None,
    db_path: Path | str | None = None,
) -> PedagogicalState:
    """Verify whether a learner has authoritatively submitted a University question.

    Security Rules:
    - X-User-Id is classified as anonymous/demo identity, NOT authentication.
    - PRE_SUBMISSION is always the fail-closed default.
    - If question_id is None, returns GENERAL_STUDY.
    - Transition to POST_SUBMISSION requires exact persisted tuple match:
      (user_id, question_id, attempt_key) in university_attempts.
    - Absent, mismatched, or cross-learner attempt keys fail closed to PRE_SUBMISSION.
    - Zero exposure of another learner's submission state.
    """
    if not question_id:
        return "GENERAL_STUDY"

    # Strict fail-closed default: if any component is missing, cannot transition
    if not user_id or not user_id.strip() or not attempt_key or not attempt_key.strip():
        return "PRE_SUBMISSION"

    target_db = Path(db_path) if db_path else DEFAULT_UNIVERSITY_DB
    if not target_db.exists():
        return "PRE_SUBMISSION"

    try:
        with closing(sqlite3.connect(target_db, timeout=5.0)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT 1 FROM university_attempts WHERE user_id = ? AND question_id = ? AND attempt_key = ?",
                (user_id.strip(), question_id.strip(), attempt_key.strip()),
            ).fetchone()
            if row:
                return "POST_SUBMISSION"
    except Exception as exc:
        logger.warning(f"Error checking university attempts proof: {exc}")

    return "PRE_SUBMISSION"
