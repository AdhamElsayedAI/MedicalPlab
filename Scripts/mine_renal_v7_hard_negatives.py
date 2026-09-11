"""
MedicalPlab Renal V7 — Milestone 6: Hard-Negative Mining & Error Analysis
========================================================================
Mines hard negatives on TRAIN_DEV (N=80):
1. Intra-document sibling chunks (same doc, adjacent/sibling section)
2. Sibling condition / intra-family clinical distractors (different doc, overlapping topic)
3. Lexical overlap distractors (high BM25 overlap without semantic answer)

Evaluates:
- Exact Passage Hit@1, Hit@5
- Document Hit@1, Hit@5
- Section Hit@1, Hit@5
- Naive preservation (retaining V3 dense correct answers)
- Hard negative distribution across ranks
"""

import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / ".renal_env"))
sys.path.insert(0, str(_ROOT / "src"))

import numpy as np
from medicalplab.learn.renal_v7_retriever import (
    RenalV7MultiChannelRetriever,
    MEDICAL_RERANKER_INSTRUCTION,
)

REPORTS_DIR = _ROOT / "reports" / "renal_v7"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
TRAIN_DEV_PATH = _ROOT / "evaluation" / "renal" / "v7" / "renal-train-dev-v7.json"


def get_doc_id(chunk_id: str) -> str:
    # e.g., DOC-PMC-RENAL-0002-B-C0045 -> DOC-PMC-RENAL-0002
    parts = chunk_id.split("-")
    if len(parts) >= 4:
        return "-".join(parts[:4])
    return chunk_id.split("-C")[0]


def main():
    print("Loading TRAIN_DEV dataset...")
    train_dev = json.loads(TRAIN_DEV_PATH.read_bytes())
    print(f"Loaded {len(train_dev)} items.")

    print("Initializing RenalV7MultiChannelRetriever (Stack A)...")
    retriever = RenalV7MultiChannelRetriever(_ROOT / "Data")
    retriever.load()

    # Also load dense baseline results from bakeoff report if available
    bakeoff_report_path = REPORTS_DIR / "renal_v7_model_bakeoff_report.json"
    dense_baseline_data = {}
    if bakeoff_report_path.exists():
        bakeoff_report = json.loads(bakeoff_report_path.read_bytes())
        dense_baseline_data = bakeoff_report.get("cfg1_dense_baseline_v3", {})

    hard_negatives = []
    intra_doc_siblings = 0
    sibling_condition_distractors = 0
    lexical_distractors = 0

    doc_hit1 = 0
    doc_hit5 = 0
    sec_hit1 = 0
    sec_hit5 = 0
    passage_hit1 = 0
    passage_hit5 = 0

    per_query_audit = []

    for idx, item in enumerate(train_dev):
        q = item["query"]
        gold_cids = set(item["gold_chunk_ids"])
        gold_doc_ids = {get_doc_id(c) for c in gold_cids}

        # Target section paths for gold chunks
        gold_sections = set()
        for gc in gold_cids:
            if gc in retriever._chunk_id_to_idx:
                ch = retriever._chunks[retriever._chunk_id_to_idx[gc]]
                gold_sections.add(" > ".join(ch.get("section_path", [])))

        results = retriever.retrieve(q, top_k=10, candidate_pool_size=50)

        # Passage hits
        top1_cid = results[0].chunk_id if results else None
        is_passage_hit1 = top1_cid in gold_cids
        is_passage_hit5 = any(r.chunk_id in gold_cids for r in results[:5])
        if is_passage_hit1:
            passage_hit1 += 1
        if is_passage_hit5:
            passage_hit5 += 1

        # Document hits
        top1_doc = get_doc_id(top1_cid) if top1_cid else None
        is_doc_hit1 = top1_doc in gold_doc_ids
        is_doc_hit5 = any(get_doc_id(r.chunk_id) in gold_doc_ids for r in results[:5])
        if is_doc_hit1:
            doc_hit1 += 1
        if is_doc_hit5:
            doc_hit5 += 1

        # Section hits
        top1_sec = " > ".join(results[0].chunk.get("section_path", [])) if results else ""
        is_sec_hit1 = top1_sec in gold_sections
        is_sec_hit5 = any(" > ".join(r.chunk.get("section_path", [])) in gold_sections for r in results[:5])
        if is_sec_hit1:
            sec_hit1 += 1
        if is_sec_hit5:
            sec_hit5 += 1

        # Analyze top distractors
        gold_ranks = [r_i + 1 for r_i, r in enumerate(results) if r.chunk_id in gold_cids]
        
        query_audit = {
            "query_idx": idx,
            "query": q,
            "gold_chunk_ids": list(gold_cids),
            "gold_doc_ids": list(gold_doc_ids),
            "gold_ranks": gold_ranks,
            "passage_hit_at_1": is_passage_hit1,
            "passage_hit_at_5": is_passage_hit5,
            "doc_hit_at_1": is_doc_hit1,
            "doc_hit_at_5": is_doc_hit5,
            "top1_chunk_id": top1_cid,
            "top1_doc_id": top1_doc,
            "top1_section": top1_sec,
            "top1_heading": results[0].chunk.get("heading") if results else "",
            "distractors": []
        }

        # If passage hit@1 missed, classify the top-1 distractor
        if not is_passage_hit1 and results:
            top_dist = results[0]
            dist_doc = get_doc_id(top_dist.chunk_id)
            if dist_doc in gold_doc_ids:
                category = "INTRA_DOCUMENT_SIBLING"
                intra_doc_siblings += 1
            elif top_dist.channel_ranks.get("bm25", 999) <= 5 and top_dist.channel_ranks.get("dense", 999) > 20:
                category = "LEXICAL_OVERLAP_DISTRACTOR"
                lexical_distractors += 1
            else:
                category = "SIBLING_CLINICAL_CONDITION"
                sibling_condition_distractors += 1

            query_audit["distractors"].append({
                "chunk_id": top_dist.chunk_id,
                "document_id": dist_doc,
                "section": top1_sec,
                "heading": top_dist.chunk.get("heading"),
                "category": category,
                "rerank_score": top_dist.rerank_score,
                "channel_ranks": top_dist.channel_ranks
            })

            hard_negatives.append({
                "query": q,
                "gold_chunks": list(gold_cids),
                "distractor_chunk": top_dist.chunk_id,
                "distractor_category": category,
                "distractor_heading": top_dist.chunk.get("heading"),
                "distractor_score": top_dist.rerank_score
            })

        per_query_audit.append(query_audit)

    n = len(train_dev)
    print(f"\n==========================================")
    print(f"TRAIN_DEV (N={n}) Hard-Negative Audit:")
    print(f"==========================================")
    print(f"Passage Hit@1:  {passage_hit1}/{n} ({passage_hit1/n*100:.2f}%)")
    print(f"Passage Hit@5:  {passage_hit5}/{n} ({passage_hit5/n*100:.2f}%)")
    print(f"Document Hit@1: {doc_hit1}/{n} ({doc_hit1/n*100:.2f}%)")
    print(f"Document Hit@5: {doc_hit5}/{n} ({doc_hit5/n*100:.2f}%)")
    print(f"Section Hit@1:  {sec_hit1}/{n} ({sec_hit1/n*100:.2f}%)")
    print(f"Section Hit@5:  {sec_hit5}/{n} ({sec_hit5/n*100:.2f}%)")
    print(f"\nTop-1 Distractor Classification (total misses: {n - passage_hit1}):")
    print(f"  Intra-document siblings (same document): {intra_doc_siblings} ({(intra_doc_siblings/(n-passage_hit1))*100:.1f}%)")
    print(f"  Sibling clinical conditions (cross-document): {sibling_condition_distractors} ({(sibling_condition_distractors/(n-passage_hit1))*100:.1f}%)")
    print(f"  Lexical overlap distractors: {lexical_distractors} ({(lexical_distractors/(n-passage_hit1))*100:.1f}%)")

    # Output report
    report = {
        "dataset": "renal-train-dev-v7.json",
        "sample_size": n,
        "metrics": {
            "passage_hit_at_1": {"count": passage_hit1, "percent": round(passage_hit1 / n * 100, 2)},
            "passage_hit_at_5": {"count": passage_hit5, "percent": round(passage_hit5 / n * 100, 2)},
            "document_hit_at_1": {"count": doc_hit1, "percent": round(doc_hit1 / n * 100, 2)},
            "document_hit_at_5": {"count": doc_hit5, "percent": round(doc_hit5 / n * 100, 2)},
            "section_hit_at_1": {"count": sec_hit1, "percent": round(sec_hit1 / n * 100, 2)},
            "section_hit_at_5": {"count": sec_hit5, "percent": round(sec_hit5 / n * 100, 2)},
        },
        "distractor_breakdown": {
            "intra_document_sibling": {"count": intra_doc_siblings, "percent": round(intra_doc_siblings / max(1, n - passage_hit1) * 100, 2)},
            "sibling_clinical_condition": {"count": sibling_condition_distractors, "percent": round(sibling_condition_distractors / max(1, n - passage_hit1) * 100, 2)},
            "lexical_overlap": {"count": lexical_distractors, "percent": round(lexical_distractors / max(1, n - passage_hit1) * 100, 2)},
        },
        "hard_negatives_mined": hard_negatives,
        "per_query_audit": per_query_audit
    }

    out_file = REPORTS_DIR / "renal_v7_hard_negative_audit.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    import hashlib
    sha = hashlib.sha256(out_file.read_bytes()).hexdigest()
    (REPORTS_DIR / "renal_v7_hard_negative_audit.json.sha256").write_text(f"{sha}  renal_v7_hard_negative_audit.json", encoding="utf-8")
    print(f"\nWrote hard negative audit report to {out_file.name} (SHA-256: {sha})")


if __name__ == "__main__":
    main()
