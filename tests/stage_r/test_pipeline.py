import unittest
from medicalplab.stage_b.models import ContractError
from medicalplab.stage_r.evaluation import (
    compute_hit_rate,
    compute_mrr,
    compute_precision_at_k,
    compute_recall_at_k,
    evaluate_retrieval,
)
from medicalplab.stage_r.models import (
    EvidenceBlock,
    EvidencePacket,
    QueryIntent,
)
from medicalplab.stage_r.pipeline import StageRPipeline


class TestStageRPipeline(unittest.TestCase):

    def setUp(self):
        self.corpus = [
            EvidenceBlock(
                ref="CARD-001",
                document_id="DOC-WHO",
                source="WHO",
                heading="Cardiovascular Diseases Overview",
                section="Introduction",
                text="Hypertension is a chronic medical condition in which blood pressure in the arteries is persistently elevated.",
            ),
            EvidenceBlock(
                ref="CARD-002",
                document_id="DOC-WHO",
                source="WHO",
                heading="Hypertension Management and Pharmacotherapy",
                section="Management",
                text="First-line pharmacological treatment for hypertension includes ACE inhibitors, ARBs, and thiazide diuretics. Regular follow-up is necessary.",
            ),
            EvidenceBlock(
                ref="ENDO-001",
                document_id="DOC-NICE",
                source="NICE",
                heading="Type 2 Diabetes Mellitus",
                section="Pharmacology",
                text="Metformin is the initial drug of choice for type 2 diabetes mellitus if tolerated.",
            ),
            EvidenceBlock(
                ref="RESP-001",
                document_id="DOC-BTS",
                source="BTS",
                heading="Asthma Guidelines",
                section="Therapy",
                text="Inhaled corticosteroids are recommended for persistent asthma symptoms.",
            ),
        ]
        self.pipeline = StageRPipeline(alpha=0.5, top_k=2, compress=True)

    def test_pipeline_end_to_end_retrieval(self):
        query = "What first-line drugs treat hypertension?"
        packet = self.pipeline.retrieve(query, self.corpus, top_k=2)

        self.assertIsInstance(packet, EvidencePacket)
        self.assertEqual(packet.query, query)
        self.assertEqual(packet.top_k, 2)
        self.assertTrue(len(packet.blocks) <= 2)

        # CARD-002 contains exact treatment + management match -> must be rank 1
        top_block = packet.blocks[0]
        self.assertEqual(top_block.ref, "CARD-002")
        self.assertIn("ACE inhibitors", top_block.text)

        # Verify metadata
        meta_dict = dict(packet.metadata)
        self.assertEqual(meta_dict.get("intent"), QueryIntent.TREATMENT.value)
        self.assertIn("hypertension", meta_dict.get("entities", ""))

        # Verify pipeline execution trace
        self.assertEqual(len(self.pipeline.trace), 1)
        self.assertEqual(self.pipeline.trace[0]["query"], query)
        self.assertEqual(self.pipeline.trace[0]["intent"], "treatment")

    def test_pipeline_alpha_override(self):
        query = "What is the definition of hypertension?"
        packet = self.pipeline.retrieve(query, self.corpus, top_k=1, alpha_override=0.9)

        meta_dict = dict(packet.metadata)
        self.assertEqual(meta_dict.get("alpha"), "0.9")
        self.assertEqual(len(packet.blocks), 1)

    def test_retrieval_evaluation_metrics(self):
        retrieved = ["CARD-002", "CARD-001", "ENDO-001"]
        relevant = {"CARD-002"}

        hit_rate = compute_hit_rate(retrieved, relevant, k=1)
        self.assertEqual(hit_rate, 1.0)

        recall = compute_recall_at_k(retrieved, relevant, k=1)
        self.assertEqual(recall, 1.0)

        precision = compute_precision_at_k(retrieved, relevant, k=2)
        self.assertEqual(precision, 0.5)  # 1 hit out of 2 retrieved

        mrr = compute_mrr(retrieved, relevant, k=3)
        self.assertEqual(mrr, 1.0)  # Found at rank 1 -> 1/1 = 1.0

        # Multi-query aggregate evaluation
        test_cases = [
            (["CARD-002", "CARD-001"], {"CARD-002"}),
            (["ENDO-001", "RESP-001"], {"RESP-001"}),  # Hit at rank 2 -> MRR = 0.5
        ]
        result = evaluate_retrieval(test_cases, k=2)
        self.assertEqual(result.hit_rate, 1.0)
        self.assertEqual(result.recall_at_k, 1.0)
        self.assertEqual(result.precision_at_k, 0.5)
        self.assertEqual(result.mrr, 0.75)  # (1.0 + 0.5) / 2 = 0.75


if __name__ == "__main__":
    unittest.main()
