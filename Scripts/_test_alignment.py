import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_ROOT / "Scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "Scripts"))

import json
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from build_clean_train_v1 import all_chunks

chunks_dir = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
cache_dir = _ROOT / "Data/experiments/renal_v3/cache"

chunks = []
chunk_doc_ids = []
for p in sorted(chunks_dir.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        chunks.append(ch)
        chunk_doc_ids.append(ch["document_id"])

corpus_embs = np.load(cache_dir / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(cache_dir / "all23_doc_embeddings.npy").astype(np.float32)
doc_ids_sorted = sorted(list(set(chunk_doc_ids)))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
chunk_id_to_idx = {ch["chunk_id"]: i for i, ch in enumerate(chunks)}

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True)
mod = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True).to(device).eval()

QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "

test_cases = [
    {
        "query": "How do aldosterone synthase inhibitors (ASIs) reduce aldosterone-mediated organ damage?",
        "cid": "DOC-PMC-RENAL-0001-B-C0023",
        "doc": "DOC-PMC-RENAL-0001"
    },
    {
        "query": "How does angiotensin II-induced oxidative stress cause endothelial dysfunction in the kidney?",
        "cid": "DOC-PMC-RENAL-0001-B-C0012",
        "doc": "DOC-PMC-RENAL-0001"
    },
    {
        "query": "What adhesion molecules are upregulated by endothelial inflammation to recruit circulating monocytes?",
        "cid": "DOC-PMC-RENAL-0001-B-C0010",
        "doc": "DOC-PMC-RENAL-0001"
    }
]

for tc in test_cases:
    q_text = QUERY_INSTRUCTION + tc["query"]
    with torch.inference_mode():
        enc = tok([q_text], padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        out = mod(**enc)
        mask = enc["attention_mask"].unsqueeze(-1)
        q_emb = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        q_emb = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)[0]

    p_scores = corpus_embs @ q_emb
    d_scores = doc_embs @ q_emb

    comb_scores = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb_scores[c_idx] += 0.18 * d_scores[doc_id_to_idx[did]]

    ranked_indices = comb_scores.argsort()[::-1]
    gold_idx = chunk_id_to_idx[tc["cid"]]
    rank = int(np.where(ranked_indices == gold_idx)[0][0]) + 1
    print(f"Query: \"{tc['query']}\"")
    print(f"  Gold CID: {tc['cid']} -> Combined Rank: {rank} / 2691")
