"""Stage-D Pipeline for Medical Tutor Reasoning Layer.

Orchestrates intent classification, pedagogical prompt dispatch, JSON generation,
response parsing, and strict clinical safety/provenance validation.
"""

import json
import time
from typing import Sequence
import uuid

from medicalplab.stage_b.models import (
    ContractError,
    require,
    strict_json,
)
from .intent import classify_intent
from .models import (
    ConfidenceLevel,
    EvidenceBlock,
    TutorMode,
    TutorRequest,
    TutorResponse,
)
from .prompts import TUTOR_PROMPT
from .tutor import parse_tutor_response
from .validator import validate_tutor_response


class ModelFailure(RuntimeError):
    pass


class StageDPipeline:
    """End-to-end evidence-grounded Medical Tutor reasoning pipeline."""

    def __init__(self, backend):
        self.backend = backend
        self.trace = []

    def generate(self, system: str, user: str) -> dict:
        """Execute generation on the backend with basic validation."""
        try:
            result = self.backend.generate(system, user)
            require(isinstance(result, dict), "Backend response must be dictionary")
            require("text" in result, "Backend response missing 'text' field")
            return result
        except Exception as e:
            raise ModelFailure(f"{type(e).__name__}: {e}") from e

    def generate_json_safe(
        self,
        system: str,
        user: str,
        retries: int = 2,
    ) -> dict:
        """Generate with JSON validation and automated recovery retries."""
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
                        "Every claim must cite literal quotes from the supplied evidence blocks. "
                        "Do not recommend unsupported treatments or doses. No markdown wrapping."
                    )

                result = self.generate(system, prompt)
                text = result["text"].strip()
                strict_json(text)
                return result

            except Exception as e:
                last_error = e

        raise ModelFailure(f"JSON generation failed: {last_error}")

    def run(self, request: TutorRequest) -> TutorResponse:
        """Execute tutor reasoning for a given request.

        1. Classifies intent if mode is not specified.
        2. Dispatches pedagogical prompt grounded in evidence.
        3. Parses response into TutorResponse domain model.
        4. Validates citation provenance and clinical safety.
        """
        require(isinstance(request, TutorRequest), "request must be a TutorRequest instance")

        run_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # 1. Resolve pedagogical mode
        if request.mode is not None:
            resolved_mode = request.mode
        else:
            resolved_mode = classify_intent(
                request.query,
                request.context,
                backend=self.backend,
            )

        # 2. Build structured prompt payload
        evidence_payload = [
            {
                "ref": b.ref,
                "document_id": b.document_id,
                "heading": b.heading,
                "section": b.section,
                "text": b.text,
            }
            for b in request.evidence
        ]

        user_input = {
            "query": request.query,
            "mode": resolved_mode.value,
            "context": request.context or "",
            "evidence": evidence_payload,
        }

        # 3. Generate JSON
        raw_result = self.generate_json_safe(
            TUTOR_PROMPT,
            json.dumps(user_input, ensure_ascii=False),
        )

        # 4. Parse response
        response = parse_tutor_response(
            raw_result["text"],
            query=request.query,
            mode=resolved_mode,
        )

        # 5. Validate provenance and clinical safety
        validate_tutor_response(response, request.evidence)

        elapsed = time.perf_counter() - start_time

        self.trace.append(
            {
                "run_id": run_id,
                "stage": "stage_d_tutor",
                "mode": resolved_mode.value,
                "query": request.query,
                "citations_count": len(response.citations),
                "confidence": response.confidence.value,
                "seconds": elapsed,
            }
        )

        return response

    def ask(
        self,
        query: str,
        evidence: Sequence[EvidenceBlock],
        mode: TutorMode | None = None,
        context: str | None = None,
    ) -> TutorResponse:
        """Convenience wrapper to ask the tutor directly."""
        req = TutorRequest(
            query=query,
            evidence=tuple(evidence),
            mode=mode,
            context=context,
        )
        return self.run(req)
