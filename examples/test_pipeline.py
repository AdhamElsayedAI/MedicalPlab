from medicalplab.stage_b.backend import LocalQwenBackend
from medicalplab.stage_b.evidence_loader import load_top10_evidence
from medicalplab.stage_b.pipeline import StageBPipeline


EVIDENCE_FILE = (
    "Data/processed/cardiology/"
    "DOC-WHO-CARD-0001.chunks.json"
)


query = """
What is hypertension and how is it defined?
"""


print("Loading evidence...")

packet = load_top10_evidence(EVIDENCE_FILE)

print("Evidence blocks:", len(packet))


print("Loading local Qwen backend...")

backend = LocalQwenBackend()


pipeline = StageBPipeline(backend)


print("Running Stage-B pipeline...")


result = pipeline.run(
    query,
    packet
)


print("\n=== CLAIMS ===")

for claim in result.claims:
    print("----------------")
    print("ID:", claim.claim_id)
    print("Status:", claim.status)
    print("Text:", claim.text)

    print("Citations:")
    for c in claim.citations:
        print(c.ref)
        print(c.quote[:200])


print("\n=== METADATA ===")
print(result.metadata)


print("\n=== VERDICT ===")
print(result.verdict)