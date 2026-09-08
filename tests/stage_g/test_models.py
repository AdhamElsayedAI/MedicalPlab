"""Unit tests for Stage-G data models and validation constraints."""

from dataclasses import FrozenInstanceError
import unittest

from medicalplab.stage_b.models import ContractError
from medicalplab.stage_g.models import (
    AIUsageRecord,
    APIRequest,
    APIResponse,
    AppConfig,
    AuditEvent,
    AuditEventType,
    DocumentRecord,
    DocumentStage,
    Environment,
    InstitutionAnalyticsRecord,
    Membership,
    Organization,
    StudentAnalyticsRecord,
    SubscriptionPlan,
    SubscriptionTier,
    Tenant,
    UserRecord,
    UserRole,
)


class TestStageGModels(unittest.TestCase):
    """Test suite for Stage-G frozen dataclasses and enums."""

    def test_enums(self):
        """Verify all enum members and values."""
        self.assertEqual(UserRole.STUDENT.value, "STUDENT")
        self.assertEqual(UserRole.DOCTOR.value, "DOCTOR")
        self.assertEqual(UserRole.INSTITUTION_ADMIN.value, "INSTITUTION_ADMIN")

        self.assertEqual(SubscriptionTier.FREE.value, "FREE")
        self.assertEqual(SubscriptionTier.PREMIUM.value, "PREMIUM")
        self.assertEqual(SubscriptionTier.INSTITUTION.value, "INSTITUTION")

        self.assertEqual(DocumentStage.UPLOAD.value, "UPLOAD")
        self.assertEqual(DocumentStage.VALIDATION.value, "VALIDATION")
        self.assertEqual(DocumentStage.EXTRACTION.value, "EXTRACTION")
        self.assertEqual(DocumentStage.CLEANING.value, "CLEANING")
        self.assertEqual(DocumentStage.INDEXING.value, "INDEXING")
        self.assertEqual(DocumentStage.AVAILABLE.value, "AVAILABLE")
        self.assertEqual(DocumentStage.FAILED.value, "FAILED")

        self.assertEqual(AuditEventType.LOGIN.value, "LOGIN")
        self.assertEqual(AuditEventType.AI_REQUEST.value, "AI_REQUEST")

    def test_immutability(self):
        """Verify models are frozen and reject direct attribute mutation."""
        tenant = Tenant(tenant_id="ten_1", name="Hospital A")
        with self.assertRaises(FrozenInstanceError):
            tenant.name = "Hospital B"  # type: ignore

        user = UserRecord(
            user_id="usr_1",
            tenant_id="ten_1",
            email="dr@plab.org",
            name="Dr. Smith",
            role=UserRole.DOCTOR,
            tier=SubscriptionTier.PREMIUM,
        )
        with self.assertRaises(FrozenInstanceError):
            user.role = UserRole.INSTITUTION_ADMIN  # type: ignore

    def test_tenant_validation(self):
        """Verify Tenant constraints."""
        t = Tenant(tenant_id="t_1", name="Oxford Trust", is_active=True)
        self.assertEqual(t.tenant_id, "t_1")
        self.assertEqual(t.name, "Oxford Trust")

        with self.assertRaises(ContractError):
            Tenant(tenant_id="", name="Oxford Trust")
        with self.assertRaises(ContractError):
            Tenant(tenant_id="t_1", name="")
        with self.assertRaises(ContractError):
            Tenant(tenant_id="t_1", name="Oxford", is_active="true")  # type: ignore

    def test_organization_and_membership_validation(self):
        """Verify Organization and Membership constraints."""
        org = Organization(org_id="org_1", tenant_id="t_1", name="Cardiology Dept")
        self.assertEqual(org.org_id, "org_1")

        with self.assertRaises(ContractError):
            Organization(org_id="", tenant_id="t_1", name="Dept")

        mem = Membership(membership_id="m_1", user_id="u_1", org_id="org_1", tenant_id="t_1")
        self.assertEqual(mem.role, "MEMBER")

        with self.assertRaises(ContractError):
            Membership(membership_id="m_1", user_id="", org_id="org_1", tenant_id="t_1")

    def test_user_record_validation(self):
        """Verify UserRecord validation logic."""
        user = UserRecord(
            user_id="u_1",
            tenant_id="t_1",
            email="student@plab.uk",
            name="Alice",
            role=UserRole.STUDENT,
            tier=SubscriptionTier.FREE,
        )
        self.assertTrue(user.is_active)

        with self.assertRaises(ContractError):
            UserRecord(
                user_id="u_1",
                tenant_id="t_1",
                email="not-an-email",
                name="Alice",
                role=UserRole.STUDENT,
                tier=SubscriptionTier.FREE,
            )
        with self.assertRaises(ContractError):
            UserRecord(
                user_id="u_1",
                tenant_id="t_1",
                email="alice@plab.uk",
                name="Alice",
                role="STUDENT",  # type: ignore
                tier=SubscriptionTier.FREE,
            )

    def test_subscription_plan_validation(self):
        """Verify SubscriptionPlan limits."""
        plan = SubscriptionPlan(
            plan_id="p_1",
            tier=SubscriptionTier.PREMIUM,
            name="Pro Tier",
            max_daily_requests=500,
            monthly_price_usd=29.99,
        )
        self.assertEqual(plan.max_daily_requests, 500)

        with self.assertRaises(ContractError):
            SubscriptionPlan(
                plan_id="p_1",
                tier=SubscriptionTier.PREMIUM,
                name="Pro Tier",
                max_daily_requests=-1,
                monthly_price_usd=29.99,
            )
        with self.assertRaises(ContractError):
            SubscriptionPlan(
                plan_id="p_1",
                tier=SubscriptionTier.PREMIUM,
                name="Pro Tier",
                max_daily_requests=10,
                monthly_price_usd=-5.0,
            )

    def test_document_record_validation(self):
        """Verify DocumentRecord lifecycle fields."""
        doc = DocumentRecord(
            doc_id="d_1",
            tenant_id="t_1",
            owner_id="u_1",
            title="NICE Cardiology Guidelines",
            stage=DocumentStage.UPLOAD,
            version=1,
            file_path="/data/cardio.pdf",
            file_size_bytes=2048,
        )
        self.assertEqual(doc.stage, DocumentStage.UPLOAD)

        with self.assertRaises(ContractError):
            DocumentRecord(
                doc_id="d_1",
                tenant_id="t_1",
                owner_id="u_1",
                title="Title",
                stage="UPLOAD",  # type: ignore
                version=1,
                file_path="/data/a.pdf",
                file_size_bytes=10,
            )
        with self.assertRaises(ContractError):
            DocumentRecord(
                doc_id="d_1",
                tenant_id="t_1",
                owner_id="u_1",
                title="Title",
                stage=DocumentStage.UPLOAD,
                version=-1,
                file_path="/data/a.pdf",
                file_size_bytes=10,
            )

    def test_ai_usage_and_audit_validation(self):
        """Verify AIUsageRecord and AuditEvent contracts."""
        usage = AIUsageRecord(
            record_id="rec_1",
            tenant_id="t_1",
            user_id="u_1",
            request_type="teaching",
            stage_used="stage_f",
            model_name="qwen-2.5-7b-instruct",
            input_tokens=150,
            output_tokens=300,
            estimated_cost=0.00045,
            latency_ms=120.5,
            success=True,
            timestamp=1700000000.0,
        )
        self.assertTrue(usage.success)

        with self.assertRaises(ContractError):
            AIUsageRecord(
                record_id="rec_1",
                tenant_id="t_1",
                user_id="u_1",
                request_type="teaching",
                stage_used="stage_f",
                model_name="m",
                input_tokens=-10,
                output_tokens=300,
                estimated_cost=0.01,
                latency_ms=10.0,
                success=True,
                timestamp=1.0,
            )

        event = AuditEvent(
            event_id="ev_1",
            tenant_id="t_1",
            actor_id="u_1",
            event_type=AuditEventType.DOCUMENT_UPLOAD,
            action="Uploaded new file",
            timestamp=1700000000.0,
        )
        self.assertEqual(event.event_type, AuditEventType.DOCUMENT_UPLOAD)

    def test_analytics_and_api_envelopes(self):
        """Verify StudentAnalyticsRecord, InstitutionAnalyticsRecord, APIRequest, APIResponse."""
        s_rec = StudentAnalyticsRecord(
            student_id="u_1",
            tenant_id="t_1",
            total_attempts=50,
            overall_accuracy=0.84,
            mastery_level="ADVANCED",
            weak_topics=("Neurology",),
            improvement_rate=0.05,
            updated_at=1700000000.0,
        )
        self.assertEqual(s_rec.mastery_level, "ADVANCED")

        with self.assertRaises(ContractError):
            StudentAnalyticsRecord(
                student_id="u_1",
                tenant_id="t_1",
                total_attempts=10,
                overall_accuracy=1.5,  # > 1.0
                mastery_level="ADVANCED",
                weak_topics=(),
                improvement_rate=0.0,
                updated_at=1.0,
            )

        req = APIRequest(path="/ai/chat", method="POST", body="hello")
        self.assertEqual(req.method, "POST")

        res = APIResponse(status_code=200, body='{"status": "ok"}')
        self.assertEqual(res.status_code, 200)

        with self.assertRaises(ContractError):
            APIResponse(status_code=999)

        cfg = AppConfig(
            env=Environment.PRODUCTION,
            api_version="v1",
            db_uri="postgresql://user:pass@localhost:5432/medplab",
            rate_limit_per_minute=120,
        )
        self.assertEqual(cfg.env, Environment.PRODUCTION)


if __name__ == "__main__":
    unittest.main()
