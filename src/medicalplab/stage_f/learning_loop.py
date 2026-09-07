"""Continuous adaptive Learning Loop manager for Stage-F.

Tracks and audits student mastery transitions before and after educational interventions,
closing the feedback loop across diagnostic assessments, study plans, and re-evaluations.
"""

import time
from typing import Sequence
import uuid

from medicalplab.stage_b.models import require, strings
from .models import LearningLoopCycle


MASTERY_RANKS = {
    "beginner": 0,
    "developing": 1,
    "proficient": 2,
    "advanced": 3,
}


class LearningLoopManager:
    """Manages iterative learning loops and measures educational intervention efficacy."""

    def __init__(self):
        self._active_cycles: dict[str, dict] = {}
        self._completed_cycles: list[LearningLoopCycle] = []

    def start_cycle(
        self,
        student_id: str,
        topic: str,
        initial_mastery: str,
    ) -> str:
        """Initiate a learning loop cycle prior to educational intervention."""
        strings(student_id, topic, initial_mastery)
        cycle_id = f"LOOP-{uuid.uuid4().hex[:8].upper()}"

        self._active_cycles[cycle_id] = {
            "student_id": student_id.strip(),
            "topic": topic.strip(),
            "initial_mastery": initial_mastery.strip().lower(),
            "started_at": time.time(),
        }
        return cycle_id

    def complete_cycle(
        self,
        cycle_id: str,
        interventions: Sequence[str],
        resulting_mastery: str,
    ) -> LearningLoopCycle:
        """Close a learning loop cycle, evaluate progress, and record audit trail."""
        require(cycle_id in self._active_cycles, f"Active loop cycle '{cycle_id}' not found")
        strings(resulting_mastery)
        require(isinstance(interventions, (list, tuple)), "interventions must be a sequence of strings")

        data = self._active_cycles.pop(cycle_id)
        initial = data["initial_mastery"]
        result = resulting_mastery.strip().lower()

        initial_rank = MASTERY_RANKS.get(initial, 0)
        result_rank = MASTERY_RANKS.get(result, 0)
        improved = result_rank > initial_rank

        record = LearningLoopCycle(
            cycle_id=cycle_id,
            student_id=data["student_id"],
            topic=data["topic"],
            initial_mastery=initial,
            interventions_applied=tuple(interventions),
            resulting_mastery=result,
            mastery_improved=improved,
            timestamp=time.time(),
        )
        self._completed_cycles.append(record)
        return record

    def recommend_next_step(self, cycle: LearningLoopCycle) -> str:
        """Recommend adaptive next action based on learning loop outcome."""
        if cycle.mastery_improved:
            return (
                f"Mastery improved for {cycle.topic} ({cycle.initial_mastery} -> {cycle.resulting_mastery}). "
                "Advance to higher-difficulty practice and adjacent clinical curriculum topics."
            )
        else:
            return (
                f"Mastery unchanged for {cycle.topic} ({cycle.initial_mastery}). "
                "Switch intervention strategy: review primary guideline principles in Stage-D Teaching mode "
                "before re-attempting assessments."
            )
