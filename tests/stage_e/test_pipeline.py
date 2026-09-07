import unittest
from medicalplab.stage_b.models import ContractError
from medicalplab.stage_e.models import (
    LearningReport,
    MasteryLevel,
    QuestionAttempt,
    RecommendationPriority,
)
from medicalplab.stage_e.pipeline import StageEPipeline


class TestStageEPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = StageEPipeline(weak_threshold=0.60, min_gap_attempts=1)
        self.attempts = [
            # Cardiology: 1 correct out of 3 = 0.33 (weak)
            QuestionAttempt("A1", "STU-001", "Q1", "Hypertension", True, 100.0, "medium"),
            QuestionAttempt("A2", "STU-001", "Q2", "Hypertension", False, 101.0, "medium"),
            QuestionAttempt("A3", "STU-001", "Q3", "Hypertension", False, 102.0, "medium"),
            # Endocrinology: 4 correct out of 4 = 1.00 (strong)
            QuestionAttempt("A4", "STU-001", "Q4", "Diabetes Mellitus", True, 103.0, "medium"),
            QuestionAttempt("A5", "STU-001", "Q5", "Diabetes Mellitus", True, 104.0, "medium"),
            QuestionAttempt("A6", "STU-001", "Q6", "Diabetes Mellitus", True, 105.0, "medium"),
            QuestionAttempt("A7", "STU-001", "Q7", "Diabetes Mellitus", True, 106.0, "medium"),
        ]

    def test_pipeline_initial_evaluation(self):
        report = self.pipeline.evaluate("STU-001", self.attempts)

        self.assertIsInstance(report, LearningReport)
        self.assertEqual(report.student_profile.student_id, "STU-001")

        # Weak topics
        self.assertIn("Hypertension", report.student_profile.weak_topics)
        self.assertNotIn("Diabetes Mellitus", report.student_profile.weak_topics)

        # Knowledge gaps
        self.assertEqual(len(report.knowledge_gaps), 1)
        self.assertEqual(report.knowledge_gaps[0].topic, "Hypertension")
        self.assertAlmostEqual(report.knowledge_gaps[0].gap_score, 0.6667, places=3)

        # Recommendations
        self.assertTrue(len(report.recommendations) >= 2)
        # First recommendation must be HIGH priority for Hypertension
        self.assertEqual(report.recommendations[0].topic, "Hypertension")
        self.assertEqual(report.recommendations[0].priority, RecommendationPriority.HIGH)
        self.assertIn("Stage-D Teaching mode", report.recommendations[0].recommended_action)

        # Next actions
        self.assertTrue(len(report.next_learning_actions) >= 1)
        self.assertTrue(report.next_learning_actions[0].startswith("[HIGH]"))

        # Trace
        self.assertEqual(len(self.pipeline.trace), 1)
        self.assertEqual(self.pipeline.trace[0]["student_id"], "STU-001")
        self.assertEqual(self.pipeline.trace[0]["total_attempts"], 7)

    def test_pipeline_profile_evolution(self):
        # 1. Initial report
        report1 = self.pipeline.evaluate("STU-001", self.attempts)

        # 2. Student practices more Hypertension and improves (3 correct out of 3)
        follow_up_attempts = [
            QuestionAttempt("A8", "STU-001", "Q8", "Hypertension", True, 110.0, "easy"),
            QuestionAttempt("A9", "STU-001", "Q9", "Hypertension", True, 111.0, "easy"),
            QuestionAttempt("A10", "STU-001", "Q10", "Hypertension", True, 112.0, "easy"),
        ]
        # Combined attempts: 4/6 = 0.667 (> 0.60 threshold)
        combined_attempts = self.attempts + follow_up_attempts

        report2 = self.pipeline.evaluate(
            "STU-001",
            combined_attempts,
            current_profile=report1.student_profile,
        )

        # Hypertension is no longer in weak_topics!
        self.assertNotIn("Hypertension", report2.student_profile.weak_topics)
        self.assertEqual(len(report2.knowledge_gaps), 0)

    def test_pipeline_student_id_mismatch_raises(self):
        report = self.pipeline.evaluate("STU-001", self.attempts)
        with self.assertRaises(ContractError):
            self.pipeline.evaluate(
                "DIFFERENT-STUDENT",
                self.attempts,
                current_profile=report.student_profile,
            )

    def test_pipeline_invalid_configuration_raises(self):
        with self.assertRaises(ContractError):
            StageEPipeline(weak_threshold=1.5)  # Out of range

        with self.assertRaises(ContractError):
            StageEPipeline(min_gap_attempts=0)  # Must be >= 1


if __name__ == "__main__":
    unittest.main()
