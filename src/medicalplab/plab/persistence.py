"""Durable SQLite storage for clinical reviews, revisions, and student attempts."""

from __future__ import annotations

import json
import sqlite3
from contextlib import nullcontext
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from .governance import (
    QuestionRevision,
    ReviewDecision,
    ReviewFinding,
    ReviewRecord,
    ReviewStatus,
)


class SQLitePilotPersistence:
    """Transactional local storage; callers must propagate storage failures."""

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            with conn:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS attempts (
                        attempt_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        question_id TEXT NOT NULL,
                        idempotency_key TEXT NOT NULL,
                        selected_option TEXT NOT NULL,
                        correct_option TEXT NOT NULL,
                        is_correct INTEGER NOT NULL,
                        response_json TEXT NOT NULL,
                        submitted_at TEXT NOT NULL,
                        response_time_ms INTEGER,
                        UNIQUE(user_id, idempotency_key)
                    );

                    CREATE TABLE IF NOT EXISTS reviews (
                        question_id TEXT PRIMARY KEY,
                        question_version INTEGER NOT NULL,
                        question_content_sha256 TEXT NOT NULL,
                        review_status TEXT NOT NULL,
                        clinical_correctness TEXT,
                        sba_unambiguity TEXT,
                        uk_alignment TEXT,
                        evidence_adequacy TEXT,
                        distractor_quality TEXT,
                        explanation_quality TEXT,
                        reviewer_id TEXT,
                        reviewer_name TEXT,
                        review_started_at TEXT,
                        reviewed_at TEXT,
                        review_comments TEXT,
                        revision_notes TEXT,
                        final_decision TEXT,
                        golden_status INTEGER NOT NULL DEFAULT 0
                    );

                    CREATE TABLE IF NOT EXISTS revisions (
                        revision_id TEXT PRIMARY KEY,
                        question_id TEXT NOT NULL,
                        version_number INTEGER NOT NULL,
                        changes_json TEXT NOT NULL,
                        revised_payload_json TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        editor_id TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS review_events (
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        question_id TEXT NOT NULL,
                        record_json TEXT NOT NULL,
                        recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
                columns = {row[1] for row in conn.execute("PRAGMA table_info(attempts)")}
                if "attempt_json" not in columns:
                    conn.execute("ALTER TABLE attempts ADD COLUMN attempt_json TEXT")

                rev_columns = {row[1] for row in conn.execute("PRAGMA table_info(revisions)")}
                if rev_columns and ("version_number" not in rev_columns or "revision_id" not in rev_columns):
                    conn.execute("ALTER TABLE revisions RENAME TO _revisions_old")
                    conn.execute(
                        """
                        CREATE TABLE revisions (
                            revision_id TEXT PRIMARY KEY,
                            question_id TEXT NOT NULL,
                            version_number INTEGER NOT NULL,
                            changes_json TEXT NOT NULL,
                            revised_payload_json TEXT NOT NULL,
                            reason TEXT NOT NULL,
                            editor_id TEXT NOT NULL,
                            created_at TEXT NOT NULL
                        );
                        """
                    )
                    has_revised_questions = bool(
                        conn.execute(
                            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='revised_questions'"
                        ).fetchone()
                    )
                    for row in conn.execute("SELECT * FROM _revisions_old").fetchall():
                        row_dict = dict(row)
                        qid = row_dict["question_id"]
                        v = row_dict.get("version_number", row_dict.get("version", 1))
                        rev_id = row_dict.get("revision_id") or f"{qid}:{v}"
                        changes = row_dict.get("changes_json") or row_dict.get("changed_fields_json", "[]")
                        reason = row_dict.get("reason") or row_dict.get("revision_reason", "")
                        editor = row_dict.get("editor_id", "")
                        created = row_dict.get("created_at", "")
                        payload = row_dict.get("revised_payload_json")
                        if not payload and has_revised_questions:
                            p_row = conn.execute(
                                "SELECT question_json FROM revised_questions WHERE question_id = ?",
                                (qid,),
                            ).fetchone()
                            if p_row:
                                payload = p_row[0]
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO revisions (
                                revision_id, question_id, version_number, changes_json,
                                revised_payload_json, reason, editor_id, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                rev_id,
                                qid,
                                v,
                                changes,
                                payload or "{}",
                                reason,
                                editor,
                                created,
                            ),
                        )
                    conn.execute("DROP TABLE _revisions_old")
        finally:
            conn.close()

    def save_attempt(self, attempt: Mapping[str, Any]) -> None:
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO attempts (
                        attempt_id, user_id, question_id, idempotency_key,
                        selected_option, correct_option, is_correct,
                        response_json, submitted_at, response_time_ms, attempt_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(attempt["attempt_id"]),
                        str(attempt["user_id"]),
                        str(attempt["question_id"]),
                        str(attempt.get("idempotency_key", attempt["attempt_id"])),
                        str(attempt["selected_option"]),
                        str(attempt["correct_option"]),
                        int(attempt["is_correct"]),
                        json.dumps(attempt.get("response", {}), ensure_ascii=False),
                        str(attempt.get("submitted_at", "")),
                        attempt.get("response_time_ms"),
                        json.dumps(dict(attempt), ensure_ascii=False),
                    ),
                )
        finally:
            conn.close()

    def load_attempts(self) -> dict[tuple[str, str], dict[str, Any]]:
        conn = self._connect()
        try:
            cur = conn.execute("SELECT * FROM attempts ORDER BY submitted_at, rowid")
            rows = cur.fetchall()
            result = {}
            for row in rows:
                key = (row["user_id"], row["idempotency_key"])
                resp = json.loads(row["response_json"]) if row["response_json"] else {}
                result[key] = {
                    **(json.loads(row["attempt_json"]) if row["attempt_json"] else {}),
                    "attempt_id": row["attempt_id"],
                    "user_id": row["user_id"],
                    "question_id": row["question_id"],
                    "idempotency_key": row["idempotency_key"],
                    "selected_option": row["selected_option"],
                    "correct_option": row["correct_option"],
                    "is_correct": bool(row["is_correct"]),
                    "submitted_at": row["submitted_at"],
                    "response_time_ms": row["response_time_ms"],
                    "response": resp,
                }
                # Older records did not persist the complete attempt envelope.
                result[key].setdefault("topic", resp.get("topic", "UNKNOWN_LEGACY_TOPIC"))
                result[key].setdefault("question_version", resp.get("question_version"))
            return result
        finally:
            conn.close()

    def save_review(self, review: ReviewRecord, *, _connection: sqlite3.Connection | None = None) -> None:
        conn = _connection or self._connect()
        try:
            with (conn if _connection is None else nullcontext()):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO reviews (
                        question_id, question_version, question_content_sha256,
                        review_status, clinical_correctness, sba_unambiguity,
                        uk_alignment, evidence_adequacy, distractor_quality,
                        explanation_quality, reviewer_id, reviewer_name,
                        review_started_at, reviewed_at, review_comments,
                        revision_notes, final_decision, golden_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        review.question_id,
                        review.question_version,
                        review.question_content_sha256,
                        review.review_status.value,
                        review.clinical_correctness.value if review.clinical_correctness else None,
                        review.sba_unambiguity.value if review.sba_unambiguity else None,
                        review.uk_alignment.value if review.uk_alignment else None,
                        review.evidence_adequacy.value if review.evidence_adequacy else None,
                        review.distractor_quality.value if review.distractor_quality else None,
                        review.explanation_quality.value if review.explanation_quality else None,
                        review.reviewer_id,
                        review.reviewer_name,
                        review.review_started_at,
                        review.reviewed_at,
                        review.review_comments,
                        review.revision_notes,
                        review.final_decision.value if review.final_decision else None,
                        int(review.golden_status),
                    ),
                )
                conn.execute(
                    "INSERT INTO review_events (question_id, record_json) VALUES (?, ?)",
                    (review.question_id, json.dumps(asdict(review), ensure_ascii=False)),
                )
        finally:
            if _connection is None:
                conn.close()

    def load_reviews(self) -> dict[str, ReviewRecord]:
        conn = self._connect()
        try:
            cur = conn.execute("SELECT * FROM reviews")
            rows = cur.fetchall()
            reviews = {}
            for row in rows:
                qid = row["question_id"]
                reviews[qid] = ReviewRecord(
                    question_id=qid,
                    question_version=row["question_version"],
                    question_content_sha256=row["question_content_sha256"],
                    review_status=ReviewStatus(row["review_status"]),
                    clinical_correctness=ReviewFinding(row["clinical_correctness"]) if row["clinical_correctness"] else None,
                    sba_unambiguity=ReviewFinding(row["sba_unambiguity"]) if row["sba_unambiguity"] else None,
                    uk_alignment=ReviewFinding(row["uk_alignment"]) if row["uk_alignment"] else None,
                    evidence_adequacy=ReviewFinding(row["evidence_adequacy"]) if row["evidence_adequacy"] else None,
                    distractor_quality=ReviewFinding(row["distractor_quality"]) if row["distractor_quality"] else None,
                    explanation_quality=ReviewFinding(row["explanation_quality"]) if row["explanation_quality"] else None,
                    reviewer_id=row["reviewer_id"],
                    reviewer_name=row["reviewer_name"],
                    review_started_at=row["review_started_at"],
                    reviewed_at=row["reviewed_at"],
                    review_comments=row["review_comments"],
                    revision_notes=row["revision_notes"],
                    final_decision=ReviewDecision(row["final_decision"]) if row["final_decision"] else None,
                    golden_status=bool(row["golden_status"]),
                )
            return reviews
        finally:
            conn.close()

    def save_revision(self, revision: QuestionRevision, revised_payload: Mapping[str, Any], *, _connection: sqlite3.Connection | None = None) -> None:
        conn = _connection or self._connect()
        try:
            with (conn if _connection is None else nullcontext()):
                conn.execute(
                    """
                    INSERT INTO revisions (
                        revision_id, question_id, version_number, changes_json,
                        revised_payload_json, reason, editor_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"{revision.question_id}:{revision.version}",
                        revision.question_id,
                        revision.version,
                        json.dumps(list(revision.changed_fields), ensure_ascii=False),
                        json.dumps(dict(revised_payload), ensure_ascii=False),
                        revision.revision_reason,
                        revision.editor_id,
                        revision.created_at,
                    ),
                )
        finally:
            if _connection is None:
                conn.close()

    def save_revision_and_review(self, revision: QuestionRevision, payload: Mapping[str, Any], review: ReviewRecord) -> None:
        """Commit edited content and invalidation of old approval together."""
        conn = self._connect()
        try:
            with conn:
                self.save_revision(revision, payload, _connection=conn)
                self.save_review(review, _connection=conn)
        finally:
            conn.close()

    def load_revisions(self) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
        conn = self._connect()
        try:
            cur = conn.execute("SELECT * FROM revisions ORDER BY version_number ASC")
            rows = cur.fetchall()
            revisions: dict[str, list[dict[str, Any]]] = {}
            revised_questions: dict[str, dict[str, Any]] = {}
            for row in rows:
                qid = row["question_id"]
                if qid not in revisions:
                    revisions[qid] = []
                revisions[qid].append({
                    "revision_id": row["revision_id"],
                    "question_id": qid,
                    "version_number": row["version_number"],
                    "changes": json.loads(row["changes_json"]),
                    "reason": row["reason"],
                    "editor_id": row["editor_id"],
                    "created_at": row["created_at"],
                })
                revised_questions[qid] = json.loads(row["revised_payload_json"])
            return revisions, revised_questions
        finally:
            conn.close()
