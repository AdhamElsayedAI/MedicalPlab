"""Executable API contract tests for Application and Mobile Client Handoff."""

import os
import sys
import unittest
import uuid
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from medicalplab.stage_g.product_api import configure_course_learning_service, configure_plab_service, router
from medicalplab.plab.pilot import PLABPilotService
from medicalplab.learn.service import CourseLearningService
from medicalplab.learn.renal_retrieval import RenalRetrievalHit


class _ContractRenalRetriever:
    def retrieve(self, query, top_k=5):
        return [RenalRetrievalHit({
            "document_id": "DOC-PMC-RENAL-0006",
            "chunk_id": "DOC-PMC-RENAL-0006-B0001-C01",
            "section_path": ["Abstract"],
            "text": "Acute kidney injury requires early detection and intervention.",
        }, 0.9)]


class TestMobileApiContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = FastAPI()
        app.include_router(router)
        cls.client = TestClient(app)

    def setUp(self):
        # Default strict pilot service (0 Golden, Preview QA off)
        configure_plab_service(PLABPilotService.load_default(preview_qa=False, enable_persistence=False))
        configure_course_learning_service(None)

    def test_version_endpoint_contract(self):
        res = self.client.get("/api/v1/version")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("service"), "MedicalPlab Product API")
        self.assertEqual(data.get("api_version"), "v1")
        self.assertEqual(data.get("contract_version"), "2026-09-10")

    def test_anatomy_structures_contract(self):
        res = self.client.get("/api/v1/anatomy/structures")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("schema_version"), "anatomy-ontology-v1")
        self.assertEqual(data.get("count"), 11)
        self.assertEqual(len(data.get("structures", [])), 11)

    def test_anatomy_command_natural_language_show(self):
        payload = {"query": "Show me the left ventricle"}
        res = self.client.post("/api/v1/anatomy/command", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("validated"))
        self.assertEqual(data.get("command", {}).get("action"), "show")
        self.assertEqual(data.get("command", {}).get("structure_ids"), ["left_ventricle"])
        self.assertIsNotNone(data.get("educational_context"))

    def test_anatomy_command_natural_language_alias(self):
        payload = {"query": "Highlight the LAD artery"}
        res = self.client.post("/api/v1/anatomy/command", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("command", {}).get("action"), "highlight")
        self.assertEqual(data.get("command", {}).get("structure_ids"), ["lad"])

    def test_anatomy_command_reset(self):
        payload = {"query": "Reset viewport view"}
        res = self.client.post("/api/v1/anatomy/command", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("command", {}).get("action"), "reset")
        self.assertEqual(data.get("command", {}).get("structure_ids"), [])

    def test_anatomy_command_unsupported_structure_refusal(self):
        payload = {"query": "Show me the kidney"}
        res = self.client.post("/api/v1/anatomy/command", json=payload)
        self.assertEqual(res.status_code, 422)
        err = res.json().get("detail", {})
        self.assertEqual(err.get("code"), "UNSUPPORTED_ANATOMY_REQUEST")
        self.assertIn("UNSUPPORTED_STRUCTURE", err.get("message", ""))

    def test_course_learning_cardiorespiratory_grounded(self):
        payload = {
            "course_id": "cardiorespiratory",
            "query": "percutaneous coronary intervention in acute myocardial infarction STEMI",
            "intent": "explain",
        }
        res = self.client.post("/api/v1/learn/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("course_id"), "cardiorespiratory")
        self.assertEqual(data.get("grounding_status"), "GROUNDED")
        self.assertEqual(data.get("evidence_sufficiency_state"), "SUFFICIENT")
        self.assertIsNotNone(data.get("answer"))
        self.assertTrue(len(data.get("citations", [])) > 0)
        self.assertTrue(data.get("trace_id", "").startswith("LRN-"))

    def test_course_learning_renal_grounded_contract(self):
        configure_course_learning_service(CourseLearningService(renal_retriever=_ContractRenalRetriever()))
        payload = {
            "course_id": "urinary_renal",
            "query": "Diagnostic criteria for acute kidney injury and staging",
            "intent": "explain",
        }
        res = self.client.post("/api/v1/learn/query", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("course_id"), "urinary_renal")
        self.assertEqual(data.get("grounding_status"), "GROUNDED")
        self.assertEqual(data.get("evidence_sufficiency_state"), "SUFFICIENT")
        self.assertIsNotNone(data.get("answer"))
        self.assertEqual(data["citations"][0]["document_id"], "DOC-PMC-RENAL-0006")

    def test_plab_questions_empty_in_production_golden_only(self):
        res = self.client.get("/api/v1/plab/questions")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("count"), 0)
        self.assertEqual(data.get("items"), [])
        self.assertEqual(data.get("content_policy"), "GOLDEN_ONLY")

    def test_plab_pre_answer_no_leakage_in_preview_qa(self):
        configure_plab_service(PLABPilotService.load_default(preview_qa=True, enable_persistence=False))
        res = self.client.get("/api/v1/plab/questions")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data.get("count"), 0)
        q = data["items"][0]

        # Assert zero answer or review internals leaked
        self.assertNotIn("correct_answer", q)
        self.assertNotIn("is_correct", q)
        self.assertNotIn("isCorrect", q)
        self.assertNotIn("explanation", q)
        self.assertNotIn("citations", q)
        self.assertNotIn("reviewer_id", q)
        self.assertNotIn("revisions", q)

        # Assert student fields present
        self.assertIn("question_id", q)
        self.assertIn("stem", q)
        self.assertIn("options", q)
        self.assertEqual(len(q["options"]), 5)
        self.assertEqual(q.get("content_mode"), "PREVIEW_QA")
        self.assertIn("Not clinically approved", q.get("warning", ""))

    def test_plab_evaluate_flow_and_idempotency(self):
        configure_plab_service(PLABPilotService.load_default(preview_qa=True, enable_persistence=False))
        questions = self.client.get("/api/v1/plab/questions").json()["items"]
        qid = questions[0]["question_id"]
        key = str(uuid.uuid4())

        payload = {
            "question_id": qid,
            "selected_option": "A",
            "idempotency_key": key,
            "response_time_ms": 12500,
        }
        res1 = self.client.post("/api/v1/plab/evaluate", json=payload, headers={"X-User-Id": "STU-CONTRACT-01"})
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()

        self.assertIn("attempt_id", data1)
        self.assertIn("correct", data1)
        self.assertEqual(data1.get("selected_answer"), "A")
        self.assertIn("correct_answer", data1)
        self.assertIn("explanation", data1)
        self.assertIn("citations", data1)
        self.assertIn("learning_feedback", data1)

        # Submit identical duplicate with same idempotency key
        res2 = self.client.post("/api/v1/plab/evaluate", json=payload, headers={"X-User-Id": "STU-CONTRACT-01"})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data1["attempt_id"], data2["attempt_id"])
        self.assertEqual(data1["correct"], data2["correct"])

    def test_plab_progress_contract(self):
        configure_plab_service(PLABPilotService.load_default(preview_qa=True, enable_persistence=False))
        res = self.client.get("/api/v1/plab/progress", headers={"X-User-Id": "STU-CONTRACT-01"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("user_id"), "STU-CONTRACT-01")
        self.assertIn("total_attempts", data)
        self.assertIn("overall_accuracy", data)
        self.assertIn("topic_accuracy", data)


if __name__ == "__main__":
    unittest.main()

