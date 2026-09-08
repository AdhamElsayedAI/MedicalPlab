import unittest

from medicalplab.plab.models import (
    PLABCitation,
    PLABChoice,
    PLABQuestion,
    PLABQuestionStatus,
)
from medicalplab.plab.validation import validate_plab_question


class TestPLABProductContract(unittest.TestCase):
    def _question(self) -> PLABQuestion:
        return PLABQuestion(
            question_id="PLAB-CARD-0001",
            stem="A patient presents with a clinically relevant cardiovascular scenario requiring a single best answer.",
            choices=tuple(
                PLABChoice(key, text)
                for key, text in zip(
                    ("A", "B", "C", "D", "E"),
                    (
                        "First distinct option",
                        "Second distinct option",
                        "Third distinct option",
                        "Fourth distinct option",
                        "Fifth distinct option",
                    ),
                )
            ),
            correct_answer="B",
            explanation="The second option is supported by the supplied evidence and best matches the learning objective.",
            specialty="Cardiology",
            topic="Acute coronary syndromes",
            learning_objective="Select the single best evidence-supported management step.",
            difficulty="medium",
            citations=(
                PLABCitation(
                    ref="DOC-1:B0001",
                    quote="evidence supporting the second option",
                    document_id="DOC-1",
                ),
            ),
            status=PLABQuestionStatus.NEEDS_REVIEW,
        )

    def test_requires_exactly_five_choices(self):
        question = self._question()
        self.assertEqual(len(question.choices), 5)
        self.assertEqual(tuple(choice.id for choice in question.choices), ("A", "B", "C", "D", "E"))

    def test_validation_accepts_citation_quote_present_in_evidence(self):
        question = self._question()
        errors = validate_plab_question(
            question,
            evidence_texts=["This is evidence supporting the second option in context."],
        )
        self.assertEqual(errors, [])

    def test_validation_rejects_missing_citation_quote(self):
        question = self._question()
        errors = validate_plab_question(question, evidence_texts=["unrelated evidence"])
        self.assertIn("citation_quote_not_found:DOC-1:B0001", errors)


if __name__ == "__main__":
    unittest.main()
