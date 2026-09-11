"""
MedicalPlab Renal V5 — Audit B=500 Candidate Ceilings on Clean Train Splits
===========================================================================
Recomputes candidate coverage, best-gold rank distribution, gold-document rank,
empty/unresolved qrels, and multi-positive distribution from scratch on:
- TRAIN_CORE_CLEAN (N=60)
- TRAIN_VAL_CLEAN (N=20)
"""

import sys
import json
import hashlib
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

core_path = _ROOT / "evaluation/renal/v5/renal-rerank-train-core-v5-clean-v1.json"
val_path = _ROOT / "evaluation/renal/v5/renal-rerank-train-val-v5-clean-v1.json"
chunks_dir = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
cache_dir = _ROOT / "Data/experiments/renal_v3/cache"
reports_dir = _ROOT / "reports/renal_v5"
reports_dir.mkdir(parents=True, exist_ok=True)
out_report = reports_dir / "renal_v5_b500_clean_train_ceiling_report.json"

core = json.loads(core_path.read_text(encoding="utf-8"))
val = json.loads(val_path.read_text(encoding="utf-8"))

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

def audit_split(name, items):
    q_texts = [QUERY_INSTRUCTION + it["query"] for it in items]
    with torch.inference_mode():
        enc = tok(q_texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        out = mod(**enc)
        mask = enc["attention_mask"].unsqueeze(-1)
        q_embs = (out.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        q_embs = torch.nn.functional.normalize(q_embs, p=2, dim=1).cpu().numpy().astype(np.float32)

    n_items = len(items)
    empty_qrels = []
    multi_positives = []
    gold_in_b500 = 0
    best_dense_ranks = []
    gold_doc_ranks = []
    per_query_records = []

    for i, it in enumerate(items):
        qid = it["query_id"]
        g_cids = it.get("gold_chunk_ids", [])
        if not g_cids:
            empty_qrels.append(qid)
            continue
        if len(g_cids) > 1:
            multi_positives.append({"query_id": qid, "num_positives": len(g_cids)})

        g_doc = it.get("gold_doc_id") or it.get("source_document_id")
        q_vec = q_embs[i]
        p_scores = corpus_embs @ q_vec
        d_scores = doc_embs @ q_vec

        comb_scores = p_scores.copy()
        for c_idx, did in enumerate(chunk_doc_ids):
            if did in doc_id_to_idx:
                comb_scores[c_idx] += 0.18 * d_scores[doc_id_to_idx[did]]

        ranked_indices = comb_scores.argsort()[::-1]
        top500_indices = set(ranked_indices[:500])
        gold_indices = [chunk_id_to_idx[cid] for cid in g_cids if cid in chunk_id_to_idx]

        in_500 = any(g_idx in top500_indices for g_idx in gold_indices)
        if in_500:
            gold_in_b500 += 1

        best_rank = min(int(np.where(ranked_indices == g_idx)[0][0]) + 1 for g_idx in gold_indices)
        best_dense_ranks.append(best_rank)

        doc_ranked = d_scores.argsort()[::-1]
        doc_idx = doc_id_to_idx.get(g_doc)
        gold_doc_rank = int(np.where(doc_ranked == doc_idx)[0][0]) + 1 if doc_idx is not None else -1
        gold_doc_ranks.append(gold_doc_rank)

        per_query_records.append({
            "query_id": qid,
            "best_dense_rank": best_rank,
            "in_b500": in_500,
            "gold_doc_rank": gold_doc_rank,
            "gold_chunk_ids": g_cids
        })

    best_ranks_arr = np.array(best_dense_ranks)
    doc_ranks_arr = np.array(gold_doc_ranks)

    summary = {
        "split_name": name,
        "n_queries": n_items,
        "empty_qrel_count": len(empty_qrels),
        "empty_qrels": empty_qrels,
        "multi_positive_count": len(multi_positives),
        "multi_positives": multi_positives,
        "b500_coverage_count": gold_in_b500,
        "b500_coverage_ratio": gold_in_b500 / n_items,
        "b500_coverage_percent": round(gold_in_b500 / n_items * 100, 2),
        "best_gold_rank_percentiles": {
            "min": int(best_ranks_arr.min()),
            "p25": float(np.percentile(best_ranks_arr, 25)),
            "median_p50": float(np.percentile(best_ranks_arr, 50)),
            "p75": float(np.percentile(best_ranks_arr, 75)),
            "p90": float(np.percentile(best_ranks_arr, 90)),
            "max": int(best_ranks_arr.max())
        },
        "coverage_at_k": {
            "top1": int((best_ranks_arr <= 1).sum()),
            "top5": int((best_ranks_arr <= 5).sum()),
            "top10": int((best_ranks_arr <= 10).sum()),
            "top20": int((best_ranks_arr <= 20).sum()),
            "top50": int((best_ranks_arr <= 50).sum()),
            "top100": int((best_ranks_arr <= 100).sum()),
            "top200": int((best_ranks_arr <= 200).sum()),
            "top500": int((best_ranks_arr <= 500).sum())
        },
        "gold_document_rank_percentiles": {
            "doc_rank1_count": int((doc_ranks_arr == 1).sum()),
            "doc_rank1_ratio": round(float((doc_ranks_arr == 1).mean()), 4),
            "doc_top3_count": int((doc_ranks_arr <= 3).sum()),
            "doc_top3_ratio": round(float((doc_ranks_arr <= 3).mean()), 4),
            "doc_median_rank": float(np.percentile(doc_ranks_arr, 50))
        },
        "per_query_records": per_query_records
    }
    return summary

def main():
    print("=" * 80)
    print("AUDITING B=500 CANDIDATE CEILINGS ON CLEAN TRAIN BENCHMARK")
    print("=" * 80)
    print(f"TRAIN_CORE_CLEAN: {core_path} (N={len(core)})")
    print(f"TRAIN_VAL_CLEAN:  {val_path} (N={len(val)})")

    core_summary = audit_split("TRAIN_CORE_CLEAN", core)
    val_summary = audit_split("TRAIN_VAL_CLEAN", val)

    report = {
        "report_type": "MEDICALPLAB_RENAL_V5_B500_CLEAN_TRAIN_CEILING_REPORT",
        "timestamp_utc": "2026-09-11T07:55:00Z",
        "artifacts": {
            "core": {"path": str(core_path), "sha256": hashlib.sha256(core_path.read_bytes()).hexdigest(), "n": len(core)},
            "val": {"path": str(val_path), "sha256": hashlib.sha256(val_path.read_bytes()).hexdigest(), "n": len(val)}
        },
        "train_core_clean": core_summary,
        "train_val_clean": val_summary
    }

    out_report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\n--- Summary ---")
    print(f"TRAIN_CORE_CLEAN B=500 Coverage: {core_summary['b500_coverage_count']}/{core_summary['n_queries']} ({core_summary['b500_coverage_percent']}%)")
    print(f"TRAIN_CORE_CLEAN Median Rank:     {core_summary['best_gold_rank_percentiles']['median_p50']}")
    print(f"TRAIN_VAL_CLEAN  B=500 Coverage: {val_summary['b500_coverage_count']}/{val_summary['n_queries']} ({val_summary['b500_coverage_percent']}%)")
    print(f"TRAIN_VAL_CLEAN  Median Rank:     {val_summary['best_gold_rank_percentiles']['median_p50']}")
    print(f"Written to: {out_report}")

if __name__ == "__main__":
    main()
