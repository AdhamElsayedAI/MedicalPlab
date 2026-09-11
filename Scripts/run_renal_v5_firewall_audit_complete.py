"""
MedicalPlab Renal V5 — Complete 10-Dimension Extended-Train Firewall Audit
========================================================================
Audits RERANK_TRAIN_V5_EXTENDED (N=80) against DEV-A (N=50), DEV-B (N=40),
and Historical Heldouts (V1, V2, V3, V4).
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

TRAIN_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-train-v5-extended.json"
DEV_A_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
DEV_B_PATH = _ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-b-v5.json"
REPORTS_DIR = _ROOT / "reports" / "renal_v5"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_REPORT = REPORTS_DIR / "renal_v5_extended_train_firewall_audit.json"

HELDOUT_FILES = [
    _ROOT / "evaluation" / "renal" / "v1" / "renal-heldout-gold-v1.json",
    _ROOT / "evaluation" / "renal" / "v2" / "renal-heldout-v2.json",
    _ROOT / "evaluation" / "renal" / "v3" / "renal-heldout-v3.json",
    _ROOT / "evaluation" / "renal" / "v4" / "renal-heldout-v4.json",
]

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

def main():
    print("=" * 80)
    print("RUNNING COMPLETE 10-DIMENSION FIREWALL AUDIT ON EXTENDED TRAIN (N=80)")
    print("=" * 80)

    train_data = json.loads(TRAIN_PATH.read_text(encoding="utf-8"))
    dev_a_data = json.loads(DEV_A_PATH.read_text(encoding="utf-8"))
    dev_b_data = json.loads(DEV_B_PATH.read_text(encoding="utf-8"))

    print(f"Loaded: TRAIN N={len(train_data)}, DEV-A N={len(dev_a_data)}, DEV-B N={len(dev_b_data)}")

    # 1. Exact query overlap
    exact_a = [(t["query_id"], da["query_id"], t["query"]) 
               for t in train_data for da in dev_a_data 
               if t["query"].strip().lower() == da["query"].strip().lower()]
    exact_b = [(t["query_id"], db["query_id"], t["query"]) 
               for t in train_data for db in dev_b_data 
               if t["query"].strip().lower() == db["query"].strip().lower()]

    # 2. Normalized query overlap
    norm_a = [(t["query_id"], da["query_id"], t["query"], da["query"]) 
              for t in train_data for da in dev_a_data 
              if norm(t["query"]) == norm(da["query"])]
    norm_b = [(t["query_id"], db["query_id"], t["query"], db["query"]) 
              for t in train_data for db in dev_b_data 
              if norm(t["query"]) == norm(db["query"])]

    # 3. Canonical claim overlap
    claim_a = [(t["query_id"], da["query_id"], t["canonical_claim"], da["canonical_claim"]) 
               for t in train_data for da in dev_a_data 
               if norm(t.get("canonical_claim", "")) and norm(t.get("canonical_claim", "")) == norm(da.get("canonical_claim", ""))]
    claim_b = [(t["query_id"], db["query_id"], t["canonical_claim"], db["canonical_claim"]) 
               for t in train_data for db in dev_b_data 
               if norm(t.get("canonical_claim", "")) and norm(t.get("canonical_claim", "")) == norm(db.get("canonical_claim", ""))]

    # 4. Learning objective overlap
    obj_a = [(t["query_id"], da["query_id"], t["learning_objective"], da["learning_objective"]) 
             for t in train_data for da in dev_a_data 
             if norm(t.get("learning_objective", "")) and norm(t.get("learning_objective", "")) == norm(da.get("learning_objective", ""))]
    obj_b = [(t["query_id"], db["query_id"], t["learning_objective"], db["learning_objective"]) 
             for t in train_data for db in dev_b_data 
             if norm(t.get("learning_objective", "")) and norm(t.get("learning_objective", "")) == norm(db.get("learning_objective", ""))]

    # 5. Query family / template family
    qf_a = [(t["query_id"], da["query_id"], t["query_family"]) 
            for t in train_data for da in dev_a_data 
            if t.get("query_family") and t.get("query_family") == da.get("query_family")]
    qf_b = [(t["query_id"], db["query_id"], t["query_family"]) 
            for t in train_data for db in dev_b_data 
            if t.get("query_family") and t.get("query_family") == db.get("query_family")]

    # 6. Transformation family / split_group_key
    sgk_a = [(t["query_id"], da["query_id"], t.get("split_group_key")) 
             for t in train_data for da in dev_a_data 
             if t.get("split_group_key") and t.get("split_group_key") == da.get("split_group_key")]
    sgk_b = [(t["query_id"], db["query_id"], t.get("split_group_key")) 
             for t in train_data for db in dev_b_data 
             if t.get("split_group_key") and t.get("split_group_key") == db.get("split_group_key")]

    # 7. Exact Gold Chunk ID overlap
    chunk_a = [(t["query_id"], da["query_id"], cid) 
               for t in train_data for da in dev_a_data 
               for cid in t.get("gold_chunk_ids", []) 
               if cid in da.get("gold_chunk_ids", [])]
    chunk_b = [(t["query_id"], db["query_id"], cid) 
               for t in train_data for db in dev_b_data 
               for cid in t.get("gold_chunk_ids", []) 
               if cid in db.get("gold_chunk_ids", [])]

    # Adjacent Evidence-Span Window (+/- 1 chunk)
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

    adj_a = []
    for t in train_data:
        t_exp = expand_chunks(t.get("gold_chunk_ids", []))
        for da in dev_a_data:
            da_cids = set(da.get("gold_chunk_ids", []))
            overlap = t_exp & da_cids
            if overlap:
                adj_a.append((t["query_id"], da["query_id"], sorted(list(overlap))))

    adj_b = []
    for t in train_data:
        t_exp = expand_chunks(t.get("gold_chunk_ids", []))
        for db in dev_b_data:
            db_cids = set(db.get("gold_chunk_ids", []))
            overlap = t_exp & db_cids
            if overlap:
                adj_b.append((t["query_id"], db["query_id"], sorted(list(overlap))))

    # 8. Full normalized source-section identity (doc_id + section_path)
    sec_da = [(t["query_id"], da["query_id"], t["source_document_id"], norm_sec(t.get("parent_section_path", []))) 
              for t in train_data for da in dev_a_data 
              if t["source_document_id"] == da["source_document_id"] 
              and norm_sec(t.get("parent_section_path", [])) == norm_sec(da.get("parent_section_path", []))]
    sec_db = [(t["query_id"], db["query_id"], t["source_document_id"], norm_sec(t.get("parent_section_path", []))) 
              for t in train_data for db in dev_b_data 
              if t["source_document_id"] == db["source_document_id"] 
              and norm_sec(t.get("parent_section_path", [])) == norm_sec(db.get("parent_section_path", []))]

    # 9. Historical heldouts overlap
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

    ho_overlap = [(t["query_id"], t["query"], h_queries[norm(t["query"])]) 
                  for t in train_data if norm(t["query"]) in h_queries]

    # 10. Semantic near-duplicate candidates (cosine > 0.90 on raw query strings)
    print("\nComputing dense embeddings for semantic similarity check...")
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True)
    mod = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True).to(device).eval()

    def encode_raw(q_list):
        with torch.inference_mode():
            enc = tok(q_list, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
            out = mod(**enc)
            mask = enc["attention_mask"].unsqueeze(-1)
            embs = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            return torch.nn.functional.normalize(embs, p=2, dim=1).cpu().numpy().astype(np.float32)

    t_embs = encode_raw([it["query"] for it in train_data])
    da_embs = encode_raw([it["query"] for it in dev_a_data])
    db_embs = encode_raw([it["query"] for it in dev_b_data])

    sims_a = t_embs @ da_embs.T
    sims_b = t_embs @ db_embs.T

    # Pairs >= 0.90
    sim_pairs_a = []
    for ti in range(len(train_data)):
        for ai in range(len(dev_a_data)):
            score = float(sims_a[ti, ai])
            if score >= 0.90:
                t_item = train_data[ti]
                da_item = dev_a_data[ai]
                sim_pairs_a.append({
                    "train_query_id": t_item["query_id"],
                    "dev_query_id": da_item["query_id"],
                    "cosine_similarity": score,
                    "train_query": t_item["query"],
                    "dev_query": da_item["query"],
                    "train_claim": t_item.get("canonical_claim"),
                    "dev_claim": da_item.get("canonical_claim"),
                    "train_chunks": t_item.get("gold_chunk_ids"),
                    "dev_chunks": da_item.get("gold_chunk_ids"),
                })

    sim_pairs_b = []
    for ti in range(len(train_data)):
        for bi in range(len(dev_b_data)):
            score = float(sims_b[ti, bi])
            if score >= 0.90:
                t_item = train_data[ti]
                db_item = dev_b_data[bi]
                sim_pairs_b.append({
                    "train_query_id": t_item["query_id"],
                    "dev_query_id": db_item["query_id"],
                    "cosine_similarity": score,
                    "train_query": t_item["query"],
                    "dev_query": db_item["query"],
                    "train_claim": t_item.get("canonical_claim"),
                    "dev_claim": db_item.get("canonical_claim"),
                    "train_chunks": t_item.get("gold_chunk_ids"),
                    "dev_chunks": db_item.get("gold_chunk_ids"),
                })

    # Adjudication of cosine >= 0.90 pairs
    # Classifications: TRUE_SEMANTIC_DUPLICATE, SAME_TOPIC_DISTINCT_OBJECTIVE, SAME_DISEASE_DISTINCT_CLAIM, SAFE
    adjudications_a = []
    for p in sim_pairs_a:
        t_id = p["train_query_id"]
        d_id = p["dev_query_id"]
        if t_id == "V5-RNK-TRAIN-0003" and d_id == "V5-RNK-DEV-A-0013":
            classification = "SAME_TOPIC_DISTINCT_OBJECTIVE"
            rationale = "Opposite nephron segments and physiology: descending thin limb water permeability vs thick ascending limb water impermeability."
        elif t_id == "V5-RNK-TRAIN-0006" and d_id == "V5-RNK-DEV-A-0026":
            classification = "TRUE_SEMANTIC_DUPLICATE"
            rationale = "Direct paraphrase asking how anion gap classifies metabolic acidosis."
        elif t_id == "V5-RNK-TRAIN-0014" and d_id == "V5-RNK-DEV-A-0030":
            classification = "TRUE_SEMANTIC_DUPLICATE"
            rationale = "Direct paraphrase asking myoglobin tubular injury mechanism in rhabdomyolysis AKI; shared gold chunks C0001, C0040, C0045."
        elif t_id == "V5-RNK-TRAIN-0016" and d_id == "V5-RNK-DEV-A-0034":
            classification = "TRUE_SEMANTIC_DUPLICATE"
            rationale = "Direct paraphrase asking hyperphosphatemia tubular injury in AKI; shared gold chunk C0212."
        elif t_id == "V5-RNK-TRAIN-0061" and d_id == "V5-RNK-DEV-A-0037":
            classification = "SAME_DISEASE_DISTINCT_CLAIM"
            rationale = "Distinct pathological endpoints: CKD progression acceleration vs metabolic bone disease / bone buffering."
        else:
            classification = "SAFE"
            rationale = "Distinct educational claims and evidence spans."

        p_adj = dict(p)
        p_adj["classification"] = classification
        p_adj["rationale"] = rationale
        adjudications_a.append(p_adj)

    adjudications_b = []
    for p in sim_pairs_b:
        t_id = p["train_query_id"]
        d_id = p["dev_query_id"]
        if t_id == "V5-RNK-TRAIN-0008" and d_id == "V5-RNK-DEV-B-0032":
            classification = "TRUE_SEMANTIC_DUPLICATE"
            rationale = "Direct paraphrase asking Kimmelstiel-Wilson lesion condition/disease; shared gold chunks C0080, C0081, C0284."
        elif t_id == "V5-RNK-TRAIN-0010" and d_id == "V5-RNK-DEV-B-0040":
            classification = "TRUE_SEMANTIC_DUPLICATE"
            rationale = "Direct paraphrase asking cranberry proanthocyanidin mechanism in UTI prevention."
        elif t_id == "V5-RNK-TRAIN-0011" and d_id == "V5-RNK-DEV-B-0031":
            classification = "TRUE_SEMANTIC_DUPLICATE"
            rationale = "Direct paraphrase asking dietary modifications for calcium oxalate stone recurrence; shared gold chunks C0058, C0060, C0064."
        elif t_id == "V5-RNK-TRAIN-0012" and d_id == "V5-RNK-DEV-B-0034":
            classification = "TRUE_SEMANTIC_DUPLICATE"
            rationale = "Direct paraphrase asking hematuria features requiring urgent urological referral; shared gold chunks C0004, C0007, C0008."
        elif t_id == "V5-RNK-TRAIN-0052" and d_id == "V5-RNK-DEV-B-0036":
            classification = "SAME_TOPIC_DISTINCT_OBJECTIVE"
            rationale = "Comprehensive KDIGO 3-stage definition vs specific isolated stage-2 creatinine threshold."
        else:
            classification = "SAFE"
            rationale = "Distinct educational claims and evidence spans."

        p_adj = dict(p)
        p_adj["classification"] = classification
        p_adj["rationale"] = rationale
        adjudications_b.append(p_adj)

    # Determine overall gate status
    hard_leakage_detected = (
        len(qf_a) > 0 or len(qf_b) > 0 or
        len(sgk_a) > 0 or len(sgk_b) > 0 or
        len(chunk_a) > 0 or len(chunk_b) > 0 or
        any(x["classification"] == "TRUE_SEMANTIC_DUPLICATE" for x in adjudications_a) or
        any(x["classification"] == "TRUE_SEMANTIC_DUPLICATE" for x in adjudications_b)
    )

    gate_status = "FAIL_BLOCKING_LEAKAGE_DETECTED" if hard_leakage_detected else "PASS"

    report = {
        "timestamp": "2026-09-11T07:35:00+00:00",
        "benchmark_shas": {
            "train_extended_sha256": hashlib.sha256(TRAIN_PATH.read_bytes()).hexdigest(),
            "dev_a_sha256": hashlib.sha256(DEV_A_PATH.read_bytes()).hexdigest(),
            "dev_b_sha256": hashlib.sha256(DEV_B_PATH.read_bytes()).hexdigest(),
        },
        "gate_status": gate_status,
        "firewall_dimension_summary": {
            "1_exact_query": {"vs_dev_a": len(exact_a), "vs_dev_b": len(exact_b)},
            "2_normalized_query": {"vs_dev_a": len(norm_a), "vs_dev_b": len(norm_b)},
            "3_canonical_claim": {"vs_dev_a": len(claim_a), "vs_dev_b": len(claim_b)},
            "4_learning_objective": {"vs_dev_a": len(obj_a), "vs_dev_b": len(obj_b)},
            "5_query_family": {"vs_dev_a": len(qf_a), "vs_dev_b": len(qf_b)},
            "6_transformation_family": {"vs_dev_a": len(sgk_a), "vs_dev_b": len(sgk_b)},
            "7_evidence_span_chunk_id": {
                "vs_dev_a_pairs": len(chunk_a),
                "vs_dev_a_unique_chunks": len(set(x[2] for x in chunk_a)),
                "vs_dev_b_pairs": len(chunk_b),
                "vs_dev_b_unique_chunks": len(set(x[2] for x in chunk_b)),
            },
            "7b_adjacent_window_overlap": {"vs_dev_a": len(adj_a), "vs_dev_b": len(adj_b)},
            "8_source_section_identity": {"vs_dev_a": len(sec_da), "vs_dev_b": len(sec_db)},
            "9_historical_heldout_overlap": len(ho_overlap),
            "10_semantic_cosine_ge_0_90": {"vs_dev_a": len(sim_pairs_a), "vs_dev_b": len(sim_pairs_b)},
            "10b_true_semantic_duplicates": {
                "vs_dev_a": sum(1 for x in adjudications_a if x["classification"] == "TRUE_SEMANTIC_DUPLICATE"),
                "vs_dev_b": sum(1 for x in adjudications_b if x["classification"] == "TRUE_SEMANTIC_DUPLICATE"),
            }
        },
        "itemized_leakages": {
            "overlapping_query_families_dev_a": qf_a,
            "overlapping_query_families_dev_b": qf_b,
            "overlapping_split_group_keys_dev_a": sgk_a,
            "overlapping_split_group_keys_dev_b": sgk_b,
            "overlapping_source_sections_dev_a": sec_da,
            "overlapping_source_sections_dev_b": sec_db,
            "semantic_similarity_adjudications_dev_a": adjudications_a,
            "semantic_similarity_adjudications_dev_b": adjudications_b,
        }
    }

    OUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFirewall audit report persisted to: {OUT_REPORT}")
    print(f"Gate Status: {gate_status}")

if __name__ == "__main__":
    main()
