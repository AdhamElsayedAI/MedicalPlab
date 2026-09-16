"""SQLite persistence repository for Anatomy learning sessions."""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from .models import AnatomySession, ChallengeResult, LessonState

DEFAULT_ANATOMY_DB = Path(__file__).resolve().parents[3] / "Data" / "persistence" / "anatomy.sqlite3"


class AnatomyRepository:
    """Thread-safe SQLite repository for persistent 3D anatomy learning sessions."""

    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_ANATOMY_DB
        self._is_memory = str(self.db_path) == ":memory:"
        self._mem_conn: Optional[sqlite3.Connection] = None
        if self._is_memory:
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
        self._ensure_tables()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        if self._is_memory and self._mem_conn is not None:
            yield self._mem_conn
        else:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path), timeout=10.0)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def _ensure_tables(self) -> None:
        with self._connection() as conn:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS anatomy_sessions (
                        session_id TEXT PRIMARY KEY,
                        learner_id TEXT NOT NULL,
                        learning_objective TEXT NOT NULL,
                        lesson_state TEXT NOT NULL,
                        current_target_structure_id TEXT,
                        selected_structure_ids TEXT NOT NULL,
                        hint_level INTEGER NOT NULL DEFAULT 0,
                        challenge_state TEXT NOT NULL DEFAULT 'NOT_STARTED',
                        challenge_result TEXT,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_anatomy_learner
                    ON anatomy_sessions(learner_id)
                    """
                )

    def save_session(self, session: AnatomySession) -> None:
        """Insert or update an anatomy learning session."""
        now = time.time()
        with self._connection() as conn:
            with conn:
                conn.execute(
                    """
                    INSERT INTO anatomy_sessions (
                        session_id, learner_id, learning_objective, lesson_state,
                        current_target_structure_id, selected_structure_ids,
                        hint_level, challenge_state, challenge_result,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        learning_objective=excluded.learning_objective,
                        lesson_state=excluded.lesson_state,
                        current_target_structure_id=excluded.current_target_structure_id,
                        selected_structure_ids=excluded.selected_structure_ids,
                        hint_level=excluded.hint_level,
                        challenge_state=excluded.challenge_state,
                        challenge_result=excluded.challenge_result,
                        updated_at=excluded.updated_at
                    """,
                    (
                        session.session_id,
                        session.learner_id,
                        session.learning_objective,
                        session.lesson_state.value,
                        session.current_target_structure_id,
                        json.dumps(session.selected_structure_ids),
                        session.hint_level,
                        session.challenge_state,
                        session.challenge_result.value if session.challenge_result else None,
                        session.created_at,
                        now,
                    ),
                )

    def get_session(self, session_id: str) -> Optional[AnatomySession]:
        """Fetch session by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM anatomy_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if not row:
                return None

            selected_list = json.loads(row["selected_structure_ids"]) if row["selected_structure_ids"] else []
            res_val = row["challenge_result"]

            return AnatomySession(
                session_id=row["session_id"],
                learner_id=row["learner_id"],
                learning_objective=row["learning_objective"],
                lesson_state=LessonState(row["lesson_state"]),
                current_target_structure_id=row["current_target_structure_id"],
                selected_structure_ids=selected_list,
                hint_level=row["hint_level"],
                challenge_state=row["challenge_state"],
                challenge_result=ChallengeResult(res_val) if res_val else None,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def list_sessions_for_learner(self, learner_id: str) -> list[AnatomySession]:
        """Fetch all sessions owned by learner."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM anatomy_sessions WHERE learner_id = ? ORDER BY updated_at DESC",
                (learner_id,),
            ).fetchall()
            results = []
            for row in rows:
                selected_list = json.loads(row["selected_structure_ids"]) if row["selected_structure_ids"] else []
                res_val = row["challenge_result"]
                results.append(
                    AnatomySession(
                        session_id=row["session_id"],
                        learner_id=row["learner_id"],
                        learning_objective=row["learning_objective"],
                        lesson_state=LessonState(row["lesson_state"]),
                        current_target_structure_id=row["current_target_structure_id"],
                        selected_structure_ids=selected_list,
                        hint_level=row["hint_level"],
                        challenge_state=row["challenge_state"],
                        challenge_result=ChallengeResult(res_val) if res_val else None,
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                )
            return results
