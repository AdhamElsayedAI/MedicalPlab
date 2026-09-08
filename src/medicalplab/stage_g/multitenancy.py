"""Multi-tenant domain service for Stage-G.

Enforces tenant hierarchies (Tenant -> Organization -> Membership) and cross-tenant isolation guarantees.
"""

import time
from typing import Sequence
import uuid

from medicalplab.stage_b.models import ContractError, require, strings
from .database import DatabaseService
from .models import (
    DocumentRecord,
    Membership,
    Organization,
    SubscriptionTier,
    Tenant,
    UserRecord,
    UserRole,
)


class MultiTenancyService:
    """Multi-tenant management service ensuring strict data isolation."""

    def __init__(self, db: DatabaseService):
        self.db = db

    def create_tenant(
        self,
        name: str,
        tenant_id: str | None = None,
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Tenant:
        """Create and persist a new institutional tenant."""
        strings(name)
        tid = tenant_id.strip() if tenant_id else f"ten_{uuid.uuid4().hex[:8]}"
        tenant = Tenant(
            tenant_id=tid,
            name=name.strip(),
            tier=tier,
            created_at=time.time(),
            is_active=True,
        )
        self.db.tenants.save(tenant)
        return tenant

    def create_organization(
        self,
        tenant_id: str,
        name: str,
        org_id: str | None = None,
    ) -> Organization:
        """Create an organization unit nested inside an active tenant."""
        strings(tenant_id, name)
        tenant = self.db.tenants.get_by_id(tenant_id.strip())
        require(tenant is not None, f"Tenant '{tenant_id}' does not exist")
        require(tenant.is_active, f"Tenant '{tenant_id}' is inactive")

        oid = org_id.strip() if org_id else f"org_{uuid.uuid4().hex[:8]}"
        org = Organization(
            org_id=oid,
            tenant_id=tenant_id.strip(),
            name=name.strip(),
            created_at=time.time(),
            is_active=True,
        )
        self.db.orgs.save(org)
        return org

    def list_organizations(self, tenant_id: str) -> tuple[Organization, ...]:
        """List all organizations belonging strictly to a tenant."""
        return self.db.orgs.list_by_tenant(tenant_id.strip())

    def assign_membership(
        self,
        user_id: str,
        org_id: str,
        tenant_id: str,
        role: str = "MEMBER",
        membership_id: str | None = None,
    ) -> Membership:
        """Associate a user with a tenant and organization, enforcing zero cross-tenant leakage."""
        strings(user_id, tenant_id, org_id, str(role))
        tenant = self.db.tenants.get_by_id(tenant_id.strip())
        require(tenant is not None, f"Tenant '{tenant_id}' does not exist")

        org = self.db.orgs.get_by_id(org_id.strip())
        require(org is not None, f"Organization '{org_id}' does not exist")
        require(
            org.tenant_id == tenant.tenant_id,
            f"Organization '{org_id}' does not belong to tenant '{tenant_id}'",
        )

        user = self.db.users.get_by_id(user_id.strip())
        require(user is not None, f"User '{user_id}' does not exist")
        require(
            user.tenant_id == tenant.tenant_id,
            f"User '{user_id}' belongs to tenant '{user.tenant_id}', not '{tenant_id}'",
        )

        mid = membership_id.strip() if membership_id else f"mem_{uuid.uuid4().hex[:8]}"
        membership = Membership(
            membership_id=mid,
            user_id=user_id.strip(),
            tenant_id=tenant_id.strip(),
            org_id=org_id.strip(),
            role=role,
            created_at=time.time(),
        )
        self.db.orgs.create_membership(membership)
        return membership

    def add_membership(
        self,
        membership_id: str,
        user_id: str,
        tenant_id: str,
        org_id: str,
        role: str = "MEMBER",
    ) -> Membership:
        """Alias for assign_membership with membership_id positional."""
        return self.assign_membership(
            user_id=user_id,
            org_id=org_id,
            tenant_id=tenant_id,
            role=role,
            membership_id=membership_id,
        )

    def list_organization_members(self, org_id: str, tenant_id: str) -> tuple[Membership, ...]:
        """List memberships in an organization, enforcing tenant boundary."""
        org = self.db.orgs.get_by_id(org_id.strip())
        require(org is not None, f"Organization '{org_id}' does not exist")
        require(
            org.tenant_id == tenant_id.strip(),
            f"Tenant boundary violation: Org '{org_id}' does not belong to tenant '{tenant_id}'",
        )
        return self.db.orgs.list_memberships_by_org(org_id.strip())

    def get_tenant_users(
        self,
        tenant_id: str,
        requesting_user: UserRecord,
    ) -> tuple[UserRecord, ...]:
        """Query users within a tenant with strict tenant isolation."""
        require(
            requesting_user.tenant_id == tenant_id.strip(),
            f"Tenant isolation breach prevented: user from '{requesting_user.tenant_id}' requested '{tenant_id}'",
        )
        return self.db.users.list_by_tenant(tenant_id.strip())

    def get_tenant_documents(
        self,
        tenant_id: str,
        requesting_user: UserRecord,
    ) -> tuple[DocumentRecord, ...]:
        """Query documents within a tenant with strict tenant isolation."""
        require(
            requesting_user.tenant_id == tenant_id.strip(),
            f"Tenant isolation breach prevented: user from '{requesting_user.tenant_id}' requested '{tenant_id}'",
        )
        return self.db.documents.list_by_tenant(tenant_id.strip())
