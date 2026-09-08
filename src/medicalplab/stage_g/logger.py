"""Structured JSON telemetry and audit logger for Stage-G.
"""

import json
import time
from typing import Any


class StructuredLogger:
    """Production structured logger emitting deterministic JSON lines."""

    def __init__(self, service_name: str = "medicalplab"):
        self.service_name = service_name
        self.entries: list[dict[str, Any]] = []

    def log(
        self,
        level: str,
        event: str,
        tenant_id: str | None = None,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Emit and store a structured log record."""
        record = {
            "service": self.service_name,
            "level": level.upper(),
            "event": event,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "timestamp": time.time(),
            "metadata": kwargs,
        }
        self.entries.append(record)
        return record

    def info(self, event: str, **kwargs: Any) -> dict[str, Any]:
        return self.log("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> dict[str, Any]:
        return self.log("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> dict[str, Any]:
        return self.log("ERROR", event, **kwargs)
