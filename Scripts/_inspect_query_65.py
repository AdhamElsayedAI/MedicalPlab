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
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    chunks.extend(payload.get("chunks", []))

doc_ids_sorted = sorted(list(set(ch["document_id"] for ch in chunks)))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
chunk_doc_ids = [ch["document_id"] for ch in chunks]

corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)

train_val = json.loads(TRAIN_VAL_PATH.read_bytes())
item_65 = next(it for it in train_val if it["query_id"] == "V5-RNK-TRAIN-0065")

import torch
from transformers import AutoModel, AutoTokenizer
EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "

tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to("cuda:0").eval()

with torch.inference_mode():
    enc = tokenizer([QUERY_INSTRUCTION + item_65["query"]], padding=True, truncation=True, return_tensors="pt").to("cuda:0")
    out = embed_model(**enc)
    mask = enc["attention_mask"].unsqueeze(-1)
    q_emb = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
    q_vec = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)[0]

del embed_model
del tokenizer
torch.cuda.empty_cache()

p_scores = corpus_embs @ q_vec
d_scores = doc_embs @ q_vec
comb = p_scores.copy()
for c_idx, did in enumerate(chunk_doc_ids):
    if did in doc_id_to_idx:
        comb[c_idx] += 0.18 * d_scores[doc_id_to_idx[did]]

ranked = comb.argsort()[::-1]
print(f"Query: {item_65['query']}")
print(f"Gold Chunks: {item_65['gold_chunk_ids']}")

# Print top 45
docs_in_top45 = {}
for rank, idx in enumerate(ranked[:45], 1):
    ch = chunks[idx]
    did = ch["document_id"]
    docs_in_top45[did] = docs_in_top45.get(did, 0) + 1
    is_gold = " *** GOLD ***" if ch["chunk_id"] in item_65["gold_chunk_ids"] else ""
    if rank <= 20 or is_gold:
        print(f"  Rank {rank:2d} | Score: {comb[idx]:.4f} | {did} | {ch.get('section_path')} | {ch['chunk_id']}{is_gold}")

print("\nDocument representation in top 45:")
for did, cnt in sorted(docs_in_top45.items(), key=lambda x: x[1], reverse=True):
    print(f"  {did}: {cnt} chunks")
