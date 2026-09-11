import os
import sys
import json
from pathlib import Path
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

CACHE_DIR = _ROOT / "Data" / "experiments" / "renal_v3" / "cache"
CHUNKS_DIR = _ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
TRAIN_CORE_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-core-v5.json"
TRAIN_VAL_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-val-v5.json"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
ALPHA_DOC_PRIOR = 0.18

chunks = []
chunk_doc_ids = []
chunk_cids = []
doc_to_chunks = {}

for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        chunks.append(ch)
        did = ch["document_id"]
        cid = ch["chunk_id"]
        chunk_doc_ids.append(did)
        chunk_cids.append(cid)
        doc_to_chunks.setdefault(did, []).append(len(chunks) - 1)

doc_ids_sorted = sorted(list(doc_to_chunks.keys()))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}

corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)

train_core = json.loads(TRAIN_CORE_PATH.read_bytes())
train_val = json.loads(TRAIN_VAL_PATH.read_bytes())

tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to("cuda:0").eval()

def encode_queries(items):
    texts = [QUERY_INSTRUCTION + it["query"] for it in items]
    with torch.inference_mode():
        encoded = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to("cuda:0")
        outputs = embed_model(**encoded)
        mask = encoded["attention_mask"].unsqueeze(-1)
        q_emb = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        q_emb = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)
    return q_emb

q_core = encode_queries(train_core)
q_val = encode_queries(train_val)
del embed_model
del tokenizer
torch.cuda.empty_cache()

def get_first_stage_scores(q_vec):
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb_scores = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb_scores[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
    return comb_scores

# Test bounded selectors:
# 1. Soft Doc Diminishing Return (doc_decay)
# 2. Adjacent Chunk Suppression (adj_suppress)
# 3. Soft Cosine MMR (mmr_lambda)
# 4. Combinations

def select_candidates(comb_scores, B=200, R=20, doc_decay=0.0, adj_penalty=0.0, mmr_lambda=0.0):
    top_b = comb_scores.argsort()[::-1][:B]
    
    selected = []
    selected_set = set()
    doc_counts = {}
    
    cand_pool = list(top_b)
    
    for _ in range(R):
        best_cand = None
        best_score = -float("inf")
        best_pos = -1
        
        for pos, c_idx in enumerate(cand_pool):
            base_s = comb_scores[c_idx]
            did = chunk_doc_ids[c_idx]
            
            penalty = 0.0
            # Doc diminishing return penalty
            if doc_decay > 0.0:
                n_doc = doc_counts.get(did, 0)
                penalty += doc_decay * np.log1p(n_doc)
                
            # Adjacent chunk penalty: if c_idx - 1 or c_idx + 1 in selected
            if adj_penalty > 0.0:
                if (c_idx - 1) in selected_set or (c_idx + 1) in selected_set:
                    penalty += adj_penalty
                    
            # Soft MMR cosine similarity
            if mmr_lambda > 0.0 and selected:
                sim = np.max(corpus_embs[selected] @ corpus_embs[c_idx])
                penalty += mmr_lambda * sim
                
            eff_score = base_s - penalty
            if eff_score > best_score:
                best_score = eff_score
                best_cand = c_idx
                best_pos = pos
                
        if best_cand is not None:
            selected.append(best_cand)
            selected_set.add(best_cand)
            did = chunk_doc_ids[best_cand]
            doc_counts[did] = doc_counts.get(did, 0) + 1
            cand_pool.pop(best_pos)
            
    return selected, top_b

configs = [
    ("Naive Top-20", 0.0, 0.0, 0.0),
    ("AdjSuppress 0.03", 0.0, 0.03, 0.0),
    ("AdjSuppress 0.05", 0.0, 0.05, 0.0),
    ("DocDecay 0.02", 0.02, 0.0, 0.0),
    ("DocDecay 0.03", 0.03, 0.0, 0.0),
    ("DocDecay 0.04", 0.04, 0.0, 0.0),
    ("DocDecay 0.02 + Adj 0.03", 0.02, 0.03, 0.0),
    ("DocDecay 0.03 + Adj 0.03", 0.03, 0.03, 0.0),
    ("MMR 0.03", 0.0, 0.0, 0.03),
    ("MMR 0.05", 0.0, 0.0, 0.05),
    ("DocDecay 0.02 + MMR 0.03", 0.02, 0.0, 0.03),
]

def eval_split(items, q_embs, B, config):
    name, dd, ap, ml = config
    cov_b = 0
    cov_r = 0
    retained = 0
    n = len(items)
    for i, it in enumerate(items):
        golds = set(it.get("gold_chunk_ids", []))
        if not golds:
            continue
        scores = get_first_stage_scores(q_embs[i])
        sel, top_b = select_candidates(scores, B=B, R=20, doc_decay=dd, adj_penalty=ap, mmr_lambda=ml)
        b_cids = set(chunk_cids[idx] for idx in top_b)
        r_cids = set(chunk_cids[idx] for idx in sel)
        in_b = any(c in golds for c in b_cids)
        in_r = any(c in golds for c in r_cids)
        if in_b:
            cov_b += 1
            if in_r:
                retained += 1
        if in_r:
            cov_r += 1
    return cov_b, cov_r, retained, n

print("=" * 70)
print("BOUNDED SELECTOR EXPERIMENTS ON TRAIN_CORE (N=60)")
print("=" * 70)
for B in [200, 500]:
    print(f"\n--- Pool B={B} -> R=20 on TRAIN_CORE ---")
    for cfg in configs:
        cb, cr, ret, n = eval_split(train_core, q_core, B, cfg)
        cov_r_pct = cr / n * 100
        ret_pct = ret / cb * 100 if cb else 0
        diff = cr - 37 # 37 was naive top-20
        diff_str = f"(+{diff})" if diff > 0 else f"({diff})"
        print(f"  {cfg[0]:28s} | Output Cov@20: {cov_r_pct:5.1f}% ({cr:2d}/60) {diff_str:>5s} | Retention: {ret_pct:5.1f}%")

print("\n" + "=" * 70)
print("BOUNDED SELECTOR VALIDATION ON TRAIN_VAL (N=20)")
print("=" * 70)
for B in [200, 500]:
    print(f"\n--- Pool B={B} -> R=20 on TRAIN_VAL ---")
    for cfg in configs:
        cb, cr, ret, n = eval_split(train_val, q_val, B, cfg)
        cov_r_pct = cr / n * 100
        ret_pct = ret / cb * 100 if cb else 0
        diff = cr - 12 # 12 was naive top-20
        diff_str = f"(+{diff})" if diff > 0 else f"({diff})"
        print(f"  {cfg[0]:28s} | Output Cov@20: {cov_r_pct:5.1f}% ({cr:2d}/20) {diff_str:>5s} | Retention: {ret_pct:5.1f}%")
