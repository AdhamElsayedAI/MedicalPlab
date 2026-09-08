"""Unit tests for Stage-G Platform API Router."""

import json
import unittest

from medicalplab.stage_g.analytics import PlatformAnalyticsService
from medicalplab.stage_g.api import PlatformAPIRouter
from medicalplab.stage_g.audit import AuditService
from medicalplab.stage_g.database import DatabaseService
from medicalplab.stage_g.gateway import AIGateway
from medicalplab.stage_g.knowledge_management import MedicalKnowledgeManager
from medicalplab.stage_g.models import (
    APIRequest,
    SubscriptionTier,
    Tenant,
    UserRecord,
    UserRole,
)
from medicalplab.stage_g.multitenancy import MultiTenancyService
from medicalplab.stage_g.security import SecurityService
from medicalplab.stage_g.usage import AIUsageTracker


class TestStageGAPI(unittest.TestCase):
    """Test suite for the REST-style Platform API endpoints."""

    def setUp(self):
        self.db = DatabaseService()
        self.security = SecurityService()
        self.multitenancy = MultiTenancyService(self.db)
        self.audit = AuditService(self.db)
        self.usage = AIUsageTracker(self.db)
        self.knowledge = MedicalKnowledgeManager(self.db, self.audit)
        self.analytics = PlatformAnalyticsService(self.db)
        self.gateway = AIGateway(self.db, self.security, self.usage, self.audit)

        self.router = PlatformAPIRouter(
            db=self.db,
            security=self.security,
            multitenancy=self.multitenancy,
            knowledge=self.knowledge,
            analytics=self.analytics,
            gateway=self.gateway,
            audit=self.audit,
        )

        # Setup initial tenant
        self.tenant = Tenant(tenant_id="ten_api", name="National Health Service")
        self.db.tenants.create(self.tenant)

        # Setup Admin User
        self.admin = UserRecord(
            user_id="adm_1",
            tenant_id="ten_api",
            email="admin@nhs.uk",
            name="Admin Chief",
            role=UserRole.INSTITUTION_ADMIN,
            tier=SubscriptionTier.INSTITUTION,
        )
        self.db.users.create(self.admin)

        # Setup Student User
        self.student = UserRecord(
            user_id="stu_1",
            tenant_id="ten_api",
            email="student@nhs.uk",
            name="Alice Student",
            role=UserRole.STUDENT,
            tier=SubscriptionTier.FREE,
        )
        self.db.users.create(self.student)

    # ----------------------------------------------------------------------
    # /auth Endpoint Tests
    # ----------------------------------------------------------------------

    def test_auth_register_success(self):
        """Register a new student."""
        body = json.dumps({
            "tenant_id": "ten_api",
            "email": "newbie@nhs.uk",
            "name": "Newbie Doc",
            "role": "STUDENT",
            "tier": "FREE",
        })
        req = APIRequest(path="/auth/register", method="POST", body=body)
        res = self.router.handle(req)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.body)
        self.assertEqual(data["email"], "newbie@nhs.uk")

    def test_auth_register_duplicate_email(self):
        """Duplicate registration rejected with 409 Conflict."""
        body = json.dumps({
            "tenant_id": "ten_api",
            "email": "student@nhs.uk",
            "name": "Another Student",
        })
        req = APIRequest(path="/auth/register", method="POST", body=body)
        res = self.router.handle(req)
        self.assertEqual(res.status_code, 409)

    def test_auth_login_success(self):
        """Valid login returns user details."""
        body = json.dumps({"email": "student@nhs.uk"})
        req = APIRequest(path="/auth/login", method="POST", body=body)
        res = self.router.handle(req)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.body)
        self.assertEqual(data["user_id"], "stu_1")

    def test_auth_me_authenticated(self):
        """Current user profile retrieved."""
        req = APIRequest(path="/auth/me", method="GET", user_id="stu_1")
        res = self.router.handle(req, user=self.student)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.body)
        self.assertEqual(data["email"], "student@nhs.uk")

    # ----------------------------------------------------------------------
    # /ai Endpoint Tests
    # ----------------------------------------------------------------------

    def test_ai_request_success(self):
        """AI chat request routed through gateway."""
        req = APIRequest(
            path="/ai/chat",
            method="POST",
            body="Describe symptoms of acute myocardial infarction",
            user_id="stu_1",
            tenant_id="ten_api",
        )
        res = self.router.handle(req, user=self.student)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.body)
        self.assertIn("explanation", data)

    # ----------------------------------------------------------------------
    # /student Endpoint Tests
    # ----------------------------------------------------------------------

    def test_student_record_attempt_and_view_analytics(self):
        """Student records attempt and retrieves progress analytics."""
        attempt_body = json.dumps({"topic": "Cardiology", "is_correct": True, "time_spent_seconds": 25.0})
        req_post = APIRequest(path="/student/attempts", method="POST", body=attempt_body)
        res_post = self.router.handle(req_post, user=self.student)
        self.assertEqual(res_post.status_code, 201)

        req_get = APIRequest(path="/student/analytics", method="GET")
        res_get = self.router.handle(req_get, user=self.student)
        self.assertEqual(res_get.status_code, 200)
        data = json.loads(res_get.body)
        self.assertEqual(data["total_attempts"], 1)
        self.assertEqual(data["overall_accuracy"], 1.0)

    # ----------------------------------------------------------------------
    # /documents Endpoint Tests
    # ----------------------------------------------------------------------

    def test_document_rbac_and_lifecycle(self):
        """Admin can upload and advance documents; student is denied upload."""
        # Student cannot upload
        body = json.dumps({"title": "BNF Guidelines"})
        req_stu = APIRequest(path="/documents/upload", method="POST", body=body)
        res_stu = self.router.handle(req_stu, user=self.student)
        self.assertEqual(res_stu.status_code, 403)

        # Admin can upload
        req_adm = APIRequest(path="/documents/upload", method="POST", body=body)
        res_adm = self.router.handle(req_adm, user=self.admin)
        self.assertEqual(res_adm.status_code, 201)
        doc_id = json.loads(res_adm.body)["doc_id"]

        # Advance to VALIDATION
        advance_body = json.dumps({"doc_id": doc_id, "next_stage": "VALIDATION"})
        req_adv = APIRequest(path="/documents/advance", method="POST", body=advance_body)
        res_adv = self.router.handle(req_adv, user=self.admin)
        self.assertEqual(res_adv.status_code, 200)
        self.assertEqual(json.loads(res_adv.body)["stage"], "VALIDATION")

    # ----------------------------------------------------------------------
    # /analytics Endpoint Tests
    # ----------------------------------------------------------------------

    def test_institution_analytics_rbac(self):
        """Admin can view institutional analytics; student is forbidden."""
        req = APIRequest(path="/analytics/institution", method="GET")

        # Student forbidden
        res_stu = self.router.handle(req, user=self.student)
        self.assertEqual(res_stu.status_code, 403)

        # Admin authorized
        res_adm = self.router.handle(req, user=self.admin)
        self.assertEqual(res_adm.status_code, 200)
        data = json.loads(res_adm.body)
        self.assertIn("cohort_accuracy", data)

    # ----------------------------------------------------------------------
    # /admin Endpoint Tests
    # ----------------------------------------------------------------------

    def test_admin_organizations_and_audit(self):
        """Admin creates organizations and views audit and usage."""
        # Create organization
        body = json.dumps({"name": "Emergency Department"})
        req_org = APIRequest(path="/admin/organizations", method="POST", body=body)
        res_org = self.router.handle(req_org, user=self.admin)
        self.assertEqual(res_org.status_code, 201)

        # Get audit logs
        req_aud = APIRequest(path="/admin/audit", method="GET")
        res_aud = self.router.handle(req_aud, user=self.admin)
        self.assertEqual(res_aud.status_code, 200)

        # Get usage metrics
        req_use = APIRequest(path="/admin/usage", method="GET")
        res_use = self.router.handle(req_use, user=self.admin)
        self.assertEqual(res_use.status_code, 200)

    def test_404_not_found(self):
        """Nonexistent route returns 404."""
        req = APIRequest(path="/unknown/path", method="GET")
        res = self.router.handle(req)
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
