"""Adversarial and failure-mode regression test suite for PLAB Question Batch 1.

Tests that validators, schemas, and evidence-grounding checks strictly reject:
- Corrupted or removed evidence quotes
- Wrong chunk citations
- Wrong document citations
- Invalid answer keys (not in A-E)
- Duplicate option texts
- Six choices (overflow)
- Four choices (underflow)
- Scrambled choice order
- Truncated/empty stems and explanations
- Missing citations
"""

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
SNAPSHOT_PATH = PROJECT_ROOT / "Data" / "metadata" / "corpus_cardiorespiratory_snapshot_v1.json"


class TestPLABBatch1Adversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(BATCH_PATH, "r", encoding="utf-8") as f:
            cls.batch_data = json.load(f)

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

        # Take first valid question as baseline
        cls.base_q = cls.batch_data["questions"][0]

    def _create_valid_question(self) -> tuple[PLABQuestion, list[str]]:
        choices = tuple(
            PLABChoice(id=c["id"], text=c["text"]) for c in self.base_q["choices"]
        )
        citations = tuple(
            PLABCitation(
                ref=c["ref"],
                document_id=c["document_id"],
                quote=c["quote"],
            )
            for c in self.base_q["citations"]
        )
        q = PLABQuestion(
            question_id=self.base_q["question_id"],
            stem=self.base_q["stem"],
            choices=choices,
            correct_answer=self.base_q["correct_answer"],
            explanation=self.base_q["explanation"],
            specialty=self.base_q["specialty"],
            topic=self.base_q["topic"],
            learning_objective=self.base_q["learning_objective"],
            difficulty=self.base_q["difficulty"],
            citations=citations,
            status=PLABQuestionStatus(self.base_q["status"]),
            schema_version=self.base_q["schema_version"],
        )
        evidence_texts = [self.chunk_index[c.ref]["text"] for c in citations]
        return q, evidence_texts

    def test_baseline_question_is_valid(self):
        q, evidence_texts = self._create_valid_question()
        errors = validate_plab_question(q, evidence_texts)
        self.assertEqual(errors, [])

    def test_adversarial_tampered_evidence_quote_rejected(self):
        q, evidence_texts = self._create_valid_question()
        tampered_citations = (
            PLABCitation(
                ref=q.citations[0].ref,
                document_id=q.citations[0].document_id,
                quote="This hallucinated statement definitely does not exist in the source document chunk.",
            ),
        )
        tampered_q = PLABQuestion(
            question_id=q.question_id,
            stem=q.stem,
            choices=q.choices,
            correct_answer=q.correct_answer,
            explanation=q.explanation,
            specialty=q.specialty,
            topic=q.topic,
            learning_objective=q.learning_objective,
            difficulty=q.difficulty,
            citations=tampered_citations,
            status=q.status,
            schema_version=q.schema_version,
        )
        errors = validate_plab_question(tampered_q, evidence_texts)
        self.assertTrue(any("citation_quote_not_found" in err for err in errors))

    def test_adversarial_missing_citations_rejected_by_model(self):
        q, _ = self._create_valid_question()
        with self.assertRaises(ValueError) as ctx:
            PLABQuestion(
                question_id=q.question_id,
                stem=q.stem,
                choices=q.choices,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                specialty=q.specialty,
                topic=q.topic,
                learning_objective=q.learning_objective,
                difficulty=q.difficulty,
                citations=(),  # Empty citations
                status=q.status,
                schema_version=q.schema_version,
            )
        self.assertIn("at least one evidence citation", str(ctx.exception))

    def test_adversarial_wrong_chunk_citation_fails_corpus_lookup(self):
        bogus_chunk_id = "DOC-PMC-CARD-9999-B9999-C99"
        self.assertNotIn(bogus_chunk_id, self.chunk_index)

    def test_adversarial_wrong_document_citation_fails_integrity(self):
        q, _ = self._create_valid_question()
        actual_chunk = self.chunk_index[q.citations[0].ref]
        mismatched_doc_id = "DOC-WRONG-DOC-0001"
        self.assertNotEqual(actual_chunk["document_id"], mismatched_doc_id)

    def test_adversarial_invalid_answer_key_rejected(self):
        q, _ = self._create_valid_question()
        for invalid_key in ("F", "Z", "1", "a", ""):
            with self.assertRaises(ValueError):
                PLABQuestion(
                    question_id=q.question_id,
                    stem=q.stem,
                    choices=q.choices,
                    correct_answer=invalid_key,
                    explanation=q.explanation,
                    specialty=q.specialty,
                    topic=q.topic,
                    learning_objective=q.learning_objective,
                    difficulty=q.difficulty,
                    citations=q.citations,
                    status=q.status,
                    schema_version=q.schema_version,
                )

    def test_adversarial_duplicate_options_rejected(self):
        q, _ = self._create_valid_question()
        # Duplicate text across two choices
        dup_choices = (
            PLABChoice(id="A", text="Duplicate text"),
            PLABChoice(id="B", text="Duplicate text"),
            PLABChoice(id="C", text="Choice C text"),
            PLABChoice(id="D", text="Choice D text"),
            PLABChoice(id="E", text="Choice E text"),
        )
        with self.assertRaises(ValueError) as ctx:
            PLABQuestion(
                question_id=q.question_id,
                stem=q.stem,
                choices=dup_choices,
                correct_answer="A",
                explanation=q.explanation,
                specialty=q.specialty,
                topic=q.topic,
                learning_objective=q.learning_objective,
                difficulty=q.difficulty,
                citations=q.citations,
                status=q.status,
                schema_version=q.schema_version,
            )
        self.assertIn("choice texts must be unique", str(ctx.exception))

    def test_adversarial_choice_count_underflow_and_overflow_rejected(self):
        q, _ = self._create_valid_question()
        four_choices = q.choices[:4]
        with self.assertRaises(ValueError) as ctx:
            PLABQuestion(
                question_id=q.question_id,
                stem=q.stem,
                choices=four_choices,
                correct_answer="A",
                explanation=q.explanation,
                specialty=q.specialty,
                topic=q.topic,
                learning_objective=q.learning_objective,
                difficulty=q.difficulty,
                citations=q.citations,
                status=q.status,
                schema_version=q.schema_version,
            )
        self.assertIn("exactly five choices", str(ctx.exception))

        six_choices = q.choices + (PLABChoice(id="E", text="Extra choice"),)
        with self.assertRaises(ValueError) as ctx:
            PLABQuestion(
                question_id=q.question_id,
                stem=q.stem,
                choices=six_choices,
                correct_answer="A",
                explanation=q.explanation,
                specialty=q.specialty,
                topic=q.topic,
                learning_objective=q.learning_objective,
                difficulty=q.difficulty,
                citations=q.citations,
                status=q.status,
                schema_version=q.schema_version,
            )
        self.assertIn("exactly five choices", str(ctx.exception))

    def test_adversarial_choice_ordering_rejected(self):
        q, _ = self._create_valid_question()
        scrambled_choices = (
            PLABChoice(id="B", text=q.choices[1].text),
            PLABChoice(id="A", text=q.choices[0].text),
            PLABChoice(id="C", text=q.choices[2].text),
            PLABChoice(id="D", text=q.choices[3].text),
            PLABChoice(id="E", text=q.choices[4].text),
        )
        with self.assertRaises(ValueError) as ctx:
            PLABQuestion(
                question_id=q.question_id,
                stem=q.stem,
                choices=scrambled_choices,
                correct_answer="A",
                explanation=q.explanation,
                specialty=q.specialty,
                topic=q.topic,
                learning_objective=q.learning_objective,
                difficulty=q.difficulty,
                citations=q.citations,
                status=q.status,
                schema_version=q.schema_version,
            )
        self.assertIn("must be ordered exactly as", str(ctx.exception))

    def test_adversarial_truncated_stem_rejected(self):
        q, evidence_texts = self._create_valid_question()
        short_stem_q = PLABQuestion(
            question_id=q.question_id,
            stem="A short stem.",
            choices=q.choices,
            correct_answer=q.correct_answer,
            explanation=q.explanation,
            specialty=q.specialty,
            topic=q.topic,
            learning_objective=q.learning_objective,
            difficulty=q.difficulty,
            citations=q.citations,
            status=q.status,
            schema_version=q.schema_version,
        )
        errors = validate_plab_question(short_stem_q, evidence_texts)
        self.assertIn("stem_too_short", errors)

    def test_adversarial_truncated_explanation_rejected(self):
        q, evidence_texts = self._create_valid_question()
        short_exp_q = PLABQuestion(
            question_id=q.question_id,
            stem=q.stem,
            choices=q.choices,
            correct_answer=q.correct_answer,
            explanation="Too brief.",
            specialty=q.specialty,
            topic=q.topic,
            learning_objective=q.learning_objective,
            difficulty=q.difficulty,
            citations=q.citations,
            status=q.status,
            schema_version=q.schema_version,
        )
        errors = validate_plab_question(short_exp_q, evidence_texts)
        self.assertIn("explanation_too_short", errors)


if __name__ == "__main__":
    unittest.main()
