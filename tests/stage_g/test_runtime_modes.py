import json
import unittest

from medicalplab.stage_g.audit import AuditService
from medicalplab.stage_g.database import DatabaseService
from medicalplab.stage_g.gateway import AIGateway
from medicalplab.stage_g.models import APIRequest, SubscriptionTier, UserRecord, UserRole
from medicalplab.stage_g.runtime import RuntimeMode, demo_fallbacks_allowed, strict_runtime_enabled
from medicalplab.stage_g.security import SecurityService
from medicalplab.stage_g.usage import AIUsageTracker


class TestRuntimeModes(unittest.TestCase):
    def _student(self, db: DatabaseService) -> UserRecord:
        student = UserRecord(
            user_id="runtime_student",
            tenant_id="runtime_tenant",
            email="runtime@example.com",
            name="Runtime Student",
            role=UserRole.STUDENT,
            tier=SubscriptionTier.FREE,
            is_active=True,
        )
        db.users.create(student)
        return student

    def test_mode_policy(self):
        self.assertTrue(demo_fallbacks_allowed(RuntimeMode.DEMO))
        self.assertTrue(demo_fallbacks_allowed(RuntimeMode.TEST))
        self.assertFalse(demo_fallbacks_allowed(RuntimeMode.PILOT))
        self.assertFalse(demo_fallbacks_allowed(RuntimeMode.PRODUCTION))
        self.assertTrue(strict_runtime_enabled(RuntimeMode.PILOT))
        self.assertTrue(strict_runtime_enabled(RuntimeMode.PRODUCTION))

    def test_production_gateway_fails_closed_without_orchestrator(self):
        db = DatabaseService()
        security = SecurityService()
        usage = AIUsageTracker(db)
        audit = AuditService(db)
        student = self._student(db)
        gateway = AIGateway(
            db,
            security,
            usage,
            audit,
            orchestrator=None,
            runtime_mode="production",
        )
        response = gateway.process_request(
            APIRequest(
                path="/ai/chat",
                method="POST",
                body="Explain this cardiovascular topic",
                tenant_id="runtime_tenant",
            ),
            user=student,
        )
        self.assertEqual(response.status_code, 503)
        payload = json.loads(response.body)
        self.assertEqual(payload["code"], "AI_ORCHESTRATOR_NOT_CONFIGURED")

        records = db.usage.list_by_user(student.user_id)
        self.assertEqual(len(records), 1)
        self.assertFalse(records[0].success)
        self.assertEqual(records[0].model_name, "unconfigured")
        self.assertEqual(records[0].estimated_cost, 0.0)

    def test_demo_gateway_labels_fallback(self):
        db = DatabaseService()
        security = SecurityService()
        usage = AIUsageTracker(db)
        audit = AuditService(db)
        student = self._student(db)
        gateway = AIGateway(
            db,
            security,
            usage,
            audit,
            orchestrator=None,
            runtime_mode="demo",
        )
        response = gateway.process_request(
            APIRequest(
                path="/ai/chat",
                method="POST",
                body="Demo question",
                tenant_id="runtime_tenant",
            ),
            user=student,
        )
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.body)
        self.assertTrue(payload["demo_fallback"])
        self.assertEqual(payload["model_name"], "demo-fallback")

        records = db.usage.list_by_user(student.user_id)
        self.assertEqual(records[0].estimated_cost, 0.0)


if __name__ == "__main__":
    unittest.main()
