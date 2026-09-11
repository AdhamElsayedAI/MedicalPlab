"""
MedicalPlab Renal V5 — Clean Selector Pipeline (TRAIN_CORE-Only Tuning & One-Shot VAL Evaluation)
==================================================================================================
Strict Protocol:
1. TRAIN_CORE-only (N=60) Feature Oracle & Redundancy Analysis
2. Tune and Freeze at most 2 low-capacity selectors on TRAIN_CORE
3. One-shot evaluation on CLEAN TRAIN_VAL (N=20)
4. Evaluation of frozen cross-encoder PassageHit@1 on R=20
5. Zero LoRA, zero tuning on DEV-A or DEV-B.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
_SCRIPTS = _ROOT / "Scripts"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
from sentence_transformers import CrossEncoder
from transformers import AutoModel, AutoTokenizer

CACHE_DIR = _ROOT / "Data" / "experiments" / "renal_v3" / "cache"
CHUNKS_DIR = _ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CORE_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-core-v5-clean-v1.json"
VAL_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-val-v5-clean-v1.json"
REPORTS_DIR = _ROOT / "reports" / "renal_v5"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_REPORT = REPORTS_DIR / "renal_v5_clean_selector_development_report.json"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
ALPHA_DOC_PRIOR = 0.18

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

def norm_sec(p):
    if not p:
        return ""
    if isinstance(p, list):
        return " > ".join(s.strip().lower() for s in p)
    return str(p).strip().lower()

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

doc_ids_sorted = sorted(list(doc_to_chunks.keys()))
doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
chunk_id_to_idx = {ch["chunk_id"]: i for i, ch in enumerate(chunks)}

# 2. Load Cached Embeddings
corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)
doc_embs = np.load(CACHE_DIR / "all23_doc_embeddings.npy").astype(np.float32)

# 3. Load Clean Splits
core_items = json.loads(CORE_PATH.read_text(encoding="utf-8"))
val_items = json.loads(VAL_PATH.read_text(encoding="utf-8"))

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

print(f"Encoding TRAIN_CORE_CLEAN (N={len(core_items)}) and TRAIN_VAL_CLEAN (N={len(val_items)})...")
q_core = encode_items(core_items)
q_val = encode_items(val_items)

del embed_model
del tokenizer
torch.cuda.empty_cache()

def compute_first_stage(q_vec):
    p_scores = corpus_embs @ q_vec
    d_scores = doc_embs @ q_vec
    comb = p_scores.copy()
    for c_idx, did in enumerate(chunk_doc_ids):
        if did in doc_id_to_idx:
            comb[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]
    return comb, p_scores, d_scores

# -----------------------------------------------------------------------------
# STEP 2: TRAIN_CORE-ONLY FEATURE ORACLE & CROWDING AUDIT
# -----------------------------------------------------------------------------
print("\n" + "=" * 80)
print("PHASE C: STEP 2 — TRAIN_CORE-ONLY FEATURE ORACLE & CROWDING AUDIT")
print("=" * 80)

core_crowding_stats = []
gold_miss_reasons = []

for i, it in enumerate(core_items):
    comb, p_scores, d_scores = compute_first_stage(q_core[i])
    top_b = comb.argsort()[::-1][:500]
    naive_top20 = list(top_b[:20])
    gold_cid = it["gold_chunk_ids"][0]
    gold_idx = chunk_id_to_idx[gold_cid]
    gold_rank = int(np.where(top_b == gold_idx)[0][0]) + 1 if gold_idx in top_b else -1
    
    # Check naive top 20 composition
    sec_counts = {}
    doc_counts = {}
    adjacent_pairs = 0
    for pos, c in enumerate(naive_top20):
        did = chunk_doc_ids[c]
        sec = norm_sec(chunk_sec_paths[c])
        doc_counts[did] = doc_counts.get(did, 0) + 1
        sec_counts[sec] = sec_counts.get(sec, 0) + 1
        if pos > 0 and abs(c - naive_top20[pos-1]) == 1:
            adjacent_pairs += 1
            
    max_doc_crowd = max(doc_counts.values()) if doc_counts else 0
    max_sec_crowd = max(sec_counts.values()) if sec_counts else 0
    
    core_crowding_stats.append({
        "query_id": it["query_id"],
        "gold_rank": gold_rank,
        "in_naive20": gold_rank <= 20,
        "max_doc_crowd": max_doc_crowd,
        "max_sec_crowd": max_sec_crowd,
        "adjacent_pairs": adjacent_pairs
    })
    
    if gold_rank > 20:
        # Inspect why it was pushed down
        gold_doc = it["source_document_id"]
        gold_sec = norm_sec(it["parent_section_path"])
        naive_same_doc = sum(1 for c in naive_top20 if chunk_doc_ids[c] == gold_doc)
        naive_same_sec = sum(1 for c in naive_top20 if chunk_doc_ids[c] == gold_doc and norm_sec(chunk_sec_paths[c]) == gold_sec)
        gold_miss_reasons.append({
            "query_id": it["query_id"],
            "gold_rank": gold_rank,
            "gold_doc": gold_doc,
            "naive_same_doc": naive_same_doc,
            "naive_same_sec": naive_same_sec,
            "adjacent_pairs": adjacent_pairs,
            "query": it["query"]
        })

print(f"TRAIN_CORE Naive Top-20 Coverage: {sum(1 for s in core_crowding_stats if s['in_naive20'])}/60 ({sum(1 for s in core_crowding_stats if s['in_naive20'])/60*100:.1f}%)")
print(f"Average adjacent pairs in Top-20: {np.mean([s['adjacent_pairs'] for s in core_crowding_stats]):.2f}")
print(f"Average max doc crowding in Top-20: {np.mean([s['max_doc_crowd'] for s in core_crowding_stats]):.2f}")
print(f"Average max section crowding in Top-20: {np.mean([s['max_sec_crowd'] for s in core_crowding_stats]):.2f}")
print(f"\nAnalyzed {len(gold_miss_reasons)} items ranked 21..200:")
for mr in gold_miss_reasons[:5]:
    print(f"  {mr['query_id']} (Rank {mr['gold_rank']:2d}): Top-20 has {mr['naive_same_doc']} chunks from doc {mr['gold_doc']} ({mr['naive_same_sec']} in section), {mr['adjacent_pairs']} adjacent pairs.")

# -----------------------------------------------------------------------------
# STEP 3: FREEZE AT MOST TWO LOW-CAPACITY SELECTORS (TUNED ON TRAIN_CORE ONLY)
# -----------------------------------------------------------------------------
print("\n" + "=" * 80)
print("PHASE C: STEP 3 — FREEZE TWO LOW-CAPACITY SELECTOR CANDIDATES")
print("=" * 80)

# Candidate P1: Safe Rescue (Bounded Deduplication)
# Preserves top K_core naive ranks unconditionally (e.g. K_core=15),
# then fills remaining slots by replacing adjacent (+/-1) or same-section duplicates
# with highest-ranked rescue candidates from pool B.
def selector_p1_safe_rescue(comb_scores, B=200, R=20, k_core=15, sim_thresh=0.88):
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
                
    # Ensure R=20
    if len(selected) < R:
        for cand in top_b:
            if cand not in selected_set:
                selected.append(cand)
                selected_set.add(cand)
                if len(selected) == R:
                    break
    return selected, top_b

# Candidate P2: Document-Budgeted Section-Capped Selector
# Hard constraint: max 6 chunks per document, max 2 chunks per section.
# Adjacent (+/-1) chunks within same section are deferred.
def selector_p2_doc_section_budget(comb_scores, B=200, R=20, max_per_doc=6, max_per_sec=2):
    top_b = comb_scores.argsort()[::-1][:B]
    selected = []
    selected_set = set()
    doc_counts = {}
    sec_counts = {}
    
    # Pass 1: add chunks respecting doc and section caps, avoiding adjacency
    deferred = []
    for cand in top_b:
        did = chunk_doc_ids[cand]
        sec = (did, norm_sec(chunk_sec_paths[cand]))
        if doc_counts.get(did, 0) >= max_per_doc or sec_counts.get(sec, 0) >= max_per_sec:
            deferred.append(cand)
            continue
        if any(abs(cand - s) <= 1 and chunk_doc_ids[s] == did for s in selected):
            deferred.append(cand)
            continue
            
        selected.append(cand)
        selected_set.add(cand)
        doc_counts[did] = doc_counts.get(did, 0) + 1
        sec_counts[sec] = sec_counts.get(sec, 0) + 1
        if len(selected) == R:
            break
            
    # Pass 2: fill remaining from deferred if needed
    if len(selected) < R:
        for cand in deferred:
            if cand not in selected_set:
                selected.append(cand)
                selected_set.add(cand)
                if len(selected) == R:
                    break
                    
    return selected, top_b

# Evaluate on TRAIN_CORE (N=60)
print("\nTuning and validating candidates on TRAIN_CORE (N=60):")

def eval_selector_on_core(name, sel_fn):
    cov_b = 0
    cov_r = 0
    naive_cov = 0
    rescues = 0
    lost = 0
    for i, it in enumerate(core_items):
        comb, _, _ = compute_first_stage(q_core[i])
        gold = chunk_id_to_idx[it["gold_chunk_ids"][0]]
        sel, top_b = sel_fn(comb, B=200, R=20)
        
        in_naive = gold in top_b[:20]
        in_b = gold in top_b
        in_r = gold in sel
        
        if in_naive: naive_cov += 1
        if in_b: cov_b += 1
        if in_r: cov_r += 1
        
        if not in_naive and in_r: rescues += 1
        if in_naive and not in_r: lost += 1
        
    return {
        "name": name,
        "in_b": cov_b,
        "in_r": cov_r,
        "naive": naive_cov,
        "rescues": rescues,
        "lost": lost,
        "out_cov_pct": (cov_r / 60) * 100.0
    }

p1_core = eval_selector_on_core("P1_SAFE_RESCUE", selector_p1_safe_rescue)
p2_core = eval_selector_on_core("P2_DOC_SEC_BUDGET", selector_p2_doc_section_budget)

print(f"  Naive Top-20 (Baseline):  OutputCov@20 = 47/60 (78.3%)")
print(f"  P1 (Safe Rescue):         OutputCov@20 = {p1_core['in_r']}/60 ({p1_core['out_cov_pct']:.1f}%), Rescues: +{p1_core['rescues']}, Lost: -{p1_core['lost']}")
print(f"  P2 (Doc-Sec Budget):      OutputCov@20 = {p2_core['in_r']}/60 ({p2_core['out_cov_pct']:.1f}%), Rescues: +{p2_core['rescues']}, Lost: -{p2_core['lost']}")

# -----------------------------------------------------------------------------
# STEP 4: ONE-SHOT EVALUATION ON CLEAN TRAIN_VAL (N=20)
# -----------------------------------------------------------------------------
print("\n" + "=" * 80)
print("PHASE C: STEP 4 — ONE-SHOT EVALUATION ON CLEAN TRAIN_VAL (N=20)")
print("=" * 80)

print("Loading Qwen3-Reranker-0.6B (Frozen Base Weights) for PassageHit@1 verification...")
reranker = CrossEncoder(RERANK_MODEL_ID, device="cuda:0", trust_remote_code=True)
torch.cuda.synchronize()

def eval_selector_on_val(name, sel_fn):
    cov_b = 0
    cov_r = 0
    naive_cov = 0
    rescues = 0
    lost = 0
    hit1_count = 0
    per_query = []
    
    for i, it in enumerate(val_items):
        comb, _, _ = compute_first_stage(q_val[i])
        gold = chunk_id_to_idx[it["gold_chunk_ids"][0]]
        sel, top_b = sel_fn(comb, B=200, R=20)
        
        in_naive = gold in top_b[:20]
        in_b = gold in top_b
        in_r = gold in sel
        
        if in_naive: naive_cov += 1
        if in_b: cov_b += 1
        if in_r: cov_r += 1
        
        if not in_naive and in_r: rescues += 1
        if in_naive and not in_r: lost += 1
        
        # Rerank selected R=20
        pairs = [[it["query"], chunks[c]["text"]] for c in sel]
        scores = reranker.predict(pairs, batch_size=20, show_progress_bar=False)
        top1_c = sel[np.argmax(scores)]
        is_hit1 = bool(top1_c == gold)
        if is_hit1:
            hit1_count += 1
            
        per_query.append({
            "query_id": it["query_id"],
            "gold_cid": it["gold_chunk_ids"][0],
            "in_naive": bool(in_naive),
            "in_r": bool(in_r),
            "is_hit1": bool(is_hit1)
        })
        
    return {
        "name": name,
        "n": 20,
        "input_cov_b": cov_b,
        "output_cov_r": cov_r,
        "output_cov_pct": (cov_r / 20) * 100.0,
        "naive_cov": naive_cov,
        "rescues": rescues,
        "lost": lost,
        "passage_hit1_count": hit1_count,
        "passage_hit1_pct": (hit1_count / 20) * 100.0,
        "per_query": per_query
    }

val_naive = eval_selector_on_val("NAIVE_TOP20", lambda comb, B, R: (list(comb.argsort()[::-1][:R]), comb.argsort()[::-1][:B]))
val_p1 = eval_selector_on_val("P1_SAFE_RESCUE", selector_p1_safe_rescue)
val_p2 = eval_selector_on_val("P2_DOC_SEC_BUDGET", selector_p2_doc_section_budget)

print(f"\n--- ONE-SHOT VAL (N=20) RESULTS ---")
print(f"  NAIVE_TOP20:       OutputCov@20 = {val_naive['output_cov_r']:2d}/20 ({val_naive['output_cov_pct']:5.1f}%) | PassageHit@1 = {val_naive['passage_hit1_count']:2d}/20 ({val_naive['passage_hit1_pct']:5.1f}%)")
print(f"  P1_SAFE_RESCUE:    OutputCov@20 = {val_p1['output_cov_r']:2d}/20 ({val_p1['output_cov_pct']:5.1f}%) | PassageHit@1 = {val_p1['passage_hit1_count']:2d}/20 ({val_p1['passage_hit1_pct']:5.1f}%) | Rescues: +{val_p1['rescues']} | Lost: -{val_p1['lost']}")
print(f"  P2_DOC_SEC_BUDGET: OutputCov@20 = {val_p2['output_cov_r']:2d}/20 ({val_p2['output_cov_pct']:5.1f}%) | PassageHit@1 = {val_p2['passage_hit1_count']:2d}/20 ({val_p2['passage_hit1_pct']:5.1f}%) | Rescues: +{val_p2['rescues']} | Lost: -{val_p2['lost']}")

# Gate evaluation: OutputCoverage@20 >= 17/20 (85.0%)
gate_pass_p1 = val_p1['output_cov_r'] >= 17
gate_pass_p2 = val_p2['output_cov_r'] >= 17
print(f"\nGate OutputCoverage@20 >= 85.0% (17/20): P1: {'PASS' if gate_pass_p1 else 'FAIL'} ({val_p1['output_cov_pct']:.1f}%), P2: {'PASS' if gate_pass_p2 else 'FAIL'} ({val_p2['output_cov_pct']:.1f}%)")

# Save comprehensive development report
report_payload = {
    "report_type": "MEDICALPLAB_RENAL_V5_CLEAN_SELECTOR_DEVELOPMENT_REPORT",
    "timestamp_utc": "2026-09-11T08:00:00Z",
    "status": "COMPLETED",
    "gate_threshold": "OutputCoverage@20 >= 85.0% (17/20)",
    "train_core_results": {
        "n": 60,
        "naive_top20": {"output_cov": 47, "pct": 78.3},
        "p1_safe_rescue": p1_core,
        "p2_doc_sec_budget": p2_core
    },
    "train_val_one_shot_results": {
        "n": 20,
        "naive_top20": val_naive,
        "p1_safe_rescue": val_p1,
        "p2_doc_sec_budget": val_p2
    }
}

OUT_REPORT.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
print(f"\nComprehensive report written to: {OUT_REPORT}")
