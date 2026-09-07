import unittest
from medicalplab.stage_r.models import (
    EvidenceCandidate,
    QueryIntent,
    RetrievalQuery,
    ScoreBreakdown,
)
from medicalplab.stage_r.reranker import MedicalReranker


class TestStageRReranker(unittest.TestCase):

    def setUp(self):
        self.query = RetrievalQuery(
            raw_query="What medications treat essential hypertension?",
            normalized_query="what medications treat essential hypertension",
            expanded_terms=("high blood pressure",),
            intent=QueryIntent.TREATMENT,
            entities=("essential hypertension", "hypertension"),
        )
        # Block A: High retrieval score but general definition section
        self.cand_def = EvidenceCandidate(
            ref="DOC-001:B0001",
            document_id="DOC-001",
            source="WHO",
            heading="Definition and Epidemiology",
            section="Section 1",
            text="Hypertension is defined as persistent elevated blood pressure in adults.",
            score=0.85,
            score_breakdown=ScoreBreakdown(0.85, 0.85, 0.5, 0.85),
        )
        # Block B: Lower retrieval score but exact treatment match + Management section
        self.cand_treat = EvidenceCandidate(
            ref="DOC-001:B0002",
            document_id="DOC-001",
            source="WHO",
            heading="Hypertension Management and Pharmacotherapy",
            section="Section 2",
            text="First-line pharmacotherapy for essential hypertension includes ACE inhibitors and thiazide diuretics.",
            score=0.75,
            score_breakdown=ScoreBreakdown(0.75, 0.75, 0.5, 0.75),
        )
        # Block C: Low relevance (Diabetes)
        self.cand_other = EvidenceCandidate(
            ref="DOC-002:B0001",
            document_id="DOC-002",
            source="NICE",
            heading="Diabetes Mellitus",
            section="Section 1",
            text="Metformin is prescribed for type 2 diabetes.",
            score=0.30,
            score_breakdown=ScoreBreakdown(0.30, 0.30, 0.5, 0.30),
        )
        self.candidates = (self.cand_def, self.cand_treat, self.cand_other)

    def test_reranker_promotes_clinically_matched_section(self):
        reranker = MedicalReranker(retrieval_weight=0.30, rerank_weight=0.70)
        reranked = reranker.rerank(self.query, self.candidates, top_k=3)

        self.assertEqual(len(reranked), 3)

        # Candidate B (Management section + exact treatment keywords + entity) must be promoted to Rank 1!
        top = reranked[0]
        self.assertEqual(top.ref, "DOC-001:B0002")
        self.assertIn("Pharmacotherapy", top.heading)

        # Check explainability breakdown
        self.assertIsNotNone(top.score_breakdown)
        self.assertTrue(top.rerank_score > 0.6)
        self.assertEqual(top.score_breakdown.final_score, top.final_score)

        # Candidate C should be last
        self.assertEqual(reranked[2].ref, "DOC-002:B0001")

    def test_reranker_empty_candidates(self):
        reranker = MedicalReranker()
        self.assertEqual(reranker.rerank(self.query, []), ())


if __name__ == "__main__":
    unittest.main()
