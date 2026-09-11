import os
import sys
import hashlib
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

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
from transformers import AutoModel, AutoTokenizer

CHUNKS_DIR = _ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = _ROOT / "Data" / "experiments" / "renal_v3" / "cache"
TRAIN_CORE_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-core-v5.json"
TRAIN_VAL_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-val-v5.json"
OUT_DIR = _ROOT / "Data" / "experiments" / "renal_v5"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = _ROOT / "reports" / "renal_v5"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
ALPHA_DOC_PRIOR = 0.18

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def normalize_section_path(path):
    if not path:
        return ""
    if isinstance(path, list):
        return " > ".join(s.strip().lower() for s in path)
    return str(path).strip().lower()

# 1. Load Corpus
chunks = []
chunk_doc_ids = []
chunk_cids = []
chunk_sec_paths = []
doc_to_chunks = {}

for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        chunks.append(ch)
        did = ch["document_id"]
        cid = ch["chunk_id"]
        sec = tuple(ch.get("section_path", []))
        chunk_doc_ids.append(did)
        chunk_cids.append(cid)
        chunk_sec_paths.append(sec)
        doc_to_chunks.setdefault(did, []).append(len(chunks) - 1)

n_chunks = len(chunks)
doc_ids_sorted = sorted(list(doc_to_chunks.keys()))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
chunk_id_to_idx = {ch["chunk_id"]: i for i, ch in enumerate(chunks)}

corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)

train_core = json.loads(TRAIN_CORE_PATH.read_bytes())
train_val = json.loads(TRAIN_VAL_PATH.read_bytes())

tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device).eval()

def encode_items(items):
    texts = [QUERY_INSTRUCTION + it["query"] for it in items]
    with torch.inference_mode():
        enc = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        out = embed_model(**enc)
        mask = enc["attention_mask"].unsqueeze(-1)
        q_emb = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        q_emb = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)
    return q_emb

q_core = encode_items(train_core)
q_val = encode_items(train_val)
del embed_model
del tokenizer
torch.cuda.empty_cache()

# Frozen Candidate A (SAFE RESCUE) Selector Function
def select_safe_rescue(comb_scores, B=200, R=20, k_core=14, sim_thresh=0.88):
    top_b = comb_scores.argsort()[::-1][:B]
    naive_top20 = list(top_b[:R])
    
    selected = list(naive_top20[:k_core])
    selected_set = set(selected)
    slots_to_fill = 0
    
    for idx in naive_top20[k_core:]:
        is_adjacent = any(abs(idx - s) <= 1 for s in selected)
        is_high_sim = False
        if selected:
            max_sim = np.max(corpus_embs[selected] @ corpus_embs[idx])
            sec_match = any(chunk_sec_paths[idx] == chunk_sec_paths[s] and chunk_doc_ids[idx] == chunk_doc_ids[s] for s in selected)
            if sec_match and max_sim >= sim_thresh:
                is_high_sim = True
        if is_adjacent or is_high_sim:
            slots_to_fill += 1
        else:
            selected.append(idx)
            selected_set.add(idx)
            
    if slots_to_fill > 0:
        for cand in top_b[R:]:
            if cand in selected_set:
                continue
            is_adj = any(abs(cand - s) <= 1 for s in selected)
            if is_adj:
                continue
            max_sim = np.max(corpus_embs[selected] @ corpus_embs[cand])
            if max_sim >= 0.92:
                continue
            selected.append(cand)
            selected_set.add(cand)
            slots_to_fill -= 1
            if slots_to_fill == 0 or len(selected) == R:
                break
                
    if len(selected) < R:
        for cand in top_b:
            if cand not in selected_set:
                selected.append(cand)
                selected_set.add(cand)
                if len(selected) == R:
                    break
                    
    return selected, top_b

# 1. Mine TRAIN_CORE Negatives
print("=" * 70)
print(f"MINING TRAIN_CORE (N={len(train_core)}) HARD NEGATIVES FROM FROZEN SAFE RESCUE SELECTOR")
print("=" * 70)

mined_core = []
neg_type_counts = {}
total_pos = 0
total_neg = 0

for i, item in enumerate(train_core):
    qid = item["query_id"]
    query = item["query"]
    gold_doc = item["gold_doc_id"]
    gold_cids = set(item.get("gold_chunk_ids", []))
    
    # Gold section paths
    gold_sec_paths = set()
    for gcid in gold_cids:
        if gcid in chunk_id_to_idx:
            g_ch = chunks[chunk_id_to_idx[gcid]]
            gold_sec_paths.add(normalize_section_path(g_ch.get("section_path", [])))
            
    q_vec = q_core[i]
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
            
    sel_idx, top_b = select_safe_rescue(comb, B=200, R=20, k_core=14, sim_thresh=0.88)
    
    # Build positive passages (multi-positive support)
    positives = []
    for gcid in gold_cids:
        if gcid in chunk_id_to_idx:
            ch = chunks[chunk_id_to_idx[gcid]]
            positives.append({
                "chunk_id": gcid,
                "document_id": ch["document_id"],
                "section_path": ch.get("section_path", []),
                "text": ch["text"]
            })
    total_pos += len(positives)
    
    # Mine negatives from selected R=20 (strictly excluding all gold chunks)
    negatives = []
    for rank, idx in enumerate(sel_idx, 1):
        cid = chunk_cids[idx]
        if cid in gold_cids:
            continue
        ch = chunks[idx]
        did = ch["document_id"]
        sec_norm = normalize_section_path(ch.get("section_path", []))
        
        if did == gold_doc:
            if sec_norm in gold_sec_paths:
                ntype = "SAME_SECTION_NEIGHBORING_PASSAGE"
            else:
                ntype = "SAME_DOC_WRONG_SECTION"
        else:
            if rank <= 5:
                ntype = "HIGH_SCORING_TOP5_DISTRACTOR"
            else:
                ntype = "CLOSE_RENAL_TOPIC_DISTRACTOR"
                
        neg_type_counts[ntype] = neg_type_counts.get(ntype, 0) + 1
        negatives.append({
            "chunk_id": cid,
            "document_id": did,
            "section_path": ch.get("section_path", []),
            "text": ch["text"],
            "negative_type": ntype,
            "selector_rank": rank,
            "first_stage_score": float(comb[idx])
        })
    total_neg += len(negatives)
    
    mined_core.append({
        "query_id": qid,
        "query": query,
        "curriculum_stratum": item["curriculum_stratum"],
        "query_style": item["query_style"],
        "learning_objective": item["learning_objective"],
        "canonical_claim": item["canonical_claim"],
        "gold_doc_id": gold_doc,
        "positives": positives,
        "negatives": negatives,
        "num_positives": len(positives),
        "num_negatives": len(negatives)
    })

core_out_file = OUT_DIR / "mined_hard_negatives_train_core.json"
core_bytes = json.dumps(mined_core, indent=2, ensure_ascii=False).encode("utf-8")
core_out_file.write_bytes(core_bytes)
core_sha = hashlib.sha256(core_bytes).hexdigest()

print(f"TRAIN_CORE Mined: {len(mined_core)} queries")
print(f"Total Positives:  {total_pos} (mean: {total_pos/len(mined_core):.2f})")
print(f"Total Negatives:  {total_neg} (mean: {total_neg/len(mined_core):.2f})")
print(f"Dataset SHA-256:  {core_sha}")

# 2. Prepare TRAIN_VAL Candidates for Evaluation Only
print("\n" + "=" * 70)
print(f"PREPARING TRAIN_VAL (N={len(train_val)}) CANDIDATE POOLS (EVALUATION ONLY)")
print("=" * 70)

val_eval_pools = []
for i, item in enumerate(train_val):
    qid = item["query_id"]
    query = item["query"]
    gold_cids = set(item.get("gold_chunk_ids", []))
    q_vec = q_val[i]
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
    sel_idx, top_b = select_safe_rescue(comb, B=200, R=20, k_core=14, sim_thresh=0.88)
    
    val_eval_pools.append({
        "query_id": qid,
        "query": query,
        "gold_chunk_ids": list(gold_cids),
        "gold_doc_id": item["gold_doc_id"],
        "curriculum_stratum": item["curriculum_stratum"],
        "selected_r20_chunks": [
            {
                "chunk_id": chunk_cids[idx],
                "document_id": chunk_doc_ids[idx],
                "section_path": chunk_sec_paths[idx],
                "text": chunks[idx]["text"],
                "first_stage_score": float(comb[idx])
            }
            for idx in sel_idx
        ]
    })

val_out_file = OUT_DIR / "eval_candidates_train_val.json"
val_bytes = json.dumps(val_eval_pools, indent=2, ensure_ascii=False).encode("utf-8")
val_out_file.write_bytes(val_bytes)
val_sha = hashlib.sha256(val_bytes).hexdigest()

print(f"TRAIN_VAL Eval Pools: {len(val_eval_pools)} queries")
print(f"Dataset SHA-256:      {val_sha}")

# Persist Audit Report
audit_payload = {
    "timestamp": "2026-09-11T07:25:00+00:00",
    "selector_used": "SELECTOR_V5_SAFE_RESCUE_CANDIDATE_A",
    "train_core": {
        "file": str(core_out_file),
        "sha256": core_sha,
        "num_queries": len(mined_core),
        "total_positives": total_pos,
        "total_negatives": total_neg,
        "negative_type_distribution": neg_type_counts
    },
    "train_val": {
        "file": str(val_out_file),
        "sha256": val_sha,
        "num_queries": len(val_eval_pools),
        "purpose": "MODEL_SELECTION_AND_EARLY_STOPPING_ONLY_NO_GRADIENTS"
    }
}
audit_file = REPORTS_DIR / "renal_v5_train_core_mining_audit.json"
audit_file.write_bytes(json.dumps(audit_payload, indent=2).encode("utf-8"))
print(f"Audit Persisted:      {audit_file}")
