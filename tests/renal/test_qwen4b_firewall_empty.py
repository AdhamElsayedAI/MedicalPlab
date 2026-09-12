import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_qwen4b_train_firewall as fw


def test_semantic_check_empty_short_circuits_without_model_load():
    clean, excluded = fw.semantic_check([], {"model": {}, "data": {}})
    assert clean == []
    assert excluded == []


def test_run_preserves_built_train_when_lexical_firewall_removes_all(tmp_path, monkeypatch):
    train_path = tmp_path / "train.json"
    report_path = tmp_path / "firewall_report.json"
    original = [{
        "query_id": "T1",
        "query": "What is CKD?",
        "positive_passage_id": "D1-B-C0001",
        "positive_passage": "CKD evidence",
        "hard_negative_ids": ["D1-B-C0002"],
        "hard_negative_passages": ["wrong claim"],
    }]
    train_path.write_text(json.dumps(original), encoding="utf-8")
    before = train_path.read_bytes()

    cfg = {
        "data": {
            "train_output": str(train_path),
            "firewall_report": str(report_path),
        }
    }
    excluded = [{"query_id": "T1", "reasons": [{"type": "same_atomic_claim"}]}]
    monkeypatch.setattr(fw, "lexical_firewall", lambda train, cfg: ([], excluded, ["eval.json"], []))

    with pytest.raises(RuntimeError, match="TRAIN_FIREWALL_EMPTY"):
        fw.run(cfg)

    assert train_path.read_bytes() == before
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "TRAIN_FIREWALL_EMPTY"
    assert report["input_n"] == 1
    assert report["clean_n"] == 0
    assert report["train_sha256"] is None
    assert report["input_train_preserved"] is True
    assert report["semantic_check"] == "NOT_RUN_EMPTY_AFTER_LEXICAL"
    assert report["exclusion_reason_counts"] == {"same_atomic_claim": 1}
