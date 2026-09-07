import unittest
from medicalplab.stage_e.models import (
    ConfidenceLevel,
    MasteryLevel,
    QuestionAttempt,
    TopicMastery,
)
from medicalplab.stage_e.performance_tracker import (
    calculate_accuracy,
    calculate_topic_mastery,
    detect_learning_gaps,
    detect_weak_topics,
    determine_confidence_level,
    determine_mastery_level,
)


class TestStageEPerformance(unittest.TestCase):

    def setUp(self):
        self.attempts_cardio = [
            QuestionAttempt("A1", "S1", "Q1", "Hypertension", True, 100.0),
            QuestionAttempt("A2", "S1", "Q2", "Hypertension", False, 101.0),
            QuestionAttempt("A3", "S1", "Q3", "Hypertension", True, 102.0),
            QuestionAttempt("A4", "S1", "Q4", "Hypertension", False, 103.0),
            QuestionAttempt("A5", "S1", "Q5", "Hypertension", False, 104.0),
        ]  # 2/5 = 0.40

        self.attempts_endo = [
            QuestionAttempt("A6", "S1", "Q6", "Diabetes Mellitus", True, 105.0),
            QuestionAttempt("A7", "S1", "Q7", "Diabetes Mellitus", True, 106.0),
            QuestionAttempt("A8", "S1", "Q8", "Diabetes Mellitus", True, 107.0),
            QuestionAttempt("A9", "S1", "Q9", "Diabetes Mellitus", True, 108.0),
            QuestionAttempt("A10", "S1", "Q10", "Diabetes Mellitus", True, 109.0),
        ]  # 5/5 = 1.0

    def test_calculate_accuracy_empty(self):
        self.assertEqual(calculate_accuracy([]), 0.0)

    def test_calculate_accuracy_values(self):
        self.assertEqual(calculate_accuracy(self.attempts_cardio), 0.40)
        self.assertEqual(calculate_accuracy(self.attempts_endo), 1.00)

    def test_determine_mastery_level_boundaries(self):
        # 0 attempts
        self.assertEqual(determine_mastery_level(0.0, 0), MasteryLevel.BEGINNER)
        # Below 0.50
        self.assertEqual(determine_mastery_level(0.49, 10), MasteryLevel.BEGINNER)
        # 0.50 - 0.69
        self.assertEqual(determine_mastery_level(0.50, 10), MasteryLevel.DEVELOPING)
        self.assertEqual(determine_mastery_level(0.69, 10), MasteryLevel.DEVELOPING)
        # 0.70 - 0.84
        self.assertEqual(determine_mastery_level(0.70, 10), MasteryLevel.PROFICIENT)
        self.assertEqual(determine_mastery_level(0.84, 10), MasteryLevel.PROFICIENT)
        # >= 0.85 with low sample count (< 5) stays PROFICIENT
        self.assertEqual(determine_mastery_level(0.90, 3), MasteryLevel.PROFICIENT)
        # >= 0.85 with adequate sample count (>= 5) is ADVANCED
        self.assertEqual(determine_mastery_level(0.85, 5), MasteryLevel.ADVANCED)
        self.assertEqual(determine_mastery_level(1.00, 20), MasteryLevel.ADVANCED)

    def test_determine_confidence_level(self):
        self.assertEqual(determine_confidence_level(2), ConfidenceLevel.LOW)
        self.assertEqual(determine_confidence_level(4), ConfidenceLevel.LOW)
        self.assertEqual(determine_confidence_level(5), ConfidenceLevel.MEDIUM)
        self.assertEqual(determine_confidence_level(14), ConfidenceLevel.MEDIUM)
        self.assertEqual(determine_confidence_level(15), ConfidenceLevel.HIGH)
        self.assertEqual(determine_confidence_level(50), ConfidenceLevel.HIGH)

    def test_calculate_topic_mastery(self):
        mastery = calculate_topic_mastery(self.attempts_cardio, "Hypertension")
        self.assertEqual(mastery.topic, "Hypertension")
        self.assertEqual(mastery.total_attempts, 5)
        self.assertEqual(mastery.correct_attempts, 2)
        self.assertEqual(mastery.accuracy, 0.40)
        self.assertEqual(mastery.mastery_level, MasteryLevel.BEGINNER)
        self.assertEqual(mastery.confidence_level, ConfidenceLevel.MEDIUM)

    def test_calculate_topic_mastery_empty_topic(self):
        mastery = calculate_topic_mastery([], "Nonexistent Topic")
        self.assertEqual(mastery.total_attempts, 0)
        self.assertEqual(mastery.accuracy, 0.0)
        self.assertEqual(mastery.mastery_level, MasteryLevel.BEGINNER)
        self.assertEqual(mastery.confidence_level, ConfidenceLevel.LOW)

    def test_detect_weak_topics(self):
        m1 = TopicMastery("Hypertension", 10, 4, 0.40, MasteryLevel.BEGINNER, ConfidenceLevel.MEDIUM)
        m2 = TopicMastery("Heart Failure", 10, 5, 0.50, MasteryLevel.DEVELOPING, ConfidenceLevel.MEDIUM)
        m3 = TopicMastery("Diabetes", 10, 9, 0.90, MasteryLevel.ADVANCED, ConfidenceLevel.MEDIUM)

        weak = detect_weak_topics([m1, m2, m3], threshold=0.60)
        # Should contain Hypertension and Heart Failure, with Hypertension first (lowest accuracy)
        self.assertEqual(weak, ("Hypertension", "Heart Failure"))

    def test_detect_learning_gaps_explainability(self):
        all_attempts = self.attempts_cardio + self.attempts_endo
        gaps = detect_learning_gaps(all_attempts, min_attempts=1, threshold=0.60)

        self.assertEqual(len(gaps), 1)
        gap = gaps[0]
        self.assertEqual(gap.topic, "Hypertension")
        self.assertEqual(gap.gap_score, 0.60)  # 1.0 - 0.40
        # Check explainable reason text
        self.assertIn("60% of Hypertension questions incorrectly", gap.reason)
        self.assertIn("3/5 attempts", gap.reason)


if __name__ == "__main__":
    unittest.main()
