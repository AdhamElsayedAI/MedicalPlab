"""Data models for MedicalPlab Phase 3 Learning Intelligence / Reasoning-Gap Radar.

Strictly enforces epistemic modesty:
- Labels gaps as 'POSSIBLE_PATTERN' or 'Possible shared reasoning gap'.
- Zero diagnostic certainty or misconception claims.
- Zero learner-identifying row leakage.
"""
from __future__ import annotations

import time
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DataSufficiencyStatus(str, Enum):
    """Cohort data sufficiency status based on MIN_COHORT_N threshold."""
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT_COHORT_DATA = "INSUFFICIENT_COHORT_DATA"


class EvidenceSummaryItem(BaseModel):
    """Safe, verified clinical/scientific evidence reference summary."""
    document_id: str
    chunk_id: Optional[str] = None
    title: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None


class TransferEffectivenessMetrics(BaseModel):
    """Deterministic transfer metrics.

    CRITICAL INVARIANTS:
    1. qualified_independent_transfer_count = transfer_attempted_count - assisted_excluded_count
    2. Assisted/disqualified attempts are excluded from BOTH numerator AND denominator of transfer_demonstration_rate.
    3. transfer_demonstration_rate = transfer_demonstrated_count / qualified_independent_transfer_count (or None if qualified == 0).
    """
    transfer_attempted_count: int = 0
    qualified_independent_transfer_count: int = 0
    transfer_demonstrated_count: int = 0
    transfer_not_demonstrated_count: int = 0
    assisted_excluded_count: int = 0
    transfer_demonstration_rate: Optional[float] = None


class ReasoningGapAggregate(BaseModel):
    """Aggregate metric for a specific observed reasoning-pattern signal across a cohort."""
    pattern_id: str
    category: str
    reasoning_pattern: str
    epistemic_status: str = Field(
        default="POSSIBLE_PATTERN",
        description="Epistemic status; always modest ('POSSIBLE_PATTERN'). Never 'CONFIRMED' or 'DIAGNOSED'."
    )
    unique_learners_count: int = Field(
        description="Number of distinct learners exhibiting this possible reasoning pattern."
    )
    pattern_learner_count: int = Field(
        default=0,
        description="Number of distinct learners exhibiting this possible reasoning pattern."
    )
    sessions_count: int = Field(
        description="Total completed remediation sessions associated with this pattern."
    )
    prevalence_rate: float = Field(
        description="Ratio of unique learners exhibiting this pattern to total eligible cohort learners."
    )
    transfer_metrics: TransferEffectivenessMetrics
    evidence_references: List[EvidenceSummaryItem] = Field(default_factory=list)


class ReasoningGapRadarResponse(BaseModel):
    """Top-level response payload for the Educator Reasoning-Gap Radar view."""
    cohort_id: str
    cohort_name: str
    topic: Optional[str] = None
    subject: Optional[str] = None
    sufficiency_status: DataSufficiencyStatus
    min_cohort_n: int = 3
    total_eligible_learners: int = 0
    total_eligible_sessions: int = 0
    reasoning_gaps: List[ReasoningGapAggregate] = Field(default_factory=list)
    overall_transfer_effectiveness: TransferEffectivenessMetrics = Field(
        default_factory=TransferEffectivenessMetrics
    )
    is_demo_data: bool = False
    demo_disclaimer: Optional[str] = None
    generated_at: float = Field(default_factory=time.time)
