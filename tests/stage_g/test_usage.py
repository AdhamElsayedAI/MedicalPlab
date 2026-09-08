"""Unit tests for Stage-G AI usage and cost accounting."""

import unittest

from medicalplab.stage_g.database import DatabaseService
from medicalplab.stage_g.usage import AIUsageTracker


class TestStageGUsage(unittest.TestCase):
    """Test suite for AI usage tracking and token/cost analytics."""

    def setUp(self):
        self.db = DatabaseService()
        self.tracker = AIUsageTracker(self.db)

    def test_record_usage_and_cost_calculation(self):
        """Record usage and verify deterministic token pricing calculation."""
        # 1000 input tokens at $0.0015/1k = $0.0015
        # 2000 output tokens at $0.0020/1k = $0.0040
        # Total cost = $0.0055
        rec = self.tracker.record_usage(
            tenant_id="ten_1",
            user_id="usr_1",
            request_type="teaching",
            stage_used="stage_f",
            latency_ms=150.0,
            success=True,
            input_tokens=1000,
            output_tokens=2000,
            model_name="qwen-2.5-7b-instruct",
        )

        self.assertEqual(rec.input_tokens, 1000)
        self.assertEqual(rec.output_tokens, 2000)
        self.assertAlmostEqual(rec.estimated_cost, 0.0055, places=5)
        self.assertEqual(rec.latency_ms, 150.0)
        self.assertTrue(rec.success)

    def test_user_daily_request_count(self):
        """Verify request counting for quota limits."""
        self.assertEqual(self.tracker.get_user_request_count("usr_1"), 0)

        self.tracker.record_usage(
            tenant_id="ten_1",
            user_id="usr_1",
            request_type="case_simulation",
            stage_used="stage_f",
            latency_ms=100.0,
            success=True,
            input_tokens=50,
            output_tokens=100,
        )
        self.tracker.record_usage(
            tenant_id="ten_1",
            user_id="usr_1",
            request_type="exam",
            stage_used="stage_f",
            latency_ms=80.0,
            success=True,
            input_tokens=40,
            output_tokens=80,
        )

        self.assertEqual(self.tracker.get_user_request_count("usr_1"), 2)
        # Other user has 0
        self.assertEqual(self.tracker.get_user_request_count("usr_2"), 0)

    def test_tenant_aggregated_metrics(self):
        """Verify multi-request aggregated metrics per tenant."""
        self.tracker.record_usage(
            tenant_id="ten_1",
            user_id="usr_1",
            request_type="teaching",
            stage_used="stage_f",
            latency_ms=100.0,
            success=True,
            input_tokens=100,
            output_tokens=100,
        )
        self.tracker.record_usage(
            tenant_id="ten_1",
            user_id="usr_2",
            request_type="exam",
            stage_used="stage_f",
            latency_ms=200.0,
            success=False,
            input_tokens=100,
            output_tokens=0,
        )

        metrics = self.tracker.get_tenant_metrics("ten_1")
        self.assertEqual(metrics["total_requests"], 2)
        self.assertEqual(metrics["total_input_tokens"], 200)
        self.assertEqual(metrics["total_output_tokens"], 100)
        self.assertEqual(metrics["total_tokens"], 300)
        self.assertEqual(metrics["average_latency_ms"], 150.0)
        self.assertEqual(metrics["success_rate"], 0.5)
        self.assertEqual(metrics["requests_by_type"]["teaching"], 1)
        self.assertEqual(metrics["requests_by_type"]["exam"], 1)


if __name__ == "__main__":
    unittest.main()
