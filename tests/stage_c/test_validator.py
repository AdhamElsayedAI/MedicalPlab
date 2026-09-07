import unittest
from medicalplab.stage_b.models import ContractError
from medicalplab.stage_c.models import (
    Citation,
    EvidenceBlock,
    GeneratedQuestion,
)
from medicalplab.stage_c.validator import (
    is_valid_question,
    validate_question,
)


class TestStageCValidator(unittest.TestCase):

    def setUp(self):
        self.block = EvidenceBlock(
            ref="DOC-001:B0001",
            document_id="DOC-001",
            source="WHO",
            heading="Introduction",
            section="Section 1",
            text="Hypertension or elevated blood pressure is a serious medical condition. Hypertension can be defined using specific systolic and diastolic blood pressure levels.",
        )
        self.packet = (self.block,)

        self.valid_question = GeneratedQuestion(
            question_id="Q001",
            question_type="mcq",
            question="How can hypertension be defined according to the guideline?",
            options=(
                "A. Using specific systolic and diastolic blood pressure levels",
                "B. Exclusively through continuous 24-hour monitoring",
                "C. By checking electrocardiogram voltage criteria",
                "D. By immediate response to loop diuretic challenge",
            ),
            correct_answer="A",
            explanation="The guideline states that hypertension can be defined using specific systolic and diastolic blood pressure levels.",
            difficulty="easy",
            topic="Hypertension Definition",
            citations=(
                Citation(
                    ref="DOC-001:B0001",
                    quote="Hypertension can be defined using specific systolic and diastolic blood pressure levels.",
                ),
            ),
        )

    def test_valid_question_accepted(self):
        # Should execute without raising
        validate_question(self.valid_question, self.packet)
        ok, errors = is_valid_question(self.valid_question, self.packet)
        self.assertTrue(ok)
        self.assertEqual(len(errors), 0)

    def test_missing_citation_ref_rejected(self):
        bad_q = GeneratedQuestion(
            question_id="Q001",
            question_type="mcq",
            question="How can hypertension be defined?",
            options=self.valid_question.options,
            correct_answer="A",
            explanation="Explanation",
            difficulty="easy",
            topic="Hypertension",
            citations=(
                Citation(
                    ref="NONEXISTENT:B9999",  # Not in packet
                    quote="Hypertension can be defined using specific systolic and diastolic blood pressure levels.",
                ),
            ),
        )
        with self.assertRaises(ContractError):
            validate_question(bad_q, self.packet)

        ok, errors = is_valid_question(bad_q, self.packet)
        self.assertFalse(ok)
        self.assertTrue(any("not found in supplied evidence packet" in e for e in errors))

    def test_quote_not_in_block_rejected(self):
        bad_q = GeneratedQuestion(
            question_id="Q001",
            question_type="mcq",
            question="How can hypertension be defined?",
            options=self.valid_question.options,
            correct_answer="A",
            explanation="Explanation",
            difficulty="easy",
            topic="Hypertension",
            citations=(
                Citation(
                    ref="DOC-001:B0001",
                    quote="Invented text that never appears in the evidence block.",
                ),
            ),
        )
        with self.assertRaises(ContractError):
            validate_question(bad_q, self.packet)

    def test_unsupported_answer_rejected(self):
        # Correct answer points to an option completely unsupported by the cited evidence
        bad_q = GeneratedQuestion(
            question_id="Q001",
            question_type="mcq",
            question="How can hypertension be defined?",
            options=(
                "A. Using random unrelated liver enzyme measurements",
                "B. Exclusively through continuous 24-hour monitoring",
                "C. By checking electrocardiogram voltage criteria",
                "D. By immediate response to loop diuretic challenge",
            ),
            correct_answer="A",  # A has no overlap with the evidence quote
            explanation="Explanation about blood pressure.",
            difficulty="easy",
            topic="Hypertension",
            citations=(
                Citation(
                    ref="DOC-001:B0001",
                    quote="Hypertension can be defined using specific systolic and diastolic blood pressure levels.",
                ),
            ),
        )
        with self.assertRaises(ContractError):
            validate_question(bad_q, self.packet)

    def test_distractor_matching_evidence_quote_rejected(self):
        # One of the distractors is verbatim evidence from the document (unintentionally true)
        bad_q = GeneratedQuestion(
            question_id="Q001",
            question_type="mcq",
            question="How can hypertension be defined?",
            options=(
                "A. Using specific systolic and diastolic blood pressure levels",
                "B. Hypertension or elevated blood pressure is a serious medical condition",  # Verbatim sentence from block
                "C. By checking electrocardiogram voltage criteria",
                "D. By immediate response to loop diuretic challenge",
            ),
            correct_answer="A",
            explanation="The guideline states that hypertension can be defined using specific blood pressure levels.",
            difficulty="easy",
            topic="Hypertension",
            citations=(
                Citation(
                    ref="DOC-001:B0001",
                    quote="Hypertension can be defined using specific systolic and diastolic blood pressure levels.",
                ),
            ),
        )
        with self.assertRaises(ContractError):
            validate_question(bad_q, self.packet)


if __name__ == "__main__":
    unittest.main()
