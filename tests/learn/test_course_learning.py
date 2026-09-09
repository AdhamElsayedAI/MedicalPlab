"""Unit tests for Course Learning Service across Cardiorespiratory and Urinary tracks."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from medicalplab.learn.models import CourseQueryRequest, CourseTrack, GroundingStatus
from medicalplab.learn.service import CourseLearningService
from medicalplab.learn.renal_retrieval import RenalRetrievalHit, RenalRetrieverUnavailable


RENAL_CHUNK = {
    "document_id": "DOC-PMC-RENAL-0006",
    "chunk_id": "DOC-PMC-RENAL-0006-B0001-C01",
    "section_path": ["Abstract"],
    "text": "Acute kidney injury requires early detection and intervention.",
}


class FakeRenalRetriever:
    def __init__(self, score=0.9, hits=True):
        self.score = score
        self.hits = hits

    def retrieve(self, query, top_k=5):
        return [RenalRetrievalHit(RENAL_CHUNK, self.score)] if self.hits else []


class UnavailableRenalRetriever:
    def retrieve(self, query, top_k=5):
        raise RenalRetrieverUnavailable("optional runtime absent")


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
        with TemporaryDirectory() as folder:
            service = CourseLearningService(data_root=Path(folder), renal_retriever=FakeRenalRetriever())
            res = service.query(CourseQueryRequest(course_id="urinary_renal", query="AKI criteria"))
        self.assertEqual(res.grounding_status, GroundingStatus.DATA_SOURCE_MISSING)
        self.assertIn("corpus files are missing", res.warning)

    def test_renal_grounded_extract_is_cited(self):
        service = CourseLearningService(renal_retriever=FakeRenalRetriever(score=0.9))
        req = CourseQueryRequest(
            course_id="urinary_renal",
            query="What are the diagnostic criteria for acute kidney injury?",
        )
        res = service.query(req)
        self.assertEqual(res.course_id, "urinary_renal")
        self.assertEqual(res.grounding_status, GroundingStatus.GROUNDED)
        self.assertEqual(res.evidence_sufficiency_state, "SUFFICIENT")
        self.assertEqual(res.answer, RENAL_CHUNK["text"])
        self.assertEqual(res.citations[0].reference, "DOC-PMC-RENAL-0006#DOC-PMC-RENAL-0006-B0001-C01")

    def test_renal_insufficient_evidence_fails_closed(self):
        service = CourseLearningService(renal_retriever=FakeRenalRetriever(score=0.7))
        res = service.query(CourseQueryRequest(course_id="renal", query="AKI criteria"))
        self.assertEqual(res.grounding_status, GroundingStatus.INSUFFICIENT_EVIDENCE)
        self.assertIsNone(res.answer)
        self.assertEqual(res.evidence_sufficiency_state, "INSUFFICIENT")

    def test_renal_unsupported_when_retrieval_is_empty(self):
        service = CourseLearningService(renal_retriever=FakeRenalRetriever(hits=False))
        res = service.query(CourseQueryRequest(course_id="renal", query="uncovered topic"))
        self.assertEqual(res.grounding_status, GroundingStatus.UNSUPPORTED)
        self.assertEqual(res.citations, ())

    def test_renal_optional_runtime_failure_is_safe(self):
        service = CourseLearningService(renal_retriever=UnavailableRenalRetriever())
        res = service.query(CourseQueryRequest(course_id="renal", query="AKI criteria"))
        self.assertEqual(res.grounding_status, GroundingStatus.INSUFFICIENT_EVIDENCE)
        self.assertIsNone(res.answer)

    def test_renal_quiz_stays_blocked_by_quality_gate(self):
        service = CourseLearningService(renal_retriever=FakeRenalRetriever(score=0.9))
        res = service.query(CourseQueryRequest(course_id="renal", query="AKI criteria", intent="quiz"))
        self.assertEqual(res.grounding_status, GroundingStatus.GROUNDED)
        self.assertIsNone(res.learning_check)
        self.assertIn("SBA generation is quality-gated", res.warning)

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
