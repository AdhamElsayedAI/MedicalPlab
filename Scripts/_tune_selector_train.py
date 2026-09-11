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
from transformers import AutoModel, AutoTokenizer

ROOT = Path(".")
CACHE_DIR = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
TRAIN_CORE_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-core-v5.json"
TRAIN_VAL_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-val-v5.json"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
ALPHA_DOC_PRIOR = 0.18

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# 1. Load Chunks & Metadata
chunks = []
chunk_doc_ids = []
chunk_sec_ids = []
doc_to_chunks = {}

for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        chunks.append(ch)
        did = ch["document_id"]
        sec = tuple(ch.get("section_path", []))
        chunk_doc_ids.append(did)
        chunk_sec_ids.append((did, sec))
        doc_to_chunks.setdefault(did, []).append(len(chunks) - 1)

n_chunks = len(chunks)
doc_ids_sorted = sorted(list(doc_to_chunks.keys()))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
chunk_id_to_idx = {ch["chunk_id"]: i for i, ch in enumerate(chunks)}

# 2. Load Cached Embeddings
corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)
assert corpus_embs.shape == (2691, 1024)
assert doc_embs.shape == (23, 1024)

# 3. Load Queries
train_core = json.loads(TRAIN_CORE_PATH.read_bytes())
train_val = json.loads(TRAIN_VAL_PATH.read_bytes())

# 4. Encode Queries
tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device).eval()

def encode_queries(items):
    texts = [QUERY_INSTRUCTION + it["query"] for it in items]
    with torch.inference_mode():
        encoded = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        outputs = embed_model(**encoded)
        mask = encoded["attention_mask"].unsqueeze(-1)
        q_emb = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        q_emb = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)
    return q_emb

print(f"Encoding TRAIN_CORE (N={len(train_core)}) and TRAIN_VAL (N={len(train_val)})...")
q_core = encode_queries(train_core)
q_val = encode_queries(train_val)

# Free embed_model from GPU memory
del embed_model
del tokenizer
torch.cuda.empty_cache()

# 5. First-Stage Scoring Function
def get_first_stage_scores(q_vec):
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb_scores = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb_scores[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
    return comb_scores

# 6. Candidate Selector Implementation
def run_candidate_selector(comb_scores, B=200, R=20, max_per_sec=3, max_per_doc=6, mmr_lambda=0.0):
    # Get top B candidates from first-stage
    top_b_idx = comb_scores.argsort()[::-1][:B]
    
    selected_idx = []
    sec_counts = {}
    doc_counts = {}
    
    # Candidate pool representation
    # If mmr_lambda > 0, we do greedy MMR
    # Otherwise, greedy constrained selection with caps
    remaining = list(top_b_idx)
    
    while len(selected_idx) < R and remaining:
        best_cand = None
        best_val = -float("inf")
        best_cand_pos = -1
        
        for pos, c_idx in enumerate(remaining):
            did = chunk_doc_ids[c_idx]
            sec = chunk_sec_ids[c_idx]
            
            # Check hard caps
            if max_per_sec is not None and sec_counts.get(sec, 0) >= max_per_sec:
                continue
            if max_per_doc is not None and doc_counts.get(did, 0) >= max_per_doc:
                continue
            
            # Compute score
            base_score = comb_scores[c_idx]
            if mmr_lambda > 0.0 and selected_idx:
                # Max similarity with already selected
                sim_to_sel = np.max(corpus_embs[selected_idx] @ corpus_embs[c_idx])
                cand_score = base_score - mmr_lambda * sim_to_sel
            else:
                cand_score = base_score
                
            if cand_score > best_val:
                best_val = cand_score
                best_cand = c_idx
                best_cand_pos = pos
                if mmr_lambda == 0.0:
                    # Pure greed without MMR, first valid candidate has highest base_score
                    break
                    
        if best_cand is None:
            # If all remaining candidates violate caps, relax caps or take next best
            for pos, c_idx in enumerate(remaining):
                best_cand = c_idx
                best_cand_pos = pos
                break
                
        selected_idx.append(best_cand)
        did = chunk_doc_ids[best_cand]
        sec = chunk_sec_ids[best_cand]
        doc_counts[did] = doc_counts.get(did, 0) + 1
        sec_counts[sec] = sec_counts.get(sec, 0) + 1
        remaining.pop(best_cand_pos)
        
    return selected_idx, top_b_idx

# 7. Evaluate Selector Configurations on Split
def evaluate_split(items, q_embs, selector_fn, B=200, R=20):
    n = len(items)
    b_coverage = 0
    r_coverage = 0
    retention_count = 0
    
    for i, it in enumerate(items):
        gold_cids = set(it.get("gold_chunk_ids", []))
        if not gold_cids:
            continue
        comb_scores = get_first_stage_scores(q_embs[i])
        sel_idx, top_b_idx = selector_fn(comb_scores, B=B, R=R)
        
        b_cids = set(chunks[idx]["chunk_id"] for idx in top_b_idx)
        r_cids = set(chunks[idx]["chunk_id"] for idx in sel_idx)
        
        has_in_b = any(c in gold_cids for c in b_cids)
        has_in_r = any(c in gold_cids for c in r_cids)
        
        if has_in_b:
            b_coverage += 1
            if has_in_r:
                retention_count += 1
        if has_in_r:
            r_coverage += 1
            
    b_cov_pct = (b_coverage / n) * 100
    r_cov_pct = (r_coverage / n) * 100
    ret_pct = (retention_count / b_coverage * 100) if b_coverage > 0 else 0.0
    return {
        "N": n,
        "Coverage@B": b_cov_pct,
        "Coverage@R": r_cov_pct,
        "Retention": ret_pct,
        "B_count": b_coverage,
        "R_count": r_coverage,
        "Retained_count": retention_count
    }

print("\n" + "=" * 70)
print("BOUNDED SELECTOR SEARCH ON TRAIN_CORE (N=60)")
print("=" * 70)

configs = [
    # Label, max_per_sec, max_per_doc, mmr_lambda
    ("Naive Top-20 (No Selector)", None, None, 0.0),
    ("Cap Sec=3, Doc=6", 3, 6, 0.0),
    ("Cap Sec=2, Doc=5", 2, 5, 0.0),
    ("Cap Sec=2, Doc=4", 2, 4, 0.0),
    ("MMR Lambda=0.08 (No Cap)", None, None, 0.08),
    ("Hybrid: Cap Sec=3, Doc=6 + MMR 0.05", 3, 6, 0.05),
    ("Hybrid: Cap Sec=2, Doc=5 + MMR 0.05", 2, 5, 0.05),
]

for B in [200, 500]:
    print(f"\n--- Evaluation at B={B} -> R=20 on TRAIN_CORE ---")
    for name, sec_cap, doc_cap, lam in configs:
        def fn(scores, B=B, R=20, s=sec_cap, d=doc_cap, l=lam):
            return run_candidate_selector(scores, B=B, R=R, max_per_sec=s, max_per_doc=d, mmr_lambda=l)
        res = evaluate_split(train_core, q_core, fn, B=B, R=20)
        print(f"  {name:38s} | Cov@B: {res['Coverage@B']:5.1f}% | Cov@20: {res['Coverage@R']:5.1f}% ({res['R_count']:2d}/60) | Retention: {res['Retention']:5.1f}%")

print("\n" + "=" * 70)
print("VALIDATION ON TRAIN_VAL (N=20)")
print("=" * 70)

for B in [200, 500]:
    print(f"\n--- Evaluation at B={B} -> R=20 on TRAIN_VAL ---")
    for name, sec_cap, doc_cap, lam in configs:
        def fn(scores, B=B, R=20, s=sec_cap, d=doc_cap, l=lam):
            return run_candidate_selector(scores, B=B, R=R, max_per_sec=s, max_per_doc=d, mmr_lambda=l)
        res = evaluate_split(train_val, q_val, fn, B=B, R=20)
        print(f"  {name:38s} | Cov@B: {res['Coverage@B']:5.1f}% | Cov@20: {res['Coverage@R']:5.1f}% ({res['R_count']:2d}/20) | Retention: {res['Retention']:5.1f}%")
