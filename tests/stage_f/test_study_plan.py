import unittest
from medicalplab.stage_f.learning_loop import LearningLoopManager
from medicalplab.stage_f.models import (
    GoalStatus,
    PersonalizedStudyPlan,
    PlatformDifficulty,
    UserGoal,
)
from medicalplab.stage_f.study_planner import LearningPathGenerator


class DummyGap:

    def __init__(self, topic: str, reason: str):
        self.topic = topic
        self.reason = reason


class DummyProfile:

    def __init__(self, learning_level: str):
        self.learning_level = learning_level


class DummyReport:

    def __init__(self, level: str, gaps: list[DummyGap]):
        self.student_profile = DummyProfile(level)
        self.knowledge_gaps = tuple(gaps)
        self.recommendations = ()


class TestStageFStudyPlan(unittest.TestCase):

    def setUp(self):
        self.planner = LearningPathGenerator()
        self.loop = LearningLoopManager()

    def test_generate_study_plan_with_gaps_and_goal(self):
        report = DummyReport(
            level="developing",
            gaps=[DummyGap("Hypertension", "Low accuracy 40%")],
        )
        goal = UserGoal(
            goal_id="G1",
            student_id="STU-001",
            target_topic="Hypertension Management",
            target_mastery="proficient",
            target_accuracy=0.85,
            status=GoalStatus.IN_PROGRESS,
        )

        plan = self.planner.generate_study_plan("STU-001", report, user_goal=goal)

        self.assertIsInstance(plan, PersonalizedStudyPlan)
        self.assertEqual(plan.student_id, "STU-001")
        self.assertTrue(len(plan.milestones) >= 2)

        # Milestone 1: Remediation
        m1 = plan.milestones[0]
        self.assertEqual(m1.topic, "Hypertension")
        self.assertEqual(m1.priority, "HIGH")

        # Milestone 2: User Goal
        m2 = plan.milestones[1]
        self.assertEqual(m2.topic, "Hypertension Management")
        self.assertIn("85%", m2.objective)

    def test_learning_loop_cycle_improvement(self):
        cycle_id = self.loop.start_cycle("STU-001", "Hypertension", "beginner")
        cycle = self.loop.complete_cycle(
            cycle_id=cycle_id,
            interventions=["Completed Stage-D Tutorial", "Practiced 10 MCQs"],
            resulting_mastery="developing",
        )
        self.assertTrue(cycle.mastery_improved)
        advice = self.loop.recommend_next_step(cycle)
        self.assertIn("Advance to higher-difficulty", advice)

    def test_learning_loop_cycle_no_improvement(self):
        cycle_id = self.loop.start_cycle("STU-001", "Asthma", "developing")
        cycle = self.loop.complete_cycle(
            cycle_id=cycle_id,
            interventions=["Practiced 5 MCQs"],
            resulting_mastery="developing",
        )
        self.assertFalse(cycle.mastery_improved)
        advice = self.loop.recommend_next_step(cycle)
        self.assertIn("Switch intervention strategy", advice)


if __name__ == "__main__":
    unittest.main()
