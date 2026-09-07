"""Deterministic performance and mastery tracking engine for Stage-E.

All calculations are strictly algorithmic and reproducible with zero non-deterministic or LLM evaluation.
"""

from collections import defaultdict
from typing import Sequence

from medicalplab.stage_b.models import require
from .models import (
    ConfidenceLevel,
    KnowledgeGap,
    MasteryLevel,
    QuestionAttempt,
    TopicMastery,
)


def calculate_accuracy(attempts: Sequence[QuestionAttempt]) -> float:
    """Calculate deterministic percentage of correct attempts. Returns 0.0 for empty sequences."""
    if not attempts:
        return 0.0
    correct = sum(1 for a in attempts if a.correct)
    return round(correct / len(attempts), 4)


def determine_mastery_level(accuracy: float, total_attempts: int) -> MasteryLevel:
    """Map accuracy and sample size to a deterministic MasteryLevel."""
    if total_attempts == 0 or accuracy < 0.50:
        return MasteryLevel.BEGINNER
    elif accuracy < 0.70:
        return MasteryLevel.DEVELOPING
    elif accuracy < 0.85:
        return MasteryLevel.PROFICIENT
    else:
        # Require at least 5 attempts to reach ADVANCED
        return MasteryLevel.ADVANCED if total_attempts >= 5 else MasteryLevel.PROFICIENT


def determine_confidence_level(total_attempts: int) -> ConfidenceLevel:
    """Map sample size to statistical confidence."""
    if total_attempts < 5:
        return ConfidenceLevel.LOW
    elif total_attempts < 15:
        return ConfidenceLevel.MEDIUM
    else:
        return ConfidenceLevel.HIGH


def calculate_topic_mastery(
    attempts: Sequence[QuestionAttempt],
    topic: str,
) -> TopicMastery:
    """Calculate deterministic mastery statistics for a given topic."""
    require(isinstance(topic, str) and topic.strip(), "topic must be a non-empty string")
    
    topic_clean = topic.strip()
    topic_attempts = [a for a in attempts if a.topic.strip().lower() == topic_clean.lower()]
    total = len(topic_attempts)

    if total == 0:
        return TopicMastery(
            topic=topic_clean,
            total_attempts=0,
            correct_attempts=0,
            accuracy=0.0,
            mastery_level=MasteryLevel.BEGINNER,
            confidence_level=ConfidenceLevel.LOW,
        )

    correct = sum(1 for a in topic_attempts if a.correct)
    accuracy = round(correct / total, 4)
    mastery = determine_mastery_level(accuracy, total)
    confidence = determine_confidence_level(total)

    return TopicMastery(
        topic=topic_clean,
        total_attempts=total,
        correct_attempts=correct,
        accuracy=accuracy,
        mastery_level=mastery,
        confidence_level=confidence,
    )


def detect_weak_topics(
    masteries: Sequence[TopicMastery],
    threshold: float = 0.60,
) -> tuple[str, ...]:
    """Identify weak topics where accuracy is below threshold, ordered from lowest to highest accuracy."""
    weak = [
        m for m in masteries
        if m.total_attempts > 0 and m.accuracy < threshold
    ]
    # Sort weakest first
    weak.sort(key=lambda m: (m.accuracy, -m.total_attempts))
    return tuple(m.topic for m in weak)


def detect_learning_gaps(
    attempts: Sequence[QuestionAttempt],
    min_attempts: int = 1,
    threshold: float = 0.60,
) -> tuple[KnowledgeGap, ...]:
    """Detect and rank knowledge gaps with explicit mathematical explainability."""
    grouped = defaultdict(list)
    for a in attempts:
        grouped[a.topic.strip()].append(a)

    gaps = []
    for topic, topic_attempts in grouped.items():
        total = len(topic_attempts)
        if total < min_attempts:
            continue

        correct = sum(1 for a in topic_attempts if a.correct)
        accuracy = round(correct / total, 4)

        if accuracy < threshold:
            gap_score = round(1.0 - accuracy, 4)
            incorrect = total - correct
            incorrect_pct = int(round((incorrect / total) * 100))
            reason = (
                f"The student answered {incorrect_pct}% of {topic} questions "
                f"incorrectly ({incorrect}/{total} attempts)."
            )
            gaps.append(
                KnowledgeGap(
                    topic=topic,
                    gap_score=gap_score,
                    reason=reason,
                )
            )

    # Sort gaps from highest gap_score to lowest
    gaps.sort(key=lambda g: -g.gap_score)
    return tuple(gaps)
