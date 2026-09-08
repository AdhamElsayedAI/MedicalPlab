"""Unit tests for Stage-G multi-tenancy and strict isolation guarantees."""

import unittest

from medicalplab.stage_b.models import ContractError
from medicalplab.stage_g.database import DatabaseService
from medicalplab.stage_g.models import SubscriptionTier, UserRecord, UserRole
from medicalplab.stage_g.multitenancy import MultiTenancyService


class TestStageGMultiTenancy(unittest.TestCase):
    """Test suite for multi-tenancy hierarchies and strict isolation."""

    def setUp(self):
        self.db = DatabaseService()
        self.mt = MultiTenancyService(self.db)

        # Create two distinct tenants
        self.tenant_a = self.mt.create_tenant(name="St. Thomas Hospital Trust")
        self.tenant_b = self.mt.create_tenant(name="Edinburgh Royal Infirmary")

        # Create users in distinct tenants
        self.user_a = UserRecord(
            user_id="usr_a1",
            tenant_id=self.tenant_a.tenant_id,
            email="doc_a@st-thomas.uk",
            name="Dr. Alpha",
            role=UserRole.DOCTOR,
            tier=SubscriptionTier.PREMIUM,
        )
        self.db.users.create(self.user_a)

        self.user_b = UserRecord(
            user_id="usr_b1",
            tenant_id=self.tenant_b.tenant_id,
            email="doc_b@edinburgh.uk",
            name="Dr. Beta",
            role=UserRole.DOCTOR,
            tier=SubscriptionTier.PREMIUM,
        )
        self.db.users.create(self.user_b)

    def test_organization_creation_and_isolation(self):
        """Organizations created under one tenant must not leak to another."""
        org_a = self.mt.create_organization(self.tenant_a.tenant_id, "Acute Medicine")
        org_b = self.mt.create_organization(self.tenant_b.tenant_id, "Cardiothoracic Surgery")

        orgs_a = self.mt.list_organizations(self.tenant_a.tenant_id)
        self.assertEqual(len(orgs_a), 1)
        self.assertEqual(orgs_a[0].name, "Acute Medicine")

        orgs_b = self.mt.list_organizations(self.tenant_b.tenant_id)
        self.assertEqual(len(orgs_b), 1)
        self.assertEqual(orgs_b[0].name, "Cardiothoracic Surgery")

        # Cross-tenant list must not return any foreign organizations
        self.assertNotIn(org_b.org_id, [o.org_id for o in orgs_a])
        self.assertNotIn(org_a.org_id, [o.org_id for o in orgs_b])

    def test_membership_cross_tenant_rejection(self):
        """Assigning a user from Tenant A to an organization in Tenant B must fail."""
        org_b = self.mt.create_organization(self.tenant_b.tenant_id, "Cardiothoracic Surgery")

        # user_a belongs to tenant_a; org_b belongs to tenant_b
        with self.assertRaises(ContractError):
            self.mt.assign_membership(
                user_id=self.user_a.user_id,
                org_id=org_b.org_id,
                tenant_id=self.tenant_a.tenant_id,
            )

        # Even if someone fakes the tenant_id to tenant_b, user_a's actual tenant is tenant_a
        with self.assertRaises(ContractError):
            self.mt.assign_membership(
                user_id=self.user_a.user_id,
                org_id=org_b.org_id,
                tenant_id=self.tenant_b.tenant_id,
            )

    def test_valid_membership_assignment(self):
        """Assigning user within the same tenant succeeds."""
        org_a = self.mt.create_organization(self.tenant_a.tenant_id, "Acute Medicine")
        membership = self.mt.assign_membership(
            user_id=self.user_a.user_id,
            org_id=org_a.org_id,
            tenant_id=self.tenant_a.tenant_id,
            role="LEAD",
        )
        self.assertEqual(membership.role, "LEAD")

        members = self.mt.list_organization_members(org_a.org_id, self.tenant_a.tenant_id)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].user_id, self.user_a.user_id)

    def test_cross_tenant_member_listing_forbidden(self):
        """Attempting to list organization members with wrong tenant_id raises ContractError."""
        org_a = self.mt.create_organization(self.tenant_a.tenant_id, "Acute Medicine")
        with self.assertRaises(ContractError):
            self.mt.list_organization_members(org_a.org_id, self.tenant_b.tenant_id)


if __name__ == "__main__":
    unittest.main()
