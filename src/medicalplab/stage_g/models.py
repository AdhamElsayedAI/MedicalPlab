"""Independent Stage-G data contracts for Productization & Deployment Platform.

All dataclasses are immutable and frozen.
Reuses only generic validation utilities (require, strings, ContractError, normalize).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from medicalplab.stage_b.evidence_policy import normalize
from medicalplab.stage_b.models import (
    ContractError,
    exact_keys,
    require,
    strict_json,
    strings,
)


class UserRole(str, Enum):
    STUDENT = "STUDENT"
    DOCTOR = "DOCTOR"
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN"


class SubscriptionTier(str, Enum):
    FREE = "FREE"
    PREMIUM = "PREMIUM"
    INSTITUTION = "INSTITUTION"


class DocumentStage(str, Enum):
    UPLOAD = "UPLOAD"
    VALIDATION = "VALIDATION"
    EXTRACTION = "EXTRACTION"
    CLEANING = "CLEANING"
    INDEXING = "INDEXING"
    AVAILABLE = "AVAILABLE"
    FAILED = "FAILED"


class AuditEventType(str, Enum):
    LOGIN = "LOGIN"
    AI_REQUEST = "AI_REQUEST"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_UPDATE = "DOCUMENT_UPDATE"
    ADMIN_ACTION = "ADMIN_ACTION"
    PERMISSION_CHANGE = "PERMISSION_CHANGE"


class Environment(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


@dataclass(frozen=True)
class Tenant:
    """Multi-tenant institutional boundary."""

    tenant_id: str
    name: str
    tier: SubscriptionTier = SubscriptionTier.FREE
    created_at: float = 0.0
    is_active: bool = True

    def __post_init__(self):
        strings(self.tenant_id, self.name)
        require(isinstance(self.tier, SubscriptionTier), f"'tier' must be SubscriptionTier enum, got {self.tier}")
        require(isinstance(self.created_at, (int, float)) and self.created_at >= 0, "'created_at' must be >= 0")
        require(isinstance(self.is_active, bool), "'is_active' must be a boolean")


@dataclass(frozen=True)
class Organization:
    """Department, hospital branch, or cohort nested within a Tenant."""

    org_id: str
    tenant_id: str
    name: str
    created_at: float = 0.0
    is_active: bool = True

    def __post_init__(self):
        strings(self.org_id, self.tenant_id, self.name)
        require(isinstance(self.created_at, (int, float)) and self.created_at >= 0, "'created_at' must be >= 0")
        require(isinstance(self.is_active, bool), "'is_active' must be a boolean")


@dataclass(frozen=True)
class Membership:
    """User membership association with a Tenant and Organization."""

    membership_id: str
    user_id: str
    tenant_id: str
    org_id: str
    role: str = "MEMBER"
    created_at: float = 0.0

    def __post_init__(self):
        strings(self.membership_id, self.user_id, self.tenant_id, self.org_id, str(self.role))
        require(isinstance(self.created_at, (int, float)) and self.created_at >= 0, "'created_at' must be >= 0")


@dataclass(frozen=True)
class UserRecord:
    """Primary user identity record."""

    user_id: str
    tenant_id: str
    email: str
    name: str
    role: UserRole
    tier: SubscriptionTier
    created_at: float = 0.0
    is_active: bool = True

    def __post_init__(self):
        strings(self.user_id, self.tenant_id, self.email, self.name)
        require("@" in self.email and "." in self.email, f"Invalid email format: {self.email}")
        require(isinstance(self.role, UserRole), f"'role' must be UserRole enum, got {self.role}")
        require(isinstance(self.tier, SubscriptionTier), f"'tier' must be SubscriptionTier enum, got {self.tier}")
        require(isinstance(self.created_at, (int, float)) and self.created_at >= 0, "'created_at' must be >= 0")
        require(isinstance(self.is_active, bool), "'is_active' must be a boolean")


@dataclass(frozen=True)
class SubscriptionPlan:
    """Subscription quota and feature policy."""

    tier: SubscriptionTier
    name: str = ""
    max_daily_requests: int = 100
    monthly_price_usd: float = 0.0
    tutor_enabled: bool = True
    case_simulation_enabled: bool = True
    cohort_analytics_enabled: bool = False
    plan_id: str = ""

    def __post_init__(self):
        require(isinstance(self.tier, SubscriptionTier), "'tier' must be SubscriptionTier")
        require(isinstance(self.max_daily_requests, int) and self.max_daily_requests >= 0, "'max_daily_requests' must be >= 0")
        require(isinstance(self.monthly_price_usd, (int, float)) and self.monthly_price_usd >= 0, "'monthly_price_usd' must be >= 0")
        require(isinstance(self.tutor_enabled, bool), "'tutor_enabled' must be boolean")
        require(isinstance(self.case_simulation_enabled, bool), "'case_simulation_enabled' must be boolean")
        require(isinstance(self.cohort_analytics_enabled, bool), "'cohort_analytics_enabled' must be boolean")


@dataclass(frozen=True)
class DocumentRecord:
    """Clinical guideline document tracking complete ingestion lifecycle."""

    doc_id: str
    tenant_id: str
    owner_id: str
    title: str
    stage: DocumentStage = DocumentStage.UPLOAD
    version: int = 1
    file_path: str = ""
    file_size_bytes: int = 0
    mime_type: str = "application/pdf"
    status: DocumentStage | None = None
    filename: str = ""
    source: str = "NICE"
    block_count: int = 0
    created_at: float = 0.0
    uploaded_at: float = 0.0
    updated_at: float = 0.0
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self):
        strings(self.doc_id, self.tenant_id, self.owner_id, self.title)
        active_stage = self.status if self.status is not None else self.stage
        require(isinstance(active_stage, DocumentStage), f"'stage' must be DocumentStage enum, got {active_stage}")
        # Keep stage and status in sync
        object.__setattr__(self, "stage", active_stage)
        object.__setattr__(self, "status", active_stage)

        require(isinstance(self.version, int) and self.version >= 1, "'version' must be >= 1")
        require(isinstance(self.file_size_bytes, int) and self.file_size_bytes >= 0, "'file_size_bytes' must be >= 0")
        require(isinstance(self.block_count, int) and self.block_count >= 0, "'block_count' must be >= 0")
        require(isinstance(self.created_at, (int, float)) and self.created_at >= 0, "'created_at' must be >= 0")
        require(isinstance(self.uploaded_at, (int, float)) and self.uploaded_at >= 0, "'uploaded_at' must be >= 0")
        require(isinstance(self.updated_at, (int, float)) and self.updated_at >= 0, "'updated_at' must be >= 0")
        require(isinstance(self.metadata, tuple), "'metadata' must be a tuple")


@dataclass(frozen=True)
class AIUsageRecord:
    """Granular record of AI request execution and cost estimation."""

    record_id: str
    tenant_id: str
    user_id: str
    request_type: str
    stage_used: str
    model_name: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    latency_ms: float
    success: bool
    timestamp: float = 0.0

    def __post_init__(self):
        strings(self.record_id, self.tenant_id, self.user_id, self.request_type, self.stage_used, self.model_name)
        require(isinstance(self.input_tokens, int) and self.input_tokens >= 0, "'input_tokens' must be >= 0")
        require(isinstance(self.output_tokens, int) and self.output_tokens >= 0, "'output_tokens' must be >= 0")
        require(isinstance(self.estimated_cost, (int, float)) and self.estimated_cost >= 0, "'estimated_cost' must be >= 0")
        require(isinstance(self.latency_ms, (int, float)) and self.latency_ms >= 0, "'latency_ms' must be >= 0")
        require(isinstance(self.success, bool), "'success' must be a boolean")
        require(isinstance(self.timestamp, (int, float)) and self.timestamp >= 0, "'timestamp' must be >= 0")


@dataclass(frozen=True)
class AuditEvent:
    """Security and compliance audit event."""

    event_id: str
    tenant_id: str
    actor_id: str
    event_type: AuditEventType
    action: str
    timestamp: float = 0.0
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self):
        strings(self.event_id, self.tenant_id, self.actor_id, self.action)
        require(isinstance(self.event_type, AuditEventType), f"'event_type' must be AuditEventType, got {self.event_type}")
        require(isinstance(self.timestamp, (int, float)) and self.timestamp >= 0, "'timestamp' must be >= 0")
        require(isinstance(self.metadata, tuple), "'metadata' must be a tuple")


@dataclass(frozen=True)
class StudentAnalyticsRecord:
    """Aggregated student learning metrics."""

    student_id: str
    tenant_id: str
    total_attempts: int
    overall_accuracy: float
    mastery_level: str
    weak_topics: tuple[str, ...]
    improvement_rate: float
    updated_at: float = 0.0

    def __post_init__(self):
        strings(self.student_id, self.tenant_id, self.mastery_level)
        require(isinstance(self.total_attempts, int) and self.total_attempts >= 0, "'total_attempts' must be >= 0")
        require(isinstance(self.overall_accuracy, (int, float)) and 0.0 <= self.overall_accuracy <= 1.0, "'overall_accuracy' must be between 0.0 and 1.0")
        require(isinstance(self.weak_topics, tuple), "'weak_topics' must be a tuple")
        require(isinstance(self.improvement_rate, (int, float)), "'improvement_rate' must be numeric")
        require(isinstance(self.updated_at, (int, float)) and self.updated_at >= 0, "'updated_at' must be >= 0")


@dataclass(frozen=True)
class InstitutionAnalyticsRecord:
    """Aggregated institutional cohort metrics."""

    tenant_id: str
    cohort_id: str
    total_students: int
    active_students_7d: int
    cohort_accuracy: float
    difficult_topics: tuple[str, ...]
    total_ai_requests: int
    updated_at: float = 0.0

    def __post_init__(self):
        strings(self.tenant_id, self.cohort_id)
        require(isinstance(self.total_students, int) and self.total_students >= 0, "'total_students' must be >= 0")
        require(isinstance(self.active_students_7d, int) and self.active_students_7d >= 0, "'active_students_7d' must be >= 0")
        require(isinstance(self.cohort_accuracy, (int, float)) and 0.0 <= self.cohort_accuracy <= 1.0, "'cohort_accuracy' must be between 0.0 and 1.0")
        require(isinstance(self.difficult_topics, tuple), "'difficult_topics' must be a tuple")
        require(isinstance(self.total_ai_requests, int) and self.total_ai_requests >= 0, "'total_ai_requests' must be >= 0")
        require(isinstance(self.updated_at, (int, float)) and self.updated_at >= 0, "'updated_at' must be >= 0")


@dataclass(frozen=True)
class APIRequest:
    """HTTP-like request envelope."""

    path: str
    method: str
    headers: tuple[tuple[str, str], ...] = ()
    body: str = ""
    user_id: str | None = None
    tenant_id: str | None = None

    def __post_init__(self):
        strings(self.path, self.method)
        require(isinstance(self.headers, tuple), "'headers' must be a tuple")


@dataclass(frozen=True)
class APIResponse:
    """HTTP-like response envelope."""

    status_code: int
    headers: tuple[tuple[str, str], ...] = ()
    body: str = ""

    def __post_init__(self):
        require(isinstance(self.status_code, int) and 100 <= self.status_code <= 599, "Invalid HTTP status_code")
        require(isinstance(self.headers, tuple), "'headers' must be a tuple")


@dataclass(frozen=True)
class AppConfig:
    """Global deployment configuration."""

    env: Environment
    api_version: str
    db_uri: str
    rate_limit_per_minute: int
    log_level: str = "INFO"

    def __post_init__(self):
        require(isinstance(self.env, Environment), f"'env' must be Environment enum, got {self.env}")
        strings(self.api_version, self.db_uri, self.log_level)
        require(isinstance(self.rate_limit_per_minute, int) and self.rate_limit_per_minute >= 1, "'rate_limit_per_minute' must be >= 1")
