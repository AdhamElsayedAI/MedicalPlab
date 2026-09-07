import unittest
from medicalplab.stage_f.models import (
    PlatformDifficulty,
    PlatformIntent,
    SessionContext,
)
from medicalplab.stage_f.session import SessionIntelligenceManager


class TestStageFSession(unittest.TestCase):

    def setUp(self):
        self.mgr = SessionIntelligenceManager()

    def test_create_and_retrieve_session(self):
        ctx = self.mgr.create_session(
            student_id="STU-001",
            topic="Hypertension",
            objective="Master Guidelines",
            difficulty=PlatformDifficulty.MEDIUM,
        )
        self.assertIsInstance(ctx, SessionContext)
        self.assertEqual(ctx.student_id, "STU-001")
        self.assertEqual(ctx.current_topic, "Hypertension")
        self.assertEqual(ctx.interactions_count, 0)

        retrieved = self.mgr.get_session(ctx.session_id)
        self.assertEqual(retrieved, ctx)

    def test_record_interaction_and_history(self):
        ctx = self.mgr.create_session("STU-001")
        updated = self.mgr.record_interaction(
            session_id=ctx.session_id,
            intent=PlatformIntent.TEACHING,
            query="Teach me hypertension",
            response_summary="Hypertension is defined as BP > 140/90",
            topic_update="Hypertension",
        )
        self.assertEqual(updated.interactions_count, 1)
        self.assertEqual(updated.current_topic, "Hypertension")

        history = self.mgr.get_history(ctx.session_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["intent"], "teaching")
        self.assertIn("Teach me hypertension", history[0]["query"])

    def test_update_difficulty(self):
        ctx = self.mgr.create_session("STU-001", difficulty=PlatformDifficulty.EASY)
        updated = self.mgr.update_difficulty(ctx.session_id, PlatformDifficulty.HARD)
        self.assertEqual(updated.difficulty_context, PlatformDifficulty.HARD)


if __name__ == "__main__":
    unittest.main()
