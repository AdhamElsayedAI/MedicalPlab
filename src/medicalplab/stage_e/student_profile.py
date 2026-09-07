"""Student profile lifecycle and intelligence state management for Stage-E.

Manages student profiles, updates mastery metrics deterministically, and aggregates overall learning levels.
"""

from collections import defaultdict
import time
from typing import Sequence

from medicalplab.stage_b.models import require, strings
from .models import (
    MasteryLevel,
    QuestionAttempt,
    StudentProfile,
    TopicMastery,
)
from .performance_tracker import (
    calculate_topic_mastery,
    detect_weak_topics,
    determine_mastery_level,
)


def create_initial_profile(
    student_id: str,
    created_at: float | None = None,
) -> StudentProfile:
    """Instantiate a new, blank student profile."""
    strings(student_id)
    return StudentProfile(
        student_id=student_id.strip(),
        created_at=created_at if created_at is not None else time.time(),
        topics=(),
        mastery_scores=(),
        weak_topics=(),
        learning_level=MasteryLevel.BEGINNER,
    )


def calculate_aggregate_learning_level(masteries: Sequence[TopicMastery]) -> MasteryLevel:
    """Determine the student's overall curriculum mastery level."""
    active = [m for m in masteries if m.total_attempts > 0]
    if not active:
        return MasteryLevel.BEGINNER

    total_attempts = sum(m.total_attempts for m in active)
    total_correct = sum(m.correct_attempts for m in active)
    aggregate_accuracy = total_correct / total_attempts

    return determine_mastery_level(aggregate_accuracy, total_attempts)


def update_student_profile(
    profile: StudentProfile,
    attempts: Sequence[QuestionAttempt],
    weak_threshold: float = 0.60,
) -> StudentProfile:
    """Update a student profile with a batch of question attempts.
    
    Recomputes topic mastery scores, weak topics, and aggregate learning level.
    """
    require(isinstance(profile, StudentProfile), "profile must be a StudentProfile instance")
    require(
        isinstance(attempts, (list, tuple)),
        "attempts must be a sequence of QuestionAttempt",
    )
    for a in attempts:
        require(isinstance(a, QuestionAttempt), "All items must be QuestionAttempt instances")

    if not attempts:
        return profile

    # Group all attempts by topic (case-insensitive key, preserving clean display name)
    attempts_by_topic: dict[str, list[QuestionAttempt]] = defaultdict(list)
    topic_display_names: dict[str, str] = {}

    for a in attempts:
        key = a.topic.strip().lower()
        attempts_by_topic[key].append(a)
        if key not in topic_display_names:
            topic_display_names[key] = a.topic.strip()

    # Calculate mastery for each topic present in attempts
    mastery_map: dict[str, TopicMastery] = {}
    for key, topic_attempts in attempts_by_topic.items():
        canonical_name = topic_display_names[key]
        mastery_map[key] = calculate_topic_mastery(topic_attempts, canonical_name)

    # Sort topics alphabetically
    sorted_keys = sorted(mastery_map.keys())
    topics_tuple = tuple(topic_display_names[k] for k in sorted_keys)
    mastery_tuple = tuple(mastery_map[k] for k in sorted_keys)

    # Detect weak topics
    weak_topics = detect_weak_topics(mastery_tuple, threshold=weak_threshold)

    # Compute overall learning level
    overall_level = calculate_aggregate_learning_level(mastery_tuple)

    return StudentProfile(
        student_id=profile.student_id,
        created_at=profile.created_at,
        topics=topics_tuple,
        mastery_scores=mastery_tuple,
        weak_topics=weak_topics,
        learning_level=overall_level,
    )
