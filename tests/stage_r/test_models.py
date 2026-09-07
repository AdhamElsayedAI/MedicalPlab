import unittest
from medicalplab.stage_b.models import ContractError
from medicalplab.stage_r.models import (
    EvaluationResult,
    EvidenceBlock,
    EvidenceCandidate,
    EvidencePacket,
    QueryIntent,
    RerankedEvidence,
    RetrievalQuery,
    ScoreBreakdown,
)


class TestStageRModels(unittest.TestCase):

    def setUp(self):
        self.query = RetrievalQuery(
            raw_query="What drugs treat hypertension?",
            normalized_query="what drugs treat hypertension",
            expanded_terms=("high blood pressure", "elevated blood pressure"),
            intent=QueryIntent.TREATMENT,
            entities=("hypertension",),
        )
        self.breakdown = ScoreBreakdown(
            dense_score=0.85,
            sparse_score=0.75,
            alpha=0.6,
            hybrid_score=0.81,
            rerank_score=0.88,
            final_score=0.85,
        )
        self.candidate = EvidenceCandidate(
            ref="DOC-001:B0001",
            document_id="DOC-001",
            source="WHO",
            heading="Management",
            section="Section 1",
            text="ACE inhibitors are recommended for hypertension.",
            score=0.81,
            score_breakdown=self.breakdown,
        )
        self.reranked = RerankedEvidence(
            ref="DOC-001:B0001",
            document_id="DOC-001",
            source="WHO",
            heading="Management",
            section="Section 1",
            text="ACE inhibitors are recommended for hypertension.",
            retrieval_score=0.81,
            rerank_score=0.88,
            final_score=0.85,
            score_breakdown=self.breakdown,
        )
        self.block = EvidenceBlock(
            ref="DOC-001:B0001",
            document_id="DOC-001",
            source="WHO",
            heading="Management",
            section="Section 1",
            text="ACE inhibitors are recommended for hypertension.",
        )

    def test_retrieval_query_valid_and_frozen(self):
        self.assertEqual(self.query.intent, QueryIntent.TREATMENT)
        self.assertEqual(self.query.entities, ("hypertension",))
        with self.assertRaises(Exception):
            self.query.raw_query = "Changed"

    def test_retrieval_query_invalid_intent_rejected(self):
        with self.assertRaises(ContractError):
            RetrievalQuery(
                raw_query="query",
                normalized_query="query",
                expanded_terms=(),
                intent="treatment",  # Must be QueryIntent enum
                entities=(),
            )

    def test_score_breakdown_alpha_bounds(self):
        with self.assertRaises(ContractError):
            ScoreBreakdown(
                dense_score=0.5,
                sparse_score=0.5,
                alpha=1.5,  # > 1.0
                hybrid_score=0.5,
            )

    def test_evidence_candidate_immutability(self):
        with self.assertRaises(Exception):
            self.candidate.score = 0.99

    def test_evidence_packet_top_k_constraint(self):
        with self.assertRaises(ContractError):
            EvidencePacket(
                query="Query",
                blocks=(self.block,),
                top_k=0,  # Must be >= 1
            )

    def test_evaluation_result_bounds(self):
        with self.assertRaises(ContractError):
            EvaluationResult(
                recall_at_k=1.2,  # > 1.0
                precision_at_k=0.8,
                hit_rate=1.0,
                mrr=0.9,
                k=5,
            )


if __name__ == "__main__":
    unittest.main()
