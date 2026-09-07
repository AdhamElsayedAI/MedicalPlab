import json
from pathlib import Path

from medicalplab.stage_b.backend import LocalQwenBackend
from medicalplab.stage_b.evidence_loader import load_top10_evidence
from medicalplab.stage_b.pipeline import StageBPipeline


QUESTIONS_FILE = Path(
    "evaluation/questions.json"
)

EVIDENCE_FILE = (
    "Data/processed/cardiology/"
    "DOC-WHO-CARD-0001.chunks.json"
)


OUTPUT_FILE = Path(
    "evaluation/results.json"
)



def main():

    print("Loading questions...")

    with open(
        QUESTIONS_FILE,
        encoding="utf-8"
    ) as f:
        questions = json.load(f)



    print("Loading evidence...")

    packet = load_top10_evidence(
        EVIDENCE_FILE
    )


    print(
        "Evidence blocks:",
        len(packet)
    )


    print(
        "Loading backend..."
    )

    backend = LocalQwenBackend()

    pipeline = StageBPipeline(
        backend
    )



    results = []



    for item in questions:

        print("\n================")
        print(
            "Running:",
            item["id"]
        )

        result = pipeline.run(
            item["question"],
            packet
        )


        results.append(
            {
                "id": item["id"],
                "question": item["question"],
                "expected": item["expected"],
                "verdict": result.verdict,
                "claims": [
                    {
                        "id": c.claim_id,
                        "status": c.status.value,
                        "text": c.text,
                    }
                    for c in result.claims
                ],
                "metadata": {
                    "latency":
                        result.metadata.total_seconds,
                    "model":
                        result.metadata.model,
                },
            }
        )



    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2,
        )


    print("\n================")
    print("Evaluation finished")
    print(
        "Saved:",
        OUTPUT_FILE
    )



if __name__ == "__main__":
    main()