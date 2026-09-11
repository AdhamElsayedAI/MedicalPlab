import os
import sys
import hashlib
import json
import math
from pathlib import Path
import time

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import numpy as np
import torch
from sentence_transformers import CrossEncoder
from transformers import AutoModel, AutoTokenizer

DEV_A_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
REGISTRY_PATH = _ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = _ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = _ROOT / "Data" / "experiments" / "renal_v3" / "cache"
REPORTS_DIR = _ROOT / "reports" / "renal_v5"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
ALPHA_DOC_PRIOR = 0.18

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

def compute_dcg_at_k(relevance: list[int], k: int = 10) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevance[:k]):
        if rel > 0:
            dcg += (2**rel - 1) / math.log2(i + 2)
    return dcg

def compute_ndcg_at_k(relevance: list[int], k: int = 10) -> float:
    actual_dcg = compute_dcg_at_k(relevance, k)
    ideal_relevance = sorted(relevance, reverse=True)
    ideal_dcg = compute_dcg_at_k(ideal_relevance, k)
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0

def normalize_section_path(path):
    if not path:
        return ""
    if isinstance(path, list):
        return " > ".join(s.strip().lower() for s in path)
    return str(path).strip().lower()

# 1. Load Corpus Chunks
chunks = []
chunk_doc_ids = []
chunk_cids = []
chunk_sec_paths = []
doc_to_chunks = {}

for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        chunks.append(ch)
        did = ch["document_id"]
        cid = ch["chunk_id"]
        sec = tuple(ch.get("section_path", []))
        chunk_doc_ids.append(did)
        chunk_cids.append(cid)
        chunk_sec_paths.append(sec)
        doc_to_chunks.setdefault(did, []).append(len(chunks) - 1)

n_chunks = len(chunks)
doc_ids_sorted = sorted(list(doc_to_chunks.keys()))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
chunk_id_to_idx = {ch["chunk_id"]: i for i, ch in enumerate(chunks)}
print(f"Loaded {n_chunks} chunks across {len(doc_ids_sorted)} documents.")

# 2. Load Embeddings
corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)

# 3. Load DEV-A Items
dev_a = json.loads(DEV_A_PATH.read_bytes())
n_dev = len(dev_a)
print(f"Loaded DEV-A: N={n_dev} items")

# 4. Encode Queries
tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device).eval()

query_texts = [QUERY_INSTRUCTION + it["query"] for it in dev_a]
with torch.inference_mode():
    encoded = tokenizer(query_texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
    outputs = embed_model(**encoded)
    mask = encoded["attention_mask"].unsqueeze(-1)
    q_emb = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
    q_emb = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)

# Free embedding model to preserve VRAM for reranker
del embed_model
del tokenizer
torch.cuda.empty_cache()

# 5. Load Reranker
print("Loading Qwen3-Reranker-0.6B...")
reranker = CrossEncoder(RERANK_MODEL_ID, device="cuda:0", trust_remote_code=True)
print("Reranker loaded successfully.")

# Warmup reranker
torch.cuda.synchronize()
_ = reranker.predict([["warmup query", "warmup text"] for _ in range(2)], batch_size=2, show_progress_bar=False)
torch.cuda.synchronize()

# 6. Candidate Selector Implementation
# Uses dense passage score + doc prior, with section diversity cap and adjacent chunk suppression
def candidate_selector(q_idx, B=200, R=20, max_per_sec=3, adj_penalty=0.03):
    q_vec = q_emb[q_idx]
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb_scores = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb_scores[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
            
    top_b = comb_scores.argsort()[::-1][:B]
    
    selected = []
    selected_set = set()
    sec_counts = {}
    
    cand_pool = list(top_b)
    
    for _ in range(R):
        best_cand = None
        best_eff = -float("inf")
        best_pos = -1
        
        for pos, c_idx in enumerate(cand_pool):
            sec = (chunk_doc_ids[c_idx], chunk_sec_paths[c_idx])
            
            # Check hard section cap
            if max_per_sec is not None and sec_counts.get(sec, 0) >= max_per_sec:
                continue
                
            penalty = 0.0
            if adj_penalty > 0.0:
                if (c_idx - 1) in selected_set or (c_idx + 1) in selected_set:
                    penalty += adj_penalty
                    
            eff_score = comb_scores[c_idx] - penalty
            if eff_score > best_eff:
                best_eff = eff_score
                best_cand = c_idx
                best_pos = pos
                
        if best_cand is None:
            # Fallback: take next highest scoring candidate regardless of constraints
            if cand_pool:
                best_cand = cand_pool[0]
                best_pos = 0
            else:
                break
                
        selected.append(best_cand)
        selected_set.add(best_cand)
        sec = (chunk_doc_ids[best_cand], chunk_sec_paths[best_cand])
        sec_counts[sec] = sec_counts.get(sec, 0) + 1
        cand_pool.pop(best_pos)
        
    rejected = [c for c in top_b if c not in selected_set]
    return selected, top_b, rejected, comb_scores

# 7. Experiment Runner Function
def run_experiment(exp_name, use_selector=False, B=200, R=20, max_per_sec=3, adj_penalty=0.03):
    print("\n" + "=" * 70)
    print(f"RUNNING EXPERIMENT: {exp_name}")
    print("=" * 70)
    
    doc_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    sec_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    pas_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    
    input_cov_b_count = 0
    output_cov_r_count = 0
    retention_count = 0
    
    mrr_list = []
    ndcg_list = []
    latencies = []
    
    query_records = []
    
    torch.cuda.reset_peak_memory_stats()
    
    for i, item in enumerate(dev_a):
        query = item["query"]
        gold_doc = item.get("gold_doc_id")
        gold_cids = set(item.get("gold_chunk_ids", []))
        
        # Gold section paths (from actual gold chunks)
        gold_sec_paths = set()
        for gcid in gold_cids:
            if gcid in chunk_id_to_idx:
                g_ch = chunks[chunk_id_to_idx[gcid]]
                g_path = normalize_section_path(g_ch.get("section_path", []))
                if g_path:
                    gold_sec_paths.add(g_path)
                    
        # Candidate selection
        if not use_selector:
            # Naive Top-20
            q_vec = q_emb[i]
            p_scores = corpus_embs @ q_vec
            d_scores = doc_embs @ q_vec
            comb = p_scores.copy()
            for c_idx, did in enumerate(chunk_doc_ids):
                if did in doc_id_to_idx:
                    comb[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
            top_b = comb.argsort()[::-1][:20]
            sel_idx = list(top_b)
            rej_idx = []
            comb_scores = comb
        else:
            sel_idx, top_b, rej_idx, comb_scores = candidate_selector(
                i, B=B, R=R, max_per_sec=max_per_sec, adj_penalty=adj_penalty
            )
            
        b_cids = [chunk_cids[idx] for idx in top_b]
        r_cids = [chunk_cids[idx] for idx in sel_idx]
        
        has_in_b = any(c in gold_cids for c in b_cids) if gold_cids else False
        has_in_r = any(c in gold_cids for c in r_cids) if gold_cids else False
        
        if has_in_b:
            input_cov_b_count += 1
            if has_in_r:
                retention_count += 1
        if has_in_r:
            output_cov_r_count += 1
            
        # Reranker scoring (Cross-Encoder on R=20 pairs)
        pairs = [[query, chunks[idx]["text"]] for idx in sel_idx]
        
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        rerank_scores = reranker.predict(pairs, batch_size=20, show_progress_bar=False)
        torch.cuda.synchronize()
        t_rerank = time.perf_counter() - t0
        latencies.append(t_rerank)
        
        # Rank by reranker score
        reranked_order = np.argsort(rerank_scores)[::-1]
        reranked_chunks = [chunks[sel_idx[idx]] for idx in reranked_order]
        reranked_scores = [float(rerank_scores[idx]) for idx in reranked_order]
        
        # Compute metrics
        reciprocal_rank = 0.0
        relevance_binary = []
        for rank, ch in enumerate(reranked_chunks, 1):
            is_rel = 1 if (ch["chunk_id"] in gold_cids) else 0
            relevance_binary.append(is_rel)
            if is_rel and reciprocal_rank == 0.0:
                reciprocal_rank = 1.0 / rank
        mrr_list.append(reciprocal_rank)
        ndcg_list.append(compute_ndcg_at_k(relevance_binary, k=10))
        
        for k in [1, 3, 5, 10]:
            top_k_chunks = reranked_chunks[:k]
            if any(ch["document_id"] == gold_doc for ch in top_k_chunks):
                doc_hits[k] += 1
            if any(normalize_section_path(ch.get("section_path", [])) in gold_sec_paths for ch in top_k_chunks):
                sec_hits[k] += 1
            if any(ch["chunk_id"] in gold_cids for ch in top_k_chunks):
                pas_hits[k] += 1
                
        # Per-query diagnostic record
        query_records.append({
            "query_id": item["query_id"],
            "query": item["query"],
            "gold_doc_id": gold_doc,
            "gold_chunk_ids": list(gold_cids),
            "b_pool_count": len(top_b),
            "selected_r20_ids": [chunks[idx]["chunk_id"] for idx in sel_idx],
            "rejected_candidate_ids": [chunks[idx]["chunk_id"] for idx in rej_idx],
            "relevant_in_b": has_in_b,
            "relevant_in_r": has_in_r,
            "top1_chunk_id": reranked_chunks[0]["chunk_id"],
            "top1_is_gold": reranked_chunks[0]["chunk_id"] in gold_cids,
            "hit_at_1": (reranked_chunks[0]["chunk_id"] in gold_cids),
            "hit_at_5": any(ch["chunk_id"] in gold_cids for ch in reranked_chunks[:5]),
            "mrr": reciprocal_rank,
            "ndcg_at_10": compute_ndcg_at_k(relevance_binary, k=10),
            "rerank_latency_ms": t_rerank * 1000.0
        })
        
    peak_vram_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)
    latencies_sorted = sorted(latencies)
    p50_latency = latencies_sorted[int(len(latencies_sorted) * 0.50)] * 1000.0
    p95_latency = latencies_sorted[int(len(latencies_sorted) * 0.95)] * 1000.0
    
    results = {
        "experiment_name": exp_name,
        "use_selector": use_selector,
        "B": B,
        "R": R,
        "max_per_sec": max_per_sec if use_selector else None,
        "adj_penalty": adj_penalty if use_selector else None,
        "N_queries": n_dev,
        "SelectorInputCoverage@B": (input_cov_b_count / n_dev) * 100.0,
        "SelectorOutputCoverage@20": (output_cov_r_count / n_dev) * 100.0,
        "Retention_pct": (retention_count / input_cov_b_count * 100.0) if input_cov_b_count else 0.0,
        "PassageHit@1": (pas_hits[1] / n_dev) * 100.0,
        "PassageHit@3": (pas_hits[3] / n_dev) * 100.0,
        "PassageHit@5": (pas_hits[5] / n_dev) * 100.0,
        "PassageHit@10": (pas_hits[10] / n_dev) * 100.0,
        "ParentSectionHit@1": (sec_hits[1] / n_dev) * 100.0,
        "ParentSectionHit@3": (sec_hits[3] / n_dev) * 100.0,
        "ParentSectionHit@5": (sec_hits[5] / n_dev) * 100.0,
        "ParentSectionHit@10": (sec_hits[10] / n_dev) * 100.0,
        "DocumentHit@1": (doc_hits[1] / n_dev) * 100.0,
        "DocumentHit@3": (doc_hits[3] / n_dev) * 100.0,
        "DocumentHit@5": (doc_hits[5] / n_dev) * 100.0,
        "DocumentHit@10": (doc_hits[10] / n_dev) * 100.0,
        "MRR": float(np.mean(mrr_list)),
        "nDCG@10": float(np.mean(ndcg_list)),
        "latency_p50_ms": p50_latency,
        "latency_p95_ms": p95_latency,
        "peak_vram_mb": peak_vram_mb,
        "query_records": query_records
    }
    
    print(f"  SelectorInputCoverage@B:    {results['SelectorInputCoverage@B']:5.1f}% ({input_cov_b_count}/{n_dev})")
    print(f"  SelectorOutputCoverage@20:  {results['SelectorOutputCoverage@20']:5.1f}% ({output_cov_r_count}/{n_dev})")
    print(f"  Retention:                  {results['Retention_pct']:5.1f}%")
    print(f"  PassageHit@1:               {results['PassageHit@1']:5.1f}% ({pas_hits[1]}/{n_dev})")
    print(f"  PassageHit@5:               {results['PassageHit@5']:5.1f}% ({pas_hits[5]}/{n_dev})")
    print(f"  PassageHit@10:              {results['PassageHit@10']:5.1f}% ({pas_hits[10]}/{n_dev})")
    print(f"  ParentSectionHit@1:         {results['ParentSectionHit@1']:5.1f}%")
    print(f"  MRR:                        {results['MRR']:.4f}")
    print(f"  nDCG@10:                    {results['nDCG@10']:.4f}")
    print(f"  Latency (p50 / p95):        {p50_latency:.1f} ms / {p95_latency:.1f} ms")
    print(f"  Peak VRAM:                  {peak_vram_mb:.1f} MB")
    
    return results

# Run the three requested comparisons:
# 1. Naive Top-20
# 2. B=200 -> R=20
# 3. B=500 -> R=20

res_naive = run_experiment("Naive Top-20 (Baseline)", use_selector=False, B=20, R=20)
res_b200 = run_experiment("Selector B=200 -> R=20", use_selector=True, B=200, R=20, max_per_sec=3, adj_penalty=0.03)
res_b500 = run_experiment("Selector B=500 -> R=20", use_selector=True, B=500, R=20, max_per_sec=3, adj_penalty=0.03)

# Save results
out_path = REPORTS_DIR / "renal_v5_candidate_selector_dev_a_results.json"
final_payload = {
    "benchmark": "RERANK_DEV_A_V5",
    "timestamp": "2026-09-11T06:50:00+00:00",
    "naive_top20": res_naive,
    "b200_to_r20": res_b200,
    "b500_to_r20": res_b500,
    "comparison_summary": {
        "PassageHit@1": {
            "naive_top20": res_naive["PassageHit@1"],
            "b200_to_r20": res_b200["PassageHit@1"],
            "b500_to_r20": res_b500["PassageHit@1"],
        },
        "PassageHit@5": {
            "naive_top20": res_naive["PassageHit@5"],
            "b200_to_r20": res_b200["PassageHit@5"],
            "b500_to_r20": res_b500["PassageHit@5"],
        },
        "SelectorInputCoverage": {
            "naive_top20": res_naive["SelectorInputCoverage@B"],
            "b200_to_r20": res_b200["SelectorInputCoverage@B"],
            "b500_to_r20": res_b500["SelectorInputCoverage@B"],
        },
        "SelectorOutputCoverage": {
            "naive_top20": res_naive["SelectorOutputCoverage@20"],
            "b200_to_r20": res_b200["SelectorOutputCoverage@20"],
            "b500_to_r20": res_b500["SelectorOutputCoverage@20"],
        },
        "Retention": {
            "naive_top20": res_naive["Retention_pct"],
            "b200_to_r20": res_b200["Retention_pct"],
            "b500_to_r20": res_b500["Retention_pct"],
        },
        "MRR": {
            "naive_top20": res_naive["MRR"],
            "b200_to_r20": res_b200["MRR"],
            "b500_to_r20": res_b500["MRR"],
        },
        "nDCG@10": {
            "naive_top20": res_naive["nDCG@10"],
            "b200_to_r20": res_b200["nDCG@10"],
            "b500_to_r20": res_b500["nDCG@10"],
        },
        "latency_p50_ms": {
            "naive_top20": res_naive["latency_p50_ms"],
            "b200_to_r20": res_b200["latency_p50_ms"],
            "b500_to_r20": res_b500["latency_p50_ms"],
        },
        "peak_vram_mb": {
            "naive_top20": res_naive["peak_vram_mb"],
            "b200_to_r20": res_b200["peak_vram_mb"],
            "b500_to_r20": res_b500["peak_vram_mb"],
        }
    }
}

out_bytes = json.dumps(final_payload, indent=2, ensure_ascii=False).encode("utf-8")
out_path.write_bytes(out_bytes)
out_sha = hashlib.sha256(out_bytes).hexdigest()

print("\n" + "=" * 70)
print("SELECTOR EVALUATION COMPLETE & PERSISTED")
print("=" * 70)
print(f"Path:   {out_path}")
print(f"SHA256: {out_sha}")
