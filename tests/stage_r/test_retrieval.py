import unittest
from medicalplab.stage_b.models import ContractError
from medicalplab.stage_r.hybrid_retriever import (
    HybridRetriever,
    SparseBM25Retriever,
    StubDenseRetriever,
)
from medicalplab.stage_r.models import (
    EvidenceBlock,
    QueryIntent,
    RetrievalQuery,
)


class TestStageRRetrieval(unittest.TestCase):

    def setUp(self):
        self.block1 = EvidenceBlock(
            ref="DOC-001:B0001",
            document_id="DOC-001",
            source="WHO",
            heading="Hypertension Definition",
            section="Section 1",
            text="Hypertension is defined as persistent blood pressure of 140/90 mmHg or higher.",
        )
        self.block2 = EvidenceBlock(
            ref="DOC-001:B0002",
            document_id="DOC-001",
            source="WHO",
            heading="Hypertension Management",
            section="Section 2",
            text="Pharmacological treatment is recommended with ACE inhibitors and thiazide diuretics.",
        )
        self.block3 = EvidenceBlock(
            ref="DOC-002:B0001",
            document_id="DOC-002",
            source="NICE",
            heading="Diabetes Mellitus",
            section="Section 1",
            text="Metformin is first-line therapy for type 2 diabetes mellitus.",
        )
        self.corpus = (self.block1, self.block2, self.block3)

        self.query = RetrievalQuery(
            raw_query="What medications treat high blood pressure?",
            normalized_query="what medications treat high blood pressure",
            expanded_terms=("hypertension", "elevated blood pressure"),
            intent=QueryIntent.TREATMENT,
            entities=("hypertension",),
        )

    def test_sparse_bm25_retriever(self):
        bm25 = SparseBM25Retriever()
        scores = bm25.score(self.query, self.corpus)

        self.assertIn("DOC-001:B0001", scores)
        self.assertIn("DOC-001:B0002", scores)
        self.assertIn("DOC-002:B0001", scores)

        # Block 2 mentions "treatment" and "hypertension" -> should score high
        self.assertTrue(scores["DOC-001:B0002"] > scores["DOC-002:B0001"])
        for score in scores.values():
            self.assertTrue(0.0 <= score <= 1.0)

    def test_hybrid_retriever_alpha_weighting(self):
        # Stub dense with known scores
        dense = StubDenseRetriever(
            scores={
                "DOC-001:B0001": 0.20,
                "DOC-001:B0002": 0.80,
                "DOC-002:B0001": 0.10,
            }
        )

        # Test alpha = 1.0 (purely dense)
        retriever_dense = HybridRetriever(dense_retriever=dense, alpha=1.0)
        candidates_dense = retriever_dense.retrieve(self.query, self.corpus, top_k=3)
        self.assertEqual(candidates_dense[0].ref, "DOC-001:B0002")
        self.assertAlmostEqual(candidates_dense[0].score, 0.80, places=2)
        self.assertEqual(candidates_dense[0].score_breakdown.alpha, 1.0)

        # Test alpha = 0.0 (purely sparse)
        retriever_sparse = HybridRetriever(dense_retriever=dense, alpha=0.0)
        candidates_sparse = retriever_sparse.retrieve(self.query, self.corpus, top_k=3)
        self.assertEqual(candidates_sparse[0].score_breakdown.alpha, 0.0)
        self.assertAlmostEqual(
            candidates_sparse[0].score,
            candidates_sparse[0].score_breakdown.sparse_score,
            places=4,
        )

        # Test alpha = 0.5 (balanced)
        retriever_balanced = HybridRetriever(dense_retriever=dense, alpha=0.5)
        candidates_balanced = retriever_balanced.retrieve(self.query, self.corpus, top_k=3)
        top = candidates_balanced[0]
        expected_score = round(
            0.5 * top.score_breakdown.dense_score + 0.5 * top.score_breakdown.sparse_score,
            4,
        )
        self.assertAlmostEqual(top.score, expected_score, places=4)

    def test_hybrid_retriever_alpha_override(self):
        dense = StubDenseRetriever()
        retriever = HybridRetriever(dense_retriever=dense, alpha=0.5)
        candidates = retriever.retrieve(self.query, self.corpus, top_k=2, alpha_override=0.8)
        self.assertEqual(candidates[0].score_breakdown.alpha, 0.8)

    def test_hybrid_retriever_empty_corpus(self):
        retriever = HybridRetriever()
        results = retriever.retrieve(self.query, [], top_k=5)
        self.assertEqual(results, ())


if __name__ == "__main__":
    unittest.main()
