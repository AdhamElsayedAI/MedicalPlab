"""
MedicalPlab Renal V4 — Phase 19, 21, 24: Predeclared Safety Datasets Generator
=============================================================================
Author: Antigravity / Senior ML Systems & Medical AI Safety Engineer
Role: Construct fresh, unspent, firewall-isolated safety datasets:
- SAFETY_TRAIN_V4 (N=100: 50 positive [40 supported, 10 partial], 50 negative [20 coverage gap, 15 out-of-domain, 15 difficult perturbations])
- SAFETY_DEV_V4 (N=60: 30 positive [25 supported, 5 partial], 30 negative [10 coverage gap, 10 out-of-domain, 10 difficult perturbations])
- SAFETY_CALIBRATION_V4 (N=60: 30 positive [25 supported, 5 partial], 30 negative [10 coverage gap, 10 out-of-domain, 10 difficult perturbations])
- SAFETY_TEST_V4 (N=120: 60 positive [50 supported, 10 partial], 60 negative [20 coverage gap, 20 out-of-domain, 20 difficult perturbations])

Statistical Sizing Rationale (Section 27):
- 60 negatives in SAFETY_TEST_V4 guarantees that 0 observed unsafe accepts achieves
  a 95% one-sided Clopper-Pearson upper confidence bound of 4.88% <= 5.00%.
- Difficult negative stratum has N=20 (not single-digit).

Strict Scientific Discipline:
- Zero overlap with spent evaluation sets (V2 Heldout, V3 Heldout, V3.1 Safety Test-2, Spent V3 DEV).
- Zero overlap between TRAIN, DEV, CALIBRATION, and TEST.
- Group split by canonical medical claim / learning objective / source section / transformation family.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import sys
from pathlib import Path

if not hasattr(sys.stdout, "_is_wrapped"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stdout._is_wrapped = True

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "evaluation" / "renal" / "v4"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"

TRAIN_PATH = EVAL_DIR / "renal-safety-train-v4.json"
DEV_PATH = EVAL_DIR / "renal-safety-dev-v4.json"
CALIB_PATH = EVAL_DIR / "renal-safety-calibration-v4.json"
TEST_PATH = EVAL_DIR / "renal-safety-test-v4.json"


def normalize_text(t: str) -> str:
    if not t:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", t.lower())).strip()


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_spent_entities() -> tuple[set[str], set[str], set[str]]:
    spent_q = set()
    spent_c = set()
    spent_o = set()
    spent_files = [
        ROOT / "evaluation" / "renal" / "renal-heldout-v2-final.json",
        ROOT / "evaluation" / "renal" / "v3" / "renal-heldout-v3-final.json",
        ROOT / "evaluation" / "renal" / "v3" / "renal-v3-safety-test-2.json",
        ROOT / "evaluation" / "renal" / "v3" / "renal-dev-v3-qrels.json",
        ROOT / "evaluation" / "renal" / "renal-safety-test-v2.json",
        ROOT / "evaluation" / "renal" / "renal-calibration-v2.json",
        ROOT / "evaluation" / "renal" / "v4" / "renal-retrieval-dev-v4.json",
    ]
    for sf in spent_files:
        if sf.exists():
            data = json.loads(sf.read_text(encoding="utf-8"))
            for q in data.get("queries", []):
                if q.get("query"):
                    spent_q.add(normalize_text(q["query"]))
                if q.get("medical_claim"):
                    spent_c.add(normalize_text(q["medical_claim"]))
                if q.get("learning_objective"):
                    spent_o.add(normalize_text(q["learning_objective"]))
    return spent_q, spent_c, spent_o


def build_safety_dataset(
    name: str,
    pos_items: list[tuple],
    neg_items: list[tuple],
    doc_chunks: dict[str, list[dict]],
    qid_prefix: str,
    spent_q: set[str],
    spent_c: set[str],
    spent_o: set[str],
) -> dict:
    queries = []
    counter = 1

    # Positive items: (did, anchor, topic, qtype, obj, query, claim, is_partial)
    for item in pos_items:
        did, anchor, top, qtype, obj, query, claim, is_partial = item
        qid = f"{qid_prefix}-{counter:03d}"
        counter += 1

        chunks = doc_chunks[did]
        matching_chunks = [ch for ch in chunks if anchor.lower() in ch.get("text", "").lower()]
        assert len(matching_chunks) > 0, f"Anchor '{anchor}' not found in {did}!"

        matching_chunk_ids = [ch["chunk_id"] for ch in matching_chunks]
        parent_ids = list(dict.fromkeys([ch.get("parent_section_id") for ch in matching_chunks if ch.get("parent_section_id")]))

        eval_label = "PARTIALLY_SUPPORTED" if is_partial else "SUPPORTED"
        queries.append({
            "query_id": qid,
            "query": query,
            "topic": top,
            "question_type": qtype,
            "learning_objective": obj,
            "medical_claim": claim,
            "answerable": True,
            "is_partial": is_partial,
            "evaluation_label": eval_label,
            "gold_document_ids": [did],
            "gold_parent_section_ids": parent_ids,
            "gold_child_chunk_ids": matching_chunk_ids,
            "primary_evidence_quote": claim,
            "evidence_spans": [anchor],
            "review_status": "AUTOMATED_SEMANTIC_REVIEW"
        })

    # Negative items: (neg_type, topic, obj, query, claim_or_contradiction, transformation_family)
    for item in neg_items:
        neg_type, top, obj, query, claim_or_contra, transf = item
        qid = f"{qid_prefix}-{counter:03d}"
        counter += 1

        queries.append({
            "query_id": qid,
            "query": query,
            "topic": top,
            "question_type": "investigation",
            "learning_objective": obj,
            "medical_claim": claim_or_contra,
            "answerable": False,
            "is_partial": False,
            "evaluation_label": neg_type, # IN_DOMAIN_CORPUS_COVERAGE_GAP, OUT_OF_DOMAIN_UNSUPPORTED, DIFFICULT_PERTURBATION_NEGATIVE
            "transformation_family": transf,
            "gold_document_ids": [],
            "gold_parent_section_ids": [],
            "gold_child_chunk_ids": [],
            "primary_evidence_quote": None,
            "evidence_spans": [],
            "review_status": "AUTOMATED_SEMANTIC_REVIEW"
        })

    # Firewall checks
    for q in queries:
        nq = normalize_text(q["query"])
        assert nq not in spent_q, f"FIREWALL VIOLATION: Query '{q['query']}' in spent set!"
        if q.get("medical_claim"):
            nc = normalize_text(q["medical_claim"])
            assert nc not in spent_c, f"FIREWALL VIOLATION: Claim '{q['medical_claim']}' in spent set!"
        if q.get("learning_objective"):
            no = normalize_text(q["learning_objective"])
            assert no not in spent_o, f"FIREWALL VIOLATION: Objective '{q['learning_objective']}' in spent set!"

    return {
        "dataset_name": name,
        "n_total": len(queries),
        "n_positive": len(pos_items),
        "n_negative": len(neg_items),
        "n_supported": sum(1 for q in queries if q["evaluation_label"] == "SUPPORTED"),
        "n_partially_supported": sum(1 for q in queries if q["evaluation_label"] == "PARTIALLY_SUPPORTED"),
        "n_coverage_gap": sum(1 for q in queries if q["evaluation_label"] == "IN_DOMAIN_CORPUS_COVERAGE_GAP"),
        "n_out_of_domain": sum(1 for q in queries if q["evaluation_label"] == "OUT_OF_DOMAIN_UNSUPPORTED"),
        "n_difficult_perturbation": sum(1 for q in queries if q["evaluation_label"] == "DIFFICULT_PERTURBATION_NEGATIVE"),
        "queries": queries
    }
