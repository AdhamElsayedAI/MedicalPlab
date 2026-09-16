"""Regression tests for cross-question remediation context binding and isolation.

Ensures that sequential remediation sessions for different questions:
1. Bind to their own originating attempt and question ID;
2. Do NOT leak or reuse previous question text, probes, or citations;
3. Reference the exact medical concept and evidence for the active question;
4. Maintain session isolation when executed back-to-back for the same learner.
"""
from __future__ import annotations

import sqlite3
import uuid
import pytest

from medicalplab.remediation.controller import RemediationLoopController
from medicalplab.remediation.bridge import RemediationTutorBridge
from medicalplab.remediation.models import (
    ReasoningPatternCategory,
    RemediationLifecycleState,
    SocraticStrategyType,
)
from medicalplab.tutor.session import DEFAULT_UNIVERSITY_DB


@pytest.fixture
def clean_db():
    """Ensure attempts exist for the test learner in SQLite."""
    conn = sqlite3.connect(DEFAULT_UNIVERSITY_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create attempts table if not exists (standard schema)
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS university_attempts (
            user_id TEXT,
            attempt_key TEXT UNIQUE,
            question_id TEXT,
            subject TEXT,
            topic TEXT,
            selected TEXT,
            correct INTEGER
        )"""
    )
    conn.commit()
    conn.close()
    yield DEFAULT_UNIVERSITY_DB


def test_sequential_cross_question_remediation_isolation(clean_db):
    """Start remediation for Question A (renin/angiotensinogen), then Question B (AT1R).

    Assert that Session B:
    - references B's concept (AT1R / Ang II receptor);
    - does NOT contain A's question-specific probe/context ('What substrate does active renin act upon');
    - uses B's originating question ID and attempt key;
    - does NOT receive A's cached evidence/context.
    """
    learner_id = f"learner_{uuid.uuid4().hex[:8]}"
    attempt_a = f"att_a_{uuid.uuid4().hex[:8]}"
    attempt_b = f"att_b_{uuid.uuid4().hex[:8]}"

    # Seed university attempts
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO university_attempts (user_id, attempt_key, question_id, subject, topic, selected, correct) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (learner_id, attempt_a, "UNI-RENAL-001", "Renal physiology", "RAAS mechanisms", "B", 0),
    )
    cursor.execute(
        "INSERT INTO university_attempts (user_id, attempt_key, question_id, subject, topic, selected, correct) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (learner_id, attempt_b, "UNI-RENAL-003", "Renal physiology", "RAAS mechanisms", "B", 0),
    )
    conn.commit()
    conn.close()

    controller = RemediationLoopController(db_path=clean_db)

    # 1. Start Remediation for Question A (UNI-RENAL-001: Renin / substrate)
    res_a = controller.start_session(
        user_id=learner_id,
        question_id="UNI-RENAL-001",
        selected_option="B",
        topic="RAAS mechanisms",
        attempt_id=attempt_a,
    )

    assert res_a.session_id.startswith("REM-")
    assert res_a.turn_number == 1
    # Question A concerns renin cleaving substrate (angiotensinogen)
    assert "renin" in res_a.tutor_message.lower() or "angiotensinogen" in res_a.tutor_message.lower()
    assert "upstream stimulus" in res_a.socratic_probe.lower() or "substrate" in res_a.tutor_message.lower()

    # 2. Advance Session A through a turn
    res_a_t2 = controller.advance_turn(
        session_id=res_a.session_id,
        user_id=learner_id,
        student_message="Renin cleaves angiotensinogen into Ang I.",
    )
    assert res_a_t2.turn_number == 2

    # 3. Now start Remediation for Question B (UNI-RENAL-003: AT1 receptor) for SAME learner
    res_b = controller.start_session(
        user_id=learner_id,
        question_id="UNI-RENAL-003",
        selected_option="B",
        topic="RAAS mechanisms",
        attempt_id=attempt_b,
    )

    # STRICT ASSERTIONS ON ISOLATION:
    # A. Distinct session ID
    assert res_b.session_id != res_a.session_id
    assert res_b.turn_number == 1

    # B. Session Question Binding in Controller State
    session_b_state = controller.get_session(res_b.session_id, user_id=learner_id)
    assert session_b_state is not None
    assert session_b_state.question_id == "UNI-RENAL-003"
    assert session_b_state.original_attempt_id == attempt_b
    assert session_b_state.selected_option == "B"
    assert session_b_state.detected_gap.category == ReasoningPatternCategory.RECEPTOR_SPECIFICITY_CONFUSION

    # C. Content must reference Question B's concept (AT1R / Ang II receptor)
    msg_b_lower = res_b.tutor_message.lower()
    probe_b_lower = (res_b.socratic_probe or "").lower()
    assert "at1r" in msg_b_lower or "receptor" in msg_b_lower

    # D. Content must NOT contain Question A's question-specific probe or context
    assert "what substrate does active renin act upon" not in probe_b_lower
    assert "what substrate does active renin act upon" not in msg_b_lower
    assert "substrate must be present before any downstream conversion" not in probe_b_lower

    # E. Evidence citations must be bound to Question B
    assert len(res_b.citations) > 0
    citation_text = " ".join(c.get("quote", "").lower() for c in res_b.citations)
    assert "at1r" in citation_text or "receptor" in citation_text

    # F. Advance Session B to Turn 2 and verify guidance probe is receptor-specific
    res_b_t2 = controller.advance_turn(
        session_id=res_b.session_id,
        user_id=learner_id,
        student_message="Ang II acts on the AT1 receptor.",
    )
    assert res_b_t2.turn_number == 2
    probe_b_t2_lower = (res_b_t2.socratic_probe or "").lower()
    # Must NOT ask about enzyme preparing substrate
    assert "upstream enzyme prepare the substrate" not in probe_b_t2_lower
    assert "receptor" in probe_b_t2_lower or "effector" in probe_b_t2_lower or "response" in probe_b_t2_lower

    # G. Advance Session B to Turn 3 and verify it concludes dialogue
    res_b_t3 = controller.advance_turn(
        session_id=res_b.session_id,
        user_id=learner_id,
        student_message="The AT1 receptor mediates vasoconstriction and classical RAAS effects.",
    )
    assert res_b_t3.turn_number == 3
    assert res_b_t3.lifecycle_state == RemediationLifecycleState.AWAITING_TRANSFER
    assert res_b_t3.transfer_available is True


def test_back_to_back_remediation_sessions_same_learner(clean_db):
    """Test two remediation sessions back-to-back for the same learner on two different questions."""
    learner_id = f"learner_{uuid.uuid4().hex[:8]}"
    att_1 = f"att_1_{uuid.uuid4().hex[:8]}"
    att_2 = f"att_2_{uuid.uuid4().hex[:8]}"

    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO university_attempts (user_id, attempt_key, question_id, subject, topic, selected, correct) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (learner_id, att_1, "UNI-RENAL-002", "Renal physiology", "RAAS mechanisms", "A", 0),
    )
    cursor.execute(
        "INSERT INTO university_attempts (user_id, attempt_key, question_id, subject, topic, selected, correct) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (learner_id, att_2, "UNI-RENAL-003", "Renal physiology", "RAAS mechanisms", "A", 0),
    )
    conn.commit()
    conn.close()

    controller = RemediationLoopController(db_path=clean_db)

    # Session 1 for UNI-RENAL-002 (ACE enzyme)
    s1 = controller.start_session(
        user_id=learner_id,
        question_id="UNI-RENAL-002",
        selected_option="A",
        topic="RAAS mechanisms",
        attempt_id=att_1,
    )
    assert "ace" in s1.tutor_message.lower() or "converting enzyme" in s1.tutor_message.lower()
    s1_state = controller.get_session(s1.session_id, user_id=learner_id)
    assert s1_state.question_id == "UNI-RENAL-002"

    # Session 2 for UNI-RENAL-003 (AT1 receptor)
    s2 = controller.start_session(
        user_id=learner_id,
        question_id="UNI-RENAL-003",
        selected_option="A",
        topic="RAAS mechanisms",
        attempt_id=att_2,
    )
    assert s2.session_id != s1.session_id
    s2_state = controller.get_session(s2.session_id, user_id=learner_id)
    assert s2_state.question_id == "UNI-RENAL-003"
    assert "at1r" in s2.tutor_message.lower() or "receptor" in s2.tutor_message.lower()
    # Confirm S2 did not inherit S1's ACE-exclusive message
    assert "ang i is cleaved by angiotensin-converting enzyme" not in s2.tutor_message.lower()
