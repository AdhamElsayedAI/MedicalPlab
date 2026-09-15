"""Weakness Detection Engine for Phase 2A Adaptive Learning.

Detects student knowledge gaps, repeated mistake patterns, and assigns
deterministic priorities (HIGH, MEDIUM, LOW) with transparent educational explanations.
"""
from __future__ import annotations

from typing import Mapping, Sequence
from .models import (
    AttemptRecord,
    TopicMasteryRecord,
    WeakTopicRecord,
    WeaknessPriority,
)


class WeaknessDetectionEngine:
    """Identifies and prioritizes learning deficits from topic masteries and attempt history."""

    def __init__(
        self,
        high_priority_accuracy_threshold: float = 0.40,
        medium_priority_accuracy_threshold: float = 0.60,
    ) -> None:
        self.high_thresh = high_priority_accuracy_threshold
        self.medium_thresh = medium_priority_accuracy_threshold

    def detect_weaknesses(
        self,
        masteries: Mapping[str, TopicMasteryRecord] | Sequence[TopicMasteryRecord],
        attempts: Sequence[AttemptRecord] | None = None,
    ) -> list[WeakTopicRecord]:
        """Analyze topic mastery metrics and extract prioritized weaknesses."""
        records: list[TopicMasteryRecord] = (
            list(masteries.values()) if isinstance(masteries, dict) else list(masteries)
        )

        weak_topics: list[WeakTopicRecord] = []

        for m in records:
            if m.total_attempts == 0 or m.accuracy is None:
                continue

            # Candidate for weakness if accuracy < medium threshold or consecutive errors >= 2
            is_weak = (m.accuracy < self.medium_thresh) or (m.consecutive_errors >= 2)
            if not is_weak:
                continue

            missed = m.total_attempts - m.correct_attempts
            failure_rate = round(missed / m.total_attempts, 4)

            # Determine Priority
            if m.accuracy < self.high_thresh or m.consecutive_errors >= 2 or (m.total_attempts >= 4 and m.accuracy < 0.50):
                priority = WeaknessPriority.HIGH
            elif m.accuracy < self.medium_thresh:
                priority = WeaknessPriority.MEDIUM
            else:
                priority = WeaknessPriority.LOW

            # Synthesize explainable reason
            if m.consecutive_errors >= 2:
                reason = (
                    f"Missed {missed} of {m.total_attempts} attempts on {m.topic} "
                    f"({int(round(m.accuracy * 100))}% accuracy) with {m.consecutive_errors} consecutive recent errors."
                )
            else:
                reason = (
                    f"Performance in {m.topic} is below benchmark ({int(round(m.accuracy * 100))}% accuracy, "
                    f"{missed}/{m.total_attempts} missed)."
                )

            weak_topics.append(
                WeakTopicRecord(
                    subject=m.subject,
                    topic=m.topic,
                    priority=priority,
                    failure_rate=failure_rate,
                    missed_count=missed,
                    total_attempts=m.total_attempts,
                    consecutive_errors=m.consecutive_errors,
                    reason=reason,
                )
            )

        # Sort: HIGH -> MEDIUM -> LOW, then highest failure rate, then highest attempts, then topic name
        priority_rank = {
            WeaknessPriority.HIGH: 0,
            WeaknessPriority.MEDIUM: 1,
            WeaknessPriority.LOW: 2,
        }
        weak_topics.sort(
            key=lambda w: (
                priority_rank[w.priority],
                -w.failure_rate,
                -w.consecutive_errors,
                -w.total_attempts,
                w.topic,
            )
        )

        return weak_topics
