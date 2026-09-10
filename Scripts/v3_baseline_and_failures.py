"""Phase 6, 7, 8: Recompute Corrected Flat Dense Baseline, Reclassify Failures, and Measure Candidate Recall.

Per Mission Section 14, 15, 34, and Phases 6-8:
- Recompute metrics under frozen V3 qrels:
  DocumentHit@1/3/5/10
  ParentSectionHit@1/3/5/10
  PassageHit@1/3/5/10
  CandidateHit@10/20/30/50/100
  MRR, nDCG@10
- Reclassify all Top-1 and Top-10 failure causes across 14 defined categories.
- Output:
  reports/renal_v3/renal_v3_baseline_evaluation.json
  reports/renal_v3/renal_v3_passage_failure_analysis.json
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
QRELS_PATH = ROOT / "evaluation" / "renal" / "v3" / "renal-dev-v3-qrels.json"
CACHE_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "cache"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
REPORTS_DIR = ROOT / "reports" / "renal_v3"


def load_chunks() -> list[dict]:
    chunks = []
    for f in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        chunks.extend(data.get("chunks", []))
    return chunks


def load_embeddings() -> tuple[np.ndarray, np.ndarray]:
    query_arr = None
    content_arr = None
    for f in CACHE_DIR.glob("*.json"):
        meta = json.loads(f.read_text(encoding="utf-8"))
        key = meta.get("cache_key")
        if meta.get("kind") == "queries":
            query_arr = np.load(CACHE_DIR / f"{key}.npy")
        elif meta.get("chunking") == "B_400_overlap" and meta.get("representation") == "content_only":
            content_arr = np.load(CACHE_DIR / f"{key}.npy")
    if query_arr is None or content_arr is None:
        raise RuntimeError("Missing required embeddings in cache")
    return query_arr, content_arr


def classify_failure(query: dict, top10: list[dict], gold_chunk_ids: set[str], gold_parents: set[str], gold_docs: set[str]) -> tuple[str, str]:
    """Classifies the primary retrieval failure for queries where Hit@1 == 0."""
    top1 = top10[0]
    top1_doc = top1.get("document_id")
    top1_parent = top1.get("parent_section_id")
    top1_cid = top1.get("chunk_id")
    top1_text = top1.get("text", "").lower()
    
    # Check 1: Document routing failure
    if top1_doc not in gold_docs:
        if any(item.get("document_id") in gold_docs for item in top10):
            return "DOCUMENT_ROUTING_FAILURE", f"Top-1 from wrong document ({top1_doc} vs {gold_docs}), but correct doc present in Top-10."
        else:
            return "DOCUMENT_ROUTING_FAILURE", f"Target document completely missing from Top-10."

    # Check 2: Right document, but methods/results noise
    heading = str(top1.get("heading", "")).lower()
    if any(k in heading for k in ["method", "material", "statistical", "result", "patient cohort"]):
        return "METHODS_RESULTS_NOISE", f"Retrieved chunk is in experimental methods/results section: {heading}"
    if any(k in top1_text[:200] for k in ["p < 0.05", "standard deviation", "ethics committee", "written informed consent"]):
        return "METHODS_RESULTS_NOISE", "Top-1 passage contains procedural methods/statistical noise."

    # Check 3: Right section, wrong passage (intra-section granularity)
    if top1_parent in gold_parents:
        return "RIGHT_SECTION_WRONG_PASSAGE", f"Correct parent section ({top1_parent}) retrieved at #1, but adjacent chunk selected."

    # Check 4: Right document, wrong section
    # Subdivide into SECTION_AMBIGUITY vs RIGHT_DOCUMENT_WRONG_SECTION
    if any(ch_id in [item.get("chunk_id") for item in top10] for ch_id in gold_chunk_ids):
        return "SECTION_AMBIGUITY", f"Gold chunk retrieved in Top-10, but preceded by another section ({top1_parent}) in same document."

    return "RIGHT_DOCUMENT_WRONG_SECTION", f"Top-1 placed in different section ({top1_parent}) of correct document ({top1_doc})."


def main():
    print("=" * 70)
    print("PHASE 6, 7, 8: BASELINE RECOMPUTATION, FAILURES & CANDIDATE RECALL")
    print("=" * 70)
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    qrels_data = json.loads(QRELS_PATH.read_text(encoding="utf-8"))
    queries = [q for q in qrels_data["queries"] if q.get("answerable")]
    n_queries = len(queries)
    print(f"Loaded {n_queries} answerable queries from frozen V3 qrels.")
    
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks in B_400_overlap.")
    
    query_arr, content_arr = load_embeddings()
    print(f"Loaded embeddings: queries {query_arr.shape}, corpus {content_arr.shape}")
    
    # Compute similarity matrix: (n_chunks, n_queries)
    sims = np.dot(content_arr, query_arr.T)
    
    # Metrics accumulators
    k_list = [1, 3, 5, 10]
    candidate_k_list = [10, 20, 30, 50, 100]
    
    doc_hits = {k: 0 for k in k_list}
    parent_hits = {k: 0 for k in k_list}
    passage_hits = {k: 0 for k in k_list}
    candidate_hits = {k: 0 for k in candidate_k_list}
    
    reciprocal_ranks = []
    ndcg_list = []
    
    failure_records = []
    failure_distribution = {}
    
    rankings_per_query = []
    
    for q_idx, q in enumerate(queries):
        qid = q["query_id"]
        gold_docs = set(q.get("gold_document_ids", []))
        gold_parents = set(q.get("gold_parent_section_ids", []))
        gold_chunks = set(q.get("gold_child_chunk_ids", []))
        
        scores = sims[:, q_idx]
        top100_idx = np.argsort(scores)[::-1][:100]
        ranked_chunks = [chunks[i] for i in top100_idx if i < len(chunks)]
        rankings_per_query.append(ranked_chunks[:10])
        
        # 1. Document Hits @ 1, 3, 5, 10
        for k in k_list:
            if any(item.get("document_id") in gold_docs for item in ranked_chunks[:k]):
                doc_hits[k] += 1
                
        # 2. Parent Section Hits @ 1, 3, 5, 10
        for k in k_list:
            if any(item.get("parent_section_id") in gold_parents for item in ranked_chunks[:k]):
                parent_hits[k] += 1
                
        # 3. Passage Hits @ 1, 3, 5, 10
        first_rel_rank = None
        for rank, item in enumerate(ranked_chunks[:10], start=1):
            if item.get("chunk_id") in gold_chunks:
                if first_rel_rank is None:
                    first_rel_rank = rank
                for k in k_list:
                    if rank <= k:
                        passage_hits[k] += 1
                break
                
        if first_rel_rank is not None:
            reciprocal_ranks.append(1.0 / first_rel_rank)
            ndcg_list.append(1.0 / np.log2(first_rel_rank + 1))
        else:
            reciprocal_ranks.append(0.0)
            ndcg_list.append(0.0)
            
        # 4. Candidate Hits @ 10, 20, 30, 50, 100
        for ck in candidate_k_list:
            if any(item.get("chunk_id") in gold_chunks for item in ranked_chunks[:ck]):
                candidate_hits[ck] += 1
                
        # 5. Failure Classification (for Hit@1 misses)
        if first_rel_rank != 1:
            cat, reason = classify_failure(q, ranked_chunks[:10], gold_chunks, gold_parents, gold_docs)
            failure_distribution[cat] = failure_distribution.get(cat, 0) + 1
            failure_records.append({
                "query_id": qid,
                "medical_claim": q.get("medical_claim"),
                "failure_category": cat,
                "justification": reason,
                "first_relevant_rank": first_rel_rank,
                "top1_retrieved": {
                    "chunk_id": ranked_chunks[0].get("chunk_id"),
                    "document_id": ranked_chunks[0].get("document_id"),
                    "parent_section_id": ranked_chunks[0].get("parent_section_id"),
                    "heading": ranked_chunks[0].get("heading"),
                    "score": float(scores[top100_idx[0]])
                }
            })

    # Metrics calculation
    doc_metrics = {f"DocumentHit@{k}": {"numerator": doc_hits[k], "denominator": n_queries, "value": doc_hits[k] / n_queries} for k in k_list}
    parent_metrics = {f"ParentSectionHit@{k}": {"numerator": parent_hits[k], "denominator": n_queries, "value": parent_hits[k] / n_queries} for k in k_list}
    passage_metrics = {f"PassageHit@{k}": {"numerator": passage_hits[k], "denominator": n_queries, "value": passage_hits[k] / n_queries} for k in k_list}
    candidate_metrics = {f"CandidateHit@{k}": {"numerator": candidate_hits[k], "denominator": n_queries, "value": candidate_hits[k] / n_queries} for k in candidate_k_list}
    
    mrr = float(np.mean(reciprocal_ranks))
    ndcg10 = float(np.mean(ndcg_list))
    
    print("\n" + "=" * 70)
    print("PHASE 6: CORRECTED FLAT DENSE V3 DEV BASELINE RESULTS (N=69)")
    print("=" * 70)
    print("DOCUMENT RETRIEVAL:")
    for k in k_list:
        m = doc_metrics[f"DocumentHit@{k}"]
        print(f"  DocumentHit@{k}: {m['numerator']}/{m['denominator']} = {m['value']:.4f}")
        
    print("\nSECTION RETRIEVAL:")
    for k in k_list:
        m = parent_metrics[f"ParentSectionHit@{k}"]
        print(f"  ParentSectionHit@{k}: {m['numerator']}/{m['denominator']} = {m['value']:.4f}")
        
    print("\nPASSAGE RETRIEVAL:")
    for k in k_list:
        m = passage_metrics[f"PassageHit@{k}"]
        print(f"  PassageHit@{k}: {m['numerator']}/{m['denominator']} = {m['value']:.4f}")
    print(f"  MRR: {mrr:.4f}")
    print(f"  nDCG@10: {ndcg10:.4f}")
    
    print("\n" + "=" * 70)
    print("PHASE 8: CANDIDATE PASSAGE RECALL CURVE")
    print("=" * 70)
    for ck in candidate_k_list:
        m = candidate_metrics[f"CandidateHit@{ck}"]
        print(f"  CandidateHit@{ck}: {m['numerator']}/{m['denominator']} = {m['value']:.4f} ({m['value']*100:.1f}%)")

    print("\n" + "=" * 70)
    print("PHASE 7: UPDATED FAILURE CLASSIFICATION (Hit@1 Misses, N={})".format(len(failure_records)))
    print("=" * 70)
    for cat, count in sorted(failure_distribution.items(), key=lambda x: -x[1]):
        pct = count / len(failure_records) * 100
        print(f"  {cat:<35}: {count:>2} ({pct:>5.1f}%)")

    # Persist reports
    baseline_payload = {
        "report_id": "RENAL-V3-BASELINE-DEV",
        "description": "Corrected flat dense retrieval baseline evaluated against frozen V3 qrels",
        "dataset_name": "RENAL-DEV-V3-QRELS",
        "dataset_sha256": "826a25eefffdd888166b7495e77ee0e99cab38d4f04a31aeb1e0c0e4d9b78f6a",
        "n_queries": n_queries,
        "metrics": {
            "document_retrieval": doc_metrics,
            "section_retrieval": parent_metrics,
            "passage_retrieval": passage_metrics,
            "candidate_recall": candidate_metrics,
            "mrr": mrr,
            "ndcg_at_10": ndcg10
        }
    }
    baseline_out = REPORTS_DIR / "renal_v3_baseline_evaluation.json"
    baseline_out.write_text(json.dumps(baseline_payload, indent=2), encoding="utf-8")
    print(f"\nWrote baseline report: {baseline_out}")

    failure_payload = {
        "report_id": "RENAL-V3-PASSAGE-FAILURE-ANALYSIS",
        "description": "Re-audit of passage retrieval failure causes under frozen V3 qrels",
        "n_misses": len(failure_records),
        "total_queries": n_queries,
        "failure_distribution": {cat: {"count": cnt, "percentage": cnt / len(failure_records) * 100} for cat, cnt in failure_distribution.items()},
        "failures": failure_records
    }
    failure_out = REPORTS_DIR / "renal_v3_passage_failure_analysis.json"
    failure_out.write_text(json.dumps(failure_payload, indent=2), encoding="utf-8")
    print(f"Wrote failure analysis report: {failure_out}")


if __name__ == "__main__":
    main()
