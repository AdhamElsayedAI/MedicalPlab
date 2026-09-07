import unittest
from medicalplab.stage_b.models import ContractError
from medicalplab.stage_c.models import (
    Citation,
    EvidenceBlock,
    GeneratedQuestion,
    QuestionType,
    DifficultyLevel,
)


class TestStageCModels(unittest.TestCase):

    def setUp(self):
        self.citation = Citation(
            ref="DOC-001:B0001",
            quote="Hypertension can be defined using specific systolic levels.",
        )
        self.options = (
            "A. Using systolic levels",
            "B. Using liver enzymes",
            "C. Using blood glucose",
            "D. Using visual acuity",
        )

    def test_valid_question_creation(self):
        q = GeneratedQuestion(
            question_id="Q001",
            question_type="mcq",
            question="How can hypertension be defined?",
            options=self.options,
            correct_answer="A",
            explanation="The guideline states that hypertension is defined using systolic levels.",
            difficulty="easy",
            topic="Hypertension",
            citations=(self.citation,),
        )
        self.assertEqual(q.question_id, "Q001")
        self.assertEqual(q.get_correct_option_text(), "Using systolic levels")
        self.assertEqual(len(q.get_distractor_texts()), 3)
        self.assertIn("Using liver enzymes", q.get_distractor_texts())

    def test_invalid_option_count_rejected(self):
        with self.assertRaises(ContractError):
            GeneratedQuestion(
                question_id="Q001",
                question_type="mcq",
                question="How?",
                options=self.options[:3],  # Only 3 options
                correct_answer="A",
                explanation="Explanation",
                difficulty="easy",
                topic="Topic",
                citations=(self.citation,),
            )

    def test_invalid_correct_answer_rejected(self):
        with self.assertRaises(ContractError):
            GeneratedQuestion(
                question_id="Q001",
                question_type="mcq",
                question="How?",
                options=self.options,
                correct_answer="E",  # Invalid pointer
                explanation="Explanation",
                difficulty="easy",
                topic="Topic",
                citations=(self.citation,),
            )

    def test_missing_citations_rejected(self):
        with self.assertRaises(ContractError):
            GeneratedQuestion(
                question_id="Q001",
                question_type="mcq",
                question="How?",
                options=self.options,
                correct_answer="A",
                explanation="Explanation",
                difficulty="easy",
                topic="Topic",
                citations=(),  # Empty citations
            )

    def test_invalid_difficulty_rejected(self):
        with self.assertRaises(ContractError):
            GeneratedQuestion(
                question_id="Q001",
                question_type="mcq",
                question="How?",
                options=self.options,
                correct_answer="A",
                explanation="Explanation",
                difficulty="extreme",  # Invalid difficulty
                topic="Topic",
                citations=(self.citation,),
            )


if __name__ == "__main__":
    unittest.main()
