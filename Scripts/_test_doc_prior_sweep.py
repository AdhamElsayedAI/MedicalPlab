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

def evaluate_alpha(items, q_embs, alpha):
    n = len(items)
    cov20 = 0
    cov50 = 0
    cov100 = 0
    cov200 = 0
    for i, it in enumerate(items):
        golds = set(it.get("gold_chunk_ids", []))
        if not golds:
            continue
        q_vec = q_embs[i]
        p_scores = corpus_embs @ q_vec
        d_scores = doc_embs @ q_vec
        comb = p_scores.copy()
        for c_idx, did in enumerate(chunk_doc_ids):
            if did in doc_id_to_idx:
                comb[c_idx] += alpha * d_scores[doc_id_to_idx[did]]
        top200 = comb.argsort()[::-1][:200]
        top_cids = [chunk_cids[idx] for idx in top200]
        if any(c in golds for c in top_cids[:20]):
            cov20 += 1
        if any(c in golds for c in top_cids[:50]):
            cov50 += 1
        if any(c in golds for c in top_cids[:100]):
            cov100 += 1
        if any(c in golds for c in top_cids[:200]):
            cov200 += 1
    return cov20 / n * 100, cov50 / n * 100, cov100 / n * 100, cov200 / n * 100, cov20

print("=" * 70)
print("ALPHA_DOC_PRIOR SWEEP ON TRAIN_CORE (N=60)")
print("=" * 70)
for alpha in [0.0, 0.05, 0.10, 0.15, 0.18, 0.22, 0.28, 0.35, 0.50]:
    c20, c50, c100, c200, count = evaluate_alpha(train_core, q_core, alpha)
    print(f"  alpha={alpha:4.2f} | Cov@20: {c20:5.1f}% ({count:2d}/60) | Cov@50: {c50:5.1f}% | Cov@100: {c100:5.1f}% | Cov@200: {c200:5.1f}%")

print("\n" + "=" * 70)
print("ALPHA_DOC_PRIOR SWEEP ON TRAIN_VAL (N=20)")
print("=" * 70)
for alpha in [0.0, 0.05, 0.10, 0.15, 0.18, 0.22, 0.28, 0.35, 0.50]:
    c20, c50, c100, c200, count = evaluate_alpha(train_val, q_val, alpha)
    print(f"  alpha={alpha:4.2f} | Cov@20: {c20:5.1f}% ({count:2d}/20) | Cov@50: {c50:5.1f}% | Cov@100: {c100:5.1f}% | Cov@200: {c200:5.1f}%")
