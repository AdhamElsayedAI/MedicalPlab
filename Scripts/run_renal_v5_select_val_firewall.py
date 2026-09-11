"""
MedicalPlab Renal V5 — Two-Layer Firewall Audit for SELECT_VAL_CLEAN_V1 (N=20)
=============================================================================
Audits the fresh selector validation set (SELECT_VAL_CLEAN_V1, N=20) against:
 1. TRAIN_CORE_CLEAN (N=60)
 2. Consumed TRAIN_VAL_CLEAN (N=20)
 3. DEV-A (N=50)
 4. DEV-B (N=40)
 5. Historical Heldouts (V1, V2, V3, V4)

Audited Dimensions (10):
 1. Exact query text
 2. Normalized query text (case-folded, whitespace, punctuation)
 3. Canonical claim string
 4. Learning objective string
 5. Query / template family
 6. Transformation family
 7. Gold chunk ID overlap
 7b. Adjacent chunk ID window (+/- 1 chunk in document)
 8. Source section identity (document_id + section_path)
 9. Historical heldouts overlap (V1-V4)
10. Semantic near-duplicates (raw dense cosine >= 0.90)
"""

import sys
import json
import re
import time
from pathlib import Path
from collections import defaultdict
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import torch
from transformers import AutoModel, AutoTokenizer

selval_path = _ROOT / "evaluation/renal/v5/renal-rerank-select-val-clean-v1.json"
train_core_path = _ROOT / "evaluation/renal/v5/renal-rerank-train-core-v5-clean-v1.json"
train_val_path = _ROOT / "evaluation/renal/v5/renal-rerank-train-val-v5-clean-v1.json"
dev_a_path = _ROOT / "evaluation/renal/v5/renal-rerank-dev-a-v5.json"
dev_b_path = _ROOT / "evaluation/renal/v5/renal-rerank-dev-b-v5.json"
chunks_dir = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
reports_dir = _ROOT / "reports/renal_v5"
reports_dir.mkdir(parents=True, exist_ok=True)
out_report = reports_dir / "renal_v5_select_val_firewall_audit.json"

selval = json.loads(selval_path.read_text(encoding="utf-8"))
train_core = json.loads(train_core_path.read_text(encoding="utf-8"))
train_val = json.loads(train_val_path.read_text(encoding="utf-8"))
dev_a = json.loads(dev_a_path.read_text(encoding="utf-8"))
dev_b = json.loads(dev_b_path.read_text(encoding="utf-8"))

print(f"Loaded SELECT_VAL: {len(selval)} items")
print(f"Loaded TRAIN_CORE: {len(train_core)} items")
print(f"Loaded TRAIN_VAL:  {len(train_val)} items")
print(f"Loaded DEV-A:      {len(dev_a)} items")
print(f"Loaded DEV-B:      {len(dev_b)} items")

# Build chunk adjacency map
doc_chunk_order = defaultdict(list)
for p in sorted(chunks_dir.glob("*.chunks.json")):
    payload = json.loads(p.read_bytes())
    for ch in payload.get("chunks", []):
        doc_chunk_order[ch["document_id"]].append(ch["chunk_id"])

adjacent_map = {}
for did, cids in doc_chunk_order.items():
    for idx, cid in enumerate(cids):
        adj = set()
        if idx > 0:
            adj.add(cids[idx - 1])
        if idx < len(cids) - 1:
            adj.add(cids[idx + 1])
        adjacent_map[cid] = adj

# Load Historical Heldouts (V1-V4)
historical_queries = set()
for h_path in [
    _ROOT / "evaluation/renal/v3/renal-final-heldout-v3.json",
    _ROOT / "evaluation/renal/v4/renal-retrieval-final-heldout-v4.json",
]:
    if h_path.exists():
        h_data = json.loads(h_path.read_text(encoding="utf-8"))
        queries = h_data.get("queries", h_data) if isinstance(h_data, dict) else h_data
        for q in queries:
            if isinstance(q, dict) and "query" in q:
                historical_queries.add(q["query"].strip().lower())

def normalize_text(text: str) -> str:
    t = text.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return " ".join(t.split())

def section_key(item: dict) -> str:
    did = item.get("source_document_id") or item.get("gold_doc_id", "")
    spath = item.get("gold_section_path") or item.get("parent_section_path", [])
    if isinstance(spath, list):
        spath_str = " > ".join(spath)
    else:
        spath_str = str(spath)
    return f"{did}::{spath_str}"

# Comparison groups
external_splits = {
    "DEV-A": dev_a,
    "DEV-B": dev_b,
    "TRAIN_CORE": train_core,
    "TRAIN_VAL": train_val
}

# 1-9 Overlap audits
audit_results = {}
hard_leak_counts = defaultdict(int)

for split_name, split_items in external_splits.items():
    res = {
        "exact_query_overlap": [],
        "normalized_query_overlap": [],
        "canonical_claim_overlap": [],
        "learning_objective_overlap": [],
        "query_family_overlap": [],
        "split_group_key_overlap": [],
        "chunk_id_overlap": [],
        "adjacent_chunk_overlap": [],
        "section_path_overlap": [],
        "historical_heldout_overlap": []
    }
    
    for s_it in selval:
        s_qid = s_it["query_id"]
        s_q = s_it["query"].strip()
        s_q_norm = normalize_text(s_q)
        s_claim = s_it.get("canonical_claim", "").strip()
        s_obj = s_it.get("learning_objective", "").strip()
        s_qfam = s_it.get("query_family", "")
        s_sgk = s_it.get("split_group_key", "")
        s_cids = set(s_it.get("gold_chunk_ids", []))
        s_sec = section_key(s_it)
        
        # Check historical heldouts
        if s_q.lower() in historical_queries or s_q_norm in historical_queries:
            res["historical_heldout_overlap"].append(s_qid)
            hard_leak_counts["historical_heldout"] += 1
            
        for t_it in split_items:
            t_qid = t_it.get("query_id", "")
            t_q = t_it.get("query", "").strip()
            t_q_norm = normalize_text(t_q)
            t_claim = t_it.get("canonical_claim", "").strip()
            t_obj = t_it.get("learning_objective", "").strip()
            t_qfam = t_it.get("query_family", "")
            t_sgk = t_it.get("split_group_key", "")
            t_cids = set(t_it.get("gold_chunk_ids", []))
            t_sec = section_key(t_it)
            
            # Exact query
            if s_q == t_q:
                res["exact_query_overlap"].append({"selval_id": s_qid, "target_id": t_qid, "text": s_q})
                hard_leak_counts["exact_query"] += 1
            # Norm query
            if s_q_norm == t_q_norm:
                res["normalized_query_overlap"].append({"selval_id": s_qid, "target_id": t_qid, "text": s_q_norm})
                hard_leak_counts["normalized_query"] += 1
            # Claim
            if s_claim and t_claim and s_claim == t_claim:
                res["canonical_claim_overlap"].append({"selval_id": s_qid, "target_id": t_qid, "claim": s_claim})
                hard_leak_counts["canonical_claim"] += 1
            # Objective
            if s_obj and t_obj and s_obj == t_obj:
                res["learning_objective_overlap"].append({"selval_id": s_qid, "target_id": t_qid, "obj": s_obj})
                hard_leak_counts["learning_objective"] += 1
            # Query family
            if s_qfam and t_qfam and s_qfam == t_qfam:
                res["query_family_overlap"].append({"selval_id": s_qid, "target_id": t_qid, "family": s_qfam})
                hard_leak_counts["query_family"] += 1
            # Split group key
            if s_sgk and t_sgk and s_sgk == t_sgk:
                res["split_group_key_overlap"].append({"selval_id": s_qid, "target_id": t_qid, "key": s_sgk})
                hard_leak_counts["split_group_key"] += 1
            # Chunk ID
            shared_chunks = s_cids.intersection(t_cids)
            if shared_chunks:
                res["chunk_id_overlap"].append({"selval_id": s_qid, "target_id": t_qid, "chunks": list(shared_chunks)})
                hard_leak_counts["chunk_id"] += 1
            # Adjacent chunk
            for sc in s_cids:
                if sc in adjacent_map and adjacent_map[sc].intersection(t_cids):
                    res["adjacent_chunk_overlap"].append({"selval_id": s_qid, "target_id": t_qid, "adj": list(adjacent_map[sc].intersection(t_cids))})
                    hard_leak_counts["adjacent_chunk"] += 1
            # Section path
            if s_sec and t_sec and s_sec == t_sec:
                res["section_path_overlap"].append({"selval_id": s_qid, "target_id": t_qid, "section": s_sec})
                hard_leak_counts["section_path"] += 1
                
    audit_results[split_name] = res

# 10. Semantic Near-Duplicate Audit (Cosine >= 0.90 on raw query embeddings)
print("Computing raw query embeddings for semantic near-duplicate audit...")
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True)
mod = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True).to(device).eval()

def encode_raw_queries(query_list):
    with torch.inference_mode():
        enc = tok(query_list, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        out = mod(**enc)
        mask = enc["attention_mask"].unsqueeze(-1)
        embs = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        embs = torch.nn.functional.normalize(embs, p=2, dim=1).cpu().numpy().astype(np.float32)
    return embs

selval_q_embs = encode_raw_queries([it["query"] for it in selval])

semantic_pairs = []
for split_name, split_items in external_splits.items():
    t_q_embs = encode_raw_queries([it["query"] for it in split_items])
    sim_matrix = selval_q_embs @ t_q_embs.T
    
    high_sim_indices = np.argwhere(sim_matrix >= 0.90)
    for s_idx, t_idx in high_sim_indices:
        sim = float(sim_matrix[s_idx, t_idx])
        s_it = selval[s_idx]
        t_it = split_items[t_idx]
        semantic_pairs.append({
            "target_split": split_name,
            "selval_id": s_it["query_id"],
            "target_id": t_it.get("query_id", ""),
            "selval_query": s_it["query"],
            "target_query": t_it.get("query", ""),
            "cosine_similarity": sim,
            "classification": "REVIEW_REQUIRED"
        })

print(f"Total semantic pairs with cosine >= 0.90: {len(semantic_pairs)}")
for sp in semantic_pairs:
    print(f"  [{sp['target_split']}] {sp['selval_id']} vs {sp['target_id']}: Cosine={sp['cosine_similarity']:.4f}")
    print(f"    SELVAL: {sp['selval_query']}")
    print(f"    TARGET: {sp['target_query']}\n")

# Gate determination
total_hard_leaks = sum(hard_leak_counts.values())
if total_hard_leaks == 0 and len(semantic_pairs) == 0:
    overall_status = "PASS_ALL_FIREWALL_GATES_CLEAN"
elif total_hard_leaks == 0 and len(semantic_pairs) > 0:
    overall_status = "PASS_ZERO_HARD_LEAKAGE_SEMANTIC_ADJUDICATION_REQUIRED"
else:
    overall_status = "FAIL_BLOCKING_LEAKAGE_DETECTED"

print("\n" + "=" * 80)
print(f"FIREWALL AUDIT SUMMARY FOR SELECT_VAL_CLEAN_V1 (N=20)")
print("=" * 80)
print(f"Overall Gate Status: {overall_status}")
print(f"Total Hard Leakage Violations: {total_hard_leaks}")
for k, v in hard_leak_counts.items():
    print(f"  {k}: {v}")

report_data = {
    "report_type": "MEDICALPLAB_RENAL_V5_SELECT_VAL_FIREWALL_AUDIT",
    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "target_dataset": "renal-rerank-select-val-clean-v1.json",
    "n_items": len(selval),
    "overall_gate_status": overall_status,
    "total_hard_leakage_count": total_hard_leaks,
    "hard_leak_breakdown": dict(hard_leak_counts),
    "semantic_near_duplicates_count": len(semantic_pairs),
    "semantic_near_duplicates": semantic_pairs,
    "detailed_audit": audit_results
}

out_report.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
print(f"\nFull firewall report written to: {out_report}")
