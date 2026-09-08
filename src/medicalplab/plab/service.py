"""Evidence-grounded PLAB question service built on the existing Stage-C backend/retry layer."""

from __future__ import annotations

import json
from typing import Sequence

from medicalplab.stage_c.models import EvidenceBlock
from medicalplab.stage_c.pipeline import StageCPipeline

from .models import PLABCitation, PLABChoice, PLABQuestion, PLABQuestionStatus
from .validation import validate_plab_question


PLAB_GENERATOR_PROMPT = """
You are MedicalPlab's PLAB 1 single-best-answer assessment generator.

Create questions ONLY from the supplied evidence. Do not use outside medical
knowledge. Every correct answer and explanation must be supported by the cited
evidence. If the evidence is insufficient, return an empty questions array.

PLAB PRODUCT FORMAT:
- short clinically realistic scenario/stem;
- exactly five options A, B, C, D, E;
- exactly one single best answer;
- original wording; never copy public sample questions;
- difficulty: easy, medium, or hard;
- at least one citation containing an exact quote from a supplied evidence block;
- explanation must explain the best answer from the supplied evidence;
- distractors must be distinct and must not be stated as correct by the supplied evidence.

Return ONLY valid JSON with this shape:
{
  "questions": [
    {
      "question_id": "PLAB-CARD-0001",
      "stem": "...",
      "choices": [
        {"id":"A","text":"..."},
        {"id":"B","text":"..."},
        {"id":"C","text":"..."},
        {"id":"D","text":"..."},
        {"id":"E","text":"..."}
      ],
      "correct_answer": "A",
      "explanation": "...",
      "specialty": "Cardiology",
      "topic": "...",
      "learning_objective": "...",
      "difficulty": "medium",
      "citations": [
        {"ref":"DOC:B0001","document_id":"DOC","quote":"exact evidence quote"}
      ]
    }
  ]
}
"""


class PLABGenerationError(RuntimeError):
    pass


class PLABQuestionService:
    """Generate five-option PLAB questions without replacing Stage-C infrastructure."""

    def __init__(self, backend):
        self.stage_c = StageCPipeline(backend)
        self.trace: list[dict] = []

    def generate(
        self,
        evidence: Sequence[EvidenceBlock],
        specialty: str,
        topic: str,
        difficulty: str = "medium",
        count: int = 1,
        learning_objective: str | None = None,
    ) -> tuple[PLABQuestion, ...]:
        if not evidence:
            raise PLABGenerationError("Evidence packet must not be empty")
        if count < 1 or count > 20:
            raise PLABGenerationError("count must be between 1 and 20")
        if difficulty not in {"easy", "medium", "hard"}:
            raise PLABGenerationError("difficulty must be easy, medium, or hard")

        payload = {
            "requested_count": count,
            "specialty": specialty,
            "topic": topic,
            "difficulty": difficulty,
            "learning_objective": learning_objective,
            "evidence": [
                {
                    "ref": block.ref,
                    "document_id": block.document_id,
                    "source": block.source,
                    "heading": block.heading,
                    "section": block.section,
                    "text": block.text,
                }
                for block in evidence
            ],
        }

        raw = self.stage_c.generate_json_safe(
            PLAB_GENERATOR_PROMPT,
            json.dumps(payload, ensure_ascii=False),
        )
        parsed = json.loads(raw["text"])
        raw_questions = parsed.get("questions")
        if not isinstance(raw_questions, list):
            raise PLABGenerationError("Model output must contain a questions array")

        evidence_by_ref = {block.ref: block for block in evidence}
        output: list[PLABQuestion] = []

        for item in raw_questions:
            if not isinstance(item, dict):
                raise PLABGenerationError("Each question must be a JSON object")

            citations = tuple(
                PLABCitation(
                    ref=str(citation["ref"]),
                    document_id=str(citation["document_id"]),
                    quote=str(citation["quote"]),
                )
                for citation in item.get("citations", [])
            )
            choices = tuple(
                PLABChoice(id=str(choice["id"]), text=str(choice["text"]))
                for choice in item.get("choices", [])
            )

            question = PLABQuestion(
                question_id=str(item["question_id"]),
                stem=str(item["stem"]),
                choices=choices,
                correct_answer=str(item["correct_answer"]),
                explanation=str(item["explanation"]),
                specialty=str(item.get("specialty") or specialty),
                topic=str(item.get("topic") or topic),
                learning_objective=str(
                    item.get("learning_objective")
                    or learning_objective
                    or topic
                ),
                difficulty=str(item.get("difficulty") or difficulty),
                citations=citations,
                status=PLABQuestionStatus.NEEDS_REVIEW,
            )

            citation_evidence: list[str] = []
            for citation in question.citations:
                block = evidence_by_ref.get(citation.ref)
                if block is None:
                    raise PLABGenerationError(
                        f"Citation ref not present in supplied evidence: {citation.ref}"
                    )
                if block.document_id != citation.document_id:
                    raise PLABGenerationError(
                        f"Citation document mismatch for {citation.ref}"
                    )
                normalized_quote = " ".join(citation.quote.casefold().split())
                normalized_text = " ".join(block.text.casefold().split())
                if normalized_quote not in normalized_text:
                    raise PLABGenerationError(
                        f"Citation quote not found in evidence block: {citation.ref}"
                    )
                citation_evidence.append(block.text)

            errors = validate_plab_question(question, citation_evidence)
            if errors:
                raise PLABGenerationError(
                    f"Question {question.question_id} failed PLAB validation: {errors}"
                )

            output.append(question)

        if len(output) > count:
            output = output[:count]

        self.trace.append(
            {
                "requested_count": count,
                "generated_count": len(output),
                "specialty": specialty,
                "topic": topic,
                "difficulty": difficulty,
                "stage_c_trace_count": len(self.stage_c.trace),
            }
        )
        return tuple(output)
