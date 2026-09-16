"""Deterministic aggregation engine for Phase 3 Learning Intelligence / Reasoning-Gap Radar.

CORE PRINCIPLES:
1. Strict Epistemic Modesty:
   - Labels all signals as 'POSSIBLE_PATTERN' or 'Possible shared reasoning gap'.
   - Never converts a hypothesis into a confirmed or diagnosed misconception.
2. Honest Denominators:
   - Uses UNIQUE LEARNERS for prevalence rates (e.g. "X of Y eligible learners").
   - Explicitly reports sessions_count alongside unique_learners_count.
3. Qualified Transfer Integrity:
   - Assisted or disqualified transfer attempts are strictly excluded from positive
     demonstrated transfer counts and accounted for in assisted_excluded_count.
4. Privacy & Small-N Suppression:
   - MIN_COHORT_N = 3. Suppresses aggregate rows if cohort < 3 unique learners.
   - Zero raw learner IDs or personal names exposed in returned payloads.
5. Invariant Exclusions:
   - SAFETY_FALLBACK sessions excluded from reasoning-gap pattern signals.
   - INSUFFICIENT_EVIDENCE sessions excluded from pattern assertions.
   - Incomplete / abandoned sessions excluded.
"""
from __future__ import annotations

import logging
import os
from collections import defaultdict
from typing import Dict, List, Optional, Set

from medicalplab.learning_intelligence.demo_data import (
    DEMO_COHORT_ID,
    DEMO_COHORT_NAME,
    DEMO_DISCLAIMER,
)
from medicalplab.learning_intelligence.models import (
    DataSufficiencyStatus,
    EvidenceSummaryItem,
    ReasoningGapAggregate,
    ReasoningGapRadarResponse,
    TransferEffectivenessMetrics,
)
from medicalplab.learning_intelligence.repository import LearningIntelligenceRepository
from medicalplab.remediation.models import (
    DetectionStatus,
    RemediationLifecycleState,
    RemediationOutcome,
    RemediationSessionState,
)

logger = logging.getLogger(__name__)

DEFAULT_MIN_COHORT_N = 3
MIN_COHORT_N_ENV_VAR = "MEDICALPLAB_PHASE_3_MIN_COHORT_N"


def get_min_cohort_n() -> int:
    """Resolve server-side minimum cohort size threshold for privacy suppression.

    Defaults to 3. If configured via environment variable, enforces value >= 3.
    Fails safely back to 3 if invalid or if value < 3.
    """
    raw = os.getenv(MIN_COHORT_N_ENV_VAR)
    if raw is not None:
        try:
            val = int(raw.strip())
            if val >= 3:
                return val
            logger.warning(
                "Configured %s=%s is below safe minimum 3. Enforcing threshold 3.",
                MIN_COHORT_N_ENV_VAR,
                raw,
            )
            return 3
        except (ValueError, TypeError):
            logger.warning(
                "Could not parse %s=%s as int. Defaulting to 3.",
                MIN_COHORT_N_ENV_VAR,
                raw,
            )
            return 3
    return DEFAULT_MIN_COHORT_N


MIN_COHORT_N = DEFAULT_MIN_COHORT_N


def is_session_eligible(session: RemediationSessionState) -> bool:
    """Check if a session represents an eligible learning signal for radar aggregation."""
    # 1. Must be a completed lifecycle
    if session.lifecycle_state != RemediationLifecycleState.COMPLETED:
        return False
    if not session.is_complete:
        return False

    # 2. Exclude SAFETY_FALLBACK
    if session.outcome == RemediationOutcome.SAFETY_FALLBACK:
        return False
    if session.timeline and session.timeline.status == "SAFETY_FALLBACK":
        return False

    # 3. Exclude INSUFFICIENT_EVIDENCE detection status
    if session.hypothesis and session.hypothesis.detection_status == DetectionStatus.INSUFFICIENT_EVIDENCE:
        return False
    if session.detected_gap and getattr(session.detected_gap, "is_fallback", False):
        return False

    # 4. Must have a valid detected gap and pattern_id
    if not session.detected_gap or not session.detected_gap.pattern_id:
        return False

    return True


class ReasoningGapAggregator:
    """Aggregates multi-learner Phase 2B remediation sessions into educator radar metrics."""

    def __init__(self, repository: Optional[LearningIntelligenceRepository] = None) -> None:
        self.repo = repository or LearningIntelligenceRepository()

    def aggregate_cohort(
        self,
        cohort_id: str = DEMO_COHORT_ID,
        topic: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> ReasoningGapRadarResponse:
        """Derive deterministic cross-learner reasoning-gap radar for the specified cohort."""
        raw_sessions, is_demo = self.repo.get_cohort_sessions(cohort_id, topic=topic, subject=subject)

        # 1. Filter to strictly eligible sessions
        eligible_sessions = [s for s in raw_sessions if is_session_eligible(s)]

        # 2. Calculate unique eligible learners
        eligible_learners: Set[str] = {s.user_id for s in eligible_sessions if s.user_id}
        total_learners = len(eligible_learners)
        total_sessions = len(eligible_sessions)

        cohort_name = DEMO_COHORT_NAME if is_demo else f"Cohort {cohort_id}"
        disclaimer = DEMO_DISCLAIMER if is_demo else None

        # Server-side MIN_COHORT_N enforcement (caller cannot override or lower below 3)
        min_cohort_n = get_min_cohort_n()

        # 3. Privacy / Small-N check
        if total_learners < min_cohort_n:
            return ReasoningGapRadarResponse(
                cohort_id=cohort_id,
                cohort_name=cohort_name,
                topic=topic,
                subject=subject,
                sufficiency_status=DataSufficiencyStatus.INSUFFICIENT_COHORT_DATA,
                min_cohort_n=min_cohort_n,
                total_eligible_learners=total_learners,
                total_eligible_sessions=total_sessions,
                reasoning_gaps=[],
                overall_transfer_effectiveness=TransferEffectivenessMetrics(),
                is_demo_data=is_demo,
                demo_disclaimer=disclaimer,
            )

        # 4. Group by pattern_id
        pattern_sessions: Dict[str, List[RemediationSessionState]] = defaultdict(list)
        for s in eligible_sessions:
            pid = s.detected_gap.pattern_id
            pattern_sessions[pid].append(s)

        gap_aggregates: List[ReasoningGapAggregate] = []

        overall_attempted = 0
        overall_demonstrated = 0
        overall_not_demonstrated = 0
        overall_assisted_excluded = 0

        # Sort patterns deterministically by learner prevalence descending, then pattern_id
        sorted_patterns = sorted(
            pattern_sessions.keys(),
            key=lambda p: (len({s.user_id for s in pattern_sessions[p]}), len(pattern_sessions[p]), p),
            reverse=True,
        )

        for pid in sorted_patterns:
            p_sessions = pattern_sessions[pid]
            first_gap = p_sessions[0].detected_gap

            p_unique_learners = {s.user_id for s in p_sessions}
            unique_count = len(p_unique_learners)
            sessions_count = len(p_sessions)
            prevalence = round(unique_count / total_learners, 4) if total_learners > 0 else 0.0

            # Transfer metrics for this pattern
            p_attempted = 0
            p_demonstrated = 0
            p_not_demonstrated = 0
            p_assisted_excluded = 0

            evidence_refs_set: Set[str] = set()

            for s in p_sessions:
                # Collect evidence references from detected_gap and verified turn citations
                if s.detected_gap.evidence_references:
                    evidence_refs_set.update(s.detected_gap.evidence_references)
                for turn in s.turns:
                    for cit in turn.citations:
                        cid = cit.get("chunk_id") or cit.get("document_id")
                        if cid:
                            evidence_refs_set.add(cid)

                # Transfer evaluation
                if s.transfer_attempt:
                    p_attempted += 1
                    t_att = s.transfer_attempt

                    # Check if assisted or assistance invoked
                    is_assisted = t_att.was_assisted or s.assistance_invoked
                    if is_assisted:
                        p_assisted_excluded += 1
                        # Excluded from both numerator and denominator of qualified independent transfer
                    elif t_att.is_correct or s.outcome == RemediationOutcome.TRANSFER_CONFIRMED:
                        p_demonstrated += 1
                    else:
                        p_not_demonstrated += 1

            # FIX 2: Define qualified independent transfer attempts:
            # qualified_independent_transfer_count = submitted held-out transfer attempts MINUS assisted/disqualified attempts
            p_qualified = p_attempted - p_assisted_excluded
            # If qualified_independent_transfer_count == 0, transfer_demonstration_rate is None (no misleading percentage)
            t_rate = round(p_demonstrated / p_qualified, 4) if p_qualified > 0 else None

            # FIX 5: Deduplicate and resolve genuine evidence only; never fabricate or return safety fallback citations
            resolved_evidence: List[EvidenceSummaryItem] = []
            seen_evidence_keys: Set[tuple[str, Optional[str]]] = set()
            for ref in sorted(evidence_refs_set):
                item = self.repo.resolve_evidence(ref)
                if item:
                    key = (item.document_id, item.chunk_id)
                    if key not in seen_evidence_keys:
                        seen_evidence_keys.add(key)
                        resolved_evidence.append(item)

            transfer_metrics = TransferEffectivenessMetrics(
                transfer_attempted_count=p_attempted,
                qualified_independent_transfer_count=p_qualified,
                transfer_demonstrated_count=p_demonstrated,
                transfer_not_demonstrated_count=p_not_demonstrated,
                assisted_excluded_count=p_assisted_excluded,
                transfer_demonstration_rate=t_rate,
            )

            gap_aggregates.append(ReasoningGapAggregate(
                pattern_id=pid,
                category=first_gap.category.value if hasattr(first_gap.category, "value") else str(first_gap.category),
                reasoning_pattern=first_gap.reasoning_pattern,
                epistemic_status="POSSIBLE_PATTERN",
                unique_learners_count=unique_count,
                pattern_learner_count=unique_count,
                sessions_count=sessions_count,
                prevalence_rate=prevalence,
                transfer_metrics=transfer_metrics,
                evidence_references=resolved_evidence,
            ))

            overall_attempted += p_attempted
            overall_demonstrated += p_demonstrated
            overall_not_demonstrated += p_not_demonstrated
            overall_assisted_excluded += p_assisted_excluded

        overall_qualified = overall_attempted - overall_assisted_excluded
        overall_rate = round(overall_demonstrated / overall_qualified, 4) if overall_qualified > 0 else None
        overall_transfer = TransferEffectivenessMetrics(
            transfer_attempted_count=overall_attempted,
            qualified_independent_transfer_count=overall_qualified,
            transfer_demonstrated_count=overall_demonstrated,
            transfer_not_demonstrated_count=overall_not_demonstrated,
            assisted_excluded_count=overall_assisted_excluded,
            transfer_demonstration_rate=overall_rate,
        )

        return ReasoningGapRadarResponse(
            cohort_id=cohort_id,
            cohort_name=cohort_name,
            topic=topic,
            subject=subject,
            sufficiency_status=DataSufficiencyStatus.SUFFICIENT,
            min_cohort_n=min_cohort_n,
            total_eligible_learners=total_learners,
            total_eligible_sessions=total_sessions,
            reasoning_gaps=gap_aggregates,
            overall_transfer_effectiveness=overall_transfer,
            is_demo_data=is_demo,
            demo_disclaimer=disclaimer,
        )
