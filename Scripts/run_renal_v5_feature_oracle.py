"""
MedicalPlab Renal V5 — TRAIN_CORE-Only 10-Feature Oracle & Ablation Audit
=========================================================================
Strictly evaluates on TRAIN_CORE_CLEAN (N=60 query families) at B=500.
Zero exposure to DEV-A, DEV-B, or consumed TRAIN_VAL labels.

Feature families evaluated:
 1. Dense passage score & rank
 2. Document score & rank
 3. Document prior (Dense + 0.18 * Doc)
 4. Section centroid similarity
 5. Section structural similarity
 6. BM25 / sparse relevance
 7. Heading / title similarity
 8. Lexical overlap (Jaccard, containment)
 9. Medical entity / abbreviation overlap
10. Redundancy features (Adjacency, doc/sec crowding penalty)
and bounded combinations (RRF, Linear soft fusion, Deduplication).

Reports:
- Coverage@20 (count / 60, %)
- Coverage@50 (count / 60, %)
- MRR of best relevant passage
- Median best-relevant rank
- p75 / p90 best-relevant rank
- Incremental gain over dense-only baseline
- Latency / computational cost (ms/query)
"""

import sys
import re
import json
import time
import math
from pathlib import Path
from collections import Counter, defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

core_path = _ROOT / "evaluation/renal/v5/renal-rerank-train-core-v5-clean-v1.json"
chunks_dir = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
cache_dir = _ROOT / "Data/experiments/renal_v3/cache"
reg_path = _ROOT / "Data/metadata/renal_source_registry_v2.json"
reports_dir = _ROOT / "reports/renal_v5"
reports_dir.mkdir(parents=True, exist_ok=True)
out_report = reports_dir / "renal_v5_feature_oracle_report.json"

# Load core dataset
items = json.loads(core_path.read_text(encoding="utf-8"))
print(f"Loaded {len(items)} queries from {core_path.name}")

# Load registry metadata
doc_titles = {}
doc_topics = {}
if reg_path.exists():
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    for d in reg.get("documents", []):
        doc_titles[d["document_id"]] = d.get("title", "")
        doc_topics[d["document_id"]] = d.get("topic_tags", [])

# Load corpus chunks
chunks = []
chunk_doc_ids = []
chunk_sec_ids = []
chunk_headings = []
chunk_sec_paths = []
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
        chunk_headings.append(ch.get("heading", ""))
        chunk_sec_paths.append(" > ".join(ch.get("section_path", [])))
        chunk_texts.append(ch.get("text", ""))

n_chunks = len(chunks)
doc_ids_sorted = sorted(list(set(chunk_doc_ids)))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
print(f"Loaded {n_chunks} chunks across {len(doc_ids_sorted)} documents.")

# Load precomputed embeddings
corpus_embs = np.load(cache_dir / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(cache_dir / "all23_doc_embeddings.npy").astype(np.float32)

# Compute Section Centroid Embeddings
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
print(f"Computed {len(sec_ids_unique)} section centroid embeddings.")

# Section structural positions
chunk_pos_in_sec = np.zeros(n_chunks, dtype=np.float32)
sec_lengths = {sid: len(c_indices) for sid, c_indices in sec_chunk_indices.items()}
for sid, c_indices in sec_chunk_indices.items():
    total = len(c_indices)
    for pos, c_idx in enumerate(c_indices):
        chunk_pos_in_sec[c_idx] = (pos + 1) / total

# BM25 Corpus Indexing
def tokenize(text):
    return re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())

chunk_tokens = [tokenize(t) for t in chunk_texts]
chunk_lens = np.array([len(t) for t in chunk_tokens], dtype=np.float32)
avg_chunk_len = float(np.mean(chunk_lens))

# Document frequencies
df = Counter()
for tokens in chunk_tokens:
    df.update(set(tokens))

N_docs = n_chunks
k1 = 1.5
b = 0.75
idf = {term: math.log((N_docs - freq + 0.5) / (freq + 0.5) + 1.0) for term, freq in df.items()}
print("Indexed Okapi BM25 for all 2,691 chunks.")

# Medical terms glossary for Feature 9
RENAL_VOCAB = {
    "egfr", "gfr", "creatinine", "bun", "proteinuria", "albuminuria", "microalbuminuria",
    "hematuria", "aki", "ckd", "kdigo", "nephritic", "nephrotic", "glomerular", "glomerulus",
    "glomerulonephritis", "podocyte", "mesangial", "tubular", "interstitial", "rhabdomyolysis",
    "myoglobin", "hyperkalemia", "hypokalemia", "hyponatremia", "hypernatremia", "aldosterone",
    "renin", "angiotensin", "acei", "arb", "sglt2", "furosemide", "thiazide", "spironolactone",
    "dialysis", "hemodialysis", "peritoneal", "transplant", "calcineurin", "tacrolimus",
    "cyclosporine", "iga", "streptococcal", "membranous", "fsgs", "minimal", "change",
    "lupus", "anca", "vasculitis", "goodpasture", "antiglomerular", "alport", "polycystic",
    "adpkd", "prerenal", "intrinsic", "postrenal", "fractional", "excretion", "fena", "fenau",
    "osmolarity", "osmolality", "casts", "hyaline", "granular", "muddy", "brown", "wbc", "rbc",
    "bartter", "gitelman", "liddle", "fanconi", "rta", "acidosis", "alkalosis", "bicarbonate",
    "anion", "gap", "phosphate", "calcium", "oxalate", "nephrolithiasis", "calculus", "lithotripsy",
    "potassium", "sodium", "chloride", "urea", "nephrosclerosis", "tubulointerstitial", "nephritis"
}

# Encode queries with Qwen3
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

print(f"Encoded {len(items)} queries on {device}.")

# Extract Candidates at B=500 per query using baseline Dense + 0.18*Doc
# and precompute candidate-level feature values
query_candidate_pools = []
query_golds = []

for i, it in enumerate(items):
    qid = it["query_id"]
    g_cids = it.get("gold_chunk_ids", [])
    g_indices = [chunk_id_to_idx[cid] for cid in g_cids if cid in chunk_id_to_idx]
    query_golds.append(set(g_indices))
    
    q_vec = q_embs[i]
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    
    # Baseline combined dense score
    comb_scores = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb_scores[c_idx] += 0.18 * d_scores[doc_id_to_idx[did]]
            
    b500_indices = comb_scores.argsort()[::-1][:500].tolist()
    query_candidate_pools.append(b500_indices)

print("Generated B=500 candidate pools for all 60 queries.")

# Helper function to compute BM25 score for a query against a candidate chunk
def compute_bm25_candidate(q_tokens, c_idx):
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

# Precompute candidate features for each query
print("Extracting feature matrices for all 60 queries x 500 candidates...")
t0_feat = time.perf_counter()

# Features dict: feature_name -> list of length 60, each is array of shape (500,)
query_features = defaultdict(list)

for i, it in enumerate(items):
    q_text = it["query"]
    q_tokens = tokenize(q_text)
    q_tokens_set = set(q_tokens)
    q_med_tokens = q_tokens_set.intersection(RENAL_VOCAB)
    q_vec = q_embs[i]
    
    cand_indices = query_candidate_pools[i]
    
    # 1. Dense passage score
    f_dense = (corpus_embs[cand_indices] @ q_vec).astype(np.float32)
    
    # 2. Document score
    cand_doc_indices = [doc_id_to_idx[chunk_doc_ids[c]] for c in cand_indices]
    f_doc = (doc_embs[cand_doc_indices] @ q_vec).astype(np.float32)
    
    # 3. Document prior (Baseline combined score)
    f_baseline = f_dense + 0.18 * f_doc
    
    # 4. Section centroid similarity
    cand_sec_indices = [sec_id_to_idx[chunk_sec_ids[c]] for c in cand_indices]
    f_sec_centroid = (sec_centroids[cand_sec_indices] @ q_vec).astype(np.float32)
    
    # 5. Section structural position
    f_sec_struct = chunk_pos_in_sec[cand_indices]
    
    # 6. BM25 score
    f_bm25 = np.array([compute_bm25_candidate(q_tokens, c) for c in cand_indices], dtype=np.float32)
    
    # 7. Heading / Title lexical overlap
    f_heading = np.zeros(500, dtype=np.float32)
    for k, c in enumerate(cand_indices):
        head_toks = set(tokenize(chunk_headings[c] + " " + chunk_sec_paths[c] + " " + doc_titles.get(chunk_doc_ids[c], "")))
        if head_toks:
            f_heading[k] = len(q_tokens_set.intersection(head_toks)) / (len(q_tokens_set) + 1e-9)
            
    # 8. Lexical overlap (Token Jaccard and containment)
    f_jaccard = np.zeros(500, dtype=np.float32)
    f_containment = np.zeros(500, dtype=np.float32)
    for k, c in enumerate(cand_indices):
        c_toks_set = set(chunk_tokens[c])
        inter = len(q_tokens_set.intersection(c_toks_set))
        union = len(q_tokens_set.union(c_toks_set))
        f_jaccard[k] = inter / (union + 1e-9)
        f_containment[k] = inter / (len(q_tokens_set) + 1e-9)
    f_lexical = 0.5 * f_jaccard + 0.5 * f_containment
    
    # 9. Medical entity / abbreviation overlap
    f_med = np.zeros(500, dtype=np.float32)
    if q_med_tokens:
        for k, c in enumerate(cand_indices):
            c_toks_set = set(chunk_tokens[c])
            f_med[k] = len(q_med_tokens.intersection(c_toks_set)) / len(q_med_tokens)
            
    # 10. Redundancy / Doc crowding penalty feature
    # Measure frequency of doc in candidate pool
    cand_docs = [chunk_doc_ids[c] for c in cand_indices]
    doc_freqs = Counter(cand_docs)
    f_redundancy = np.array([1.0 / (doc_freqs[d] ** 0.5) for d in cand_docs], dtype=np.float32)
    
    query_features["dense_passage"].append(f_dense)
    query_features["document_score"].append(f_doc)
    query_features["document_prior_baseline"].append(f_baseline)
    query_features["section_centroid"].append(f_sec_centroid)
    query_features["section_structural"].append(f_sec_struct)
    query_features["bm25_sparse"].append(f_bm25)
    query_features["heading_title"].append(f_heading)
    query_features["lexical_overlap"].append(f_lexical)
    query_features["medical_entity"].append(f_med)
    query_features["redundancy_feature"].append(f_redundancy)

total_extraction_time = time.perf_counter() - t0_feat
avg_latency_ms = (total_extraction_time / 60.0) * 1000.0
print(f"Feature extraction completed in {total_extraction_time:.2f}s ({avg_latency_ms:.2f} ms/query).")

# Evaluation function for any candidate scoring / ranking strategy
def evaluate_ranking_strategy(score_generator_fn):
    cov_20 = 0
    cov_50 = 0
    mrr_sum = 0.0
    ranks = []
    
    t0 = time.perf_counter()
    for i in range(len(items)):
        golds = query_golds[i]
        cand_indices = query_candidate_pools[i]
        scores = score_generator_fn(i)
        
        # Rank candidates descending by score
        order = np.argsort(-scores)
        ordered_cands = [cand_indices[idx] for idx in order]
        
        # Find rank of best gold (1-indexed)
        best_rank = 999999
        for r, c in enumerate(ordered_cands, 1):
            if c in golds:
                best_rank = r
                break
                
        ranks.append(best_rank)
        if best_rank <= 20:
            cov_20 += 1
        if best_rank <= 50:
            cov_50 += 1
        if best_rank < 999999:
            mrr_sum += 1.0 / best_rank
            
    dur_ms = ((time.perf_counter() - t0) / 60.0) * 1000.0
    
    ranks_arr = np.array(ranks)
    med_rank = float(np.median(ranks_arr))
    p75_rank = float(np.percentile(ranks_arr, 75))
    p90_rank = float(np.percentile(ranks_arr, 90))
    mrr = float(mrr_sum / 60.0)
    
    return {
        "cov20_count": cov_20,
        "cov20_pct": float(cov_20 / 60.0 * 100.0),
        "cov50_count": cov_50,
        "cov50_pct": float(cov_50 / 60.0 * 100.0),
        "mrr": float(mrr),
        "median_rank": med_rank,
        "p75_rank": p75_rank,
        "p90_rank": p90_rank,
        "latency_ms": float(dur_ms + avg_latency_ms)
    }

# Helper: Reciprocal Rank Fusion on 2 or more score vectors
def rrf_scores(score_vectors, k=60):
    total = np.zeros(500, dtype=np.float32)
    for scores in score_vectors:
        order = np.argsort(-scores)
        ranks = np.empty_like(order)
        ranks[order] = np.arange(len(scores)) + 1
        total += 1.0 / (k + ranks)
    return total

# Standardize feature values per query
def z_score(arr):
    std = np.std(arr)
    if std < 1e-9:
        return arr - np.mean(arr)
    return (arr - np.mean(arr)) / std

# Helper: Bounded Deduplication Selector (preserves top Kcore, then picks diversity)
def deduplicate_scores(base_scores_fn, k_core=15, max_doc=6, max_sec=2):
    def fn(i):
        base_s = base_scores_fn(i)
        order = np.argsort(-base_s)
        cand_indices = query_candidate_pools[i]
        
        # We simulate a reranking score where selected items get high scores
        final_scores = np.zeros(500, dtype=np.float32)
        selected = []
        doc_counts = Counter()
        sec_counts = Counter()
        
        # Unconditionally take top k_core
        for idx in order[:k_core]:
            c = cand_indices[idx]
            selected.append(idx)
            doc_counts[chunk_doc_ids[c]] += 1
            sec_counts[chunk_sec_ids[c]] += 1
            
        # Fill remaining from rank k_core onwards with budget constraints
        for idx in order[k_core:]:
            if len(selected) >= 50:
                break
            c = cand_indices[idx]
            d = chunk_doc_ids[c]
            s = chunk_sec_ids[c]
            if doc_counts[d] < max_doc and sec_counts[s] < max_sec:
                selected.append(idx)
                doc_counts[d] += 1
                sec_counts[s] += 1
                
        # Fill any remainder
        for idx in order:
            if idx not in selected:
                selected.append(idx)
                
        # Assign descending synthetic scores
        for rank_pos, idx in enumerate(selected):
            final_scores[idx] = 1000.0 - rank_pos
        return final_scores
    return fn

configurations = {
    # Reference Baselines
    "01_Dense_Passage_Score": lambda i: query_features["dense_passage"][i],
    "02_Document_Score": lambda i: query_features["document_score"][i],
    "03_Document_Prior_Baseline": lambda i: query_features["document_prior_baseline"][i],
    "04_Section_Centroid": lambda i: query_features["section_centroid"][i],
    "05_Section_Structural": lambda i: query_features["section_structural"][i],
    "06_BM25_Sparse": lambda i: query_features["bm25_sparse"][i],
    "07_Heading_Title_Overlap": lambda i: query_features["heading_title"][i],
    "08_Lexical_Overlap": lambda i: query_features["lexical_overlap"][i],
    "09_Medical_Entity_Overlap": lambda i: query_features["medical_entity"][i],
    "10_Redundancy_Diversity_Score": lambda i: query_features["redundancy_feature"][i],
    
    # Bounded Combinations
    "11_Dense_plus_BM25_RRF60": lambda i: rrf_scores([
        query_features["document_prior_baseline"][i],
        query_features["bm25_sparse"][i]
    ], k=60),
    
    "12_Dense_plus_SecCentroid_RRF60": lambda i: rrf_scores([
        query_features["document_prior_baseline"][i],
        query_features["section_centroid"][i]
    ], k=60),
    
    "13_Dense_plus_Heading_RRF60": lambda i: rrf_scores([
        query_features["document_prior_baseline"][i],
        query_features["heading_title"][i]
    ], k=60),

    "14_Dense_plus_MedicalEntity_RRF60": lambda i: rrf_scores([
        query_features["document_prior_baseline"][i],
        query_features["medical_entity"][i]
    ], k=60),
    
    "15_TriHybrid_Dense_BM25_SecCentroid_RRF": lambda i: rrf_scores([
        query_features["document_prior_baseline"][i],
        query_features["bm25_sparse"][i],
        query_features["section_centroid"][i]
    ], k=60),
    
    "16_QuadHybrid_Dense_BM25_SecCentroid_MedEntity_RRF": lambda i: rrf_scores([
        query_features["document_prior_baseline"][i],
        query_features["bm25_sparse"][i],
        query_features["section_centroid"][i],
        query_features["medical_entity"][i]
    ], k=60),
    
    "17_LinearSoftFusion_ZScore_Dense_BM25_Centroid": lambda i: (
        1.0 * z_score(query_features["document_prior_baseline"][i]) +
        0.35 * z_score(query_features["bm25_sparse"][i]) +
        0.25 * z_score(query_features["section_centroid"][i]) +
        0.20 * z_score(query_features["heading_title"][i]) +
        0.20 * z_score(query_features["medical_entity"][i])
    ),
    
    "18_Dense_plus_SafeRescue_Deduplication": deduplicate_scores(
        lambda i: query_features["document_prior_baseline"][i], k_core=15, max_doc=6, max_sec=2
    ),
    
    "19_TriHybrid_plus_SafeRescue_Deduplication": deduplicate_scores(
        lambda i: rrf_scores([
            query_features["document_prior_baseline"][i],
            query_features["bm25_sparse"][i],
            query_features["section_centroid"][i]
        ], k=60), k_core=15, max_doc=6, max_sec=2
    ),
    
    "20_LinearFusion_plus_Deduplication": deduplicate_scores(
        lambda i: (
            1.0 * z_score(query_features["document_prior_baseline"][i]) +
            0.35 * z_score(query_features["bm25_sparse"][i]) +
            0.25 * z_score(query_features["section_centroid"][i]) +
            0.20 * z_score(query_features["heading_title"][i]) +
            0.20 * z_score(query_features["medical_entity"][i])
        ), k_core=15, max_doc=6, max_sec=2
    )
}

print("\n" + "=" * 80)
print("COMPUTING ABLATION MATRIX FOR ALL 20 CONFIGURATIONS ON TRAIN_CORE (N=60)")
print("=" * 80)

results = {}
baseline_cov20 = None

for name, fn in configurations.items():
    res = evaluate_ranking_strategy(fn)
    if baseline_cov20 is None:
        baseline_cov20 = res["cov20_count"]
    delta = res["cov20_count"] - baseline_cov20
    res["delta_cov20_vs_dense"] = delta
    results[name] = res
    print(f"{name:<45} | Cov@20: {res['cov20_count']:>2}/60 ({res['cov20_pct']:>5.1f}%) | Cov@50: {res['cov50_count']:>2}/60 ({res['cov50_pct']:>5.1f}%) | MRR: {res['mrr']:.4f} | Med: {res['median_rank']:>4.1f} | Delta: {delta:>+2}")

# Save full report
report_data = {
    "report_type": "MEDICALPLAB_RENAL_V5_TRAIN_CORE_FEATURE_ORACLE",
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "dataset": "renal-rerank-train-core-v5-clean-v1.json",
    "n_queries": 60,
    "candidate_pool_size": 500,
    "reference_baseline": "03_Document_Prior_Baseline",
    "results": results
}

out_report.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
print(f"\nFull report written to: {out_report}")
