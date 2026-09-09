"""Evidence Sufficiency Recalibration over Full 817-Chunk Frozen Corpus.

Recomputes evidence-sufficiency calibration on evaluation/evidence_sufficiency_calibration_v1.json (48 cases)
using the actual retrieval stack and score distribution over the full 817-chunk corpus snapshot.

Explicitly tracks:
- Dataset version: 1.0.0-draft (historical 48-case set: 20 supported, 12 partial, 16 unsupported)
- Score definition: Dense Cosine Similarity (Qwen/Qwen3-Embedding-0.6B) and Hybrid RRF
- Metrics: AUROC, AUPRC, threshold tau sweep
- Confusion counts: TP, FP (partial/unsupported), TN, FN
- Rates: Precision, Recall, Coverage, Unsafe Acceptance Rate, Unsupported Acceptance Rate, False Refusal Rate
"""

import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = PROJECT_ROOT / "Data" / "metadata" / "corpus_cardiorespiratory_snapshot_v1.json"
EMB_CACHE_PATH = PROJECT_ROOT / "Data" / "metadata" / "corpus_817_qwen3_embeddings.npy"
CALIB_PATH = PROJECT_ROOT / "evaluation" / "evidence_sufficiency_calibration_v1.json"
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"

QUERY_INSTRUCTION = (
    "Instruct: Given a medical education query, retrieve the passages "
    "from the available medical sources that most directly support the "
    "requested claim. Respect any source explicitly requested by the "
    "query. Do not assume every query targets a guideline.\nQuery:"
)


def block_key(chunk: dict[str, Any]) -> str:
    return f"{chunk['document_id']}:B{int(chunk['source_block_index']):04d}"


def run_recalibration(retrieval_mode: str = "dense_only"):
    from sentence_transformers import SentenceTransformer

    # 1. Load Snapshot
    snapshot = json.load(open(SNAPSHOT_PATH, encoding="utf-8"))
    chunks = []
    for d in snapshot["documents"]:
        c_path = PROJECT_ROOT / d["chunks_file"]
        c_data = json.load(open(c_path, encoding="utf-8"))
        c_list = c_data.get("chunks", []) if isinstance(c_data, dict) else c_data
        chunks.extend(c_list)

    chunk_keys = [block_key(c) for c in chunks]
    print(f"Loaded {len(chunks)} chunks from {snapshot['corpus_id']} v{snapshot['version']}")

    # 2. Load Embeddings
    if not EMB_CACHE_PATH.exists():
        raise FileNotFoundError(f"Corpus embeddings cache not found at {EMB_CACHE_PATH}. Run benchmark_full_corpus_suite.py first.")
    corpus_embs = np.load(EMB_CACHE_PATH)
    print(f"Loaded corpus embeddings matrix shape: {corpus_embs.shape}")

    # 3. Load Calibration Cases
    calib_data = json.load(open(CALIB_PATH, encoding="utf-8"))
    cases = calib_data["cases"]
    n_total = len(cases)
    supported_cases = [c for c in cases if c["support_label"] == "supported"]
    partial_cases = [c for c in cases if c["support_label"] == "partial"]
    unsupported_cases = [c for c in cases if c["support_label"] == "unsupported"]

    print(f"Calibration Dataset: {calib_data.get('calibration_set_id')} v{calib_data.get('version')} (HISTORICAL SET)")
    print(f"Total Cases: {n_total} | Supported: {len(supported_cases)} | Partial: {len(partial_cases)} | Unsupported: {len(unsupported_cases)}")

    # 4. Dense Model for Query Inference
    device = "cpu"
    dense_model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B", device=device)

    # 5. Compute Retrieval Scores for each calibration case
    case_results = []
    for case in cases:
        cid = case["case_id"]
        q_text = case["query"]
        label = case["support_label"]

        formatted_q = f"{QUERY_INSTRUCTION}\n{q_text.strip()}"
        q_emb = dense_model.encode([formatted_q], normalize_embeddings=True, show_progress_bar=False)[0]
        sims = np.dot(corpus_embs, q_emb)

        top1_idx = int(np.argmax(sims))
        top1_score = float(sims[top1_idx])
        top1_key = chunk_keys[top1_idx]
        top1_doc = chunks[top1_idx]["document_id"]

        case_results.append({
            "case_id": cid,
            "support_label": label,
            "is_supported": (label == "supported"),
            "is_partial": (label == "partial"),
            "is_unsupported": (label == "unsupported"),
            "top1_score": top1_score,
            "top1_block": top1_key,
            "top1_doc": top1_doc,
        })

    # 6. Evaluation metrics
    scores = np.array([r["top1_score"] for r in case_results])
    y_true_binary = np.array([1 if r["is_supported"] else 0 for r in case_results])

    auroc = roc_auc_score(y_true_binary, scores)
    auprc = average_precision_score(y_true_binary, scores)

    print(f"\n--- Fresh Calibration Results over 817 Chunks ({retrieval_mode}) ---")
    print(f"AUROC: {auroc:.4f}")
    print(f"AUPRC: {auprc:.4f}")

    # Score distributions by class
    dist = {}
    for l_name in ["supported", "partial", "unsupported"]:
        l_scores = [r["top1_score"] for r in case_results if r["support_label"] == l_name]
        dist[l_name] = {
            "count": len(l_scores),
            "min": round(float(np.min(l_scores)), 4),
            "mean": round(float(np.mean(l_scores)), 4),
            "median": round(float(np.median(l_scores)), 4),
            "max": round(float(np.max(l_scores)), 4),
            "std": round(float(np.std(l_scores)), 4),
        }
        print(f"{l_name:<12}: min={dist[l_name]['min']:.4f}, mean={dist[l_name]['mean']:.4f}, median={dist[l_name]['median']:.4f}, max={dist[l_name]['max']:.4f}")

    # Threshold sweep
    thresholds = np.linspace(float(scores.min()), float(scores.max()), 100)
    operating_points = []

    n_pos = len(supported_cases)      # 20
    n_part = len(partial_cases)       # 12
    n_unsup = len(unsupported_cases)  # 16
    n_non_sup = n_part + n_unsup      # 28

    for tau in thresholds:
        accepted = scores >= tau
        tp = sum(1 for r, acc in zip(case_results, accepted) if acc and r["is_supported"])
        fp_part = sum(1 for r, acc in zip(case_results, accepted) if acc and r["is_partial"])
        fp_unsup = sum(1 for r, acc in zip(case_results, accepted) if acc and r["is_unsupported"])
        fp = fp_part + fp_unsup

        fn = sum(1 for r, acc in zip(case_results, accepted) if (not acc) and r["is_supported"])
        tn_part = sum(1 for r, acc in zip(case_results, accepted) if (not acc) and r["is_partial"])
        tn_unsup = sum(1 for r, acc in zip(case_results, accepted) if (not acc) and r["is_unsupported"])
        tn = tn_part + tn_unsup

        cov = (tp + fp) / n_total
        prec = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
        rec = tp / n_pos
        f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        unsafe_acc_rate = fp / n_non_sup
        unsup_acc_rate = fp_unsup / n_unsup
        part_acc_rate = fp_part / n_part if n_part > 0 else 0.0
        false_ref_rate = fn / n_pos

        operating_points.append({
            "threshold": round(float(tau), 4),
            "coverage": round(float(cov), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1": round(float(f1), 4),
            "unsafe_acceptance_rate": round(float(unsafe_acc_rate), 4),
            "unsupported_acceptance_rate": round(float(unsup_acc_rate), 4),
            "partial_acceptance_rate": round(float(part_acc_rate), 4),
            "false_refusal_rate": round(float(false_ref_rate), 4),
            "confusion": {
                "tp": int(tp),
                "fp": int(fp),
                "fp_partial": int(fp_part),
                "fp_unsupported": int(fp_unsup),
                "tn": int(tn),
                "tn_partial": int(tn_part),
                "tn_unsupported": int(tn_unsup),
                "fn": int(fn),
            },
        })

    # Pick canonical profiles
    # 1. Zero Unsafe Accept (strictly 0 FP non-supported)
    zero_unsafe_pts = [p for p in operating_points if p["unsafe_acceptance_rate"] == 0.0]
    best_zero_unsafe = max(zero_unsafe_pts, key=lambda x: x["coverage"]) if zero_unsafe_pts else operating_points[-1]

    # 2. Balanced Profile (Recall >= 0.70 while minimizing unsafe accept)
    rec_70_pts = [p for p in operating_points if p["recall"] >= 0.70]
    best_balanced = min(rec_70_pts, key=lambda x: (x["unsafe_acceptance_rate"], -x["coverage"])) if rec_70_pts else operating_points[0]

    # 3. High-Coverage Profile (Coverage >= 0.60)
    cov_60_pts = [p for p in operating_points if p["coverage"] >= 0.60]
    best_high_cov = min(cov_60_pts, key=lambda x: (x["unsafe_acceptance_rate"], -x["recall"])) if cov_60_pts else operating_points[0]

    print("\n---------------------------------------------------------------------------------------------------------------------------------------")
    print(f"{'Profile':<25} | {'Tau':<6} | {'Coverage':<8} | {'Precision':<9} | {'Recall':<7} | {'UnsafeAcc':<9} | {'UnsupAcc':<9} | {'FalseRef':<8} | {'TP/FP/FN/TN'}")
    print("---------------------------------------------------------------------------------------------------------------------------------------")
    for name, p in [
        ("Zero-Unsafe (Cautious)", best_zero_unsafe),
        ("Balanced Operating Point", best_balanced),
        ("High-Coverage Point", best_high_cov),
    ]:
        c = p["confusion"]
        print(f"{name:<25} | {p['threshold']:<6.4f} | {p['coverage']*100:<7.1f}% | {p['precision']*100:<8.1f}% | {p['recall']*100:<6.1f}% | {p['unsafe_acceptance_rate']*100:<8.1f}% | {p['unsupported_acceptance_rate']*100:<8.1f}% | {p['false_refusal_rate']*100:<7.1f}% | {c['tp']}/{c['fp']}/{c['fn']}/{c['tn']}")

    # Save artifact
    out_payload = {
        "calibration_id": "medicalplab-evidence-sufficiency-recalibration-817-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "freshly_recomputed_on_817_chunk_corpus",
        "corpus": {
            "version": snapshot["version"],
            "snapshot_id": snapshot["corpus_id"],
            "document_count": snapshot["document_count"],
            "chunk_count": len(chunks),
        },
        "dataset": {
            "dataset_file": "evaluation/evidence_sufficiency_calibration_v1.json",
            "version": calib_data.get("version"),
            "dataset_note": "Reuses historical 48-case calibration set for comparability",
            "total_cases": n_total,
            "supported_cases": n_pos,
            "partial_cases": n_part,
            "unsupported_cases": n_unsup,
            "non_supported_cases": n_non_sup,
        },
        "retrieval_configuration": {
            "mode": retrieval_mode,
            "model": "Qwen/Qwen3-Embedding-0.6B",
            "device": device,
            "score_definition": "Cosine similarity of top-1 retrieved chunk embedding against instruction-formatted query embedding over 817 chunks",
        },
        "overall_calibration_performance": {
            "auroc": round(float(auroc), 4),
            "auprc": round(float(auprc), 4),
            "score_distributions": dist,
        },
        "operating_profiles": {
            "zero_unsafe_cautious": best_zero_unsafe,
            "balanced": best_balanced,
            "high_coverage": best_high_cov,
        },
        "all_operating_points": operating_points,
        "per_case_scores": case_results,
    }

    out_file = RESULTS_DIR / "evidence_sufficiency_recalibration_817_v1.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"\nSaved freshly recomputed calibration results to {out_file}")


if __name__ == "__main__":
    run_recalibration()
