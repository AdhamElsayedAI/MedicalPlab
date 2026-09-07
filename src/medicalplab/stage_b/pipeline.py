from dataclasses import asdict

import json
import time
import uuid

from .claim_planner import parse_plan
from .evidence_policy import validate_and_apply
from .models import ModelRunMetadata, StageBResult, require, strict_json
from .prompts import PLANNER, VERIFIER
from .verifier import parse_verification


class ModelFailure(RuntimeError):
    pass



class StageBPipeline:


    def __init__(self, backend):

        self.backend = backend
        self.trace = []



    def generate(self, system, user):

        try:

            result = self.backend.generate(
                system,
                user,
            )


            require(
                isinstance(result, dict),
                "Backend response must be dictionary",
            )


            require(
                "text" in result,
                "Backend response missing text",
            )


            return result


        except Exception as e:

            raise ModelFailure(
                f"{type(e).__name__}: {e}"
            ) from e



    def generate_json_safe(
        self,
        system,
        user,
        retries=2,
    ):

        last_error = None

        original_user = user

        for attempt in range(retries + 1):

            try:

                prompt = original_user
                if attempt > 0:
                    prompt = (
                        original_user
                        + "\n\nIMPORTANT:\n"
                        "Return ONLY valid JSON. "
                        "No markdown. "
                        "No explanation."
                    )

                result = self.generate(
                    system,
                    prompt,
                )


                text = result["text"].strip()


                strict_json(text)

                return result


            except Exception as e:

                last_error = e


        raise ModelFailure(
            f"JSON generation failed: {last_error}"
        )


    def run(
        self,
        query,
        packet,
    ):

        self.trace = []


        run_id = str(uuid.uuid4())


        require(
            isinstance(query, str)
            and query.strip(),
            "Empty query",
        )


        require(
            len(packet) == 10
            and len({b.ref for b in packet}) == 10,
            "Exactly Top-10 unique blocks required",
        )


        start = time.perf_counter()


        documents = {
            b.document_id: b.source
            for b in packet
        }



        # =============================
        # Planner
        # =============================


        planner_start = time.perf_counter()


        plan = self.generate_json_safe(
            PLANNER,
            json.dumps(
                {
                    "query": query,
                    "documents": documents,
                },
                ensure_ascii=False,
            ),
        )


        print("\n===== RAW PLANNER OUTPUT =====")
        print(plan["text"])
        print("===== END PLANNER OUTPUT =====\n")



        claims = parse_plan(
            plan["text"],
            query,
            documents,
        )


        planner_seconds = (
            time.perf_counter()
            -
            planner_start
        )


        self.trace.append(
            {
                "run_id": run_id,
                "stage": "planner",
                "raw": plan,
                "parsed_claims": [
                    asdict(c)
                    for c in claims
                ],
                "seconds": planner_seconds,
            }
        )



        # =============================
        # Verifier
        # =============================


        verifier_start = time.perf_counter()


        verification = self.generate_json_safe(
            VERIFIER,
            json.dumps(
                {
                    "query": query,
                    "claims": [
                        {
                            "claim_id": c.claim_id,
                            "text": c.text,
                        }
                        for c in claims
                    ],
                    "evidence": [
                        asdict(b)
                        for b in packet
                    ],
                },
                ensure_ascii=False,
            ),
        )


        print("\n===== RAW VERIFIER OUTPUT =====")
        print(verification["text"])
        print("===== END VERIFIER OUTPUT =====\n")



        judgments = parse_verification(
            verification["text"],
            claims,
        )



        verifier_seconds = (
            time.perf_counter()
            -
            verifier_start
        )



        self.trace.append(
            {
                "run_id": run_id,
                "stage": "verifier",
                "raw": verification,
                "parsed_judgments": [
                    asdict(j)
                    for j in judgments
                ],
                "seconds": verifier_seconds,
            }
        )



        # =============================
        # Policy
        # =============================


        final = []
        downgrades = []


        for claim, judgment in zip(
            claims,
            judgments,
        ):

            checked, reasons = validate_and_apply(
                claim,
                judgment,
                packet,
            )


            final.append(checked)


            downgrades.extend(
                f"{claim.claim_id}:{reason}"
                for reason in reasons
            )



        total_seconds = (
            time.perf_counter()
            -
            start
        )



        # =============================
        # Metadata
        # =============================


        metadata = ModelRunMetadata(
            self.backend.model,
            self.backend.revision,
            getattr(
                self.backend,
                "quantization",
                "AWQ 4-bit",
            ),
            sum(
                x["raw"].get(
                    "input_tokens",
                    0
                )
                for x in self.trace
                if "raw" in x
            ),
            sum(
                x["raw"].get(
                    "output_tokens",
                    0
                )
                for x in self.trace
                if "raw" in x
            ),
            planner_seconds,
            verifier_seconds,
            total_seconds,
            self.backend.peak_vram(),
        )



        return StageBResult(
            tuple(final),
            tuple(downgrades),
            metadata,
        )