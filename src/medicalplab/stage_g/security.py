"""Role-Based Access Control (RBAC), tenant isolation, and quota enforcement for Stage-G.
"""

from typing import Set

from medicalplab.stage_b.models import ContractError, require
from .models import SubscriptionTier, UserRecord, UserRole


# Permission Identifiers
PERM_AI_ASSIST = "ai:assist"
PERM_LEARNING_READ = "student:learning_data"
PERM_LEARNING_DATA = PERM_LEARNING_READ
PERM_PROFESSIONAL_CASE = "doctor:professional_case"
PERM_CONTENT_REVIEW = "doctor:review_content"
PERM_REVIEW_CONTENT = PERM_CONTENT_REVIEW
PERM_USER_MANAGE = "admin:manage_users"
PERM_MANAGE_USERS = PERM_USER_MANAGE
PERM_ANALYTICS_VIEW = "admin:view_analytics"
PERM_VIEW_INSTITUTION_ANALYTICS = PERM_ANALYTICS_VIEW
PERM_DOC_MANAGE = "admin:manage_documents"
PERM_MANAGE_DOCUMENTS = PERM_DOC_MANAGE

ROLE_PERMISSIONS: dict[UserRole, Set[str]] = {
    UserRole.STUDENT: {
        PERM_AI_ASSIST,
        PERM_LEARNING_READ,
    },
    UserRole.DOCTOR: {
        PERM_AI_ASSIST,
        PERM_LEARNING_READ,
        PERM_PROFESSIONAL_CASE,
        PERM_CONTENT_REVIEW,
    },
    UserRole.INSTITUTION_ADMIN: {
        PERM_AI_ASSIST,
        PERM_LEARNING_READ,
        PERM_PROFESSIONAL_CASE,
        PERM_CONTENT_REVIEW,
        PERM_USER_MANAGE,
        PERM_ANALYTICS_VIEW,
        PERM_DOC_MANAGE,
    },
}

TIER_DAILY_LIMITS: dict[SubscriptionTier, int] = {
    SubscriptionTier.FREE: 20,
    SubscriptionTier.PREMIUM: 500,
    SubscriptionTier.INSTITUTION: 10000,
}

TIER_QUOTAS = TIER_DAILY_LIMITS


class SecurityService:
    """Enterprise security service enforcing RBAC, tenant isolation, and subscription quotas."""

    def has_permission(self, role: UserRole, permission: str) -> bool:
        """Verify if a user role holds the requested permission."""
        perms = ROLE_PERMISSIONS.get(role, set())
        return permission in perms

    def validate_tenant_access(self, tenant_id_a: str, tenant_id_b: str) -> bool:
        """Return True if both tenant IDs match."""
        return tenant_id_a.strip() == tenant_id_b.strip()

    def enforce_tenant_access(self, tenant_id_a: str, tenant_id_b: str) -> None:
        """Raise ContractError if tenant IDs do not match."""
        require(
            self.validate_tenant_access(tenant_id_a, tenant_id_b),
            f"Cross-tenant access forbidden: '{tenant_id_a}' cannot access '{tenant_id_b}'",
        )

    def verify_tenant_access(self, user: UserRecord, target_tenant_id: str) -> None:
        """Prevent cross-tenant data leaks by strictly validating user against target tenant."""
        self.enforce_tenant_access(user.tenant_id, target_tenant_id)

    def check_quota(self, tier: SubscriptionTier, daily_questions_used: int) -> bool:
        """Verify if usage is within subscription plan quotas."""
        limit = TIER_DAILY_LIMITS.get(tier, 20)
        return daily_questions_used < limit

    def enforce_access(
        self,
        user: UserRecord,
        required_permission: str,
        target_tenant_id: str | None = None,
    ) -> None:
        """Validate active user state, tenant isolation, and RBAC permission."""
        require(user.is_active, f"User account '{user.user_id}' is inactive or suspended")

        if target_tenant_id is not None:
            self.verify_tenant_access(user, target_tenant_id)

        require(
            self.has_permission(user.role, required_permission),
            f"Access denied: User role '{user.role.value}' lacks required permission '{required_permission}'",
        )
