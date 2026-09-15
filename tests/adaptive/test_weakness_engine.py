"""Tests for WeaknessDetectionEngine."""
from __future__ import annotations

import pytest
from medicalplab.adaptive.models import (
    ConfidenceLevel,
    MasteryLevel,
    MasteryStatus,
    TopicMasteryRecord,
    WeaknessPriority,
)
from medicalplab.adaptive.weakness import WeaknessDetectionEngine


@pytest.fixture
def weakness_engine() -> WeaknessDetectionEngine:
    return WeaknessDetectionEngine()


def test_detects_low_accuracy_as_high_priority(weakness_engine: WeaknessDetectionEngine):
    record = TopicMasteryRecord(
        subject="Renal physiology",
        topic="RAAS mechanisms",
        total_attempts=5,
        correct_attempts=1,
        accuracy=0.20,
        mastery_score=0.20,
        mastery_level=MasteryLevel.BEGINNER,
        mastery_status=MasteryStatus.NEEDS_REVIEW,
        confidence=ConfidenceLevel.MEDIUM,
        consecutive_errors=2,
        last_attempt_correct=False,
    )
    weaknesses = weakness_engine.detect_weaknesses([record])
    assert len(weaknesses) == 1
    w = weaknesses[0]
    assert w.topic == "RAAS mechanisms"
    assert w.priority == WeaknessPriority.HIGH
    assert w.failure_rate == 0.80
    assert w.missed_count == 4
    assert w.consecutive_errors == 2
    assert "consecutive recent errors" in w.reason


def test_detects_medium_priority_weakness(weakness_engine: WeaknessDetectionEngine):
    record = TopicMasteryRecord(
        subject="Renal physiology",
        topic="Acid-base balance",
        total_attempts=4,
        correct_attempts=2,
        accuracy=0.50,
        mastery_score=0.50,
        mastery_level=MasteryLevel.DEVELOPING,
        mastery_status=MasteryStatus.NEEDS_REVIEW,
        confidence=ConfidenceLevel.LOW,
        consecutive_errors=1,
        last_attempt_correct=False,
    )
    weaknesses = weakness_engine.detect_weaknesses([record])
    assert len(weaknesses) == 1
    w = weaknesses[0]
    assert w.topic == "Acid-base balance"
    assert w.priority == WeaknessPriority.MEDIUM
    assert w.failure_rate == 0.50


def test_ignores_mastered_topics(weakness_engine: WeaknessDetectionEngine):
    record = TopicMasteryRecord(
        subject="Renal physiology",
        topic="Glomerular filtration",
        total_attempts=5,
        correct_attempts=4,
        accuracy=0.80,
        mastery_score=0.80,
        mastery_level=MasteryLevel.ADVANCED,
        mastery_status=MasteryStatus.MASTERED,
        confidence=ConfidenceLevel.MEDIUM,
        consecutive_errors=0,
        last_attempt_correct=True,
    )
    weaknesses = weakness_engine.detect_weaknesses([record])
    assert len(weaknesses) == 0


def test_sorts_weaknesses_by_priority_and_failure_rate(weakness_engine: WeaknessDetectionEngine):
    w1 = TopicMasteryRecord(
        subject="Renal physiology", topic="Mild gap", total_attempts=4, correct_attempts=2,
        accuracy=0.50, mastery_score=0.50, mastery_level=MasteryLevel.DEVELOPING,
        mastery_status=MasteryStatus.NEEDS_REVIEW, confidence=ConfidenceLevel.LOW, consecutive_errors=1,
    )
    w2 = TopicMasteryRecord(
        subject="Renal physiology", topic="Severe gap", total_attempts=5, correct_attempts=1,
        accuracy=0.20, mastery_score=0.20, mastery_level=MasteryLevel.BEGINNER,
        mastery_status=MasteryStatus.NEEDS_REVIEW, confidence=ConfidenceLevel.MEDIUM, consecutive_errors=3,
    )
    weaknesses = weakness_engine.detect_weaknesses([w1, w2])
    assert len(weaknesses) == 2
    assert weaknesses[0].topic == "Severe gap"
    assert weaknesses[0].priority == WeaknessPriority.HIGH
    assert weaknesses[1].topic == "Mild gap"
    assert weaknesses[1].priority == WeaknessPriority.MEDIUM
