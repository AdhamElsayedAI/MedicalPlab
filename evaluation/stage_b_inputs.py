"""Evaluation-only bridge: whitelist inputs; replay frozen Stage-A ranking."""

from collections import defaultdict
import hashlib
import json
from medicalplab.stage_b.models import EvidenceBlock, require

FROZEN = {
    "evaluation/evidence_sufficiency_calibration_v1.json": "4ece4e35de1f46888f75f4dcae624e34b8e8f2696959f162a5f434615b021ad5",
    "evaluation/results/evidence_sufficiency_retrieval_only_baseline_v1.json": "019a7098e3364782a5599ee570915d06bada01eb6af31d2f8dd6d1f212408cc8",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs(root):
    for name, expected in FROZEN.items():
        require(digest(root / name) == expected, f"Frozen SHA mismatch: {name}")
    cal, baseline = [json.loads((root / p).read_text(encoding="utf-8")) for p in FROZEN]
    require(
        baseline["retrieval"]["model"] == "Qwen/Qwen3-Embedding-0.6B"
        and baseline["retrieval"]["source_aware"] is True,
        "Unexpected retrieval",
    )
    catalog, corpus_hashes = {}, {}
    for doc in cal["corpus_document_ids"]:
        path = root / "Data/processed/cardiology" / f"{doc}.chunks.json"
        corpus_hashes[path.relative_to(root).as_posix()] = digest(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        grouped = defaultdict(list)
        for chunk in data["chunks"]:
            require(chunk["document_id"] == doc, "Chunk document mismatch")
            grouped[chunk["source_block_index"]].append(chunk)
        for index, chunks in grouped.items():
            chunks.sort(key=lambda c: c["chunk_index"])
            first = chunks[0]
            text = "\n".join(dict.fromkeys(c["text"].strip() for c in chunks))
            ref = f"{doc}:B{index:04d}"
            catalog[ref] = EvidenceBlock(
                ref,
                doc,
                data["title"],
                first.get("heading") or "",
                " > ".join(
                    first.get("retrieval_section_path")
                    or first.get("section_path")
                    or []
                ),
                text,
                first["block_type"],
            )
    rows = {r["case_id"]: r for r in baseline["cases"]}
    require(
        len(rows) == len(baseline["cases"]) == len(cal["cases"]),
        "Duplicate/missing retrieval rows",
    )
    require(set(rows) == {c["case_id"] for c in cal["cases"]}, "Case IDs mismatch")
    packets = {}
    for c in cal["cases"]:
        r = rows[c["case_id"]]
        keys = r["top_10_blocks"]
        require(
            len(keys) == len(set(keys)) == len(r["top_10_scores"]) == 10,
            "Top-10 violated",
        )
        packets[c["case_id"]] = tuple(catalog[k] for k in keys)
    return cal["cases"], packets, corpus_hashes
