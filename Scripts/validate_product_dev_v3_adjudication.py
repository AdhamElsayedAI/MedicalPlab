from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from qwen4b_adaptation_common import (
    load_chunks,
    load_config,
    literal_span_in_text,
    canonical_json_bytes,
    sha256_file,
    resolve_corpus_dir,
    root_path,
    sha256_tree,
    verify_product_dev_sha,
)

ALLOWED_DECISIONS = {"KEEP", "REPAIR", "REJECT"}
SYNTHETIC_PROVENANCE = {"BLUEPRINT_EXPANSION_SPEC", "BLUEPRINT_TARGETED_FILL"}


def _split_ids(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def _span_in_chunks(span: str, chunk_ids: list[str], chunks: dict) -> bool:
    return any(literal_span_in_text(span, chunks[cid].get("text", "")) for cid in chunk_ids)


def validate(cfg: dict, manifest_path: Path) -> dict:
    product_sha = verify_product_dev_sha(cfg)
    corpus_dir = resolve_corpus_dir(cfg)
    corpus_sha = sha256_tree(corpus_dir)
    chunks, _ = load_chunks(corpus_dir)
    originals = {
        item["query_id"]: item
        for item in json.loads(root_path(cfg["data"]["product_dev_v3"]).read_text(encoding="utf-8"))
        if item.get("provenance") in SYNTHETIC_PROVENANCE
    }

    summary_path = root_path(cfg["outputs"]["root"]) / "product_dev_v3_reconstruction" / "summary.json"
    if not summary_path.exists():
        raise RuntimeError("RECONSTRUCTION_SUMMARY_REQUIRED")
    reconstruction = json.loads(summary_path.read_text(encoding="utf-8"))
    if reconstruction.get("benchmark_sha256") != product_sha:
        raise RuntimeError("RECONSTRUCTION_BENCHMARK_SHA_MISMATCH")
    if reconstruction.get("locked_corpus_sha256_tree") != corpus_sha:
        raise RuntimeError("RECONSTRUCTION_CORPUS_SHA_MISMATCH")

    if not manifest_path.exists():
        raise FileNotFoundError(f"ADJUDICATION_MANIFEST_NOT_FOUND path={manifest_path}")

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    expected_n = len(originals)
    if reconstruction.get("selected_item_n") != expected_n:
        raise RuntimeError("RECONSTRUCTION_ITEM_COUNT_MISMATCH")
    if len(rows) != expected_n:
        raise RuntimeError(f"ADJUDICATION_ROW_COUNT_MISMATCH expected={expected_n} actual={len(rows)}")

    errors = []
    validated = []
    decision_counts = Counter()
    seen = set()

    for i, row in enumerate(rows, start=2):
        qid = (row.get("query_id") or "").strip()
        decision = (row.get("review_decision") or "").strip().upper()
        reviewer = (row.get("reviewer") or "").strip()
        notes = (row.get("review_notes") or "").strip()
        original = originals.get(qid, {})
        original_doc = original.get("gold_document_id", "")
        declared_present = any(ch["document_id"] == original_doc for ch in chunks.values())
        original_exact = original.get("exact_gold_chunk_ids", [])
        original_semantic = original.get("semantic_support_chunk_ids", [])
        corrected_doc = (row.get("correct_gold_document_id") or "").strip()
        corrected_exact = _split_ids(row.get("correct_exact_gold_chunk_ids") or "")
        corrected_semantic = _split_ids(row.get("correct_semantic_support_chunk_ids") or "")
        corrected_span = (row.get("correct_evidence_span") or "").strip()

        row_errors = []
        if not qid:
            row_errors.append("QUERY_ID_REQUIRED")
        elif qid in seen:
            row_errors.append("DUPLICATE_QUERY_ID")
        seen.add(qid)
        if qid not in originals:
            row_errors.append("UNKNOWN_QUERY_ID")
        elif (
            row.get("declared_gold_document_id", "").strip() != original_doc
            or _split_ids(row.get("original_exact_gold_chunk_ids", "")) != original_exact
            or _split_ids(row.get("original_semantic_support_chunk_ids", "")) != original_semantic
            or row.get("query") != original.get("query")
            or row.get("canonical_claim") != original.get("canonical_claim")
            or row.get("provenance") != original.get("provenance")
        ):
            row_errors.append("IMMUTABLE_SOURCE_FIELDS_CHANGED")

        if decision not in ALLOWED_DECISIONS:
            row_errors.append("DECISION_MUST_BE_KEEP_REPAIR_OR_REJECT")
        if not reviewer:
            row_errors.append("REVIEWER_REQUIRED")
        if not notes:
            row_errors.append("REVIEW_NOTES_REQUIRED")
        support_status = (row.get("source_support_status") or "").strip().upper()
        if support_status != ("SUPPORTED" if decision in {"KEEP", "REPAIR"} else "UNSUPPORTED"):
            row_errors.append("SOURCE_SUPPORT_STATUS_INCONSISTENT")

        if decision == "KEEP":
            if not declared_present:
                row_errors.append("KEEP_FORBIDDEN_DECLARED_DOCUMENT_MISSING")
            missing = [cid for cid in original_exact + original_semantic if cid not in chunks]
            if missing:
                row_errors.append("KEEP_FORBIDDEN_ORIGINAL_CHUNK_IDS_MISSING:" + ";".join(sorted(set(missing))))
            if not original_exact or not original_semantic:
                row_errors.append("KEEP_REQUIRES_NONEMPTY_QRELS")
            if not missing:
                if any(chunks[cid]["document_id"] != original_doc for cid in original_exact + original_semantic):
                    row_errors.append("KEEP_CHUNK_DOCUMENT_MISMATCH")
                if not _span_in_chunks(original.get("evidence_span", ""), original_semantic, chunks):
                    row_errors.append("KEEP_EVIDENCE_SPAN_NOT_LITERAL")
            if any([corrected_doc, corrected_exact, corrected_semantic, corrected_span]):
                row_errors.append("KEEP_MUST_NOT_SUPPLY_REPAIR_FIELDS")

        elif decision == "REPAIR":
            if not corrected_doc:
                row_errors.append("REPAIR_CORRECT_GOLD_DOCUMENT_ID_REQUIRED")
            if not corrected_exact:
                row_errors.append("REPAIR_EXACT_GOLD_CHUNK_IDS_REQUIRED")
            if not corrected_semantic:
                row_errors.append("REPAIR_SEMANTIC_SUPPORT_CHUNK_IDS_REQUIRED")
            if not corrected_span:
                row_errors.append("REPAIR_EVIDENCE_SPAN_REQUIRED")

            all_ids = corrected_exact + corrected_semantic
            missing = [cid for cid in all_ids if cid not in chunks]
            if missing:
                row_errors.append("REPAIR_CHUNK_IDS_NOT_IN_LOCKED_CORPUS:" + ";".join(sorted(set(missing))))
            if corrected_doc and not missing:
                wrong_doc = [cid for cid in all_ids if str(chunks[cid].get("document_id")) != corrected_doc]
                if wrong_doc:
                    row_errors.append("REPAIR_CHUNK_DOCUMENT_MISMATCH:" + ";".join(sorted(set(wrong_doc))))
            if corrected_span and corrected_semantic and not missing:
                if not _span_in_chunks(corrected_span, corrected_semantic, chunks):
                    row_errors.append("REPAIR_EVIDENCE_SPAN_NOT_LITERAL_IN_SEMANTIC_SUPPORT")

        elif decision == "REJECT":
            if any([corrected_doc, corrected_exact, corrected_semantic, corrected_span]):
                row_errors.append("REJECT_MUST_NOT_SUPPLY_REPAIR_FIELDS")

        if row_errors:
            errors.append({"csv_line": i, "query_id": qid, "errors": row_errors})
        else:
            decision_counts[decision] += 1
            validated.append({
                "query_id": qid,
                "decision": decision,
                "reviewer": reviewer,
                "review_notes": notes,
                "correct_gold_document_id": corrected_doc or None,
                "correct_exact_gold_chunk_ids": corrected_exact,
                "correct_semantic_support_chunk_ids": corrected_semantic,
                "correct_evidence_span": corrected_span or None,
            })

    if seen != set(originals):
        errors.append({"errors": ["ADJUDICATION_QUERY_ID_SET_MISMATCH"], "missing_query_ids": sorted(set(originals) - seen)})
    complete = len(errors) == 0 and len(validated) == expected_n
    result = {
        "status": "PRODUCT_DEV_V3_ADJUDICATION_VALIDATION_COMPLETE" if complete else "PRODUCT_DEV_V3_ADJUDICATION_VALIDATION_FAILED",
        "benchmark_sha256": product_sha,
        "manifest_sha256": sha256_file(manifest_path),
        "review_validation_scope": "STRUCTURE_AND_LITERAL_PROVENANCE_ONLY",
        "clinician_review_status": "NOT_ESTABLISHED_BY_THIS_VALIDATOR",
        "locked_corpus_path": str(corpus_dir),
        "locked_corpus_sha256_tree": corpus_sha,
        "expected_item_n": expected_n,
        "validated_item_n": len(validated),
        "error_item_n": len(errors),
        "decision_counts": dict(sorted(decision_counts.items())),
        "adjudication_complete": complete,
        "benchmark_mutated": False,
        "replacement_benchmark_created": False,
        "model_weights_loaded": False,
        "benchmark_rerun": False,
        "training_run": False,
        "reranker_authorized": False,
        "errors": errors,
        "validated_decisions": validated if complete else [],
        "next_state": "READY_FOR_VERSIONED_BENCHMARK_RECONSTRUCTION" if complete else "COMPLETE_BLIND_SOURCE_GROUNDED_ADJUDICATION",
    }

    out = root_path(cfg["outputs"]["root"]) / "adjudication_validations" / (result["manifest_sha256"] + ".json")
    out.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json_bytes(result)
    if out.exists():
        if out.read_bytes() != data:
            raise FileExistsError(f"VALIDATION_ARTIFACT_ALREADY_EXISTS path={out}")
    else:
        with out.open("xb") as stream:
            stream.write(data)
    print(json.dumps({k: v for k, v in result.items() if k not in {"errors", "validated_decisions"}}, indent=2))
    if errors:
        print(json.dumps({"errors": errors[:20]}, indent=2))
        raise SystemExit(2)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--manifest", default="artifacts/qwen4b_domain_adaptation/product_dev_v3_reconstruction/adjudication_manifest_blind.csv")
    args = ap.parse_args()
    validate(load_config(args.config), root_path(args.manifest))
