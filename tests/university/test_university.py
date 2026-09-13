import copy
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from medicalplab.university.api import router, service
from medicalplab.university.service import BANK, UniversityService, audit_bank


@pytest.fixture
def bank():
    return json.loads(BANK.read_text(encoding="utf-8"))


@pytest.fixture
def uni(tmp_path):
    return UniversityService(db=tmp_path / "uni.sqlite3")


@pytest.fixture
def client(uni):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[service] = lambda: uni
    with TestClient(app) as client:
        yield client


HEADERS = {"X-User-Id": "university-learner-1"}


def submit(client, q="UNI-RENAL-001", option="A", key="attempt-0001", headers=HEADERS):
    return client.post("/api/v1/university/answer", headers=headers,
                       json={"question_id": q, "selected_option": option, "idempotency_key": key})


def test_subjects_and_topic_counts(client):
    assert client.get("/api/v1/university/subjects").json() == {"items": [{"name": "Renal physiology", "count": 6}]}
    topics = client.get("/api/v1/university/topics", params={"subject": "Renal physiology"}).json()["items"]
    assert topics == [{"name": "Glomerular filtration barrier", "count": 3}, {"name": "RAAS mechanisms", "count": 3}]


def test_question_contract_no_answer_leak(client):
    result = client.get("/api/v1/university/question", params={"subject": "Renal physiology", "topic": "RAAS mechanisms"}).json()
    assert result["question"]["id"] == "UNI-RENAL-001"
    assert set(result["question"]) == {"id", "track", "stem", "subject", "topic", "options", "difficulty"}
    assert result["position"] == 1 and result["total"] == 3


@pytest.mark.parametrize("option,correct", [("A", True), ("B", False), ("C", False), ("D", False)])
def test_answer_feedback_and_persistence(client, uni, option, correct):
    result = submit(client, option=option)
    assert result.status_code == 200
    data = result.json()
    assert data["is_correct"] is correct
    assert data["correct_answer"] == "A"
    assert "angiotensinogen" in data["explanation"]
    assert data["source"]["url"].startswith("https://")
    assert data["subject"] == "Renal physiology" and data["next_action"] == "next_question"
    restarted = UniversityService(db=uni.db)
    assert restarted.progress(HEADERS["X-User-Id"])["correct"] == int(correct)


def test_idempotency_and_conflicting_retry(client):
    assert submit(client).status_code == 200
    assert submit(client).status_code == 200
    assert submit(client, option="B").status_code == 409
    assert client.get("/api/v1/university/progress", headers=HEADERS).json()["attempted"] == 1


def test_empty_progress_and_user_isolation(client):
    empty = client.get("/api/v1/university/progress", headers=HEADERS).json()
    assert empty["attempted"] == 0 and empty["accuracy"] is None
    submit(client)
    other = client.get("/api/v1/university/progress", headers={"X-User-Id": "another-learner"}).json()
    assert other["attempted"] == 0


def test_weak_topic_recommendation(client):
    submit(client, option="B")
    submit(client, q="UNI-RENAL-004", option="D", key="attempt-0002")
    progress = client.get("/api/v1/university/progress", headers=HEADERS).json()
    assert progress["attempted"] == 2 and progress["accuracy"] == .5
    assert progress["recommendation"]["topic"] == "RAAS mechanisms"
    assert progress["weak_topics"][0]["mastery"] == "beginner"


@pytest.mark.parametrize("path,params", [
    ("topics", {"subject": "PLAB"}),
    ("question", {"subject": "Renal physiology", "topic": "STEMI"}),
    ("question", {"subject": "invalid", "topic": "RAAS mechanisms"}),
])
def test_invalid_taxonomy(client, path, params):
    assert client.get(f"/api/v1/university/{path}", params=params).status_code == 404


@pytest.mark.parametrize("q,option,status", [("PLAB-001", "A", 404), ("UNI-RENAL-001", "E", 422), ("UNI-RENAL-001", "Z", 422)])
def test_invalid_question_or_answer(client, q, option, status):
    assert submit(client, q=q, option=option).status_code == status
    assert client.get("/api/v1/university/progress", headers=HEADERS).json()["attempted"] == 0


def test_missing_identity(client):
    assert submit(client, headers={}).status_code == 422


def test_end_of_topic_and_wrong_cursor(client):
    params = {"subject": "Renal physiology", "topic": "RAAS mechanisms", "after": "UNI-RENAL-003"}
    assert client.get("/api/v1/university/question", params=params).json() == {"question": None, "next_action": "review_topic"}
    params["after"] = "UNI-RENAL-004"
    assert client.get("/api/v1/university/question", params=params).status_code == 422


@pytest.mark.parametrize("field,value", [
    ("stem", ""), ("explanation", ""), ("subject", ""), ("topic", ""),
    ("options", {}), ("options", {"A": "same", "B": "same"}),
    ("correct_answer", "Z"), ("difficulty", "expert"), ("track", "plab"),
    ("content_kind", "CLINICAL_DECISION_CONTENT"), ("evidence", {}), ("stem", "broken \ufffd"),
])
def test_malformed_content_excluded(bank, tmp_path, field, value):
    bank[0][field] = value
    path = tmp_path / "bank.json"
    path.write_text(json.dumps(bank), encoding="utf-8")
    s = UniversityService(path, tmp_path / "uni.sqlite3")
    assert "UNI-RENAL-001" not in s.questions
    assert s.audit[0]["status"] == "QUARANTINED"


@pytest.mark.parametrize("status", ["QUARANTINED", "REVIEW_REQUIRED"])
def test_nonservable_status(bank, tmp_path, status):
    for q in bank:
        q["status"] = status
    path = tmp_path / "bank.json"
    path.write_text(json.dumps(bank), encoding="utf-8")
    s = UniversityService(path, tmp_path / "uni.sqlite3")
    assert not s.questions and s.subjects() == []
    with pytest.raises(ValueError):
        s.answer("user", bank[0]["id"], "A", "attempt-001")


def test_duplicate_groups_excluded(bank):
    duplicate = copy.deepcopy(bank[0])
    assert all(a["status"] == "QUARANTINED" for a in audit_bank([bank[0], duplicate]))
    duplicate["id"] = "UNI-OTHER"
    assert all(a["status"] == "QUARANTINED" for a in audit_bank([bank[0], duplicate]))


def test_source_integrity(bank):
    assert all(a["status"] == "VERIFIED_EDUCATIONAL" for a in audit_bank(bank))
    for q in bank:
        source = q["evidence"]
        path = BANK.parents[1] / "processed/renal_v1" / f"{source['document_id']}.chunks.json"
        chunks = json.loads(path.read_text(encoding="utf-8"))["chunks"]
        assert source["excerpt"] in next(c["text"] for c in chunks if c["chunk_id"] == source["chunk_id"])


def test_storage_failure_is_professional(client, uni, tmp_path):
    uni.db = tmp_path  # A directory cannot be opened as SQLite storage.
    assert submit(client).status_code == 503


def test_empty_and_missing_bank(tmp_path):
    path = tmp_path / "bank.json"
    path.write_text("[]")
    assert UniversityService(path).subjects() == []
    with pytest.raises(ValueError, match="content is unavailable"):
        UniversityService(tmp_path / "missing.json")


def test_plab_separation_and_no_state_mutation(client, uni):
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1] / "plab"))
    from test_pilot_acceptance import service as plab_service
    from medicalplab.plab.pilot import PLABProductError

    raw_batch = json.loads((BANK.parents[1] / "questions/cardiorespiratory_batch_1.json").read_text(encoding="utf-8"))
    raw_plab_ids = {q["question_id"] for q in raw_batch["questions"]}
    assert not (raw_plab_ids & set(uni.questions))
    for qid in list(raw_plab_ids)[:5]:
        assert submit(client, q=qid).status_code == 404

    plab = plab_service(approved=True, preview=True)
    before = plab.governance_counts()
    before_progress = plab.progress(HEADERS["X-User-Id"])
    assert not (set(plab.questions) & set(uni.questions))
    for qid in plab.questions:
        assert submit(client, q=qid).status_code == 404
    submit(client)
    assert plab.governance_counts() == before
    assert plab.progress(HEADERS["X-User-Id"]) == before_progress
    for qid in uni.questions:
        with pytest.raises((ValueError, PLABProductError)):
            plab.question_dto(qid)
