"""Tests for UnifiedLearnerStateManager and persistence compatibility."""
from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest
from medicalplab.adaptive.learner_state import UnifiedLearnerStateManager
from medicalplab.adaptive.models import AttemptRecord


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    db_file = tmp_path / "test_university.sqlite3"
    conn = sqlite3.connect(db_file)
    conn.execute("""
        CREATE TABLE university_attempts (
            user_id TEXT NOT NULL,
            attempt_key TEXT NOT NULL,
            question_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            selected TEXT NOT NULL,
            correct INTEGER NOT NULL,
            PRIMARY KEY(user_id, attempt_key)
        )
    """)
    conn.commit()
    conn.close()
    return db_file


def test_empty_learner_state_initialized(temp_db: Path):
    manager = UnifiedLearnerStateManager(db_path=temp_db)
    state = manager.get_learner_state("learner_fresh")
    assert state.learner_id == "learner_fresh"
    assert state.total_attempts == 0
    assert state.correct_attempts == 0
    assert state.overall_accuracy is None
    assert isinstance(state.topic_mastery, dict)
    assert len(state.weak_topics) == 0


def test_state_updates_from_persisted_attempts(temp_db: Path):
    conn = sqlite3.connect(temp_db)
    # Insert 3 attempts for learner_1
    conn.execute(
        "INSERT INTO university_attempts VALUES ('learner_1', 'k1', 'UNI-RENAL-001', 'Renal physiology', 'RAAS mechanisms', 'B', 0)"
    )
    conn.execute(
        "INSERT INTO university_attempts VALUES ('learner_1', 'k2', 'UNI-RENAL-002', 'Renal physiology', 'RAAS mechanisms', 'B', 1)"
    )
    conn.execute(
        "INSERT INTO university_attempts VALUES ('learner_1', 'k3', 'UNI-RENAL-003', 'Renal physiology', 'RAAS mechanisms', 'A', 0)"
    )
    conn.commit()
    conn.close()

    manager = UnifiedLearnerStateManager(db_path=temp_db)
    state = manager.get_learner_state("learner_1")

    assert state.total_attempts == 3
    assert state.correct_attempts == 1
    assert state.overall_accuracy == round(1 / 3, 4)
    assert len(state.recent_activity) == 3

    # Check topic mastery
    assert "RAAS mechanisms" in state.topic_mastery
    raas = state.topic_mastery["RAAS mechanisms"]
    assert raas.total_attempts == 3
    assert raas.correct_attempts == 1
    assert raas.accuracy == round(1 / 3, 4)
    assert raas.consecutive_errors == 1

    # Check weak topics
    assert len(state.weak_topics) >= 1
    assert state.weak_topics[0].topic == "RAAS mechanisms"


def test_state_user_isolation(temp_db: Path):
    conn = sqlite3.connect(temp_db)
    conn.execute(
        "INSERT INTO university_attempts VALUES ('user_a', 'ka', 'UNI-RENAL-001', 'Renal physiology', 'RAAS mechanisms', 'A', 1)"
    )
    conn.execute(
        "INSERT INTO university_attempts VALUES ('user_b', 'kb', 'UNI-RENAL-001', 'Renal physiology', 'RAAS mechanisms', 'B', 0)"
    )
    conn.commit()
    conn.close()

    manager = UnifiedLearnerStateManager(db_path=temp_db)
    state_a = manager.get_learner_state("user_a")
    state_b = manager.get_learner_state("user_b")

    assert state_a.total_attempts == 1
    assert state_a.correct_attempts == 1
    assert state_a.overall_accuracy == 1.0

    assert state_b.total_attempts == 1
    assert state_b.correct_attempts == 0
    assert state_b.overall_accuracy == 0.0
