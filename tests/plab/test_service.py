import json
import unittest

from medicalplab.plab.service import PLABGenerationError, PLABQuestionService
from medicalplab.stage_c.models import EvidenceBlock


class FakeBackend:
    model = "fake-plab-backend"
    revision = "test"

    def __init__(self, payload):
        self.payload = payload

    def generate(self, system, user):
        return {"text": json.dumps(self.payload), "input_tokens": 10, "output_tokens": 20}


class TestPLABQuestionService(unittest.TestCase):
    def setUp(self):
        self.block = EvidenceBlock(
            ref="DOC-1:B0001",
            document_id="DOC-1",
            source="WHO",
            heading="Management",
            section="1",
            text="The recommended management step is immediate transfer for definitive treatment.",
        )

    def _payload(self):
        return {
            "questions": [
                {
                    "question_id": "PLAB-CARD-0001",
                    "stem": "A patient presents with acute symptoms and requires the single best next management step.",
                    "choices": [
                        {"id": "A", "text": "Observe without treatment"},
                        {"id": "B", "text": "Immediate transfer for definitive treatment"},
                        {"id": "C", "text": "Arrange routine review next month"},
                        {"id": "D", "text": "Discharge with no follow-up"},
                        {"id": "E", "text": "Delay all management pending unrelated testing"},
                    ],
                    "correct_answer": "B",
                    "explanation": "Immediate transfer for definitive treatment is the evidence-supported management step for this scenario.",
                    "specialty": "Cardiology",
                    "topic": "Emergency management",
                    "learning_objective": "Choose the evidence-supported immediate management step.",
                    "difficulty": "medium",
                    "citations": [
                        {
                            "ref": "DOC-1:B0001",
                            "document_id": "DOC-1",
                            "quote": "The recommended management step is immediate transfer for definitive treatment.",
                        }
                    ],
                }
            ]
        }

    def test_generates_five_option_question_with_exact_evidence(self):
        service = PLABQuestionService(FakeBackend(self._payload()))
        questions = service.generate(
            [self.block],
            specialty="Cardiology",
            topic="Emergency management",
        )
        self.assertEqual(len(questions), 1)
        self.assertEqual(len(questions[0].choices), 5)
        self.assertEqual(questions[0].correct_answer, "B")

    def test_rejects_quote_not_in_evidence(self):
        payload = self._payload()
        payload["questions"][0]["citations"][0]["quote"] = "invented evidence quote"
        service = PLABQuestionService(FakeBackend(payload))
        with self.assertRaises(PLABGenerationError):
            service.generate([self.block], specialty="Cardiology", topic="Emergency management")


if __name__ == "__main__":
    unittest.main()
