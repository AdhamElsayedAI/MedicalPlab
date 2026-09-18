"""MedicalPlab Phase 6: Cross-Module Integration End-to-End Test Suite.

Verifies that University, PLAB, 3D Anatomy, Grounded Tutor, Adaptive Learning,
Socratic Remediation, and Learning Intelligence form ONE coherent startup product.

Tests:
- Scenario A: University Attempt -> LearningEvent -> Adaptive State Observable
- Scenario B: PLAB Question -> Evaluation -> LearningEvent -> Adaptive State Observable
- Scenario C: PLAB Reasoning Gap -> ReasoningPatternDetectionEngine -> Remediation -> Transfer
- Scenario D: Grounded Medical Explanation Convergence (Tutor -> RAG -> Verification)
- Scenario E: 3D Anatomy -> Meaningful Challenge Event -> Adaptive Learning Signal
- Scenario F: Single Stable Learner Identity across all modules
- Scenario G: Strict Cross-Learner Data Isolation
- Negative Integration Tests: fail-closed safety, permissions, and invalid states
"""
from __future__ import annotations

import os
import sqlite3
import time
import uuid
import pytest
from fastapi.testclient import TestClient

from main import app
from medicalplab.plab.pilot import PLABPilotService
from medicalplab.stage_g.product_api import configure_plab_service, configure_tutor_service
from medicalplab.tutor.provider import StubGenerativeProvider
from medicalplab.tutor.service import TutorService


@pytest.fixture(autouse=True)
def setup_integration_env(tmp_path, monkeypatch):
    """Ensure predictable, isolated test environment for Phase 6 tests."""
    monkeypatch.setenv("MEDICALPLAB_PHASE_2B_ENABLED", "1")
    monkeypatch.setenv("MEDICALPLAB_ANATOMY_3D_ENABLED", "1")
    monkeypatch.setenv("MEDICALPLAB_RUNTIME_MODE", "pilot")
    monkeypatch.setenv("MEDICALPLAB_PLAB_PREVIEW_QA", "1")
    
    # Configure deterministic PLAB service in preview mode
    plab_svc = PLABPilotService.load_default(preview_qa=True, enable_persistence=False)
    configure_plab_service(plab_svc)

    # Configure deterministic tutor provider
    stub_provider = StubGenerativeProvider()
    tutor_svc = TutorService(provider=stub_provider)
    configure_tutor_service(tutor_svc)

    yield



@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ============================================================================
# SCENARIO A — UNIVERSITY JOURNEY
# ============================================================================

def test_scenario_a_university_attempt_to_adaptive_state(client: TestClient):
    """Scenario A: Same learner attempts University question, event emits, and Adaptive state reflects it."""
    learner_id = f"stu_uni_{uuid.uuid4().hex[:8]}"
    headers = {"X-User-Id": learner_id}

    # 1. Fetch available subjects & questions
    sub_res = client.get("/api/v1/university/subjects", headers=headers)
    assert sub_res.status_code == 200
    subjects = sub_res.json().get("items", [])
    assert len(subjects) > 0

    # 2. Submit answer to a university question
    ans_payload = {
        "question_id": "UNI-RENAL-001",
        "selected_option": "A",  # Correct answer (Angiotensinogen)
        "idempotency_key": f"key-{uuid.uuid4().hex[:10]}",
    }
    ans_res = client.post("/api/v1/university/answer", json=ans_payload, headers=headers)
    assert ans_res.status_code == 200
    ans_data = ans_res.json()
    assert ans_data["is_correct"] is True

    # 3. Verify Adaptive state observes the attempt
    adapt_res = client.get("/api/v1/adaptive/state", headers=headers)
    assert adapt_res.status_code == 200
    adapt_data = adapt_res.json()
    assert adapt_data["learner_id"] == learner_id
    assert adapt_data["total_attempts"] >= 1
    assert adapt_data["correct_attempts"] >= 1


# ============================================================================
# SCENARIO B — PLAB SUCCESS JOURNEY
# ============================================================================

def test_scenario_b_plab_success_to_adaptive_and_progress(client: TestClient):
    """Scenario B: Learner answers PLAB question, evaluates correctly, and Adaptive/PLAB progress updates."""
    learner_id = f"stu_plab_{uuid.uuid4().hex[:8]}"
    headers = {"X-User-Id": learner_id}

    eval_payload = {
        "question_id": "PLAB-CARD-0001",
        "selected_option": "A",  # Correct answer (Amlodipine)
        "idempotency_key": f"plab-idem-{uuid.uuid4().hex[:10]}",
        "response_time_ms": 8200,
    }
    eval_res = client.post("/api/v1/plab/evaluate", json=eval_payload, headers=headers)
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["correct"] is True
    assert eval_data["remediation"]["eligible"] is False

    # Check PLAB module-owned progress
    prog_res = client.get("/api/v1/plab/progress", headers=headers)
    assert prog_res.status_code == 200
    assert prog_res.json()["total_attempts"] == 1

    # Check Adaptive state observes the PLAB attempt
    adapt_res = client.get("/api/v1/adaptive/state", headers=headers)
    assert adapt_res.status_code == 200
    adapt_data = adapt_res.json()
    assert adapt_data["total_attempts"] >= 1
    assert any(a["question_id"] == "PLAB-CARD-0001" for a in adapt_data["recent_activity"])


# ============================================================================
# SCENARIO C — REASONING GAP & REMEDIATION BRIDGE
# ============================================================================

def test_scenario_c_plab_reasoning_gap_to_socratic_remediation_and_transfer(client: TestClient):
    """Scenario C: Cross-module reasoning gap triggers Socratic loop and held-out transfer.

    Proves:
    1. Wrong answer alone does NOT prove misconception: PLAB preview distractor without
       taxonomy mapping fails closed to neutral guidance (no overclaimed reasoning pattern).
    2. Validated University reasoning path (UNI-RENAL-001 option B -> PATTERN-RAAS-SUB-01)
       initiates bounded 3-turn Socratic remediation and independent transfer confirmation.
    """
    learner_id = f"stu_rem_{uuid.uuid4().hex[:8]}"
    headers = {"X-User-Id": learner_id}

    # 1. PLAB Preview QA evaluation: Wrong answer != misconception (unmapped distractor fails closed)
    plab_payload = {
        "question_id": "PLAB-CARD-0001",
        "selected_option": "B",  # Ramipril (guideline selection error; unmapped in reasoning taxonomy)
        "idempotency_key": f"plab-eval-{uuid.uuid4().hex[:10]}",
    }
    res_plab = client.post("/api/v1/plab/evaluate", json=plab_payload, headers=headers)
    assert res_plab.status_code == 200
    plab_data = res_plab.json()
    assert plab_data["correct"] is False
    assert plab_data["remediation"]["eligible"] is False
    assert "Wrong answer did not match" in plab_data["remediation"]["reason"]

    # 2. Validated University reasoning path: UNI-RENAL-001 option B -> PATTERN-RAAS-SUB-01
    uni_idem = f"uni-att-{uuid.uuid4().hex[:10]}"
    uni_payload = {
        "question_id": "UNI-RENAL-001",
        "selected_option": "B",  # Selected Angiotensin II instead of Angiotensinogen
        "idempotency_key": uni_idem,
    }
    res_uni = client.post("/api/v1/university/answer", json=uni_payload, headers=headers)
    assert res_uni.status_code == 200
    uni_data = res_uni.json()
    assert uni_data["is_correct"] is False

    # 3. Start Socratic Remediation Session (Turn 1: Probe)
    start_payload = {
        "question_id": "UNI-RENAL-001",
        "selected_option": "B",
        "topic": "RAAS mechanisms",
        "attempt_id": uni_idem,
        "idempotency_key": f"rem-start-{uuid.uuid4().hex[:8]}",
    }
    rem_start_res = client.post("/api/v1/remediation/start", json=start_payload, headers=headers)
    assert rem_start_res.status_code == 200
    rem_start_data = rem_start_res.json()
    session_id = rem_start_data["session_id"]
    assert rem_start_data["turn_number"] == 1
    assert rem_start_data["is_complete"] is False
    assert rem_start_data["pattern_id"] == "PATTERN-RAAS-SUB-01"

    # 4. Advance Dialogue: Turn 2 (Guide)
    turn2_payload = {
        "session_id": session_id,
        "student_message": "Renin is released by juxtaglomerular cells in response to decreased renal perfusion.",
        "idempotency_key": f"turn2-{uuid.uuid4().hex[:8]}",
    }
    turn2_res = client.post("/api/v1/remediation/turn", json=turn2_payload, headers=headers)
    assert turn2_res.status_code == 200
    turn2_data = turn2_res.json()
    assert turn2_data["turn_number"] == 2

    # 5. Advance Dialogue: Turn 3 (Consolidate & Transfer Readiness)
    turn3_payload = {
        "session_id": session_id,
        "student_message": "Active renin cleaves circulating angiotensinogen into angiotensin I, acting on the upstream precursor.",
        "idempotency_key": f"turn3-{uuid.uuid4().hex[:8]}",
    }
    turn3_res = client.post("/api/v1/remediation/turn", json=turn3_payload, headers=headers)
    assert turn3_res.status_code == 200
    turn3_data = turn3_res.json()
    assert turn3_data["turn_number"] == 3
    assert turn3_data["transfer_available"] is True

    # 6. Retrieve Held-out Transfer Item (ensure answer keys stripped)
    item_res = client.get(f"/api/v1/remediation/session/{session_id}/transfer", headers=headers)
    assert item_res.status_code == 200
    transfer_item = item_res.json()
    assert "correct_answer" not in transfer_item
    assert "explanation" not in transfer_item
    assert transfer_item["question_id"] == "UNI-RENAL-001-T"

    # 7. Submit Transfer Answer (Option A: Angiotensinogen cleavage)
    transfer_payload = {
        "session_id": session_id,
        "question_id": "UNI-RENAL-001-T",
        "selected_option": "A",
        "was_assisted": False,
        "idempotency_key": f"tf-sub-{uuid.uuid4().hex[:8]}",
    }
    tf_res = client.post(f"/api/v1/remediation/session/{session_id}/transfer", json=transfer_payload, headers=headers)
    assert tf_res.status_code == 200
    tf_data = tf_res.json()
    assert tf_data["outcome"] == "TRANSFER_CONFIRMED"
    assert tf_data["is_correct"] is True


# ============================================================================
# SCENARIO D — GROUNDED EXPLANATION CONVERGENCE
# ============================================================================

def test_scenario_d_grounded_tutor_explanation(client: TestClient):
    """Scenario D: AI explanation queries route strictly through TutorService and evidence engine."""
    learner_id = f"stu_tutor_{uuid.uuid4().hex[:8]}"
    headers = {"X-User-Id": learner_id}

    chat_payload = {
        "query": "Explain the role of active renin in cleavage of circulating angiotensinogen.",
        "mode": "mechanistic_explanation",
        "topic": "Renal physiology",
        "question_id": "UNI-RENAL-001",
    }
    chat_res = client.post("/api/v1/tutor/chat", json=chat_payload, headers=headers)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["support_status"] in {"GROUNDED", "VERIFIED", "SUPPORTED", "SAFE_FALLBACK"}
    assert "response_id" in chat_data


# ============================================================================
# SCENARIO E — 3D ANATOMY ADAPTIVE INTEGRATION
# ============================================================================

def test_scenario_e_3d_anatomy_session_and_deterministic_challenge(client: TestClient):
    """Scenario E: Anatomy session start, challenge submission, and deterministic scoring reflected in progress."""
    learner_id = f"stu_anat_{uuid.uuid4().hex[:8]}"
    headers = {"X-User-Id": learner_id}

    # 1. Start session
    start_payload = {
        "learner_id": learner_id,
        "learning_objective": "RENAL_BLOOD_FLOW_AND_HILUM",
    }
    start_res = client.post("/api/v1/anatomy/session/start", json=start_payload, headers=headers)
    assert start_res.status_code == 200
    session_data = start_res.json()
    session_id = session_data["session"]["session_id"]

    # 2. Submit deterministic challenge: correct target is renal_artery_left
    chal_payload = {
        "learner_id": learner_id,
        "selected_structure_id": "renal_artery_left",
    }
    chal_res = client.post(f"/api/v1/anatomy/session/{session_id}/challenge", json=chal_payload, headers=headers)
    assert chal_res.status_code == 200
    chal_data = chal_res.json()
    assert chal_data["is_correct"] is True
    assert chal_data["target_structure_id"] == "renal_artery_left"

    # 3. Verify unified progress reflects anatomy activity
    prog_res = client.get("/api/v1/learner/progress", headers=headers)
    assert prog_res.status_code == 200
    prog_data = prog_res.json()
    assert prog_data["anatomy"]["total_sessions"] >= 1
    assert prog_data["anatomy"]["challenges_passed"] >= 1
    assert "anatomy" in prog_data["summary"]["active_modules"]


# ============================================================================
# SCENARIO F — SINGLE STABLE LEARNER IDENTITY
# ============================================================================

def test_scenario_f_single_learner_identity_across_all_modules(client: TestClient):
    """Scenario F: One unified identity flows through University, PLAB, Anatomy, and Progress."""
    learner_id = f"stu_unified_{uuid.uuid4().hex[:8]}"
    headers = {"X-User-Id": learner_id}

    # University attempt
    client.post(
        "/api/v1/university/answer",
        json={"question_id": "UNI-RENAL-001", "selected_option": "A", "idempotency_key": f"uni-{uuid.uuid4().hex[:8]}"},
        headers=headers,
    )

    # PLAB attempt
    client.post(
        "/api/v1/plab/evaluate",
        json={"question_id": "PLAB-CARD-0001", "selected_option": "A", "idempotency_key": f"plab-{uuid.uuid4().hex[:8]}"},
        headers=headers,
    )

    # Anatomy session
    client.post(
        "/api/v1/anatomy/session/start",
        json={"learner_id": learner_id, "learning_objective": "RENAL_BLOOD_FLOW_AND_HILUM"},
        headers=headers,
    )

    # Check Unified Progress reflects all activity under this single identity
    prog_res = client.get("/api/v1/learner/progress", headers=headers)
    assert prog_res.status_code == 200
    data = prog_res.json()
    assert data["learner_id"] == learner_id
    assert "university" in data["summary"]["active_modules"]
    assert "plab" in data["summary"]["active_modules"]
    assert "anatomy" in data["summary"]["active_modules"]


# ============================================================================
# SCENARIO G — STRICT CROSS-LEARNER DATA ISOLATION
# ============================================================================

def test_scenario_g_cross_learner_data_isolation(client: TestClient):
    """Scenario G: Learner A activity is completely invisible in Learner B state and progress."""
    learner_a = f"stu_a_{uuid.uuid4().hex[:8]}"
    learner_b = f"stu_b_{uuid.uuid4().hex[:8]}"

    # Learner A engages heavily
    client.post(
        "/api/v1/university/answer",
        json={"question_id": "UNI-RENAL-001", "selected_option": "A", "idempotency_key": f"a-uni-{uuid.uuid4().hex[:8]}"},
        headers={"X-User-Id": learner_a},
    )
    client.post(
        "/api/v1/plab/evaluate",
        json={"question_id": "PLAB-CARD-0001", "selected_option": "A", "idempotency_key": f"a-plab-{uuid.uuid4().hex[:8]}"},
        headers={"X-User-Id": learner_a},
    )

    # Learner B progress must be pristine and contain ZERO Learner A activity
    prog_b = client.get("/api/v1/learner/progress", headers={"X-User-Id": learner_b}).json()
    assert prog_b["learner_id"] == learner_b
    assert prog_b["university"]["attempted"] == 0
    assert prog_b["plab"]["total_attempts"] == 0
    assert prog_b["anatomy"]["total_sessions"] == 0
    assert prog_b["summary"]["total_questions_attempted"] == 0


# ============================================================================
# NEGATIVE INTEGRATION TESTS
# ============================================================================

def test_negative_missing_learner_identity_fails_closed(client: TestClient):
    """Endpoints requiring identity fail closed when header is missing."""
    res_plab = client.post("/api/v1/plab/evaluate", json={"question_id": "PLAB-CARD-0001", "selected_option": "A", "idempotency_key": "k1"})
    assert res_plab.status_code in {401, 422}

    res_prog = client.get("/api/v1/learner/progress")
    assert res_prog.status_code in {401, 422}

    res_adapt = client.get("/api/v1/adaptive/state")
    assert res_adapt.status_code in {401, 422}



def test_negative_unknown_plab_question_returns_404(client: TestClient):
    """Evaluating unknown PLAB question returns 404."""
    headers = {"X-User-Id": "student_test"}
    payload = {"question_id": "PLAB-NONEXISTENT-9999", "selected_option": "A", "idempotency_key": "key-9999"}
    res = client.post("/api/v1/plab/evaluate", json=payload, headers=headers)
    assert res.status_code == 404


def test_negative_cross_learner_session_access_forbidden(client: TestClient):
    """Learner B cannot access or advance Learner A remediation session."""
    learner_a = f"stu_owner_{uuid.uuid4().hex[:8]}"
    learner_b = f"stu_intruder_{uuid.uuid4().hex[:8]}"

    # Submit distractor as Learner A in University
    attempt_key_a = f"uni-a-{uuid.uuid4().hex[:8]}"
    uni_res = client.post(
        "/api/v1/university/answer",
        json={"question_id": "UNI-RENAL-001", "selected_option": "B", "idempotency_key": attempt_key_a},
        headers={"X-User-Id": learner_a},
    )
    assert uni_res.status_code == 200

    # Start session as Learner A
    start_res = client.post(
        "/api/v1/remediation/start",
        json={
            "question_id": "UNI-RENAL-001",
            "selected_option": "B",
            "topic": "RAAS mechanisms",
            "attempt_id": attempt_key_a,
            "idempotency_key": f"start-{uuid.uuid4().hex[:8]}",
        },
        headers={"X-User-Id": learner_a},
    ).json()
    session_id = start_res["session_id"]

    # Learner B tries to view session -> 403 Forbidden
    intrude_res = client.get(f"/api/v1/remediation/session/{session_id}", headers={"X-User-Id": learner_b})
    assert intrude_res.status_code == 403


def test_negative_feature_disabled_anatomy_returns_503(client: TestClient, monkeypatch):
    """When anatomy feature flag is disabled, anatomy endpoints fail closed with 503."""
    monkeypatch.setenv("MEDICALPLAB_ANATOMY_3D_ENABLED", "0")
    res = client.get("/api/v1/anatomy/manifest")
    assert res.status_code == 503

