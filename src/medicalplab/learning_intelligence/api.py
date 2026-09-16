"""FastAPI Router for Phase 3 Learning Intelligence / Reasoning-Gap Radar.

Read-only educator intelligence API.
"""
from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from medicalplab.learning_intelligence.aggregation import (
    ReasoningGapAggregator,
)
from medicalplab.learning_intelligence.demo_data import DEMO_COHORT_ID
from medicalplab.learning_intelligence.models import ReasoningGapRadarResponse
from medicalplab.learning_intelligence.repository import (
    DemoCohortDisabledError,
    LearningIntelligenceRepository,
    UnknownCohortError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/learning-intelligence",
    tags=["learning-intelligence"],
)

_aggregator: Optional[ReasoningGapAggregator] = None


def get_aggregator() -> ReasoningGapAggregator:
    global _aggregator
    if _aggregator is None:
        repo = LearningIntelligenceRepository()
        _aggregator = ReasoningGapAggregator(repository=repo)
    return _aggregator


@router.get("/reasoning-gaps", response_model=ReasoningGapRadarResponse)
def get_reasoning_gap_radar(
    cohort_id: str = Query(
        default=DEMO_COHORT_ID,
        description="Cohort identifier. Defaults to the deterministic demo cohort.",
    ),
    topic: Optional[str] = Query(
        default=None,
        description="Optional clinical topic filter (e.g. 'preclinical_renal').",
    ),
    subject: Optional[str] = Query(
        default=None,
        description="Optional subject area filter.",
    ),
) -> ReasoningGapRadarResponse:
    """Derive deterministic cross-learner reasoning-gap radar for educators.

    CRITICAL INVARIANTS:
    - Never leaks individual student names, emails, or IDs.
    - Suppresses aggregate breakdown if cohort unique learners < MIN_COHORT_N (server-enforced >= 3).
    - Caller CANNOT override or lower MIN_COHORT_N via query parameter.
    - Strictly excludes assisted transfer from qualified independent transfer counts and rates.
    - Modest epistemic language only ('POSSIBLE_PATTERN').
    - Rejects unknown cohort IDs with 404.
    - Blocks demo cohort in production without explicit configuration with 403.
    """
    aggregator = get_aggregator()
    try:
        return aggregator.aggregate_cohort(
            cohort_id=cohort_id,
            topic=topic,
            subject=subject,
        )
    except UnknownCohortError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DemoCohortDisabledError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
