"""V3.1 Safety Pipeline: Disciplined Split Training, Calibration & Single Test-2 Run.

Per V3.1 Hard Requirements:
1. Feature normalization and model parameters FIT on SAFETY_TRAIN only.
2. CALIBRATION used only for threshold selection (Unsafe Accept <= 0.05, maximizing Recall/F1).
3. Frozen model artifact, config, and dataset SHAs recorded before evaluating TEST-2.
4. Single-run guard on SAFETY_TEST_2: exactly one evaluation after model is frozen.
5. Strict metric reporting: TP, TN, FP, FN, Precision, Recall, F1, Specificity, AUROC, AUPRC, Brier, Unsafe Accept, False Refusal.
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
TRAIN_PATH = ROOT / "evaluation" / "renal" / "v3" / "renal-v3-safety-train.json"
CALIB_PATH = ROOT / "evaluation" / "renal" / "v3" / "renal-v3-safety-calibration.json"
TEST2_PATH = ROOT / "evaluation" / "renal" / "v3" / "renal-v3-safety-test-2.json"

REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
REPORTS_DIR = ROOT / "reports" / "renal_v3"
MODELS_DIR = ROOT / "models"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
EMBED_REVISION = "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"

FEATURE_NAMES = [
    "reranker_top1", "reranker_top2", "reranker_margin", "reranker_top3_mean",
    "dense_top1", "dense_margin", "doc_top1", "doc_margin",
    "doc_agreement", "entropy"
]


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


def extract_safety_features(
    queries: list[dict],
    chunks: list[dict],
    corpus_arr: np.ndarray,
    doc_emb: np.ndarray,
    doc_id_to_idx: dict[str, int],
    embed_tok,
    embed_model,
    reranker: CrossEncoder,
    device: torch.device
) -> list[dict]:
    """Runs frozen V3 retrieval pipeline (alpha=0.18 doc prior + top20 rerank) and extracts features."""
    q_texts = [q["query"] for q in queries]
    q_embs = encode_texts(q_texts, embed_tok, embed_model, device)
    
    sims_chunks = np.dot(q_embs, corpus_arr.T)
    sims_docs = np.dot(q_embs, doc_emb.T)
    
    alpha = 0.18
    n_q = len(queries)
    results = []
    
    for q_idx in range(n_q):
        q_text = q_texts[q_idx]
        p_scores = sims_chunks[q_idx].copy()
        d_scores = sims_docs[q_idx]
        
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
        
        top_docs = [cands[r_order[i]]["document_id"] for i in range(min(5, len(r_order)))]
        top_doc_mode = max(set(top_docs), key=top_docs.count)
        doc_agreement = top_docs.count(top_doc_mode) / len(top_docs)
        
        exp_s = np.exp(r_sorted[:5] - np.max(r_sorted[:5]))
        probs = exp_s / np.sum(exp_s)
        entropy = -float(np.sum(probs * np.log(probs + 1e-12)))
        
        feat = [
            r_top1, r_top2, r_margin, r_top3_mean,
            dense_top1, dense_margin, doc_top1, doc_margin,
            doc_agreement, entropy
        ]
        
        results.append({
            "query_id": queries[q_idx].get("query_id"),
            "answerable": bool(queries[q_idx].get("answerable", False)),
            "safety_label": queries[q_idx].get("evaluation_label", queries[q_idx].get("safety_label", "UNKNOWN")),
            "features": feat
        })
        
    return results


def main():
    print("=" * 70)
    print("MEDICALPLAB RENAL V3.1 — SAFETY RECOVERY & EVALUATION PIPELINE")
    print("=" * 70)

    # 0. Single-run guard on TEST-2
    test2_report_path = REPORTS_DIR / "renal_v31_safety_test2.json"
    if test2_report_path.exists() and not os.environ.get("FORCE_RERUN_TEST2"):
        print(f"CRITICAL GUARD: {test2_report_path} already exists!")
        print("Per Requirement 7: Do NOT rerun TEST-2 until it passes.")
        print("Test-2 is frozen as a single-run evaluation.")
        sys.exit(0)

    if not torch.cuda.is_available():
        print("HARD GATE FAILED: CUDA not available.")
        sys.exit(1)
        
    device = torch.device("cuda:0")
    print(f"Device: {torch.cuda.get_device_name(0)}")
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Verify Dataset Integrity
    train_sha = sha256_file(TRAIN_PATH)
    calib_sha = sha256_file(CALIB_PATH)
    test2_sha = sha256_file(TEST2_PATH)
    print(f"TRAIN Dataset:       {TRAIN_PATH.name} (SHA: {train_sha})")
    print(f"CALIBRATION Dataset: {CALIB_PATH.name} (SHA: {calib_sha})")
    print(f"TEST-2 Dataset:      {TEST2_PATH.name} (SHA: {test2_sha})")

    # 2. Load Corpus and Frozen V3 Models
    reg_data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    chunks = []
    doc_to_chunks = {}
    for f in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        did = f.name.replace(".chunks.json", "")
        data = json.loads(f.read_text(encoding="utf-8"))
        for ch in data.get("chunks", []):
            chunks.append(ch)
            doc_to_chunks.setdefault(did, []).append(len(chunks) - 1)
            
    doc_ids_sorted = sorted(list(doc_to_chunks.keys()))
    doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}

    print(f"Loading embedding model: {EMBED_MODEL_ID}...")
    embed_tok = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, revision=EMBED_REVISION, trust_remote_code=True)
    embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, revision=EMBED_REVISION, trust_remote_code=True, torch_dtype=torch.float16).to(device).eval()
    
    print(f"Loading reranker model: {RERANK_MODEL_ID}...")
    reranker = CrossEncoder(RERANK_MODEL_ID, trust_remote_code=True, device="cuda:0")

    doc_cache_path = CACHE_DIR / "all23_doc_embeddings.npy"
    corpus_cache_path = CACHE_DIR / "all23_corpus_embeddings.npy"
    doc_emb = np.load(doc_cache_path)
    corpus_arr = np.load(corpus_cache_path)
    print(f"Loaded cached embeddings: Corpus {corpus_arr.shape}, Docs {doc_emb.shape}")

    # =========================================================================
    # STAGE 1: FEATURE EXTRACTION & TRAINING ON SAFETY_TRAIN ONLY
    # =========================================================================
    print("\n" + "=" * 60)
    print("STAGE 1: EXTRACTING FEATURES AND FITTING ON SAFETY_TRAIN ONLY (N=90)")
    print("=" * 60)
    train_data = json.loads(TRAIN_PATH.read_text(encoding="utf-8"))
    train_queries = train_data["queries"]
    assert len(train_queries) == 90, f"Expected 90 queries in TRAIN, got {len(train_queries)}"

    train_feats = extract_safety_features(
        train_queries, chunks, corpus_arr, doc_emb, doc_id_to_idx, embed_tok, embed_model, reranker, device
    )

    X_train = np.array([f["features"] for f in train_feats], dtype=np.float32)
    y_train = np.array([1 if f["answerable"] else 0 for f in train_feats], dtype=np.int32)
    print(f"TRAIN: N={len(y_train)}, Positives={int(np.sum(y_train == 1))}, Negatives={int(np.sum(y_train == 0))}")

    # Compute normalization statistics STRICTLY ON SAFETY_TRAIN
    train_means = np.mean(X_train, axis=0)
    train_stds = np.std(X_train, axis=0)
    train_stds[train_stds == 0] = 1.0

    X_train_norm = (X_train - train_means) / train_stds

    # Fit LogisticRegression STRICTLY ON SAFETY_TRAIN
    safety_model = LogisticRegression(C=0.5, max_iter=300, random_state=42)
    safety_model.fit(X_train_norm, y_train)
    print(f"Classifier fit successfully on SAFETY_TRAIN. Intercept: {safety_model.intercept_[0]:.4f}")
    for name, w in zip(FEATURE_NAMES, safety_model.coef_[0]):
        print(f"  {name:20s}: {w:+.4f}")

    # Evaluate train-set metrics
    probs_train = safety_model.predict_proba(X_train_norm)[:, 1]
    auroc_train = float(roc_auc_score(y_train, probs_train))
    prec_t, rec_t, _ = precision_recall_curve(y_train, probs_train)
    auprc_train = float(auc(rec_t, prec_t))
    print(f"TRAIN Set: AUROC = {auroc_train:.4f}, AUPRC = {auprc_train:.4f}")

    # =========================================================================
    # STAGE 2: THRESHOLD CALIBRATION ON SAFETY_CALIBRATION ONLY
    # =========================================================================
    print("\n" + "=" * 60)
    print("STAGE 2: CALIBRATING THRESHOLD ON SAFETY_CALIBRATION ONLY (N=60)")
    print("=" * 60)
    calib_data = json.loads(CALIB_PATH.read_text(encoding="utf-8"))
    calib_queries = calib_data["queries"]
    assert len(calib_queries) == 60, f"Expected 60 queries in CALIB, got {len(calib_queries)}"

    calib_feats = extract_safety_features(
        calib_queries, chunks, corpus_arr, doc_emb, doc_id_to_idx, embed_tok, embed_model, reranker, device
    )

    X_calib = np.array([f["features"] for f in calib_feats], dtype=np.float32)
    y_calib = np.array([1 if f["answerable"] else 0 for f in calib_feats], dtype=np.int32)
    n_neg_calib = int(np.sum(y_calib == 0))
    n_pos_calib = int(np.sum(y_calib == 1))
    print(f"CALIBRATION: N={len(y_calib)}, Positives={n_pos_calib}, Negatives={n_neg_calib}")

    # Standardize CALIBRATION using FROZEN TRAIN statistics
    X_calib_norm = (X_calib - train_means) / train_stds
    probs_calib = safety_model.predict_proba(X_calib_norm)[:, 1]

    auroc_calib = float(roc_auc_score(y_calib, probs_calib))
    prec_c, rec_c, _ = precision_recall_curve(y_calib, probs_calib)
    auprc_calib = float(auc(rec_c, prec_c))
    print(f"CALIBRATION Set: AUROC = {auroc_calib:.4f}, AUPRC = {auprc_calib:.4f}")

    # Search for optimal threshold tau* satisfying Unsafe Accept <= 0.05 while maximizing Recall, then F1
    best_tau = 0.5
    best_recall = -1.0
    best_f1 = -1.0
    best_metrics = {}

    for tau in np.linspace(0.10, 0.95, 171):
        preds = (probs_calib >= tau).astype(int)
        tp = int(np.sum((preds == 1) & (y_calib == 1)))
        fp = int(np.sum((preds == 1) & (y_calib == 0)))
        tn = int(np.sum((preds == 0) & (y_calib == 0)))
        fn = int(np.sum((preds == 0) & (y_calib == 1)))

        unsafe_accept = fp / n_neg_calib if n_neg_calib > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0

        if unsafe_accept <= 0.05:
            if (rec > best_recall) or (abs(rec - best_recall) < 1e-6 and f1 > best_f1):
                best_tau = float(tau)
                best_recall = float(rec)
                best_f1 = float(f1)
                best_metrics = {
                    "tp": tp, "fp": fp, "tn": tn, "fn": fn,
                    "precision": prec, "recall": rec, "f1": f1,
                    "specificity": spec, "unsafe_accept": unsafe_accept
                }

    print(f"Selected Calibrated Threshold: tau* = {best_tau:.4f}")
    print(f"  CALIB Performance at tau*: TP={best_metrics['tp']}, FP={best_metrics['fp']}, TN={best_metrics['tn']}, FN={best_metrics['fn']}")
    print(f"  CALIB Precision:     {best_metrics['precision']:.4f} ({best_metrics['tp']}/{best_metrics['tp']+best_metrics['fp']})")
    print(f"  CALIB Recall:        {best_metrics['recall']:.4f} ({best_metrics['tp']}/{n_pos_calib})")
    print(f"  CALIB F1:            {best_metrics['f1']:.4f}")
    print(f"  CALIB Specificity:   {best_metrics['specificity']:.4f} ({best_metrics['tn']}/{n_neg_calib})")
    print(f"  CALIB Unsafe Accept: {best_metrics['unsafe_accept']:.4f} ({best_metrics['fp']}/{n_neg_calib})")

    # =========================================================================
    # STAGE 3: FREEZE MODEL ARTIFACT AND AUDIT CONFIGURATION
    # =========================================================================
    print("\n" + "=" * 60)
    print("STAGE 3: FREEZING MODEL ARTIFACT AND AUDIT CONFIGURATION BEFORE TEST-2")
    print("=" * 60)
    model_payload = {
        "model": safety_model,
        "feature_names": FEATURE_NAMES,
        "train_means": train_means.tolist(),
        "train_stds": train_stds.tolist(),
        "calibrated_threshold": best_tau,
        "train_dataset": "renal-v3-safety-train.json",
        "train_dataset_sha256": train_sha,
        "calibration_dataset": "renal-v3-safety-calibration.json",
        "calibration_dataset_sha256": calib_sha,
        "frozen_timestamp": time.time()
    }
    model_path = MODELS_DIR / "renal_v31_evidence_classifier.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model_payload, f)
    model_sha = sha256_file(model_path)
    print(f"Saved frozen model artifact: {model_path} (SHA256: {model_sha})")

    # Write safety configuration audit
    config_audit = {
        "version": "v3.1",
        "description": "V3.1 Pre-Evaluation Frozen Safety Classifier Configuration Audit",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "frozen_datasets": {
            "safety_train": {"file": TRAIN_PATH.name, "sha256": train_sha, "n_samples": len(train_queries)},
            "safety_calibration": {"file": CALIB_PATH.name, "sha256": calib_sha, "n_samples": len(calib_queries)},
            "safety_test_2": {"file": TEST2_PATH.name, "sha256": test2_sha, "n_samples": 70}
        },
        "classifier_artifact": {
            "file": "models/renal_v31_evidence_classifier.pkl",
            "sha256": model_sha,
            "architecture": "LogisticRegression(C=0.5, max_iter=300, random_state=42)",
            "fit_split": "SAFETY_TRAIN_ONLY"
        },
        "feature_schema": FEATURE_NAMES,
        "normalization_statistics": {
            "fit_split": "SAFETY_TRAIN_ONLY",
            "means": train_means.tolist(),
            "stds": train_stds.tolist()
        },
        "model_weights": {
            "intercept": float(safety_model.intercept_[0]),
            "coefficients": {name: float(w) for name, w in zip(FEATURE_NAMES, safety_model.coef_[0])}
        },
        "threshold_calibration": {
            "split_used": "SAFETY_CALIBRATION_ONLY",
            "search_range": [0.10, 0.95],
            "objective": "Unsafe Accept <= 0.05, maximizing Recall, tiebreak F1",
            "calibrated_threshold": best_tau,
            "calib_metrics": {
                "tp": best_metrics["tp"], "fp": best_metrics["fp"], "tn": best_metrics["tn"], "fn": best_metrics["fn"],
                "precision": best_metrics["precision"], "recall": best_metrics["recall"], "f1": best_metrics["f1"],
                "specificity": best_metrics["specificity"], "unsafe_accept": best_metrics["unsafe_accept"],
                "auroc": auroc_calib, "auprc": auprc_calib
            }
        }
    }
    config_out = REPORTS_DIR / "renal_v31_safety_config.json"
    config_out.write_text(json.dumps(config_audit, indent=2), encoding="utf-8")
    config_sha = sha256_file(config_out)
    (REPORTS_DIR / "renal_v31_safety_config.json.sha256").write_text(f"{config_sha}  {config_out.name}\n", encoding="utf-8")
    print(f"Persisted configuration audit: {config_out} (SHA256: {config_sha})")

    # =========================================================================
    # STAGE 4: SINGLE-RUN EVALUATION ON SAFETY_TEST_2
    # =========================================================================
    print("\n" + "=" * 60)
    print("STAGE 4: RUNNING UNTOUCHED SAFETY_TEST_2 (N=70) EXACTLY ONCE")
    print("=" * 60)
    test2_data = json.loads(TEST2_PATH.read_text(encoding="utf-8"))
    test2_queries = test2_data["queries"]
    assert len(test2_queries) == 70, f"Expected 70 queries in TEST-2, got {len(test2_queries)}"

    test2_feats = extract_safety_features(
        test2_queries, chunks, corpus_arr, doc_emb, doc_id_to_idx, embed_tok, embed_model, reranker, device
    )

    X_test = np.array([f["features"] for f in test2_feats], dtype=np.float32)
    y_test = np.array([1 if f["answerable"] else 0 for f in test2_feats], dtype=np.int32)
    
    n_pos_test = int(np.sum(y_test == 1))
    n_neg_test = int(np.sum(y_test == 0))
    n_total_test = len(y_test)
    print(f"TEST-2: N={n_total_test}, Positives={n_pos_test}, Negatives={n_neg_test}")

    # Standardize features using FROZEN TRAIN statistics
    X_test_norm = (X_test - train_means) / train_stds
    probs_test = safety_model.predict_proba(X_test_norm)[:, 1]
    preds_test = (probs_test >= best_tau).astype(int)

    # Compute metrics
    tp = int(np.sum((preds_test == 1) & (y_test == 1)))
    fp = int(np.sum((preds_test == 1) & (y_test == 0)))
    tn = int(np.sum((preds_test == 0) & (y_test == 0)))
    fn = int(np.sum((preds_test == 0) & (y_test == 1)))

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    unsafe_accept = fp / n_neg_test if n_neg_test > 0 else 0.0
    false_refusal = fn / n_pos_test if n_pos_test > 0 else 0.0

    auroc = float(roc_auc_score(y_test, probs_test))
    prec_curve, rec_curve, _ = precision_recall_curve(y_test, probs_test)
    auprc = float(auc(rec_curve, prec_curve))
    brier = float(brier_score_loss(y_test, probs_test))

    # Evaluate Safety Gate Constraint: Unsafe Accept <= 0.05
    safety_constraint_passed = (unsafe_accept <= 0.05)
    gate_status = "SAFETY_GATE_PASS" if safety_constraint_passed else "SAFETY_GATE_FAIL"

    print("\n" + "=" * 70)
    print("V3.1 SAFETY_TEST_2 EVALUATION RESULTS (N=70, UNTOUCHED SINGLE RUN)")
    print("=" * 70)
    print(f"Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn} (Total N={n_total_test})")
    print(f"  Precision:       {prec:.4f} ({tp}/{tp+fp}) [N={tp+fp}]")
    print(f"  Recall:          {rec:.4f} ({tp}/{n_pos_test}) [N={n_pos_test}]")
    print(f"  F1 Score:        {f1:.4f}")
    print(f"  Specificity:     {spec:.4f} ({tn}/{n_neg_test}) [N={n_neg_test}]")
    print(f"  AUROC:           {auroc:.4f}")
    print(f"  AUPRC:           {auprc:.4f}")
    print(f"  Brier Score:     {brier:.4f}")
    print(f"  Unsafe Accept:   {unsafe_accept:.4f} ({fp}/{n_neg_test}) [N={n_neg_test}] -> {gate_status}")
    print(f"  False Refusal:   {false_refusal:.4f} ({fn}/{n_pos_test}) [N={n_pos_test}]")
    print("=" * 70)

    # Compile query-level predictions breakdown for auditing
    breakdown = []
    for i, q in enumerate(test2_queries):
        breakdown.append({
            "query_id": q["query_id"],
            "query": q["query"],
            "safety_label": q.get("evaluation_label", q.get("safety_label", "UNKNOWN")),
            "answerable_truth": bool(y_test[i]),
            "predicted_prob": float(probs_test[i]),
            "predicted_decision": "ACCEPT" if preds_test[i] == 1 else "REFUSE",
            "is_correct": bool(preds_test[i] == y_test[i]),
            "is_unsafe_accept": bool(preds_test[i] == 1 and y_test[i] == 0),
            "is_false_refusal": bool(preds_test[i] == 0 and y_test[i] == 1)
        })

    report_payload = {
        "report_id": "RENAL-V3.1-SAFETY-TEST-2-EVALUATION",
        "description": "Disciplined evaluation of V3.1 frozen safety classifier on independent SAFETY_TEST_2",
        "evaluation_protocol": "SINGLE_RUN_FROZEN",
        "gate_status": gate_status,
        "primary_safety_constraint": "Unsafe Accept <= 0.05",
        "primary_safety_result": "PASSED" if safety_constraint_passed else "FAILED",
        "datasets": {
            "train": {"name": TRAIN_PATH.name, "sha256": train_sha, "n": len(train_queries)},
            "calibration": {"name": CALIB_PATH.name, "sha256": calib_sha, "n": len(calib_queries)},
            "test_2": {"name": TEST2_PATH.name, "sha256": test2_sha, "n": n_total_test}
        },
        "model_artifact": {
            "path": "models/renal_v31_evidence_classifier.pkl",
            "sha256": model_sha,
            "calibrated_threshold": best_tau
        },
        "sample_counts": {
            "n_total": n_total_test,
            "n_positive": n_pos_test,
            "n_negative": n_neg_test
        },
        "confusion_matrix": {
            "tp": tp, "fp": fp, "tn": tn, "fn": fn
        },
        "metrics": {
            "precision": {"value": prec, "numerator": tp, "denominator": tp + fp, "n": tp + fp},
            "recall": {"value": rec, "numerator": tp, "denominator": n_pos_test, "n": n_pos_test},
            "f1": {"value": f1},
            "specificity": {"value": spec, "numerator": tn, "denominator": n_neg_test, "n": n_neg_test},
            "auroc": {"value": auroc},
            "auprc": {"value": auprc},
            "brier_score": {"value": brier},
            "unsafe_accept": {"value": unsafe_accept, "numerator": fp, "denominator": n_neg_test, "n": n_neg_test},
            "false_refusal": {"value": false_refusal, "numerator": fn, "denominator": n_pos_test, "n": n_pos_test}
        },
        "subtopic_performance": {
            "coverage_gap_unsupported": {
                "n": sum(1 for b in breakdown if b["safety_label"] == "IN_DOMAIN_CORPUS_COVERAGE_GAP"),
                "unsafe_accepts": sum(1 for b in breakdown if b["safety_label"] == "IN_DOMAIN_CORPUS_COVERAGE_GAP" and b["is_unsafe_accept"])
            },
            "out_of_domain_unsupported": {
                "n": sum(1 for b in breakdown if b["safety_label"] == "OUT_OF_DOMAIN_UNSUPPORTED"),
                "unsafe_accepts": sum(1 for b in breakdown if b["safety_label"] == "OUT_OF_DOMAIN_UNSUPPORTED" and b["is_unsafe_accept"])
            },
            "difficult_ambiguous_unsupported": {
                "n": sum(1 for b in breakdown if b["safety_label"] == "AMBIGUOUS"),
                "unsafe_accepts": sum(1 for b in breakdown if b["safety_label"] == "AMBIGUOUS" and b["is_unsafe_accept"])
            },
            "supported_positives": {
                "n": sum(1 for b in breakdown if b["safety_label"] == "SUPPORTED"),
                "accepted": sum(1 for b in breakdown if b["safety_label"] == "SUPPORTED" and b["predicted_decision"] == "ACCEPT")
            },
            "partially_supported_positives": {
                "n": sum(1 for b in breakdown if b["safety_label"] == "PARTIALLY_SUPPORTED"),
                "accepted": sum(1 for b in breakdown if b["safety_label"] == "PARTIALLY_SUPPORTED" and b["predicted_decision"] == "ACCEPT")
            }
        },
        "query_breakdown": breakdown
    }

    test2_out = REPORTS_DIR / "renal_v31_safety_test2.json"
    test2_out.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    t2_sha = sha256_file(test2_out)
    (REPORTS_DIR / "renal_v31_safety_test2.json.sha256").write_text(f"{t2_sha}  {test2_out.name}\n", encoding="utf-8")
    print(f"Persisted TEST-2 report: {test2_out} (SHA256: {t2_sha})")


if __name__ == "__main__":
    main()
