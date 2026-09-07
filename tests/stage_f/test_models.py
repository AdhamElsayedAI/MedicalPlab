import unittest
from medicalplab.stage_b.models import ContractError
from medicalplab.stage_f.models import (
    CaseSimulationResult,
    CaseSimulationStep,
    ExamAnalytics,
    ExamConfig,
    ExamMode,
    ExamQuestion,
    ExamSubmission,
    GoalStatus,
    LearningLoopCycle,
    PersonalizedStudyPlan,
    PlatformDifficulty,
    PlatformIntent,
    PlatformResponse,
    SessionContext,
    StudyMilestone,
    UserGoal,
)


class TestStageFModels(unittest.TestCase):

    def test_user_goal_valid_and_frozen(self):
        goal = UserGoal(
            goal_id="G1",
            student_id="S1",
            target_topic="Hypertension",
            target_mastery="proficient",
            target_accuracy=0.85,
            status=GoalStatus.IN_PROGRESS,
        )
        self.assertEqual(goal.target_topic, "Hypertension")
        self.assertEqual(goal.status, GoalStatus.IN_PROGRESS)
        with self.assertRaises(Exception):
            goal.status = GoalStatus.ACHIEVED

    def test_user_goal_accuracy_bounds(self):
        with self.assertRaises(ContractError):
            UserGoal(
                goal_id="G1",
                student_id="S1",
                target_topic="Hypertension",
                target_mastery="proficient",
                target_accuracy=1.5,  # > 1.0
            )

    def test_session_context_immutability(self):
        ctx = SessionContext(
            session_id="SES-001",
            student_id="S1",
            current_topic="Cardiology",
            learning_objective="Pass PLAB",
            difficulty_context=PlatformDifficulty.MEDIUM,
            interactions_count=3,
            created_at=100.0,
            last_active_at=150.0,
        )
        self.assertEqual(ctx.interactions_count, 3)
        with self.assertRaises(Exception):
            ctx.interactions_count = 4

    def test_exam_config_invariants(self):
        with self.assertRaises(ContractError):
            ExamConfig(
                exam_id="E1",
                student_id="S1",
                mode=ExamMode.PRACTICE,
                topic="Cardiology",
                question_count=0,  # Must be >= 1
                time_limit_minutes=30,
            )

    def test_exam_question_options_requirement(self):
        with self.assertRaises(ContractError):
            ExamQuestion(
                question_id="Q1",
                topic="Cardiology",
                question="What is hypertension?",
                options=("A. BP > 140/90",),  # Only 1 option (< 2)
                correct_answer="A",
                explanation="Explanation",
                difficulty=PlatformDifficulty.EASY,
            )

    def test_platform_response_valid(self):
        resp = PlatformResponse(
            intent=PlatformIntent.TEACHING,
            session_id="SES-001",
            payload=(("key", "val"),),
            explanation="Explanation",
            next_actions=("Action 1",),
        )
        self.assertEqual(resp.intent, PlatformIntent.TEACHING)
        self.assertEqual(len(resp.next_actions), 1)


if __name__ == "__main__":
    unittest.main()
