import unittest
from medicalplab.stage_b.models import ContractError
from medicalplab.stage_e.models import (
    ConfidenceLevel,
    KnowledgeGap,
    LearningRecommendation,
    LearningReport,
    MasteryLevel,
    QuestionAttempt,
    QuestionDifficulty,
    RecommendationPriority,
    StudentProfile,
    TopicMastery,
)


class TestStageEModels(unittest.TestCase):

    def setUp(self):
        self.attempt = QuestionAttempt(
            attempt_id="ATT-001",
            student_id="STU-001",
            question_id="Q-001",
            topic="Hypertension",
            correct=True,
            timestamp=1700000000.0,
            difficulty="medium",
        )
        self.mastery = TopicMastery(
            topic="Hypertension",
            total_attempts=10,
            correct_attempts=8,
            accuracy=0.80,
            mastery_level=MasteryLevel.PROFICIENT,
            confidence_level=ConfidenceLevel.MEDIUM,
        )
        self.gap = KnowledgeGap(
            topic="Cardiology",
            gap_score=0.45,
            reason="Low accuracy across recent attempts",
        )
        self.rec = LearningRecommendation(
            topic="Hypertension",
            priority=RecommendationPriority.HIGH,
            reason="Low accuracy in diagnostic thresholds",
            recommended_action="Review WHO criteria in Stage-D Teaching mode",
            target_difficulty="easy",
        )
        self.profile = StudentProfile(
            student_id="STU-001",
            created_at=1700000000.0,
            topics=("Hypertension",),
            mastery_scores=(self.mastery,),
            weak_topics=(),
            learning_level=MasteryLevel.PROFICIENT,
        )

    def test_question_attempt_valid_and_frozen(self):
        self.assertEqual(self.attempt.attempt_id, "ATT-001")
        self.assertTrue(self.attempt.correct)
        with self.assertRaises(Exception):
            self.attempt.correct = False

    def test_question_attempt_invalid_difficulty_rejected(self):
        with self.assertRaises(ContractError):
            QuestionAttempt(
                attempt_id="ATT-002",
                student_id="STU-001",
                question_id="Q-002",
                topic="Hypertension",
                correct=True,
                timestamp=100.0,
                difficulty="impossible",  # Invalid difficulty
            )

    def test_topic_mastery_correct_exceeding_total_rejected(self):
        with self.assertRaises(ContractError):
            TopicMastery(
                topic="Hypertension",
                total_attempts=5,
                correct_attempts=6,  # > total_attempts
                accuracy=1.0,
                mastery_level=MasteryLevel.PROFICIENT,
                confidence_level=ConfidenceLevel.LOW,
            )

    def test_topic_mastery_invalid_accuracy_rejected(self):
        with self.assertRaises(ContractError):
            TopicMastery(
                topic="Hypertension",
                total_attempts=10,
                correct_attempts=5,
                accuracy=1.5,  # > 1.0
                mastery_level=MasteryLevel.DEVELOPING,
                confidence_level=ConfidenceLevel.MEDIUM,
            )

    def test_topic_mastery_enum_enforcement(self):
        with self.assertRaises(ContractError):
            TopicMastery(
                topic="Hypertension",
                total_attempts=10,
                correct_attempts=8,
                accuracy=0.80,
                mastery_level="proficient",  # Must be MasteryLevel enum
                confidence_level=ConfidenceLevel.MEDIUM,
            )

    def test_knowledge_gap_bounds(self):
        with self.assertRaises(ContractError):
            KnowledgeGap(
                topic="Hypertension",
                gap_score=-0.1,  # < 0.0
                reason="Invalid",
            )

    def test_recommendation_priority_enum_enforcement(self):
        with self.assertRaises(ContractError):
            LearningRecommendation(
                topic="Hypertension",
                priority="high",  # Must be RecommendationPriority enum
                reason="Reason",
                recommended_action="Action",
            )

    def test_student_profile_immutability(self):
        with self.assertRaises(Exception):
            self.profile.learning_level = MasteryLevel.ADVANCED

    def test_learning_report_valid(self):
        report = LearningReport(
            student_profile=self.profile,
            knowledge_gaps=(self.gap,),
            recommendations=(self.rec,),
            next_learning_actions=("[HIGH] Review WHO criteria",),
            generated_at=1700000000.0,
        )
        self.assertEqual(report.student_profile.student_id, "STU-001")
        self.assertEqual(len(report.knowledge_gaps), 1)
        self.assertEqual(len(report.recommendations), 1)
        self.assertEqual(len(report.next_learning_actions), 1)


if __name__ == "__main__":
    unittest.main()
