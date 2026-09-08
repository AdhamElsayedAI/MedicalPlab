"""Production REST-style API Layer for Stage-G.

Provides endpoint routing, request validation, RBAC enforcement,
tenant boundary isolation, error handling, and uniform APIResponse generation.

Endpoints supported:
- /auth: Registration, login, current profile
- /ai: Direct gateway invocation into Stage-F AI intelligence
- /student: Student performance metrics, attempts recording
- /documents: Document ingestion lifecycle and tenant document management
- /analytics: Individual student and institutional cohort analytics
- /admin: Organization hierarchy, memberships, tenant usage and audit logs
"""

import json
import uuid
from typing import Any, Dict, Optional

from medicalplab.stage_b.models import ContractError, require
from .analytics import PlatformAnalyticsService
from .audit import AuditService
from .database import DatabaseService
from .gateway import AIGateway
from .knowledge_management import MedicalKnowledgeManager
from .models import (
    APIRequest,
    APIResponse,
    AuditEventType,
    DocumentStage,
    SubscriptionTier,
    UserRecord,
    UserRole,
)
from .multitenancy import MultiTenancyService
from .security import (
    PERM_AI_ASSIST,
    PERM_ANALYTICS_VIEW,
    PERM_CONTENT_REVIEW,
    PERM_DOC_MANAGE,
    PERM_LEARNING_READ,
    PERM_USER_MANAGE,
    SecurityService,
)


class PlatformAPIRouter:
    """Production API gateway and router for MedicalPlab SaaS platform."""

    def __init__(
        self,
        db: DatabaseService,
        security: SecurityService,
        multitenancy: MultiTenancyService,
        knowledge: MedicalKnowledgeManager,
        analytics: PlatformAnalyticsService,
        gateway: AIGateway,
        audit: AuditService,
    ):
        self.db = db
        self.security = security
        self.multitenancy = multitenancy
        self.knowledge = knowledge
        self.analytics = analytics
        self.gateway = gateway
        self.audit = audit

    def handle(self, request: APIRequest, user: Optional[UserRecord] = None) -> APIResponse:
        """Route incoming APIRequest to the appropriate controller."""
        try:
            # 1. Resolve user from request if not explicitly provided
            resolved_user = user or self._resolve_user(request)

            # 2. Path dispatching
            path = request.path.rstrip("/")
            method = request.method.upper()

            # /auth endpoints
            if path.startswith("/auth"):
                return self._handle_auth(path, method, request, resolved_user)

            # /ai endpoints
            if path.startswith("/ai"):
                return self._handle_ai(path, method, request, resolved_user)

            # /student endpoints
            if path.startswith("/student"):
                return self._handle_student(path, method, request, resolved_user)

            # /documents endpoints
            if path.startswith("/documents"):
                return self._handle_documents(path, method, request, resolved_user)

            # /analytics endpoints
            if path.startswith("/analytics"):
                return self._handle_analytics(path, method, request, resolved_user)

            # /admin endpoints
            if path.startswith("/admin"):
                return self._handle_admin(path, method, request, resolved_user)

            return self._json_response(404, {"error": f"Endpoint not found: {method} {request.path}"})

        except ContractError as ce:
            return self._json_response(400, {"error": str(ce)})
        except json.JSONDecodeError:
            return self._json_response(400, {"error": "Invalid JSON body payload"})
        except Exception as ex:
            return self._json_response(500, {"error": f"Internal server error: {type(ex).__name__} - {str(ex)}"})

    # ----------------------------------------------------------------------
    # Controller: /auth
    # ----------------------------------------------------------------------

    def _handle_auth(
        self, path: str, method: str, request: APIRequest, user: Optional[UserRecord]
    ) -> APIResponse:
        if path == "/auth/register" and method == "POST":
            data = self._parse_json(request.body)
            tenant_id = data.get("tenant_id")
            email = data.get("email")
            name = data.get("name")
            role_str = data.get("role", "STUDENT")
            tier_str = data.get("tier", "FREE")

            if not tenant_id or not email or not name:
                return self._json_response(400, {"error": "Missing required fields: tenant_id, email, name"})

            # Verify tenant exists
            tenant = self.db.tenants.get(tenant_id)
            if not tenant:
                return self._json_response(404, {"error": f"Tenant '{tenant_id}' does not exist"})

            # Check if user already exists
            existing = self.db.users.get_by_email(email)
            if existing:
                return self._json_response(409, {"error": f"User with email '{email}' already registered"})

            try:
                role = UserRole(role_str)
                tier = SubscriptionTier(tier_str)
            except ValueError:
                return self._json_response(400, {"error": f"Invalid role '{role_str}' or tier '{tier_str}'"})

            user_id = f"user_{uuid.uuid4().hex[:12]}"
            new_user = UserRecord(
                user_id=user_id,
                tenant_id=tenant_id,
                email=email,
                name=name,
                role=role,
                tier=tier,
                is_active=True,
            )
            self.db.users.create(new_user)

            self.audit.record_event(
                tenant_id=tenant_id,
                actor_id=user_id,
                event_type=AuditEventType.LOGIN,
                action="User registered",
                metadata={"email": email, "role": role.value},
            )

            return self._json_response(
                201,
                {
                    "message": "User registered successfully",
                    "user_id": new_user.user_id,
                    "email": new_user.email,
                    "tenant_id": new_user.tenant_id,
                    "role": new_user.role.value,
                    "tier": new_user.tier.value,
                },
            )

        if path == "/auth/login" and method == "POST":
            data = self._parse_json(request.body)
            email = data.get("email")
            if not email:
                return self._json_response(400, {"error": "Missing 'email' in request body"})

            user_record = self.db.users.get_by_email(email)
            if not user_record or not user_record.is_active:
                return self._json_response(401, {"error": "Invalid credentials or inactive account"})

            self.audit.record_event(
                tenant_id=user_record.tenant_id,
                actor_id=user_record.user_id,
                event_type=AuditEventType.LOGIN,
                action="User logged in",
                metadata={"email": email},
            )

            return self._json_response(
                200,
                {
                    "message": "Authentication successful",
                    "token": user_record.user_id,
                    "user_id": user_record.user_id,
                    "tenant_id": user_record.tenant_id,
                    "role": user_record.role.value,
                    "tier": user_record.tier.value,
                },
            )

        if path == "/auth/me" and method == "GET":
            if not user:
                return self._json_response(401, {"error": "Authentication required"})
            return self._json_response(
                200,
                {
                    "user_id": user.user_id,
                    "tenant_id": user.tenant_id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role.value,
                    "tier": user.tier.value,
                    "is_active": user.is_active,
                },
            )

        return self._json_response(404, {"error": f"Endpoint not found: {method} {path}"})

    # ----------------------------------------------------------------------
    # Controller: /ai
    # ----------------------------------------------------------------------

    def _handle_ai(
        self, path: str, method: str, request: APIRequest, user: Optional[UserRecord]
    ) -> APIResponse:
        if not user:
            return self._json_response(401, {"error": "Authentication required for AI gateway"})

        if method != "POST":
            return self._json_response(405, {"error": "Method not allowed for /ai endpoint"})

        # Route through AI Gateway
        return self.gateway.process_request(request, user=user)

    # ----------------------------------------------------------------------
    # Controller: /student
    # ----------------------------------------------------------------------

    def _handle_student(
        self, path: str, method: str, request: APIRequest, user: Optional[UserRecord]
    ) -> APIResponse:
        if not user:
            return self._json_response(401, {"error": "Authentication required"})

        if not self.security.has_permission(user.role, PERM_LEARNING_READ):
            return self._json_response(403, {"error": "Permission denied for student learning data"})

        if path == "/student/analytics" and method == "GET":
            # Student can only query their own data unless admin or doctor
            target_student_id = user.user_id
            stats = self.analytics.compute_student_analytics(target_student_id, user.tenant_id)
            return self._json_response(
                200,
                {
                    "student_id": stats.student_id,
                    "tenant_id": stats.tenant_id,
                    "total_attempts": stats.total_attempts,
                    "overall_accuracy": stats.overall_accuracy,
                    "mastery_level": stats.mastery_level,
                    "weak_topics": list(stats.weak_topics),
                    "improvement_rate": stats.improvement_rate,
                },
            )

        if path == "/student/attempts" and method == "POST":
            data = self._parse_json(request.body)
            topic = data.get("topic")
            is_correct = data.get("is_correct")
            time_spent = data.get("time_spent_seconds", 30.0)

            if topic is None or is_correct is None:
                return self._json_response(400, {"error": "Missing 'topic' or 'is_correct'"})

            attempt_id = f"att_{uuid.uuid4().hex[:12]}"
            attempt = {
                "attempt_id": attempt_id,
                "student_id": user.user_id,
                "tenant_id": user.tenant_id,
                "topic": topic,
                "is_correct": bool(is_correct),
                "time_spent_seconds": float(time_spent),
            }
            self.db.attempts.record(attempt)
            return self._json_response(201, {"message": "Attempt recorded", "attempt_id": attempt_id})

        return self._json_response(404, {"error": f"Endpoint not found: {method} {path}"})

    # ----------------------------------------------------------------------
    # Controller: /documents
    # ----------------------------------------------------------------------

    def _handle_documents(
        self, path: str, method: str, request: APIRequest, user: Optional[UserRecord]
    ) -> APIResponse:
        if not user:
            return self._json_response(401, {"error": "Authentication required"})

        if path == "/documents" and method == "GET":
            # List tenant documents
            docs = self.knowledge.list_tenant_documents(user.tenant_id)
            return self._json_response(
                200,
                {
                    "documents": [
                        {
                            "doc_id": d.doc_id,
                            "title": d.title,
                            "stage": d.stage.value,
                            "version": d.version,
                            "file_size_bytes": d.file_size_bytes,
                            "mime_type": d.mime_type,
                            "created_at": d.created_at,
                            "updated_at": d.updated_at,
                        }
                        for d in docs
                    ]
                },
            )

        if path == "/documents/upload" and method == "POST":
            if not self.security.has_permission(user.role, PERM_DOC_MANAGE):
                return self._json_response(403, {"error": "Permission denied: Cannot upload documents"})

            data = self._parse_json(request.body)
            title = data.get("title")
            file_path = data.get("file_path", f"/uploads/{title}")
            file_size_bytes = data.get("file_size_bytes", 1024)
            mime_type = data.get("mime_type", "application/pdf")
            metadata = data.get("metadata", {})

            if not title:
                return self._json_response(400, {"error": "Missing required field: 'title'"})

            doc = self.knowledge.upload_document(
                tenant_id=user.tenant_id,
                owner_id=user.user_id,
                title=title,
                file_path=file_path,
                file_size_bytes=int(file_size_bytes),
                mime_type=mime_type,
                metadata=metadata,
            )
            return self._json_response(
                201,
                {
                    "message": "Document uploaded successfully",
                    "doc_id": doc.doc_id,
                    "stage": doc.stage.value,
                    "title": doc.title,
                    "version": doc.version,
                },
            )

        if path == "/documents/advance" and method == "POST":
            if not self.security.has_permission(user.role, PERM_DOC_MANAGE):
                return self._json_response(403, {"error": "Permission denied: Cannot advance document stages"})

            data = self._parse_json(request.body)
            doc_id = data.get("doc_id")
            next_stage_str = data.get("next_stage")

            if not doc_id or not next_stage_str:
                return self._json_response(400, {"error": "Missing 'doc_id' or 'next_stage'"})

            try:
                next_stage = DocumentStage(next_stage_str)
            except ValueError:
                return self._json_response(400, {"error": f"Invalid DocumentStage: {next_stage_str}"})

            updated_doc = self.knowledge.advance_stage(doc_id, user.tenant_id, next_stage, actor_id=user.user_id)
            return self._json_response(
                200,
                {
                    "message": f"Document advanced to {updated_doc.stage.value}",
                    "doc_id": updated_doc.doc_id,
                    "stage": updated_doc.stage.value,
                    "version": updated_doc.version,
                },
            )

        return self._json_response(404, {"error": f"Endpoint not found: {method} {path}"})

    # ----------------------------------------------------------------------
    # Controller: /analytics
    # ----------------------------------------------------------------------

    def _handle_analytics(
        self, path: str, method: str, request: APIRequest, user: Optional[UserRecord]
    ) -> APIResponse:
        if not user:
            return self._json_response(401, {"error": "Authentication required"})

        if path == "/analytics/student" and method == "GET":
            student_stats = self.analytics.compute_student_analytics(user.user_id, user.tenant_id)
            return self._json_response(
                200,
                {
                    "student_id": student_stats.student_id,
                    "tenant_id": student_stats.tenant_id,
                    "total_attempts": student_stats.total_attempts,
                    "overall_accuracy": student_stats.overall_accuracy,
                    "mastery_level": student_stats.mastery_level,
                    "weak_topics": list(student_stats.weak_topics),
                    "improvement_rate": student_stats.improvement_rate,
                },
            )

        if path == "/analytics/institution" and method == "GET":
            if not self.security.has_permission(user.role, PERM_ANALYTICS_VIEW):
                return self._json_response(403, {"error": "Permission denied: Requires institutional analytics access"})

            cohort_stats = self.analytics.compute_institution_analytics(user.tenant_id)
            return self._json_response(
                200,
                {
                    "tenant_id": cohort_stats.tenant_id,
                    "cohort_id": cohort_stats.cohort_id,
                    "total_students": cohort_stats.total_students,
                    "active_students_7d": cohort_stats.active_students_7d,
                    "cohort_accuracy": cohort_stats.cohort_accuracy,
                    "difficult_topics": list(cohort_stats.difficult_topics),
                    "total_ai_requests": cohort_stats.total_ai_requests,
                },
            )

        return self._json_response(404, {"error": f"Endpoint not found: {method} {path}"})

    # ----------------------------------------------------------------------
    # Controller: /admin
    # ----------------------------------------------------------------------

    def _handle_admin(
        self, path: str, method: str, request: APIRequest, user: Optional[UserRecord]
    ) -> APIResponse:
        if not user:
            return self._json_response(401, {"error": "Authentication required"})

        if not self.security.has_permission(user.role, PERM_USER_MANAGE):
            return self._json_response(403, {"error": "Permission denied: Requires INSTITUTION_ADMIN privileges"})

        if path == "/admin/organizations" and method == "POST":
            data = self._parse_json(request.body)
            org_name = data.get("name")
            if not org_name:
                return self._json_response(400, {"error": "Missing 'name' in request body"})

            org = self.multitenancy.create_organization(user.tenant_id, org_name)
            return self._json_response(
                201,
                {"message": "Organization created", "org_id": org.org_id, "name": org.name, "tenant_id": org.tenant_id},
            )

        if path == "/admin/organizations" and method == "GET":
            orgs = self.multitenancy.list_organizations(user.tenant_id)
            return self._json_response(
                200,
                {"organizations": [{"org_id": o.org_id, "name": o.name, "tenant_id": o.tenant_id} for o in orgs]},
            )

        if path == "/admin/memberships" and method == "POST":
            data = self._parse_json(request.body)
            target_user_id = data.get("user_id")
            org_id = data.get("org_id")
            role_str = data.get("role", "MEMBER")

            if not target_user_id or not org_id:
                return self._json_response(400, {"error": "Missing 'user_id' or 'org_id'"})

            membership = self.multitenancy.assign_membership(target_user_id, org_id, user.tenant_id, role=role_str)
            return self._json_response(
                201,
                {
                    "message": "Membership assigned",
                    "membership_id": membership.membership_id,
                    "user_id": membership.user_id,
                    "org_id": membership.org_id,
                    "tenant_id": membership.tenant_id,
                    "role": membership.role,
                },
            )

        if path == "/admin/usage" and method == "GET":
            metrics = self.gateway.usage.get_tenant_metrics(user.tenant_id)
            return self._json_response(200, metrics)

        if path == "/admin/audit" and method == "GET":
            events = self.audit.get_tenant_events(user.tenant_id)
            return self._json_response(
                200,
                {
                    "audit_events": [
                        {
                            "event_id": e.event_id,
                            "actor_id": e.actor_id,
                            "event_type": e.event_type.value,
                            "action": e.action,
                            "timestamp": e.timestamp,
                            "metadata": dict(e.metadata),
                        }
                        for e in events
                    ]
                },
            )

        return self._json_response(404, {"error": f"Endpoint not found: {method} {path}"})

    # ----------------------------------------------------------------------
    # Internal Helpers
    # ----------------------------------------------------------------------

    def _resolve_user(self, request: APIRequest) -> Optional[UserRecord]:
        """Resolve authenticated UserRecord from request token, headers, or request envelope."""
        # 1. Direct user_id attribute on APIRequest
        if request.user_id:
            user = self.db.users.get(request.user_id)
            if user:
                return user

        # 2. Authorization header: "Bearer <user_id>" or "<user_id>"
        for key, val in request.headers:
            if key.lower() == "authorization":
                token = val.replace("Bearer ", "").strip()
                if token:
                    user = self.db.users.get(token)
                    if user:
                        return user

        return None

    def _parse_json(self, body: str) -> Dict[str, Any]:
        """Safely parse JSON request body."""
        if not body or not body.strip():
            return {}
        return json.loads(body)

    def _json_response(self, status_code: int, data: Dict[str, Any]) -> APIResponse:
        """Helper to build APIResponse with application/json header."""
        return APIResponse(
            status_code=status_code,
            headers=(("Content-Type", "application/json"),),
            body=json.dumps(data),
        )
