import unittest
from medicalplab.stage_f.models import PlatformIntent
from medicalplab.stage_f.router import IntelligenceRouter


class TestStageFRouter(unittest.TestCase):

    def setUp(self):
        self.router = IntelligenceRouter()

    def test_classify_all_platform_intents(self):
        cases = [
            ("Start a 30-minute mock exam on cardiology", PlatformIntent.EXAM),
            ("Simulate a patient case presenting with chest pain", PlatformIntent.CASE_SIMULATION),
            ("Show my weak topics and learning progress", PlatformIntent.LEARNING_ANALYSIS),
            ("Quiz me on diabetes mellitus with 5 practice questions", PlatformIntent.ASSESSMENT),
            ("Teach me hypertension management step-by-step", PlatformIntent.TEACHING),
        ]
        for query, expected_intent in cases:
            intent = self.router.classify_intent(query)
            self.assertEqual(
                intent,
                expected_intent,
                f"Query '{query}' expected {expected_intent}, got {intent}",
            )

    def test_extensible_custom_rule_registration(self):
        router = IntelligenceRouter()
        # Register custom keyword for EXAM
        router.register_rule(PlatformIntent.EXAM, [r"\bflashcard\s+sprint\b"])
        intent = router.classify_intent("Start a flashcard sprint on antibiotics")
        self.assertEqual(intent, PlatformIntent.EXAM)

    def test_extract_topic_hint(self):
        query = "Quiz me on essential hypertension criteria"
        topic = self.router.extract_topic_hint(query)
        self.assertIsNotNone(topic)
        self.assertIn("Hypertension", topic)


if __name__ == "__main__":
    unittest.main()
