"""Unit tests for Stage-G Medical Knowledge Management and document lifecycle."""

import unittest

from medicalplab.stage_b.models import ContractError
from medicalplab.stage_g.audit import AuditService
from medicalplab.stage_g.database import DatabaseService
from medicalplab.stage_g.knowledge_management import MedicalKnowledgeManager
from medicalplab.stage_g.models import DocumentStage


class TestStageGKnowledgeManagement(unittest.TestCase):
    """Test suite for document lifecycle state machine and tenant isolation."""

    def setUp(self):
        self.db = DatabaseService()
        self.audit = AuditService(self.db)
        self.km = MedicalKnowledgeManager(self.db, self.audit)

    def test_document_upload(self):
        """Uploaded document must initialize in UPLOAD stage."""
        doc = self.km.upload_document(
            tenant_id="ten_1",
            owner_id="doc_1",
            title="NICE Stroke Guidelines (NG128)",
            file_path="/storage/nice_ng128.pdf",
            file_size_bytes=524288,
        )

        self.assertEqual(doc.stage, DocumentStage.UPLOAD)
        self.assertEqual(doc.version, 1)

        retrieved = self.km.get_document(doc.doc_id, "ten_1")
        self.assertEqual(retrieved.title, "NICE Stroke Guidelines (NG128)")

    def test_full_lifecycle_progression(self):
        """Progress document through all valid stages to AVAILABLE."""
        doc = self.km.upload_document(
            tenant_id="ten_1",
            owner_id="doc_1",
            title="Oxford Handbook of Clinical Medicine",
            file_path="/storage/oxford.pdf",
            file_size_bytes=1048576,
        )

        # UPLOAD -> VALIDATION
        doc = self.km.advance_stage(doc.doc_id, "ten_1", DocumentStage.VALIDATION)
        self.assertEqual(doc.stage, DocumentStage.VALIDATION)

        # VALIDATION -> EXTRACTION
        doc = self.km.advance_stage(doc.doc_id, "ten_1", DocumentStage.EXTRACTION)
        self.assertEqual(doc.stage, DocumentStage.EXTRACTION)

        # EXTRACTION -> CLEANING
        doc = self.km.advance_stage(doc.doc_id, "ten_1", DocumentStage.CLEANING)
        self.assertEqual(doc.stage, DocumentStage.CLEANING)

        # CLEANING -> INDEXING
        doc = self.km.advance_stage(doc.doc_id, "ten_1", DocumentStage.INDEXING)
        self.assertEqual(doc.stage, DocumentStage.INDEXING)

        # INDEXING -> AVAILABLE
        doc = self.km.advance_stage(doc.doc_id, "ten_1", DocumentStage.AVAILABLE)
        self.assertEqual(doc.stage, DocumentStage.AVAILABLE)
        self.assertEqual(doc.version, 6)

    def test_transition_to_failed(self):
        """Any non-terminal stage can transition to FAILED."""
        doc = self.km.upload_document(
            tenant_id="ten_1",
            owner_id="doc_1",
            title="Corrupted Scan",
            file_path="/storage/corrupted.pdf",
            file_size_bytes=100,
        )

        failed_doc = self.km.advance_stage(doc.doc_id, "ten_1", DocumentStage.FAILED)
        self.assertEqual(failed_doc.stage, DocumentStage.FAILED)

    def test_invalid_lifecycle_transition(self):
        """Skipping intermediate stages must be rejected."""
        doc = self.km.upload_document(
            tenant_id="ten_1",
            owner_id="doc_1",
            title="Manual",
            file_path="/storage/manual.pdf",
            file_size_bytes=100,
        )

        # Cannot jump from UPLOAD directly to AVAILABLE
        with self.assertRaises(ContractError):
            self.km.advance_stage(doc.doc_id, "ten_1", DocumentStage.AVAILABLE)

        # Cannot jump from UPLOAD directly to CLEANING
        with self.assertRaises(ContractError):
            self.km.advance_stage(doc.doc_id, "ten_1", DocumentStage.CLEANING)

    def test_cross_tenant_document_isolation(self):
        """Tenant B must not access or advance Tenant A's documents."""
        doc_a = self.km.upload_document(
            tenant_id="ten_a",
            owner_id="doc_a1",
            title="Hospital A Protocol",
            file_path="/storage/doc_a.pdf",
            file_size_bytes=2048,
        )

        # Read attempt by tenant_b raises ContractError
        with self.assertRaises(ContractError):
            self.km.get_document(doc_a.doc_id, "ten_b")

        # Advancement attempt by tenant_b raises ContractError
        with self.assertRaises(ContractError):
            self.km.advance_stage(doc_a.doc_id, "ten_b", DocumentStage.VALIDATION)

        # Listing by tenant_b returns 0 documents
        docs_b = self.km.list_tenant_documents("ten_b")
        self.assertEqual(len(docs_b), 0)


if __name__ == "__main__":
    unittest.main()
