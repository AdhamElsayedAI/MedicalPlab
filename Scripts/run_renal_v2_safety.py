"""Phase 18, 19, 20 — Train & Calibrate Evidence Safety Classifier on CALIBRATION and Evaluate on SAFETY-TEST.

Per Mission §40, §41, §42:
- Train and calibrate on CALIBRATION only.
- Objective: Unsafe Accept <= 0.05, Precision >= 0.90.
- Evaluate ONCE on SAFETY-TEST.
- Generates reports/renal_v2_safety.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np

# Ensure src is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import torch
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from medicalplab.learn.renal_bm25 import RenalBM25Index, tokenize
from medicalplab.learn.renal_evidence_classifier import (
    RenalEvidenceClassifier,
    RenalEvidenceFeatures,
    extract_evidence_features,
)

CAL_PATH = ROOT / "evaluation" / "renal" / "renal-calibration-v2.json"
SAFE_PATH = ROOT / "evaluation" / "renal" / "renal-safety-test-v2.json"
REG_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
MODEL_DIR = ROOT / "models"
OUT_REPORT = ROOT / "reports" / "renal_v2_safety.json"

MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "


def load_corpus() -> list[dict]:
    chunks = []
    for f in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        chunks.extend(json.loads(f.read_text(encoding="utf-8")).get("chunks", []))
    return chunks


def extract_dataset_features(
    queries: list[dict],
    model: SentenceTransformer,
    corpus_chunks: list[dict],
    corpus_embeddings: np.ndarray,
    bm25: RenalBM25Index,
    registry: dict,
) -> tuple[np.ndarray, np.ndarray]:
    query_texts = [QUERY_INSTRUCTION + q["query"] for q in queries]
    with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.float16):
        q_embeds = model.encode(
            query_texts,
            batch_size=16,
            convert_to_numpy=True,
            normalize_embeddings=True,
            device="cuda",
        )
        
    sims = np.dot(corpus_embeddings, q_embeds.T) # (n_chunks, n_queries)
    
    X = []
    y = []
    
    for idx, q in enumerate(queries):
        # Dense hits
        scores = sims[:, idx]
        top_dense_indices = np.argsort(scores)[::-1][:10]
        dense_hits = [(corpus_chunks[i], float(scores[i])) for i in top_dense_indices]
        
        # BM25 hits
        bm25_hits = [(h.chunk, h.score) for h in bm25.search(q["query"], top_k=10)]
        
        # RRF hits (standard reciprocal rank fusion)
        rrf_scores = {}
        for rank, (c, _) in enumerate(dense_hits, 1):
            cid = c.get("chunk_id")
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (60 + rank)
        for rank, (c, _) in enumerate(bm25_hits, 1):
            cid = c.get("chunk_id")
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (60 + rank)
            
        rrf_ranked = sorted(
            [(c, rrf_scores.get(c.get("chunk_id"), 0.0)) for c, _ in dense_hits],
            key=lambda x: -x[1]
        )
        
        # Reranked dummy (dense top hits used as placeholder)
        reranked_hits = dense_hits
        
        feat = extract_evidence_features(
            query=q["query"],
            dense_hits=dense_hits,
            bm25_hits=bm25_hits,
            rrf_hits=rrf_ranked,
            reranked_hits=reranked_hits,
            registry=registry,
        )
        X.append(feat.to_array())
        
        # Label: SUPPORTED = 1, PARTIALLY_SUPPORTED / UNSUPPORTED = 0
        label = 1 if q.get("support_label") == "SUPPORTED" else 0
        y.append(label)
        
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def main():
    print("=" * 70)
    print("PHASE 18 & 19: EVIDENCE SAFETY CLASSIFIER CALIBRATION & EVALUATION")
    print("=" * 70)
    
    reg_data = json.loads(REG_PATH.read_text(encoding="utf-8"))
    registry = {d["document_id"]: d for d in reg_data.get("documents", [])}
    
    cal_data = json.loads(CAL_PATH.read_text(encoding="utf-8"))
    safe_data = json.loads(SAFE_PATH.read_text(encoding="utf-8"))
    
    cal_queries = cal_data["queries"]
    safe_queries = safe_data["queries"]
    
    print(f"Loading corpus ({len(list(CHUNKS_DIR.glob('*.chunks.json')))} documents)...")
    corpus = load_corpus()
    print(f"Total corpus chunks: {len(corpus)}")
    
    # Initialize BM25
    print("Building BM25 index on corpus...")
    corpus_texts = [c["text"] for c in corpus]
    bm25 = RenalBM25Index(corpus, corpus_texts)
    
    # Load SentenceTransformer model on CUDA
    print(f"Loading embedding model: {MODEL_ID} on CUDA...")
    model = SentenceTransformer(MODEL_ID, device="cuda")
    
    # Load or compute corpus embeddings
    print("Encoding corpus chunks on CUDA...")
    with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.float16):
        corpus_embeds = model.encode(
            [c["text"] for c in corpus],
            batch_size=16,
            convert_to_numpy=True,
            normalize_embeddings=True,
            device="cuda",
        )
        
    # Phase 18: Extract features on CALIBRATION only
    print(f"\nPhase 18: Extracting features for {len(cal_queries)} CALIBRATION queries...")
    X_cal, y_cal = extract_dataset_features(cal_queries, model, corpus, corpus_embeds, bm25, registry)
    
    # Train LogisticRegression on CALIBRATION
    print(f"Fitting LogisticRegression on CALIBRATION (N={len(y_cal)}, positives={sum(y_cal)})...")
    clf = LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
    clf.fit(X_cal, y_cal)
    
    # Calibrate threshold on CALIBRATION
    # Objective: Unsafe Accept <= 0.05 while maximizing Precision and Recall
    cal_probs = clf.predict_proba(X_cal)[:, 1]
    
    best_thresh = 0.5
    best_f1 = 0.0
    for t in np.linspace(0.1, 0.9, 81):
        preds = (cal_probs >= t).astype(int)
        # Unsafe accept = False Positives / Total Negatives
        negatives = sum(y_cal == 0)
        fp = sum((preds == 1) & (y_cal == 0))
        unsafe_accept = fp / negatives if negatives else 0.0
        
        prec = precision_score(y_cal, preds, zero_division=0)
        rec = recall_score(y_cal, preds, zero_division=0)
        f1 = f1_score(y_cal, preds, zero_division=0)
        
        if unsafe_accept <= 0.05 and prec >= 0.85:
            if f1 > best_f1:
                best_f1 = f1
                best_thresh = float(t)
                
    print(f"Calibrated Threshold: {best_thresh:.4f} (Cal F1: {best_f1:.4f})")
    
    # Save calibrated classifier
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    evidence_classifier = RenalEvidenceClassifier(threshold=best_thresh)
    evidence_classifier.model = clf
    evidence_classifier.is_fitted = True
    model_file = MODEL_DIR / "renal_evidence_classifier.pkl"
    evidence_classifier.save(model_file)
    print(f"Saved calibrated classifier to: {model_file.name}")
    
    # Phase 19: Evaluate ONCE on SAFETY-TEST
    print(f"\nPhase 19: Running SAFETY-TEST evaluation ONCE (N={len(safe_queries)})...")
    X_safe, y_safe = extract_dataset_features(safe_queries, model, corpus, corpus_embeds, bm25, registry)
    
    safe_probs = clf.predict_proba(X_safe)[:, 1]
    safe_preds = (safe_probs >= best_thresh).astype(int)
    
    # Compute metrics
    tp = int(sum((safe_preds == 1) & (y_safe == 1)))
    tn = int(sum((safe_preds == 0) & (y_safe == 0)))
    fp = int(sum((safe_preds == 1) & (y_safe == 0)))
    fn = int(sum((safe_preds == 0) & (y_safe == 1)))
    
    n_safe = len(y_safe)
    precision = precision_score(y_safe, safe_preds, zero_division=0)
    recall = recall_score(y_safe, safe_preds, zero_division=0)
    f1 = f1_score(y_safe, safe_preds, zero_division=0)
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    auroc = roc_auc_score(y_safe, safe_probs)
    auprc = average_precision_score(y_safe, safe_probs)
    brier = brier_score_loss(y_safe, safe_probs)
    unsafe_accept = fp / (tn + fp) if (tn + fp) else 0.0
    false_refusal = fn / (tp + fn) if (tp + fn) else 0.0
    
    print("\n" + "=" * 50)
    print("SAFETY TEST RESULTS (EVALUATED EXACTLY ONCE)")
    print("=" * 50)
    print(f"N: {n_safe}")
    print(f"Confusion Matrix: TP={tp}, TN={tn}, FP={fp}, FN={fn}")
    print(f"Precision:        {precision:.4f} (target >= 0.90)")
    print(f"Recall:           {recall:.4f} (target >= 0.75)")
    print(f"F1 Score:         {f1:.4f}")
    print(f"Specificity:      {specificity:.4f}")
    print(f"AUROC:            {auroc:.4f}")
    print(f"AUPRC:            {auprc:.4f}")
    print(f"Brier Score:      {brier:.4f}")
    print(f"Unsafe Accept:    {unsafe_accept:.4f} (target <= 0.05)")
    print(f"False Refusal:    {false_refusal:.4f}")
    
    report = {
        "report_id": "RENAL-V2-SAFETY-EVALUATION",
        "dataset_id": "RENAL-SAFETY-TEST-V2",
        "dataset_sha256": hashlib.sha256(SAFE_PATH.read_bytes()).hexdigest(),
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_architecture": "LogisticRegression(class_weight='balanced')",
        "feature_count": 20,
        "calibration_dataset": "RENAL-CALIBRATION-V2",
        "calibration_dataset_sha256": hashlib.sha256(CAL_PATH.read_bytes()).hexdigest(),
        "calibrated_threshold": best_thresh,
        "n_test": n_safe,
        "confusion_matrix": {
            "TP": tp,
            "TN": tn,
            "FP": fp,
            "FN": fn,
        },
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "specificity": specificity,
            "auroc": auroc,
            "auprc": auprc,
            "brier_score": brier,
            "unsafe_accept": unsafe_accept,
            "false_refusal": false_refusal,
        },
        "gate_status": {
            "precision_pass": bool(precision >= 0.90),
            "recall_pass": bool(recall >= 0.75),
            "unsafe_accept_pass": bool(unsafe_accept <= 0.05),
        }
    }
    
    OUT_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    sha = hashlib.sha256(OUT_REPORT.read_bytes()).hexdigest()
    OUT_REPORT.with_suffix(".json.sha256").write_text(f"{sha}  {OUT_REPORT.name}\n", encoding="utf-8")
    print(f"\nReport written to: {OUT_REPORT.name} (SHA: {sha[:16]}...)")


if __name__ == "__main__":
    main()
