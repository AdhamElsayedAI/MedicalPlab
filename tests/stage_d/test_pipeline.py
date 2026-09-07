import json
import unittest

from medicalplab.stage_b.models import ContractError
from medicalplab.stage_d.models import (
    ConfidenceLevel,
    EvidenceBlock,
    TutorMode,
    TutorRequest,
    TutorResponse,
)
from medicalplab.stage_d.pipeline import ModelFailure, StageDPipeline


class StubTutorBackend:
    model = "stub-tutor-d"
    revision = "test"
    quantization = "none"

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or []
        self.call_count = 0
        self.last_system = None
        self.last_user = None

    def generate(self, system: str, user: str) -> dict:
        self.call_count += 1
        self.last_system = system
        self.last_user = user

        if self.responses:
            idx = min(self.call_count - 1, len(self.responses) - 1)
            resp = self.responses[idx]
        else:
            resp = json.dumps(
                {
                    "answer": "Hypertension is defined as persistent blood pressure of 140/90 mmHg or higher based on repeated measurements.",
                    "sections": [
                        {
                            "heading": "Diagnostic Criteria",
                            "content": "A systolic reading of 140 mmHg or higher or diastolic of 90 mmHg or higher is required across clinical visits.",
                        }
                    ],
                    "citations": [
                        {
                            "ref": "DOC-WHO-001:B0001",
                            "quote": "persistent systolic blood pressure of 140 mmHg or higher, or diastolic blood pressure of 90 mmHg or higher",
                        }
                    ],
                    "confidence": "high",
                    "unsupported_aspects": [],
                }
            )

        return {
            "text": resp,
            "input_tokens": 120,
            "output_tokens": 85,
        }


class TestStageDPipeline(unittest.TestCase):

    def setUp(self):
        self.block1 = EvidenceBlock(
            ref="DOC-WHO-001:B0001",
            document_id="DOC-WHO-001",
            source="WHO",
            heading="Hypertension Definition",
            section="Section 1",
            text="Hypertension is defined as persistent systolic blood pressure of 140 mmHg or higher, or diastolic blood pressure of 90 mmHg or higher. Repeated measurements are required for diagnosis.",
        )
        self.block2 = EvidenceBlock(
            ref="DOC-WHO-001:B0002",
            document_id="DOC-WHO-001",
            source="WHO",
            heading="Management",
            section="Section 2",
            text="Pharmacological treatment is recommended for individuals with confirmed hypertension. Lifestyle intervention should accompany therapy.",
        )
        self.packet = (self.block1, self.block2)

    def test_pipeline_explanation_mode(self):
        backend = StubTutorBackend()
        pipeline = StageDPipeline(backend)

        resp = pipeline.ask(
            query="What is the definition of hypertension?",
            evidence=self.packet,
            mode=TutorMode.EXPLANATION,
        )

        self.assertIsInstance(resp, TutorResponse)
        self.assertEqual(resp.mode, TutorMode.EXPLANATION)
        self.assertEqual(resp.confidence, ConfidenceLevel.HIGH)
        self.assertEqual(len(resp.citations), 1)
        self.assertEqual(len(pipeline.trace), 1)
        self.assertEqual(pipeline.trace[0]["mode"], "explanation")

    def test_pipeline_automatic_intent_case_discussion(self):
        backend = StubTutorBackend()
        pipeline = StageDPipeline(backend)

        # Mode is None; query should automatically resolve to CASE_DISCUSSION
        req = TutorRequest(
            query="A 65-year-old male with BP 155/95 presents to clinic.",
            evidence=self.packet,
            mode=None,
        )
        resp = pipeline.run(req)

        self.assertEqual(resp.mode, TutorMode.CASE_DISCUSSION)
        self.assertEqual(pipeline.trace[0]["mode"], "case_discussion")

    def test_pipeline_automatic_intent_teaching(self):
        backend = StubTutorBackend()
        pipeline = StageDPipeline(backend)

        # Mode is None; query should automatically resolve to TEACHING
        req = TutorRequest(
            query="Teach me how to diagnose hypertension step-by-step.",
            evidence=self.packet,
            mode=None,
        )
        resp = pipeline.run(req)

        self.assertEqual(resp.mode, TutorMode.TEACHING)
        self.assertEqual(pipeline.trace[0]["mode"], "teaching")

    def test_pipeline_json_retry_recovery(self):
        # First attempt returns invalid non-JSON string, second attempt returns valid JSON
        valid_json = json.dumps(
            {
                "answer": "Hypertension is defined as persistent blood pressure of 140/90 mmHg or higher.",
                "sections": [
                    {
                        "heading": "Overview",
                        "content": "Persistent readings above 140/90 mmHg confirm hypertension.",
                    }
                ],
                "citations": [
                    {
                        "ref": "DOC-WHO-001:B0001",
                        "quote": "persistent systolic blood pressure of 140 mmHg or higher, or diastolic blood pressure of 90 mmHg or higher",
                    }
                ],
                "confidence": "high",
                "unsupported_aspects": [],
            }
        )
        backend = StubTutorBackend(responses=["not json at all, sorry!", valid_json])
        pipeline = StageDPipeline(backend)

        resp = pipeline.ask(
            query="What is the definition of hypertension?",
            evidence=self.packet,
        )
        self.assertIsInstance(resp, TutorResponse)
        self.assertEqual(backend.call_count, 2)  # Recovered on 2nd attempt

    def test_pipeline_model_failure_when_all_retries_fail(self):
        backend = StubTutorBackend(responses=["not json 1", "not json 2", "not json 3"])
        pipeline = StageDPipeline(backend)

        with self.assertRaises(ModelFailure):
            pipeline.ask(
                query="What is the definition of hypertension?",
                evidence=self.packet,
            )

    def test_pipeline_clinical_safety_rejection(self):
        # Model returns unsupported cure claim
        bad_json = json.dumps(
            {
                "answer": "Hypertension is defined as persistent blood pressure 140/90 and this drug cures the patient completely.",
                "sections": [
                    {
                        "heading": "Cure",
                        "content": "This drug permanently cures hypertension in patients.",
                    }
                ],
                "citations": [
                    {
                        "ref": "DOC-WHO-001:B0001",
                        "quote": "persistent systolic blood pressure of 140 mmHg or higher, or diastolic blood pressure of 90 mmHg or higher",
                    }
                ],
                "confidence": "high",
                "unsupported_aspects": [],
            }
        )
        backend = StubTutorBackend(responses=[bad_json])
        pipeline = StageDPipeline(backend)

        with self.assertRaises(ContractError) as ctx:
            pipeline.ask(
                query="Can hypertension be cured?",
                evidence=self.packet,
            )
        self.assertIn("cure", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
