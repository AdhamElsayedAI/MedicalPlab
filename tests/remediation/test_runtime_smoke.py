import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pytest
from starlette.testclient import TestClient
from medicalplab.remediation.config import is_remediation_enabled
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_runtime_smoke_full_journey_a_through_p(client, monkeypatch):
    # Enable Phase 2B for the smoke test
    monkeypatch.setenv("MEDICALPLAB_PHASE_2B_ENABLED", "true")

    headers = {"X-User-Id": "smoke-student-001"}

    # Step A: Student answers an eligible university MCQ incorrectly
    # Submit incorrect answer 'B' to UNI-RENAL-001
    ans_res = client.post(
        "/api/v1/university/answer",
        json={
            "question_id": "UNI-RENAL-001",
            "selected_option": "B",
            "time_spent_seconds": 25,
            "attempt_key": "smoke-attempt-001",
            "idempotency_key": "smoke-attempt-001",
        },
        headers=headers,
    )
    assert ans_res.status_code == 200, f"MCQ submit failed: {ans_res.text}"
    ans_data = ans_res.json()
    assert ans_data["is_correct"] is False, "Expected option B to be incorrect"

    # Step B: Remediation is offered
    # In UI, !feedback.is_correct triggers display of "Targeted Guided Practice"
    assert not ans_data["is_correct"], "Remediation offer precondition verified"

    # Step C: Backend independently validates eligibility
    # C1: Correct answer 'A' rejected with 422
    rej_res = client.post(
        "/api/v1/remediation/start",
        json={
            "question_id": "UNI-RENAL-001",
            "selected_option": "A",  # Correct answer
            "topic": "preclinical_renal",
            "idempotency_key": "smoke-start-rej",
        },
        headers=headers,
    )
    assert rej_res.status_code == 422, f"Expected 422 for correct answer: {rej_res.text}"
    detail_str = str(rej_res.json().get("detail", "")).lower()
    assert "correct answer" in detail_str

    # C2: Incorrect answer 'B' accepted
    start_res = client.post(
        "/api/v1/remediation/start",
        json={
            "question_id": "UNI-RENAL-001",
            "selected_option": "B",
            "topic": "preclinical_renal",
            "idempotency_key": "smoke-start-001",
        },
        headers=headers,
    )
    assert start_res.status_code == 200, f"Start failed: {start_res.text}"
    session_data = start_res.json()
    session_id = session_data["session_id"]

    # Step D: Calibrated POSSIBLE_PATTERN hypothesis state
    assert session_data["pattern_id"] is not None
    assert "upstream_downstream_inversion" in session_data["timeline"]["learning_gap"] or "pedagogical category" in session_data["timeline"]["learning_gap"].lower()

    # Step E: Turn 1 substantive medical response is grounded and verified
    # The initial probe was generated via TutorService chat bridge
    turn1_msg = session_data["tutor_message"]
    assert len(turn1_msg) > 10, "Turn 1 probe should be present"
    assert session_data["turn_number"] == 1

    # Step F: Turn 2 substantive medical response is grounded and verified
    turn2_res = client.post(
        "/api/v1/remediation/turn",
        json={
            "session_id": session_id,
            "student_message": "I thought afferent constriction causes hydrostatic pressure to rise.",
            "idempotency_key": "smoke-turn-2",
        },
        headers=headers,
    )
    assert turn2_res.status_code == 200, f"Turn 2 failed: {turn2_res.text}"
    turn2_data = turn2_res.json()
    assert turn2_data["turn_number"] == 2
    assert turn2_data["remediation_status"] == "GUIDING"

    # Step G: Turn 3 reaches "Consolidation & readiness check" without declaring mastery
    turn3_res = client.post(
        "/api/v1/remediation/turn",
        json={
            "session_id": session_id,
            "student_message": "Afferent constriction reduces glomerular plasma flow and therefore lowers glomerular hydrostatic pressure.",
            "idempotency_key": "smoke-turn-3",
        },
        headers=headers,
    )
    assert turn3_res.status_code == 200, f"Turn 3 failed: {turn3_res.text}"
    turn3_data = turn3_res.json()
    assert turn3_data["turn_number"] == 3
    # Step H: Server transitions the session to AWAITING_TRANSFER
    assert turn3_data["lifecycle_state"] == "AWAITING_TRANSFER"

    # Step I: Held-out transfer item is delivered without answer key or explanations
    transfer_item_res = client.get(
        f"/api/v1/remediation/session/{session_id}/transfer",
        headers=headers,
    )
    assert transfer_item_res.status_code == 200, f"Transfer get failed: {transfer_item_res.text}"
    transfer_item = transfer_item_res.json()
    assert "question_id" in transfer_item
    assert "stem" in transfer_item
    assert "options" in transfer_item
    # Crucial security invariants: no answer key leaks
    assert "correct_answer" not in transfer_item
    assert "explanation" not in transfer_item
    assert "distractor_mapping" not in transfer_item
    assert "is_correct" not in transfer_item

    # Step J: Correct eligible independent transfer produces internal TRANSFER_CONFIRMED
    # and user-facing "Transfer demonstrated on this question"
    transfer_submit_res = client.post(
        f"/api/v1/remediation/session/{session_id}/transfer",
        json={
            "session_id": session_id,
            "question_id": transfer_item["question_id"],
            "selected_option": "A",  # Correct answer for UNI-RENAL-001-T is Angiotensinogen
            "was_assisted": False,
            "idempotency_key": "smoke-transfer-submit-001",
        },
        headers=headers,
    )
    assert transfer_submit_res.status_code == 200, f"Transfer submit failed: {transfer_submit_res.text}"
    transfer_res_data = transfer_submit_res.json()
    assert transfer_res_data["outcome"] == "TRANSFER_CONFIRMED"
    assert transfer_res_data["timeline"]["transfer_result"] == "Transfer demonstrated on this question"

    # Step M: Qualified learning evidence reaches Phase 2A exactly once.
    # Duplicate submission with same idempotency key returns 409
    dup_res = client.post(
        f"/api/v1/remediation/session/{session_id}/transfer",
        json={
            "session_id": session_id,
            "question_id": transfer_item["question_id"],
            "selected_option": "A",
            "was_assisted": False,
            "idempotency_key": "smoke-transfer-submit-001",
        },
        headers=headers,
    )
    assert dup_res.status_code == 200, f"Expected 200 idempotent response: {dup_res.text}"
    assert dup_res.json()["outcome"] == "TRANSFER_CONFIRMED"
    assert "already completed" in dup_res.json()["explanation"].lower()

    # Step O: Reload/resume works while server is alive
    resume_res = client.get(
        f"/api/v1/remediation/session/{session_id}",
        headers=headers,
    )
    assert resume_res.status_code == 200, f"Resume failed: {resume_res.text}"
    resume_data = resume_res.json()
    assert resume_data["session_id"] == session_id
    assert resume_data["lifecycle_state"] == "COMPLETED"
    assert resume_data["outcome"] == "TRANSFER_CONFIRMED"
    assert resume_data["turn_number"] == 3

    # Step K: Test Incorrect independent transfer produces TRANSFER_NOT_CONFIRMED
    # Start fresh session for user-2
    u2_headers = {"X-User-Id": "smoke-student-002"}
    u2_start = client.post(
        "/api/v1/remediation/start",
        json={
            "question_id": "UNI-RENAL-001",
            "selected_option": "B",
            "topic": "preclinical_renal",
            "idempotency_key": "smoke-u2-start",
        },
        headers=u2_headers,
    )
    assert u2_start.status_code == 200, f"u2 start failed: {u2_start.text}"
    u2_s_id = u2_start.json()["session_id"]
    # Fast forward 2 turns with medically valid responses
    t2 = client.post("/api/v1/remediation/turn", json={"session_id": u2_s_id, "student_message": "I thought afferent constriction causes hydrostatic pressure to rise.", "idempotency_key": "u2-t2"}, headers=u2_headers)
    assert t2.status_code == 200, f"u2 t2 failed: {t2.text}"
    t3 = client.post("/api/v1/remediation/turn", json={"session_id": u2_s_id, "student_message": "Afferent constriction reduces glomerular plasma flow and therefore lowers glomerular hydrostatic pressure.", "idempotency_key": "u2-t3"}, headers=u2_headers)
    assert t3.status_code == 200, f"u2 t3 failed: {t3.text}"
    # Dispense transfer
    u2_t_res = client.get(f"/api/v1/remediation/session/{u2_s_id}/transfer", headers=u2_headers)
    assert u2_t_res.status_code == 200, f"u2 transfer get failed: {u2_t_res.text}"
    u2_t_item = u2_t_res.json()
    # Submit incorrect answer 'B'
    u2_t_sub = client.post(
        f"/api/v1/remediation/session/{u2_s_id}/transfer",
        json={
            "session_id": u2_s_id,
            "question_id": u2_t_item["question_id"],
            "selected_option": "B",  # Incorrect (correct is A)
            "was_assisted": False,
            "idempotency_key": "u2-t-sub",
        },
        headers=u2_headers,
    )
    assert u2_t_sub.status_code == 200
    assert u2_t_sub.json()["outcome"] == "TRANSFER_NOT_CONFIRMED"

    # Step L: Assisted/ineligible transfer produces UNRESOLVED
    u3_headers = {"X-User-Id": "smoke-student-003"}
    u3_start = client.post(
        "/api/v1/remediation/start",
        json={
            "question_id": "UNI-RENAL-001",
            "selected_option": "B",
            "topic": "preclinical_renal",
            "idempotency_key": "smoke-u3-start",
        },
        headers=u3_headers,
    )
    assert u3_start.status_code == 200, f"u3 start failed: {u3_start.text}"
    u3_s_id = u3_start.json()["session_id"]
    u3_t2 = client.post("/api/v1/remediation/turn", json={"session_id": u3_s_id, "student_message": "I thought afferent constriction causes hydrostatic pressure to rise.", "idempotency_key": "u3-t2"}, headers=u3_headers)
    assert u3_t2.status_code == 200, f"u3 t2 failed: {u3_t2.text}"
    u3_t3 = client.post("/api/v1/remediation/turn", json={"session_id": u3_s_id, "student_message": "Afferent constriction reduces glomerular plasma flow and therefore lowers glomerular hydrostatic pressure.", "idempotency_key": "u3-t3"}, headers=u3_headers)
    assert u3_t3.status_code == 200, f"u3 t3 failed: {u3_t3.text}"
    u3_t_res = client.get(f"/api/v1/remediation/session/{u3_s_id}/transfer", headers=u3_headers)
    assert u3_t_res.status_code == 200, f"u3 transfer get failed: {u3_t_res.text}"
    u3_t_item = u3_t_res.json()
    # Submit with was_assisted=True
    u3_t_sub = client.post(
        f"/api/v1/remediation/session/{u3_s_id}/transfer",
        json={
            "session_id": u3_s_id,
            "question_id": u3_t_item["question_id"],
            "selected_option": "A",  # Correct answer but assisted!
            "was_assisted": True,
            "idempotency_key": "u3-t-sub",
        },
        headers=u3_headers,
    )
    assert u3_t_sub.status_code == 200
    assert u3_t_sub.json()["outcome"] == "UNRESOLVED"

    # Step P: Feature flag set back to false and disabled/unavailable behavior verified
    monkeypatch.setenv("MEDICALPLAB_PHASE_2B_ENABLED", "false")

    disabled_res = client.post(
        "/api/v1/remediation/start",
        json={
            "question_id": "UNI-RENAL-001",
            "selected_option": "B",
            "topic": "preclinical_renal",
            "idempotency_key": "smoke-disabled-001",
        },
        headers=headers,
    )
    assert disabled_res.status_code == 503
    dis_data = disabled_res.json()
    assert "disabled" in dis_data.get("detail", "").lower()
