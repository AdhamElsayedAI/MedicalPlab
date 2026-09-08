"""AI usage tracking and cost accounting for Stage-G.

Logs every AI core request, token volume, model inference latency, and estimated cloud cost.
Demo/unconfigured runtime events are explicitly non-billable so telemetry never attributes
model cost to requests that did not execute a real model.
"""

from collections import Counter
import time
from typing import Any
import uuid

from medicalplab.stage_b.models import require, strings
from .database import DatabaseService
from .models import AIUsageRecord


# Pricing per 1k tokens in USD.
# Non-model runtime states are deliberately zero-cost and explicitly named.
MODEL_PRICING: dict[str, dict[str, float]] = {
    "qwen-2.5-7b-instruct": {
        "input_per_1k": 0.0015,
        "output_per_1k": 0.0020,
    },
    "demo-fallback": {
        "input_per_1k": 0.0,
        "output_per_1k": 0.0,
    },
    "unconfigured": {
        "input_per_1k": 0.0,
        "output_per_1k": 0.0,
    },
    "default": {
        "input_per_1k": 0.0015,
        "output_per_1k": 0.0020,
    },
}


class AIUsageTracker:
    """Tracks token consumption, latency, and costs for AI platform operations."""

    def __init__(self, db: DatabaseService):
        self.db = db

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_name: str = "qwen-2.5-7b-instruct",
    ) -> float:
        """Calculate deterministic dollar cost for token consumption."""
        require(input_tokens >= 0 and output_tokens >= 0, "Tokens cannot be negative")
        rates = MODEL_PRICING.get(model_name, MODEL_PRICING["default"])
        input_cost = (input_tokens / 1000.0) * rates["input_per_1k"]
        output_cost = (output_tokens / 1000.0) * rates["output_per_1k"]
        return round(input_cost + output_cost, 6)

    def record_usage(
        self,
        tenant_id: str,
        user_id: str,
        request_type: str,
        stage_used: str,
        latency_ms: float,
        success: bool,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model_name: str = "qwen-2.5-7b-instruct",
        timestamp: float | None = None,
    ) -> AIUsageRecord:
        """Record and persist an AI request execution event."""
        strings(tenant_id, user_id, request_type, stage_used, model_name)
        cost = self.calculate_cost(input_tokens, output_tokens, model_name)
        rec_id = f"USE-{uuid.uuid4().hex[:8].upper()}"

        record = AIUsageRecord(
            record_id=rec_id,
            tenant_id=tenant_id.strip(),
            user_id=user_id.strip(),
            request_type=request_type.strip(),
            stage_used=stage_used.strip(),
            model_name=model_name.strip(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=cost,
            latency_ms=round(latency_ms, 3),
            success=success,
            timestamp=timestamp if timestamp is not None else time.time(),
        )

        self.db.usage.save(record)
        return record

    def get_tenant_total_cost(self, tenant_id: str) -> float:
        """Aggregate total estimated AI spending for a tenant."""
        records = self.db.usage.list_by_tenant(tenant_id.strip())
        return round(sum(r.estimated_cost for r in records), 4)

    def get_user_request_count(self, user_id: str) -> int:
        """Return total requests issued by a specific user."""
        records = self.db.usage.list_by_user(user_id.strip())
        return len(records)

    def get_tenant_metrics(self, tenant_id: str) -> dict[str, Any]:
        """Aggregate granular operational and cost metrics for a tenant."""
        records = self.db.usage.list_by_tenant(tenant_id.strip())
        if not records:
            return {
                "total_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_estimated_cost_usd": 0.0,
                "average_latency_ms": 0.0,
                "success_rate": 1.0,
                "requests_by_type": {},
                "requests_by_model": {},
            }

        total_reqs = len(records)
        total_inp = sum(r.input_tokens for r in records)
        total_out = sum(r.output_tokens for r in records)
        total_cost = sum(r.estimated_cost for r in records)
        avg_lat = sum(r.latency_ms for r in records) / total_reqs
        succ_count = sum(1 for r in records if r.success)
        types_counter = Counter(r.request_type for r in records)
        models_counter = Counter(r.model_name for r in records)

        return {
            "total_requests": total_reqs,
            "total_input_tokens": total_inp,
            "total_output_tokens": total_out,
            "total_tokens": total_inp + total_out,
            "total_estimated_cost_usd": round(total_cost, 4),
            "average_latency_ms": round(avg_lat, 2),
            "success_rate": round(succ_count / total_reqs, 4),
            "requests_by_type": dict(types_counter),
            "requests_by_model": dict(models_counter),
        }
