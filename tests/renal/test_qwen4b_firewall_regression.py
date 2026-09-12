from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "Scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_qwen4b_train_firewall as fw


def _record(hard_ids, hard_texts):
    return {
        "query_id": "T1",
        "query": "How is renal disease assessed?",
        "atomic_claim": "renal assessment",
        "positive_passage_id": "SAFE-B-C0001",
        "positive_passage": "A safe source-grounded positive passage.",
        "hard_negative_ids": hard_ids,
        "hard_negative_passages": hard_texts,
        "hard_negative_categories": ["x"] * len(hard_ids),
    }


def test_firewall_sanitizes_leaking_hard_negative_without_dropping_safe_row(monkeypatch):
    monkeypatch.setattr(
        fw,
        "extract_eval",
        lambda cfg: ([], [], [], {"EVAL-B-C0002"}, ["evaluation/mock.json"]),
    )
    train = [_record(["EVAL-B-C0002", "SAFE-B-C0009"], ["leaking negative", "safe negative"])]
    clean, excluded, sources, sanitized = fw.lexical_firewall(train, {"data": {"near_duplicate_threshold": 0.86}})
    assert excluded == []
    assert sources == ["evaluation/mock.json"]
    assert len(clean) == 1
    assert clean[0]["hard_negative_ids"] == ["SAFE-B-C0009"]
    assert clean[0]["hard_negative_passages"] == ["safe negative"]
    assert sanitized[0]["removed_hard_negative_count"] == 1


def test_firewall_excludes_row_if_no_safe_hard_negative_remains(monkeypatch):
    monkeypatch.setattr(
        fw,
        "extract_eval",
        lambda cfg: ([], [], [], {"EVAL-B-C0002"}, ["evaluation/mock.json"]),
    )
    train = [_record(["EVAL-B-C0002"], ["leaking negative"])]
    clean, excluded, _, sanitized = fw.lexical_firewall(train, {"data": {"near_duplicate_threshold": 0.86}})
    assert clean == []
    assert sanitized[0]["kept_hard_negative_count"] == 0
    reason_types = {r["type"] for r in excluded[0]["reasons"]}
    assert "no_safe_hard_negatives_after_firewall" in reason_types


def test_semantic_check_empty_input_short_circuits_without_cuda():
    assert fw.semantic_check([], {}) == ([], [])
