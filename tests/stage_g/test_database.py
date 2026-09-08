"""Unit tests for Stage-G database repository layer."""

import unittest

from medicalplab.stage_g.database import DatabaseService
from medicalplab.stage_g.models import (
    AIUsageRecord,
    AuditEvent,
    AuditEventType,
    DocumentRecord,
    DocumentStage,
    InstitutionAnalyticsRecord,
    Membership,
    Organization,
    StudentAnalyticsRecord,
    SubscriptionTier,
    Tenant,
    UserRecord,
    UserRole,
)


class TestStageGDatabase(unittest.TestCase):
    """Test suite for repository abstractions and in-memory storage."""

    def setUp(self):
        self.db = DatabaseService()

    def test_tenant_repository(self):
        """Test tenant CRUD operations."""
        tenant = Tenant(tenant_id="ten_1", name="King's College Hospital")
        self.db.tenants.create(tenant)

        retrieved = self.db.tenants.get("ten_1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "King's College Hospital")

        all_tenants = self.db.tenants.list_all()
        self.assertEqual(len(all_tenants), 1)

    def test_user_repository(self):
        """Test user CRUD and email lookup."""
        user = UserRecord(
            user_id="usr_101",
            tenant_id="ten_1",
            email="resident@nhs.uk",
            name="Dr. Jane",
            role=UserRole.DOCTOR,
            tier=SubscriptionTier.PREMIUM,
        )
        self.db.users.create(user)

        by_id = self.db.users.get("usr_101")
        self.assertEqual(by_id.name, "Dr. Jane")

        by_email = self.db.users.get_by_email("resident@nhs.uk")
        self.assertEqual(by_email.user_id, "usr_101")

        by_tenant = self.db.users.list_by_tenant("ten_1")
        self.assertEqual(len(by_tenant), 1)

        # Update
        updated = UserRecord(
            user_id="usr_101",
            tenant_id="ten_1",
            email="resident@nhs.uk",
            name="Dr. Jane Smith",
            role=UserRole.DOCTOR,
            tier=SubscriptionTier.PREMIUM,
        )
        self.db.users.update(updated)
        self.assertEqual(self.db.users.get("usr_101").name, "Dr. Jane Smith")

        # Delete
        self.db.users.delete("usr_101")
        self.assertIsNone(self.db.users.get("usr_101"))

    def test_organization_and_membership_repository(self):
        """Test organization and membership management."""
        org = Organization(org_id="org_1", tenant_id="ten_1", name="Pediatrics")
        self.db.organizations.create(org)

        retrieved = self.db.organizations.get("org_1")
        self.assertEqual(retrieved.name, "Pediatrics")

        mem = Membership(membership_id="m_1", user_id="usr_101", org_id="org_1", tenant_id="ten_1")
        self.db.organizations.create_membership(mem)

        mems = self.db.organizations.list_memberships_by_org("org_1")
        self.assertEqual(len(mems), 1)
        self.assertEqual(mems[0].user_id, "usr_101")

    def test_document_repository(self):
        """Test document tracking."""
        doc = DocumentRecord(
            doc_id="doc_1",
            tenant_id="ten_1",
            owner_id="usr_101",
            title="BNF 85 Guidelines",
            stage=DocumentStage.UPLOAD,
            version=1,
            file_path="/files/bnf.pdf",
            file_size_bytes=4096,
        )
        self.db.documents.create(doc)

        retrieved = self.db.documents.get("doc_1")
        self.assertEqual(retrieved.stage, DocumentStage.UPLOAD)

        docs = self.db.documents.list_by_tenant("ten_1")
        self.assertEqual(len(docs), 1)

        # Update stage
        updated = DocumentRecord(
            doc_id="doc_1",
            tenant_id="ten_1",
            owner_id="usr_101",
            title="BNF 85 Guidelines",
            stage=DocumentStage.AVAILABLE,
            version=2,
            file_path="/files/bnf.pdf",
            file_size_bytes=4096,
        )
        self.db.documents.update(updated)
        self.assertEqual(self.db.documents.get("doc_1").stage, DocumentStage.AVAILABLE)

    def test_attempts_and_analytics_repository(self):
        """Test student attempt storage and analytics persistence."""
        attempt = {
            "attempt_id": "att_1",
            "student_id": "usr_stu_1",
            "tenant_id": "ten_1",
            "topic": "Cardiology",
            "is_correct": True,
            "time_spent_seconds": 45.0,
        }
        self.db.attempts.record(attempt)

        attempts = self.db.attempts.list_by_student("usr_stu_1")
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["topic"], "Cardiology")

        # Student analytics
        s_rec = StudentAnalyticsRecord(
            student_id="usr_stu_1",
            tenant_id="ten_1",
            total_attempts=1,
            overall_accuracy=1.0,
            mastery_level="BEGINNER",
            weak_topics=(),
            improvement_rate=0.0,
            updated_at=1700000000.0,
        )
        self.db.analytics.save_student_analytics(s_rec)
        saved = self.db.analytics.get_student_analytics("usr_stu_1")
        self.assertEqual(saved.overall_accuracy, 1.0)

        # Institution analytics
        i_rec = InstitutionAnalyticsRecord(
            tenant_id="ten_1",
            cohort_id="cohort_2026",
            total_students=10,
            active_students_7d=8,
            cohort_accuracy=0.78,
            difficult_topics=("Pharmacology",),
            total_ai_requests=120,
            updated_at=1700000000.0,
        )
        self.db.analytics.save_institution_analytics(i_rec)
        saved_inst = self.db.analytics.get_institution_analytics("ten_1", "cohort_2026")
        self.assertEqual(saved_inst.total_students, 10)

    def test_usage_and_audit_repository(self):
        """Test AI usage tracking and compliance audit event storage."""
        usage = AIUsageRecord(
            record_id="use_1",
            tenant_id="ten_1",
            user_id="usr_1",
            request_type="assessment",
            stage_used="stage_f",
            model_name="qwen-2.5-7b-instruct",
            input_tokens=100,
            output_tokens=200,
            estimated_cost=0.0003,
            latency_ms=80.0,
            success=True,
            timestamp=1700000000.0,
        )
        self.db.usage.record(usage)
        user_usages = self.db.usage.list_by_user("usr_1")
        self.assertEqual(len(user_usages), 1)

        event = AuditEvent(
            event_id="aud_1",
            tenant_id="ten_1",
            actor_id="usr_1",
            event_type=AuditEventType.LOGIN,
            action="User logged in",
            timestamp=1700000000.0,
        )
        self.db.audit.record(event)
        events = self.db.audit.list_by_tenant("ten_1")
        self.assertEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main()
