"""Unit tests for Stage-G AI Gateway."""

import json
import unittest

from medicalplab.stage_g.audit import AuditService
from medicalplab.stage_g.database import DatabaseService
from medicalplab.stage_g.gateway import AIGateway
from medicalplab.stage_g.models import (
    APIRequest,
    AuditEventType,
    SubscriptionTier,
    UserRecord,
    UserRole,
)
from medicalplab.stage_g.security import SecurityService
from medicalplab.stage_g.usage import AIUsageTracker


class TestStageGGateway(unittest.TestCase):
    """Test suite for AI Gateway request lifecycle and policy enforcement."""

    def setUp(self):
        self.db = DatabaseService()
        self.security = SecurityService()
        self.usage = AIUsageTracker(self.db)
        self.audit = AuditService(self.db)
        self.gateway = AIGateway(self.db, self.security, self.usage, self.audit)

        self.student = UserRecord(
            user_id="stu_10",
            tenant_id="ten_x",
            email="s10@med.org",
            name="Alice Student",
            role=UserRole.STUDENT,
            tier=SubscriptionTier.FREE,
            is_active=True,
        )
        self.db.users.create(self.student)

    def test_successful_gateway_request(self):
        """Standard valid request completes with 200, creates usage record, and emits audit event."""
        req = APIRequest(
            path="/ai/chat",
            method="POST",
            body="What are the signs of acute cardiac tamponade?",
            user_id="stu_10",
            tenant_id="ten_x",
        )

        res = self.gateway.process_request(req, user=self.student)
        self.assertEqual(res.status_code, 200)

        data = json.loads(res.body)
        self.assertIn("explanation", data)
        self.assertIn("latency_ms", data)

        # Verify usage record created
        user_usages = self.db.usage.list_by_user("stu_10")
        self.assertEqual(len(user_usages), 1)
        self.assertEqual(user_usages[0].stage_used, "stage_f")
        self.assertTrue(user_usages[0].success)

        # Verify audit event created
        audit_events = self.db.audit.list_by_tenant("ten_x")
        self.assertEqual(len(audit_events), 1)
        self.assertEqual(audit_events[0].event_type, AuditEventType.AI_REQUEST)

    def test_inactive_user_rejected(self):
        """Inactive user receives 401 Unauthorized."""
        inactive_user = UserRecord(
            user_id="stu_inactive",
            tenant_id="ten_x",
            email="inactive@med.org",
            name="Inactive User",
            role=UserRole.STUDENT,
            tier=SubscriptionTier.FREE,
            is_active=False,
        )

        req = APIRequest(path="/ai/chat", method="POST", body="Test question")
        res = self.gateway.process_request(req, user=inactive_user)
        self.assertEqual(res.status_code, 401)

    def test_cross_tenant_request_rejected(self):
        """Request targeting different tenant_id receives 403 Forbidden."""
        req = APIRequest(
            path="/ai/chat",
            method="POST",
            body="Test question",
            tenant_id="ten_other",
        )
        res = self.gateway.process_request(req, user=self.student)
        self.assertEqual(res.status_code, 403)
        self.assertIn("Cross-tenant access forbidden", res.body)

    def test_quota_exceeded_rejected(self):
        """Free tier user exceeding 20 daily requests receives 429 Too Many Requests."""
        # Exhaust quota (FREE has 20 requests)
        for i in range(20):
            self.usage.record_usage(
                tenant_id="ten_x",
                user_id="stu_10",
                request_type="teaching",
                stage_used="stage_f",
                latency_ms=10.0,
                success=True,
                input_tokens=10,
                output_tokens=10,
            )

        req = APIRequest(path="/ai/chat", method="POST", body="Request #21")
        res = self.gateway.process_request(req, user=self.student)
        self.assertEqual(res.status_code, 429)
        self.assertIn("Daily quota exceeded", res.body)

    def test_empty_body_rejected(self):
        """Empty query body receives 400 Bad Request."""
        req = APIRequest(path="/ai/chat", method="POST", body="   ")
        res = self.gateway.process_request(req, user=self.student)
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
