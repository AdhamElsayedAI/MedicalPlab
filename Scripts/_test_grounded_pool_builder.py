import sys
import os
import re
import json
import hashlib
from pathlib import Path
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_ROOT / "Scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "Scripts"))

import torch
from transformers import AutoModel, AutoTokenizer
from mine_rich_safe_curriculum import get_candidates
from build_clean_train_v1 import all_chunks, safe_chunk_ids, all_excluded_sec, all_excluded_window, norm_sec, norm

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

QUOTAS = {
    "STR-01": 7, "STR-02": 7, "STR-03": 6, "STR-04": 6,
    "STR-05": 7, "STR-06": 6, "STR-07": 7, "STR-08": 7,
    "STR-09": 7, "STR-10": 6, "STR-11": 7, "STR-12": 7
}

pools = get_candidates()

def get_num(cid: str) -> int:
    m = re.search(r"-C(\d+)$", cid)
    return int(m.group(1)) if m else -1

def get_pfx(cid: str) -> str:
    m = re.match(r"(DOC-PMC-RENAL-\d+-B)-C\d+$", cid)
    return m.group(1) if m else cid

def expand_cid(cid):
    pfx = get_pfx(cid)
    num = get_num(cid)
    return {f"{pfx}-C{num-1:04d}", f"{pfx}-C{num:04d}", f"{pfx}-C{num+1:04d}"}

# Select candidates
core_cands = []
val_cands = []
core_secs = set()
val_secs = set()
core_chunks = set()
val_chunks = set()
core_win = set()
val_win = set()

for strat, quota in QUOTAS.items():
    pool = pools[strat]
    n_core = 5
    n_val = quota - n_core

    sel_core = []
    for c in pool:
        cid = c["chunk_id"]
        did = c["document_id"]
        sec = norm_sec(c["section_path"])
        if cid in core_chunks or cid in core_win or cid in val_chunks or cid in val_win: continue
        if (did, sec) in val_secs: continue

        sel_core.append(c)
        core_chunks.add(cid)
        core_win.update(expand_cid(cid))
        core_secs.add((did, sec))
        if len(sel_core) == n_core:
            break
    assert len(sel_core) == n_core

    sel_val = []
    for c in pool:
        cid = c["chunk_id"]
        did = c["document_id"]
        sec = norm_sec(c["section_path"])
        if cid in core_chunks or cid in core_win or cid in val_chunks or cid in val_win: continue
        if (did, sec) in core_secs: continue

        sel_val.append(c)
        val_chunks.add(cid)
        val_win.update(expand_cid(cid))
        val_secs.add((did, sec))
        if len(sel_val) == n_val:
            break
    assert len(sel_val) == n_val

    for c in sel_core: core_cands.append((strat, c))
    for c in sel_val: val_cands.append((strat, c))

print(f"Selected: Core N={len(core_cands)}, Val N={len(val_cands)}")
assert len(core_secs & val_secs) == 0
assert len(core_chunks & val_chunks) == 0
assert len(core_win & val_chunks) == 0
assert len(val_win & core_chunks) == 0
print("CORE and VAL sections, chunks, and windows are 100% DISJOINT!")
