"""Stage-C Pipeline for Question Generation.

Orchestrates generation, parsing, strict provenance validation, and retry handling.
"""

from dataclasses import asdict
import json
import time
from typing import Sequence
import uuid

from medicalplab.stage_b.models import (
    ContractError,
    require,
    strict_json,
)
from .generator import parse_generated_questions
from .models import EvidenceBlock, GeneratedQuestion
from .prompts import QUESTION_GENERATOR
from .validator import validate_question


class ModelFailure(RuntimeError):
    pass


class StageCPipeline:

    def __init__(self, backend):
        self.backend = backend
        self.trace = []

    def generate(self, system: str, user: str) -> dict:
        try:
            result = self.backend.generate(system, user)
            require(isinstance(result, dict), "Backend response must be dictionary")
            require("text" in result, "Backend response missing text")
            return result
        except Exception as e:
            raise ModelFailure(f"{type(e).__name__}: {e}") from e

    def generate_json_safe(
        self,
        system: str,
        user: str,
        retries: int = 2,
    ) -> dict:
        last_error = None
        original_user = user

        for attempt in range(retries + 1):
            try:
                prompt = original_user
                if attempt > 0:
                    prompt = (
                        original_user
                        + f"\n\nIMPORTANT (Attempt {attempt + 1}):\n"
                        f"Previous output failed validation with error: {last_error}\n"
                        "Return ONLY valid JSON matching the exact schema. "
                        "Every question MUST have citations with exact quotes from the supplied evidence. "
                        "No markdown. No explanation."
                    )

                result = self.generate(system, prompt)
                text = result["text"].strip()
                strict_json(text)
                return result

            except Exception as e:
                last_error = e

        raise ModelFailure(f"JSON generation failed: {last_error}")

    def generate_questions(
        self,
        packet: Sequence[EvidenceBlock],
        count: int = 1,
        topic: str | None = None,
        difficulty: str | None = None,
    ) -> tuple[GeneratedQuestion, ...]:
        """Generate, parse, and validate evidence-grounded medical MCQs from evidence blocks."""
        require(
            isinstance(packet, (list, tuple)) and len(packet) >= 1,
            "Evidence packet must contain at least 1 block",
        )
        require(count >= 1, "Count must be >= 1")

        run_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Build payload for LLM
        evidence_payload = [
            {
                "ref": b.ref,
                "document_id": b.document_id,
                "heading": b.heading,
                "section": b.section,
                "text": b.text,
            }
            for b in packet
        ]

        user_input = {
            "requested_count": count,
            "topic": topic or "General Cardiology / Hypertension",
            "target_difficulty": difficulty or "medium",
            "evidence": evidence_payload,
        }

        raw_result = self.generate_json_safe(
            QUESTION_GENERATOR,
            json.dumps(user_input, ensure_ascii=False),
        )

        # Parse generated questions
        questions = parse_generated_questions(raw_result["text"])

        # Validate each question against the evidence packet
        validated = []
        for q in questions:
            validate_question(q, packet)
            validated.append(q)

        elapsed = time.perf_counter() - start_time

        self.trace.append(
            {
                "run_id": run_id,
                "stage": "question_generation",
                "count": len(validated),
                "seconds": elapsed,
                "raw": raw_result,
            }
        )

        return tuple(validated)
