"""Synthetic lifecycle tests: storage failures must never appear successful."""
import sqlite3

import pytest

from medicalplab.plab.freeze import create_golden_dataset_freeze, write_freeze
from medicalplab.plab.governance import REVIEW_DIMENSIONS, ReviewDecision, ReviewFinding, create_revision
from medicalplab.plab.persistence import SQLitePilotPersistence
from medicalplab.plab.pilot import PLABProductError
from test_pilot_acceptance import service


def test_revision_and_review_survive_new_storage_instance(tmp_path):
    configured = service(approved=True)
    configured.persistence = SQLitePilotPersistence(tmp_path / "pilot.db")
    qid = "PLAB-TEST-0001"
    result = configured.revise_question(qid, {"stem": "An updated vignette with sufficient detail for this synthetic test."}, "Clarify", "editor")
    reloaded = SQLitePilotPersistence(tmp_path / "pilot.db")
    reviews = reloaded.load_reviews()
    revisions, questions = reloaded.load_revisions()
    assert reviews[qid].question_version == result["question_version"] == 2
    assert not reviews[qid].golden_status
    assert questions[qid]["stem"] == configured.questions[qid]["stem"]
    assert len(revisions[qid]) == 1


def test_revision_failure_rolls_back_content_and_review(tmp_path, monkeypatch):
    configured = service(approved=True)
    store = SQLitePilotPersistence(tmp_path / "pilot.db")
    configured.persistence = store
    qid = "PLAB-TEST-0001"
    original = dict(configured.questions[qid])
    record = configured.reviews[qid]
    store.save_review(record)

    def fail(*args, **kwargs):
        raise sqlite3.OperationalError("synthetic disk failure")

    monkeypatch.setattr(store, "save_review", fail)
    with pytest.raises(PLABProductError, match="not saved"):
        configured.revise_question(qid, {"stem": "Revised synthetic clinical vignette for a transaction test."}, "Clarify", "editor")
    assert configured.questions[qid] == original
    assert configured.reviews[qid] == record
    assert store.load_revisions() == ({}, {})
    assert store.load_reviews()[qid] == record


def test_restart_preserves_idempotency_and_progress(tmp_path):
    configured = service(approved=True)
    configured.persistence = SQLitePilotPersistence(tmp_path / "pilot.db")
    args = dict(user_id="student", question_id="PLAB-TEST-0001", selected_option="A", idempotency_key="retry-123")
    first = configured.evaluate(**args)
    before = configured.progress("student")
    restarted = service(approved=True)
    restarted.persistence = SQLitePilotPersistence(tmp_path / "pilot.db")
    restarted.attempts = restarted.persistence.load_attempts()
    assert restarted.evaluate(**args) == first
    assert restarted.progress("student") == before
    assert len(restarted.persistence.load_attempts()) == 1
    with pytest.raises(PLABProductError, match="reused"):
        restarted.evaluate(**dict(args, selected_option="B"))


def test_approval_never_publishes_golden(tmp_path):
    configured = service()
    configured.persistence = SQLitePilotPersistence(tmp_path / "pilot.db")
    qid = "PLAB-TEST-0001"
    configured.start_review(qid, "synthetic-reviewer")
    result = configured.submit_review(qid, "synthetic-reviewer", ReviewDecision.APPROVED,
        {key: ReviewFinding.PASS for key in REVIEW_DIMENSIONS}, "synthetic test", None)
    assert result["review_status"] == "approved"
    assert not result["golden_status"]
    assert not configured.persistence.load_reviews()[qid].golden_status


def test_freeze_is_detached_and_existing_file_cannot_be_replaced(tmp_path):
    configured = service(approved=True)
    frozen = create_golden_dataset_freeze(configured, "test-commit")
    original_choice = frozen.golden_questions[0]["choices"][0]["text"]
    configured.questions["PLAB-TEST-0001"]["choices"][0]["text"] = "changed"
    assert frozen.golden_questions[0]["choices"][0]["text"] == original_choice
    path = tmp_path / "freeze.json"
    write_freeze(frozen, path)
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_freeze(frozen, path)
    assert path.read_bytes() == before
    assert frozen.source_batch_id == "test-batch-v1"


def test_quote_from_different_citation_cannot_authorize_golden():
    configured = service(approved=True)
    qid = "PLAB-TEST-0001"
    configured.questions[qid]["citations"].append({"ref": "DOC:B2", "document_id": "DOC", "quote": "direct evidence"})
    configured.chunk_index["DOC:B2"] = {"document_id": "DOC", "text": "unrelated passage"}
    assert "citation_unresolved" in configured._promotion(qid).error_codes


def test_source_repair_blocks_even_forged_approved_review():
    configured = service(approved=True)
    configured.questions["PLAB-TEST-0001"]["evidence_verification_status"] = "NEEDS_SOURCE_REPAIR"
    assert not configured.is_golden("PLAB-TEST-0001")


def test_failed_attempt_save_is_not_cached_as_success(tmp_path, monkeypatch):
    configured = service(approved=True)
    configured.persistence = SQLitePilotPersistence(tmp_path / "pilot.db")
    def fail(*args, **kwargs):
        raise sqlite3.OperationalError("synthetic disk full")
    monkeypatch.setattr(configured.persistence, "save_attempt", fail)
    with pytest.raises(PLABProductError, match="not saved"):
        configured.evaluate("student", "PLAB-TEST-0001", "A", "retry-key")
    assert not configured.attempts


def test_revision_id_cannot_overwrite_existing_history(tmp_path):
    configured = service(approved=True)
    q = configured.questions["PLAB-TEST-0001"]
    revised = {**q, "stem": q["stem"] + " More detail."}
    revision = create_revision(q, revised, 1, "Clarify", "editor")
    store = SQLitePilotPersistence(tmp_path / "pilot.db")
    store.save_revision(revision, revised)
    with pytest.raises(sqlite3.IntegrityError):
        store.save_revision(revision, {**revised, "stem": "attempted overwrite"})
    assert store.load_revisions()[1][q["question_id"]] == revised


def test_real_checkpoint_restart_preserves_preview_attempt(tmp_path):
    from medicalplab.plab.pilot import PLABPilotService
    try:
        from .fixture_helper import build_test_data_root
    except ImportError:
        from fixture_helper import build_test_data_root

    data_root = build_test_data_root(tmp_path / "data_root")
    path = tmp_path / "pilot.db"
    first = PLABPilotService.load_default(preview_qa=True, persistence_path=path, data_root=data_root)
    qid = next(iter(first.questions))
    response = first.evaluate("synthetic-student", qid, "A", "durable-retry")
    progress = first.progress("synthetic-student")
    second = PLABPilotService.load_default(preview_qa=True, persistence_path=path, data_root=data_root)
    assert second.evaluate("synthetic-student", qid, "A", "durable-retry") == response
    assert second.progress("synthetic-student") == progress
    assert second.governance_counts()["golden"] == 0


def test_review_events_preserve_prior_state(tmp_path):
    configured = service()
    path = tmp_path / "pilot.db"
    configured.persistence = SQLitePilotPersistence(path)
    configured.start_review("PLAB-TEST-0001", "synthetic-reviewer")
    configured.submit_review("PLAB-TEST-0001", "synthetic-reviewer", ReviewDecision.REJECT,
        {key: ReviewFinding.FAIL for key in REVIEW_DIMENSIONS}, "synthetic test", None)
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT record_json FROM review_events ORDER BY event_id").fetchall()
    import json
    assert [json.loads(row[0])["review_status"] for row in rows] == ["in_review", "rejected"]


def test_legacy_revision_schema_migration(tmp_path):
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE revisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                content_sha256 TEXT NOT NULL,
                parent_version INTEGER,
                revision_reason TEXT NOT NULL,
                changed_fields_json TEXT NOT NULL,
                reviewer_feedback TEXT,
                editor_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute(
            """
            INSERT INTO revisions (
                question_id, version, content_sha256, parent_version,
                revision_reason, changed_fields_json, reviewer_feedback, editor_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("PLAB-TEST-0001", 1, "hash1", None, "legacy reason", '["stem"]', None, "ed1", "2026-01-01")
        )
    store = SQLitePilotPersistence(db_path)
    revs, questions = store.load_revisions()
    assert "PLAB-TEST-0001" in revs
    assert revs["PLAB-TEST-0001"][0]["version_number"] == 1
    assert revs["PLAB-TEST-0001"][0]["reason"] == "legacy reason"
