"""Unified Learner State Layer for Phase 2A Adaptive Learning.

Provides a unified educational representation of the student across historical attempts,
topic mastery calculations, detected weaknesses, and active recommendations.
Acts as a non-destructive compatibility layer over existing SQLite attempt storage.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Sequence

from .decision import AdaptiveDecisionEngine
from .mastery import DeterministicMVPMasteryEngine
from .models import (
    AdaptiveRecommendation,
    AttemptRecord,
    LearnerState,
    LearningEvent,
    TopicMasteryRecord,
    WeakTopicRecord,
)
from .weakness import WeaknessDetectionEngine

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_DB = ROOT_DIR / "Data/persistence/university.sqlite3"
DEFAULT_QUESTIONS_FILE = ROOT_DIR / "Data/university/questions.json"


class UnifiedLearnerStateManager:
    """Consolidates and manages learner state without mutating existing databases."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        questions_path: Path | str | None = None,
        mastery_engine: DeterministicMVPMasteryEngine | None = None,
        weakness_engine: WeaknessDetectionEngine | None = None,
        decision_engine: AdaptiveDecisionEngine | None = None,
    ) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB
        self.questions_path = Path(questions_path) if questions_path else DEFAULT_QUESTIONS_FILE
        self.mastery_engine = mastery_engine or DeterministicMVPMasteryEngine()
        self.weakness_engine = weakness_engine or WeaknessDetectionEngine()
        self.decision_engine = decision_engine or AdaptiveDecisionEngine()

        self._questions: list[dict[str, Any]] = []
        self._load_questions()

    def _load_questions(self) -> None:
        if self.questions_path.exists():
            try:
                data = json.loads(self.questions_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self._questions = [q for q in data if isinstance(q, dict) and "id" in q]
            except Exception as exc:
                logger.warning("Failed to load questions from %s: %s", self.questions_path, exc)

    def _connect(self) -> sqlite3.Connection | None:
        if not self.db_path.exists():
            return None
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def get_raw_attempts(self, learner_id: str) -> list[AttemptRecord]:
        """Read all historical attempts for this student from the university attempt store."""
        attempts: list[AttemptRecord] = []
        conn = self._connect()
        if conn is None:
            return attempts

        try:
            with closing(conn):
                # Ensure table exists before querying
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='university_attempts'"
                )
                if not cursor.fetchone():
                    return attempts

                rows = conn.execute(
                    "SELECT user_id, attempt_key, question_id, subject, topic, selected, correct "
                    "FROM university_attempts WHERE user_id = ? ORDER BY rowid ASC",
                    (learner_id.strip(),),
                ).fetchall()

                for r in rows:
                    attempts.append(
                        AttemptRecord(
                            attempt_key=r["attempt_key"],
                            question_id=r["question_id"],
                            subject=r["subject"],
                            topic=r["topic"],
                            selected=r["selected"],
                            correct=bool(r["correct"]),
                        )
                    )
        except Exception as exc:
            logger.warning("Error reading attempts for learner %s: %s", learner_id, exc)

        return attempts

    def get_learner_state(
        self,
        learner_id: str,
        additional_attempts: Sequence[AttemptRecord] | None = None,
    ) -> LearnerState:
        """Compile complete unified LearnerState for the given learner identity."""
        cleaned_id = learner_id.strip() if learner_id else "anonymous_device"
        attempts = self.get_raw_attempts(cleaned_id)
        if additional_attempts:
            attempts.extend(additional_attempts)

        total_attempts = len(attempts)
        correct_attempts = sum(1 for a in attempts if a.correct)
        overall_accuracy = round(correct_attempts / total_attempts, 4) if total_attempts > 0 else None

        # Determine all known topics from both question bank and past attempts
        known_topics: set[tuple[str, str]] = set()
        for q in self._questions:
            s = q.get("subject", "Renal physiology")
            t = q.get("topic", "")
            if t:
                known_topics.add((s, t))

        for a in attempts:
            if a.topic:
                known_topics.add((a.subject, a.topic))

        # 1. Compute Topic Mastery
        topic_mastery: dict[str, TopicMasteryRecord] = {}
        for subj, top in sorted(known_topics, key=lambda pair: pair[1]):
            rec = self.mastery_engine.evaluate_topic(
                subject=subj,
                topic=top,
                attempts=attempts,
            )
            topic_mastery[top] = rec

        # 2. Detect Weaknesses
        weak_topics = self.weakness_engine.detect_weaknesses(
            masteries=topic_mastery,
            attempts=attempts,
        )

        # 3. Formulate Adaptive Recommendations
        attempted_q_ids = {a.question_id for a in attempts}
        recommendations = self.decision_engine.select_recommendations(
            weak_topics=weak_topics,
            topic_masteries=topic_mastery,
            available_questions=self._questions,
            attempted_question_ids=attempted_q_ids,
        )

        # 4. Recent activity log (up to last 10 attempts, newest first)
        recent_activity = list(reversed(attempts[-10:]))

        return LearnerState(
            learner_id=cleaned_id,
            total_attempts=total_attempts,
            correct_attempts=correct_attempts,
            overall_accuracy=overall_accuracy,
            topic_mastery=topic_mastery,
            weak_topics=weak_topics,
            recent_activity=recent_activity,
            recommendations=recommendations,
        )
