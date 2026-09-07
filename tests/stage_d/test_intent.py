import json
import unittest
from medicalplab.stage_d.intent import classify_intent, rule_based_intent
from medicalplab.stage_d.models import TutorMode


class StubIntentBackend:

    def __init__(self, mode_to_return: str, should_fail: bool = False):
        self.mode_to_return = mode_to_return
        self.should_fail = should_fail
        self.call_count = 0

    def generate(self, system: str, user: str) -> dict:
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("Backend connection error")
        return {
            "text": json.dumps({"mode": self.mode_to_return}),
            "input_tokens": 50,
            "output_tokens": 15,
        }


class TestStageDIntent(unittest.TestCase):

    def test_rule_based_case_discussion(self):
        queries = [
            "A 62-year-old male with BP 150/95 presents with mild dizziness.",
            "55 yo patient presents with persistent elevated blood pressure.",
            "What is the next step in management for this patient?",
            "Clinical vignette of a hypertensive patient admitted to emergency.",
        ]
        for q in queries:
            mode = rule_based_intent(q)
            self.assertEqual(
                mode,
                TutorMode.CASE_DISCUSSION,
                f"Query '{q}' failed to classify as CASE_DISCUSSION",
            )

    def test_rule_based_teaching(self):
        queries = [
            "Teach me how to diagnose hypertension step-by-step.",
            "Walk me through the hypertension guideline algorithm.",
            "Can you quiz me on blood pressure treatment?",
            "I need a tutorial on cardiology guidelines.",
            "How should I approach interpreting systolic readings?",
        ]
        for q in queries:
            mode = rule_based_intent(q)
            self.assertEqual(
                mode,
                TutorMode.TEACHING,
                f"Query '{q}' failed to classify as TEACHING",
            )

    def test_rule_based_explanation(self):
        queries = [
            "What is the definition of hypertension according to WHO?",
            "Why is blood pressure categorized into different stages?",
            "Explain the criteria for diagnosing essential hypertension.",
            "How is elevated blood pressure defined in adults?",
        ]
        for q in queries:
            mode = rule_based_intent(q)
            self.assertEqual(
                mode,
                TutorMode.EXPLANATION,
                f"Query '{q}' failed to classify as EXPLANATION",
            )

    def test_rule_based_ambiguous_returns_none(self):
        ambiguous = "Cardiovascular risks in general population."
        mode = rule_based_intent(ambiguous)
        self.assertIsNone(mode)

    def test_classify_intent_skips_backend_when_rule_matches(self):
        backend = StubIntentBackend("teaching")
        mode = classify_intent(
            "A 45-year-old female presents with BP 160/100.",
            backend=backend,
        )
        self.assertEqual(mode, TutorMode.CASE_DISCUSSION)
        self.assertEqual(backend.call_count, 0)  # Rule matched; backend not invoked

    def test_classify_intent_uses_llm_fallback_for_ambiguous(self):
        backend = StubIntentBackend("teaching")
        mode = classify_intent(
            "Pedagogy and structured assessment discussion.",
            backend=backend,
        )
        self.assertEqual(mode, TutorMode.TEACHING)
        self.assertEqual(backend.call_count, 1)

    def test_classify_intent_graceful_default_on_backend_failure(self):
        backend = StubIntentBackend("teaching", should_fail=True)
        mode = classify_intent(
            "Some ambiguous query with failed backend.",
            backend=backend,
        )
        self.assertEqual(mode, TutorMode.EXPLANATION)  # Defaults safely


if __name__ == "__main__":
    unittest.main()
