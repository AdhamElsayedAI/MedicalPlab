"""Focused regression test suite for Phase 3 Reasoning-Gap Aggregator.

Verifies:
1. Deterministic aggregate counts
2. Unique learner denominator correctness
3. Pattern grouping correctness
4. Assisted transfer excluded from demonstrated transfer
5. SAFETY_FALLBACK excluded
6. INSUFFICIENT_EVIDENCE excluded from asserted pattern counts
7. Small-N suppression (MIN_COHORT_N = 3)
8. No raw learner identity leakage
9. Reload / read idempotency
10. Malformed/incomplete records fail safely
11. Demo fixtures clearly identified as demo
12. Existing Phase 2B data is never mutated by read aggregation
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import pytest

from medicalplab.learning_intelligence.aggregation import (
    MIN_COHORT_N,
    ReasoningGapAggregator,
    is_session_eligible,
)
from medicalplab.learning_intelligence.demo_data import (
    DEMO_COHORT_ID,
    DEMO_COHORT_NAME,
    DEMO_DISCLAIMER,
    get_demo_sessions,
)
from medicalplab.learning_intelligence.models import (
    DataSufficiencyStatus,
    ReasoningGapRadarResponse,
)
from medicalplab.learning_intelligence.repository import LearningIntelligenceRepository
from medicalplab.remediation.models import (
    DetectedLearningGap,
    ReasoningPatternCategory,
    ReasoningTimelineItem,
    RemediationLifecycleState,
    RemediationOutcome,
    RemediationSessionState,
    RemediationStatus,
    SocraticStrategyType,
    TransferAttempt,
)


@pytest.fixture
def repo():
    return LearningIntelligenceRepository()


@pytest.fixture
def aggregator(repo):
    return ReasoningGapAggregator(repository=repo)


def test_demo_cohort_deterministic_counts_and_denominators(aggregator):
    """Verify deterministic aggregate counts and unique learner denominators on demo cohort."""
    resp = aggregator.aggregate_cohort(cohort_id=DEMO_COHORT_ID)

    assert resp.cohort_id == DEMO_COHORT_ID
    assert resp.cohort_name == DEMO_COHORT_NAME
    assert resp.is_demo_data is True
    assert resp.demo_disclaimer == DEMO_DISCLAIMER
    assert resp.sufficiency_status == DataSufficiencyStatus.SUFFICIENT
    assert resp.min_cohort_n == MIN_COHORT_N

    # 13 unique learners with eligible reasoning gap signals (demo_learner_001 to 013)
    # demo_learner_014 had only SAFETY_FALLBACK, which is strictly excluded
    assert resp.total_eligible_learners == 13
    assert resp.total_eligible_sessions == 13

    # Gaps count
    assert len(resp.reasoning_gaps) == 3

    # Gap 1: PATTERN-RAAS-SUB-01
    sub_gap = next((g for g in resp.reasoning_gaps if g.pattern_id == "PATTERN-RAAS-SUB-01"), None)
    assert sub_gap is not None
    assert sub_gap.unique_learners_count == 6
    assert sub_gap.sessions_count == 6
    assert sub_gap.prevalence_rate == round(6 / 13, 4)
    assert sub_gap.epistemic_status == "POSSIBLE_PATTERN"

    # Transfer breakdown for SUB-01:
    # 4 demonstrated independent transfer
    # 1 failed independent transfer
    # 1 assisted transfer (excluded from demonstrated numerator AND qualified denominator)
    t = sub_gap.transfer_metrics
    assert t.transfer_attempted_count == 6
    assert t.assisted_excluded_count == 1
    assert t.qualified_independent_transfer_count == 5  # 6 attempted - 1 assisted
    assert t.transfer_demonstrated_count == 4
    assert t.transfer_not_demonstrated_count == 1  # 5 qualified - 4 demonstrated
    assert t.transfer_demonstration_rate == round(4 / 5, 4)  # 0.8000 (80%), NOT 4/6 (66.7%)!

    # Gap 2: PATTERN-RAAS-ENZ-01
    enz_gap = next((g for g in resp.reasoning_gaps if g.pattern_id == "PATTERN-RAAS-ENZ-01"), None)
    assert enz_gap is not None
    assert enz_gap.unique_learners_count == 4
    assert enz_gap.pattern_learner_count == 4
    assert enz_gap.transfer_metrics.transfer_demonstrated_count == 3
    assert enz_gap.transfer_metrics.qualified_independent_transfer_count == 4
    assert enz_gap.transfer_metrics.transfer_attempted_count == 4
    assert enz_gap.transfer_metrics.transfer_demonstration_rate == round(3 / 4, 4)

    # Gap 3: PATTERN-RAAS-REC-01
    rec_gap = next((g for g in resp.reasoning_gaps if g.pattern_id == "PATTERN-RAAS-REC-01"), None)
    assert rec_gap is not None
    assert rec_gap.unique_learners_count == 3
    assert rec_gap.pattern_learner_count == 3
    assert rec_gap.transfer_metrics.transfer_demonstrated_count == 2
    assert rec_gap.transfer_metrics.qualified_independent_transfer_count == 3
    assert rec_gap.transfer_metrics.transfer_attempted_count == 3
    assert rec_gap.transfer_metrics.transfer_demonstration_rate == round(2 / 3, 4)

    # Overall transfer effectiveness
    ot = resp.overall_transfer_effectiveness
    assert ot.transfer_attempted_count == 13
    assert ot.assisted_excluded_count == 1
    assert ot.qualified_independent_transfer_count == 12  # 13 attempted - 1 assisted
    assert ot.transfer_demonstrated_count == 9  # 4 + 3 + 2
    assert ot.transfer_not_demonstrated_count == 3  # 1 + 1 + 1
    assert ot.transfer_demonstration_rate == round(9 / 12, 4)  # 0.7500 (75%), NOT 9/13 (69.2%)!


def test_assisted_transfer_excluded_from_demonstrated_transfer(aggregator):
    """Invariant: assisted transfer must NEVER count in transfer numerator OR denominator."""
    demo_sessions = get_demo_sessions()
    # Find the assisted session for learner 6
    assisted_session = next(s for s in demo_sessions if s.user_id == "demo_learner_006")
    assert assisted_session.transfer_attempt.was_assisted is True
    assert assisted_session.transfer_attempt.is_correct is True

    # Aggregate specifically
    resp = aggregator.aggregate_cohort(cohort_id=DEMO_COHORT_ID)
    sub_gap = next(g for g in resp.reasoning_gaps if g.pattern_id == "PATTERN-RAAS-SUB-01")

    # If assisted was erroneously included in numerator, demonstrated would be 5.
    # It MUST be 4.
    assert sub_gap.transfer_metrics.transfer_demonstrated_count == 4
    # If assisted was erroneously included in denominator, qualified would be 6.
    # It MUST be 5.
    assert sub_gap.transfer_metrics.assisted_excluded_count == 1
    assert sub_gap.transfer_metrics.qualified_independent_transfer_count == 5
    assert sub_gap.transfer_metrics.transfer_demonstration_rate == 0.8


def test_safety_fallback_excluded_from_aggregation():
    """Invariant: SAFETY_FALLBACK sessions must be excluded from reasoning gap signal counts."""
    demo_sessions = get_demo_sessions()
    fallback_session = next(s for s in demo_sessions if s.session_id == "DEMO-SES-FALLBACK-014")

    assert fallback_session.outcome == RemediationOutcome.SAFETY_FALLBACK
    assert is_session_eligible(fallback_session) is False


def test_insufficient_evidence_excluded_from_aggregation():
    """Invariant: INSUFFICIENT_EVIDENCE sessions must be excluded from pattern assertions."""
    from medicalplab.remediation.models import DetectionStatus, PatternHypothesis, EpistemicType
    session = RemediationSessionState(
        session_id="SES-INSUFF-001",
        user_id="learner_x",
        question_id="UNI-RENAL-001",
        selected_option="B",
        topic="preclinical_renal",
        is_complete=True,
        lifecycle_state=RemediationLifecycleState.COMPLETED,
        outcome=RemediationOutcome.UNRESOLVED,
        remediation_status=RemediationStatus.UNRESOLVED,
        detected_gap=DetectedLearningGap(
            pattern_id="PATTERN-UNKNOWN",
            topic="preclinical_renal",
            category=ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION,
            reasoning_pattern="Ambiguous gap",
            recommended_strategy=SocraticStrategyType.GUIDED_RECALL,
            detection_rationale="Sub-threshold distractor without clear pattern match",
            is_fallback=True,
        ),
        hypothesis=PatternHypothesis(
            hypothesis_id="HYP-INSUFF",
            epistemic_type=EpistemicType.HYPOTHESIS,
            detection_status=DetectionStatus.INSUFFICIENT_EVIDENCE,
            category=ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION,
            pattern_id="PATTERN-UNKNOWN",
            candidate_pattern="Ambiguous gap",
            detection_rationale="Sub-threshold distractor",
        ),
        timeline=ReasoningTimelineItem(
            initial_pattern="Initial selection",
            learning_gap="Ambiguous gap",
            status="COMPLETED",
        ),
    )
    assert is_session_eligible(session) is False


def test_small_n_privacy_suppression(aggregator):
    """Invariant: Cohorts with fewer than MIN_COHORT_N learners return INSUFFICIENT_COHORT_DATA."""
    # Custom aggregator with empty/small cohort
    class MockSmallRepo(LearningIntelligenceRepository):
        def get_cohort_sessions(self, cohort_id, topic=None, subject=None):
            # Return only 2 learners (below MIN_COHORT_N=3)
            all_s = get_demo_sessions()
            return [s for s in all_s if s.user_id in {"demo_learner_001", "demo_learner_002"}], False

    small_aggregator = ReasoningGapAggregator(
        repository=MockSmallRepo(allowed_cohorts={DEMO_COHORT_ID})
    )
    resp = small_aggregator.aggregate_cohort(cohort_id=DEMO_COHORT_ID)

    assert resp.sufficiency_status == DataSufficiencyStatus.INSUFFICIENT_COHORT_DATA
    assert resp.total_eligible_learners == 2
    assert resp.reasoning_gaps == []
    assert resp.overall_transfer_effectiveness.transfer_attempted_count == 0


def test_zero_learner_identity_leakage(aggregator):
    """Invariant: Returned payload must contain ZERO raw learner IDs, emails, or student names."""
    resp = aggregator.aggregate_cohort(cohort_id=DEMO_COHORT_ID)
    payload_str = resp.model_dump_json()

    # Assert no demo learner IDs are in the output JSON
    for i in range(1, 15):
        learner_id = f"demo_learner_{i:03d}"
        assert learner_id not in payload_str, f"Learner ID {learner_id} leaked in educator payload!"

    # Assert no 'user_id' or 'student_id' fields in the payload schema
    payload_dict = json.loads(payload_str)
    assert "user_id" not in payload_dict
    assert "learners" not in payload_dict
    for gap in payload_dict.get("reasoning_gaps", []):
        assert "user_id" not in gap
        assert "learners" not in gap


def test_epistemic_modesty_enforced(aggregator):
    """Invariant: Every reasoning gap must use modest epistemic status."""
    resp = aggregator.aggregate_cohort(cohort_id=DEMO_COHORT_ID)
    for gap in resp.reasoning_gaps:
        assert gap.epistemic_status == "POSSIBLE_PATTERN"
        # Verify forbidden strings are not used as epistemic assertions
        assert "CONFIRMED" not in gap.epistemic_status
        assert "DIAGNOSED" not in gap.epistemic_status


def test_real_evidence_references_resolved(aggregator):
    """Invariant: Real evidence citations are mapped with genuine titles and URLs."""
    resp = aggregator.aggregate_cohort(cohort_id=DEMO_COHORT_ID)
    sub_gap = next(g for g in resp.reasoning_gaps if g.pattern_id == "PATTERN-RAAS-SUB-01")

    assert len(sub_gap.evidence_references) > 0
    ev = sub_gap.evidence_references[0]
    assert ev.document_id == "DOC-PMC-RENAL-0001"
    assert ev.chunk_id == "DOC-PMC-RENAL-0001-B0003-C01"
    assert ev.title is not None
    assert "Renin-Angiotensin" in ev.title or "vascular" in ev.title.lower()
    assert ev.source_url is not None


def test_reload_and_read_idempotency(aggregator):
    """Invariant: Repeated calls return identically without mutation."""
    resp1 = aggregator.aggregate_cohort(cohort_id=DEMO_COHORT_ID)
    resp2 = aggregator.aggregate_cohort(cohort_id=DEMO_COHORT_ID)

    assert resp1.model_dump(exclude={"generated_at"}) == resp2.model_dump(exclude={"generated_at"})


def test_malformed_sqlite_records_fail_safely(tmp_path):
    """Invariant: Corrupted SQLite records are safely skipped without failing the cohort."""
    db_file = tmp_path / "test_remediation.sqlite3"
    conn = sqlite3.connect(db_file)
    conn.execute("""
        CREATE TABLE remediation_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            selected_option TEXT NOT NULL,
            topic TEXT NOT NULL,
            turn_number INTEGER NOT NULL,
            is_complete INTEGER NOT NULL,
            remediation_status TEXT NOT NULL,
            lifecycle_state TEXT NOT NULL,
            outcome TEXT,
            session_state_json TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        )
    """)
    # Insert 1 corrupted JSON row and 3 valid rows
    conn.execute("INSERT INTO remediation_sessions VALUES ('s_corrupt', 'u_bad', 'q1', 'B', 'top', 1, 1, 'RESOLVED', 'COMPLETED', 'TRANSFER_CONFIRMED', '{invalid json', 1.0, 1.0)")
    for i in range(1, 4):
        session = RemediationSessionState(
            session_id=f"s_{i}",
            user_id=f"u_{i}",
            question_id="q1",
            selected_option="B",
            topic="preclinical_renal",
            turn_number=3,
            max_turns=3,
            is_complete=True,
            lifecycle_state=RemediationLifecycleState.COMPLETED,
            outcome=RemediationOutcome.TRANSFER_CONFIRMED,
            remediation_status=RemediationStatus.RESOLVED,
            detected_gap=DetectedLearningGap(
                pattern_id="PATTERN-TEST",
                topic="preclinical_renal",
                category=ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION,
                reasoning_pattern="Test pattern",
                recommended_strategy=SocraticStrategyType.CONTRAST_CASE,
                detection_rationale="Test rationale",
            ),
            timeline=ReasoningTimelineItem(
                initial_pattern="Initial",
                learning_gap="Gap",
                status="COMPLETED",
            ),
        )
        conn.execute("INSERT INTO remediation_sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            session.session_id, session.user_id, session.question_id, session.selected_option,
            session.topic, session.turn_number, 1, "RESOLVED", "COMPLETED", "TRANSFER_CONFIRMED",
            session.model_dump_json(), 1.0, 1.0
        ))
    conn.commit()
    conn.close()

    repo = LearningIntelligenceRepository(db_path=db_file, allowed_cohorts={"real_cohort_test"})
    agg = ReasoningGapAggregator(repository=repo)
    resp = agg.aggregate_cohort(cohort_id="real_cohort_test")

    # Should safely skip corrupted row and aggregate 3 valid rows
    assert resp.sufficiency_status == DataSufficiencyStatus.SUFFICIENT
    assert resp.total_eligible_learners == 3
    assert len(resp.reasoning_gaps) == 1
    assert resp.reasoning_gaps[0].unique_learners_count == 3


def test_zero_qualified_transfer_attempts_produces_none_rate():
    """Invariant: When qualified independent attempts == 0, rate must be None, not 0.0 or misleading float."""
    class MockAssistedOnlyRepo(LearningIntelligenceRepository):
        def get_cohort_sessions(self, cohort_id, topic=None, subject=None):
            all_s = get_demo_sessions()
            # 3 learners, but ALL of them had assisted transfer attempts
            sessions = []
            for s in all_s[:3]:
                s_copy = s.model_copy(deep=True)
                s_copy.transfer_attempt.was_assisted = True
                s_copy.assistance_invoked = True
                sessions.append(s_copy)
            return sessions, False

    agg = ReasoningGapAggregator(
        repository=MockAssistedOnlyRepo(allowed_cohorts={"test_assisted_cohort"})
    )
    resp = agg.aggregate_cohort(cohort_id="test_assisted_cohort")

    assert resp.sufficiency_status == DataSufficiencyStatus.SUFFICIENT
    gap = resp.reasoning_gaps[0]
    assert gap.transfer_metrics.transfer_attempted_count == 3
    assert gap.transfer_metrics.assisted_excluded_count == 3
    assert gap.transfer_metrics.qualified_independent_transfer_count == 0
    assert gap.transfer_metrics.transfer_demonstrated_count == 0
    assert gap.transfer_metrics.transfer_demonstration_rate is None


def test_server_side_min_cohort_n_env_configuration_and_clamping(monkeypatch):
    """Invariant: MIN_COHORT_N is server-controlled only and clamped to >= 3."""
    from medicalplab.learning_intelligence.aggregation import get_min_cohort_n

    # Case 1: Unset -> defaults to 3
    monkeypatch.delenv("MEDICALPLAB_PHASE_3_MIN_COHORT_N", raising=False)
    assert get_min_cohort_n() == 3

    # Case 2: Configured to valid >= 3
    monkeypatch.setenv("MEDICALPLAB_PHASE_3_MIN_COHORT_N", "5")
    assert get_min_cohort_n() == 5

    # Case 3: Caller/env attempts to lower below 3 (e.g. 1 or 2) -> clamped to 3
    monkeypatch.setenv("MEDICALPLAB_PHASE_3_MIN_COHORT_N", "1")
    assert get_min_cohort_n() == 3

    # Case 4: Invalid string -> fails safely to 3
    monkeypatch.setenv("MEDICALPLAB_PHASE_3_MIN_COHORT_N", "invalid_threshold")
    assert get_min_cohort_n() == 3


def test_evidence_aggregation_rejects_fallback_and_fabricated_citations():
    """Invariant: Citations must originate from genuine verified records, deduplicated, no safety fallback citations."""
    repo = LearningIntelligenceRepository()
    # Reject fallback or safety strings
    assert repo.resolve_evidence("SAFETY_FALLBACK_CITATION") is None
    assert repo.resolve_evidence("UNKNOWN_REF") is None
    assert repo.resolve_evidence("") is None

    # Valid genuine reference resolves
    valid = repo.resolve_evidence("DOC-PMC-RENAL-0001")
    assert valid is not None
    assert valid.document_id == "DOC-PMC-RENAL-0001"


def test_unknown_cohort_id_rejected_by_repository():
    """Invariant: Arbitrary unknown cohort identifiers must be rejected with UnknownCohortError."""
    from medicalplab.learning_intelligence.repository import UnknownCohortError
    repo = LearningIntelligenceRepository()
    with pytest.raises(UnknownCohortError):
        repo.get_cohort_sessions(cohort_id="arbitrary_unregistered_cohort")


def test_demo_cohort_disabled_in_production_runtime(monkeypatch):
    """Invariant: In production runtime, demo cohort is disabled unless MEDICALPLAB_PHASE_3_DEMO_ENABLED=true."""
    from medicalplab.learning_intelligence.repository import DemoCohortDisabledError

    repo = LearningIntelligenceRepository()

    # In production without flag -> raises DemoCohortDisabledError
    monkeypatch.setenv("MEDICALPLAB_RUNTIME_MODE", "production")
    monkeypatch.delenv("MEDICALPLAB_PHASE_3_DEMO_ENABLED", raising=False)
    with pytest.raises(DemoCohortDisabledError):
        repo.get_cohort_sessions(cohort_id=DEMO_COHORT_ID)

    # In production with explicit flag -> succeeds
    monkeypatch.setenv("MEDICALPLAB_PHASE_3_DEMO_ENABLED", "true")
    sessions, is_demo = repo.get_cohort_sessions(cohort_id=DEMO_COHORT_ID)
    assert is_demo is True
    assert len(sessions) > 0
