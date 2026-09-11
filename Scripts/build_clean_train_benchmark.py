"""
MedicalPlab Renal V5 — Build Clean Train Benchmark (N=80)
==========================================================
Constructs 80 source-grounded, curriculum-aligned items across 12 strata:
- 60 TRAIN_CORE_CLEAN items
- 20 TRAIN_VAL_CLEAN items
Disjoint by:
- Chunk IDs
- +/- 1 chunk windows
- Section paths
- Claims & Learning Objectives
- Query families & Split group keys

Zero leakage against:
- DEV-A (N=50)
- DEV-B (N=40)
- Historical Heldouts V1-V4
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SCRIPTS = _ROOT / "Scripts"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import torch
from transformers import AutoModel, AutoTokenizer
from build_clean_train_v1 import (
    all_chunks,
    safe_chunk_ids,
    all_excluded_window,
    all_excluded_sec,
    norm_sec,
    norm
)

CHUNKS_DIR = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
CACHE_DIR = _ROOT / "Data/experiments/renal_v3/cache"
V5_DIR = _ROOT / "evaluation/renal/v5"

OUT_CLEAN_ALL = V5_DIR / "renal-rerank-train-v5-clean-v1.json"
OUT_CLEAN_CORE = V5_DIR / "renal-rerank-train-core-v5-clean-v1.json"
OUT_CLEAN_VAL = V5_DIR / "renal-rerank-train-val-v5-clean-v1.json"

# Load corpus and embeddings
corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)

all_chunks_list = []
chunk_doc_ids = []
for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        all_chunks_list.append(ch)
        chunk_doc_ids.append(ch["document_id"])

doc_ids_sorted = sorted(list(set(chunk_doc_ids)))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
chunk_id_to_idx = {ch["chunk_id"]: i for i, ch in enumerate(all_chunks_list)}

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True)
mod = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True).to(device).eval()

QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "

def eval_query_rank(query_str: str, gold_cid: str):
    q_text = QUERY_INSTRUCTION + query_str
    with torch.inference_mode():
        enc = tok([q_text], padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        out = mod(**enc)
        mask = enc["attention_mask"].unsqueeze(-1)
        q_emb = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        q_vec = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().detach().numpy()[0]
    
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += 0.18 * d_scores[doc_id_to_idx[did]]
    
    ranked = comb.argsort()[::-1]
    g_idx = chunk_id_to_idx[gold_cid]
    rank = int(np.where(ranked == g_idx)[0][0]) + 1
    return rank

print("Initialized embedding environment successfully.")
