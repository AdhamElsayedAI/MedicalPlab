from medicalplab.stage_b.evidence_loader import load_top10_evidence


packet = load_top10_evidence(
    "Data/processed/cardiology/DOC-WHO-CARD-0001.chunks.json"
)

print("Blocks:", len(packet))

for b in packet:
    print(
        b.ref,
        b.document_id,
        b.heading,
        len(b.text)
    )