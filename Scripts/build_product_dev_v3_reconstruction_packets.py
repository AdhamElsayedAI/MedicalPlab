from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from qwen4b_adaptation_common import (
    atomic_json,
    load_chunks,
    load_config,
    resolve_corpus_dir,
    root_path,
    sha256_tree,
    verify_product_dev_sha,
)

SYNTHETIC_PROVENANCE = {"BLUEPRINT_EXPANSION_SPEC", "BLUEPRINT_TARGETED_FILL"}


def _load_audit(cfg: dict) -> dict:
    path = root_path(cfg["outputs"]["root"]) / "product_dev_v3_qrel_integrity_audit.json"
    if not path.exists():
        raise RuntimeError("QREL_INTEGRITY_AUDIT_REQUIRED")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("summary", {}).get("benchmark_sha256") != cfg["data"]["product_dev_v3_sha256"]:
        raise RuntimeError("QREL_AUDIT_SHA_MISMATCH")
    return obj


def _doc_chunks(chunks: dict, ordered: list[str]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for cid in ordered:
        ch = chunks[cid]
        grouped[str(ch.get("document_id"))].append(
            {
                "chunk_id": cid,
                "document_id": ch.get("document_id"),
                "document_title": ch.get("document_title"),
                "heading": ch.get("heading"),
                "section_path": ch.get("section_path"),
                "source_block_index": ch.get("source_block_index"),
                "text": ch.get("text", ""),
            }
        )
    return grouped


def build(cfg: dict, output_dir: Path | None = None) -> dict:
    product_sha = verify_product_dev_sha(cfg)
    corpus_dir = resolve_corpus_dir(cfg)
    chunks, ordered = load_chunks(corpus_dir)
    docs = _doc_chunks(chunks, ordered)
    audit = _load_audit(cfg)
    audit_rows = {str(r["query_id"]): r for r in audit.get("items", [])}
    items = json.loads(root_path(cfg["data"]["product_dev_v3"]).read_text(encoding="utf-8"))

    selected = []
    for it in items:
        qid = str(it.get("query_id"))
        row = audit_rows.get(qid)
        if row is None:
            raise RuntimeError(f"AUDIT_ROW_MISSING query_id={qid}")
        if it.get("provenance") not in SYNTHETIC_PROVENANCE:
            continue
        if not row.get("provenance_alignment_flags"):
            continue
        selected.append((it, row))

    if len(selected) != 31:
        raise RuntimeError(f"EXPECTED_31_SYNTHETIC_RECONSTRUCTION_ITEMS actual={len(selected)}")

    out_root = output_dir or root_path(cfg["outputs"]["root"]) / "product_dev_v3_reconstruction"
    packets_dir = out_root / "packets"
    # Review decisions are evidence. Never erase them when regenerating packets.
    out_root.mkdir(parents=True, exist_ok=False)
    packets_dir.mkdir()

    manifest_rows = []
    missing_declared_docs = []

    for it, row in selected:
        qid = str(it["query_id"])
        declared_doc = str(it.get("gold_document_id") or "")
        source_chunks = docs.get(declared_doc, [])
        if not source_chunks:
            missing_declared_docs.append(qid)

        packet = {
            "packet_version": "PRODUCT_DEV_V3_SOURCE_GROUNDED_RECONSTRUCTION_V1",
            "benchmark_sha256": product_sha,
            "locked_corpus_path": str(corpus_dir),
            "reviewer_blinding": "NO_MODEL_OUTPUTS_NO_RETRIEVAL_RANKS_NO_HEURISTIC_CANDIDATE_RANKING",
            "query_id": qid,
            "provenance": it.get("provenance"),
            "query": it.get("query"),
            "canonical_claim": it.get("canonical_claim"),
            "learning_objective": it.get("learning_objective"),
            "clinical_domain": it.get("clinical_domain"),
            "curriculum_category": it.get("curriculum_category"),
            "declared_gold_document_id": declared_doc,
            "original_exact_gold_chunk_ids": it.get("exact_gold_chunk_ids", []),
            "original_semantic_support_chunk_ids": it.get("semantic_support_chunk_ids", []),
            "original_evidence_span": it.get("evidence_span"),
            "hard_integrity_flags": row.get("hard_integrity_flags", []),
            "provenance_alignment_flags": row.get("provenance_alignment_flags", []),
            "declared_document_present_in_locked_corpus": bool(source_chunks),
            "declared_document_chunk_count": len(source_chunks),
            "declared_document_chunks_in_source_order": source_chunks,
            "adjudication": {
                "review_decision": "",
                "source_support_status": "",
                "correct_gold_document_id": "",
                "correct_exact_gold_chunk_ids": [],
                "correct_semantic_support_chunk_ids": [],
                "correct_evidence_span": "",
                "reviewer": "",
                "review_notes": "",
            },
        }
        packet_path = packets_dir / f"{qid}.json"
        atomic_json(packet_path, packet)

        manifest_rows.append(
            {
                "query_id": qid,
                "provenance": it.get("provenance"),
                "query": it.get("query"),
                "canonical_claim": it.get("canonical_claim"),
                "declared_gold_document_id": declared_doc,
                "declared_document_present_in_locked_corpus": bool(source_chunks),
                "declared_document_chunk_count": len(source_chunks),
                "original_exact_gold_chunk_ids": ";".join(str(x) for x in it.get("exact_gold_chunk_ids", [])),
                "original_semantic_support_chunk_ids": ";".join(str(x) for x in it.get("semantic_support_chunk_ids", [])),
                "hard_integrity_flags": ";".join(row.get("hard_integrity_flags", [])),
                "provenance_alignment_flags": ";".join(row.get("provenance_alignment_flags", [])),
                "packet_path": str(packet_path.relative_to(out_root)).replace("\\", "/"),
                "review_decision": "",
                "source_support_status": "",
                "correct_gold_document_id": "",
                "correct_exact_gold_chunk_ids": "",
                "correct_semantic_support_chunk_ids": "",
                "correct_evidence_span": "",
                "reviewer": "",
                "review_notes": "",
            }
        )

    manifest_path = out_root / "adjudication_manifest_blind.csv"
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as f:
        fields = list(manifest_rows[0].keys())
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(manifest_rows)

    summary = {
        "status": "PRODUCT_DEV_V3_SOURCE_GROUNDED_RECONSTRUCTION_PACKET_COMPLETE",
        "benchmark_sha256": product_sha,
        "locked_corpus_path": str(corpus_dir),
        "locked_corpus_sha256_tree": sha256_tree(corpus_dir),
        "selected_item_n": len(selected),
        "selected_provenance_labels": sorted(SYNTHETIC_PROVENANCE),
        "missing_declared_document_n": len(missing_declared_docs),
        "missing_declared_document_query_ids": missing_declared_docs,
        "reviewer_blinding": "NO_MODEL_OUTPUTS_NO_RETRIEVAL_RANKS_NO_HEURISTIC_CANDIDATE_RANKING",
        "benchmark_mutated": False,
        "model_weights_loaded": False,
        "benchmark_rerun": False,
        "training_run": False,
        "second_adaptation_authorized": False,
        "reranker_authorized": False,
        "instructions": (
            "Review each packet against the complete declared source document chunks in source order. "
            "Do not consult model outcomes or retrieval ranks. Mark KEEP, REPAIR, or REJECT and record "
            "source-grounded chunk ids/evidence. This tool never edits PRODUCT_DEV_V3."
        ),
    }
    atomic_json(out_root / "summary.json", summary)

    md = [
        "# PRODUCT_DEV_V3 Blind Source-Grounded Reconstruction",
        "",
        f"- Benchmark SHA256: `{product_sha}`",
        f"- Locked corpus: `{corpus_dir}`",
        f"- Locked corpus tree SHA256: `{summary['locked_corpus_sha256_tree']}`",
        f"- Items requiring reconstruction: {len(selected)}",
        f"- Missing declared source documents: {len(missing_declared_docs)}",
        "- Model outputs/ranks exposed to reviewer: **No**",
        "- Heuristic candidate ranking exposed to reviewer: **No**",
        "- PRODUCT_DEV_V3 mutated: **No**",
        "",
        "Use `adjudication_manifest_blind.csv` as the decision sheet and open the matching JSON packet for the full declared source document chunks.",
        "Allowed decisions: KEEP, REPAIR, REJECT.",
        "Do not create a replacement benchmark until all 31 items have independent source-grounded adjudication.",
        "",
    ]
    (out_root / "README.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--output-dir", type=Path, help="New directory; existing directories are never overwritten")
    args = ap.parse_args()
    build(load_config(args.config), args.output_dir)
