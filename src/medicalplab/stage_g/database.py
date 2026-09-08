"""PostgreSQL-ready database repository abstractions and in-memory implementation for Stage-G.

Decouples all platform business logic from underlying database engines via the Repository pattern.
"""

from abc import ABC, abstractmethod
from typing import Any, Sequence

from .models import (
    AIUsageRecord,
    AuditEvent,
    DocumentRecord,
    InstitutionAnalyticsRecord,
    Membership,
    Organization,
    StudentAnalyticsRecord,
    Tenant,
    UserRecord,
)


# --- Interfaces ---

class UserRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, user_id: str) -> UserRecord | None: ...
    @abstractmethod
    def get_by_email(self, email: str) -> UserRecord | None: ...
    @abstractmethod
    def list_by_tenant(self, tenant_id: str) -> tuple[UserRecord, ...]: ...
    @abstractmethod
    def save(self, user: UserRecord) -> None: ...
    @abstractmethod
    def delete(self, user_id: str) -> None: ...


class TenantRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, tenant_id: str) -> Tenant | None: ...
    @abstractmethod
    def list_all(self) -> tuple[Tenant, ...]: ...
    @abstractmethod
    def save(self, tenant: Tenant) -> None: ...


class OrganizationRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, org_id: str) -> Organization | None: ...
    @abstractmethod
    def list_by_tenant(self, tenant_id: str) -> tuple[Organization, ...]: ...
    @abstractmethod
    def save(self, org: Organization) -> None: ...
    @abstractmethod
    def create_membership(self, membership: Membership) -> None: ...
    @abstractmethod
    def list_memberships_by_org(self, org_id: str) -> tuple[Membership, ...]: ...


class DocumentRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, doc_id: str) -> DocumentRecord | None: ...
    @abstractmethod
    def list_by_tenant(self, tenant_id: str) -> tuple[DocumentRecord, ...]: ...
    @abstractmethod
    def save(self, doc: DocumentRecord) -> None: ...
    @abstractmethod
    def delete(self, doc_id: str) -> None: ...


class SessionRepositoryInterface(ABC):
    @abstractmethod
    def get_by_id(self, session_id: str) -> Any | None: ...
    @abstractmethod
    def save(self, session: Any) -> None: ...
    @abstractmethod
    def delete(self, session_id: str) -> None: ...


class AttemptRepositoryInterface(ABC):
    @abstractmethod
    def save(self, attempt: Any) -> None: ...
    @abstractmethod
    def list_by_student(self, student_id: str) -> tuple[Any, ...]: ...
    @abstractmethod
    def list_by_tenant(self, tenant_id: str) -> tuple[Any, ...]: ...


class AnalyticsRepositoryInterface(ABC):
    @abstractmethod
    def save_student(self, record: StudentAnalyticsRecord) -> None: ...
    @abstractmethod
    def get_student(self, student_id: str) -> StudentAnalyticsRecord | None: ...
    @abstractmethod
    def save_institution(self, record: InstitutionAnalyticsRecord) -> None: ...
    @abstractmethod
    def get_institution(self, tenant_id: str, cohort_id: str = "") -> InstitutionAnalyticsRecord | None: ...


class AIUsageRepositoryInterface(ABC):
    @abstractmethod
    def save(self, record: AIUsageRecord) -> None: ...
    @abstractmethod
    def list_by_tenant(self, tenant_id: str) -> tuple[AIUsageRecord, ...]: ...
    @abstractmethod
    def list_by_user(self, user_id: str) -> tuple[AIUsageRecord, ...]: ...


class AuditRepositoryInterface(ABC):
    @abstractmethod
    def save(self, event: AuditEvent) -> None: ...
    @abstractmethod
    def list_by_tenant(self, tenant_id: str) -> tuple[AuditEvent, ...]: ...
    @abstractmethod
    def list_by_actor(self, actor_id: str) -> tuple[AuditEvent, ...]: ...


# Type aliases for repository contracts
UserRepository = UserRepositoryInterface
TenantRepository = TenantRepositoryInterface
OrganizationRepository = OrganizationRepositoryInterface
DocumentRepository = DocumentRepositoryInterface
SessionRepository = SessionRepositoryInterface
AttemptRepository = AttemptRepositoryInterface
AnalyticsRepository = AnalyticsRepositoryInterface
AIUsageRepository = AIUsageRepositoryInterface
AuditRepository = AuditRepositoryInterface


# --- In-Memory Implementations ---

class InMemoryUserRepository(UserRepositoryInterface):
    def __init__(self):
        self._users: dict[str, UserRecord] = {}

    def get(self, user_id: str) -> UserRecord | None:
        return self.get_by_id(user_id)

    def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._users.get(user_id.strip())

    def get_by_email(self, email: str) -> UserRecord | None:
        clean = email.strip().lower()
        for u in self._users.values():
            if u.email.strip().lower() == clean:
                return u
        return None

    def list_by_tenant(self, tenant_id: str) -> tuple[UserRecord, ...]:
        clean = tenant_id.strip()
        return tuple(u for u in self._users.values() if u.tenant_id == clean)

    def save(self, user: UserRecord) -> None:
        self._users[user.user_id.strip()] = user

    def create(self, user: UserRecord) -> None:
        self.save(user)

    def update(self, user: UserRecord) -> None:
        self.save(user)

    def delete(self, user_id: str) -> None:
        self._users.pop(user_id.strip(), None)


class InMemoryTenantRepository(TenantRepositoryInterface):
    def __init__(self):
        self._tenants: dict[str, Tenant] = {}

    def get(self, tenant_id: str) -> Tenant | None:
        return self.get_by_id(tenant_id)

    def get_by_id(self, tenant_id: str) -> Tenant | None:
        return self._tenants.get(tenant_id.strip())

    def list_all(self) -> tuple[Tenant, ...]:
        return tuple(self._tenants.values())

    def save(self, tenant: Tenant) -> None:
        self._tenants[tenant.tenant_id.strip()] = tenant

    def create(self, tenant: Tenant) -> None:
        self.save(tenant)

    def update(self, tenant: Tenant) -> None:
        self.save(tenant)


class InMemoryOrganizationRepository(OrganizationRepositoryInterface):
    def __init__(self):
        self._orgs: dict[str, Organization] = {}
        self._memberships: list[Membership] = []

    def get(self, org_id: str) -> Organization | None:
        return self.get_by_id(org_id)

    def get_by_id(self, org_id: str) -> Organization | None:
        return self._orgs.get(org_id.strip())

    def list_by_tenant(self, tenant_id: str) -> tuple[Organization, ...]:
        clean = tenant_id.strip()
        return tuple(o for o in self._orgs.values() if o.tenant_id == clean)

    def save(self, org: Organization) -> None:
        self._orgs[org.org_id.strip()] = org

    def create(self, org: Organization) -> None:
        self.save(org)

    def create_membership(self, membership: Membership) -> None:
        self._memberships.append(membership)

    def list_memberships_by_org(self, org_id: str) -> tuple[Membership, ...]:
        clean = org_id.strip()
        return tuple(m for m in self._memberships if m.org_id == clean)


class InMemoryDocumentRepository(DocumentRepositoryInterface):
    def __init__(self):
        self._docs: dict[str, DocumentRecord] = {}

    def get(self, doc_id: str) -> DocumentRecord | None:
        return self.get_by_id(doc_id)

    def get_by_id(self, doc_id: str) -> DocumentRecord | None:
        return self._docs.get(doc_id.strip())

    def list_by_tenant(self, tenant_id: str) -> tuple[DocumentRecord, ...]:
        clean = tenant_id.strip()
        return tuple(d for d in self._docs.values() if d.tenant_id == clean)

    def save(self, doc: DocumentRecord) -> None:
        self._docs[doc.doc_id.strip()] = doc

    def create(self, doc: DocumentRecord) -> None:
        self.save(doc)

    def update(self, doc: DocumentRecord) -> None:
        self.save(doc)

    def delete(self, doc_id: str) -> None:
        self._docs.pop(doc_id.strip(), None)


class InMemorySessionRepository(SessionRepositoryInterface):
    def __init__(self):
        self._sessions: dict[str, Any] = {}

    def get(self, session_id: str) -> Any | None:
        return self.get_by_id(session_id)

    def get_by_id(self, session_id: str) -> Any | None:
        return self._sessions.get(session_id.strip())

    def save(self, session: Any) -> None:
        sid = getattr(session, "session_id", str(id(session)))
        self._sessions[sid.strip()] = session

    def create(self, session: Any) -> None:
        self.save(session)

    def update(self, session: Any) -> None:
        self.save(session)

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id.strip(), None)


class InMemoryAttemptRepository(AttemptRepositoryInterface):
    def __init__(self):
        self._attempts: list[Any] = []

    def record(self, attempt: Any) -> None:
        self.save(attempt)

    def save(self, attempt: Any) -> None:
        self._attempts.append(attempt)

    def list_by_student(self, student_id: str) -> tuple[Any, ...]:
        clean = student_id.strip()
        return tuple(
            a for a in self._attempts
            if (isinstance(a, dict) and a.get("student_id") == clean) or getattr(a, "student_id", "") == clean
        )

    def list_by_tenant(self, tenant_id: str) -> tuple[Any, ...]:
        clean = tenant_id.strip()
        return tuple(
            a for a in self._attempts
            if (isinstance(a, dict) and a.get("tenant_id") == clean) or getattr(a, "tenant_id", "") == clean
        )


class InMemoryAnalyticsRepository(AnalyticsRepositoryInterface):
    def __init__(self):
        self._students: dict[str, StudentAnalyticsRecord] = {}
        self._institutions: dict[str, InstitutionAnalyticsRecord] = {}

    def save_student(self, record: StudentAnalyticsRecord) -> None:
        self._students[record.student_id.strip()] = record

    def save_student_analytics(self, record: StudentAnalyticsRecord) -> None:
        self.save_student(record)

    def get_student(self, student_id: str) -> StudentAnalyticsRecord | None:
        return self._students.get(student_id.strip())

    def get_student_analytics(self, student_id: str) -> StudentAnalyticsRecord | None:
        return self.get_student(student_id)

    def save_institution(self, record: InstitutionAnalyticsRecord) -> None:
        key = f"{record.tenant_id.strip()}:{record.cohort_id.strip()}"
        self._institutions[key] = record

    def save_institution_analytics(self, record: InstitutionAnalyticsRecord) -> None:
        self.save_institution(record)

    def get_institution(self, tenant_id: str, cohort_id: str = "") -> InstitutionAnalyticsRecord | None:
        if cohort_id:
            key = f"{tenant_id.strip()}:{cohort_id.strip()}"
            return self._institutions.get(key)
        for k, v in self._institutions.items():
            if k.startswith(f"{tenant_id.strip()}:"):
                return v
        return None

    def get_institution_analytics(self, tenant_id: str, cohort_id: str = "") -> InstitutionAnalyticsRecord | None:
        return self.get_institution(tenant_id, cohort_id)


class InMemoryAIUsageRepository(AIUsageRepositoryInterface):
    def __init__(self):
        self._records: list[AIUsageRecord] = []

    def record(self, record: AIUsageRecord) -> None:
        self.save(record)

    def save(self, record: AIUsageRecord) -> None:
        self._records.append(record)

    def list_by_tenant(self, tenant_id: str) -> tuple[AIUsageRecord, ...]:
        clean = tenant_id.strip()
        return tuple(r for r in self._records if r.tenant_id == clean)

    def list_by_user(self, user_id: str) -> tuple[AIUsageRecord, ...]:
        clean = user_id.strip()
        return tuple(r for r in self._records if r.user_id == clean)


class InMemoryAuditRepository(AuditRepositoryInterface):
    def __init__(self):
        self._events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self.save(event)

    def save(self, event: AuditEvent) -> None:
        self._events.append(event)

    def list_by_tenant(self, tenant_id: str) -> tuple[AuditEvent, ...]:
        clean = tenant_id.strip()
        return tuple(e for e in self._events if e.tenant_id == clean)

    def list_by_actor(self, actor_id: str) -> tuple[AuditEvent, ...]:
        clean = actor_id.strip()
        return tuple(e for e in self._events if e.actor_id == clean)


class DatabaseService:
    """Unified database service bundling all PostgreSQL-ready repositories."""

    def __init__(
        self,
        users: UserRepositoryInterface | None = None,
        tenants: TenantRepositoryInterface | None = None,
        orgs: OrganizationRepositoryInterface | None = None,
        documents: DocumentRepositoryInterface | None = None,
        sessions: SessionRepositoryInterface | None = None,
        attempts: AttemptRepositoryInterface | None = None,
        analytics: AnalyticsRepositoryInterface | None = None,
        usage: AIUsageRepositoryInterface | None = None,
        audit: AuditRepositoryInterface | None = None,
    ):
        self.users = users or InMemoryUserRepository()
        self.tenants = tenants or InMemoryTenantRepository()
        self.orgs = orgs or InMemoryOrganizationRepository()
        self.organizations = self.orgs  # alias for clarity
        self.documents = documents or InMemoryDocumentRepository()
        self.sessions = sessions or InMemorySessionRepository()
        self.attempts = attempts or InMemoryAttemptRepository()
        self.analytics = analytics or InMemoryAnalyticsRepository()
        self.usage = usage or InMemoryAIUsageRepository()
        self.audit = audit or InMemoryAuditRepository()
