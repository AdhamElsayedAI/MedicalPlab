import json
import unittest

from medicalplab.stage_b.models import ContractError
from medicalplab.stage_c.models import EvidenceBlock
from medicalplab.stage_c.generator import parse_generated_questions
from medicalplab.stage_c.pipeline import ModelFailure, StageCPipeline


class StubQuestionBackend:
    model = "stub-c"
    revision = "test"
    quantization = "none"

    def __init__(self, response_json: str | None = None):
        if response_json is None:
            data = {
                "questions": [
                    {
                        "question_id": "Q001",
                        "question_type": "mcq",
                        "question": "How can hypertension be defined according to the guideline?",
                        "options": [
                            "A. Using specific systolic and diastolic blood pressure levels",
                            "B. Exclusively through continuous 24-hour monitoring",
                            "C. By checking electrocardiogram voltage criteria",
                            "D. By immediate response to loop diuretic challenge",
                        ],
                        "correct_answer": "A",
                        "explanation": "The guideline states that hypertension can be defined using specific systolic and diastolic blood pressure levels.",
                        "difficulty": "easy",
                        "topic": "Hypertension Definition",
                        "citations": [
                            {
                                "ref": "DOC-001:B0001",
                                "quote": "Hypertension can be defined using specific systolic and diastolic blood pressure levels.",
                            }
                        ],
                    }
                ]
            }
            self.response_json = json.dumps(data)
        else:
            self.response_json = response_json

    def generate(self, system: str, user: str) -> dict:
        return {
            "text": self.response_json,
            "input_tokens": 100,
            "output_tokens": 80,
        }

    def peak_vram(self):
        return None


class TestStageCPipeline(unittest.TestCase):

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

    def test_parse_valid_generated_questions(self):
        backend = StubQuestionBackend()
        questions = parse_generated_questions(backend.response_json)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].question_id, "Q001")
        self.assertEqual(questions[0].correct_answer, "A")
        self.assertEqual(len(questions[0].options), 4)

    def test_parse_invalid_json_raises(self):
        with self.assertRaises(ContractError):
            parse_generated_questions("not json at all")

    def test_parse_missing_required_keys_raises(self):
        invalid = json.dumps({"questions": [{"question_id": "Q001"}]})
        with self.assertRaises(ContractError):
            parse_generated_questions(invalid)

    def test_pipeline_end_to_end_generation(self):
        backend = StubQuestionBackend()
        pipeline = StageCPipeline(backend)
        questions = pipeline.generate_questions(self.packet, count=1)
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].question_id, "Q001")
        self.assertEqual(questions[0].correct_answer, "A")
        self.assertEqual(len(pipeline.trace), 1)
        self.assertEqual(pipeline.trace[0]["count"], 1)

    def test_pipeline_model_failure_on_bad_output(self):
        backend = StubQuestionBackend(response_json="completely broken output")
        pipeline = StageCPipeline(backend)
        with self.assertRaises(ModelFailure):
            pipeline.generate_questions(self.packet, count=1)


if __name__ == "__main__":
    unittest.main()
