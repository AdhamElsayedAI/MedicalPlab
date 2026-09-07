"""Adaptive difficulty engine for Stage-F.

Determines optimal pedagogical difficulty (EASY, MEDIUM, HARD) deterministically
using accuracy, mastery level, recent performance, and topic sample confidence.
"""

from typing import Tuple

from medicalplab.stage_b.models import require
from .models import PlatformDifficulty


class AdaptiveDifficultyEngine:
    """Deterministic calibrator for educational question/case difficulty."""

    def determine_difficulty(
        self,
        accuracy: float,
        mastery_level: str,
        recent_accuracy: float | None = None,
        confidence_level: str | None = None,
    ) -> Tuple[PlatformDifficulty, str]:
        """Calibrate difficulty level deterministically with an explainable justification."""
        require(
            isinstance(accuracy, (int, float)) and 0.0 <= accuracy <= 1.0,
            "'accuracy' must be between 0.0 and 1.0",
        )
        mastery_clean = str(mastery_level).strip().lower()
        confidence_clean = str(confidence_level).strip().lower() if confidence_level else "medium"

        if recent_accuracy is not None:
            require(
                isinstance(recent_accuracy, (int, float)) and 0.0 <= recent_accuracy <= 1.0,
                "'recent_accuracy' must be between 0.0 and 1.0",
            )
            effective_acc = 0.40 * accuracy + 0.60 * float(recent_accuracy)
        else:
            effective_acc = float(accuracy)

        # 1. Base difficulty assignment based on mastery and effective accuracy
        if mastery_clean == "beginner" or effective_acc < 0.50:
            difficulty = PlatformDifficulty.EASY
        elif mastery_clean == "developing" or effective_acc < 0.75:
            difficulty = PlatformDifficulty.MEDIUM
        else:
            difficulty = PlatformDifficulty.HARD

        # 2. Safety / Confidence guards
        # If confidence is LOW (few sample attempts), never assign HARD difficulty
        if confidence_clean == "low" and difficulty == PlatformDifficulty.HARD:
            difficulty = PlatformDifficulty.MEDIUM

        # If recent performance was very low (< 0.40), step down difficulty
        if recent_accuracy is not None and recent_accuracy < 0.40:
            difficulty = PlatformDifficulty.EASY

        # 3. Formulate explainable justification
        recent_str = f", recent accuracy: {int(recent_accuracy * 100)}%" if recent_accuracy is not None else ""
        reason = (
            f"Selected {difficulty.value.upper()} difficulty (Mastery: {mastery_clean}, "
            f"overall accuracy: {int(accuracy * 100)}%{recent_str}, confidence: {confidence_clean})."
        )

        return difficulty, reason
