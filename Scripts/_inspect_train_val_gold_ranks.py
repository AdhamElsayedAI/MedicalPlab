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

train_val = json.loads(TRAIN_VAL_PATH.read_bytes())

import torch
from transformers import AutoModel, AutoTokenizer
EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
ALPHA_DOC_PRIOR = 0.18

tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to("cuda:0").eval()

texts = [QUERY_INSTRUCTION + it["query"] for it in train_val]
with torch.inference_mode():
    enc = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to("cuda:0")
    out = embed_model(**enc)
    mask = enc["attention_mask"].unsqueeze(-1)
    q_emb = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
    q_emb = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)

del embed_model
del tokenizer
torch.cuda.empty_cache()

print("=" * 70)
print("TRAIN_VAL (N=20) GOLD FIRST-STAGE RANKS")
print("=" * 70)

for i, it in enumerate(train_val):
    golds = set(it.get("gold_chunk_ids", []))
    q_vec = q_emb[i]
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
    ranked_idx = comb.argsort()[::-1]
    
    gold_ranks = [rank for rank, idx in enumerate(ranked_idx, 1) if chunk_cids[idx] in golds]
    best_gold_rank = min(gold_ranks) if gold_ranks else None
    
    # Gold doc rank
    doc_ranks = d_scores.argsort()[::-1]
    g_doc = it["gold_doc_id"]
    g_doc_rank = [rank for rank, didx in enumerate(doc_ranks, 1) if doc_ids_sorted[didx] == g_doc][0]
    
    status = "TOP20" if best_gold_rank <= 20 else ("21-100" if best_gold_rank <= 100 else "101+")
    print(f"[{status:6s}] {it['query_id']} | Best Gold Rank: {best_gold_rank:3d} | Gold Doc Rank: {g_doc_rank:2d} | Query: {it['query'][:55]}...")
