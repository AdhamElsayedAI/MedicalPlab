"""Compliance and security audit service for Stage-G.

Records tamper-evident audit events for logins, AI queries, document operations, and administrative actions.
"""

import time
from typing import Any, Mapping
import uuid

from medicalplab.stage_b.models import require, strings
from .database import DatabaseService
from .models import AuditEvent, AuditEventType


class AuditService:
    """Enterprise audit trail service ensuring regulatory and security traceability."""

    def __init__(self, db: DatabaseService):
        self.db = db

    def record_event(
        self,
        tenant_id: str,
        actor_id: str,
        event_type: AuditEventType,
        action: str,
        metadata: Mapping[str, Any] | None = None,
        timestamp: float | None = None,
    ) -> AuditEvent:
        """Record and persist an immutable audit event."""
        strings(tenant_id, actor_id, action)
        require(isinstance(event_type, AuditEventType), f"Invalid event_type: {event_type}")
        evt_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"

        meta_pairs: list[tuple[str, str]] = []
        if metadata:
            for k, v in metadata.items():
                meta_pairs.append((str(k), str(v)))

        event = AuditEvent(
            event_id=evt_id,
            tenant_id=tenant_id.strip(),
            actor_id=actor_id.strip(),
            event_type=event_type,
            action=action.strip(),
            timestamp=timestamp if timestamp is not None else time.time(),
            metadata=tuple(meta_pairs),
        )

        self.db.audit.save(event)
        return event

    def get_tenant_trail(self, tenant_id: str) -> tuple[AuditEvent, ...]:
        """Retrieve complete audit history for an institutional tenant."""
        return self.db.audit.list_by_tenant(tenant_id.strip())

    def get_tenant_events(self, tenant_id: str) -> tuple[AuditEvent, ...]:
        """Alias for get_tenant_trail."""
        return self.get_tenant_trail(tenant_id)

    def get_actor_events(self, actor_id: str) -> tuple[AuditEvent, ...]:
        """Retrieve audit events initiated by a specific actor."""
        return self.db.audit.list_by_actor(actor_id.strip())
