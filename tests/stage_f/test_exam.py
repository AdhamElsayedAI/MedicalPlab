import unittest
from medicalplab.stage_f.exam_engine import MedicalExamEngine
from medicalplab.stage_f.models import (
    ExamMode,
    ExamQuestion,
    ExamSubmission,
    PlatformDifficulty,
)


class TestStageFExam(unittest.TestCase):

    def setUp(self):
        self.engine = MedicalExamEngine()
        self.q1 = ExamQuestion(
            question_id="Q1",
            topic="Hypertension",
            question="What is the diagnostic threshold for hypertension?",
            options=("A. 120/80", "B. 130/80", "C. 140/90", "D. 160/100"),
            correct_answer="C",
            explanation="WHO guidelines define hypertension as >= 140/90 mmHg.",
            difficulty=PlatformDifficulty.EASY,
            citations=("WHO Guidelines Sec 1",),
        )
        self.q2 = ExamQuestion(
            question_id="Q2",
            topic="Hypertension",
            question="First-line therapy for essential hypertension in non-black patients?",
            options=("A. Beta blockers", "B. ACE inhibitors", "C. Loop diuretics", "D. Nitrates"),
            correct_answer="B",
            explanation="ACE inhibitors or ARBs are recommended first-line.",
            difficulty=PlatformDifficulty.MEDIUM,
            citations=("WHO Guidelines Sec 2",),
        )
        self.questions = (self.q1, self.q2)

    def test_exam_grading_and_pass_fail(self):
        config = self.engine.create_exam_config(
            student_id="STU-001",
            topic="Hypertension",
            question_count=2,
            mode=ExamMode.EXAM,
            pass_percentage=0.70,
        )

        # 1 correct out of 2 = 50% (Failed)
        submission_fail = ExamSubmission(
            exam_id=config.exam_id,
            student_id="STU-001",
            answers=(("Q1", "C"), ("Q2", "A")),  # Q2 wrong
            time_taken_seconds=300.0,
        )
        analytics_fail = self.engine.grade_submission(config, self.questions, submission_fail)
        self.assertEqual(analytics_fail.score, 1)
        self.assertEqual(analytics_fail.percentage, 0.50)
        self.assertFalse(analytics_fail.passed)

        # 2 correct out of 2 = 100% (Passed)
        submission_pass = ExamSubmission(
            exam_id=config.exam_id,
            student_id="STU-001",
            answers=(("Q1", "C"), ("Q2", "B")),  # Both correct
            time_taken_seconds=250.0,
        )
        analytics_pass = self.engine.grade_submission(config, self.questions, submission_pass)
        self.assertEqual(analytics_pass.score, 2)
        self.assertEqual(analytics_pass.percentage, 1.00)
        self.assertTrue(analytics_pass.passed)

    def test_exam_analytics_feed_stage_e_format(self):
        config = self.engine.create_exam_config(
            student_id="STU-001",
            topic="Hypertension",
            question_count=2,
            mode=ExamMode.PRACTICE,
        )
        submission = ExamSubmission(
            exam_id=config.exam_id,
            student_id="STU-001",
            answers=(("Q1", "C"), ("Q2", "B")),
            time_taken_seconds=120.0,
        )
        analytics = self.engine.grade_submission(config, self.questions, submission)

        # Verify attempt_records format for feeding Stage-E
        self.assertEqual(len(analytics.attempt_records), 2)
        att1 = analytics.attempt_records[0]
        # Tuple format: (attempt_id, question_id, topic, is_correct, difficulty)
        self.assertTrue(att1[0].startswith("ATT-"))
        self.assertEqual(att1[1], "Q1")
        self.assertEqual(att1[2], "Hypertension")
        self.assertTrue(att1[3])  # True
        self.assertEqual(att1[4], "easy")

    def test_exam_review_breakdown(self):
        config = self.engine.create_exam_config(
            student_id="STU-001",
            topic="Hypertension",
            question_count=2,
            mode=ExamMode.REVIEW,
        )
        submission = ExamSubmission(
            exam_id=config.exam_id,
            student_id="STU-001",
            answers=(("Q1", "C"), ("Q2", "A")),
            time_taken_seconds=100.0,
        )
        analytics = self.engine.grade_submission(config, self.questions, submission)
        review = self.engine.generate_review_breakdown(self.questions, analytics)

        self.assertEqual(review["score"], "1/2")
        self.assertEqual(len(review["review_items"]), 2)
        self.assertIn("WHO Guidelines", review["review_items"][0]["citations"][0])


if __name__ == "__main__":
    unittest.main()
