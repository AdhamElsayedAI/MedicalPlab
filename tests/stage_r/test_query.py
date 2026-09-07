import unittest
from medicalplab.stage_r.models import QueryIntent
from medicalplab.stage_r.query_analyzer import (
    analyze_query,
    detect_intent,
    extract_entities,
)
from medicalplab.stage_r.query_expansion import (
    expand_query,
    get_synonyms,
)


class TestStageRQuery(unittest.TestCase):

    def test_detect_intent_rules(self):
        cases = [
            ("What drugs treat hypertension?", QueryIntent.TREATMENT),
            ("Recommended dose of amlodipine in mg", QueryIntent.DOSAGE),
            ("What are the classic symptoms of asthma?", QueryIntent.SYMPTOM),
            ("What is the definition and criteria for hypertension?", QueryIntent.DEFINITION),
            ("What does the WHO guideline recommend?", QueryIntent.GUIDELINE),
            ("Teach me the pathophysiology of heart failure", QueryIntent.EDUCATIONAL),
            ("What are the risk factors and etiology of this condition?", QueryIntent.DISEASE),
        ]
        for query_text, expected_intent in cases:
            intent = detect_intent(query_text)
            self.assertEqual(
                intent,
                expected_intent,
                f"Query '{query_text}' expected {expected_intent}, got {intent}",
            )

    def test_extract_entities(self):
        query = "Can ACE inhibitors and beta blockers be used for essential hypertension?"
        entities = extract_entities(query)
        self.assertIn("essential hypertension", entities)
        self.assertIn("ace inhibitors", entities)
        self.assertIn("beta blockers", entities)

    def test_extract_multi_word_entity_priority(self):
        query = "Management of diabetic ketoacidosis in adults."
        entities = extract_entities(query)
        # Should detect "diabetic ketoacidosis"
        self.assertIn("diabetic ketoacidosis", entities)

    def test_expand_query_controlled_vocabulary(self):
        query = "What drugs treat hypertension?"
        rq = expand_query(query)

        self.assertEqual(rq.intent, QueryIntent.TREATMENT)
        self.assertIn("hypertension", rq.entities)
        self.assertTrue(len(rq.expanded_terms) > 0)
        self.assertIn("high blood pressure", rq.expanded_terms)
        self.assertIn("elevated blood pressure", rq.expanded_terms)

        # Check controlled dictionary integrity (no hallucinated synonyms)
        allowed_synonyms = set(get_synonyms("hypertension"))
        for term in rq.expanded_terms:
            self.assertIn(term, allowed_synonyms)

    def test_expand_query_no_entities(self):
        query = "What are the common medical ethics rules?"
        rq = expand_query(query)
        self.assertEqual(len(rq.entities), 0)
        self.assertEqual(len(rq.expanded_terms), 0)


if __name__ == "__main__":
    unittest.main()
