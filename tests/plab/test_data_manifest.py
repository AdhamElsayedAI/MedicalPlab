"""Unit tests for Data Integrity Manifest Verification."""

import unittest

from medicalplab.plab.data_manifest import verify_production_data_manifest


class TestDataManifest(unittest.TestCase):
    def test_verify_production_data_manifest(self):
        report = verify_production_data_manifest()
        self.assertTrue(report.is_valid)
        self.assertEqual(len(report.blockers), 0)
        self.assertEqual(report.document_count, 13)
        self.assertEqual(report.chunk_count, 817)
        self.assertEqual(report.question_count, 36)
        self.assertEqual(report.batch_version, "cardiorespiratory_batch_1_source_audit_v2")
        self.assertEqual(report.snapshot_id, "medicalplab-cardiorespiratory-corpus-v1")


if __name__ == "__main__":
    unittest.main()
