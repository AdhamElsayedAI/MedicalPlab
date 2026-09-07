import unittest
from medicalplab.stage_f.models import (
    GoalStatus,
    PlatformIntent,
    PlatformResponse,
    UserGoal,
)
from medicalplab.stage_f.orchestrator import MedicalPlabPlatformOrchestrator


class DummyEvidenceBlock:

    def __init__(self, ref: str, text: str):
        self.ref = ref
        self.text = text


class DummyRetrievalPipeline:

    def retrieve(self, query: str, corpus: list, top_k: int = 2):
        return type("Packet", (), {"blocks": (DummyEvidenceBlock("REF-1", "Evidence text"),)})()


class TestStageFOrchestrator(unittest.TestCase):

    def setUp(self):
        self.retrieval = DummyRetrievalPipeline()
        self.orchestrator = MedicalPlabPlatformOrchestrator(
            retrieval_pipeline=self.retrieval,
        )
        self.corpus = [
            DummyEvidenceBlock("WHO-001", "Hypertension guideline criteria and treatment."),
        ]

    def test_orchestrator_teaching_flow(self):
        resp = self.orchestrator.handle_request(
            student_id="STU-001",
            query="Teach me hypertension management",
            corpus=self.corpus,
        )
        self.assertIsInstance(resp, PlatformResponse)
        self.assertEqual(resp.intent, PlatformIntent.TEACHING)
        self.assertTrue(len(resp.next_actions) >= 1)
        self.assertEqual(len(self.orchestrator.trace), 1)

    def test_orchestrator_assessment_flow(self):
        resp = self.orchestrator.handle_request(
            student_id="STU-001",
            query="Quiz me on cardiology with practice questions",
            session_id=None,
        )
        self.assertEqual(resp.intent, PlatformIntent.ASSESSMENT)
        payload_dict = dict(resp.payload)
        self.assertIn("target_difficulty", payload_dict)

    def test_orchestrator_exam_flow(self):
        resp = self.orchestrator.handle_request(
            student_id="STU-001",
            query="Start a timed mock exam on diabetes mellitus",
        )
        self.assertEqual(resp.intent, PlatformIntent.EXAM)
        payload_dict = dict(resp.payload)
        self.assertIn("exam_id", payload_dict)
        self.assertEqual(payload_dict.get("mode"), "exam")

    def test_orchestrator_case_simulation_flow(self):
        resp = self.orchestrator.handle_request(
            student_id="STU-001",
            query="Simulate a patient case presenting with elevated blood pressure",
            corpus=self.corpus,
        )
        self.assertEqual(resp.intent, PlatformIntent.CASE_SIMULATION)
        payload_dict = dict(resp.payload)
        self.assertEqual(payload_dict.get("safety_verified"), "True")

    def test_orchestrator_learning_analysis_flow(self):
        goal = UserGoal(
            goal_id="G1",
            student_id="STU-001",
            target_topic="Hypertension",
            target_mastery="proficient",
            target_accuracy=0.85,
            status=GoalStatus.IN_PROGRESS,
        )
        resp = self.orchestrator.handle_request(
            student_id="STU-001",
            query="Show my learning analysis and progress report",
            user_goal=goal,
        )
        self.assertEqual(resp.intent, PlatformIntent.LEARNING_ANALYSIS)
        payload_dict = dict(resp.payload)
        self.assertIn("plan_id", payload_dict)
        self.assertTrue(len(resp.next_actions) >= 1)


if __name__ == "__main__":
    unittest.main()
