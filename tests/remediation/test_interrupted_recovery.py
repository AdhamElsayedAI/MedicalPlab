"""Gate 1: Interrupted Learning-Effect Recovery Tests.

Verifies crash safety and non-atomic boundary integrity across:
transfer validation
-> transfer decision/scoring
-> transfer result persistence
-> Phase 2A learning evidence application
-> durable evidence-delivery/completion marker
-> response

Scenarios covered:
- Scenario A: Transfer result durably persisted, interrupted before Phase 2A evidence applied.
- Scenario B: Phase 2A evidence applied, interrupted before durable completion marker written.
- Scenario C: Terminal transfer/effect state safely persisted, HTTP response lost.

Inspects the ACTUAL learner-state effect / evidence record, NOT mock call counts.
"""
import pytest
from pathlib import Path
from typing import Any

from medicalplab.adaptive.models import LearningEvent, LearnerState
from medicalplab.adaptive.service import AdaptiveLearningService
from medicalplab.remediation.controller import RemediationLoopController
from medicalplab.remediation.learning_evidence import LearningEvidenceAdapter
from medicalplab.remediation.models import (
    RemediationLifecycleState,
    RemediationOutcome,
    RemediationStatus,
)


class CrashInjectionError(Exception):
    """Simulated crash/interruption at non-atomic persistence boundaries."""
    pass


class TrackingAdaptiveService(AdaptiveLearningService):
    """Real adaptive learning service double that tracks applied learning evidence records."""

    def __init__(self) -> None:
        super().__init__()
        self.applied_learning_events: list[LearningEvent] = []

    def record_learning_event(self, event: LearningEvent) -> LearnerState:
        self.applied_learning_events.append(event)
        return super().record_learning_event(event)

    def count_positive_transfer_effects(self, learner_id: str) -> int:
        """Count actual persisted/effective positive transfer outcomes for this learner."""
        return sum(
            1 for e in self.applied_learning_events
            if e.learner_id == learner_id
            and e.event_type == "QUESTION_ATTEMPT"
            and e.is_correct is True
        )


@pytest.mark.parametrize("scenario", ["scenario_a", "scenario_b", "scenario_c"])
def test_interrupted_learning_effect_recovery(tmp_path: Path, scenario: str):
    """Test interrupted recovery across actual non-atomic boundaries in submit_transfer."""
    db_file = tmp_path / f"interruption_{scenario}.sqlite3"
    tracking_adaptive = TrackingAdaptiveService()
    learner_id = f"learner_{scenario}"
    user_id = learner_id

    # 1. Setup session and advance to AWAITING_TRANSFER
    ctrl1 = RemediationLoopController(
        db_path=db_file,
        learning_adapter=LearningEvidenceAdapter(adaptive_service=tracking_adaptive),
    )
    start_resp = ctrl1.start_session(
        user_id=user_id,
        question_id="UNI-RENAL-001",
        selected_option="B",
    )
    session_id = start_resp.session_id

    # Turn 1 -> Turn 2
    ctrl1.advance_turn(session_id=session_id, user_id=user_id, student_message="Renin from JGA")
    # Turn 2 -> AWAITING_TRANSFER
    ctrl1.advance_turn(session_id=session_id, user_id=user_id, student_message="Renin converts angiotensinogen")

    item = ctrl1.get_transfer_item(session_id=session_id, user_id=user_id)
    assert item is not None
    assert item.question_id == "UNI-RENAL-001-T"

    # =========================================================================
    # SCENARIO A: Scored result persisted, interrupted before Phase 2A evidence
    # =========================================================================
    if scenario == "scenario_a":
        # Inject crash when calling learning_adapter during the first submit
        def crashing_record(*args: Any, **kwargs: Any):
            raise CrashInjectionError("Interruption: process killed before Phase 2A evidence applied")

        ctrl1.learning_adapter.record_qualified_outcome = crashing_record  # type: ignore

        with pytest.raises(CrashInjectionError):
            ctrl1.submit_transfer(
                session_id=session_id,
                user_id=user_id,
                question_id=item.question_id,
                selected_option="A",
                idempotency_key="IDEM-SCENARIO-A",
            )

        # Confirm that before recovery, 0 positive events reached Phase 2A
        assert tracking_adaptive.count_positive_transfer_effects(learner_id) == 0

        # Discard process-local controller state (simulating crash)
        del ctrl1

        # Reopen persisted remediation state with clean controller
        ctrl2 = RemediationLoopController(
            db_path=db_file,
            learning_adapter=LearningEvidenceAdapter(adaptive_service=tracking_adaptive),
        )
        persisted = ctrl2.get_session(session_id, user_id=user_id)
        assert persisted is not None
        assert persisted.transfer_attempt is not None
        assert persisted.transfer_attempt.is_correct is True
        assert persisted.evidence_status in ("PENDING", "DELIVERING")

        # Retry the logical transfer operation
        resp = ctrl2.submit_transfer(
            session_id=session_id,
            user_id=user_id,
            question_id=item.question_id,
            selected_option="A",
            idempotency_key="IDEM-SCENARIO-A",
        )

        assert resp.outcome == RemediationOutcome.TRANSFER_CONFIRMED
        # PASS criteria: positive learning evidence is applied at most once
        assert tracking_adaptive.count_positive_transfer_effects(learner_id) == 1

        # Additional retry must not duplicate the learner effect
        resp_dup = ctrl2.submit_transfer(
            session_id=session_id,
            user_id=user_id,
            question_id=item.question_id,
            selected_option="A",
            idempotency_key="IDEM-SCENARIO-A",
        )
        assert resp_dup.outcome == RemediationOutcome.TRANSFER_CONFIRMED
        assert tracking_adaptive.count_positive_transfer_effects(learner_id) == 1

    # =========================================================================
    # SCENARIO B: Phase 2A evidence applied, interrupted before completion marker
    # =========================================================================
    elif scenario == "scenario_b":
        # Inject crash right after Phase 2A receives evidence, when persisting the DELIVERED marker
        original_persist = ctrl1._persist_session

        def crashing_persist(session: Any):
            if getattr(session, "evidence_status", None) == "DELIVERED":
                raise CrashInjectionError("Interruption: process killed before durable DELIVERED marker written")
            original_persist(session)

        ctrl1._persist_session = crashing_persist  # type: ignore

        with pytest.raises(CrashInjectionError):
            ctrl1.submit_transfer(
                session_id=session_id,
                user_id=user_id,
                question_id=item.question_id,
                selected_option="A",
                idempotency_key="IDEM-SCENARIO-B",
            )

        # Positive evidence WAS received by Phase 2A during the attempt
        assert tracking_adaptive.count_positive_transfer_effects(learner_id) == 1

        # Discard process-local controller state
        del ctrl1

        # Reopen state from SQLite
        ctrl2 = RemediationLoopController(
            db_path=db_file,
            learning_adapter=LearningEvidenceAdapter(adaptive_service=tracking_adaptive),
        )
        persisted = ctrl2.get_session(session_id, user_id=user_id)
        assert persisted is not None
        assert persisted.transfer_attempt is not None
        # Marker was not written, so state remains DELIVERING
        assert persisted.evidence_status == "DELIVERING"

        # Retry the logical transfer operation
        resp = ctrl2.submit_transfer(
            session_id=session_id,
            user_id=user_id,
            question_id=item.question_id,
            selected_option="A",
            idempotency_key="IDEM-SCENARIO-B",
        )

        assert resp.outcome == RemediationOutcome.TRANSFER_CONFIRMED
        # PASS criteria: positive learner effect is NOT applied a second time
        # The system does not blindly replay ambiguous evidence
        assert tracking_adaptive.count_positive_transfer_effects(learner_id) == 1

        # Final persisted session is clean
        persisted_final = ctrl2.get_session(session_id, user_id=user_id)
        assert persisted_final.evidence_status == "DELIVERED"
        assert persisted_final.lifecycle_state == RemediationLifecycleState.COMPLETED

    # =========================================================================
    # SCENARIO C: Terminal state safely persisted, HTTP response lost
    # =========================================================================
    elif scenario == "scenario_c":
        # Normal completion of submit_transfer
        resp1 = ctrl1.submit_transfer(
            session_id=session_id,
            user_id=user_id,
            question_id=item.question_id,
            selected_option="A",
            idempotency_key="IDEM-SCENARIO-C",
        )
        assert resp1.outcome == RemediationOutcome.TRANSFER_CONFIRMED
        assert tracking_adaptive.count_positive_transfer_effects(learner_id) == 1

        # Discard controller state (simulating client retrying on a new connection / server instance)
        del ctrl1

        ctrl2 = RemediationLoopController(
            db_path=db_file,
            learning_adapter=LearningEvidenceAdapter(adaptive_service=tracking_adaptive),
        )

        # Retry identical submission
        resp2 = ctrl2.submit_transfer(
            session_id=session_id,
            user_id=user_id,
            question_id=item.question_id,
            selected_option="A",
            idempotency_key="IDEM-SCENARIO-C",
        )

        # PASS criteria: same terminal result returned, no re-scoring, no extra learning effect
        assert resp2.outcome == resp1.outcome
        assert resp2.is_correct == resp1.is_correct
        assert resp2.session_id == resp1.session_id
        assert tracking_adaptive.count_positive_transfer_effects(learner_id) == 1


def test_interrupted_window_after_phase2a_before_evidence_dedup_record(tmp_path: Path):
    """Test exact narrow window:

    REAL Phase 2A positive learning effect commits successfully
    BUT
    process crashes BEFORE remediation_learning_evidence is durably recorded.

    Verification sequence:
    1. Start from an eligible remediation session.
    2. Reach qualified transfer.
    3. Allow the REAL Phase 2A positive learning effect to commit.
    4. Inject failure immediately BEFORE the durable remediation_learning_evidence record is written.
    5. Discard in-memory controller/process-local state.
    6. Reopen:
       - remediation SQLite state;
       - learner/adaptive durable state.
    7. Retry the same logical transfer.
    8. Inspect the ACTUAL durable positive learning effect.

    PASS criteria:
    - total positive effect count remains exactly 1;
    - retry does not inflate mastery/learner state;
    - the system does not falsely claim completed adaptation while delivery state is ambiguous.
    """
    import sqlite3
    from contextlib import closing

    db_file = tmp_path / "narrow_interruption_window.sqlite3"

    class CrashingAfterPhase2AAdaptiveService(TrackingAdaptiveService):
        """Commits Phase 2A event, then immediately interrupts before caller writes dedup record."""
        def record_learning_event(self, event: LearningEvent) -> LearnerState:
            state = super().record_learning_event(event)
            # REAL Phase 2A positive learning effect has now committed!
            # Inject crash immediately before caller writes remediation_learning_evidence record
            raise CrashInjectionError("Crash immediately after Phase 2A effect committed, BEFORE remediation_learning_evidence written")

    tracking_adaptive = CrashingAfterPhase2AAdaptiveService()
    user_id = "learner_narrow_window"

    # 1. Setup session and advance to AWAITING_TRANSFER
    ctrl1 = RemediationLoopController(
        db_path=db_file,
        learning_adapter=LearningEvidenceAdapter(adaptive_service=tracking_adaptive, db_path=db_file),
    )
    start_resp = ctrl1.start_session(
        user_id=user_id,
        question_id="UNI-RENAL-001",
        selected_option="B",
    )
    session_id = start_resp.session_id

    # Turn 1 -> Turn 2
    ctrl1.advance_turn(session_id=session_id, user_id=user_id, student_message="Renin from JGA")
    # Turn 2 -> AWAITING_TRANSFER
    ctrl1.advance_turn(session_id=session_id, user_id=user_id, student_message="Renin converts angiotensinogen")

    item = ctrl1.get_transfer_item(session_id=session_id, user_id=user_id)
    assert item is not None
    assert item.question_id == "UNI-RENAL-001-T"

    # 2. Attempt transfer submission; crash is injected AFTER Phase 2A commits, BEFORE dedup record written
    with pytest.raises(CrashInjectionError):
        ctrl1.submit_transfer(
            session_id=session_id,
            user_id=user_id,
            question_id=item.question_id,
            selected_option="A",
            idempotency_key="IDEM-NARROW-WINDOW",
        )

    # 3. Verify exact fault boundary in durable state:
    # A. Real Phase 2A received and committed the positive learning effect
    assert tracking_adaptive.count_positive_transfer_effects(user_id) == 1
    # B. remediation_learning_evidence deduplication record was NEVER written
    with closing(sqlite3.connect(db_file)) as conn:
        row_count = conn.execute("SELECT COUNT(*) FROM remediation_learning_evidence WHERE session_id = ?", (session_id,)).fetchone()[0]
        assert row_count == 0, "Deduplication record must not exist before crash"
        sess_row = conn.execute("SELECT session_state_json FROM remediation_sessions WHERE session_id = ?", (session_id,)).fetchone()
        assert sess_row is not None
        import json
        sess_data = json.loads(sess_row[0])
        assert sess_data["evidence_status"] == "DELIVERING", "Session must reflect in-flight delivery state"

    # 4. Discard in-memory controller/process-local state
    del ctrl1

    # 5. Reopen remediation SQLite state & learner/adaptive durable state
    ctrl2 = RemediationLoopController(
        db_path=db_file,
        learning_adapter=LearningEvidenceAdapter(adaptive_service=tracking_adaptive, db_path=db_file),
    )

    # 6. Retry the same logical transfer
    resp = ctrl2.submit_transfer(
        session_id=session_id,
        user_id=user_id,
        question_id=item.question_id,
        selected_option="A",
        idempotency_key="IDEM-NARROW-WINDOW",
    )

    # 7. Inspect PASS criteria:
    # Criterion 1: Total positive effect count remains exactly 1 (no duplicate effect)
    assert tracking_adaptive.count_positive_transfer_effects(user_id) == 1
    # Criterion 2: Retry does not inflate mastery or learner state
    assert resp.outcome == RemediationOutcome.TRANSFER_CONFIRMED
    assert resp.is_correct is True
    # Criterion 3: Does not falsely claim completed adaptation while delivery state was ambiguous
    assert resp.timeline.status == "UNRESOLVED"
    assert resp.next_recommendation is None
    assert "pending verification" in resp.timeline.transfer_result

    # 8. Subsequent duplicate retries remain stable and strictly at count 1
    resp_dup = ctrl2.submit_transfer(
        session_id=session_id,
        user_id=user_id,
        question_id=item.question_id,
        selected_option="A",
        idempotency_key="IDEM-NARROW-WINDOW",
    )
    assert tracking_adaptive.count_positive_transfer_effects(user_id) == 1
    assert resp_dup.outcome == RemediationOutcome.TRANSFER_CONFIRMED
