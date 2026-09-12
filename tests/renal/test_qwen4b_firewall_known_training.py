import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_qwen4b_train_firewall as fw


def _record(query_id, query="What is CKD?", claim="claim A", gold=("D-B-C0001",)):
    return {
        "query_id": query_id,
        "query": query,
        "canonical_claim": claim,
        "gold_chunk_ids": list(gold),
    }


def _cfg(tmp_path):
    return {
        "data": {
            "source_pool": str(tmp_path / "approved-source.json"),
            "known_training_artifacts": [
                "evaluation/renal/v7/renal-train-dev-v7.json",
            ],
            "forbidden_eval_globs": [
                "evaluation/renal/**/*dev*.json",
            ],
        }
    }


def test_known_train_dev_artifact_is_ignored_only_after_source_pool_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(fw, "ROOT", tmp_path)
    cfg = _cfg(tmp_path)
    source = Path(cfg["data"]["source_pool"])
    source.write_text(json.dumps([_record("V5-RNK-TRAIN-0001")]), encoding="utf-8")

    known = tmp_path / "evaluation/renal/v7/renal-train-dev-v7.json"
    known.parent.mkdir(parents=True)
    known.write_text(json.dumps([_record("V7-TRN-0001")]), encoding="utf-8")

    true_dev = tmp_path / "evaluation/renal/v5/renal-rerank-dev-a-v5.json"
    true_dev.parent.mkdir(parents=True)
    true_dev.write_text(json.dumps([_record("V5-RNK-DEV-A-0001", query="Held-out dev question", claim="dev claim", gold=("X-B-C0009",))]), encoding="utf-8")

    files = fw.eval_files(cfg)
    relative = {str(p.relative_to(tmp_path)).replace("\\", "/") for p in files}

    assert "evaluation/renal/v7/renal-train-dev-v7.json" not in relative
    assert "evaluation/renal/v5/renal-rerank-dev-a-v5.json" in relative


def test_known_training_artifact_rejects_non_train_id(tmp_path, monkeypatch):
    monkeypatch.setattr(fw, "ROOT", tmp_path)
    cfg = _cfg(tmp_path)
    Path(cfg["data"]["source_pool"]).write_text(json.dumps([_record("V5-RNK-TRAIN-0001")]), encoding="utf-8")

    known = tmp_path / "evaluation/renal/v7/renal-train-dev-v7.json"
    known.parent.mkdir(parents=True)
    known.write_text(json.dumps([_record("V7-DEV-0001")]), encoding="utf-8")

    with pytest.raises(RuntimeError, match="NON_TRAIN_ID"):
        fw.eval_files(cfg)


def test_known_training_artifact_rejects_record_not_in_approved_source_pool(tmp_path, monkeypatch):
    monkeypatch.setattr(fw, "ROOT", tmp_path)
    cfg = _cfg(tmp_path)
    Path(cfg["data"]["source_pool"]).write_text(json.dumps([_record("V5-RNK-TRAIN-0001")]), encoding="utf-8")

    known = tmp_path / "evaluation/renal/v7/renal-train-dev-v7.json"
    known.parent.mkdir(parents=True)
    known.write_text(
        json.dumps([_record("V7-TRN-0001", claim="different claim")]),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="NOT_IN_APPROVED_SOURCE_POOL"):
        fw.eval_files(cfg)
