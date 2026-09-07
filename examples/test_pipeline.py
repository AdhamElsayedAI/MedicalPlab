import json
from dataclasses import asdict
from pathlib import Path
from datetime import datetime

from medicalplab.stage_b.backend import LocalQwenBackend
from medicalplab.stage_b.evidence_loader import load_top10_evidence
from medicalplab.stage_b.pipeline import StageBPipeline


EVIDENCE_FILE = (
    "Data/processed/cardiology/"
    "DOC-WHO-CARD-0001.chunks.json"
)


QUERY = """
What is hypertension and how is it defined?
"""


RUN_DIR = Path("runs")
RUN_DIR.mkdir(exist_ok=True)



def save_json(path, data):

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )



def main():

    started = datetime.now()


    print("Loading evidence...")

    packet = load_top10_evidence(
        EVIDENCE_FILE
    )

    print(
        "Evidence blocks:",
        len(packet),
    )



    print(
        "Loading local Qwen backend..."
    )

    backend = LocalQwenBackend()



    pipeline = StageBPipeline(
        backend
    )



    print(
        "Running Stage-B pipeline..."
    )


    result = pipeline.run(
        QUERY,
        packet,
    )



    print("\n=== CLAIMS ===")


    claims_output = []


    for claim in result.claims:

        print("----------------")

        print(
            "ID:",
            claim.claim_id,
        )

        print(
            "Status:",
            claim.status,
        )

        print(
            "Text:",
            claim.text,
        )


        print(
            "Citations:"
        )


        citations = []


        for citation in claim.citations:

            print(
                citation.ref
            )

            print(
                citation.quote[:200]
            )


            citations.append(
                asdict(citation)
            )


        claims_output.append(
            {
                "claim_id": claim.claim_id,
                "text": claim.text,
                "status": claim.status.value,
                "citations": citations,
                "bindings": [
                    asdict(b)
                    for b in claim.bindings
                ],
                "reason": claim.reason,
            }
        )



    print("\n=== METADATA ===")

    print(
        result.metadata
    )


    print("\n=== VERDICT ===")

    print(
        result.verdict
    )



    finished = datetime.now()



    trace_file = (
        RUN_DIR /
        "stage_b_trace.json"
    )


    result_file = (
        RUN_DIR /
        "stage_b_result.json"
    )



    save_json(
        trace_file,
        pipeline.trace,
    )



    save_json(
        result_file,
        {
            "query": QUERY,
            "started": started.isoformat(),
            "finished": finished.isoformat(),
            "verdict": result.verdict,
            "claims": claims_output,
            "metadata": asdict(
                result.metadata
            ),
            "policy_downgrades": list(
                result.policy_downgrades
            ),
        },
    )



    print("\n=== SAVED ===")

    print(
        "Trace:",
        trace_file,
    )

    print(
        "Result:",
        result_file,
    )



if __name__ == "__main__":
    main()