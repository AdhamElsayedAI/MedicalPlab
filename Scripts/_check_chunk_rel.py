"""Check relevance mapping across all chunking strategies."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEV_PATH = ROOT / "evaluation" / "renal" / "renal-dev-v2.json"
queries = [q for q in json.loads(DEV_PATH.read_text(encoding="utf-8"))["queries"] if q.get("answerable")]

def parent_id(chunk):
    if chunk.get("parent_section_id"):
        return str(chunk["parent_section_id"])
    if "source_block_index" in chunk:
        return f"{chunk['document_id']}-P{int(chunk['source_block_index']):04d}"
    return None

def is_relevant(chunk, query):
    if chunk.get("document_id") not in set(query.get("gold_document_ids", [])):
        return False
    cid = chunk.get("child_chunk_id") or chunk.get("chunk_id")
    if cid in set(query.get("gold_child_chunk_ids", [])):
        return True
    if parent_id(chunk) in set(query.get("gold_parent_section_ids", [])):
        return True
    return False

for name in ("A_250", "B_400_overlap", "C_section_aware", "E_sentence_evidence_300"):
    folder = ROOT / f"Data/experiments/renal_v2/chunking/{name}"
    chunks = []
    for f in folder.glob("*.chunks.json"):
        chunks.extend(json.loads(f.read_text(encoding="utf-8"))["chunks"])
    rel_counts = [sum(is_relevant(c, q) for c in chunks) for q in queries]
    zero_rel = sum(1 for rc in rel_counts if rc == 0)
    print(f"{name:<25}: {len(chunks)} chunks, zero_rel queries: {zero_rel}/{len(queries)}")
