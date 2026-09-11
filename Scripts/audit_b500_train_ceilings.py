import sys
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

import torch
from transformers import AutoModel, AutoTokenizer

core_path = _ROOT / "evaluation/renal/v5/renal-rerank-train-core-v5.json"
val_path = _ROOT / "evaluation/renal/v5/renal-rerank-train-val-v5.json"
chunks_dir = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
cache_dir = _ROOT / "Data/experiments/renal_v3/cache"
reports_dir = _ROOT / "reports/renal_v5"
reports_dir.mkdir(parents=True, exist_ok=True)

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
            "query": it["query"],
            "num_gold_chunks": len(g_cids),
            "best_gold_dense_rank": best_rank,
            "in_b500": in_500,
            "gold_doc_rank": gold_doc_rank
        })

    report = {
        "split": name,
        "n_queries": n_items,
        "gold_present_in_b500_count": gold_in_b500,
        "gold_present_in_b500_percent": float(gold_in_b500 / n_items * 100),
        "empty_unresolved_qrels": empty_qrels,
        "multiple_relevant_passages_count": len(multi_positives),
        "mean_gold_chunks_per_query": float(np.mean([len(it.get("gold_chunk_ids", [])) for it in items])),
        "best_gold_dense_rank_summary": {
            "min": int(min(best_dense_ranks)),
            "median": float(np.median(best_dense_ranks)),
            "p75": float(np.percentile(best_dense_ranks, 75)),
            "p90": float(np.percentile(best_dense_ranks, 90)),
            "max": int(max(best_dense_ranks)),
        },
        "gold_doc_rank_summary": {
            "min": int(min(gold_doc_ranks)),
            "median": float(np.median(gold_doc_ranks)),
            "p75": float(np.percentile(gold_doc_ranks, 75)),
            "max": int(max(gold_doc_ranks)),
        },
        "queries_with_best_rank_gt_500": [r["query_id"] for r in per_query_records if not r["in_b500"]],
        "per_query_records": per_query_records
    }
    return report

print("Auditing TRAIN_CORE...")
core_report = audit_split("TRAIN_CORE", core)
print("Auditing TRAIN_VAL...")
val_report = audit_split("TRAIN_VAL", val)

full_b500_report = {
    "timestamp": "2026-09-11T07:38:00+00:00",
    "train_core": core_report,
    "train_val": val_report
}

out_file = reports_dir / "renal_v5_b500_train_splits_ceiling_audit.json"
out_file.write_text(json.dumps(full_b500_report, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"B=500 ceiling audit persisted to: {out_file}")
print(f"TRAIN_CORE B=500 Coverage: {core_report['gold_present_in_b500_count']} / {core_report['n_queries']} ({core_report['gold_present_in_b500_percent']:.1f}%)")
print(f"TRAIN_VAL  B=500 Coverage: {val_report['gold_present_in_b500_count']} / {val_report['n_queries']} ({val_report['gold_present_in_b500_percent']:.1f}%)")
