import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SCRIPTS = _ROOT / "Scripts"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer
from build_clean_train_benchmark import (
    corpus_embs,
    doc_embs,
    chunk_doc_ids,
    doc_id_to_idx,
    chunk_id_to_idx,
    tok,
    mod,
    device,
    QUERY_INSTRUCTION
)
from clean_items_data_p2 import CLEAN_ITEMS_DATA_P2 as CLEAN_ITEMS_DATA
from build_clean_train_v1 import all_chunks

print(f"Testing {len(CLEAN_ITEMS_DATA)} candidate items in Part 2...")
# Verify verbatim spans
for it in CLEAN_ITEMS_DATA:
    cid = it["cid"]
    span = it["span"]
    txt = all_chunks[cid]["text"]
    assert span in txt, f"Span not verbatim in {cid}! Span: {span[:50]}"

print("All Part 2 spans verified verbatim!")

q_texts = [QUERY_INSTRUCTION + it["query"] for it in CLEAN_ITEMS_DATA]
with torch.inference_mode():
    enc = tok(q_texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
    out = mod(**enc)
    mask = enc["attention_mask"].unsqueeze(-1)
    q_embs = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
    q_embs = torch.nn.functional.normalize(q_embs, p=2, dim=1).cpu().numpy().astype(np.float32)

ranks = []
for i, it in enumerate(CLEAN_ITEMS_DATA):
    q_vec = q_embs[i]
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += 0.18 * d_scores[doc_id_to_idx[did]]
    ranked = comb.argsort()[::-1]
    g_idx = chunk_id_to_idx[it["cid"]]
    rank = int(np.where(ranked == g_idx)[0][0]) + 1
    ranks.append(rank)
    print(f"[{it['strat']}] {it['split'].upper():4s} | Rank {rank:4d} | {it['cid']} | Query: {it['query'][:70]}...")

ranks_arr = np.array(ranks)
print(f"\nPart 2 Total: {len(ranks_arr)}, B=500 Coverage: {(ranks_arr <= 500).sum()}/{len(ranks_arr)} ({(ranks_arr <= 500).mean()*100:.1f}%)")
print(f"Top 20 Coverage: {(ranks_arr <= 20).sum()}/{len(ranks_arr)} ({(ranks_arr <= 20).mean()*100:.1f}%), Median Rank = {np.median(ranks_arr)}")
