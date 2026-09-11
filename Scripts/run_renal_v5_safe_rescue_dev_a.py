import os
import sys
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
from sentence_transformers import CrossEncoder
from transformers import AutoModel, AutoTokenizer

DEV_A_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
CHUNKS_DIR = _ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = _ROOT / "Data" / "experiments" / "renal_v3" / "cache"
REPORTS_DIR = _ROOT / "reports" / "renal_v5"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
ALPHA_DOC_PRIOR = 0.18

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def normalize_section_path(path):
    if not path:
        return ""
    if isinstance(path, list):
        return " > ".join(s.strip().lower() for s in path)
    return str(path).strip().lower()

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

# 1. Load Corpus
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

# 2. Load Embeddings
corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)

# 3. Load DEV-A Items
dev_a_bytes = DEV_A_PATH.read_bytes()
dev_a_sha = hashlib.sha256(dev_a_bytes).hexdigest()
dev_a = json.loads(dev_a_bytes)
n_dev = len(dev_a)
print(f"Loaded DEV-A: N={n_dev} items (SHA: {dev_a_sha})")

# 4. Encode Queries
tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device).eval()

query_texts = [QUERY_INSTRUCTION + it["query"] for it in dev_a]
with torch.inference_mode():
    enc = tokenizer(query_texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
    out = embed_model(**enc)
    mask = enc["attention_mask"].unsqueeze(-1)
    q_emb = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
    q_emb = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)

del embed_model
del tokenizer
torch.cuda.empty_cache()

# Load Reranker
print("Loading Qwen3-Reranker-0.6B...")
reranker = CrossEncoder(RERANK_MODEL_ID, device="cuda:0", trust_remote_code=True)
torch.cuda.synchronize()
_ = reranker.predict([["warmup query", "warmup text"] for _ in range(2)], batch_size=2, show_progress_bar=False)
torch.cuda.synchronize()

def compute_first_stage_scores(q_vec):
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
    return comb

# Candidate A: SAFE RESCUE SELECTOR
def select_safe_rescue(comb_scores, B=200, R=20, k_core=14, sim_thresh=0.88):
    top_b = comb_scores.argsort()[::-1][:B]
    naive_top20 = list(top_b[:R])
    
    selected = list(naive_top20[:k_core])
    selected_set = set(selected)
    slots_to_fill = 0
    
    for idx in naive_top20[k_core:]:
        is_adjacent = any(abs(idx - s) <= 1 for s in selected)
        is_high_sim = False
        if selected:
            max_sim = np.max(corpus_embs[selected] @ corpus_embs[idx])
            sec_match = any(chunk_sec_paths[idx] == chunk_sec_paths[s] and chunk_doc_ids[idx] == chunk_doc_ids[s] for s in selected)
            if sec_match and max_sim >= sim_thresh:
                is_high_sim = True
                
        if is_adjacent or is_high_sim:
            slots_to_fill += 1
        else:
            selected.append(idx)
            selected_set.add(idx)
            
    if slots_to_fill > 0:
        for cand in top_b[R:]:
            if cand in selected_set:
                continue
            is_adj = any(abs(cand - s) <= 1 for s in selected)
            if is_adj:
                continue
            max_sim = np.max(corpus_embs[selected] @ corpus_embs[cand])
            if max_sim >= 0.92:
                continue
            selected.append(cand)
            selected_set.add(cand)
            slots_to_fill -= 1
            if slots_to_fill == 0 or len(selected) == R:
                break
                
    if len(selected) < R:
        for cand in top_b:
            if cand not in selected_set:
                selected.append(cand)
                selected_set.add(cand)
                if len(selected) == R:
                    break
                    
    return selected, top_b

# Bounded Evaluation on DEV-A
print("\n" + "=" * 80)
print("BOUNDED ONE-SHOT EVALUATION OF CANDIDATE A (SAFE RESCUE) ON DEV-A (N=50)")
print("=" * 80)

doc_hits = {1: 0, 3: 0, 5: 0, 10: 0}
sec_hits = {1: 0, 3: 0, 5: 0, 10: 0}
pas_hits = {1: 0, 3: 0, 5: 0, 10: 0}

cov_b_count = 0
cov_r_count = 0
naive_cov_count = 0
naive_preserved = 0
rescues_count = 0
lost_count = 0

mrr_list = []
ndcg_list = []
latencies = []
query_records = []

torch.cuda.reset_peak_memory_stats()

for i, it in enumerate(dev_a):
    query = it["query"]
    gold_doc = it.get("gold_doc_id")
    gold_cids = set(it.get("gold_chunk_ids", []))
    
    gold_sec_paths = set()
    for gcid in gold_cids:
        if gcid in chunk_id_to_idx:
            g_ch = chunks[chunk_id_to_idx[gcid]]
            g_path = normalize_section_path(g_ch.get("section_path", []))
            if g_path:
                gold_sec_paths.add(g_path)
                
    comb = compute_first_stage_scores(q_emb[i])
    top_b = comb.argsort()[::-1][:200]
    naive_top20 = list(top_b[:20])
    has_in_naive = any(chunk_cids[c] in gold_cids for c in naive_top20) if gold_cids else False
    if has_in_naive:
        naive_cov_count += 1
        
    sel_idx, _ = select_safe_rescue(comb, B=200, R=20, k_core=14, sim_thresh=0.88)
    
    b_cids = [chunk_cids[c] for c in top_b]
    r_cids = [chunk_cids[c] for c in sel_idx]
    
    has_in_b = any(c in gold_cids for c in b_cids) if gold_cids else False
    has_in_r = any(c in gold_cids for c in r_cids) if gold_cids else False
    
    if has_in_b:
        cov_b_count += 1
    if has_in_r:
        cov_r_count += 1
        
    if has_in_naive and has_in_r:
        naive_preserved += 1
    elif has_in_naive and not has_in_r:
        lost_count += 1
    elif not has_in_naive and has_in_r:
        rescues_count += 1
        
    # CrossEncoder reranking
    pairs = [[query, chunks[c]["text"]] for c in sel_idx]
    
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    rerank_scores = reranker.predict(pairs, batch_size=20, show_progress_bar=False)
    torch.cuda.synchronize()
    t_rerank = time.perf_counter() - t0
    latencies.append(t_rerank)
    
    order = np.argsort(rerank_scores)[::-1]
    reranked_chunks = [chunks[sel_idx[idx]] for idx in order]
    
    reciprocal_rank = 0.0
    rel_binary = []
    for rank, ch in enumerate(reranked_chunks, 1):
        is_rel = 1 if (ch["chunk_id"] in gold_cids) else 0
        rel_binary.append(is_rel)
        if is_rel and reciprocal_rank == 0.0:
            reciprocal_rank = 1.0 / rank
    mrr_list.append(reciprocal_rank)
    ndcg_list.append(compute_ndcg_at_k(rel_binary, k=10))
    
    for k in [1, 3, 5, 10]:
        top_k = reranked_chunks[:k]
        if any(ch["document_id"] == gold_doc for ch in top_k):
            doc_hits[k] += 1
        if any(normalize_section_path(ch.get("section_path", [])) in gold_sec_paths for ch in top_k):
            sec_hits[k] += 1
        if any(ch["chunk_id"] in gold_cids for ch in top_k):
            pas_hits[k] += 1
            
    query_records.append({
        "query_id": it["query_id"],
        "query": it["query"],
        "has_in_naive": has_in_naive,
        "has_in_b": has_in_b,
        "has_in_r": has_in_r,
        "top1_chunk_id": reranked_chunks[0]["chunk_id"],
        "top1_is_gold": (reranked_chunks[0]["chunk_id"] in gold_cids),
        "hit_at_1": (reranked_chunks[0]["chunk_id"] in gold_cids),
        "hit_at_5": any(ch["chunk_id"] in gold_cids for ch in reranked_chunks[:5]),
        "mrr": reciprocal_rank,
        "ndcg_at_10": compute_ndcg_at_k(rel_binary, k=10),
        "rerank_latency_ms": t_rerank * 1000.0
    })

peak_vram_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)
latencies_sorted = sorted(latencies)
p50_latency = latencies_sorted[int(len(latencies_sorted) * 0.50)] * 1000.0
p95_latency = latencies_sorted[int(len(latencies_sorted) * 0.95)] * 1000.0

retention_pct = (cov_r_count / cov_b_count * 100.0) if cov_b_count else 0.0
preservation_pct = (naive_preserved / naive_cov_count * 100.0) if naive_cov_count else 0.0

results_dev_a = {
    "selector_name": "SELECTOR_V5_SAFE_RESCUE_CANDIDATE_A",
    "benchmark": "RERANK_DEV_A_V5",
    "benchmark_sha256": dev_a_sha,
    "timestamp": "2026-09-11T07:20:00+00:00",
    "B": 200,
    "R": 20,
    "k_core": 14,
    "sim_thresh": 0.88,
    "N_queries": n_dev,
    "SelectorInputCoverage@B": (cov_b_count / n_dev) * 100.0,
    "SelectorOutputCoverage@20": (cov_r_count / n_dev) * 100.0,
    "RetentionRate": retention_pct,
    "NaiveTop20Coverage": (naive_cov_count / n_dev) * 100.0,
    "NaivePreserved": naive_preserved,
    "NaivePreservationRate": preservation_pct,
    "NewRescues": rescues_count,
    "CasesLost": lost_count,
    "PassageHit@1": (pas_hits[1] / n_dev) * 100.0,
    "PassageHit@3": (pas_hits[3] / n_dev) * 100.0,
    "PassageHit@5": (pas_hits[5] / n_dev) * 100.0,
    "PassageHit@10": (pas_hits[10] / n_dev) * 100.0,
    "ParentSectionHit@1": (sec_hits[1] / n_dev) * 100.0,
    "DocumentHit@1": (doc_hits[1] / n_dev) * 100.0,
    "MRR": float(np.mean(mrr_list)),
    "nDCG@10": float(np.mean(ndcg_list)),
    "latency_p50_ms": p50_latency,
    "latency_p95_ms": p95_latency,
    "peak_vram_mb": peak_vram_mb,
    "query_records": query_records
}

print(f"  InputCoverage@B:            {results_dev_a['SelectorInputCoverage@B']:5.1f}% ({cov_b_count}/{n_dev})")
print(f"  OutputCoverage@20:          {results_dev_a['SelectorOutputCoverage@20']:5.1f}% ({cov_r_count}/{n_dev})")
print(f"  RetentionRate:              {results_dev_a['RetentionRate']:5.1f}%")
print(f"  NaiveTop20Preservation:     {results_dev_a['NaivePreserved']}/30 ({results_dev_a['NaivePreservationRate']:5.1f}%)")
print(f"  NewRelevantRescues:        +{results_dev_a['NewRescues']}")
print(f"  RelevantCasesLost:         -{results_dev_a['CasesLost']}")
print(f"  PassageHit@1:               {results_dev_a['PassageHit@1']:5.1f}% ({pas_hits[1]}/{n_dev})")
print(f"  PassageHit@5:               {results_dev_a['PassageHit@5']:5.1f}% ({pas_hits[5]}/{n_dev})")
print(f"  MRR:                        {results_dev_a['MRR']:.4f}")
print(f"  nDCG@10:                    {results_dev_a['nDCG@10']:.4f}")
print(f"  Latency (p50 / p95):        {p50_latency:.1f} ms / {p95_latency:.1f} ms")
print(f"  Peak VRAM:                  {peak_vram_mb:.1f} MB")

out_file = REPORTS_DIR / "renal_v5_safe_rescue_dev_a_results.json"
out_bytes = json.dumps(results_dev_a, indent=2).encode("utf-8")
out_file.write_bytes(out_bytes)
out_sha = hashlib.sha256(out_bytes).hexdigest()
print(f"\nPersisted DEV-A Results: {out_file}")
print(f"SHA-256: {out_sha}")
