from dataclasses import asdict

import json
import time
import uuid

from .claim_planner import parse_plan
from .evidence_policy import validate_and_apply
from .models import ModelRunMetadata, StageBResult, require
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
            result = self.backend.generate(system, user)

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



    def run(self, query, packet):

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
        # Planner Stage
        # =============================

        planner_start = time.perf_counter()


        plan = self.generate(
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
            - planner_start
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
        # Verifier Stage
        # =============================


        verifier_start = time.perf_counter()


        verification = self.generate(
            VERIFIER,
            json.dumps(
                {
                    "query": query,
                    "claims": [
                        asdict(c)
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
            - verifier_start
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
        # Evidence Policy Validation
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
            - start
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
                x.get("input_tokens", 0)
                for x in [
                    self.trace[0]["raw"],
                    self.trace[1]["raw"],
                ]
            ),
            sum(
                x.get("output_tokens", 0)
                for x in [
                    self.trace[0]["raw"],
                    self.trace[1]["raw"],
                ]
            ),
            planner_seconds,
            verifier_seconds,
            total_seconds,
            self.backend.peak_vram(),
        )


        self.trace.append(
            {
                "run_id": run_id,
                "stage": "complete",
                "seconds": total_seconds,
                "verdict": [
                    {
                        "claim_id": c.claim_id,
                        "status": c.status.value,
                    }
                    for c in final
                ],
            }
        )


        return StageBResult(
            tuple(final),
            tuple(downgrades),
            metadata,
        )