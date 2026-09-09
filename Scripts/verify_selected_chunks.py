"""Inspect and verify target chunks and exact sentences for the 36 questions."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
snapshot = json.load(open(PROJECT_ROOT / "Data/metadata/corpus_cardiorespiratory_snapshot_v1.json", encoding="utf-8"))
doc_map = {d["document_id"]: PROJECT_ROOT / d["chunks_file"] for d in snapshot["documents"]}

def get_chunk(doc_id, chunk_id):
    chunks = json.load(open(doc_map[doc_id], encoding="utf-8"))["chunks"]
    for c in chunks:
        if c["chunk_id"] == chunk_id:
            return c
    raise ValueError(f"Chunk {chunk_id} not found in {doc_id}")

# Let's inspect selected candidate chunks
selected = [
    # T1
    ("DOC-WHO-CARD-0001", "DOC-WHO-CARD-0001-B0001-C01"),
    ("DOC-PMC-CARD-0002", "DOC-PMC-CARD-0002-B0003-C01"),
    ("DOC-WHO-CARD-0001", "DOC-WHO-CARD-0001-B0001-C03"),
    # T2
    ("DOC-PMC-CARD-0008", "DOC-PMC-CARD-0008-B0015-C01"),
    ("DOC-PMC-CARD-0008", "DOC-PMC-CARD-0008-B0018-C01"),
    ("DOC-PMC-CARD-0008", "DOC-PMC-CARD-0008-B0011-C01"),
    # T3
    ("DOC-PMC-CARD-0009", "DOC-PMC-CARD-0009-B0009-C01"),
    ("DOC-PMC-CARD-0009", "DOC-PMC-CARD-0009-B0010-C01"),
    ("DOC-PMC-CARD-0009", "DOC-PMC-CARD-0009-B0020-C01"),
    # T4
    ("DOC-PMC-RESP-0003", "DOC-PMC-RESP-0003-B0020-C01"),
    ("DOC-PMC-RESP-0003", "DOC-PMC-RESP-0003-B0022-C01"),
    ("DOC-PMC-RESP-0003", "DOC-PMC-RESP-0003-B0010-C01"),
    # T5
    ("DOC-PMC-EMERG-0001", "DOC-PMC-EMERG-0001-B0001-C01"),
    ("DOC-PMC-EMERG-0001", "DOC-PMC-EMERG-0001-B0002-C01"),
    ("DOC-PMC-EMERG-0001", "DOC-PMC-EMERG-0001-B0005-C01"),
    # T6
    ("DOC-PMC-RESP-0004", "DOC-PMC-RESP-0004-B0001-C01"),
    ("DOC-PMC-RESP-0004", "DOC-PMC-RESP-0004-B0004-C01"),
    ("DOC-PMC-RESP-0004", "DOC-PMC-RESP-0004-B0030-C01"),
    # T7
    ("DOC-PMC-RESP-0005", "DOC-PMC-RESP-0005-B0014-C01"),
    ("DOC-PMC-RESP-0005", "DOC-PMC-RESP-0005-B0027-C01"),
    ("DOC-PMC-RESP-0005", "DOC-PMC-RESP-0005-B0025-C01"),
    # T8
    ("DOC-PMC-CARD-0010", "DOC-PMC-CARD-0010-B0041-C01"),
    ("DOC-PMC-CARD-0010", "DOC-PMC-CARD-0010-B0042-C01"),
    ("DOC-PMC-CARD-0010", "DOC-PMC-CARD-0010-B0023-C01"),
    # T9
    ("DOC-PMC-CARD-0011", "DOC-PMC-CARD-0011-B0032-C01"),
    ("DOC-PMC-CARD-0011", "DOC-PMC-CARD-0011-B0012-C01"),
    ("DOC-PMC-CARD-0011", "DOC-PMC-CARD-0011-B0020-C01"),
    # T10
    ("DOC-PMC-CARD-0012", "DOC-PMC-CARD-0012-B0002-C01"),
    ("DOC-PMC-CARD-0012", "DOC-PMC-CARD-0012-B0003-C01"),
    ("DOC-PMC-CARD-0012", "DOC-PMC-CARD-0012-B0006-C01"),
    # T11
    ("DOC-PMC-CARD-0013", "DOC-PMC-CARD-0013-B0001-C01"),
    ("DOC-PMC-CARD-0013", "DOC-PMC-CARD-0013-B0002-C01"),
    ("DOC-PMC-CARD-0013", "DOC-PMC-CARD-0013-B0029-C03"),
    # T12
    ("DOC-PMC-CARD-0014", "DOC-PMC-CARD-0014-B0001-C01"),
    ("DOC-PMC-CARD-0014", "DOC-PMC-CARD-0014-B0002-C01"),
    ("DOC-PMC-CARD-0014", "DOC-PMC-CARD-0014-B0022-C01"),
]

print(f"Total candidate chunks to verify: {len(selected)}")
for doc_id, cid in selected:
    c = get_chunk(doc_id, cid)
    print(f"[{doc_id}] {cid}: len={len(c['text'])} chars")
