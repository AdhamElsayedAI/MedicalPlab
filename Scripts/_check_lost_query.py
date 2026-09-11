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
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        chunks.append(ch)
        chunk_doc_ids.append(ch["document_id"])
        chunk_cids.append(ch["chunk_id"])

doc_ids_sorted = sorted(list(set(chunk_doc_ids)))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}

corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)
train_val = json.loads(TRAIN_VAL_PATH.read_bytes())

import torch
from transformers import AutoModel, AutoTokenizer
EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "

tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to("cuda:0").eval()

texts = [QUERY_INSTRUCTION + it["query"] for it in train_val]
with torch.inference_mode():
    enc = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to("cuda:0")
    out = embed_model(**enc)
    mask = enc["attention_mask"].unsqueeze(-1)
    q_emb = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
    q_val = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)

del embed_model
del tokenizer
torch.cuda.empty_cache()

for i, it in enumerate(train_val):
    golds = set(it.get("gold_chunk_ids", []))
    q_vec = q_val[i]
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += 0.18 * d_scores[doc_id_to_idx[did]]
            
    top_b = comb.argsort()[::-1][:200]
    naive20 = list(top_b[:20])
    
    # max_doc=6
    doc_counts = {}
    kept = []
    excess = []
    for c in naive20:
        did = chunk_doc_ids[c]
        doc_counts[did] = doc_counts.get(did, 0) + 1
        if doc_counts[did] <= 6:
            kept.append(c)
        else:
            excess.append(c)
    in_naive = any(chunk_cids[c] in golds for c in naive20)
    in_kept = any(chunk_cids[c] in golds for c in kept)
    
    if in_naive and not in_kept:
        print(f"Lost Query: {it['query_id']} {it['query']}")
        for rank, c in enumerate(naive20, 1):
            if chunk_cids[c] in golds:
                print(f"  Gold chunk {chunk_cids[c]} was at naive rank {rank} in doc {chunk_doc_ids[c]}")
