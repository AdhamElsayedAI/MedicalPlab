"""Unit tests for Course Learning Service across Cardiorespiratory and Urinary tracks."""

import unittest

from medicalplab.learn.models import CourseQueryRequest, CourseTrack, GroundingStatus
from medicalplab.learn.service import CourseLearningService


class TestCourseLearningService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = CourseLearningService()

    def test_cardiorespiratory_grounded_query(self):
        req = CourseQueryRequest(
            course_id="cardiorespiratory",
            query="percutaneous coronary intervention myocardial infarction STEMI guideline",
        )
        res = self.service.query(req)
        self.assertEqual(res.course_id, "cardiorespiratory")
        self.assertEqual(res.grounding_status, GroundingStatus.GROUNDED)
        self.assertEqual(res.evidence_sufficiency_state, "SUFFICIENT")
        self.assertIsNotNone(res.answer)
        self.assertTrue(len(res.citations) > 0)
        self.assertIsNotNone(res.evidence_sufficiency_score)
        self.assertGreaterEqual(res.evidence_sufficiency_score, 0.7223)

    def test_cardiorespiratory_learning_check_generation(self):
        req = CourseQueryRequest(
            course_id="cardiorespiratory",
            query="acute coronary syndrome risk stratification management",
            intent="check",
        )
        res = self.service.query(req)
        self.assertEqual(res.grounding_status, GroundingStatus.GROUNDED)
        self.assertIsNotNone(res.learning_check)
        check = res.learning_check
        assert check is not None
        self.assertEqual(len(check["choices"]), 5)
        self.assertIn(check["correct_answer"], ["A", "B", "C", "D", "E"])
        self.assertIn("learning_objective", check)

    def test_cardiorespiratory_insufficient_evidence_safe_refusal(self):
        req = CourseQueryRequest(
            course_id="cardiorespiratory",
            query="obscure atypical non-cardiac vascular manifestation",
        )
        res = self.service.query(req)
        # Should not claim grounded if evidence is weak
        self.assertIn(
            res.grounding_status,
            [GroundingStatus.INSUFFICIENT_EVIDENCE, GroundingStatus.UNSUPPORTED],
        )
        if res.grounding_status == GroundingStatus.INSUFFICIENT_EVIDENCE:
            self.assertIsNone(res.answer)
            self.assertIn("refuses to speculate", res.explanation.lower())

    def test_urinary_track_reports_source_data_missing_truthfully(self):
        req = CourseQueryRequest(
            course_id="urinary_renal",
            query="What are the diagnostic criteria for acute kidney injury?",
        )
        res = self.service.query(req)
        self.assertEqual(res.course_id, "urinary_renal")
        self.assertEqual(res.grounding_status, GroundingStatus.DATA_SOURCE_MISSING)
        self.assertEqual(res.evidence_sufficiency_state, "NO_EVIDENCE")
        self.assertIsNone(res.answer)
        self.assertIsNotNone(res.warning)
        self.assertIn("URINARY_SOURCE_DATA = NOT AVAILABLE", res.warning)
        self.assertIn("Data/raw/urinary", res.explanation)

    def test_unregistered_course_module_rejected(self):
        req = CourseQueryRequest(
            course_id="dermatology",
            query="Management of eczema",
        )
        res = self.service.query(req)
        self.assertEqual(res.grounding_status, GroundingStatus.UNSUPPORTED)
        self.assertIn("not yet registered", res.explanation)


if __name__ == "__main__":
    unittest.main()
