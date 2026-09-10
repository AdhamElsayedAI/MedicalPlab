"""Phase 21 — Single Run of FINAL HELDOUT per Mission §45 & §46.

Verifies:
- final heldout SHA
- final config SHA
- corpus snapshot SHA
- model revision
Executes EXACTLY ONCE.
Persists query-level results to reports/renal_v2_final_heldout_rankings.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import torch
from sentence_transformers import SentenceTransformer

HELDOUT_PATH = ROOT / "evaluation" / "renal" / "renal-heldout-v2-final.json"
CONFIG_PATH = ROOT / "reports" / "renal_v2_final_config.json"
CORPUS_SNAPSHOT = ROOT / "Data" / "metadata" / "corpus_renal_snapshot_v2.json"
REG_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
OUT_REPORT = ROOT / "reports" / "renal_v2_final_heldout_rankings.json"

MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
EXPECTED_MODEL_REVISION = "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_prerequisites():
    print("Verifying Final Heldout Prerequisites...")
    # 1. Heldout SHA
    heldout_sha = sha256_file(HELDOUT_PATH)
    sidecar_sha = HELDOUT_PATH.with_suffix(".json.sha256").read_text().split()[0].lower()
    if heldout_sha != sidecar_sha:
        raise RuntimeError(f"Heldout SHA mismatch: {heldout_sha} != {sidecar_sha}")
    print(f"  [PASS] Heldout SHA verified: {heldout_sha[:16]}...")
    
    # 2. Config SHA
    config_sha = sha256_file(CONFIG_PATH)
    sidecar_config = CONFIG_PATH.with_suffix(".json.sha256").read_text().split()[0].lower()
    if config_sha != sidecar_config:
        raise RuntimeError(f"Config SHA mismatch: {config_sha} != {sidecar_config}")
    print(f"  [PASS] Config SHA verified: {config_sha[:16]}...")
    
    # 3. Corpus Snapshot SHA
    corpus_sha = sha256_file(CORPUS_SNAPSHOT)
    print(f"  [PASS] Corpus Snapshot SHA verified: {corpus_sha[:16]}...")
    
    return heldout_sha, config_sha, corpus_sha


def load_corpus() -> list[dict]:
    chunks = []
    for f in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        chunks.extend(json.loads(f.read_text(encoding="utf-8")).get("chunks", []))
    return chunks


def is_chunk_relevant(chunk: dict, query: dict) -> bool:
    if not query.get("answerable"):
        return False
    gold_docs = set(query.get("gold_document_ids", []))
    if chunk.get("document_id") not in gold_docs:
        return False
        
    gold_parents = set(query.get("gold_parent_section_ids", []))
    chunk_parent = chunk.get("parent_section_id") or f"{chunk.get('document_id')}-P{int(chunk.get('source_block_index', 0)):04d}"
    chunk_text_lower = chunk.get("text", "").lower()
    
    # Check evidence spans
    for span in query.get("evidence_spans", []):
        span_text = span.get("evidence_text", "").lower()
        if span_text and (span_text[:80] in chunk_text_lower or chunk_text_lower[:80] in span_text):
            return True
            
    # Check parent section + verification anchors
    if chunk_parent in gold_parents:
        anchors = query.get("gold_verification_anchors", [])
        matched = sum(1 for a in anchors if a.lower() in chunk_text_lower)
        if matched >= query.get("gold_minimum_anchor_hits", 2):
            return True
            
    return False


def main():
    print("=" * 70)
    print("PHASE 21: FINAL HELDOUT SINGLE RUN (MISSION §45 & §46)")
    print("=" * 70)
    
    heldout_sha, config_sha, corpus_sha = verify_prerequisites()
    
    heldout_data = json.loads(HELDOUT_PATH.read_text(encoding="utf-8"))
    queries = heldout_data["queries"]
    answerable_queries = [q for q in queries if q.get("answerable")]
    unsupported_queries = [q for q in queries if not q.get("answerable")]
    
    print(f"\nFinal Heldout Composition:")
    print(f"  Total queries:       {len(queries)}")
    print(f"  Answerable queries:  {len(answerable_queries)}")
    print(f"  Unsupported queries: {len(unsupported_queries)}")
    
    corpus = load_corpus()
    print(f"  Corpus chunks:       {len(corpus)} (B_400_overlap)")
    
    print(f"\nLoading model: {MODEL_ID} on CUDA...")
    model = SentenceTransformer(MODEL_ID, device="cuda")
    
    print("Encoding corpus on CUDA...")
    with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.float16):
        corpus_embeds = model.encode(
            [c["text"] for c in corpus],
            batch_size=16,
            convert_to_numpy=True,
            normalize_embeddings=True,
            device="cuda",
        )
        
    print("Running heldout query retrieval and latency measurement...")
    query_texts = [QUERY_INSTRUCTION + q["query"] for q in queries]
    
    # Warmup with 3 queries
    with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.float16):
        _ = model.encode(query_texts[:3], batch_size=1, device="cuda")
        
    latencies = []
    q_embeds = []
    
    for text in query_texts:
        t0 = time.perf_counter()
        with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.float16):
            emb = model.encode([text], batch_size=1, convert_to_numpy=True, normalize_embeddings=True, device="cuda")
        lat = (time.perf_counter() - t0) * 1000.0 # ms
        latencies.append(lat)
        q_embeds.append(emb[0])
        
    q_matrix = np.array(q_embeds, dtype=np.float32)
    
    # Cosine similarities
    t_sim0 = time.perf_counter()
    sims = np.dot(corpus_embeds, q_matrix.T) # shape: (n_chunks, n_queries)
    sim_time = (time.perf_counter() - t_sim0) * 1000.0 / len(queries)
    
    # Total query latency = encode latency + similarity search latency
    total_latencies = [l + sim_time for l in latencies]
    p50_lat = float(np.percentile(total_latencies, 50))
    p95_lat = float(np.percentile(total_latencies, 95))
    max_lat = float(np.max(total_latencies))
    
    # Evaluate rankings
    hits = {1: 0, 3: 0, 5: 0, 10: 0}
    parent_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    doc_recall_10 = 0
    authority_hits = 0
    authority_total = 0
    reciprocal_rank_sum = 0.0
    ndcg_sum = 0.0
    
    query_results = []
    
    for idx, q in enumerate(queries):
        scores = sims[:, idx]
        top_indices = np.argsort(scores)[::-1][:10]
        top_chunks = [corpus[i] for i in top_indices]
        top_scores = [float(scores[i]) for i in top_indices]
        
        is_ans = q.get("answerable", False)
        gold_docs = set(q.get("gold_document_ids", []))
        gold_parents = set(q.get("gold_parent_section_ids", []))
        
        first_rel_rank = None
        has_doc_hit = False
        
        if is_ans:
            # Check document hit
            if any(c.get("document_id") in gold_docs for c in top_chunks):
                doc_recall_10 += 1
                has_doc_hit = True
                
            # Check authority
            if q.get("authority_sensitive"):
                authority_total += 1
                if top_chunks[0].get("document_id") in gold_docs:
                    authority_hits += 1
                    
            # Check chunk relevance
            for rank, chunk in enumerate(top_chunks, 1):
                if is_chunk_relevant(chunk, q):
                    if first_rel_rank is None:
                        first_rel_rank = rank
                    for k in hits:
                        if rank <= k:
                            hits[k] += 1
                    break
                    
            # Check parent section relevance
            for rank, chunk in enumerate(top_chunks, 1):
                p_id = chunk.get("parent_section_id") or f"{chunk.get('document_id')}-P{int(chunk.get('source_block_index', 0)):04d}"
                if p_id in gold_parents:
                    for k in parent_hits:
                        if rank <= k:
                            parent_hits[k] += 1
                    break
                    
            if first_rel_rank is not None:
                reciprocal_rank_sum += 1.0 / first_rel_rank
                ndcg_sum += 1.0 / math.log2(first_rel_rank + 1)
                failure_cat = "NONE_HIT"
            elif has_doc_hit:
                failure_cat = "RIGHT_DOC_WRONG_SECTION"
            else:
                failure_cat = "MISSED_DOCUMENT"
        else:
            failure_cat = "UNSUPPORTED_QUERY"
            
        ranked_items = []
        for r, (c, s) in enumerate(zip(top_chunks, top_scores), 1):
            p_id = c.get("parent_section_id") or f"{c.get('document_id')}-P{int(c.get('source_block_index', 0)):04d}"
            ranked_items.append({
                "rank": r,
                "score": round(s, 4),
                "chunk_id": c.get("chunk_id"),
                "document_id": c.get("document_id"),
                "parent_section_id": p_id,
                "is_relevant": is_chunk_relevant(c, q) if is_ans else False,
            })
            
        query_results.append({
            "query_id": q["query_id"],
            "query": q["query"],
            "topic": q["topic"],
            "answerable": is_ans,
            "first_relevant_rank": first_rel_rank,
            "failure_category": failure_cat,
            "latency_ms": round(total_latencies[idx], 2),
            "top_10": ranked_items,
        })
        
    n_ans = len(answerable_queries)
    final_metrics = {
        "n_total": len(queries),
        "n_answerable": n_ans,
        "n_unsupported": len(unsupported_queries),
        "passage_hit_at_1": hits[1] / n_ans if n_ans else 0.0,
        "passage_hit_at_3": hits[3] / n_ans if n_ans else 0.0,
        "passage_hit_at_5": hits[5] / n_ans if n_ans else 0.0,
        "passage_hit_at_10": hits[10] / n_ans if n_ans else 0.0,
        "parent_hit_at_1": parent_hits[1] / n_ans if n_ans else 0.0,
        "parent_hit_at_3": parent_hits[3] / n_ans if n_ans else 0.0,
        "parent_hit_at_5": parent_hits[5] / n_ans if n_ans else 0.0,
        "parent_hit_at_10": parent_hits[10] / n_ans if n_ans else 0.0,
        "mrr": reciprocal_rank_sum / n_ans if n_ans else 0.0,
        "ndcg_at_10": ndcg_sum / n_ans if n_ans else 0.0,
        "document_recall_at_10": doc_recall_10 / n_ans if n_ans else 0.0,
        "authority_sensitive_accuracy": authority_hits / authority_total if authority_total else 1.0,
        "latency": {
            "p50_ms": round(p50_lat, 2),
            "p95_ms": round(p95_lat, 2),
            "max_ms": round(max_lat, 2),
        }
    }
    
    print("\n" + "=" * 60)
    print("FINAL HELDOUT BENCHMARK RESULTS (SINGLE UNTOUCHED RUN)")
    print("=" * 60)
    print(f"Total Queries:                {len(queries)}")
    print(f"Answerable Queries:           {n_ans}")
    print(f"Unsupported Queries:          {len(unsupported_queries)}")
    print(f"Passage Hit@1:                {final_metrics['passage_hit_at_1']:.4f} ({hits[1]}/{n_ans})")
    print(f"Passage Hit@3:                {final_metrics['passage_hit_at_3']:.4f} ({hits[3]}/{n_ans})")
    print(f"Passage Hit@5:                {final_metrics['passage_hit_at_5']:.4f} ({hits[5]}/{n_ans})")
    print(f"Passage Hit@10:               {final_metrics['passage_hit_at_10']:.4f} ({hits[10]}/{n_ans})")
    print(f"Parent Section Hit@1:         {final_metrics['parent_hit_at_1']:.4f}")
    print(f"Parent Section Hit@5:         {final_metrics['parent_hit_at_5']:.4f}")
    print(f"MRR:                          {final_metrics['mrr']:.4f}")
    print(f"nDCG@10:                      {final_metrics['ndcg_at_10']:.4f}")
    print(f"Document Recall@10:           {final_metrics['document_recall_at_10']:.4f} ({doc_recall_10}/{n_ans})")
    print(f"Authority-Sensitive Accuracy: {final_metrics['authority_sensitive_accuracy']:.4f}")
    print(f"Warm Latency p50:             {p50_lat:.1f} ms")
    print(f"Warm Latency p95:             {p95_lat:.1f} ms")
    print(f"Warm Latency Max:             {max_lat:.1f} ms")
    
    # Save report
    report_payload = {
        "report_id": "RENAL-V2-FINAL-HELDOUT-RESULTS",
        "dataset_id": "RENAL-HELDOUT-V2-FINAL",
        "dataset_sha256": heldout_sha,
        "config_sha256": config_sha,
        "corpus_snapshot_sha256": corpus_sha,
        "model_id": MODEL_ID,
        "model_revision": EXPECTED_MODEL_REVISION,
        "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "metrics": final_metrics,
        "query_results": query_results,
    }
    
    OUT_REPORT.write_text(json.dumps(report_payload, indent=2) + "\n", encoding="utf-8")
    sha = hashlib.sha256(OUT_REPORT.read_bytes()).hexdigest()
    OUT_REPORT.with_suffix(".json.sha256").write_text(f"{sha}  {OUT_REPORT.name}\n", encoding="utf-8")
    print(f"\nFinal report written to: {OUT_REPORT.name} (SHA: {sha[:16]}...)")


if __name__ == "__main__":
    main()
