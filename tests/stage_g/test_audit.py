"""Unit tests for Stage-G compliance and security audit service."""

import unittest

from medicalplab.stage_g.audit import AuditService
from medicalplab.stage_g.database import DatabaseService
from medicalplab.stage_g.models import AuditEventType


class TestStageGAudit(unittest.TestCase):
    """Test suite for audit event logging and retrieval."""

    def setUp(self):
        self.db = DatabaseService()
        self.audit = AuditService(self.db)

    def test_record_and_retrieve_events(self):
        """Record events across multiple event types."""
        ev1 = self.audit.record_event(
            tenant_id="ten_a",
            actor_id="usr_admin",
            event_type=AuditEventType.LOGIN,
            action="Admin login successful",
            metadata={"ip": "127.0.0.1"},
        )
        self.assertEqual(ev1.event_type, AuditEventType.LOGIN)

        ev2 = self.audit.record_event(
            tenant_id="ten_a",
            actor_id="usr_admin",
            event_type=AuditEventType.ADMIN_ACTION,
            action="Created Organization: Cardiology",
        )
        self.assertEqual(ev2.action, "Created Organization: Cardiology")

        events_a = self.audit.get_tenant_events("ten_a")
        self.assertEqual(len(events_a), 2)

    def test_audit_tenant_isolation(self):
        """Audit events must never leak across tenant boundaries."""
        self.audit.record_event(
            tenant_id="ten_a",
            actor_id="usr_1",
            event_type=AuditEventType.DOCUMENT_UPLOAD,
            action="Uploaded guidelines A",
        )
        self.audit.record_event(
            tenant_id="ten_b",
            actor_id="usr_2",
            event_type=AuditEventType.DOCUMENT_UPLOAD,
            action="Uploaded guidelines B",
        )

        events_a = self.audit.get_tenant_events("ten_a")
        events_b = self.audit.get_tenant_events("ten_b")

        self.assertEqual(len(events_a), 1)
        self.assertEqual(events_a[0].action, "Uploaded guidelines A")

        self.assertEqual(len(events_b), 1)
        self.assertEqual(events_b[0].action, "Uploaded guidelines B")

    def test_filter_by_actor(self):
        """Filter events by specific actor."""
        self.audit.record_event(
            tenant_id="ten_a",
            actor_id="usr_1",
            event_type=AuditEventType.AI_REQUEST,
            action="Requested case simulation",
        )
        self.audit.record_event(
            tenant_id="ten_a",
            actor_id="usr_2",
            event_type=AuditEventType.AI_REQUEST,
            action="Requested exam mode",
        )

        events_usr1 = self.audit.get_actor_events("usr_1")
        self.assertEqual(len(events_usr1), 1)
        self.assertEqual(events_usr1[0].actor_id, "usr_1")


if __name__ == "__main__":
    unittest.main()
