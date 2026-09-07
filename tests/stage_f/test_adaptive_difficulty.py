import unittest
from medicalplab.stage_f.adaptive_difficulty import AdaptiveDifficultyEngine
from medicalplab.stage_f.models import PlatformDifficulty


class TestStageFAdaptiveDifficulty(unittest.TestCase):

    def setUp(self):
        self.engine = AdaptiveDifficultyEngine()

    def test_beginner_mastery_assigns_easy(self):
        diff, reason = self.engine.determine_difficulty(
            accuracy=0.35,
            mastery_level="beginner",
        )
        self.assertEqual(diff, PlatformDifficulty.EASY)
        self.assertIn("EASY", reason)

    def test_developing_mastery_assigns_medium(self):
        diff, reason = self.engine.determine_difficulty(
            accuracy=0.60,
            mastery_level="developing",
        )
        self.assertEqual(diff, PlatformDifficulty.MEDIUM)
        self.assertIn("MEDIUM", reason)

    def test_advanced_high_accuracy_assigns_hard(self):
        diff, reason = self.engine.determine_difficulty(
            accuracy=0.90,
            mastery_level="advanced",
            confidence_level="high",
        )
        self.assertEqual(diff, PlatformDifficulty.HARD)
        self.assertIn("HARD", reason)

    def test_low_confidence_caps_at_medium(self):
        # Even with high accuracy, low sample count confidence caps difficulty at MEDIUM
        diff, reason = self.engine.determine_difficulty(
            accuracy=0.95,
            mastery_level="advanced",
            confidence_level="low",
        )
        self.assertEqual(diff, PlatformDifficulty.MEDIUM)
        self.assertIn("confidence: low", reason)

    def test_poor_recent_performance_steps_down_to_easy(self):
        # Overall 75% accuracy, but recent performance dropped to 20%
        diff, reason = self.engine.determine_difficulty(
            accuracy=0.75,
            mastery_level="proficient",
            recent_accuracy=0.20,
        )
        self.assertEqual(diff, PlatformDifficulty.EASY)
        self.assertIn("recent accuracy: 20%", reason)


if __name__ == "__main__":
    unittest.main()
