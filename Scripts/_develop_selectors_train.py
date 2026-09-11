import os
import sys
import hashlib
import json
import math
from pathlib import Path
import time
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
from sentence_transformers import CrossEncoder
from transformers import AutoModel, AutoTokenizer

CACHE_DIR = _ROOT / "Data" / "experiments" / "renal_v3" / "cache"
CHUNKS_DIR = _ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
TRAIN_CORE_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-core-v5.json"
TRAIN_VAL_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-val-v5.json"
REPORTS_DIR = _ROOT / "reports" / "renal_v5"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
ALPHA_DOC_PRIOR = 0.18

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def normalize_section_path(path):
    if not path:
        return ""
    if isinstance(path, list):
        return " > ".join(s.strip().lower() for s in path)
    return str(path).strip().lower()

# 1. Load Corpus Chunks
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

# 2. Load Embeddings
corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)

# 3. Load Splits
train_core = json.loads(TRAIN_CORE_PATH.read_bytes())
train_val = json.loads(TRAIN_VAL_PATH.read_bytes())

# 4. Encode Queries
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

# Load CrossEncoder for Hit@1 validation
print("Loading Qwen3-Reranker-0.6B...")
reranker = CrossEncoder(RERANK_MODEL_ID, device="cuda:0", trust_remote_code=True)
torch.cuda.synchronize()
_ = reranker.predict([["warmup query", "warmup text"] for _ in range(2)], batch_size=2, show_progress_bar=False)
torch.cuda.synchronize()

def compute_first_stage_scores(q_vec):
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
    return comb, p_scores, d_scores

# -----------------------------------------------------------------------------
# CANDIDATE A: SAFE RESCUE SELECTOR
# -----------------------------------------------------------------------------
# Keeps top K_core (e.g. 14) from naive Top-20 unconditionally.
# For slots K_core..20, checks if candidate is redundant (adjacent chunk or same section + cosine > 0.88).
# If redundant, replaces with highest-scoring non-redundant rescue candidate from B (ranks 21+).
def select_safe_rescue(comb_scores, B=200, R=20, k_core=14, sim_thresh=0.88):
    top_b = comb_scores.argsort()[::-1][:B]
    naive_top20 = list(top_b[:R])
    
    # 1. Unconditionally preserve core
    selected = list(naive_top20[:k_core])
    selected_set = set(selected)
    
    # 2. Check remaining naive candidates (slots k_core to 20)
    slots_to_fill = 0
    for idx in naive_top20[k_core:]:
        # Check redundancy against already selected
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
            
    # 3. Rescue from rank 21+ in pool B
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
                
    # Fallback to ensure R=20
    if len(selected) < R:
        for cand in top_b:
            if cand not in selected_set:
                selected.append(cand)
                selected_set.add(cand)
                if len(selected) == R:
                    break
                    
    return selected, top_b

# -----------------------------------------------------------------------------
# CANDIDATE B: HIERARCHICAL ALLOCATION SELECTOR
# -----------------------------------------------------------------------------
# Soft hierarchical quotas for top documents: Doc1: 8, Doc2: 5, Doc3: 4, Doc4: 3
# Defers adjacent duplicates within each document, fills R=20 hierarchically.
def select_hierarchical(comb_scores, d_scores, B=200, R=20, quotas=[8, 5, 4, 3]):
    top_b = comb_scores.argsort()[::-1][:B]
    top_b_set = set(top_b)
    
    doc_ranks = d_scores.argsort()[::-1]
    selected = []
    selected_set = set()
    
    for rank_pos, n_slots in enumerate(quotas):
        if rank_pos >= len(doc_ranks):
            break
        did = doc_ids_sorted[doc_ranks[rank_pos]]
        # Find candidates in top_b for this document
        doc_cands = [c for c in top_b if chunk_doc_ids[c] == did and c not in selected_set]
        # Separate non-adjacent and adjacent
        non_adj = []
        adj = []
        for c in doc_cands:
            if any(abs(c - s) <= 1 for s in selected):
                adj.append(c)
            else:
                non_adj.append(c)
        ordered_doc = non_adj + adj
        take = ordered_doc[:n_slots]
        for c in take:
            selected.append(c)
            selected_set.add(c)
            if len(selected) == R:
                break
        if len(selected) == R:
            break
            
    # Fill remaining from top_b
    if len(selected) < R:
        for c in top_b:
            if c not in selected_set:
                selected.append(c)
                selected_set.add(c)
                if len(selected) == R:
                    break
                    
    return selected, top_b

# -----------------------------------------------------------------------------
# EVALUATION HARNESS FOR SELECTORS
# -----------------------------------------------------------------------------
def evaluate_selector_on_split(split_name, items, q_embs, selector_type, B=200, R=20, run_reranker=False):
    n = len(items)
    cov_b_count = 0
    cov_r_count = 0
    naive_cov_count = 0
    
    naive_preserved_count = 0
    rescues_count = 0
    lost_count = 0
    
    pass_hit1_count = 0
    
    for i, it in enumerate(items):
        query = it["query"]
        golds = set(it.get("gold_chunk_ids", []))
        if not golds:
            continue
            
        comb, p_scores, d_scores = compute_first_stage_scores(q_embs[i])
        top_b = comb.argsort()[::-1][:B]
        naive_top20 = list(top_b[:R])
        
        has_in_naive = any(chunk_cids[c] in golds for c in naive_top20)
        if has_in_naive:
            naive_cov_count += 1
            
        if selector_type == "NAIVE":
            sel = naive_top20
        elif selector_type == "SAFE_RESCUE":
            sel, _ = select_safe_rescue(comb, B=B, R=R, k_core=14, sim_thresh=0.88)
        elif selector_type == "HIERARCHICAL":
            sel, _ = select_hierarchical(comb, d_scores, B=B, R=R, quotas=[8, 5, 4, 3])
            
        b_cids = set(chunk_cids[c] for c in top_b)
        r_cids = set(chunk_cids[c] for c in sel)
        
        in_b = any(c in golds for c in b_cids)
        in_r = any(c in golds for c in r_cids)
        
        if in_b:
            cov_b_count += 1
        if in_r:
            cov_r_count += 1
            
        # Analysis vs Naive Top20
        if has_in_naive and in_r:
            naive_preserved_count += 1
        elif has_in_naive and not in_r:
            lost_count += 1
        elif not has_in_naive and in_r:
            rescues_count += 1
            
        # Run frozen reranker on R=20 if requested
        if run_reranker:
            pairs = [[query, chunks[c]["text"]] for c in sel]
            scores = reranker.predict(pairs, batch_size=20, show_progress_bar=False)
            top1_c = sel[np.argmax(scores)]
            if chunk_cids[top1_c] in golds:
                pass_hit1_count += 1
                
    retention_pct = (cov_r_count / cov_b_count * 100.0) if cov_b_count else 0.0
    preservation_pct = (naive_preserved_count / naive_cov_count * 100.0) if naive_cov_count else 0.0
    
    return {
        "split": split_name,
        "selector": selector_type,
        "B": B,
        "R": R,
        "N": n,
        "InputCoverage@B": (cov_b_count / n) * 100.0,
        "OutputCoverage@20": (cov_r_count / n) * 100.0,
        "RetentionRate": retention_pct,
        "NaiveTop20Coverage": (naive_cov_count / n) * 100.0,
        "NaivePreserved": naive_preserved_count,
        "NaivePreservationRate": preservation_pct,
        "NewRescues": rescues_count,
        "CasesLost": lost_count,
        "PassageHit@1": (pass_hit1_count / n * 100.0) if run_reranker else None,
        "raw_counts": {
            "B_present": cov_b_count,
            "R_present": cov_r_count,
            "naive_present": naive_cov_count,
            "rescues": rescues_count,
            "lost": lost_count
        }
    }

print("=" * 80)
print("TRAIN_VAL (N=20) BENCHMARKING OF SELECTOR CANDIDATES")
print("=" * 80)

val_results = []
for B in [200, 500]:
    print(f"\n--- EVALUATION AT B={B} -> R=20 ON TRAIN_VAL (N=20) ---")
    for s_name in ["NAIVE", "SAFE_RESCUE", "HIERARCHICAL"]:
        res = evaluate_selector_on_split("TRAIN_VAL", train_val, q_val, s_name, B=B, R=20, run_reranker=True)
        val_results.append(res)
        hit1_str = f"{res['PassageHit@1']:4.1f}%" if res['PassageHit@1'] is not None else "N/A"
        print(f"  {s_name:14s} | InCov@B: {res['InputCoverage@B']:5.1f}% | OutCov@20: {res['OutputCoverage@20']:5.1f}% ({res['raw_counts']['R_present']:2d}/20) | Ret: {res['RetentionRate']:5.1f}% | Preserved: {res['NaivePreserved']:2d}/12 ({res['NaivePreservationRate']:5.1f}%) | Rescues: +{res['NewRescues']} | Lost: -{res['CasesLost']} | Hit@1: {hit1_str}")

print("\n" + "=" * 80)
print("TRAIN_CORE (N=60) BENCHMARKING OF SELECTOR CANDIDATES")
print("=" * 80)

core_results = []
for B in [200, 500]:
    print(f"\n--- EVALUATION AT B={B} -> R=20 ON TRAIN_CORE (N=60) ---")
    for s_name in ["NAIVE", "SAFE_RESCUE", "HIERARCHICAL"]:
        res = evaluate_selector_on_split("TRAIN_CORE", train_core, q_core, s_name, B=B, R=20, run_reranker=False)
        core_results.append(res)
        print(f"  {s_name:14s} | InCov@B: {res['InputCoverage@B']:5.1f}% | OutCov@20: {res['OutputCoverage@20']:5.1f}% ({res['raw_counts']['R_present']:2d}/60) | Ret: {res['RetentionRate']:5.1f}% | Preserved: {res['NaivePreserved']:2d}/37 ({res['NaivePreservationRate']:5.1f}%) | Rescues: +{res['NewRescues']} | Lost: -{res['CasesLost']}")

# Save TRAIN development report
report_path = REPORTS_DIR / "renal_v5_selector_train_development.json"
report_data = {
    "timestamp": "2026-09-11T07:15:00+00:00",
    "train_val_results": val_results,
    "train_core_results": core_results
}
report_path.write_bytes(json.dumps(report_data, indent=2).encode("utf-8"))
print(f"\nReport persisted to: {report_path}")
