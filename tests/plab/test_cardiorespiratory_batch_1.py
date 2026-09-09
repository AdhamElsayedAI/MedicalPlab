"""Test suite validating the Cardiorespiratory PLAB Question Batch 1.

Ensures that all 36 questions in Data/questions/cardiorespiratory_batch_1.json
adhere strictly to the PLAB 1 five-option SBA contract, pass all validation gates,
are 100% grounded in verified corpus chunks, and cover all 12 UK topics.
"""

from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

from medicalplab.plab.models import (
    PLABCitation,
    PLABChoice,
    PLABQuestion,
    PLABQuestionStatus,
)
from medicalplab.plab.validation import validate_plab_question


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BATCH_PATH = PROJECT_ROOT / "Data" / "questions" / "cardiorespiratory_batch_1.json"
SNAPSHOT_PATH = (
    PROJECT_ROOT / "Data" / "metadata" / "corpus_cardiorespiratory_snapshot_v1.json"
)
MANIFEST_PATH = (
    PROJECT_ROOT / "Data" / "metadata" / "cardiorespiratory_batch_1_v1.manifest.json"
)

EXPECTED_TOPICS = {
    "Hypertension (Essential & Secondary)",
    "Atrial Fibrillation (Rate vs Rhythm, Anticoagulation)",
    "Syncope & Transient Loss of Consciousness",
    "Chronic Obstructive Pulmonary Disease (COPD)",
    "Cardiopulmonary Resuscitation & Cardiac Arrest",
    "Pneumothorax",
    "Acute Respiratory Distress Syndrome (ARDS)",
    "Cardiogenic Shock",
    "Infective Endocarditis (IE)",
    "Bradyarrhythmias & Conduction Blocks",
    "Aortic Stenosis (Valvular Heart Disease)",
    "Functional Mitral Regurgitation",
}


class TestCardiorespiratoryBatch1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assertTrue(BATCH_PATH.exists(), f"Batch file not found: {BATCH_PATH}")
        with open(BATCH_PATH, "r", encoding="utf-8") as f:
            cls.batch_data = json.load(f)

        cls.assertTrue(SNAPSHOT_PATH.exists(), f"Snapshot not found: {SNAPSHOT_PATH}")
        with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
            snapshot = json.load(f)

        cls.chunk_index = {}
        for doc in snapshot["documents"]:
            doc_id = doc["document_id"]
            chunks_file = PROJECT_ROOT / doc["chunks_file"]
            with open(chunks_file, "r", encoding="utf-8") as cf:
                cdata = json.load(cf)
            for chunk in cdata["chunks"]:
                cls.chunk_index[chunk["chunk_id"]] = {
                    "document_id": doc_id,
                    "text": chunk["text"],
                }

    def test_batch_metadata_and_structure(self):
        self.assertEqual(self.batch_data.get("batch_id"), "cardiorespiratory_batch_1_v1")
        self.assertEqual(
            self.batch_data.get("status"),
            "AUTOMATED_VALIDATION_PASSED_PENDING_HUMAN_REVIEW",
        )
        self.assertEqual(self.batch_data.get("topics_covered"), 12)
        self.assertEqual(self.batch_data.get("questions_per_topic"), 3)
        self.assertEqual(len(self.batch_data["questions"]), 36)

    def test_frozen_manifest_matches_batch_bytes_and_lifecycle(self):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        actual_sha256 = hashlib.sha256(BATCH_PATH.read_bytes()).hexdigest()
        self.assertEqual(manifest["batch_file_sha256"], actual_sha256)
        self.assertEqual(manifest["total_questions"], len(self.batch_data["questions"]))
        self.assertEqual(
            manifest["question_ids"],
            [question["question_id"] for question in self.batch_data["questions"]],
        )
        self.assertEqual(manifest["human_review_status"], "PENDING")
        self.assertFalse(manifest["golden_dataset_status"])

    def test_all_12_topics_represented_equally(self):
        topics = [q["topic"] for q in self.batch_data["questions"]]
        topic_counts = Counter(topics)
        self.assertEqual(set(topic_counts.keys()), EXPECTED_TOPICS)
        for topic, count in topic_counts.items():
            self.assertEqual(count, 3, f"Topic '{topic}' should have exactly 3 questions, got {count}")

    def test_balanced_answer_key_distribution(self):
        answers = [q["correct_answer"] for q in self.batch_data["questions"]]
        counts = Counter(answers)
        self.assertEqual(set(counts.keys()), {"A", "B", "C", "D", "E"})
        for key in ("A", "B", "C", "D", "E"):
            self.assertGreaterEqual(counts[key], 6, f"Answer key '{key}' under-represented ({counts[key]})")
            self.assertLessEqual(counts[key], 9, f"Answer key '{key}' over-represented ({counts[key]})")

    def test_every_question_passes_plab_validation_gates(self):
        for q_data in self.batch_data["questions"]:
            qid = q_data["question_id"]
            choices = tuple(
                PLABChoice(id=c["id"], text=c["text"])
                for c in q_data["choices"]
            )
            citations = tuple(
                PLABCitation(
                    ref=cit["ref"],
                    document_id=cit["document_id"],
                    quote=cit["quote"],
                )
                for cit in q_data["citations"]
            )

            question = PLABQuestion(
                question_id=qid,
                stem=q_data["stem"],
                choices=choices,
                correct_answer=q_data["correct_answer"],
                explanation=q_data["explanation"],
                specialty=q_data["specialty"],
                topic=q_data["topic"],
                learning_objective=q_data["learning_objective"],
                difficulty=q_data["difficulty"],
                citations=citations,
                status=PLABQuestionStatus(q_data.get("status", "needs_review")),
                schema_version=q_data.get("schema_version", "plab-question-v1"),
            )

            # Check exact evidence grounding in chunk store
            evidence_texts = []
            for cit in question.citations:
                self.assertIn(
                    cit.ref,
                    self.chunk_index,
                    f"Question {qid} references missing chunk {cit.ref}",
                )
                chunk = self.chunk_index[cit.ref]
                self.assertEqual(
                    cit.document_id,
                    chunk["document_id"],
                    f"Question {qid} document mismatch for {cit.ref}",
                )
                norm_quote = " ".join(cit.quote.casefold().split())
                norm_chunk = " ".join(chunk["text"].casefold().split())
                self.assertIn(
                    norm_quote,
                    norm_chunk,
                    f"Question {qid} quote not found in chunk {cit.ref}",
                )
                evidence_texts.append(chunk["text"])

            errors = validate_plab_question(question, evidence_texts)
            self.assertEqual(errors, [], f"Question {qid} failed validation gates: {errors}")


if __name__ == "__main__":
    unittest.main()
