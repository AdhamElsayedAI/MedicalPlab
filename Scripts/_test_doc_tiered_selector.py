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

CACHE_DIR = _ROOT / "Data" / "experiments" / "renal_v3" / "cache"
CHUNKS_DIR = _ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
TRAIN_CORE_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-core-v5.json"
TRAIN_VAL_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-val-v5.json"

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

import torch
from transformers import AutoModel, AutoTokenizer
EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
ALPHA_DOC_PRIOR = 0.18

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

# Document-tiered selector:
# 1. Rank documents by doc score
# 2. Allocate candidate slots to top K documents (e.g. Doc1: N1, Doc2: N2, Doc3: N3, Doc4: N4)
# 3. Chunks within each document are sorted by passage score or combined score
# 4. Fill remaining slots with global top scores
def select_doc_tiered(q_vec, B=200, R=20, doc_alloc=[8, 5, 4, 3]):
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb_scores = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb_scores[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
            
    top_b = comb_scores.argsort()[::-1][:B]
    top_b_set = set(top_b)
    
    # Sort docs by score
    doc_ranks = d_scores.argsort()[::-1]
    
    selected = []
    selected_set = set()
    
    # Tiered allocation from top documents, restricted to candidates inside top_b
    for rank_idx, n_slots in enumerate(doc_alloc):
        if rank_idx >= len(doc_ranks):
            break
        did = doc_ids_sorted[doc_ranks[rank_idx]]
        # Candidates in top_b belonging to this doc
        doc_cands = [c for c in top_b if chunk_doc_ids[c] == did and c not in selected_set]
        # Sort by comb_score
        doc_cands.sort(key=lambda c: comb_scores[c], reverse=True)
        take = doc_cands[:n_slots]
        for c in take:
            selected.append(c)
            selected_set.add(c)
            if len(selected) == R:
                break
        if len(selected) == R:
            break
            
    # Fill remaining from top_b
    if len(selected) < R:
        for c in top_b:
            if c not in selected_set:
                selected.append(c)
                selected_set.add(c)
                if len(selected) == R:
                    break
                    
    return selected, top_b

allocations = [
    ("Naive Top-20", None),
    ("Tiered [10, 5, 3, 2]", [10, 5, 3, 2]),
    ("Tiered [8, 5, 4, 3]", [8, 5, 4, 3]),
    ("Tiered [7, 5, 4, 2, 2]", [7, 5, 4, 2, 2]),
    ("Tiered [6, 5, 4, 3, 2]", [6, 5, 4, 3, 2]),
    ("Tiered [12, 4, 2, 2]", [12, 4, 2, 2]),
]

def eval_alloc(items, q_embs, B, alloc):
    cov_b = 0
    cov_r = 0
    retained = 0
    n = len(items)
    for i, it in enumerate(items):
        golds = set(it.get("gold_chunk_ids", []))
        if not golds:
            continue
        q_vec = q_embs[i]
        p_scores = corpus_embs @ q_vec
        d_scores = doc_embs @ q_vec
        comb_scores = p_scores.copy()
        for c_idx, did in enumerate(chunk_doc_ids):
            if did in doc_id_to_idx:
                comb_scores[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
        top_b = comb_scores.argsort()[::-1][:B]
        
        if alloc is None:
            sel = list(top_b[:20])
        else:
            sel, _ = select_doc_tiered(q_vec, B=B, R=20, doc_alloc=alloc)
            
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
print("TIERED SELECTOR ON TRAIN_CORE (N=60)")
print("=" * 70)
for B in [200, 500]:
    print(f"\n--- Pool B={B} -> R=20 on TRAIN_CORE ---")
    for name, alloc in allocations:
        cb, cr, ret, n = eval_alloc(train_core, q_core, B, alloc)
        cov_r_pct = cr / n * 100
        ret_pct = ret / cb * 100 if cb else 0
        diff = cr - 37
        diff_str = f"(+{diff})" if diff > 0 else f"({diff})"
        print(f"  {name:25s} | Output Cov@20: {cov_r_pct:5.1f}% ({cr:2d}/60) {diff_str:>5s} | Retention: {ret_pct:5.1f}%")

print("\n" + "=" * 70)
print("TIERED SELECTOR ON TRAIN_VAL (N=20)")
print("=" * 70)
for B in [200, 500]:
    print(f"\n--- Pool B={B} -> R=20 on TRAIN_VAL ---")
    for name, alloc in allocations:
        cb, cr, ret, n = eval_alloc(train_val, q_val, B, alloc)
        cov_r_pct = cr / n * 100
        ret_pct = ret / cb * 100 if cb else 0
        diff = cr - 12
        diff_str = f"(+{diff})" if diff > 0 else f"({diff})"
        print(f"  {name:25s} | Output Cov@20: {cov_r_pct:5.1f}% ({cr:2d}/20) {diff_str:>5s} | Retention: {ret_pct:5.1f}%")
