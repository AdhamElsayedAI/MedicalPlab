"""Learning Evidence Adapter for Phase 2B.

Connects validated remediation outcomes to the Phase 2A Adaptive Grounded Learning Engine.

HARD INVARIANTS:
1. Zero mastery inflation: completed dialogue or student self-reports NEVER increase mastery.
2. Original question attempts are NEVER double-counted when remediation begins.
3. Only an unassisted, deterministically scored TRANSFER_CONFIRMED outcome supplies
   positive learning evidence to Phase 2A.
4. Assisted attempts, unresolved sessions, and abandoned sessions never produce positive mastery updates.
"""
from __future__ import annotations

import logging
from pathlib import Path
import time
from typing import Any, Dict, Optional
import uuid

from medicalplab.adaptive.models import (
    AdaptiveRecommendation,
    LearningEvent,
)
from medicalplab.adaptive.service import AdaptiveLearningService
from medicalplab.remediation.models import (
    QualifiedLearningEvidenceEvent,
    RemediationOutcome,
    TransferAttempt,
)

logger = logging.getLogger(__name__)


class LearningEvidenceAdapter:
    """Bridges Phase 2B qualified outcomes into Phase 2A learner state."""

    def __init__(
        self,
        adaptive_service: AdaptiveLearningService | None = None,
        db_path: Path | str | None = None,
    ) -> None:
        self._adaptive_service = adaptive_service
        self.db_path = Path(db_path) if db_path else None
        self._init_db()

    def _init_db(self) -> None:
        if not self.db_path:
            return
        try:
            import sqlite3
            from contextlib import closing
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(self.db_path, timeout=5.0)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS remediation_learning_evidence (
                        session_id TEXT PRIMARY KEY,
                        learner_id TEXT NOT NULL,
                        event_id TEXT NOT NULL,
                        is_confirmed INTEGER NOT NULL,
                        created_at REAL NOT NULL
                    )
                """)
                conn.commit()
        except Exception as exc:
            logger.warning("Could not initialize remediation_learning_evidence table: %s", exc)

    def has_durable_evidence_record(self, session_id: str) -> bool:
        """Check specifically if the durable remediation_learning_evidence table has this session."""
        if self.db_path and self.db_path.exists():
            try:
                import sqlite3
                from contextlib import closing
                with closing(sqlite3.connect(self.db_path, timeout=5.0)) as conn:
                    row = conn.execute(
                        "SELECT 1 FROM remediation_learning_evidence WHERE session_id = ?",
                        (session_id,),
                    ).fetchone()
                    return bool(row)
            except Exception as exc:
                logger.warning("Error querying remediation_learning_evidence table: %s", exc)
        return False

    def has_evidence_for_session(self, session_id: str, learner_id: str) -> bool:
        """Check if qualified evidence was already applied for this session."""
        if self.has_durable_evidence_record(session_id):
            return True

        if hasattr(self.adaptive_service, "applied_learning_events"):
            for ev in getattr(self.adaptive_service, "applied_learning_events", []):
                meta = getattr(ev, "metadata", None)
                if isinstance(meta, dict) and meta.get("remediation_session_id") == session_id:
                    return True

        return False

    @property
    def adaptive_service(self) -> AdaptiveLearningService:
        if self._adaptive_service is None:
            self._adaptive_service = AdaptiveLearningService()
        return self._adaptive_service

    def record_qualified_outcome(
        self,
        learner_id: str,
        session_id: str,
        original_question_id: str,
        topic: str,
        subject: str,
        outcome: RemediationOutcome,
        transfer_attempt: Optional[TransferAttempt] = None,
    ) -> tuple[QualifiedLearningEvidenceEvent, Optional[AdaptiveRecommendation]]:
        """Record the qualified outcome and fetch the next adaptive recommendation."""
        is_confirmed = (outcome == RemediationOutcome.TRANSFER_CONFIRMED)
        was_assisted = transfer_attempt.was_assisted if transfer_attempt else False
        transfer_q_id = transfer_attempt.question_id if transfer_attempt else None

        event = QualifiedLearningEvidenceEvent(
            event_id=f"QEVT-{uuid.uuid4().hex[:10].upper()}",
            learner_id=learner_id,
            original_question_id=original_question_id,
            transfer_question_id=transfer_q_id,
            topic=topic,
            subject=subject,
            outcome=outcome,
            is_transfer_confirmed=is_confirmed,
            was_assisted=was_assisted,
            timestamp=time.time(),
        )

        # Check if evidence was already delivered for this session (idempotent delivery guarantee)
        if self.has_evidence_for_session(session_id, learner_id):
            logger.info("Learning evidence already applied for session %s - skipping duplicate emission", session_id)
            rec = None
            try:
                rec = self.adaptive_service.get_top_recommendation(learner_id)
            except Exception as exc:
                logger.warning("Could not fetch recommendation on idempotent replay: %s", exc)
            return event, rec

        # Emit to Phase 2A with strict mastery rules
        if is_confirmed and transfer_attempt:
            # Unassisted independent transfer confirmed: record positive attempt on transfer item
            phase2a_event = LearningEvent(
                event_id=f"evt-trans-{session_id}",
                learner_id=learner_id,
                event_type="QUESTION_ATTEMPT",
                subject=subject,
                topic=topic,
                question_id=transfer_attempt.question_id,
                selected_option=transfer_attempt.submitted_option,
                is_correct=True,
                attempt_key=f"att-{session_id}-{transfer_attempt.question_id}",
                metadata={
                    "remediation_session_id": session_id,
                    "remediation_outcome": outcome.value,
                    "is_transfer_confirmed": True,
                    "was_assisted": False,
                },
            )
            self.adaptive_service.record_learning_event(phase2a_event)
            logger.info("Recorded positive transfer event in Phase 2A for learner %s", learner_id)

        elif outcome == RemediationOutcome.TRANSFER_NOT_CONFIRMED and transfer_attempt:
            # Scored independent transfer failed: record negative attempt on transfer item
            phase2a_event = LearningEvent(
                event_id=f"evt-trans-{session_id}",
                learner_id=learner_id,
                event_type="QUESTION_ATTEMPT",
                subject=subject,
                topic=topic,
                question_id=transfer_attempt.question_id,
                selected_option=transfer_attempt.submitted_option,
                is_correct=False,
                attempt_key=f"att-{session_id}-{transfer_attempt.question_id}",
                metadata={
                    "remediation_session_id": session_id,
                    "remediation_outcome": outcome.value,
                    "is_transfer_confirmed": False,
                },
            )
            self.adaptive_service.record_learning_event(phase2a_event)
            logger.info("Recorded incorrect transfer event in Phase 2A for learner %s", learner_id)

        else:
            # Assisted, unresolved, or abandoned: record non-scoring tutor intervention event
            phase2a_event = LearningEvent(
                event_id=f"evt-rem-{session_id}",
                learner_id=learner_id,
                event_type="TUTOR_INTERVENTION",
                subject=subject,
                topic=topic,
                question_id=original_question_id,
                is_correct=None,  # Zero effect on accuracy or mastery
                metadata={
                    "remediation_session_id": session_id,
                    "remediation_outcome": outcome.value,
                    "was_assisted": was_assisted,
                },
            )
            self.adaptive_service.record_learning_event(phase2a_event)

        # Durably record evidence emission to prevent duplicate delivery across restarts
        if self.db_path:
            try:
                import sqlite3
                from contextlib import closing
                with closing(sqlite3.connect(self.db_path, timeout=5.0)) as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO remediation_learning_evidence VALUES (?, ?, ?, ?, ?)",
                        (session_id, learner_id, event.event_id, int(is_confirmed), time.time()),
                    )
                    conn.commit()
            except Exception as exc:
                logger.warning("Could not record evidence in db: %s", exc)

        # Retrieve next recommendation from Phase 2A
        rec = None
        try:
            rec = self.adaptive_service.get_top_recommendation(learner_id)
        except Exception as exc:
            logger.warning("Could not retrieve recommendation from Phase 2A: %s", exc)
        return event, rec
