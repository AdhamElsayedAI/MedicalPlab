import unittest
from medicalplab.stage_b.models import ContractError
from medicalplab.stage_e.models import (
    ConfidenceLevel,
    MasteryLevel,
    QuestionAttempt,
    StudentProfile,
    TopicMastery,
)
from medicalplab.stage_e.student_profile import (
    calculate_aggregate_learning_level,
    create_initial_profile,
    update_student_profile,
)


class TestStageEStudentProfile(unittest.TestCase):

    def test_create_initial_profile(self):
        prof = create_initial_profile("STU-42", created_at=1000.0)
        self.assertEqual(prof.student_id, "STU-42")
        self.assertEqual(prof.created_at, 1000.0)
        self.assertEqual(prof.topics, ())
        self.assertEqual(prof.mastery_scores, ())
        self.assertEqual(prof.weak_topics, ())
        self.assertEqual(prof.learning_level, MasteryLevel.BEGINNER)

    def test_calculate_aggregate_learning_level(self):
        # Empty masteries
        self.assertEqual(calculate_aggregate_learning_level([]), MasteryLevel.BEGINNER)

        # 16/20 = 0.80 -> PROFICIENT
        m1 = TopicMastery("Hypertension", 10, 8, 0.80, MasteryLevel.PROFICIENT, ConfidenceLevel.MEDIUM)
        m2 = TopicMastery("Diabetes", 10, 8, 0.80, MasteryLevel.PROFICIENT, ConfidenceLevel.MEDIUM)
        self.assertEqual(calculate_aggregate_learning_level([m1, m2]), MasteryLevel.PROFICIENT)

        # 18/20 = 0.90 -> ADVANCED
        m3 = TopicMastery("Cardiology", 10, 9, 0.90, MasteryLevel.ADVANCED, ConfidenceLevel.MEDIUM)
        m4 = TopicMastery("Endocrinology", 10, 9, 0.90, MasteryLevel.ADVANCED, ConfidenceLevel.MEDIUM)
        self.assertEqual(calculate_aggregate_learning_level([m3, m4]), MasteryLevel.ADVANCED)

    def test_update_student_profile_with_attempts(self):
        initial = create_initial_profile("STU-100", created_at=1000.0)
        attempts = [
            QuestionAttempt("A1", "STU-100", "Q1", "Hypertension", True, 100.0),
            QuestionAttempt("A2", "STU-100", "Q2", "Hypertension", False, 101.0),
            QuestionAttempt("A3", "STU-100", "Q3", "Hypertension", False, 102.0),
            QuestionAttempt("A4", "STU-100", "Q4", "Diabetes Mellitus", True, 103.0),
            QuestionAttempt("A5", "STU-100", "Q5", "Diabetes Mellitus", True, 104.0),
        ]

        updated = update_student_profile(initial, attempts, weak_threshold=0.60)

        self.assertEqual(updated.student_id, "STU-100")
        self.assertEqual(len(updated.topics), 2)
        self.assertIn("Hypertension", updated.topics)
        self.assertIn("Diabetes Mellitus", updated.topics)

        # Hypertension (1/3 = 0.33) is below 0.60 -> in weak_topics
        self.assertIn("Hypertension", updated.weak_topics)
        self.assertNotIn("Diabetes Mellitus", updated.weak_topics)

        # Overall level check
        # Total attempts = 5, correct = 3 (60%) -> DEVELOPING
        self.assertEqual(updated.learning_level, MasteryLevel.DEVELOPING)

    def test_update_student_profile_empty_attempts(self):
        initial = create_initial_profile("STU-100", created_at=1000.0)
        updated = update_student_profile(initial, [])
        self.assertEqual(initial, updated)

    def test_update_student_profile_invalid_input(self):
        initial = create_initial_profile("STU-100", created_at=1000.0)
        with self.assertRaises(ContractError):
            update_student_profile(initial, ["not an attempt"])


if __name__ == "__main__":
    unittest.main()
