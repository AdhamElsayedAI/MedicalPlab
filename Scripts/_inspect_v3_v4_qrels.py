import json
from pathlib import Path

v3 = json.loads(Path("evaluation/renal/v3/renal-dev-v3-qrels.json").read_text(encoding="utf-8"))
q3 = v3["queries"][0]
print("V3 query 0 keys:", list(q3.keys()))
print("V3 gold_child_chunk_ids:", q3.get("gold_child_chunk_ids"))
print("V3 gold_parent_section_ids:", q3.get("gold_parent_section_ids"))
print("V3 gold_document_ids:", q3.get("gold_document_ids"))

v4 = json.loads(Path("evaluation/renal/v4/renal-retrieval-dev-v4.json").read_text(encoding="utf-8"))
q4 = v4["queries"][0]
print("\nV4 query 0 keys:", list(q4.keys()))
print("V4 gold_child_chunk_ids:", q4.get("gold_child_chunk_ids"))
print("V4 gold_parent_section_ids:", q4.get("gold_parent_section_ids"))
print("V4 gold_document_ids:", q4.get("gold_document_ids"))
