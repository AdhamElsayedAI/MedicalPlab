"""Phase 4/5/8 & Stage D Evaluation: Evaluate retrieval against Evidence-Span Ground Truth.

Evaluates dense retrieval using the claim/evidence-span centric ground truth
(renal-dev-evidence-spans-v2.json) per Mission §12, §13, and §34.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
EVAL_PATH = ROOT / "evaluation" / "renal" / "renal-dev-evidence-spans-v2.json"
CACHE_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "cache"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking"

dev_data = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
queries = [q for q in dev_data["queries"] if q.get("answerable")]


def is_chunk_relevant(chunk: dict, query: dict) -> bool:
    gold_docs = set(query.get("gold_document_ids", []))
    if chunk.get("document_id") not in gold_docs:
        return False
        
    gold_parents = set(query.get("gold_parent_section_ids", []))
    chunk_parent = chunk.get("parent_section_id") or f"{chunk.get('document_id')}-P{int(chunk.get('source_block_index', 0)):04d}"
    chunk_text_lower = chunk.get("text", "").lower()
    
    # 1. Exact or partial span containment
    for span in query.get("evidence_spans", []):
        span_text = span.get("evidence_text", "").lower()
        if span_text and (span_text[:80] in chunk_text_lower or chunk_text_lower[:80] in span_text):
            return True
            
    # 2. Parent section match + anchor verification
    if chunk_parent in gold_parents:
        anchors = query.get("gold_verification_anchors", [])
        matched = sum(1 for a in anchors if a.lower() in chunk_text_lower)
        if matched >= query.get("gold_minimum_anchor_hits", 2):
            return True
            
    return False


def compute_metrics(rankings: list[list[dict]], queries: list[dict], corpus: list[dict]) -> dict:
    n = len(queries)
    hits = {1: 0, 3: 0, 5: 0, 10: 0}
    doc_hits_at_10 = 0
    reciprocal_rank_sum = 0.0
    ndcg_sum = 0.0
    
    for query, ranked in zip(queries, rankings):
        gold_docs = set(query.get("gold_document_ids", []))
        
        # Document recall @ 10
        if any(item.get("document_id") in gold_docs for item in ranked[:10]):
            doc_hits_at_10 += 1
            
        first_rel_rank = None
        for rank, item in enumerate(ranked[:10], start=1):
            if is_chunk_relevant(item, query):
                if first_rel_rank is None:
                    first_rel_rank = rank
                for k in hits:
                    if rank <= k:
                        hits[k] += 1
                break
                
        if first_rel_rank is not None:
            reciprocal_rank_sum += 1.0 / first_rel_rank
            ndcg_sum += 1.0 / np.log2(first_rel_rank + 1)
            
    # Also evaluate Parent Section Hit
    parent_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    for query, ranked in zip(queries, rankings):
        gold_parents = set(query.get("gold_parent_section_ids", []))
        for rank, item in enumerate(ranked[:10], start=1):
            chunk_parent = item.get("parent_section_id") or f"{item.get('document_id')}-P{int(item.get('source_block_index', 0)):04d}"
            if chunk_parent in gold_parents:
                for k in parent_hits:
                    if rank <= k:
                        parent_hits[k] += 1
                break

    return {
        "n_queries": n,
        "hit_at_1": hits[1] / n,
        "hit_at_3": hits[3] / n,
        "hit_at_5": hits[5] / n,
        "hit_at_10": hits[10] / n,
        "parent_hit_at_1": parent_hits[1] / n,
        "parent_hit_at_3": parent_hits[3] / n,
        "parent_hit_at_5": parent_hits[5] / n,
        "parent_hit_at_10": parent_hits[10] / n,
        "mrr": reciprocal_rank_sum / n,
        "ndcg_at_10": ndcg_sum / n,
        "gold_doc_at_10": doc_hits_at_10 / n,
    }


def evaluate_strategy(chunking: str, representation: str = "content_only"):
    # Load corpus chunks
    folder = CHUNKS_DIR / chunking
    chunks = []
    for f in sorted(folder.glob("*.chunks.json")):
        chunks.extend(json.loads(f.read_text(encoding="utf-8")).get("chunks", []))
        
    # Find cached embeddings
    # Search cache directory for this chunking and queries
    query_cache = None
    corpus_cache = None
    
    for f in CACHE_DIR.glob("*.json"):
        meta = json.loads(f.read_text(encoding="utf-8"))
        if meta.get("kind") == "queries":
            query_cache = np.load(CACHE_DIR / f"{meta['cache_key']}.npy")
        elif meta.get("chunking") == chunking and meta.get("representation") == representation:
            corpus_cache = np.load(CACHE_DIR / f"{meta['cache_key']}.npy")
            
    if query_cache is None or corpus_cache is None:
        print(f"Missing cache for {chunking}:{representation}")
        return None
        
    # Compute cosine similarities: corpus x queries
    sims = np.dot(corpus_cache, query_cache.T) # shape: (n_chunks, n_queries)
    
    # Top-10 rankings
    rankings = []
    for q_idx in range(len(queries)):
        scores = sims[:, q_idx]
        top_indices = np.argsort(scores)[::-1][:10]
        rankings.append([chunks[i] for i in top_indices])
        
    metrics = compute_metrics(rankings, queries, chunks)
    return metrics, rankings


def main():
    print(f"{'='*95}")
    print("EVALUATION UNDER CLAIM / EVIDENCE-SPAN GROUND TRUTH (N=69)")
    print(f"{'='*95}")
    print(f"{'Strategy':<26} {'H@1':>6} {'H@3':>6} {'H@5':>6} {'H@10':>6} {'P@1':>6} {'P@5':>6} {'MRR':>7} {'nDCG':>7} {'Doc@10':>7}")
    print("-" * 95)
    
    results = {}
    for strategy in ["B_400_overlap", "E_sentence_evidence_300"]:
        res = evaluate_strategy(strategy)
        if res:
            m, _ = res
            results[strategy] = m
            print(f"{strategy:<26} {m['hit_at_1']:>6.4f} {m['hit_at_3']:>6.4f} {m['hit_at_5']:>6.4f} {m['hit_at_10']:>6.4f} {m['parent_hit_at_1']:>6.4f} {m['parent_hit_at_5']:>6.4f} {m['mrr']:>7.4f} {m['ndcg_at_10']:>7.4f} {m['gold_doc_at_10']:>7.4f}")
            
    out_path = ROOT / "reports" / "renal_v2_evidence_span_evaluation.json"
    out_path.write_text(json.dumps({
        "report_id": "RENAL-V2-EVIDENCE-SPAN-EVALUATION",
        "ground_truth": "evaluation/renal/renal-dev-evidence-spans-v2.json",
        "n_queries": len(queries),
        "results": results
    }, indent=2) + "\n", encoding="utf-8")
    print(f"\nReport written to: {out_path.name}")


if __name__ == "__main__":
    main()
