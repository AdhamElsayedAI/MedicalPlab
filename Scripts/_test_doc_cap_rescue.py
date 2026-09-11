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

def encode_items(items):
    texts = [QUERY_INSTRUCTION + it["query"] for it in items]
    with torch.inference_mode():
        enc = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to("cuda:0")
        out = embed_model(**enc)
        mask = enc["attention_mask"].unsqueeze(-1)
        q_emb = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        q_emb = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)
    return q_emb

q_core = encode_items(train_core)
q_val = encode_items(train_val)
del embed_model
del tokenizer
torch.cuda.empty_cache()

def compute_first_stage_scores(q_vec):
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
    return comb

# Safe Document-Cap Rescue Selector:
# Takes naive Top 20, but if any document has more than max_doc chunks,
# the excess chunks are replaced by the best candidates in pool B from other documents.
def select_doc_capped_rescue(comb_scores, B=200, R=20, max_doc=8):
    top_b = comb_scores.argsort()[::-1][:B]
    naive_top20 = list(top_b[:R])
    
    doc_counts = {}
    kept = []
    excess = []
    
    for c in naive_top20:
        did = chunk_doc_ids[c]
        doc_counts[did] = doc_counts.get(did, 0) + 1
        if doc_counts[did] <= max_doc:
            kept.append(c)
        else:
            excess.append(c)
            
    # If there are excess slots, fill them from top_b[R:] from documents with < max_doc
    if excess:
        kept_set = set(kept)
        for c in top_b[R:]:
            did = chunk_doc_ids[c]
            if doc_counts.get(did, 0) < max_doc and c not in kept_set:
                kept.append(c)
                kept_set.add(c)
                doc_counts[did] = doc_counts.get(did, 0) + 1
                if len(kept) == R:
                    break
                    
    # If still not full, backfill from excess
    if len(kept) < R:
        for c in excess:
            if c not in kept_set:
                kept.append(c)
                kept_set.add(c)
                if len(kept) == R:
                    break
                    
    return kept, top_b

print("=" * 70)
print("TESTING SAFE DOC-CAP RESCUE ON TRAIN_VAL (N=20)")
print("=" * 70)

for B in [200, 500]:
    print(f"\n--- B={B} on TRAIN_VAL ---")
    for max_d in [6, 7, 8, 10, 12, 15, 20]:
        n = len(train_val)
        cov_b = 0
        cov_r = 0
        rescues = 0
        lost = 0
        preserved = 0
        for i, it in enumerate(train_val):
            golds = set(it.get("gold_chunk_ids", []))
            comb = compute_first_stage_scores(q_val[i])
            top_b = comb.argsort()[::-1][:B]
            naive20 = list(top_b[:20])
            in_naive = any(chunk_cids[c] in golds for c in naive20)
            
            sel, _ = select_doc_capped_rescue(comb, B=B, R=20, max_doc=max_d)
            in_b = any(chunk_cids[c] in golds for c in top_b)
            in_r = any(chunk_cids[c] in golds for c in sel)
            
            if in_b:
                cov_b += 1
            if in_r:
                cov_r += 1
            if in_naive and in_r:
                preserved += 1
            elif in_naive and not in_r:
                lost += 1
            elif not in_naive and in_r:
                rescues += 1
                
        print(f"  max_doc={max_d:2d} | OutCov@20: {cov_r/n*100:5.1f}% ({cov_r:2d}/20) | Preserved: {preserved:2d}/12 | Rescues: +{rescues} | Lost: -{lost}")

print("\n" + "=" * 70)
print("TESTING SAFE DOC-CAP RESCUE ON TRAIN_CORE (N=60)")
print("=" * 70)

for B in [200, 500]:
    print(f"\n--- B={B} on TRAIN_CORE ---")
    for max_d in [6, 7, 8, 10, 12, 15, 20]:
        n = len(train_core)
        cov_b = 0
        cov_r = 0
        rescues = 0
        lost = 0
        preserved = 0
        for i, it in enumerate(train_core):
            golds = set(it.get("gold_chunk_ids", []))
            comb = compute_first_stage_scores(q_core[i])
            top_b = comb.argsort()[::-1][:B]
            naive20 = list(top_b[:20])
            in_naive = any(chunk_cids[c] in golds for c in naive20)
            
            sel, _ = select_doc_capped_rescue(comb, B=B, R=20, max_doc=max_d)
            in_b = any(chunk_cids[c] in golds for c in top_b)
            in_r = any(chunk_cids[c] in golds for c in sel)
            
            if in_b:
                cov_b += 1
            if in_r:
                cov_r += 1
            if in_naive and in_r:
                preserved += 1
            elif in_naive and not in_r:
                lost += 1
            elif not in_naive and in_r:
                rescues += 1
                
        print(f"  max_doc={max_d:2d} | OutCov@20: {cov_r/n*100:5.1f}% ({cov_r:2d}/60) | Preserved: {preserved:2d}/37 | Rescues: +{rescues} | Lost: -{lost}")
