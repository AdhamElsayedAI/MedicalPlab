"""Tests for MedicalPlab Renal V3 retrieval, safety, and integrity invariants."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
QRELS_V3_PATH = ROOT / "evaluation" / "renal" / "v3" / "renal-dev-v3-qrels.json"
TRAIN_V3_PATH = ROOT / "evaluation" / "renal" / "v3" / "renal-train-v3.json"
HELDOUT_V2_PATH = ROOT / "evaluation" / "renal" / "renal-heldout-v2-final.json"
CONFIG_V3_PATH = ROOT / "reports" / "renal_v3" / "renal_v3_final_config.json"
CORPUS_SNAPSHOT_PATH = ROOT / "Data" / "metadata" / "corpus_renal_snapshot_v2.json"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
ABLATION_PATH = ROOT / "reports" / "renal_v3" / "renal_v3_ablation.json"
SAFETY_REPORT_PATH = ROOT / "reports" / "renal_v3" / "renal_v3_safety.json"


def test_qrels_v3_integrity():
    """Verify V3 DEV qrels structure, non-emptiness, and SHA sidecar."""
    assert QRELS_V3_PATH.exists(), "Missing renal-dev-v3-qrels.json"
    sidecar = QRELS_V3_PATH.with_suffix(".json.sha256")
    assert sidecar.exists(), "Missing QRELS SHA sidecar"
    
    sha_expected = sidecar.read_text(encoding="utf-8").split()[0]
    sha_actual = hashlib.sha256(QRELS_V3_PATH.read_bytes()).hexdigest()
    assert sha_actual == sha_expected, f"QRELS SHA mismatch: {sha_actual} vs {sha_expected}"
    
    data = json.loads(QRELS_V3_PATH.read_text(encoding="utf-8"))
    queries = data.get("queries", [])
    assert len(queries) >= 69
    
    answerable = [q for q in queries if q.get("answerable")]
    assert len(answerable) == 69
    for q in answerable:
        assert q.get("medical_claim"), f"Query {q['query_id']} missing claim"
        assert len(q.get("gold_document_ids", [])) > 0
        assert len(q.get("gold_parent_section_ids", [])) > 0
        assert len(q.get("gold_child_chunk_ids", [])) > 0


def test_train_dev_zero_leakage():
    """Enforce strict separation: ZERO overlap in query text, claim, or gold section between TRAIN and DEV."""
    assert TRAIN_V3_PATH.exists(), "Missing renal-train-v3.json"
    train_data = json.loads(TRAIN_V3_PATH.read_text(encoding="utf-8"))
    dev_data = json.loads(QRELS_V3_PATH.read_text(encoding="utf-8"))
    
    train_queries = train_data.get("queries", [])
    dev_queries = dev_data.get("queries", [])
    
    assert len(train_queries) >= 40
    
    train_texts = {q["query"].strip().lower() for q in train_queries}
    dev_texts = {q["query"].strip().lower() for q in dev_queries}
    assert len(train_texts.intersection(dev_texts)) == 0, "Query text overlap detected!"
    
    train_claims = {q["medical_claim"].strip().lower() for q in train_queries if q.get("medical_claim")}
    dev_claims = {q["medical_claim"].strip().lower() for q in dev_queries if q.get("medical_claim")}
    assert len(train_claims.intersection(dev_claims)) == 0, "Medical claim overlap detected!"
    
    train_sections = {s for q in train_queries for s in q.get("gold_parent_section_ids", [])}
    dev_sections = {s for q in dev_queries for s in q.get("gold_parent_section_ids", [])}
    assert len(train_sections.intersection(dev_sections)) == 0, "Gold parent section overlap detected!"


def test_heldout_v2_firewall_unmodified():
    """Verify that renal-heldout-v2-final.json remains untampered and matches its frozen SHA256."""
    assert HELDOUT_V2_PATH.exists(), "Missing heldout v2 file"
    sidecar = HELDOUT_V2_PATH.with_suffix(".json.sha256")
    assert sidecar.exists(), "Missing heldout v2 sidecar"
    
    expected_sha = sidecar.read_text(encoding="utf-8").split()[0]
    actual_sha = hashlib.sha256(HELDOUT_V2_PATH.read_bytes()).hexdigest()
    assert actual_sha == expected_sha, f"Heldout V2 was modified! {actual_sha} != {expected_sha}"
    assert actual_sha == "8885b21bc1174ea6a05028c03813d4aa1e72cfb5ecbd254a7e08c56bf8c29b92"



def test_v3_final_config_integrity():
    """Verify that V3 final configuration matches its SHA256 sidecar and specifies required components."""
    assert CONFIG_V3_PATH.exists(), "Missing renal_v3_final_config.json"
    sidecar = CONFIG_V3_PATH.with_suffix(".json.sha256")
    assert sidecar.exists(), "Missing config SHA sidecar"
    
    expected_sha = sidecar.read_text(encoding="utf-8").split()[0]
    actual_sha = hashlib.sha256(CONFIG_V3_PATH.read_bytes()).hexdigest()
    assert actual_sha == expected_sha
    
    cfg = json.loads(CONFIG_V3_PATH.read_text(encoding="utf-8"))
    assert cfg["chunking"]["strategy"] == "B_400_overlap"
    assert cfg["first_stage_retriever"]["structural_prior"] == "soft_document_prior"
    assert cfg["first_stage_retriever"]["alpha_document_prior"] == 0.18
    assert cfg["second_stage_reranker"]["enabled"] is True
    assert cfg["second_stage_reranker"]["candidate_depth"] == 20


def test_corpus_snapshot_and_registry():
    """Verify active corpus contains 23 documents under commercial CC BY licenses."""
    assert CORPUS_SNAPSHOT_PATH.exists()
    assert REGISTRY_PATH.exists()
    
    reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    docs = reg.get("documents", [])
    assert len(docs) == 23
    for d in docs:
        assert d.get("commercial_reuse_status") == "APPROVED"
        assert "CC BY" in d.get("license_name", "")


def test_ablation_superiority_decision():
    """Confirm that the chosen V3 retrieval architecture outperforms baseline on DEV."""
    assert ABLATION_PATH.exists()
    abl = json.loads(ABLATION_PATH.read_text(encoding="utf-8"))
    stages = {s["stage"]: s for s in abl.get("stages", [])}
    
    baseline = stages["A_flat_dense_baseline"]["metrics"]
    doc_prior = stages["D_global_dense_plus_doc_prior"]["metrics"]
    reranker = stages["H_qwen3_reranker_on_doc_prior"]["metrics"]
    
    # Doc prior improves over baseline
    assert doc_prior["hit_at_1"]["value"] > baseline["hit_at_1"]["value"]
    assert doc_prior["mrr"] > baseline["mrr"]
    
    # Reranker on doc prior improves further
    assert reranker["hit_at_1"]["value"] > doc_prior["hit_at_1"]["value"]
    assert reranker["mrr"] > doc_prior["mrr"]
    assert reranker["hit_at_1"]["value"] >= 0.49


def test_safety_report_integrity():
    """Verify safety evaluation report metrics and SHA sidecar."""
    assert SAFETY_REPORT_PATH.exists()
    sidecar = SAFETY_REPORT_PATH.with_suffix(".json.sha256")
    assert sidecar.exists()
    
    expected_sha = sidecar.read_text(encoding="utf-8").split()[0]
    actual_sha = hashlib.sha256(SAFETY_REPORT_PATH.read_bytes()).hexdigest()
    assert actual_sha == expected_sha
    
    rep = json.loads(SAFETY_REPORT_PATH.read_text(encoding="utf-8"))
    m = rep["metrics"]
    assert m["precision"] > 0.70
    assert m["auroc"] > 0.80
    assert rep["n_samples"] == 66


def test_qwen_renal_retriever_v3_contract():
    """Verify QwenRenalRetrieverV3 imports and satisfies the RenalRetriever protocol."""
    from medicalplab.learn.renal_retrieval import QwenRenalRetrieverV3, RenalRetrievalHit
    retriever = QwenRenalRetrieverV3(ROOT / "Data", alpha_doc_prior=0.18, candidate_depth=20)
    assert retriever.alpha_doc_prior == 0.18
    assert retriever.candidate_depth == 20
