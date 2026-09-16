"""Remediation Loop Controller for MedicalPlab Phase 2B.

Orchestrates the bounded 3-turn Socratic remediation lifecycle:
- Turn 1: PROBE (Challenge flawed premise neutrally)
- Turn 2: GUIDE (Provide scaffolded mechanistic clue)
- Turn 3: CONSOLIDATE (Consolidate reasoning and check readiness for transfer)
- Transfer Step: Select, administer, and score independent held-out item.
- Learning Evidence Step: Emit qualified event to Phase 2A without mastery inflation.

HARD BOUNDS & INVARIANTS:
1. Socratic dialogue strictly bounded to 3 turns maximum.
2. Turn 3 completion transitions lifecycle to AWAITING_TRANSFER, NOT learning success.
3. Zero unverified student text declared as "Corrected Reasoning".
4. Fail-closed safety: pipeline verification failures transition to SAFETY_FALLBACK.
5. Independent transfer scored deterministically server-side; assisted answers disqualified.
"""
from __future__ import annotations

from contextlib import closing
import json
import logging
from pathlib import Path
import sqlite3
import time
from typing import Dict, Optional
import uuid

from medicalplab.remediation.bridge import RemediationTutorBridge
from medicalplab.remediation.detector import ReasoningPatternDetectionEngine
from medicalplab.remediation.learning_evidence import LearningEvidenceAdapter
from medicalplab.remediation.models import (
    DetectedLearningGap,
    PatternHypothesis,
    ReasoningTimelineItem,
    RemediationLifecycleState,
    RemediationOutcome,
    RemediationSessionResponse,
    RemediationSessionState,
    RemediationStatus,
    RemediationTurnRecord,
    RemediationTurnResponse,
    SocraticStrategyType,
    TransferAttempt,
    TransferItemDTO,
    TransferSubmissionResponse,
    CANONICAL_SAFETY_FALLBACK_MESSAGE,
)
from medicalplab.remediation.strategy import SocraticStrategyEngine
from medicalplab.remediation.transfer import TransferAssessmentService

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "Data"
    / "persistence"
    / "university.sqlite3"
)


class RemediationError(Exception):
    """Base error for remediation operations."""
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class RemediationLoopController:
    """Controls session state, turn progression, transfer assessment, and timeline tracking."""

    def __init__(
        self,
        detector: ReasoningPatternDetectionEngine | None = None,
        strategy_engine: SocraticStrategyEngine | None = None,
        bridge: RemediationTutorBridge | None = None,
        transfer_service: TransferAssessmentService | None = None,
        learning_adapter: LearningEvidenceAdapter | None = None,
        db_path: Path | str | None = None,
    ) -> None:
        self.detector = detector or ReasoningPatternDetectionEngine()
        self.strategy_engine = strategy_engine or SocraticStrategyEngine()
        self.bridge = bridge or RemediationTutorBridge()
        self.transfer_service = transfer_service or TransferAssessmentService()
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.learning_adapter = learning_adapter or LearningEvidenceAdapter(db_path=self.db_path)
        if self.learning_adapter.db_path is None:
            self.learning_adapter.db_path = self.db_path
            self.learning_adapter._init_db()
        self._memory_sessions: Dict[str, RemediationSessionState] = {}
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with closing(sqlite3.connect(self.db_path, timeout=5.0)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS remediation_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        question_id TEXT NOT NULL,
                        selected_option TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        turn_number INTEGER NOT NULL,
                        is_complete INTEGER NOT NULL,
                        remediation_status TEXT NOT NULL,
                        lifecycle_state TEXT NOT NULL DEFAULT 'CREATED',
                        outcome TEXT,
                        session_state_json TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                """)
                # Handle migrations for older tables
                cur = conn.execute("PRAGMA table_info(remediation_sessions)")
                cols = {row[1] for row in cur.fetchall()}
                if "lifecycle_state" not in cols:
                    conn.execute("ALTER TABLE remediation_sessions ADD COLUMN lifecycle_state TEXT NOT NULL DEFAULT 'CREATED'")
                if "outcome" not in cols:
                    conn.execute("ALTER TABLE remediation_sessions ADD COLUMN outcome TEXT")
                conn.commit()
        except Exception as exc:
            logger.warning("Could not initialize remediation_sessions table: %s", exc)

    def _persist_session(self, session: RemediationSessionState) -> None:
        self._memory_sessions[session.session_id] = session
        try:
            with closing(sqlite3.connect(self.db_path, timeout=5.0)) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO remediation_sessions (
                        session_id, user_id, question_id, selected_option, topic,
                        turn_number, is_complete, remediation_status, lifecycle_state, outcome,
                        session_state_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.session_id,
                    session.user_id,
                    session.question_id,
                    session.selected_option,
                    session.topic,
                    session.turn_number,
                    int(session.is_complete),
                    session.remediation_status.value,
                    session.lifecycle_state.value,
                    session.outcome.value if session.outcome else None,
                    session.model_dump_json(),
                    session.created_at,
                    session.updated_at,
                ))
                conn.commit()
        except Exception as exc:
            logger.warning("Failed to persist remediation session %s: %s", session.session_id, exc)

    def _normalize_session(self, session: RemediationSessionState) -> RemediationSessionState:
        """Ensure coherent terminal invariants on retrieved sessions."""
        if session.outcome == RemediationOutcome.SAFETY_FALLBACK or session.timeline.status == "SAFETY_FALLBACK":
            session.lifecycle_state = RemediationLifecycleState.COMPLETED
            session.outcome = RemediationOutcome.SAFETY_FALLBACK
            session.is_complete = True
            session.remediation_status = RemediationStatus.UNRESOLVED
            session.timeline.status = "SAFETY_FALLBACK"
            if not session.timeline.transfer_result or "Awaiting" in session.timeline.transfer_result:
                session.timeline.transfer_result = "Remediation stopped safely; no transfer assessment performed."
            if not session.timeline.guided_practice or "initiated" in session.timeline.guided_practice:
                session.timeline.guided_practice = "Remediation concluded due to safety fallback"
            if session.turns:
                last_turn = session.turns[-1]
                last_turn.tutor_message = CANONICAL_SAFETY_FALLBACK_MESSAGE
                last_turn.socratic_probe = None
                last_turn.citations = []
                last_turn.is_safety_fallback = True
        return session

    def get_session(self, session_id: str, user_id: str | None = None) -> Optional[RemediationSessionState]:
        """Retrieve session by ID, verifying ownership if user_id is supplied."""
        session = self._memory_sessions.get(session_id)
        if not session:
            try:
                with closing(sqlite3.connect(self.db_path, timeout=5.0)) as conn:
                    conn.row_factory = sqlite3.Row
                    row = conn.execute(
                        "SELECT session_state_json FROM remediation_sessions WHERE session_id = ?",
                        (session_id,),
                    ).fetchone()
                    if row:
                        session = RemediationSessionState.model_validate_json(row["session_state_json"])
                        self._memory_sessions[session_id] = session
            except Exception as exc:
                logger.warning("Error fetching session %s from DB: %s", session_id, exc)

        if session:
            session = self._normalize_session(session)

        if session and user_id and session.user_id != user_id:
            raise RemediationError("Session does not belong to the requesting user.", status_code=403)
        return session

    def start_session(
        self,
        user_id: str,
        question_id: str,
        selected_option: str,
        topic: str | None = None,
        attempt_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> RemediationTurnResponse:
        """Initialize a new 3-turn Socratic remediation session (Turn 1: Probe)."""
        # 0. Validate eligibility: remediation is strictly for incorrect answers / distractors
        try:
            from medicalplab.university.service import BANK
            import json
            if BANK.exists():
                with open(BANK, "r", encoding="utf-8") as f:
                    bank_questions = {q["id"]: q for q in json.load(f) if isinstance(q, dict) and "id" in q}
                if question_id in bank_questions:
                    q_data = bank_questions[question_id]
                    if selected_option == q_data.get("correct_answer"):
                        raise RemediationError(
                            f"Option '{selected_option}' is the correct answer to '{question_id}'. Remediation is only available for incorrect answers.",
                            status_code=422,
                        )
        except RemediationError:
            raise
        except Exception as exc:
            logger.warning("Could not verify question bank correctness for %s: %s", question_id, exc)

        # Validate attempt provenance against real persisted University attempts
        originating_attempt_id = attempt_id
        try:
            with closing(sqlite3.connect(self.db_path, timeout=5.0)) as conn:
                conn.row_factory = sqlite3.Row
                has_attempts = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='university_attempts'"
                ).fetchone()
                if has_attempts:
                    if attempt_id:
                        row = conn.execute(
                            "SELECT user_id, attempt_key, question_id, selected, correct FROM university_attempts WHERE attempt_key = ?",
                            (attempt_id,),
                        ).fetchone()
                        if not row:
                            raise RemediationError(f"Attempt '{attempt_id}' not found.", status_code=404)
                        if row["user_id"] != user_id:
                            raise RemediationError("Attempt belongs to another learner.", status_code=403)
                        if row["question_id"] != question_id or row["selected"] != selected_option:
                            raise RemediationError("Attempt question or selected option does not match remediation request.", status_code=422)
                        if row["correct"] == 1:
                            raise RemediationError("Remediation is only available for incorrect attempts.", status_code=422)
                        originating_attempt_id = row["attempt_key"]
                    else:
                        row = conn.execute(
                            "SELECT attempt_key, correct FROM university_attempts WHERE user_id = ? AND question_id = ? AND selected = ? ORDER BY rowid DESC LIMIT 1",
                            (user_id, question_id, selected_option),
                        ).fetchone()
                        if row:
                            if row["correct"] == 1:
                                raise RemediationError("Remediation is only available for incorrect attempts.", status_code=422)
                            originating_attempt_id = row["attempt_key"]
        except RemediationError:
            raise
        except Exception as exc:
            logger.warning("Could not verify attempt provenance in database: %s", exc)

        # Idempotency check for active session with matching idempotency key
        if idempotency_key:
            for existing in self._memory_sessions.values():
                if (
                    existing.user_id == user_id
                    and existing.question_id == question_id
                    and idempotency_key in existing.idempotency_keys
                ):
                    logger.info("Returning existing session %s for idempotency key %s", existing.session_id, idempotency_key)
                    last_turn = existing.turns[-1] if existing.turns else None
                    return RemediationTurnResponse(
                        session_id=existing.session_id,
                        turn_number=existing.turn_number,
                        max_turns=3,
                        is_complete=existing.is_complete,
                        lifecycle_state=existing.lifecycle_state,
                        outcome=existing.outcome,
                        remediation_status=existing.remediation_status,
                        pattern_id=existing.detected_gap.pattern_id,
                        reasoning_pattern=existing.detected_gap.reasoning_pattern,
                        strategy=existing.strategy,
                        timeline=existing.timeline,
                        tutor_message=last_turn.tutor_message if last_turn else "",
                        socratic_probe=last_turn.socratic_probe if last_turn else None,
                        citations=last_turn.citations if last_turn else [],
                        transfer_available=(existing.lifecycle_state == RemediationLifecycleState.AWAITING_TRANSFER),
                    )

        session_id = f"REM-{uuid.uuid4().hex[:12].upper()}"

        # 1. Deterministic hypothesis detection
        hypothesis: PatternHypothesis = self.detector.detect_hypothesis(
            question_id=question_id,
            selected_option=selected_option,
            topic=topic,
            attempt_id=attempt_id,
        )
        gap: DetectedLearningGap = self.detector.detect(
            question_id=question_id,
            selected_option=selected_option,
            topic=topic,
            attempt_id=attempt_id,
        )

        # 2. Select pedagogical strategy (default GUIDED_RECALL)
        strategy: SocraticStrategyType = self.strategy_engine.select_strategy(
            category=gap.category,
            override_strategy=gap.recommended_strategy,
        )

        # 3. Generate Turn 1 Probe
        intent, probe_question = self.strategy_engine.generate_turn_prompt(
            turn_number=1,
            strategy=strategy,
            gap=gap,
        )

        # 4. Invoke frozen TutorService via Bridge
        pedagogical_query = (
            f"The student selected distractor '{selected_option}' for question '{question_id}' on '{gap.topic}'. "
            f"Candidate pattern: {hypothesis.candidate_pattern}. Strategy: {strategy.value}. "
            f"Probe the student neutrally: {probe_question}"
        )
        tutor_response = self.bridge.invoke_tutor_turn(
            user_id=user_id,
            question_id=question_id,
            topic=gap.topic,
            selected_option=selected_option,
            turn_number=1,
            pedagogical_query=pedagogical_query,
            gap=gap,
            session_id=session_id,
            attempt_key=originating_attempt_id or attempt_id,
            probe_question=probe_question,
        )

        is_fallback = getattr(tutor_response, "fallback_applied", False) or getattr(tutor_response, "support_status", "") == "SAFE_FALLBACK"

        # 5. Build Initial Reasoning Timeline (5 stages)
        timeline = ReasoningTimelineItem(
            initial_pattern=f"Selected Option {selected_option}: {hypothesis.candidate_pattern}",
            learning_gap=f"Pedagogical category: {gap.category.value}. {hypothesis.detection_rationale}",
            guided_practice="Remediation concluded due to safety fallback" if is_fallback else "Turn 1: Socratic probe initiated",
            transfer_result="Remediation stopped safely; no transfer assessment performed." if is_fallback else "Awaiting independent transfer assessment",
            next_recommendation=None,
            corrected_reasoning=None,
            status="SAFETY_FALLBACK" if is_fallback else "IN_PROGRESS",
        )

        # 6. Assemble Turn Record
        effective_probe = None if is_fallback else (tutor_response.socratic_question or probe_question)
        effective_message = CANONICAL_SAFETY_FALLBACK_MESSAGE if is_fallback else tutor_response.message
        effective_citations = [] if is_fallback else [c.model_dump() for c in tutor_response.citations]
        turn_record = RemediationTurnRecord(
            turn_number=1,
            phase="PROBE",
            tutor_message=effective_message,
            socratic_probe=effective_probe,
            student_message=None,
            citations=effective_citations,
            is_safety_fallback=is_fallback,
        )

        # 7. Create Session State
        session = RemediationSessionState(
            session_id=session_id,
            user_id=user_id,
            original_attempt_id=originating_attempt_id or attempt_id or f"ATT-{uuid.uuid4().hex[:8]}",
            question_id=question_id,
            selected_option=selected_option,
            topic=gap.topic,
            turn_number=1,
            max_turns=3,
            is_complete=is_fallback,
            lifecycle_state=RemediationLifecycleState.COMPLETED if is_fallback else RemediationLifecycleState.REMEDIATING,
            outcome=RemediationOutcome.SAFETY_FALLBACK if is_fallback else None,
            remediation_status=RemediationStatus.UNRESOLVED if is_fallback else RemediationStatus.PROBING,
            detected_gap=gap,
            hypothesis=hypothesis,
            strategy=strategy,
            timeline=timeline,
            turns=[turn_record],
            idempotency_keys=[idempotency_key] if idempotency_key else [],
        )
        self._persist_session(session)

        return RemediationTurnResponse(
            session_id=session_id,
            turn_number=1,
            max_turns=3,
            is_complete=session.is_complete,
            lifecycle_state=session.lifecycle_state,
            outcome=session.outcome,
            remediation_status=session.remediation_status,
            pattern_id=hypothesis.pattern_id,
            reasoning_pattern=hypothesis.candidate_pattern,
            strategy=strategy,
            timeline=timeline,
            tutor_message=effective_message,
            socratic_probe=effective_probe,
            citations=effective_citations,
            transfer_available=False,
        )

    def advance_turn(
        self,
        session_id: str,
        user_id: str,
        student_message: str,
        idempotency_key: str | None = None,
    ) -> RemediationTurnResponse:
        """Advance the Socratic dialogue through Turn 2 (Guide) and Turn 3 (Consolidate)."""
        session = self.get_session(session_id, user_id=user_id)
        if not session:
            raise RemediationError(f"Remediation session '{session_id}' not found.", status_code=404)

        # Idempotency check
        if idempotency_key and idempotency_key in session.idempotency_keys:
            logger.info("Idempotent request received for session %s key %s", session_id, idempotency_key)
            last_turn = session.turns[-1] if session.turns else None
            is_fallback = session.outcome == RemediationOutcome.SAFETY_FALLBACK or session.timeline.status == "SAFETY_FALLBACK"
            return RemediationTurnResponse(
                session_id=session.session_id,
                turn_number=session.turn_number,
                max_turns=3,
                is_complete=session.is_complete,
                lifecycle_state=session.lifecycle_state,
                outcome=session.outcome,
                remediation_status=session.remediation_status,
                pattern_id=session.detected_gap.pattern_id,
                reasoning_pattern=session.detected_gap.reasoning_pattern,
                strategy=session.strategy,
                timeline=session.timeline,
                tutor_message=CANONICAL_SAFETY_FALLBACK_MESSAGE if is_fallback else (last_turn.tutor_message if last_turn else "Turn already recorded."),
                socratic_probe=None if is_fallback else (last_turn.socratic_probe if last_turn else None),
                citations=[] if is_fallback else (last_turn.citations if last_turn else []),
                transfer_available=(session.lifecycle_state == RemediationLifecycleState.AWAITING_TRANSFER and not is_fallback),
            )

        # Strict bound and terminal check
        if session.is_complete or session.lifecycle_state in (
            RemediationLifecycleState.AWAITING_TRANSFER,
            RemediationLifecycleState.COMPLETED,
        ):
            logger.info("Session %s is already at state %s", session_id, session.lifecycle_state)
            if session.lifecycle_state == RemediationLifecycleState.AWAITING_TRANSFER:
                session.assistance_invoked = True
                self._persist_session(session)
            is_fallback = session.outcome == RemediationOutcome.SAFETY_FALLBACK or session.timeline.status == "SAFETY_FALLBACK"
            last_turn = session.turns[-1] if session.turns else None
            return RemediationTurnResponse(
                session_id=session.session_id,
                turn_number=session.turn_number,
                max_turns=3,
                is_complete=session.is_complete,
                lifecycle_state=session.lifecycle_state,
                outcome=session.outcome,
                remediation_status=session.remediation_status,
                pattern_id=session.detected_gap.pattern_id,
                reasoning_pattern=session.detected_gap.reasoning_pattern,
                strategy=session.strategy,
                timeline=session.timeline,
                tutor_message=(
                    CANONICAL_SAFETY_FALLBACK_MESSAGE
                    if is_fallback
                    else (
                        "Socratic practice turns have concluded. "
                        "Please proceed to the independent transfer assessment to verify concept mastery."
                    )
                ),
                socratic_probe=None,
                citations=[] if is_fallback else (last_turn.citations if last_turn else []),
                transfer_available=(session.lifecycle_state == RemediationLifecycleState.AWAITING_TRANSFER and not is_fallback),
            )

        if session.turns:
            session.turns[-1].student_message = student_message

        next_turn = session.turn_number + 1

        if next_turn == 2:
            # Turn 2: GUIDE
            intent, guide_prompt = self.strategy_engine.generate_turn_prompt(
                turn_number=2,
                strategy=session.strategy,
                gap=session.detected_gap,
                student_message=student_message,
            )
            pedagogical_query = (
                f"For question '{session.question_id}' on '{session.topic}' regarding candidate pattern '{session.detected_gap.reasoning_pattern}': "
                f"Student response to probe: '{student_message}'. "
                f"Guide them through the biological mechanism: {guide_prompt}"
            )
            tutor_response = self.bridge.invoke_tutor_turn(
                user_id=user_id,
                question_id=session.question_id,
                topic=session.topic,
                selected_option=session.selected_option,
                turn_number=2,
                pedagogical_query=pedagogical_query,
                gap=session.detected_gap,
                session_id=session.session_id,
                attempt_key=session.original_attempt_id,
                probe_question=guide_prompt,
            )

            is_fallback = getattr(tutor_response, "fallback_applied", False) or getattr(tutor_response, "support_status", "") == "SAFE_FALLBACK"

            effective_message = CANONICAL_SAFETY_FALLBACK_MESSAGE if is_fallback else tutor_response.message
            effective_probe = None if is_fallback else (tutor_response.socratic_question or guide_prompt)
            effective_citations = [] if is_fallback else [c.model_dump() for c in tutor_response.citations]

            turn_record = RemediationTurnRecord(
                turn_number=2,
                phase="GUIDE",
                tutor_message=effective_message,
                socratic_probe=effective_probe,
                student_message=None,
                citations=effective_citations,
                is_safety_fallback=is_fallback,
            )

            session.turn_number = 2
            if is_fallback:
                session.lifecycle_state = RemediationLifecycleState.COMPLETED
                session.outcome = RemediationOutcome.SAFETY_FALLBACK
                session.is_complete = True
                session.remediation_status = RemediationStatus.UNRESOLVED
                session.timeline.status = "SAFETY_FALLBACK"
                session.timeline.guided_practice = "Remediation concluded due to safety fallback"
                session.timeline.transfer_result = "Remediation stopped safely; no transfer assessment performed."
            else:
                session.remediation_status = RemediationStatus.GUIDING
                session.timeline.guided_practice = "Turn 2: Mechanistic guidance provided"
                session.timeline.status = "IN_PROGRESS"

            session.turns.append(turn_record)
            if idempotency_key:
                session.idempotency_keys.append(idempotency_key)
            session.updated_at = time.time()
            self._persist_session(session)

            return RemediationTurnResponse(
                session_id=session.session_id,
                turn_number=2,
                max_turns=3,
                is_complete=session.is_complete,
                lifecycle_state=session.lifecycle_state,
                outcome=session.outcome,
                remediation_status=session.remediation_status,
                pattern_id=session.detected_gap.pattern_id,
                reasoning_pattern=session.detected_gap.reasoning_pattern,
                strategy=session.strategy,
                timeline=session.timeline,
                tutor_message=effective_message,
                socratic_probe=effective_probe,
                citations=effective_citations,
                transfer_available=False,
            )

        elif next_turn == 3:
            # Turn 3: CONSOLIDATE & CHECK READINESS
            intent, consolidate_prompt = self.strategy_engine.generate_turn_prompt(
                turn_number=3,
                strategy=session.strategy,
                gap=session.detected_gap,
                student_message=student_message,
            )
            pedagogical_query = (
                f"For question '{session.question_id}' on '{session.topic}': "
                f"Student response to guidance: '{student_message}'. "
                f"Synthesize the physiological concept neutrally and check readiness for independent assessment: {consolidate_prompt}"
            )
            tutor_response = self.bridge.invoke_tutor_turn(
                user_id=user_id,
                question_id=session.question_id,
                topic=session.topic,
                selected_option=session.selected_option,
                turn_number=3,
                pedagogical_query=pedagogical_query,
                gap=session.detected_gap,
                session_id=session.session_id,
                attempt_key=session.original_attempt_id,
                probe_question=consolidate_prompt,
            )

            is_fallback = getattr(tutor_response, "fallback_applied", False) or getattr(tutor_response, "support_status", "") == "SAFE_FALLBACK"

            effective_message = CANONICAL_SAFETY_FALLBACK_MESSAGE if is_fallback else tutor_response.message
            effective_probe = None if is_fallback else (tutor_response.socratic_question or consolidate_prompt)
            effective_citations = [] if is_fallback else [c.model_dump() for c in tutor_response.citations]

            turn_record = RemediationTurnRecord(
                turn_number=3,
                phase="CONSOLIDATE",
                tutor_message=effective_message,
                socratic_probe=effective_probe,
                student_message=student_message,
                citations=effective_citations,
                is_safety_fallback=is_fallback,
            )

            session.turn_number = 3
            if is_fallback:
                session.lifecycle_state = RemediationLifecycleState.COMPLETED
                session.outcome = RemediationOutcome.SAFETY_FALLBACK
                session.is_complete = True
                session.remediation_status = RemediationStatus.UNRESOLVED
                session.timeline.status = "SAFETY_FALLBACK"
                session.timeline.guided_practice = "Remediation concluded due to safety fallback"
                session.timeline.transfer_result = "Remediation stopped safely; no transfer assessment performed."
            else:
                session.lifecycle_state = RemediationLifecycleState.AWAITING_TRANSFER
                session.remediation_status = RemediationStatus.CONFIRMING
                session.timeline.guided_practice = "Completed 3 Socratic guidance turns"
                session.timeline.transfer_result = "Ready for independent transfer assessment"
                session.timeline.status = "AWAITING_TRANSFER"

            session.turns.append(turn_record)
            if idempotency_key:
                session.idempotency_keys.append(idempotency_key)
            session.updated_at = time.time()
            self._persist_session(session)

            return RemediationTurnResponse(
                session_id=session.session_id,
                turn_number=3,
                max_turns=3,
                is_complete=session.is_complete,
                lifecycle_state=session.lifecycle_state,
                outcome=session.outcome,
                remediation_status=session.remediation_status,
                pattern_id=session.detected_gap.pattern_id,
                reasoning_pattern=session.detected_gap.reasoning_pattern,
                strategy=session.strategy,
                timeline=session.timeline,
                tutor_message=effective_message,
                socratic_probe=effective_probe,
                citations=effective_citations,
                transfer_available=False if is_fallback else (session.lifecycle_state == RemediationLifecycleState.AWAITING_TRANSFER),
            )

        else:
            raise RemediationError("Turn progression out of bounds.", status_code=400)

    def abandon_session(
        self,
        session_id: str,
        user_id: str,
    ) -> RemediationTurnResponse:
        """Explicitly abandon an ongoing remediation session."""
        session = self.get_session(session_id, user_id=user_id)
        if not session:
            raise RemediationError(f"Remediation session '{session_id}' not found.", status_code=404)

        if session.is_complete:
            logger.info("Session %s is already completed with outcome %s", session_id, session.outcome)
            last_turn = session.turns[-1] if session.turns else None
            is_fallback = session.outcome == RemediationOutcome.SAFETY_FALLBACK or session.timeline.status == "SAFETY_FALLBACK"
            return RemediationTurnResponse(
                session_id=session.session_id,
                turn_number=session.turn_number,
                max_turns=3,
                is_complete=session.is_complete,
                lifecycle_state=session.lifecycle_state,
                outcome=session.outcome,
                remediation_status=session.remediation_status,
                pattern_id=session.detected_gap.pattern_id,
                reasoning_pattern=session.detected_gap.reasoning_pattern,
                strategy=session.strategy,
                timeline=session.timeline,
                tutor_message=CANONICAL_SAFETY_FALLBACK_MESSAGE if is_fallback else (last_turn.tutor_message if last_turn else "Session concluded."),
                socratic_probe=None,
                citations=[] if is_fallback else (last_turn.citations if last_turn else []),
                transfer_available=False,
            )

        session.lifecycle_state = RemediationLifecycleState.COMPLETED
        session.outcome = RemediationOutcome.ABANDONED
        session.is_complete = True
        session.timeline.status = "UNRESOLVED"
        session.timeline.transfer_result = "Remediation abandoned by learner."
        session.updated_at = time.time()

        self.learning_adapter.record_qualified_outcome(
            learner_id=user_id,
            session_id=session_id,
            original_question_id=session.question_id,
            topic=session.topic,
            subject="Renal physiology",
            outcome=RemediationOutcome.ABANDONED,
            transfer_attempt=None,
        )
        self._persist_session(session)

        last_turn = session.turns[-1] if session.turns else None
        return RemediationTurnResponse(
            session_id=session.session_id,
            turn_number=session.turn_number,
            max_turns=3,
            is_complete=True,
            lifecycle_state=session.lifecycle_state,
            outcome=session.outcome,
            remediation_status=session.remediation_status,
            pattern_id=session.detected_gap.pattern_id,
            reasoning_pattern=session.detected_gap.reasoning_pattern,
            strategy=session.strategy,
            timeline=session.timeline,
            tutor_message="Session exited. You can resume practice anytime.",
            socratic_probe=None,
            citations=last_turn.citations if last_turn else [],
            transfer_available=False,
        )

    def get_transfer_item(self, session_id: str, user_id: str) -> TransferItemDTO:
        """Fetch the eligible held-out item for this remediation session."""
        session = self.get_session(session_id, user_id=user_id)
        if not session:
            raise RemediationError(f"Remediation session '{session_id}' not found.", status_code=404)

        if session.lifecycle_state != RemediationLifecycleState.AWAITING_TRANSFER:
            raise RemediationError(
                f"Session {session_id} is not awaiting transfer assessment (current state: {session.lifecycle_state}).",
                status_code=422,
            )

        item = self.transfer_service.get_eligible_transfer_item(
            original_question_id=session.question_id,
            exposed_item_ids=[session.question_id],
        )
        if not item:
            raise RemediationError(
                f"No eligible held-out transfer item available for question '{session.question_id}'.",
                status_code=404,
            )

        session.transfer_question_id = item.question_id
        session.updated_at = time.time()
        self._persist_session(session)
        return item

    def submit_transfer(
        self,
        session_id: str,
        user_id: str,
        question_id: str,
        selected_option: str,
        was_assisted: bool = False,
        idempotency_key: str | None = None,
    ) -> TransferSubmissionResponse:
        """Score independent held-out transfer submission deterministically."""
        session = self.get_session(session_id, user_id=user_id)
        if not session:
            raise RemediationError(f"Remediation session '{session_id}' not found.", status_code=404)

        # Idempotency and interrupted-recovery check: if transfer attempt was already scored
        if session.transfer_attempt:
            logger.info("Transfer already scored for session %s (evidence_status=%s)", session_id, session.evidence_status)
            if idempotency_key and idempotency_key in session.idempotency_keys:
                if (
                    session.transfer_attempt.question_id != question_id
                    or session.transfer_attempt.submitted_option != selected_option
                ):
                    raise RemediationError("Idempotency key reused with conflicting transfer payload.", status_code=409)

            # Scenario A recovery: transfer decision durably persisted, Phase 2A delivery not yet started
            if session.evidence_status == "PENDING":
                session.evidence_status = "DELIVERING"
                self._persist_session(session)
                q_event, rec = self.learning_adapter.record_qualified_outcome(
                    learner_id=user_id,
                    session_id=session_id,
                    original_question_id=session.question_id,
                    topic=session.topic,
                    subject="Renal physiology",
                    outcome=session.outcome or RemediationOutcome.UNRESOLVED,
                    transfer_attempt=session.transfer_attempt,
                )
                session.evidence_status = "DELIVERED"
                session.lifecycle_state = RemediationLifecycleState.COMPLETED
                session.is_complete = True
                if rec:
                    session.timeline.next_recommendation = f"Recommended action: {rec.action.value} on {rec.topic}. {rec.reason}"
                session.updated_at = time.time()
                self._persist_session(session)

            # Scenario B / Narrow Interruption Window recovery:
            # Phase 2A delivery was in-flight when interrupted.
            elif session.evidence_status == "DELIVERING":
                if self.learning_adapter.has_durable_evidence_record(session_id):
                    # Scenario B: Durable deduplication record exists in SQLite.
                    # Delivery succeeded before crash; safe to complete adaptation without replaying into Phase 2A.
                    rec = None
                    try:
                        rec = self.learning_adapter.adaptive_service.get_top_recommendation(user_id)
                    except Exception as exc:
                        logger.warning("Could not fetch recommendation on recovery: %s", exc)
                    if rec:
                        session.timeline.next_recommendation = f"Recommended action: {rec.action.value} on {rec.topic}. {rec.reason}"
                    session.timeline.status = "COMPLETED"
                elif self.learning_adapter.has_evidence_for_session(session_id, user_id):
                    # Narrow Interruption Window:
                    # Phase 2A effect committed, but process crashed before remediation_learning_evidence was recorded.
                    # Delivery state is ambiguous. To guarantee zero duplicate learning effects, NEVER re-call Phase 2A.
                    # Do NOT falsely claim completed adaptation while delivery state is ambiguous.
                    session.timeline.status = "UNRESOLVED"
                    session.timeline.transfer_result = "Transfer demonstrated on this question (adaptation pending verification)"
                    session.timeline.next_recommendation = None
                else:
                    # Scenario A (interrupted when entering delivery before Phase 2A call):
                    # Phase 2A has not received evidence, deliver it now.
                    q_event, rec = self.learning_adapter.record_qualified_outcome(
                        learner_id=user_id,
                        session_id=session_id,
                        original_question_id=session.question_id,
                        topic=session.topic,
                        subject="Renal physiology",
                        outcome=session.outcome or RemediationOutcome.UNRESOLVED,
                        transfer_attempt=session.transfer_attempt,
                    )
                    if rec:
                        session.timeline.next_recommendation = f"Recommended action: {rec.action.value} on {rec.topic}. {rec.reason}"
                    session.timeline.status = "COMPLETED"

                session.evidence_status = "DELIVERED"
                session.lifecycle_state = RemediationLifecycleState.COMPLETED
                session.is_complete = True
                session.updated_at = time.time()
                self._persist_session(session)

            return TransferSubmissionResponse(
                session_id=session.session_id,
                outcome=session.outcome or RemediationOutcome.UNRESOLVED,
                is_correct=session.transfer_attempt.is_correct,
                explanation="Transfer assessment already completed for this session.",
                citations=[],
                timeline=session.timeline,
                next_recommendation={"explanation": session.timeline.next_recommendation} if session.timeline.next_recommendation else None,
            )

        if session.lifecycle_state != RemediationLifecycleState.AWAITING_TRANSFER:
            raise RemediationError(
                f"Session {session_id} is not awaiting transfer assessment (current state: {session.lifecycle_state}).",
                status_code=422,
            )

        # Invariant: Transfer item must have been dispensed by the server
        if not session.transfer_question_id:
            raise RemediationError(
                "Transfer item has not been dispensed by the server for this session.",
                status_code=422,
            )

        # Invariant: Submitted transfer question ID must match dispensed item
        if session.transfer_question_id != question_id:
            raise RemediationError(
                f"Submitted transfer question '{question_id}' does not match dispensed item '{session.transfer_question_id}'.",
                status_code=422,
            )

        # 1. Deterministic server-side scoring
        # Trust-boundary invariant: TRANSFER_CONFIRMED must never depend on a client-controlled boolean.
        authoritative_was_assisted = bool(
            was_assisted
            or session.assistance_invoked
        )

        outcome, attempt, explanation, citations = self.transfer_service.score_transfer_submission(
            original_question_id=session.question_id,
            question_id=question_id,
            selected_option=selected_option,
            was_assisted=authoritative_was_assisted,
        )

        # 2. Update session state with transfer decision/result
        session.transfer_attempt = attempt
        session.outcome = outcome

        if outcome == RemediationOutcome.TRANSFER_CONFIRMED:
            session.timeline.transfer_result = "Transfer demonstrated on this question"
            session.timeline.status = "COMPLETED"
        elif outcome == RemediationOutcome.TRANSFER_NOT_CONFIRMED:
            session.timeline.transfer_result = "More practice needed on this target concept"
            session.timeline.status = "UNRESOLVED"
        else:
            session.timeline.transfer_result = "Transfer unconfirmed (assisted attempt or unresolved)"
            session.timeline.status = "UNRESOLVED"

        # 3. Transfer result persistence: transfer attempt is durably committed before Phase 2A interaction
        session.evidence_status = "PENDING"
        session.updated_at = time.time()
        self._persist_session(session)

        # 4. Phase 2A learning evidence application boundary
        session.evidence_status = "DELIVERING"
        self._persist_session(session)

        q_event, rec = self.learning_adapter.record_qualified_outcome(
            learner_id=user_id,
            session_id=session_id,
            original_question_id=session.question_id,
            topic=session.topic,
            subject="Renal physiology",
            outcome=outcome,
            transfer_attempt=attempt,
        )

        # 5. Durable evidence-delivery/completion marker
        session.evidence_status = "DELIVERED"
        session.lifecycle_state = RemediationLifecycleState.COMPLETED
        session.is_complete = True

        if rec:
            session.timeline.next_recommendation = f"Recommended action: {rec.action.value} on {rec.topic}. {rec.reason}"
        else:
            session.timeline.next_recommendation = "Continue to next topic in Renal Physiology track."

        if idempotency_key:
            session.idempotency_keys.append(idempotency_key)
        session.updated_at = time.time()
        self._persist_session(session)

        # 6. Response
        return TransferSubmissionResponse(
            session_id=session.session_id,
            outcome=outcome,
            is_correct=attempt.is_correct,
            explanation=explanation,
            citations=citations,
            timeline=session.timeline,
            next_recommendation=rec.model_dump() if rec else None,
        )

    def abandon_session(
        self,
        session_id: str,
        user_id: str,
        reason: str = "Learner exited session",
    ) -> RemediationTurnResponse:
        """Explicitly abandon an in-flight remediation session."""
        session = self.get_session(session_id, user_id=user_id)
        if not session:
            raise RemediationError(f"Remediation session '{session_id}' not found.", status_code=404)

        session.lifecycle_state = RemediationLifecycleState.COMPLETED
        session.outcome = RemediationOutcome.ABANDONED
        session.is_complete = True
        session.timeline.status = "UNRESOLVED"
        session.timeline.transfer_result = f"Session abandoned: {reason}"
        session.updated_at = time.time()
        self._persist_session(session)

        # Notify Phase 2A without mastery increase
        self.learning_adapter.record_qualified_outcome(
            learner_id=user_id,
            session_id=session_id,
            original_question_id=session.question_id,
            topic=session.topic,
            subject="Renal physiology",
            outcome=RemediationOutcome.ABANDONED,
            transfer_attempt=None,
        )

        return RemediationTurnResponse(
            session_id=session.session_id,
            turn_number=session.turn_number,
            max_turns=3,
            is_complete=True,
            lifecycle_state=RemediationLifecycleState.COMPLETED,
            outcome=RemediationOutcome.ABANDONED,
            remediation_status=RemediationStatus.UNRESOLVED,
            pattern_id=session.detected_gap.pattern_id,
            reasoning_pattern=session.detected_gap.reasoning_pattern,
            strategy=session.strategy,
            timeline=session.timeline,
            tutor_message=f"Remediation session concluded ({reason}).",
            socratic_probe=None,
            citations=[],
            transfer_available=False,
        )
