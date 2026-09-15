"""Tests for MasteryTrackingEngine."""
from __future__ import annotations

import pytest
from medicalplab.adaptive.mastery import DeterministicMVPMasteryEngine
from medicalplab.adaptive.models import (
    AttemptRecord,
    ConfidenceLevel,
    MasteryLevel,
    MasteryStatus,
)


@pytest.fixture
def engine() -> DeterministicMVPMasteryEngine:
    return DeterministicMVPMasteryEngine()


def test_empty_attempts_defaults_to_not_started(engine: DeterministicMVPMasteryEngine):
    res = engine.evaluate_topic(
        subject="Renal physiology",
        topic="RAAS mechanisms",
        attempts=[],
    )
    assert res.total_attempts == 0
    assert res.correct_attempts == 0
    assert res.accuracy is None
    assert res.mastery_score == 0.0
    assert res.mastery_level == MasteryLevel.BEGINNER
    assert res.mastery_status == MasteryStatus.NOT_STARTED
    assert res.confidence == ConfidenceLevel.LOW
    assert res.consecutive_errors == 0
    assert res.last_attempt_correct is None


def test_single_failed_attempt_triggers_needs_review(engine: DeterministicMVPMasteryEngine):
    attempt = AttemptRecord(
        attempt_key="att-1",
        question_id="UNI-RENAL-001",
        subject="Renal physiology",
        topic="RAAS mechanisms",
        selected="B",
        correct=False,
    )
    res = engine.evaluate_topic(
        subject="Renal physiology",
        topic="RAAS mechanisms",
        attempts=[attempt],
    )
    assert res.total_attempts == 1
    assert res.correct_attempts == 0
    assert res.accuracy == 0.0
    assert res.mastery_level == MasteryLevel.BEGINNER
    assert res.mastery_status == MasteryStatus.NEEDS_REVIEW
    assert res.consecutive_errors == 1
    assert res.last_attempt_correct is False


def test_low_accuracy_maps_to_needs_review(engine: DeterministicMVPMasteryEngine):
    attempts = [
        AttemptRecord(attempt_key=f"att-{i}", question_id=f"Q-{i}", subject="Renal physiology",
                      topic="RAAS mechanisms", selected="A", correct=(i == 0))
        for i in range(5)
    ]  # 1/5 correct = 20%
    res = engine.evaluate_topic(
        subject="Renal physiology",
        topic="RAAS mechanisms",
        attempts=attempts,
    )
    assert res.total_attempts == 5
    assert res.correct_attempts == 1
    assert res.accuracy == 0.20
    assert res.mastery_level == MasteryLevel.BEGINNER
    assert res.mastery_status == MasteryStatus.NEEDS_REVIEW
    assert res.consecutive_errors == 4
    assert res.confidence == ConfidenceLevel.MEDIUM


def test_consecutive_errors_streak_overrides_to_needs_review(engine: DeterministicMVPMasteryEngine):
    # Overall 3/5 = 60%, but the last 2 attempts were wrong!
    attempts = [
        AttemptRecord(attempt_key="att-1", question_id="Q-1", subject="Renal physiology", topic="RAAS", selected="A", correct=True),
        AttemptRecord(attempt_key="att-2", question_id="Q-2", subject="Renal physiology", topic="RAAS", selected="A", correct=True),
        AttemptRecord(attempt_key="att-3", question_id="Q-3", subject="Renal physiology", topic="RAAS", selected="A", correct=True),
        AttemptRecord(attempt_key="att-4", question_id="Q-4", subject="Renal physiology", topic="RAAS", selected="B", correct=False),
        AttemptRecord(attempt_key="att-5", question_id="Q-5", subject="Renal physiology", topic="RAAS", selected="B", correct=False),
    ]
    res = engine.evaluate_topic(
        subject="Renal physiology",
        topic="RAAS",
        attempts=attempts,
    )
    assert res.accuracy == 0.60
    assert res.consecutive_errors == 2
    # Because consecutive errors >= 2, status must flag NEEDS_REVIEW
    assert res.mastery_status == MasteryStatus.NEEDS_REVIEW


def test_high_accuracy_maps_to_mastered_and_advanced(engine: DeterministicMVPMasteryEngine):
    # 5/5 correct = 100%
    attempts = [
        AttemptRecord(attempt_key=f"att-{i}", question_id=f"Q-{i}", subject="Renal physiology",
                      topic="Glomerular filtration", selected="A", correct=True)
        for i in range(5)
    ]
    res = engine.evaluate_topic(
        subject="Renal physiology",
        topic="Glomerular filtration",
        attempts=attempts,
    )
    assert res.accuracy == 1.0
    assert res.mastery_level == MasteryLevel.ADVANCED
    assert res.mastery_status == MasteryStatus.MASTERED
    assert res.consecutive_errors == 0
    assert res.last_attempt_correct is True
    assert res.confidence == ConfidenceLevel.MEDIUM


def test_high_accuracy_with_few_attempts_caps_at_proficient(engine: DeterministicMVPMasteryEngine):
    # 2/2 correct = 100%, but fewer than min_advanced_attempts (5)
    attempts = [
        AttemptRecord(attempt_key="att-1", question_id="Q-1", subject="Renal physiology", topic="Tubular transport", selected="A", correct=True),
        AttemptRecord(attempt_key="att-2", question_id="Q-2", subject="Renal physiology", topic="Tubular transport", selected="A", correct=True),
    ]
    res = engine.evaluate_topic(
        subject="Renal physiology",
        topic="Tubular transport",
        attempts=attempts,
    )
    assert res.accuracy == 1.0
    assert res.mastery_level == MasteryLevel.PROFICIENT
    assert res.confidence == ConfidenceLevel.LOW
