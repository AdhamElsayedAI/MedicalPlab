import os
import sys
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import numpy as np

CHUNKS_DIR = _ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = _ROOT / "Data" / "experiments" / "renal_v3" / "cache"
DEV_A_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"

chunks = []
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    chunks.extend(payload.get("chunks", []))

chunk_id_to_chunk = {ch["chunk_id"]: ch for ch in chunks}
dev_a = json.loads(DEV_A_PATH.read_bytes())

# Inspect query 0009 and 0049
target_qids = ["V5-RNK-DEV-A-0009", "V5-RNK-DEV-A-0015", "V5-RNK-DEV-A-0049"]

# Load first stage results from diagnostic
diag = json.loads((_ROOT / "reports" / "renal_v5" / "renal_v5_first_stage_diagnostic.json").read_bytes())

# Let's compute actual top 25 first stage chunks for these queries
corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)

doc_ids_sorted = sorted(list(set(ch["document_id"] for ch in chunks)))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
chunk_doc_ids = [ch["document_id"] for ch in chunks]

# Load tokenizer and embed_model
import torch
from transformers import AutoModel, AutoTokenizer
EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
ALPHA_DOC_PRIOR = 0.18

tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to("cuda:0").eval()

target_items = [it for it in dev_a if it["query_id"] in target_qids]
texts = [QUERY_INSTRUCTION + it["query"] for it in target_items]
with torch.inference_mode():
    enc = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to("cuda:0")
    out = embed_model(**enc)
    mask = enc["attention_mask"].unsqueeze(-1)
    q_emb = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
    q_emb = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)

for i, it in enumerate(target_items):
    print("=" * 70)
    print(f"QUERY: {it['query_id']} - {it['query']}")
    print(f"Gold Doc: {it['gold_doc_id']}, Gold Chunks: {it['gold_chunk_ids']}")
    q_vec = q_emb[i]
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
            
    top_idx = comb.argsort()[::-1][:25]
    print("\nTop 25 First-Stage Chunks:")
    for rank, idx in enumerate(top_idx, 1):
        ch = chunks[idx]
        cid = ch["chunk_id"]
        is_gold = " *** GOLD ***" if cid in it["gold_chunk_ids"] else ""
        print(f"  Rank {rank:2d} | Score: {comb[idx]:.4f} | {ch['document_id']} | {ch.get('section_path')} | {cid}{is_gold}")
