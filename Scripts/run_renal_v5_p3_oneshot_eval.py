"""
MedicalPlab Renal V5 — One-Shot Evaluation of Frozen P3 on SELECT_VAL_CLEAN_V1 (N=20)
=====================================================================================
Evaluates the frozen P3 preselector against the predeclared confirmation gate:
- Primary Gate: OutputCoverage@20 >= 17/20 (85.0%)
- Naive Top20 Preservation: >= 95.0%
- Genuine Rescues: >= 2 rank 21+ rescues
- Output Budget: R exactly 20
- Downstream verification with frozen base Qwen3-Reranker-0.6B for PassageHit@1

Zero parameter tuning. Zero external label exposure.
"""

import sys
import json
import time
import re
import math
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import torch
from transformers import AutoModel, AutoTokenizer
from sentence_transformers import CrossEncoder

selval_path = _ROOT / "evaluation/renal/v5/renal-rerank-select-val-clean-v1.json"
chunks_dir = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
cache_dir = _ROOT / "Data/experiments/renal_v3/cache"
reports_dir = _ROOT / "reports/renal_v5"
spec_path = reports_dir / "renal_v5_p3_model_specification.json"
out_report = reports_dir / "renal_v5_p3_select_val_results.json"

# Load frozen P3 spec
p3_spec = json.loads(spec_path.read_text(encoding="utf-8"))
coefs = p3_spec["frozen_coefficients"]
intercept = p3_spec["frozen_intercept"]

w_dense = coefs["dense_combined"]
w_bm25 = coefs["bm25_sparse"]
w_sec = coefs["section_centroid"]
w_jaccard = coefs["lexical_jaccard"]
w_contain = coefs["lexical_containment"]

print("Loaded Frozen P3 Specification:")
print(f"  Model Name: {p3_spec['model_name']}")
print(f"  Weights: Dense={w_dense:.4f}, BM25={w_bm25:.4f}, SecCentroid={w_sec:.4f}, Jaccard={w_jaccard:.4f}, Containment={w_contain:.4f}")
print(f"  Intercept: {intercept:.4f}")

# Load chunks
chunks = []
chunk_doc_ids = []
chunk_sec_ids = []
chunk_texts = []
chunk_id_to_idx = {}

for p in sorted(chunks_dir.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        c_idx = len(chunks)
        cid = ch["chunk_id"]
        chunks.append(ch)
        chunk_id_to_idx[cid] = c_idx
        chunk_doc_ids.append(ch["document_id"])
        sec_id = ch.get("parent_section_id") or f"{ch['document_id']}_{'_'.join(ch.get('section_path', []))}"
        chunk_sec_ids.append(sec_id)
        chunk_texts.append(ch.get("text", ""))

n_chunks = len(chunks)
doc_ids_sorted = sorted(list(set(chunk_doc_ids)))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}

# Precomputed embeddings
corpus_embs = np.load(cache_dir / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(cache_dir / "all23_doc_embeddings.npy").astype(np.float32)

# Section Centroids
sec_ids_unique = sorted(list(set(chunk_sec_ids)))
sec_id_to_idx = {sid: i for i, sid in enumerate(sec_ids_unique)}
sec_chunk_indices = defaultdict(list)
for c_idx, sid in enumerate(chunk_sec_ids):
    sec_chunk_indices[sid].append(c_idx)

sec_centroids = np.zeros((len(sec_ids_unique), corpus_embs.shape[1]), dtype=np.float32)
for sid, c_indices in sec_chunk_indices.items():
    s_idx = sec_id_to_idx[sid]
    centroid = corpus_embs[c_indices].mean(axis=0)
    norm = np.linalg.norm(centroid)
    if norm > 1e-9:
        centroid /= norm
    sec_centroids[s_idx] = centroid

# BM25 index
def tokenize(text):
    return re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())

chunk_tokens = [tokenize(t) for t in chunk_texts]
chunk_lens = np.array([len(t) for t in chunk_tokens], dtype=np.float32)
avg_chunk_len = float(np.mean(chunk_lens))

df = Counter()
for tokens in chunk_tokens:
    df.update(set(tokens))

k1 = 1.5
b = 0.75
idf = {term: math.log((n_chunks - freq + 0.5) / (freq + 0.5) + 1.0) for term, freq in df.items()}

def compute_bm25(q_tokens, c_idx):
    c_toks = chunk_tokens[c_idx]
    doc_len = chunk_lens[c_idx]
    counts = Counter(c_toks)
    score = 0.0
    for term in q_tokens:
        if term in counts:
            tf = counts[term]
            term_idf = idf.get(term, 0.0)
            denom = tf + k1 * (1.0 - b + b * (doc_len / avg_chunk_len))
            score += term_idf * (tf * (k1 + 1.0)) / denom
    return score

# Load validation queries
items = json.loads(selval_path.read_text(encoding="utf-8"))
n_val = len(items)
print(f"Loaded {n_val} validation queries from {selval_path.name}")

# Encode queries
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True)
mod = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True).to(device).eval()

QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
q_texts = [QUERY_INSTRUCTION + it["query"] for it in items]

with torch.inference_mode():
    enc = tok(q_texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
    out = mod(**enc)
    mask = enc["attention_mask"].unsqueeze(-1)
    q_embs = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
    q_embs = torch.nn.functional.normalize(q_embs, p=2, dim=1).cpu().numpy().astype(np.float32)

# First-Stage Retrieval (B=500)
query_candidate_pools = []
query_golds = []
query_naive_top20 = []

for i, it in enumerate(items):
    g_cids = it.get("gold_chunk_ids", [])
    g_indices = set(chunk_id_to_idx[cid] for cid in g_cids if cid in chunk_id_to_idx)
    query_golds.append(g_indices)
    
    q_vec = q_embs[i]
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb_scores = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb_scores[c_idx] += 0.18 * d_scores[doc_id_to_idx[did]]
            
    b500_indices = comb_scores.argsort()[::-1][:500].tolist()
    query_candidate_pools.append(b500_indices)
    query_naive_top20.append(set(b500_indices[:20]))

b500_cov = sum(1 for i in range(n_val) if any(c in query_candidate_pools[i] for c in query_golds[i]))
naive_cov = sum(1 for i in range(n_val) if any(c in query_naive_top20[i] for c in query_golds[i]))

print(f"\nBaseline First-Stage Retrieval on SELECT_VAL_CLEAN_V1 (N={n_val}):")
print(f"  B=500 Candidate Coverage: {b500_cov}/{n_val} ({b500_cov/n_val*100:.1f}%)")
print(f"  Naive Top-20 Coverage:   {naive_cov}/{n_val} ({naive_cov/n_val*100:.1f}%)")

# Execute Frozen P3 Scoring on SELECT_VAL
print("\n" + "=" * 80)
print("EXECUTING FROZEN P3 PRESELECTOR ON SELECT_VAL_CLEAN_V1 (N=20)")
print("=" * 80)

p3_top20_pools = []
p3_scores_list = []
per_query_results = []

cov20_p3 = 0
naive_preserved = 0
rescues = 0
lost = 0
ranks_p3 = []
mrr_sum = 0.0

t0_p3 = time.perf_counter()

for i, it in enumerate(items):
    qid = it["query_id"]
    q_text = it["query"]
    q_tokens = tokenize(q_text)
    q_tokens_set = set(q_tokens)
    q_vec = q_embs[i]
    golds = query_golds[i]
    cand_indices = query_candidate_pools[i]
    
    # Feature extraction (identical to frozen training procedure)
    cand_doc_indices = [doc_id_to_idx[chunk_doc_ids[c]] for c in cand_indices]
    cand_sec_indices = [sec_id_to_idx[chunk_sec_ids[c]] for c in cand_indices]
    
    f_dense = (corpus_embs[cand_indices] @ q_vec).astype(np.float32)
    f_doc = (doc_embs[cand_doc_indices] @ q_vec).astype(np.float32)
    f_comb = f_dense + 0.18 * f_doc
    
    f_bm25 = np.array([compute_bm25(q_tokens, c) for c in cand_indices], dtype=np.float32)
    f_sec = (sec_centroids[cand_sec_indices] @ q_vec).astype(np.float32)
    
    f_jaccard = np.zeros(500, dtype=np.float32)
    f_containment = np.zeros(500, dtype=np.float32)
    for k, c in enumerate(cand_indices):
        c_toks_set = set(chunk_tokens[c])
        inter = len(q_tokens_set.intersection(c_toks_set))
        union = len(q_tokens_set.union(c_toks_set))
        f_jaccard[k] = inter / (union + 1e-9)
        f_containment[k] = inter / (len(q_tokens_set) + 1e-9)
        
    X_q = np.column_stack([f_comb, f_bm25, f_sec, f_jaccard, f_containment])
    
    # Preprocessing: query-standardized z-score
    mean_q = np.mean(X_q, axis=0)
    std_q = np.std(X_q, axis=0) + 1e-9
    X_q_norm = (X_q - mean_q) / std_q
    
    # Model inference: logits = w^T z + b
    weights_vec = np.array([w_dense, w_bm25, w_sec, w_jaccard, w_contain], dtype=np.float32)
    logits = X_q_norm @ weights_vec + intercept
    
    # Rank descending
    order = np.argsort(-logits)
    top20_indices = [cand_indices[idx] for idx in order[:20]]
    p3_top20_pools.append(top20_indices)
    p3_scores_list.append(logits)
    
    # Check coverage
    in_naive = any(c in query_naive_top20[i] for c in golds)
    in_p3 = any(c in set(top20_indices) for c in golds)
    
    best_r = 999999
    for r, idx in enumerate(order, 1):
        if cand_indices[idx] in golds:
            best_r = r
            break
            
    ranks_p3.append(best_r)
    if best_r < 999999:
        mrr_sum += 1.0 / best_r
        
    if in_p3:
        cov20_p3 += 1
    if in_naive and in_p3:
        naive_preserved += 1
    elif in_naive and not in_p3:
        lost += 1
    elif not in_naive and in_p3:
        rescues += 1
        
    gold_cid = list(it.get("gold_chunk_ids", [""]))[0]
    dense_rank = query_candidate_pools[i].index(chunk_id_to_idx[gold_cid]) + 1 if chunk_id_to_idx[gold_cid] in query_candidate_pools[i] else 999
    
    per_query_results.append({
        "query_id": qid,
        "gold_chunk_id": gold_cid,
        "dense_rank": int(dense_rank),
        "p3_rank": int(best_r),
        "in_naive": bool(in_naive),
        "in_p3": bool(in_p3),
        "is_rescue": bool(not in_naive and in_p3),
        "is_lost": bool(in_naive and not in_p3)
    })

p3_duration = time.perf_counter() - t0_p3
p3_latency_ms = (p3_duration / n_val) * 1000.0

ranks_arr = np.array(ranks_p3)
p3_mrr = float(mrr_sum / n_val)
p3_med = float(np.median(ranks_arr))
p3_p75 = float(np.percentile(ranks_arr, 75))
p3_p90 = float(np.percentile(ranks_arr, 90))

print("\n" + "=" * 80)
print("ONE-SHOT VALIDATION RESULTS ON SELECT_VAL_CLEAN_V1 (N=20)")
print("=" * 80)
print(f"OutputCoverage@20:       {cov20_p3}/{n_val} ({cov20_p3/n_val*100:.1f}%)")
print(f"Naive Top-20 Preserved:  {naive_preserved}/{naive_cov} ({naive_preserved/naive_cov*100:.1f}%)")
print(f"Rank 21+ Rescues:        +{rescues}")
print(f"Relevant Cases Lost:     -{lost}")
print(f"MRR:                     {p3_mrr:.4f}")
print(f"Median Rank:             {p3_med:.1f} (p75={p3_p75:.1f}, p90={p3_p90:.1f})")
print(f"Latency:                 {p3_latency_ms:.2f} ms/query")

# PassageHit@1 Verification using Frozen Base Qwen3-Reranker-0.6B
print("\n" + "=" * 80)
print("VERIFYING DOWNSTREAM PASSAGEHIT@1 WITH FROZEN BASE QWEN3-RERANKER")
print("=" * 80)

reranker = CrossEncoder("Qwen/Qwen3-Reranker-0.6B", local_files_only=True)

hit1_naive = 0
hit1_p3 = 0

for i, it in enumerate(items):
    q_text = it["query"]
    golds = query_golds[i]
    
    # Naive Top-20
    naive_cands = list(query_candidate_pools[i][:20])
    naive_pairs = [[q_text, chunk_texts[c]] for c in naive_cands]
    naive_scores = reranker.predict(naive_pairs)
    naive_top1 = naive_cands[np.argmax(naive_scores)]
    if naive_top1 in golds:
        hit1_naive += 1
        
    # P3 Top-20
    p3_cands = p3_top20_pools[i]
    p3_pairs = [[q_text, chunk_texts[c]] for c in p3_cands]
    p3_scores = reranker.predict(p3_pairs)
    p3_top1 = p3_cands[np.argmax(p3_scores)]
    if p3_top1 in golds:
        hit1_p3 += 1
        
    per_query_results[i]["naive_hit1"] = bool(naive_top1 in golds)
    per_query_results[i]["p3_hit1"] = bool(p3_top1 in golds)

print(f"PassageHit@1 (Naive Top-20): {hit1_naive}/{n_val} ({hit1_naive/n_val*100:.1f}%)")
print(f"PassageHit@1 (P3 Top-20):    {hit1_p3}/{n_val} ({hit1_p3/n_val*100:.1f}%)")

# Predeclared Gate Evaluation
gate_target_met = cov20_p3 >= 17 # >= 85.0%
preservation_met = naive_preserved >= int(0.95 * naive_cov)
rescues_met = rescues >= 2
latency_met = p3_latency_ms <= 50.0

gate_status = "PASS_PREDECLARED_GATE" if (gate_target_met and preservation_met and rescues_met and latency_met) else "FAIL_PREDECLARED_GATE"

print("\n" + "=" * 80)
print(f"PREDECLARED GATE VERDICT: {gate_status}")
print("=" * 80)
print(f"1. OutputCoverage@20 >= 85% (17/20): {'PASS' if gate_target_met else 'FAIL'} ({cov20_p3}/{n_val} = {cov20_p3/n_val*100:.1f}%)")
print(f"2. Naive Top20 Preservation >= 95%:  {'PASS' if preservation_met else 'FAIL'} ({naive_preserved}/{naive_cov} = {naive_preserved/naive_cov*100:.1f}%)")
print(f"3. Multiple Rescues (>= 2):          {'PASS' if rescues_met else 'FAIL'} (+{rescues} rescues)")
print(f"4. Latency <= 50ms:                  {'PASS' if latency_met else 'FAIL'} ({p3_latency_ms:.2f} ms)")

report_data = {
    "report_type": "MEDICALPLAB_RENAL_V5_P3_SELECT_VAL_RESULTS",
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "validation_dataset": "renal-rerank-select-val-clean-v1.json",
    "n_items": n_val,
    "p3_model_name": p3_spec["model_name"],
    "gate_verdict": gate_status,
    "gate_breakdown": {
        "output_coverage_at_20": {
            "numerator": int(cov20_p3),
            "denominator": int(n_val),
            "percentage": float(cov20_p3 / n_val * 100.0),
            "gate_passed": bool(gate_target_met)
        },
        "naive_preservation": {
            "numerator": int(naive_preserved),
            "denominator": int(naive_cov),
            "percentage": float(naive_preserved / naive_cov * 100.0),
            "gate_passed": bool(preservation_met)
        },
        "genuine_rescues": {
            "count": int(rescues),
            "gate_passed": bool(rescues_met)
        },
        "relevant_lost": {
            "count": int(lost)
        },
        "latency_ms": {
            "value": float(p3_latency_ms),
            "gate_passed": bool(latency_met)
        }
    },
    "metrics": {
        "mrr": float(p3_mrr),
        "median_rank": float(p3_med),
        "p75_rank": float(p3_p75),
        "p90_rank": float(p3_p90),
        "passage_hit1_naive": {
            "numerator": int(hit1_naive),
            "denominator": int(n_val),
            "percentage": float(hit1_naive / n_val * 100.0)
        },
        "passage_hit1_p3": {
            "numerator": int(hit1_p3),
            "denominator": int(n_val),
            "percentage": float(hit1_p3 / n_val * 100.0)
        }
    },
    "per_query_results": per_query_results
}

out_report.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
print(f"\nFull validation results written to: {out_report}")
