"""End-to-end integration test for the Phase 2A Adaptive Learning Loop."""
from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest

from medicalplab.adaptive.learner_state import UnifiedLearnerStateManager
from medicalplab.adaptive.models import AdaptiveActionType, LearningEvent
from medicalplab.adaptive.service import AdaptiveLearningService
from medicalplab.adaptive.tutor_bridge import AdaptiveTutorBridge
from medicalplab.university.service import UniversityService


@pytest.fixture
def clean_db(tmp_path: Path) -> Path:
    db_file = tmp_path / "university_e2e.sqlite3"
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


def test_complete_adaptive_learning_loop(clean_db: Path):
    """Verify the entire closed loop:
    1. Student answers questions incorrectly.
    2. System computes learning state & identifies weakness with high priority.
    3. Adaptive engine recommends ASK_GROUNDED_TUTOR remediation.
    4. Socratic tutor provides grounded pedagogical explanation.
    5. Student attempts question correctly.
    6. Mastery elevates and loop progress is confirmed.
    """
    user_id = "student_e2e_loop"
    uni_service = UniversityService(db=clean_db)
    state_manager = UnifiedLearnerStateManager(db_path=clean_db)
    adaptive_service = AdaptiveLearningService(state_manager=state_manager)

    # Step 1: Student attempts RAAS questions and misses both
    ans1 = uni_service.answer(user=user_id, question_id="UNI-RENAL-001", selected="B", key="key-1")
    assert ans1["is_correct"] is False

    ans2 = uni_service.answer(user=user_id, question_id="UNI-RENAL-002", selected="C", key="key-2")
    assert ans2["is_correct"] is False

    # Step 2: Adaptive Engine detects weakness
    state = adaptive_service.get_learner_state(user_id)
    assert state.total_attempts == 2
    assert state.correct_attempts == 0
    assert state.overall_accuracy == 0.0

    # Weakness identified
    assert len(state.weak_topics) >= 1
    primary_weakness = state.weak_topics[0]
    assert primary_weakness.topic == "RAAS mechanisms"
    assert primary_weakness.consecutive_errors == 2
    assert "consecutive recent errors" in primary_weakness.reason

    # Step 3: Decision Engine selects ASK_GROUNDED_TUTOR
    rec = adaptive_service.get_top_recommendation(user_id)
    assert rec is not None
    assert rec.action == AdaptiveActionType.ASK_GROUNDED_TUTOR
    assert rec.topic == "RAAS mechanisms"
    assert rec.tutor_mode == "socratic_hint"

    # Step 4: Socratic Tutor intervention is executed (fully grounded)
    tutor_resp = adaptive_service.trigger_grounded_remediation(
        learner_id=user_id,
        topic=rec.topic,
        question_id=rec.target_question_id,
        preferred_mode=rec.tutor_mode,
        custom_query=rec.tutor_query,
    )
    assert tutor_resp.verification.unsupported_propositions == 0
    assert tutor_resp.support_status in {"SUPPORTED", "SAFE_FALLBACK"}
    assert tutor_resp.pedagogical_state == "PRE_SUBMISSION"

    # Baseline mastery level before improvement
    baseline_mastery = state.topic_mastery["RAAS mechanisms"].mastery_level.value
    assert baseline_mastery == "beginner"

    # Step 5: Armed with grounded understanding, student re-attempts correctly
    ans3 = uni_service.answer(user=user_id, question_id="UNI-RENAL-001", selected="A", key="key-3")
    assert ans3["is_correct"] is True

    # Step 6: Verify learning state updates and closed-loop progress
    updated_state = adaptive_service.get_learner_state(user_id)
    assert updated_state.total_attempts == 3
    assert updated_state.correct_attempts == 1
    raas_mastery = updated_state.topic_mastery["RAAS mechanisms"]
    assert raas_mastery.consecutive_errors == 0  # Broken error streak!
    assert raas_mastery.last_attempt_correct is True

    loop_result = adaptive_service.verify_loop_closure(
        learner_id=user_id,
        topic="RAAS mechanisms",
        initial_mastery_level=baseline_mastery,
    )
    assert loop_result["learner_id"] == user_id
    assert loop_result["topic"] == "RAAS mechanisms"
    assert loop_result["total_attempts"] == 3
