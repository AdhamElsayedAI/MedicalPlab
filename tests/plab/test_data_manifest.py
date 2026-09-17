"""Unit tests for Data Integrity Manifest Verification."""

import shutil
import tempfile
import unittest
from pathlib import Path

from medicalplab.plab.data_manifest import (
    ACTIVE_STARTUP_SAFE_CHUNK_COUNT,
    ACTIVE_STARTUP_SAFE_DOCUMENT_COUNT,
    ACTIVE_STARTUP_SAFE_DOCUMENT_IDS,
    EXPECTED_CHUNK_COUNT,
    EXPECTED_DOCUMENT_COUNT,
    HISTORICAL_FULL_CHUNK_COUNT,
    HISTORICAL_FULL_DOCUMENT_COUNT,
    REFERENCE_ONLY_DOCUMENT_IDS,
    verify_production_data_manifest,
)

try:
    from .fixture_helper import build_test_data_root
except ImportError:
    from fixture_helper import build_test_data_root


class TestDataManifest(unittest.TestCase):
    def test_verify_production_data_manifest(self):
        # 1. Authoritative active runtime constants regression assertions
        self.assertEqual(EXPECTED_DOCUMENT_COUNT, 12)
        self.assertEqual(EXPECTED_CHUNK_COUNT, 734)
        self.assertEqual(ACTIVE_STARTUP_SAFE_DOCUMENT_COUNT, 12)
        self.assertEqual(ACTIVE_STARTUP_SAFE_CHUNK_COUNT, 734)
        self.assertEqual(HISTORICAL_FULL_DOCUMENT_COUNT, 13)
        self.assertEqual(HISTORICAL_FULL_CHUNK_COUNT, 817)
        self.assertIn("DOC-WHO-CARD-0001", REFERENCE_ONLY_DOCUMENT_IDS)
        self.assertNotIn("DOC-WHO-CARD-0001", ACTIVE_STARTUP_SAFE_DOCUMENT_IDS)
        self.assertEqual(len(ACTIVE_STARTUP_SAFE_DOCUMENT_IDS), 12)

        # 2. Behavior A: Valid reproducible test fixture satisfies runtime manifest
        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture_root = build_test_data_root(tmp_dir)
            report_valid = verify_production_data_manifest(fixture_root)
            self.assertTrue(report_valid.is_valid)
            self.assertEqual(len(report_valid.blockers), 0)
            self.assertEqual(report_valid.document_count, 12)
            self.assertEqual(report_valid.chunk_count, 734)
            self.assertEqual(report_valid.question_count, 36)
            self.assertEqual(report_valid.batch_version, "cardiorespiratory_batch_1_source_audit_v2")
            self.assertEqual(report_valid.snapshot_id, "medicalplab-cardiorespiratory-corpus-v1")

        # 3. Behavior B: Missing or unavailable data root
        report_unavail = verify_production_data_manifest(Path(tempfile.gettempdir()) / "non_existent_plab_dir_12345")
        self.assertFalse(report_unavail.is_valid)
        self.assertIn("DATA_ROOT_UNAVAILABLE", report_unavail.blockers)

        with tempfile.TemporaryDirectory() as empty_dir:
            report_empty = verify_production_data_manifest(empty_dir)
            self.assertFalse(report_empty.is_valid)
            self.assertIn("CORPUS_SNAPSHOT_MISSING", report_empty.blockers)

        # 4. Behavior B2: Metadata present but chunks missing (simulated clean checkout)
        with tempfile.TemporaryDirectory() as checkout_dir:
            c_path = Path(checkout_dir)
            meta_dst = c_path / "metadata"
            meta_dst.mkdir(parents=True)
            repo_root = Path(__file__).resolve().parents[2]
            shutil.copy2(repo_root / "Data" / "metadata" / "corpus_cardiorespiratory_snapshot_v1.json", meta_dst)
            q_dst = c_path / "questions" / "versions"
            q_dst.mkdir(parents=True)
            shutil.copy2(repo_root / "Data" / "questions" / "versions" / "cardiorespiratory_batch_1_source_audit_v2.json", q_dst)
            shutil.copy2(repo_root / "Data" / "questions" / "cardiorespiratory_batch_1_review_queue.json", c_path / "questions")

            report_clean = verify_production_data_manifest(checkout_dir)
            self.assertFalse(report_clean.is_valid)
            self.assertEqual(report_clean.document_count, 12)
            self.assertEqual(report_clean.chunk_count, 0)
            # Must explicitly report missing active CC BY 4.0 chunk files
            self.assertIn("CHUNK_FILE_MISSING: DOC-PMC-CARD-0002", report_clean.blockers)
            self.assertIn("CHUNK_FILE_MISSING: DOC-PMC-CARD-0014", report_clean.blockers)
            # Must expect 734 chunks (NOT 817)
            self.assertIn("CHUNK_COUNT_MISMATCH: expected 734, got 0", report_clean.blockers)
            # WHO must NOT appear in missing list or active blockers
            self.assertFalse(any("DOC-WHO-CARD-0001" in b for b in report_clean.blockers))
            self.assertFalse(any("817" in b for b in report_clean.blockers))


if __name__ == "__main__":
    unittest.main()
