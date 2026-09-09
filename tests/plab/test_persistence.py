"""Unit tests for SQLitePilotPersistence."""

import tempfile
import unittest
from pathlib import Path

from medicalplab.plab.governance import (
    ReviewRecord,
    ReviewDecision,
    ReviewFinding,
    ReviewStatus,
)
from medicalplab.plab.persistence import SQLitePilotPersistence


class TestSQLitePilotPersistence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_store.db"
        self.store = SQLitePilotPersistence(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_review(self):
        record = ReviewRecord(
            question_id="PLAB-TEST-0001",
            question_version=1,
            question_content_sha256="test-sha",
            review_status=ReviewStatus.APPROVED,
            final_decision=ReviewDecision.APPROVED,
            clinical_correctness=ReviewFinding.PASS,
            sba_unambiguity=ReviewFinding.PASS,
            uk_alignment=ReviewFinding.PASS,
            evidence_adequacy=ReviewFinding.PASS,
            distractor_quality=ReviewFinding.PASS,
            explanation_quality=ReviewFinding.PASS,
            golden_status=True,
        )
        self.store.save_review(record)

        loaded = self.store.load_reviews()
        self.assertIn("PLAB-TEST-0001", loaded)
        r = loaded["PLAB-TEST-0001"]
        self.assertEqual(r.question_id, "PLAB-TEST-0001")
        self.assertEqual(r.review_status, ReviewStatus.APPROVED)
        self.assertTrue(r.golden_status)

    def test_save_and_load_attempt(self):
        attempt = {
            "attempt_id": "ATT-001",
            "user_id": "STU-001",
            "question_id": "PLAB-TEST-0001",
            "question_version": "1.0.0",
            "batch_version": "v1",
            "topic": "Cardiology",
            "selected_option": "A",
            "correct_option": "A",
            "is_correct": True,
            "submitted_at": "2026-09-09T10:00:00Z",
            "response_time_ms": 5000,
            "runtime_mode": "pilot",
            "question_lifecycle_state": "PREVIEW_QA",
            "response": {"correct": True, "selected_answer": "A"},
        }
        self.store.save_attempt(attempt)

        loaded = self.store.load_attempts()
        self.assertTrue(len(loaded) > 0)


if __name__ == "__main__":
    unittest.main()
