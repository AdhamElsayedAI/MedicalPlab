"""Persist V1 DEV rankings and failure categories without reading V1 heldout."""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data"
DEV = ROOT / "evaluation" / "renal" / "renal-dev-v1.json"
OUT = ROOT / "reports" / "renal_v1_dev_failure_analysis.json"
MODEL = "Qwen/Qwen3-Embedding-0.6B"
INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "


def relevant(chunk: dict, query: dict) -> bool:
    if chunk["document_id"] not in query["gold_document_ids"]:
        return False
    gold = {str(value).casefold() for value in query.get("gold_section_ids", [])}
    actual = {str(value).casefold() for value in chunk.get("section_path", [])}
    return not gold or bool(gold & actual)


def categorize(query: dict, retrieved: list[dict]) -> str | None:
    if any(relevant(item["chunk"], query) for item in retrieved):
        return None
    gold_docs = set(query["gold_document_ids"])
    same_doc = [item for item in retrieved if item["chunk"]["document_id"] in gold_docs]
    if same_doc:
        if any(any(word in " ".join(item["chunk"].get("section_path", [])).casefold() for word in ("method", "result", "statistical")) for item in same_doc):
            return "METHODS_RESULTS_NOISE"
        return "RIGHT_DOCUMENT_WRONG_SECTION"
    if query.get("multi_source"):
        return "MULTI_SOURCE"
    if any(token in query["query"].upper().split() for token in ("AKI", "CKD", "GFR", "UTI", "RRT", "ADH", "RAAS")):
        return "ABBREVIATION"
    if query["query"].startswith(("Explain ", "For a medical student, summarize")):
        return "QUERY_TEMPLATE_ARTIFACT"
    return "WRONG_DOCUMENT"


def main() -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer

    queries = json.loads(DEV.read_text(encoding="utf-8"))["queries"]
    registry = json.loads((DATA / "metadata" / "renal_source_registry_v1.json").read_text(encoding="utf-8"))
    metadata = {item["document_id"]: item for item in registry["documents"] if item["status"] == "accepted"}
    chunks: list[dict] = []
    folder = DATA / "experiments" / "renal" / "chunking" / "C_section_aware"
    for path in sorted(folder.glob("*.chunks.json")):
        chunks.extend(json.loads(path.read_text(encoding="utf-8"))["chunks"])
    rendered = [
        f"Topics: {', '.join(metadata[item['document_id']]['topic_tags'])}\n"
        f"Section: {' > '.join(item.get('section_path', []))}\n"
        f"Source: {metadata[item['document_id']]['title']} [{item['document_id']}]\n{item['text']}"
        for item in chunks
    ]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(MODEL, device=device, local_files_only=True)
    model.max_seq_length = 512
    corpus = model.encode(rendered, batch_size=16, normalize_embeddings=True, show_progress_bar=True)
    rows = []
    for query in queries:
        embedding = model.encode([INSTRUCTION + query["query"]], normalize_embeddings=True, show_progress_bar=False)[0]
        scores = corpus @ embedding
        indices = np.argsort(scores)[::-1][:10]
        retrieved = [{"chunk": chunks[int(index)], "score": float(scores[int(index)])} for index in indices]
        first_gold = next((rank for rank, item in enumerate(retrieved, 1) if relevant(item["chunk"], query)), None)
        category = categorize(query, retrieved)
        rows.append({
            "query_id": query["query_id"], "query": query["query"], "topic": query["topic"],
            "gold_document_ids": query["gold_document_ids"], "gold_section_ids": query["gold_section_ids"],
            "gold_chunk_ids": query["gold_chunk_ids"], "first_gold_rank": first_gold,
            "failure_category": category,
            "top_10": [{
                "rank": rank, "score": item["score"], "chunk_id": item["chunk"]["chunk_id"],
                "document_id": item["chunk"]["document_id"], "section_path": item["chunk"].get("section_path", []),
            } for rank, item in enumerate(retrieved, 1)],
        })
    failures = Counter(row["failure_category"] for row in rows if row["failure_category"])
    payload = {
        "report_id": "RENAL-V1-DEV-FAILURE-ANALYSIS", "dataset": "RENAL-DEV-v1", "n": len(rows),
        "architecture": {"model": MODEL, "chunking": "C_section_aware", "representation": "metadata_aware", "max_sequence_length": 512},
        "failure_definition": "no gold-document plus gold-section match in top 10",
        "failure_count": sum(failures.values()),
        "failure_categories": {key: {"count": value, "percentage_of_failures": value / sum(failures.values())} for key, value in sorted(failures.items())},
        "queries": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"n": len(rows), "failures": payload["failure_count"], "categories": payload["failure_categories"]}, indent=2))


if __name__ == "__main__":
    main()
