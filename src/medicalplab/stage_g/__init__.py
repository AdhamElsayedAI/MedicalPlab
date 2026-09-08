"""Stage-G: MedicalPlab Productization & Deployment Platform.

Provides multi-tenant SaaS infrastructure around the MedicalPlab AI Core:
- Tenancy, organization, and membership management with complete tenant isolation
- Database repository abstractions with in-memory reference implementations
- RBAC and subscription tier quota enforcement
- AI gateway with token, latency, and cloud cost accounting
- Medical knowledge document ingestion lifecycle (UPLOAD -> AVAILABLE)
- Student and institutional learning analytics
- Security and compliance audit logging
- Production-style REST API routing (/auth, /ai, /student, /documents, /analytics, /admin)
"""

from .analytics import PlatformAnalyticsService
from .api import PlatformAPIRouter
from .audit import AuditService
from .config import DEFAULT_CONFIGS, load_config
from .database import (
    AIUsageRepository,
    AnalyticsRepository,
    AttemptRepository,
    AuditRepository,
    DatabaseService,
    DocumentRepository,
    InMemoryAIUsageRepository,
    InMemoryAnalyticsRepository,
    InMemoryAttemptRepository,
    InMemoryAuditRepository,
    InMemoryDocumentRepository,
    InMemoryOrganizationRepository,
    InMemorySessionRepository,
    InMemoryTenantRepository,
    InMemoryUserRepository,
    OrganizationRepository,
    SessionRepository,
    TenantRepository,
    UserRepository,
)
from .gateway import AIGateway
from .knowledge_management import MedicalKnowledgeManager
from .logger import StructuredLogger
from .models import (
    AIUsageRecord,
    APIRequest,
    APIResponse,
    AppConfig,
    AuditEvent,
    AuditEventType,
    DocumentRecord,
    DocumentStage,
    Environment,
    InstitutionAnalyticsRecord,
    Membership,
    Organization,
    StudentAnalyticsRecord,
    SubscriptionPlan,
    SubscriptionTier,
    Tenant,
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
    ROLE_PERMISSIONS,
    SecurityService,
    TIER_QUOTAS,
)
from .usage import AIUsageTracker, MODEL_PRICING

__all__ = [
    # Models & Enums
    "UserRole",
    "SubscriptionTier",
    "DocumentStage",
    "AuditEventType",
    "Environment",
    "Tenant",
    "Organization",
    "Membership",
    "UserRecord",
    "SubscriptionPlan",
    "DocumentRecord",
    "AIUsageRecord",
    "AuditEvent",
    "StudentAnalyticsRecord",
    "InstitutionAnalyticsRecord",
    "APIRequest",
    "APIResponse",
    "AppConfig",
    # Config & Logger
    "load_config",
    "DEFAULT_CONFIGS",
    "StructuredLogger",
    # Database
    "UserRepository",
    "TenantRepository",
    "OrganizationRepository",
    "DocumentRepository",
    "SessionRepository",
    "AttemptRepository",
    "AnalyticsRepository",
    "AIUsageRepository",
    "AuditRepository",
    "DatabaseService",
    "InMemoryUserRepository",
    "InMemoryTenantRepository",
    "InMemoryOrganizationRepository",
    "InMemoryDocumentRepository",
    "InMemorySessionRepository",
    "InMemoryAttemptRepository",
    "InMemoryAnalyticsRepository",
    "InMemoryAIUsageRepository",
    "InMemoryAuditRepository",
    # Security
    "SecurityService",
    "ROLE_PERMISSIONS",
    "TIER_QUOTAS",
    "PERM_LEARNING_READ",
    "PERM_AI_ASSIST",
    "PERM_CONTENT_REVIEW",
    "PERM_USER_MANAGE",
    "PERM_ANALYTICS_VIEW",
    "PERM_DOC_MANAGE",
    # Services
    "MultiTenancyService",
    "AIUsageTracker",
    "MODEL_PRICING",
    "AuditService",
    "MedicalKnowledgeManager",
    "PlatformAnalyticsService",
    "AIGateway",
    "PlatformAPIRouter",
]
