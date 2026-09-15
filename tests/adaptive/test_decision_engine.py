"""Tests for AdaptiveDecisionEngine."""
from __future__ import annotations

import pytest
from medicalplab.adaptive.decision import AdaptiveDecisionEngine
from medicalplab.adaptive.models import (
    AdaptiveActionType,
    ConfidenceLevel,
    MasteryLevel,
    MasteryStatus,
    TopicMasteryRecord,
    WeakTopicRecord,
    WeaknessPriority,
)


@pytest.fixture
def decision_engine() -> AdaptiveDecisionEngine:
    return AdaptiveDecisionEngine(consecutive_error_threshold_for_tutor=2)


def test_recommends_grounded_tutor_for_repeated_consecutive_errors(decision_engine: AdaptiveDecisionEngine):
    weak = WeakTopicRecord(
        subject="Renal physiology",
        topic="RAAS mechanisms",
        priority=WeaknessPriority.HIGH,
        failure_rate=0.80,
        missed_count=4,
        total_attempts=5,
        consecutive_errors=3,
        reason="Missed 4 of 5 attempts on RAAS mechanisms with 3 consecutive recent errors.",
    )
    masteries = {
        "RAAS mechanisms": TopicMasteryRecord(
            subject="Renal physiology", topic="RAAS mechanisms", total_attempts=5, correct_attempts=1,
            accuracy=0.20, mastery_score=0.20, mastery_level=MasteryLevel.BEGINNER,
            mastery_status=MasteryStatus.NEEDS_REVIEW, confidence=ConfidenceLevel.MEDIUM, consecutive_errors=3,
        )
    }
    questions = [
        {"id": "UNI-RENAL-001", "topic": "RAAS mechanisms", "stem": "Stem 1"},
        {"id": "UNI-RENAL-002", "topic": "RAAS mechanisms", "stem": "Stem 2"},
    ]
    recs = decision_engine.select_recommendations(
        weak_topics=[weak],
        topic_masteries=masteries,
        available_questions=questions,
        attempted_question_ids={"UNI-RENAL-001"},
    )
    assert len(recs) >= 1
    top = recs[0]
    assert top.action == AdaptiveActionType.ASK_GROUNDED_TUTOR
    assert top.topic == "RAAS mechanisms"
    assert top.priority == WeaknessPriority.HIGH
    assert top.tutor_mode == "socratic_hint"
    assert "consecutive misses" in top.reason


def test_recommends_targeted_question_for_developing_gap(decision_engine: AdaptiveDecisionEngine):
    weak = WeakTopicRecord(
        subject="Renal physiology",
        topic="Tubular transport",
        priority=WeaknessPriority.MEDIUM,
        failure_rate=0.50,
        missed_count=1,
        total_attempts=2,
        consecutive_errors=0,
        reason="Performance is below benchmark (50% accuracy).",
    )
    masteries = {
        "Tubular transport": TopicMasteryRecord(
            subject="Renal physiology", topic="Tubular transport", total_attempts=2, correct_attempts=1,
            accuracy=0.50, mastery_score=0.50, mastery_level=MasteryLevel.DEVELOPING,
            mastery_status=MasteryStatus.NEEDS_REVIEW, confidence=ConfidenceLevel.LOW, consecutive_errors=0,
        )
    }
    questions = [
        {"id": "UNI-RENAL-010", "topic": "Tubular transport", "stem": "Stem 10"},
        {"id": "UNI-RENAL-011", "topic": "Tubular transport", "stem": "Stem 11"},
    ]
    recs = decision_engine.select_recommendations(
        weak_topics=[weak],
        topic_masteries=masteries,
        available_questions=questions,
        attempted_question_ids={"UNI-RENAL-010"},
    )
    assert len(recs) >= 1
    top = recs[0]
    assert top.action == AdaptiveActionType.SOLVE_TARGETED_QUESTION
    assert top.target_question_id == "UNI-RENAL-011"


def test_recommends_concept_review_when_all_questions_exhausted(decision_engine: AdaptiveDecisionEngine):
    weak = WeakTopicRecord(
        subject="Renal physiology",
        topic="Acid-base balance",
        priority=WeaknessPriority.MEDIUM,
        failure_rate=0.50,
        missed_count=2,
        total_attempts=4,
        consecutive_errors=1,
        reason="Below benchmark.",
    )
    masteries = {
        "Acid-base balance": TopicMasteryRecord(
            subject="Renal physiology", topic="Acid-base balance", total_attempts=4, correct_attempts=2,
            accuracy=0.50, mastery_score=0.50, mastery_level=MasteryLevel.DEVELOPING,
            mastery_status=MasteryStatus.NEEDS_REVIEW, confidence=ConfidenceLevel.LOW, consecutive_errors=1,
        )
    }
    questions = [
        {"id": "UNI-RENAL-020", "topic": "Acid-base balance", "stem": "Stem 20"},
    ]
    # Both questions attempted
    recs = decision_engine.select_recommendations(
        weak_topics=[weak],
        topic_masteries=masteries,
        available_questions=questions,
        attempted_question_ids={"UNI-RENAL-020"},
    )
    assert len(recs) >= 1
    top = recs[0]
    assert top.action == AdaptiveActionType.REVIEW_CONCEPT
    assert top.tutor_mode == "mechanistic_explanation"
