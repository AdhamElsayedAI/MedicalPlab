"""
MedicalPlab Renal V5 — Assemble Clean Train Benchmark (N=80)
============================================================
Freezes clean versioned artifacts:
- evaluation/renal/v5/renal-rerank-train-v5-clean-v1.json (N=80)
- evaluation/renal/v5/renal-rerank-train-core-v5-clean-v1.json (N=60)
- evaluation/renal/v5/renal-rerank-train-val-v5-clean-v1.json (N=20)
and their SHA256 sidecars.
"""

import sys
import os
import re
import json
import hashlib
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
    norm,
    get_num,
    get_pfx
)
from all_clean_train_items import ALL_CLEAN_ITEMS_DATA

CHUNKS_DIR = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
CACHE_DIR = _ROOT / "Data/experiments/renal_v3/cache"
V5_DIR = _ROOT / "evaluation/renal/v5"

OUT_CLEAN_ALL = V5_DIR / "renal-rerank-train-v5-clean-v1.json"
OUT_CLEAN_CORE = V5_DIR / "renal-rerank-train-core-v5-clean-v1.json"
OUT_CLEAN_VAL = V5_DIR / "renal-rerank-train-val-v5-clean-v1.json"

print("Loading embedding cache and model...")
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

print("Validating all 80 items...")
core_items_raw = [it for it in ALL_CLEAN_ITEMS_DATA if it["split"] == "core"]
val_items_raw = [it for it in ALL_CLEAN_ITEMS_DATA if it["split"] == "val"]

assert len(core_items_raw) == 60, f"Expected 60 core items, got {len(core_items_raw)}"
assert len(val_items_raw) == 20, f"Expected 20 val items, got {len(val_items_raw)}"

# 1. Check safety against exclusion registry
for it in ALL_CLEAN_ITEMS_DATA:
    cid = it["cid"]
    did = it["did"]
    ch = all_chunks[cid]
    sec = norm_sec(ch.get("section_path", []))
    assert cid in safe_chunk_ids, f"Chunk {cid} is in external exclusion registry!"
    assert cid not in all_excluded_window, f"Chunk {cid} is in excluded window!"
    assert (did, sec) not in all_excluded_sec, f"Section {(did, sec)} is in excluded sections!"
    assert it["span"] in ch["text"], f"Span not verbatim in {cid}! Span: {it['span'][:50]}"

print("Safety verification: ALL 80 items are safe unspent chunks with verbatim spans.")

# 2. Check CORE vs VAL disjointness
core_cids = set(it["cid"] for it in core_items_raw)
val_cids = set(it["cid"] for it in val_items_raw)
assert core_cids.isdisjoint(val_cids), "CORE and VAL share chunk IDs!"

core_windows = set(core_cids)
for cid in core_cids:
    num = get_num(cid)
    pfx = get_pfx(cid)
    if num != -1:
        core_windows.add(f"{pfx}-C{num-1:04d}")
        core_windows.add(f"{pfx}-C{num+1:04d}")

assert val_cids.isdisjoint(core_windows), "VAL chunk falls into CORE +/-1 window!"

core_sections = set((it["did"], norm_sec(all_chunks[it["cid"]].get("section_path", []))) for it in core_items_raw)
val_sections = set((it["did"], norm_sec(all_chunks[it["cid"]].get("section_path", []))) for it in val_items_raw)
assert core_sections.isdisjoint(val_sections), f"CORE and VAL share sections: {core_sections & val_sections}"

print("Internal disjointness verification: CORE and VAL are 100% disjoint by chunk, window, and section.")

# 3. Format complete JSON records
def format_single_item(it, qid):
    cid = it["cid"]
    did = it["did"]
    ch = all_chunks[cid]
    sec_path = ch.get("section_path", [])
    norm_sec_str = norm_sec(sec_path)
    
    qf_hash = hashlib.sha256(f"{did}|{norm_sec_str}|{norm(it['query'])}".encode()).hexdigest()[:12]
    sgk_hash = hashlib.sha256(f"{did}|{norm_sec_str}".encode()).hexdigest()[:12]
    
    return {
        "query_id": qid,
        "query": it["query"].strip(),
        "curriculum_stratum": it["strat"],
        "query_style": "QS-A",
        "learning_objective": it["obj"].strip(),
        "canonical_claim": it["claim"].strip(),
        "source_document_id": did,
        "parent_section_path": sec_path,
        "evidence_span_text": it["span"].strip(),
        "gold_chunk_ids": [cid],
        "gold_doc_id": did,
        "gold_section_path": sec_path,
        "qrel_support_rationale": it["rationale"].strip(),
        "qrel_construction_method": "SOURCE_GROUNDED_SPAN_VERIFICATION",
        "verification_status": "VERIFIED_SAFE_UNSPENT",
        "query_family": f"QF-{it['strat']}-{did}-{qf_hash}",
        "split_group_key": f"SGK-{sgk_hash}",
        "source": "V5_TRAIN_CLEAN_V1",
        "split": it["split"]
    }

core_formatted = [format_single_item(it, f"V5-RNK-TRAIN-{i:04d}") for i, it in enumerate(core_items_raw, 1)]
val_formatted = [format_single_item(it, f"V5-RNK-TRAIN-{i:04d}") for i, it in enumerate(val_items_raw, 61)]
formatted_items = core_formatted + val_formatted

# 4. Dense Retrieval Rank Evaluation
print("\nAuditing dense retrieval ranks across all 80 items...")
q_texts = [QUERY_INSTRUCTION + it["query"] for it in formatted_items]
with torch.inference_mode():
    enc = tok(q_texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
    out = mod(**enc)
    mask = enc["attention_mask"].unsqueeze(-1)
    q_embs = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
    q_embs = torch.nn.functional.normalize(q_embs, p=2, dim=1).cpu().numpy().astype(np.float32)

all_ranks = []
core_ranks = []
val_ranks = []
for i, it in enumerate(formatted_items):
    q_vec = q_embs[i]
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += 0.18 * d_scores[doc_id_to_idx[did]]
    ranked = comb.argsort()[::-1]
    g_idx = chunk_id_to_idx[it["gold_chunk_ids"][0]]
    rank = int(np.where(ranked == g_idx)[0][0]) + 1
    all_ranks.append(rank)
    if it["split"] == "core":
        core_ranks.append(rank)
    else:
        val_ranks.append(rank)

c_arr = np.array(core_ranks)
v_arr = np.array(val_ranks)
a_arr = np.array(all_ranks)

print("=" * 70)
print("CLEAN BENCHMARK DENSE RETRIEVAL EVALUATION RESULTS")
print("=" * 70)
print(f"TRAIN_ALL  (N=80): B=500 Coverage = {(a_arr <= 500).sum()}/80 ({(a_arr <= 500).mean()*100:.1f}%), Top20 = {(a_arr <= 20).sum()}/80 ({(a_arr <= 20).mean()*100:.1f}%), Median Rank = {np.median(a_arr):.1f}")
print(f"TRAIN_CORE (N=60): B=500 Coverage = {(c_arr <= 500).sum()}/60 ({(c_arr <= 500).mean()*100:.1f}%), Top20 = {(c_arr <= 20).sum()}/60 ({(c_arr <= 20).mean()*100:.1f}%), Median Rank = {np.median(c_arr):.1f}")
print(f"TRAIN_VAL  (N=20): B=500 Coverage = {(v_arr <= 500).sum()}/20 ({(v_arr <= 500).mean()*100:.1f}%), Top20 = {(v_arr <= 20).sum()}/20 ({(v_arr <= 20).mean()*100:.1f}%), Median Rank = {np.median(v_arr):.1f}")
print("=" * 70)

assert (a_arr <= 500).sum() == 80, f"Expected 80/80 in B=500, got {(a_arr <= 500).sum()}"

# 5. Write artifacts and SHA256 sidecars
def write_with_sha(path: Path, data: list):
    content = json.dumps(data, indent=2, ensure_ascii=False)
    path.write_text(content, encoding="utf-8")
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    sha_path = Path(str(path) + ".sha256")
    sha_path.write_text(f"{sha}  {path.name}\n", encoding="utf-8")
    print(f"Wrote {path.name} (N={len(data)}) -> SHA256: {sha}")
    return sha

print("\nWriting clean frozen artifacts...")
sha_all = write_with_sha(OUT_CLEAN_ALL, formatted_items)
sha_core = write_with_sha(OUT_CLEAN_CORE, core_formatted)
sha_val = write_with_sha(OUT_CLEAN_VAL, val_formatted)

print("\nAll clean artifacts successfully generated and frozen.")
