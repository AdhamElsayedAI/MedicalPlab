"""Unit tests for Stage-G security, RBAC, and quota enforcement."""

import unittest

from medicalplab.stage_b.models import ContractError
from medicalplab.stage_g.models import SubscriptionTier, UserRecord, UserRole
from medicalplab.stage_g.security import (
    PERM_AI_ASSIST,
    PERM_ANALYTICS_VIEW,
    PERM_CONTENT_REVIEW,
    PERM_DOC_MANAGE,
    PERM_LEARNING_READ,
    PERM_USER_MANAGE,
    SecurityService,
)


class TestStageGSecurity(unittest.TestCase):
    """Test suite for role-based access control and quota enforcement."""

    def setUp(self):
        self.sec = SecurityService()

        self.student = UserRecord(
            user_id="stu_1",
            tenant_id="ten_a",
            email="student@plab.org",
            name="Alice",
            role=UserRole.STUDENT,
            tier=SubscriptionTier.FREE,
        )

        self.doctor = UserRecord(
            user_id="doc_1",
            tenant_id="ten_a",
            email="doctor@plab.org",
            name="Dr. Bob",
            role=UserRole.DOCTOR,
            tier=SubscriptionTier.PREMIUM,
        )

        self.admin = UserRecord(
            user_id="adm_1",
            tenant_id="ten_a",
            email="admin@plab.org",
            name="Carol Admin",
            role=UserRole.INSTITUTION_ADMIN,
            tier=SubscriptionTier.INSTITUTION,
        )

    def test_student_permissions(self):
        """Student can read learning data and request AI assist, but not manage org or docs."""
        self.assertTrue(self.sec.has_permission(self.student.role, PERM_LEARNING_READ))
        self.assertTrue(self.sec.has_permission(self.student.role, PERM_AI_ASSIST))

        self.assertFalse(self.sec.has_permission(self.student.role, PERM_CONTENT_REVIEW))
        self.assertFalse(self.sec.has_permission(self.student.role, PERM_USER_MANAGE))
        self.assertFalse(self.sec.has_permission(self.student.role, PERM_ANALYTICS_VIEW))
        self.assertFalse(self.sec.has_permission(self.student.role, PERM_DOC_MANAGE))

    def test_doctor_permissions(self):
        """Doctor can review educational content and access professional AI features."""
        self.assertTrue(self.sec.has_permission(self.doctor.role, PERM_LEARNING_READ))
        self.assertTrue(self.sec.has_permission(self.doctor.role, PERM_AI_ASSIST))
        self.assertTrue(self.sec.has_permission(self.doctor.role, PERM_CONTENT_REVIEW))

        self.assertFalse(self.sec.has_permission(self.doctor.role, PERM_USER_MANAGE))
        self.assertFalse(self.sec.has_permission(self.doctor.role, PERM_DOC_MANAGE))

    def test_admin_permissions(self):
        """Institution Admin has full management privileges."""
        self.assertTrue(self.sec.has_permission(self.admin.role, PERM_LEARNING_READ))
        self.assertTrue(self.sec.has_permission(self.admin.role, PERM_AI_ASSIST))
        self.assertTrue(self.sec.has_permission(self.admin.role, PERM_CONTENT_REVIEW))
        self.assertTrue(self.sec.has_permission(self.admin.role, PERM_USER_MANAGE))
        self.assertTrue(self.sec.has_permission(self.admin.role, PERM_ANALYTICS_VIEW))
        self.assertTrue(self.sec.has_permission(self.admin.role, PERM_DOC_MANAGE))

    def test_quota_limits(self):
        """Verify tier-based quota checks."""
        # FREE Tier: 20 requests
        self.assertTrue(self.sec.check_quota(SubscriptionTier.FREE, 0))
        self.assertTrue(self.sec.check_quota(SubscriptionTier.FREE, 19))
        self.assertFalse(self.sec.check_quota(SubscriptionTier.FREE, 20))
        self.assertFalse(self.sec.check_quota(SubscriptionTier.FREE, 21))

        # PREMIUM Tier: 500 requests
        self.assertTrue(self.sec.check_quota(SubscriptionTier.PREMIUM, 499))
        self.assertFalse(self.sec.check_quota(SubscriptionTier.PREMIUM, 500))

        # INSTITUTION Tier: 10,000 requests
        self.assertTrue(self.sec.check_quota(SubscriptionTier.INSTITUTION, 9999))
        self.assertFalse(self.sec.check_quota(SubscriptionTier.INSTITUTION, 10000))

    def test_tenant_boundary_validation(self):
        """Verify cross-tenant boundary validation."""
        # Same tenant passes
        self.assertTrue(self.sec.validate_tenant_access(self.student.tenant_id, "ten_a"))

        # Different tenant fails
        self.assertFalse(self.sec.validate_tenant_access(self.student.tenant_id, "ten_b"))

        # Enforce check raises ContractError on mismatch
        self.sec.enforce_tenant_access(self.student.tenant_id, "ten_a")
        with self.assertRaises(ContractError):
            self.sec.enforce_tenant_access(self.student.tenant_id, "ten_b")


if __name__ == "__main__":
    unittest.main()
