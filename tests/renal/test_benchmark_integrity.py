"""Adversarial provenance checks use synthetic text, never clinical ground truth."""
import csv
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Scripts"))
from qwen4b_adaptation_common import literal_span_in_text, load_chunks, load_config, sha256_tree
import validate_product_dev_v3_adjudication as adjudication
import build_product_dev_v3_reconstruction_packets as packets


@pytest.mark.parametrize("span,text,expected", [
    ("value < 60", "The value < 60 is recorded.", True),
    ("value > 60", "The value < 60 is recorded.", False),
    ("not supported", "supported", False),
    ("supported with invented additions", "supported", False),
    ("supported", "", False),
    ("", "supported", False),
    ("two words", "two\n words", True),
])
def test_literal_evidence_is_directional_and_preserves_symbols(span, text, expected):
    assert literal_span_in_text(span, text) is expected


def test_duplicate_chunk_id_never_overwrites_source(tmp_path):
    payload = {"document_id": "D", "chunks": [{"chunk_id": "C", "text": "source"}]}
    (tmp_path / "a.chunks.json").write_text(json.dumps(payload))
    (tmp_path / "b.chunks.json").write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="DUPLICATE_CHUNK_ID"):
        load_chunks(tmp_path)


def test_corpus_hash_changes_on_text_edit(tmp_path):
    source = tmp_path / "a.chunks.json"
    source.write_text("source")
    before = sha256_tree(tmp_path)
    source.write_text("changed")
    assert sha256_tree(tmp_path) != before


@pytest.fixture
def review_case(tmp_path, monkeypatch):
    original = {
        "query_id": "Q1", "query": "What is stated?", "canonical_claim": "source claim",
        "gold_document_id": "D", "exact_gold_chunk_ids": ["C"],
        "semantic_support_chunk_ids": ["C"], "evidence_span": "source claim",
        "provenance": "BLUEPRINT_EXPANSION_SPEC",
    }
    source = tmp_path / "benchmark.json"
    source.write_text(json.dumps([original]))
    summary = tmp_path / "product_dev_v3_reconstruction" / "summary.json"
    summary.parent.mkdir()
    summary.write_text(json.dumps({"benchmark_sha256": "sha", "locked_corpus_sha256_tree": "tree", "selected_item_n": 1}))
    cfg = {"data": {"product_dev_v3": str(source)}, "outputs": {"root": str(tmp_path)}}
    chunks = {"C": {"document_id": "D", "text": "source claim"}, "X": {"document_id": "OTHER", "text": "other claim"}}
    monkeypatch.setattr(adjudication, "verify_product_dev_sha", lambda _: "sha")
    monkeypatch.setattr(adjudication, "resolve_corpus_dir", lambda _: tmp_path)
    monkeypatch.setattr(adjudication, "sha256_tree", lambda _: "tree")
    monkeypatch.setattr(adjudication, "load_chunks", lambda _: (chunks, list(chunks)))
    row = {
        "query_id": "Q1", "query": original["query"], "canonical_claim": original["canonical_claim"],
        "provenance": original["provenance"], "declared_gold_document_id": "D",
        "declared_document_present_in_locked_corpus": "True",
        "original_exact_gold_chunk_ids": "C", "original_semantic_support_chunk_ids": "C",
        "review_decision": "KEEP", "reviewer": "synthetic-test-reviewer",
        "review_notes": "Synthetic fixture only", "source_support_status": "SUPPORTED",
    }
    return cfg, row, tmp_path / "review.csv"


def validate_case(case):
    cfg, row, path = case
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    return adjudication.validate(cfg, path)


def test_valid_review_is_idempotent_and_does_not_claim_clinician_approval(review_case):
    result = validate_case(review_case)
    assert result["adjudication_complete"]
    assert result["clinician_review_status"] == "NOT_ESTABLISHED_BY_THIS_VALIDATOR"
    assert validate_case(review_case) == result


@pytest.mark.parametrize("field,value", [
    ("query_id", "UNKNOWN"), ("original_exact_gold_chunk_ids", "X"),
    ("original_semantic_support_chunk_ids", "X"), ("declared_gold_document_id", "OTHER"),
    ("query", "Different question"), ("canonical_claim", "Different claim"),
    ("source_support_status", ""),
])
def test_review_cannot_forge_original_or_missing_support(review_case, field, value):
    review_case[1][field] = value
    with pytest.raises(SystemExit) as error:
        validate_case(review_case)
    assert error.value.code == 2


def test_repair_rejects_fabricated_extension(review_case):
    review_case[1].update(review_decision="REPAIR", correct_gold_document_id="D",
                          correct_exact_gold_chunk_ids="C", correct_semantic_support_chunk_ids="C",
                          correct_evidence_span="source claim plus fabricated extension")
    with pytest.raises(SystemExit):
        validate_case(review_case)


def test_config_rejects_unapproved_model_revision(tmp_path):
    cfg = json.loads((Path(__file__).resolve().parents[2] / "configs/qwen4b_domain_adaptation.json").read_text())
    cfg["model"]["revision"] = "a" * 40
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match="AUTHORIZED_MODEL_REVISION_MISMATCH"):
        load_config(path)


def test_packet_rebuild_preserves_existing_review_directory(tmp_path, monkeypatch):
    items = [{"query_id": f"Q{i}", "provenance": "BLUEPRINT_EXPANSION_SPEC"} for i in range(31)]
    source = tmp_path / "benchmark.json"
    source.write_text(json.dumps(items))
    monkeypatch.setattr(packets, "verify_product_dev_sha", lambda _: "sha")
    monkeypatch.setattr(packets, "resolve_corpus_dir", lambda _: tmp_path)
    monkeypatch.setattr(packets, "load_chunks", lambda _: ({}, []))
    monkeypatch.setattr(packets, "_load_audit", lambda _: {"items": [dict(i, provenance_alignment_flags=["review"]) for i in items]})
    output = tmp_path / "product_dev_v3_reconstruction"
    output.mkdir()
    sentinel = output / "review.csv"
    sentinel.write_text("irreplaceable review")
    with pytest.raises(FileExistsError):
        packets.build({"data": {"product_dev_v3": str(source)}, "outputs": {"root": str(tmp_path)}})
    assert sentinel.read_text() == "irreplaceable review"
