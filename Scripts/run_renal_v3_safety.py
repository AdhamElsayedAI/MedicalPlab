"""Phase 21, 22 & 23: Evidence Safety Classifier Redesign, Calibration & Single Test Execution.

Per Mission Section 36, 37, 38, 39:
- Build runtime-available features from frozen V3 retrieval (dense + doc prior + reranker).
- Fit and calibrate Logistic Regression strictly on CALIBRATION (N=66).
- Threshold calibrated to satisfy Unsafe Accept <= 0.05 while maximizing Recall and F1.
- Save model to models/renal_v3_evidence_classifier.pkl.
- Run SAFETY_TEST (N=66) exactly once.
- Persist reports/renal_v3/renal_v3_safety.json + SHA256 sidecar.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import pickle
import sys
import time
from pathlib import Path
import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, brier_score_loss

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from sentence_transformers import CrossEncoder
from transformers import AutoModel, AutoTokenizer

ROOT = _ROOT
CALIB_PATH = ROOT / "evaluation" / "renal" / "renal-calibration-v2.json"
SAFETY_TEST_PATH = ROOT / "evaluation" / "renal" / "renal-safety-test-v2.json"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
REPORTS_DIR = ROOT / "reports" / "renal_v3"
MODELS_DIR = ROOT / "models"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
EMBED_REVISION = "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode_texts(texts: list[str], tokenizer, model, device: torch.device, batch_size: int = 16) -> np.ndarray:
    all_embeddings = []
    with torch.inference_mode():
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            encoded = tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
            outputs = model(**encoded)
            mask = encoded["attention_mask"].unsqueeze(-1)
            emb = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            emb = torch.nn.functional.normalize(emb, p=2, dim=1)
            all_embeddings.append(emb.cpu().numpy())
    return np.vstack(all_embeddings).astype(np.float32)


def run_frozen_v3_retrieval(
    queries: list[dict],
    chunks: list[dict],
    corpus_arr: np.ndarray,
    doc_emb: np.ndarray,
    doc_ids_sorted: list[str],
    doc_id_to_idx: dict[str, int],
    embed_tok,
    embed_model,
    reranker: CrossEncoder,
    device: torch.device
) -> list[dict]:
    """Runs frozen V3 retrieval pipeline and extracts safety features."""
    q_texts = [q["query"] for q in queries]
    q_embs = encode_texts(q_texts, embed_tok, embed_model, device)
    
    # Dense sims
    sims_chunks = np.dot(q_embs, corpus_arr.T) # (n_q, n_chunks)
    sims_docs = np.dot(q_embs, doc_emb.T)       # (n_q, n_docs)
    
    alpha = 0.18
    n_q = len(queries)
    
    features_list = []
    
    for q_idx in range(n_q):
        q_text = q_texts[q_idx]
        p_scores = sims_chunks[q_idx].copy()
        d_scores = sims_docs[q_idx]
        
        # Dense + doc prior
        combined = np.zeros_like(p_scores)
        for i, ch in enumerate(chunks):
            did = ch["document_id"]
            combined[i] = p_scores[i] + alpha * d_scores[doc_id_to_idx[did]]
            
        top20_idx = np.argsort(combined)[::-1][:20]
        cands = [chunks[i] for i in top20_idx]
        
        dense_top1 = float(combined[top20_idx[0]])
        dense_top2 = float(combined[top20_idx[1]]) if len(top20_idx) > 1 else dense_top1
        dense_margin = dense_top1 - dense_top2
        
        doc_top1 = float(np.max(d_scores))
        doc_top2 = float(np.partition(d_scores, -2)[-2]) if len(d_scores) > 1 else doc_top1
        doc_margin = doc_top1 - doc_top2
        
        # Score top-20 with reranker
        pairs = [[q_text, c.get("text", "")] for c in cands]
        with torch.inference_mode():
            raw_rerank_scores = reranker.predict(pairs, batch_size=8, show_progress_bar=False)
        r_scores = np.asarray(raw_rerank_scores, dtype=np.float32).reshape(-1)
        r_order = np.argsort(r_scores)[::-1]
        
        r_sorted = r_scores[r_order]
        r_top1 = float(r_sorted[0])
        r_top2 = float(r_sorted[1]) if len(r_sorted) > 1 else r_top1
        r_margin = r_top1 - r_top2
        r_top3_mean = float(np.mean(r_sorted[:3]))
        
        # Candidate agreement: fraction of top-5 sharing top document
        top_docs = [cands[r_order[i]]["document_id"] for i in range(min(5, len(r_order)))]
        top_doc_mode = max(set(top_docs), key=top_docs.count)
        doc_agreement = top_docs.count(top_doc_mode) / len(top_docs)
        
        # Softmax entropy over top 5
        exp_s = np.exp(r_sorted[:5] - np.max(r_sorted[:5]))
        probs = exp_s / np.sum(exp_s)
        entropy = -float(np.sum(probs * np.log(probs + 1e-12)))
        
        feat = [
            r_top1,
            r_top2,
            r_margin,
            r_top3_mean,
            dense_top1,
            dense_margin,
            doc_top1,
            doc_margin,
            doc_agreement,
            entropy
        ]
        
        features_list.append({
            "query_id": queries[q_idx].get("query_id"),
            "answerable": bool(queries[q_idx].get("answerable", False)),
            "features": feat
        })
        
    return features_list


def main():
    print("=" * 70)
    print("PHASE 21, 22, 23: V3 EVIDENCE SAFETY CLASSIFIER REDESIGN")
    print("=" * 70)
    
    if not torch.cuda.is_available():
        print("HARD GATE FAILED: CUDA not available.")
        sys.exit(1)
        
    device = torch.device("cuda:0")
    print(f"Device: {torch.cuda.get_device_name(0)}")
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Registry, Chunks, and Embeddings
    reg_data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    chunks = []
    doc_to_chunks = {}
    for f in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        did = f.name.replace(".chunks.json", "")
        # Use full 23 active documents for production runtime safety!
        data = json.loads(f.read_text(encoding="utf-8"))
        for ch in data.get("chunks", []):
            chunks.append(ch)
            doc_to_chunks.setdefault(did, []).append(len(chunks) - 1)
            
    doc_ids_sorted = sorted(list(doc_to_chunks.keys()))
    doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
    
    # Load models
    print(f"Loading embedding model: {EMBED_MODEL_ID}...")
    embed_tok = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, revision=EMBED_REVISION, trust_remote_code=True)
    embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, revision=EMBED_REVISION, trust_remote_code=True, torch_dtype=torch.float16).to(device).eval()
    
    print(f"Loading reranker model: {RERANK_MODEL_ID}...")
    reranker = CrossEncoder(RERANK_MODEL_ID, trust_remote_code=True, device="cuda:0")
    
    # Compute or load doc embeddings for all 23 documents
    doc_cache_path = CACHE_DIR / "all23_doc_embeddings.npy"
    if doc_cache_path.exists():
        doc_emb = np.load(doc_cache_path)
    else:
        doc_titles = {d["document_id"]: d.get("title", "") for d in reg_data.get("documents", [])}
        doc_topics = {d["document_id"]: ", ".join(d.get("topic_tags", [])) for d in reg_data.get("documents", [])}
        doc_texts = [f"Title: {doc_titles.get(did, '')}\nTopics: {doc_topics.get(did, '')}\nOverview: {chunks[doc_to_chunks[did][0]]['text'][:300]}" for did in doc_ids_sorted]
        doc_emb = encode_texts(doc_texts, embed_tok, embed_model, device)
        np.save(doc_cache_path, doc_emb)
        
    # Load or compute corpus embeddings for all 23 documents
    corpus_cache_path = CACHE_DIR / "all23_corpus_embeddings.npy"
    if corpus_cache_path.exists():
        corpus_arr = np.load(corpus_cache_path)
    else:
        print(f"Encoding {len(chunks)} chunks across all 23 documents...")
        all_chunk_texts = [ch["text"] for ch in chunks]
        corpus_arr = encode_texts(all_chunk_texts, embed_tok, embed_model, device)
        np.save(corpus_cache_path, corpus_arr)
        
    print(f"Corpus shape: {corpus_arr.shape}, Doc emb shape: {doc_emb.shape}")
    
    # 2. PHASE 21: Extract features on CALIBRATION (N=66)
    print("\n" + "=" * 60)
    print("PHASE 21: EXTRACTING FEATURES ON CALIBRATION (N=66)")
    print("=" * 60)
    calib_data = json.loads(CALIB_PATH.read_text(encoding="utf-8"))
    calib_queries = calib_data["queries"]
    print(f"Loaded {len(calib_queries)} queries from CALIBRATION (Answerable: {sum(1 for q in calib_queries if q.get('answerable'))}, Unsupported: {sum(1 for q in calib_queries if not q.get('answerable'))})")
    
    calib_feats = run_frozen_v3_retrieval(
        calib_queries, chunks, corpus_arr, doc_emb, doc_ids_sorted, doc_id_to_idx, embed_tok, embed_model, reranker, device
    )
    
    X_calib = np.array([f["features"] for f in calib_feats], dtype=np.float32)
    y_calib = np.array([1 if f["answerable"] else 0 for f in calib_feats], dtype=np.int32)
    
    feature_names = [
        "reranker_top1", "reranker_top2", "reranker_margin", "reranker_top3_mean",
        "dense_top1", "dense_margin", "doc_top1", "doc_margin",
        "doc_agreement", "entropy"
    ]
    
    # Standardize features using CALIBRATION statistics
    means = np.mean(X_calib, axis=0)
    stds = np.std(X_calib, axis=0)
    stds[stds == 0] = 1.0
    
    X_calib_norm = (X_calib - means) / stds
    
    # Fit Logistic Regression on CALIBRATION
    safety_model = LogisticRegression(C=0.5, max_iter=300, random_state=42)
    safety_model.fit(X_calib_norm, y_calib)
    
    probs_calib = safety_model.predict_proba(X_calib_norm)[:, 1]
    
    # Calibrate decision threshold tau on CALIBRATION to satisfy Unsafe Accept <= 0.05
    # Unsafe Accept = FP / Total Negatives
    best_tau = 0.5
    best_recall = 0.0
    best_f1 = 0.0
    
    n_neg_calib = int(np.sum(y_calib == 0))
    print(f"Calibrating threshold across CALIBRATION (N_pos={np.sum(y_calib == 1)}, N_neg={n_neg_calib}):")
    
    for tau in np.linspace(0.1, 0.95, 171):
        preds = (probs_calib >= tau).astype(int)
        fp = int(np.sum((preds == 1) & (y_calib == 0)))
        tp = int(np.sum((preds == 1) & (y_calib == 1)))
        fn = int(np.sum((preds == 0) & (y_calib == 1)))
        
        unsafe_accept = fp / n_neg_calib if n_neg_calib > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = 2 * prec * recall / (prec + recall) if (prec + recall) > 0 else 0.0
        
        if unsafe_accept <= 0.05:
            if recall > best_recall or (recall == best_recall and f1 > best_f1):
                best_tau = float(tau)
                best_recall = float(recall)
                best_f1 = float(f1)
                
    print(f"Selected calibrated threshold tau = {best_tau:.4f} (CALIB: Recall={best_recall:.4f}, F1={best_f1:.4f})")
    
    # Save frozen safety classifier model & schema
    model_payload = {
        "model": safety_model,
        "feature_names": feature_names,
        "means": means,
        "stds": stds,
        "calibrated_threshold": best_tau,
        "training_dataset": "renal-calibration-v2.json",
        "frozen_timestamp": time.time()
    }
    model_path = MODELS_DIR / "renal_v3_evidence_classifier.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model_payload, f)
    print(f"Saved frozen safety classifier to {model_path}")
    
    # 3. PHASE 22: EVALUATE SAFETY_TEST (N=66) EXACTLY ONCE
    print("\n" + "=" * 60)
    print("PHASE 22: RUNNING UNTOUCHED SAFETY_TEST (N=66) EXACTLY ONCE")
    print("=" * 60)
    
    safety_test_data = json.loads(SAFETY_TEST_PATH.read_text(encoding="utf-8"))
    safety_queries = safety_test_data["queries"]
    print(f"Loaded {len(safety_queries)} queries from SAFETY_TEST.")
    
    safety_feats = run_frozen_v3_retrieval(
        safety_queries, chunks, corpus_arr, doc_emb, doc_ids_sorted, doc_id_to_idx, embed_tok, embed_model, reranker, device
    )
    
    X_test = np.array([f["features"] for f in safety_feats], dtype=np.float32)
    y_test = np.array([1 if f["answerable"] else 0 for f in safety_feats], dtype=np.int32)
    
    # Apply frozen normalization & model
    X_test_norm = (X_test - means) / stds
    probs_test = safety_model.predict_proba(X_test_norm)[:, 1]
    preds_test = (probs_test >= best_tau).astype(int)
    
    # Metrics
    tp = int(np.sum((preds_test == 1) & (y_test == 1)))
    fp = int(np.sum((preds_test == 1) & (y_test == 0)))
    tn = int(np.sum((preds_test == 0) & (y_test == 0)))
    fn = int(np.sum((preds_test == 0) & (y_test == 1)))
    
    n_pos = int(np.sum(y_test == 1))
    n_neg = int(np.sum(y_test == 0))
    n_total = len(y_test)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    unsafe_accept = fp / n_neg if n_neg > 0 else 0.0
    false_refusal = fn / n_pos if n_pos > 0 else 0.0
    
    auroc = float(roc_auc_score(y_test, probs_test))
    prec_curve, rec_curve, _ = precision_recall_curve(y_test, probs_test)
    auprc = float(auc(rec_curve, prec_curve))
    brier = float(brier_score_loss(y_test, probs_test))
    
    print("\n" + "=" * 70)
    print("V3 SAFETY_TEST EVALUATION RESULTS (N=66, UNTOUCHED SINGLE RUN)")
    print("=" * 70)
    print(f"Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn} (Total N={n_total})")
    print(f"  Precision:       {precision:.4f} ({tp}/{tp+fp})")
    print(f"  Recall:          {recall:.4f} ({tp}/{n_pos})")
    print(f"  Specificity:     {specificity:.4f} ({tn}/{n_neg})")
    print(f"  F1 Score:        {f1:.4f}")
    print(f"  AUROC:           {auroc:.4f}")
    print(f"  AUPRC:           {auprc:.4f}")
    print(f"  Brier Score:     {brier:.4f}")
    print(f"  Unsafe Accept:   {unsafe_accept:.4f} ({fp}/{n_neg}) -> {'PASSED (<= 0.05)' if unsafe_accept <= 0.05 else 'FAILED'}")
    print(f"  False Refusal:   {false_refusal:.4f} ({fn}/{n_pos})")
    print("=" * 70)
    
    # 4. PHASE 23: Persist Safety Report & Hash
    safety_report_payload = {
        "report_id": "RENAL-V3-SAFETY-EVALUATION",
        "description": "V3 Evidence Safety Classifier single evaluation on SAFETY_TEST",
        "test_dataset": "renal-safety-test-v2.json",
        "test_dataset_sha256": sha256_file(SAFETY_TEST_PATH),
        "calibration_dataset": "renal-calibration-v2.json",
        "calibrated_threshold": best_tau,
        "n_samples": n_total,
        "n_positive": n_pos,
        "n_negative": n_neg,
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "metrics": {
            "precision": precision,
            "recall": recall,
            "specificity": specificity,
            "f1": f1,
            "auroc": auroc,
            "auprc": auprc,
            "brier_score": brier,
            "unsafe_accept_rate": unsafe_accept,
            "false_refusal_rate": false_refusal
        },
        "gate_status": "PASSED" if unsafe_accept <= 0.05 else "FAILED",
        "features": feature_names,
        "model_file": "models/renal_v3_evidence_classifier.pkl"
    }
    
    report_out = REPORTS_DIR / "renal_v3_safety.json"
    report_out.write_text(json.dumps(safety_report_payload, indent=2), encoding="utf-8")
    
    sha = sha256_file(report_out)
    sha_path = report_out.with_suffix(".json.sha256")
    sha_path.write_text(f"{sha}  {report_out.name}\n", encoding="utf-8")
    
    print(f"Wrote safety report: {report_out}")
    print(f"SHA256: {sha}")


if __name__ == "__main__":
    main()
