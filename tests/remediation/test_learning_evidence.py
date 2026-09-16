"""Tests for Phase 2A Learning Evidence Adapter and zero mastery inflation invariants."""
from unittest.mock import MagicMock
import pytest

from medicalplab.adaptive.models import AdaptiveActionType, AdaptiveRecommendation, WeaknessPriority
from medicalplab.adaptive.service import AdaptiveLearningService
from medicalplab.remediation.learning_evidence import LearningEvidenceAdapter
from medicalplab.remediation.models import (
    RemediationOutcome,
    TransferAttempt,
)


def test_transfer_confirmed_emits_positive_attempt():
    mock_adaptive = MagicMock(spec=AdaptiveLearningService)
    mock_adaptive.get_top_recommendation.return_value = AdaptiveRecommendation(
        recommendation_id="REC-TEST-01",
        action=AdaptiveActionType.SOLVE_TARGETED_QUESTION,
        subject="Renal physiology",
        topic="RAAS mechanisms",
        priority=WeaknessPriority.LOW,
        reason="Progressing well",
        explanation="Concept demonstrated on transfer test",
    )

    adapter = LearningEvidenceAdapter(adaptive_service=mock_adaptive)
    attempt = TransferAttempt(
        question_id="UNI-RENAL-001-T",
        submitted_option="A",
        is_correct=True,
        was_assisted=False,
    )

    q_event, rec = adapter.record_qualified_outcome(
        learner_id="test_learner_01",
        session_id="REM-SESSION-001",
        original_question_id="UNI-RENAL-001",
        topic="RAAS mechanisms",
        subject="Renal physiology",
        outcome=RemediationOutcome.TRANSFER_CONFIRMED,
        transfer_attempt=attempt,
    )

    assert q_event.is_transfer_confirmed is True
    assert q_event.was_assisted is False
    assert mock_adaptive.record_learning_event.call_count == 1
    call_event = mock_adaptive.record_learning_event.call_args[0][0]
    assert call_event.event_type == "QUESTION_ATTEMPT"
    assert call_event.question_id == "UNI-RENAL-001-T"
    assert call_event.is_correct is True
    assert rec is not None


def test_assisted_attempt_emits_non_evaluative_event():
    """INVARIANT: Assisted success must not emit positive attempt or inflate mastery."""
    mock_adaptive = MagicMock(spec=AdaptiveLearningService)
    mock_adaptive.get_top_recommendation.return_value = None

    adapter = LearningEvidenceAdapter(adaptive_service=mock_adaptive)
    attempt = TransferAttempt(
        question_id="UNI-RENAL-001-T",
        submitted_option="A",
        is_correct=True,
        was_assisted=True,
    )

    q_event, rec = adapter.record_qualified_outcome(
        learner_id="test_learner_02",
        session_id="REM-SESSION-002",
        original_question_id="UNI-RENAL-001",
        topic="RAAS mechanisms",
        subject="Renal physiology",
        outcome=RemediationOutcome.UNRESOLVED,
        transfer_attempt=attempt,
    )

    assert q_event.is_transfer_confirmed is False
    assert q_event.was_assisted is True
    assert mock_adaptive.record_learning_event.call_count == 1
    call_event = mock_adaptive.record_learning_event.call_args[0][0]
    # Must be TUTOR_INTERVENTION, NOT QUESTION_ATTEMPT
    assert call_event.event_type == "TUTOR_INTERVENTION"
    assert call_event.is_correct is None  # Does not alter mastery


def test_abandoned_session_emits_non_evaluative_event():
    mock_adaptive = MagicMock(spec=AdaptiveLearningService)
    adapter = LearningEvidenceAdapter(adaptive_service=mock_adaptive)

    q_event, rec = adapter.record_qualified_outcome(
        learner_id="test_learner_03",
        session_id="REM-SESSION-003",
        original_question_id="UNI-RENAL-001",
        topic="RAAS mechanisms",
        subject="Renal physiology",
        outcome=RemediationOutcome.ABANDONED,
        transfer_attempt=None,
    )

    assert q_event.outcome == RemediationOutcome.ABANDONED
    assert mock_adaptive.record_learning_event.call_count == 1
    call_event = mock_adaptive.record_learning_event.call_args[0][0]
    assert call_event.event_type == "TUTOR_INTERVENTION"
    assert call_event.is_correct is None
