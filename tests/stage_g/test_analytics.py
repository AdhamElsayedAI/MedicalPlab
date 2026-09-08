"""Unit tests for Stage-G Student and Institution Platform Analytics."""

import unittest

from medicalplab.stage_b.models import ContractError
from medicalplab.stage_g.analytics import PlatformAnalyticsService
from medicalplab.stage_g.database import DatabaseService
from medicalplab.stage_g.models import AIUsageRecord, SubscriptionTier, UserRecord, UserRole


class TestStageGAnalytics(unittest.TestCase):
    """Test suite for analytics calculations and multi-tenant scoping."""

    def setUp(self):
        self.db = DatabaseService()
        self.analytics = PlatformAnalyticsService(self.db)

        # Create students in Tenant 1
        self.user1 = UserRecord(
            user_id="stu_1",
            tenant_id="ten_1",
            email="s1@med.uk",
            name="Student 1",
            role=UserRole.STUDENT,
            tier=SubscriptionTier.FREE,
        )
        self.user2 = UserRecord(
            user_id="stu_2",
            tenant_id="ten_1",
            email="s2@med.uk",
            name="Student 2",
            role=UserRole.STUDENT,
            tier=SubscriptionTier.PREMIUM,
        )
        self.db.users.create(self.user1)
        self.db.users.create(self.user2)

    def test_student_analytics_zero_attempts(self):
        """Student with no history returns clean baseline."""
        stats = self.analytics.compute_student_analytics("stu_1", "ten_1")
        self.assertEqual(stats.total_attempts, 0)
        self.assertEqual(stats.overall_accuracy, 0.0)
        self.assertEqual(stats.mastery_level, "UNRATED")
        self.assertEqual(len(stats.weak_topics), 0)

    def test_student_analytics_with_attempts(self):
        """Record attempts and verify computed accuracy, weak topics, and mastery level."""
        # 3 Cardiology correct
        for _ in range(3):
            self.db.attempts.record({
                "student_id": "stu_1",
                "tenant_id": "ten_1",
                "topic": "Cardiology",
                "is_correct": True,
            })

        # 3 Pharmacology incorrect
        for _ in range(3):
            self.db.attempts.record({
                "student_id": "stu_1",
                "tenant_id": "ten_1",
                "topic": "Pharmacology",
                "is_correct": False,
            })

        stats = self.analytics.compute_student_analytics("stu_1", "ten_1")
        self.assertEqual(stats.total_attempts, 6)
        self.assertAlmostEqual(stats.overall_accuracy, 0.5, places=2)
        self.assertEqual(stats.mastery_level, "DEVELOPING")
        self.assertIn("Pharmacology", stats.weak_topics)
        self.assertNotIn("Cardiology", stats.weak_topics)

    def test_student_analytics_tenant_mismatch(self):
        """Querying student analytics with wrong tenant_id raises ContractError."""
        with self.assertRaises(ContractError):
            self.analytics.compute_student_analytics("stu_1", "ten_other")

    def test_institution_analytics(self):
        """Verify cohort level metrics aggregation."""
        # Add attempts for student 1 (Cardiology 100%)
        self.db.attempts.record({
            "student_id": "stu_1",
            "tenant_id": "ten_1",
            "topic": "Cardiology",
            "is_correct": True,
        })
        # Add attempts for student 2 (Pharmacology 0%)
        self.db.attempts.record({
            "student_id": "stu_2",
            "tenant_id": "ten_1",
            "topic": "Pharmacology",
            "is_correct": False,
        })

        # Add AI usage record
        self.db.usage.record(
            AIUsageRecord(
                record_id="rec_1",
                tenant_id="ten_1",
                user_id="stu_1",
                request_type="teaching",
                stage_used="stage_f",
                model_name="qwen-2.5-7b-instruct",
                input_tokens=10,
                output_tokens=20,
                estimated_cost=0.001,
                latency_ms=50.0,
                success=True,
                timestamp=1700000000.0,
            )
        )

        cohort = self.analytics.compute_institution_analytics("ten_1", cohort_id="cohort_plab1")
        self.assertEqual(cohort.total_students, 2)
        self.assertEqual(cohort.total_ai_requests, 1)
        self.assertAlmostEqual(cohort.cohort_accuracy, 0.5, places=2)
        self.assertIn("Pharmacology", cohort.difficult_topics)


if __name__ == "__main__":
    unittest.main()
