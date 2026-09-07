import unittest
from medicalplab.stage_r.context_compressor import (
    ContextCompressor,
    extract_relevant_sentences,
)
from medicalplab.stage_r.models import (
    EvidenceBlock,
    QueryIntent,
    RerankedEvidence,
    RetrievalQuery,
)


class TestStageRCompression(unittest.TestCase):

    def setUp(self):
        self.query = RetrievalQuery(
            raw_query="What drugs treat hypertension?",
            normalized_query="what drugs treat hypertension",
            expanded_terms=("high blood pressure",),
            intent=QueryIntent.TREATMENT,
            entities=("hypertension",),
        )

        self.long_text = (
            "Cardiovascular health is important worldwide and affects populations globally. "
            "Many international committees meet annually to discuss public health initiatives. "
            "First-line pharmacological treatment for hypertension includes ACE inhibitors and thiazide diuretics. "
            "Historical documentation from 1950 described early hemodynamic observations. "
            "Lifestyle interventions should accompany blood pressure therapy."
        )

        self.block = RerankedEvidence(
            ref="DOC-001:B0002",
            document_id="DOC-001",
            source="WHO Guidelines",
            heading="Management",
            section="Section 2",
            text=self.long_text,
            retrieval_score=0.8,
            rerank_score=0.9,
            final_score=0.85,
        )

    def test_compression_extractive_verbatim_integrity(self):
        compressed_text = extract_relevant_sentences(
            self.long_text,
            self.query,
            max_sentences=2,
            min_length_threshold=100,
        )

        # 1. Must contain the key treatment sentence verbatim
        expected_sent = "First-line pharmacological treatment for hypertension includes ACE inhibitors and thiazide diuretics."
        self.assertIn(expected_sent, compressed_text)

        # 2. Must NOT contain the irrelevant historical filler sentence
        self.assertNotIn("Historical documentation from 1950", compressed_text)

        # 3. Verbatim check: every sentence in compressed_text must be a verbatim substring of long_text
        for s in compressed_text.split(". "):
            if s.strip():
                clean_s = s.strip().rstrip(".")
                self.assertIn(clean_s, self.long_text)

    def test_compressor_provenance_preservation(self):
        compressor = ContextCompressor(max_sentences_per_block=2)
        compressed = compressor.compress(self.query, [self.block])

        self.assertEqual(len(compressed), 1)
        res = compressed[0]

        # Provenance must be intact
        self.assertEqual(res.ref, "DOC-001:B0002")
        self.assertEqual(res.document_id, "DOC-001")
        self.assertEqual(res.source, "WHO Guidelines")
        self.assertEqual(res.heading, "Management")
        self.assertEqual(res.section, "Section 2")
        self.assertEqual(res.final_score, 0.85)

    def test_compression_compact_text_untouched(self):
        short_text = "Hypertension requires blood pressure control."
        extracted = extract_relevant_sentences(
            short_text,
            self.query,
            min_length_threshold=160,
        )
        self.assertEqual(extracted, short_text)


if __name__ == "__main__":
    unittest.main()
