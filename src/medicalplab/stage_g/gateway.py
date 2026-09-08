"""AI Gateway layer for Stage-G.

Enforces authentication, RBAC, tenant isolation, and subscription quotas before routing to Stage-F.
Tracks end-to-end latency, token usage, cloud costs, and security audit trails.
"""

import json
import time
from typing import Any

from medicalplab.stage_b.models import ContractError, require
from .audit import AuditService
from .database import DatabaseService
from .models import (
    APIRequest,
    APIResponse,
    AuditEventType,
    UserRecord,
)
from .security import PERM_AI_ASSIST, SecurityService
from .usage import AIUsageTracker


class AIGateway:
    """Production AI Gateway routing incoming requests to Stage-F."""

    def __init__(
        self,
        db: DatabaseService,
        security: SecurityService,
        usage: AIUsageTracker,
        audit: AuditService,
        orchestrator: Any | None = None,
    ):
        self.db = db
        self.security = security
        self.usage = usage
        self.audit = audit
        self.orchestrator = orchestrator

    def process_request(
        self,
        api_request: APIRequest,
        user: UserRecord,
        corpus: Any | None = None,
    ) -> APIResponse:
        """Execute request through the security gateway to the AI core."""
        start_time = time.perf_counter()

        # 1. User Authentication & Inactivity Check
        if not user.is_active:
            return APIResponse(
                status_code=401,
                body=json.dumps({"error": "User account is inactive or disabled"}),
            )

        # 2. RBAC Permission Check
        if not self.security.has_permission(user.role, PERM_AI_ASSIST):
            return APIResponse(
                status_code=403,
                body=json.dumps({"error": f"Role '{user.role.value}' not authorized for AI assistance"}),
            )

        # 3. Tenant Isolation Check
        if api_request.tenant_id and api_request.tenant_id != user.tenant_id:
            return APIResponse(
                status_code=403,
                body=json.dumps({"error": "Cross-tenant access forbidden"}),
            )

        # 4. Subscription Quota Check
        used_today = self.usage.get_user_request_count(user.user_id)
        if not self.security.check_quota(user.tier, used_today):
            return APIResponse(
                status_code=429,
                body=json.dumps({
                    "error": f"Daily quota exceeded for subscription tier '{user.tier.value}'. Please upgrade to Premium or Institution tier."
                }),
            )

        # 5. Forwarding to Stage-F Orchestrator
        input_text = api_request.body.strip()
        if not input_text:
            return APIResponse(
                status_code=400,
                body=json.dumps({"error": "Request body cannot be empty"}),
            )

        input_tokens = max(1, len(input_text) // 4)

        try:
            if self.orchestrator:
                platform_response = self.orchestrator.handle_request(
                    student_id=user.user_id,
                    query=input_text,
                    corpus=corpus,
                )
                intent_str = platform_response.intent.value
                explanation = platform_response.explanation
                next_actions = list(platform_response.next_actions)
                payload_data = dict(platform_response.payload)
            else:
                intent_str = "teaching"
                explanation = f"AI assistant response for: {input_text}"
                next_actions = ["Continue learning"]
                payload_data = {"status": "ok"}

            output_text = f"{explanation} {' '.join(next_actions)}"
            output_tokens = max(1, len(output_text) // 4)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            # 6. Record Usage Analytics
            self.usage.record_usage(
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                request_type=intent_str,
                stage_used="stage_f",
                latency_ms=elapsed_ms,
                success=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_name="qwen-2.5-7b-instruct",
            )

            # 7. Record Security Audit Event
            self.audit.record_event(
                tenant_id=user.tenant_id,
                actor_id=user.user_id,
                event_type=AuditEventType.AI_REQUEST,
                action=f"AI Request: {intent_str}",
                metadata={"tokens": str(input_tokens + output_tokens), "latency_ms": str(int(elapsed_ms))},
            )

            response_body = json.dumps({
                "intent": intent_str,
                "explanation": explanation,
                "payload": payload_data,
                "next_actions": next_actions,
                "latency_ms": round(elapsed_ms, 2),
            })

            return APIResponse(status_code=200, body=response_body)

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.usage.record_usage(
                tenant_id=user.tenant_id,
                user_id=user.user_id,
                request_type="unknown",
                stage_used="stage_f",
                latency_ms=elapsed_ms,
                success=False,
                input_tokens=input_tokens,
                output_tokens=0,
            )
            return APIResponse(
                status_code=500,
                body=json.dumps({"error": f"Internal AI processing failure: {type(e).__name__} - {e}"}),
            )
