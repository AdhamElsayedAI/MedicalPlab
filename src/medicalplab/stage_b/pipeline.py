from dataclasses import asdict
import json
import time
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
            return self.backend.generate(system, user)
        except Exception as e:
            raise ModelFailure(f"{type(e).__name__}: {e}") from e

    def run(self, query, packet):
        self.trace = []
        require(isinstance(query, str) and query.strip(), "Empty query")
        require(
            len(packet) == 10 and len({b.ref for b in packet}) == 10,
            "Exactly Top-10 unique blocks required",
        )
        start = time.perf_counter()
        documents = {b.document_id: b.source for b in packet}
        before = time.perf_counter()
        plan = self.generate(
            PLANNER,
            json.dumps({"query": query, "documents": documents}, ensure_ascii=False),
        )
        self.trace.append({"stage": "planner", **plan})
        claims = parse_plan(plan["text"], query, documents)
        planner_seconds = time.perf_counter() - before
        before = time.perf_counter()
        verification = self.generate(
            VERIFIER,
            json.dumps(
                {
                    "query": query,
                    "claims": [asdict(c) for c in claims],
                    "evidence": [asdict(b) for b in packet],
                },
                ensure_ascii=False,
            ),
        )
        self.trace.append({"stage": "verifier", **verification})
        judgments = parse_verification(verification["text"], claims)
        verifier_seconds = time.perf_counter() - before
        final, downgrades = [], []
        for claim, judgment in zip(claims, judgments):
            checked, reasons = validate_and_apply(claim, judgment, packet)
            final.append(checked)
            downgrades.extend(f"{claim.claim_id}:{r}" for r in reasons)
        metadata = ModelRunMetadata(
            self.backend.model,
            self.backend.revision,
            "AWQ 4-bit",
            sum(x["input_tokens"] for x in self.trace),
            sum(x["output_tokens"] for x in self.trace),
            planner_seconds,
            verifier_seconds,
            time.perf_counter() - start,
            self.backend.peak_vram(),
        )
        return StageBResult(tuple(final), tuple(downgrades), metadata)
