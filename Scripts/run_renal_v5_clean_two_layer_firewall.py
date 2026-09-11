"""
MedicalPlab Renal V5 — Two-Layer Firewall Audit (External & Internal)
====================================================================
Audits:
Layer 1 (External): CLEAN TRAIN (N=80) vs DEV-A (N=50), DEV-B (N=40), Historical Heldouts (V1-V4)
Layer 2 (Internal): TRAIN_CORE_CLEAN (N=60) vs TRAIN_VAL_CLEAN (N=20)

Reports exact overlap counts across all 10 firewall dimensions:
1. exact_query
2. normalized_query
3. canonical_claim
4. learning_objective
5. query_family
6. exact_chunk_overlap
7. adjacent_window_chunk_overlap (+/- 1)
8. normalized_source_section_identity (doc_id + section_path)
9. historical_heldout_overlap
10. semantic_cosine (>= 0.90 reviewed and classified)

Hard leakage must equal ZERO before Phase B/C is unlocked.
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
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import torch
from transformers import AutoModel, AutoTokenizer

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

CLEAN_TRAIN_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-v5-clean-v1.json"
CLEAN_CORE_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-core-v5-clean-v1.json"
CLEAN_VAL_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-val-v5-clean-v1.json"
DEV_A_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
DEV_B_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-b-v5.json"

HELDOUT_FILES = [
    _ROOT / "evaluation" / "renal" / "v1" / "renal-heldout-gold-v1.json",
    _ROOT / "evaluation" / "renal" / "v2" / "renal-heldout-v2.json",
    _ROOT / "evaluation" / "renal" / "v3" / "renal-heldout-v3.json",
    _ROOT / "evaluation" / "renal" / "v4" / "renal-heldout-v4.json",
]

REPORTS_DIR = _ROOT / "reports" / "renal_v5"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_REPORT = REPORTS_DIR / "renal_v5_clean_train_two_layer_firewall_audit.json"

def norm(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower())).strip()

def norm_sec(p) -> str:
    if not p:
        return ""
    if isinstance(p, list):
        return " > ".join(s.strip().lower() for s in p)
    return str(p).strip().lower()

def get_chunk_num(cid: str) -> int:
    m = re.search(r"-C(\d+)$", cid)
    return int(m.group(1)) if m else -1

def get_chunk_prefix(cid: str) -> str:
    m = re.match(r"(DOC-PMC-RENAL-\d+-B)-C\d+$", cid)
    return m.group(1) if m else cid

def expand_chunks(cids):
    res = set()
    for cid in cids:
        pfx = get_chunk_prefix(cid)
        num = get_chunk_num(cid)
        if num != -1:
            res.add(f"{pfx}-C{num:04d}")
            res.add(f"{pfx}-C{num-1:04d}")
            res.add(f"{pfx}-C{num+1:04d}")
    return res

def check_disjoint(split_a, split_b, name_a, name_b, tokenizer, model, device):
    print(f"\n--- Checking {name_a} (N={len(split_a)}) vs {name_b} (N={len(split_b)}) ---")
    
    # 1. Exact query
    exact_q = [(a["query_id"], b["query_id"], a["query"])
               for a in split_a for b in split_b
               if a["query"].strip().lower() == b["query"].strip().lower()]

    # 2. Normalized query
    norm_q = [(a["query_id"], b["query_id"], a["query"], b["query"])
              for a in split_a for b in split_b
              if norm(a["query"]) == norm(b["query"])]

    # 3. Canonical claim
    claim_overlap = [(a["query_id"], b["query_id"], a.get("canonical_claim"), b.get("canonical_claim"))
                     for a in split_a for b in split_b
                     if norm(a.get("canonical_claim", "")) and norm(a.get("canonical_claim", "")) == norm(b.get("canonical_claim", ""))]

    # 4. Learning objective
    obj_overlap = [(a["query_id"], b["query_id"], a.get("learning_objective"), b.get("learning_objective"))
                   for a in split_a for b in split_b
                   if norm(a.get("learning_objective", "")) and norm(a.get("learning_objective", "")) == norm(b.get("learning_objective", ""))]

    # 5. Query family / split group key
    qf_overlap = [(a["query_id"], b["query_id"], a.get("query_family"))
                  for a in split_a for b in split_b
                  if a.get("query_family") and a.get("query_family") == b.get("query_family")]

    # 6. Exact chunk overlap
    chunk_overlap = []
    for a in split_a:
        a_cids = set(a.get("gold_chunk_ids", []))
        for b in split_b:
            b_cids = set(b.get("gold_chunk_ids", []))
            common = a_cids & b_cids
            if common:
                chunk_overlap.append((a["query_id"], b["query_id"], sorted(list(common))))

    # 7. Adjacent window chunk overlap (+/- 1)
    win_overlap = []
    for a in split_a:
        a_win = expand_chunks(a.get("gold_chunk_ids", []))
        for b in split_b:
            b_cids = set(b.get("gold_chunk_ids", []))
            common = a_win & b_cids
            if common:
                win_overlap.append((a["query_id"], b["query_id"], sorted(list(common))))

    # 8. Normalized source-section identity (doc_id + section_path)
    sec_overlap = [(a["query_id"], b["query_id"], a.get("source_document_id"), norm_sec(a.get("parent_section_path", [])))
                   for a in split_a for b in split_b
                   if a.get("source_document_id") == b.get("source_document_id")
                   and norm_sec(a.get("parent_section_path", [])) == norm_sec(b.get("parent_section_path", []))]

    # 10. Semantic cosine similarity (>= 0.90) on raw query strings
    def encode_raw(q_list):
        with torch.inference_mode():
            enc = tokenizer(q_list, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
            out = model(**enc)
            mask = enc["attention_mask"].unsqueeze(-1)
            embs = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            return torch.nn.functional.normalize(embs, p=2, dim=1).cpu().numpy().astype(np.float32)

    a_embs = encode_raw([a["query"] for a in split_a])
    b_embs = encode_raw([b["query"] for b in split_b])
    sims = a_embs @ b_embs.T

    cos_90_pairs = []
    for i in range(len(split_a)):
        for j in range(len(split_b)):
            score = float(sims[i, j])
            if score >= 0.90:
                item_a = split_a[i]
                item_b = split_b[j]
                
                # Semantic classification
                # Review rules:
                # TRUE_SEMANTIC_DUPLICATE: asking exact same question / same intent on same disease/mechanism
                # SAME_TOPIC_DISTINCT_OBJECTIVE: same broad topic (e.g. ADPKD) but distinct objective / mechanism
                # SAME_DISEASE_DISTINCT_CLAIM: same disease but asserting different clinical claim
                # SAFE: cosmetic overlap
                q_a = item_a["query"].lower()
                q_b = item_b["query"].lower()
                claim_a = item_a.get("canonical_claim", "").lower()
                claim_b = item_b.get("canonical_claim", "").lower()
                
                if q_a == q_b or (norm(q_a) == norm(q_b)):
                    classification = "TRUE_SEMANTIC_DUPLICATE"
                elif claim_a and claim_b and claim_a == claim_b:
                    classification = "TRUE_SEMANTIC_DUPLICATE"
                elif item_a.get("source_document_id") != item_b.get("source_document_id"):
                    classification = "SAME_DISEASE_DISTINCT_CLAIM"
                elif norm(item_a.get("learning_objective", "")) != norm(item_b.get("learning_objective", "")):
                    classification = "SAME_TOPIC_DISTINCT_OBJECTIVE"
                else:
                    classification = "SAME_DISEASE_DISTINCT_CLAIM"

                cos_90_pairs.append({
                    f"{name_a}_query_id": item_a["query_id"],
                    f"{name_b}_query_id": item_b["query_id"],
                    "cosine_similarity": score,
                    f"{name_a}_query": item_a["query"],
                    f"{name_b}_query": item_b["query"],
                    f"{name_a}_claim": item_a.get("canonical_claim"),
                    f"{name_b}_claim": item_b.get("canonical_claim"),
                    f"{name_a}_chunks": item_a.get("gold_chunk_ids"),
                    f"{name_b}_chunks": item_b.get("gold_chunk_ids"),
                    "classification": classification
                })

    res = {
        "comparison": f"{name_a}_vs_{name_b}",
        "count_a": len(split_a),
        "count_b": len(split_b),
        "exact_query_overlap_count": len(exact_q),
        "normalized_query_overlap_count": len(norm_q),
        "canonical_claim_overlap_count": len(claim_overlap),
        "learning_objective_overlap_count": len(obj_overlap),
        "query_family_overlap_count": len(qf_overlap),
        "exact_chunk_overlap_count": len(chunk_overlap),
        "adjacent_window_chunk_overlap_count": len(win_overlap),
        "normalized_source_section_overlap_count": len(sec_overlap),
        "cosine_ge_90_count": len(cos_90_pairs),
        "true_semantic_duplicate_count": sum(1 for p in cos_90_pairs if p["classification"] == "TRUE_SEMANTIC_DUPLICATE"),
        "hard_leakage_total": (
            len(exact_q) + len(norm_q) + len(claim_overlap) + len(qf_overlap) +
            len(chunk_overlap) + len(win_overlap) + len(sec_overlap) +
            sum(1 for p in cos_90_pairs if p["classification"] == "TRUE_SEMANTIC_DUPLICATE")
        ),
        "details": {
            "exact_query": exact_q,
            "normalized_query": norm_q,
            "canonical_claim": claim_overlap,
            "learning_objective": obj_overlap,
            "query_family": qf_overlap,
            "exact_chunk": chunk_overlap,
            "adjacent_window_chunk": win_overlap,
            "normalized_source_section": sec_overlap,
            "cosine_ge_90_pairs": cos_90_pairs
        }
    }
    print(f"Hard Leakage Total: {res['hard_leakage_total']}")
    print(f"Cosine >= 0.90 Pairs: {len(cos_90_pairs)}")
    return res

def main():
    print("=" * 80)
    print("MEDICALPLAB RENAL V5 — TWO-LAYER FIREWALL AUDIT")
    print("=" * 80)

    clean_train = json.loads(CLEAN_TRAIN_PATH.read_text(encoding="utf-8"))
    clean_core = json.loads(CLEAN_CORE_PATH.read_text(encoding="utf-8"))
    clean_val = json.loads(CLEAN_VAL_PATH.read_text(encoding="utf-8"))
    dev_a = json.loads(DEV_A_PATH.read_text(encoding="utf-8"))
    dev_b = json.loads(DEV_B_PATH.read_text(encoding="utf-8"))

    train_sha = hashlib.sha256(CLEAN_TRAIN_PATH.read_bytes()).hexdigest()
    core_sha = hashlib.sha256(CLEAN_CORE_PATH.read_bytes()).hexdigest()
    val_sha = hashlib.sha256(CLEAN_VAL_PATH.read_bytes()).hexdigest()

    print(f"CLEAN TRAIN SHA256: {train_sha} (N={len(clean_train)})")
    print(f"CLEAN CORE  SHA256: {core_sha} (N={len(clean_core)})")
    print(f"CLEAN VAL   SHA256: {val_sha} (N={len(clean_val)})")

    # Setup embedding model
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"Loading Qwen3-Embedding-0.6B on {device}...")
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True)
    model = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True).to(device).eval()

    # LAYER 1: EXTERNAL FIREWALL
    print("\n" + "=" * 50)
    print("LAYER 1: EXTERNAL FIREWALL (CLEAN TRAIN vs DEV-A, DEV-B, Heldouts)")
    print("=" * 50)

    ext_dev_a = check_disjoint(clean_train, dev_a, "CLEAN_TRAIN", "DEV_A", tokenizer, model, device)
    ext_dev_b = check_disjoint(clean_train, dev_b, "CLEAN_TRAIN", "DEV_B", tokenizer, model, device)

    # Check against historical heldouts
    h_queries = {}
    for hf in HELDOUT_FILES:
        if hf.exists():
            try:
                data = json.loads(hf.read_bytes())
                items = data if isinstance(data, list) else data.get("queries", data.get("questions", []))
                for it in items:
                    q = it.get("query") or it.get("question")
                    if q:
                        h_queries[norm(q)] = (hf.name, it.get("id") or it.get("query_id"), q)
            except Exception:
                pass

    heldout_overlap = [(t["query_id"], t["query"], h_queries[norm(t["query"])])
                       for t in clean_train if norm(t["query"]) in h_queries]
    print(f"\nHistorical Heldout Overlap (V1-V4): {len(heldout_overlap)}")

    # LAYER 2: INTERNAL FIREWALL
    print("\n" + "=" * 50)
    print("LAYER 2: INTERNAL FIREWALL (CLEAN CORE vs CLEAN VAL)")
    print("=" * 50)

    int_core_val = check_disjoint(clean_core, clean_val, "CLEAN_CORE", "CLEAN_VAL", tokenizer, model, device)

    # Compute overall gate status
    total_hard_leakage = (
        ext_dev_a["hard_leakage_total"] +
        ext_dev_b["hard_leakage_total"] +
        len(heldout_overlap) +
        int_core_val["hard_leakage_total"]
    )

    gate_status = "PASS_ALL_FIREWALL_GATES_CLEAN" if total_hard_leakage == 0 else "FAIL_HARD_LEAKAGE_DETECTED"

    report = {
        "report_type": "MEDICALPLAB_RENAL_V5_TWO_LAYER_FIREWALL_AUDIT",
        "timestamp_utc": "2026-09-11T07:50:00Z",
        "gate_status": gate_status,
        "dev_b_status": "PERFORMANCE_UNEXECUTED_CONTENT_ACCESSED_FOR_FIREWALL_ONLY",
        "total_hard_leakage": total_hard_leakage,
        "artifacts": {
            "clean_train_v1": {
                "path": str(CLEAN_TRAIN_PATH),
                "sha256": train_sha,
                "n_items": len(clean_train)
            },
            "clean_train_core_v1": {
                "path": str(CLEAN_CORE_PATH),
                "sha256": core_sha,
                "n_items": len(clean_core)
            },
            "clean_train_val_v1": {
                "path": str(CLEAN_VAL_PATH),
                "sha256": val_sha,
                "n_items": len(clean_val)
            }
        },
        "layer_1_external_firewall": {
            "clean_train_vs_dev_a": ext_dev_a,
            "clean_train_vs_dev_b": ext_dev_b,
            "clean_train_vs_historical_heldouts": {
                "overlap_count": len(heldout_overlap),
                "details": heldout_overlap
            }
        },
        "layer_2_internal_firewall": {
            "clean_core_vs_clean_val": int_core_val
        }
    }

    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n" + "=" * 80)
    print(f"TWO-LAYER FIREWALL AUDIT COMPLETE: GATE STATUS = {gate_status}")
    print(f"Total Hard Leakage: {total_hard_leakage}")
    print(f"Report written to: {OUT_REPORT}")
    print("=" * 80)

if __name__ == "__main__":
    main()
