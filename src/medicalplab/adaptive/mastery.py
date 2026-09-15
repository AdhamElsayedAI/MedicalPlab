"""Mastery Tracking Engine for Phase 2A Adaptive Learning.

Provides an MVP deterministic mastery estimation model designed for future
drop-in replacement with Item Response Theory (IRT) or Bayesian Knowledge Tracing (BKT).
"""
from __future__ import annotations

from typing import Protocol, Sequence
from .models import (
    AttemptRecord,
    ConfidenceLevel,
    MasteryLevel,
    MasteryStatus,
    TopicMasteryRecord,
)


class BaseMasteryModel(Protocol):
    """Abstract protocol for mastery estimation algorithms."""

    def evaluate_topic(
        self,
        subject: str,
        topic: str,
        attempts: Sequence[AttemptRecord],
    ) -> TopicMasteryRecord:
        ...


class DeterministicMVPMasteryEngine:
    """Deterministic, explainable MVP mastery estimation engine.

    Calculates sample-size-calibrated mastery, recency weighting, and error streaks
    without requiring uncalibrated parameter fitting.
    """

    def __init__(
        self,
        needs_review_threshold: float = 0.60,
        mastered_threshold: float = 0.80,
        min_advanced_attempts: int = 5,
    ) -> None:
        self.needs_review_threshold = needs_review_threshold
        self.mastered_threshold = mastered_threshold
        self.min_advanced_attempts = min_advanced_attempts

    def evaluate_topic(
        self,
        subject: str,
        topic: str,
        attempts: Sequence[AttemptRecord],
    ) -> TopicMasteryRecord:
        """Evaluate mastery metrics for a single topic from its attempt sequence."""
        topic_clean = topic.strip()
        subject_clean = subject.strip()
        matched = [
            a for a in attempts
            if a.topic.strip().lower() == topic_clean.lower()
            and (not subject_clean or a.subject.strip().lower() == subject_clean.lower())
        ]

        total = len(matched)
        if total == 0:
            return TopicMasteryRecord(
                subject=subject_clean,
                topic=topic_clean,
                total_attempts=0,
                correct_attempts=0,
                accuracy=None,
                mastery_score=0.0,
                mastery_level=MasteryLevel.BEGINNER,
                mastery_status=MasteryStatus.NOT_STARTED,
                confidence=ConfidenceLevel.LOW,
                consecutive_errors=0,
                last_attempt_correct=None,
            )

        correct = sum(1 for a in matched if a.correct)
        raw_accuracy = round(correct / total, 4)

        # Recency weighting: Give progressive weight to the most recent attempts (up to last 5)
        recent_window = matched[-5:]
        if recent_window:
            weights = list(range(1, len(recent_window) + 1))
            weighted_correct = sum(w for w, a in zip(weights, recent_window) if a.correct)
            recent_accuracy = weighted_correct / sum(weights)
            # Combine 60% raw cumulative accuracy + 40% recent weighted accuracy
            mastery_score = round(0.60 * raw_accuracy + 0.40 * recent_accuracy, 4)
        else:
            mastery_score = raw_accuracy

        # Consecutive errors streak from most recent backwards
        consecutive_errors = 0
        for a in reversed(matched):
            if not a.correct:
                consecutive_errors += 1
            else:
                break

        last_attempt_correct = matched[-1].correct

        # 1. Mastery Level
        if raw_accuracy < 0.50:
            level = MasteryLevel.BEGINNER
        elif raw_accuracy < 0.70:
            level = MasteryLevel.DEVELOPING
        elif raw_accuracy < 0.85:
            level = MasteryLevel.PROFICIENT
        else:
            level = MasteryLevel.ADVANCED if total >= self.min_advanced_attempts else MasteryLevel.PROFICIENT

        # 2. Mastery Status
        if raw_accuracy < self.needs_review_threshold or consecutive_errors >= 2:
            status = MasteryStatus.NEEDS_REVIEW
        elif raw_accuracy < self.mastered_threshold:
            status = MasteryStatus.IN_PROGRESS
        else:
            status = MasteryStatus.MASTERED if consecutive_errors == 0 else MasteryStatus.IN_PROGRESS

        # 3. Confidence Level
        if total < 5:
            confidence = ConfidenceLevel.LOW
        elif total < 15:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.HIGH

        return TopicMasteryRecord(
            subject=subject_clean,
            topic=topic_clean,
            total_attempts=total,
            correct_attempts=correct,
            accuracy=raw_accuracy,
            mastery_score=mastery_score,
            mastery_level=level,
            mastery_status=status,
            confidence=confidence,
            consecutive_errors=consecutive_errors,
            last_attempt_correct=last_attempt_correct,
        )
