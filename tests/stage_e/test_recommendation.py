import unittest
from medicalplab.stage_e.models import (
    ConfidenceLevel,
    KnowledgeGap,
    MasteryLevel,
    RecommendationPriority,
    StudentProfile,
    TopicMastery,
)
from medicalplab.stage_e.recommendation import (
    compile_next_learning_actions,
    generate_recommendations,
)


class TestStageERecommendation(unittest.TestCase):

    def setUp(self):
        # Hypertension: Weak (1/4 = 0.25) -> in KnowledgeGap
        self.m_hyper = TopicMastery(
            topic="Hypertension Management",
            total_attempts=4,
            correct_attempts=1,
            accuracy=0.25,
            mastery_level=MasteryLevel.BEGINNER,
            confidence_level=ConfidenceLevel.LOW,
        )
        # Asthma: Developing (6/10 = 0.60)
        self.m_asthma = TopicMastery(
            topic="Asthma",
            total_attempts=10,
            correct_attempts=6,
            accuracy=0.60,
            mastery_level=MasteryLevel.DEVELOPING,
            confidence_level=ConfidenceLevel.MEDIUM,
        )
        # Diabetes: Proficient (9/10 = 0.90)
        self.m_diab = TopicMastery(
            topic="Diabetes Mellitus",
            total_attempts=10,
            correct_attempts=9,
            accuracy=0.90,
            mastery_level=MasteryLevel.ADVANCED,
            confidence_level=ConfidenceLevel.MEDIUM,
        )

        self.profile = StudentProfile(
            student_id="STU-001",
            created_at=1000.0,
            topics=("Hypertension Management", "Asthma", "Diabetes Mellitus"),
            mastery_scores=(self.m_hyper, self.m_asthma, self.m_diab),
            weak_topics=("Hypertension Management",),
            learning_level=MasteryLevel.DEVELOPING,
        )

        self.gap = KnowledgeGap(
            topic="Hypertension Management",
            gap_score=0.75,
            reason="The student answered 75% of Hypertension Management questions incorrectly (3/4 attempts).",
        )

    def test_generate_recommendations_priorities_and_explainability(self):
        recs = generate_recommendations(self.profile, [self.gap])

        self.assertEqual(len(recs), 3)

        # 1. First rec must be HIGH priority (addressing the gap)
        rec_high = recs[0]
        self.assertEqual(rec_high.topic, "Hypertension Management")
        self.assertEqual(rec_high.priority, RecommendationPriority.HIGH)
        self.assertEqual(rec_high.target_difficulty, "easy")  # accuracy 0.25 < 0.40 -> easy
        self.assertIn("75% of Hypertension Management questions incorrectly", rec_high.reason)
        # Knowledge graph check: Hypertension Management has prerequisites
        self.assertIn("Ensure core foundational grasp of", rec_high.recommended_action)

        # 2. Second rec must be MEDIUM priority (Asthma)
        rec_med = recs[1]
        self.assertEqual(rec_med.topic, "Asthma")
        self.assertEqual(rec_med.priority, RecommendationPriority.MEDIUM)
        self.assertIn("developing competency in Asthma with 60% accuracy", rec_med.reason)

        # 3. Third rec must be LOW priority (Diabetes Mellitus)
        rec_low = recs[2]
        self.assertEqual(rec_low.topic, "Diabetes Mellitus")
        self.assertEqual(rec_low.priority, RecommendationPriority.LOW)
        self.assertEqual(rec_low.target_difficulty, "hard")
        self.assertIn("strong proficiency in Diabetes Mellitus (90% accuracy", rec_low.reason)
        # Knowledge graph check: includes related topics
        self.assertIn("Consider progressing to related topics", rec_low.recommended_action)

    def test_compile_next_learning_actions(self):
        recs = generate_recommendations(self.profile, [self.gap])
        actions = compile_next_learning_actions(recs, max_actions=2)

        self.assertEqual(len(actions), 2)
        self.assertTrue(actions[0].startswith("[HIGH]"))
        self.assertTrue(actions[1].startswith("[MEDIUM]"))


if __name__ == "__main__":
    unittest.main()
