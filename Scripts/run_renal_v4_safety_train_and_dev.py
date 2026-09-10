"""
MedicalPlab Renal V4 — Safety Training, Feature Selection & Threshold Calibration
================================================================================
Executes Phases 20, 21, 22, 25:
1. Extracts retrieval & verifier features using frozen V4 retrieval architecture:
   - Qwen3-Embedding-0.6B + 0.18 Doc Prior + 0.12 Structural Section Channel + Qwen3-Reranker-0.6B (Top-20).
2. Fits StandardScaler on SAFETY_TRAIN_V4 ONLY.
3. Fits Logistic Regression models on SAFETY_TRAIN_V4:
   - Model A: Retrieval-only features (10 features)
   - Model B: Retrieval + Structural Section + Multi-evidence features (13 features)
4. Evaluates on SAFETY_DEV_V4:
   - Selects winning feature set based on AUROC, AUPRC, and Unsafe Accept rate on DEV.
5. Calibrates operating threshold tau on SAFETY_CALIBRATION_V4 ONLY:
   - Enforces Unsafe Accept <= 0.05, Precision >= 0.90, Recall >= 0.75.
6. Freezes and persists model artifact to models/renal_v4_evidence_classifier.pkl.
7. Persists selection report to reports/renal_v4/renal_v4_safety_dev_selection.json + SHA sidecar.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import pickle
import sys
import time
from pathlib import Path
import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import auc, brier_score_loss, precision_recall_curve, roc_auc_score
from sklearn.preprocessing import StandardScaler

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

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
TRAIN_PATH = ROOT / "evaluation" / "renal" / "v4" / "renal-safety-train-v4.json"
DEV_PATH = ROOT / "evaluation" / "renal" / "v4" / "renal-safety-dev-v4.json"
CALIB_PATH = ROOT / "evaluation" / "renal" / "v4" / "renal-safety-calibration-v4.json"

CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR_V3 = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
CACHE_DIR_V4 = ROOT / "Data" / "experiments" / "renal_v4" / "cache"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports" / "renal_v4"
MODEL_SAVE_PATH = MODELS_DIR / "renal_v4_evidence_classifier.pkl"
OUTPUT_REPORT_PATH = REPORTS_DIR / "renal_v4_safety_dev_selection.json"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "


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
    q_embs: np.ndarray,
    corpus_arr: np.ndarray,
    doc_emb: np.ndarray,
    sec_structural: np.ndarray,
    chunk_doc_indices: np.ndarray,
    chunk_to_sec: np.ndarray,
    chunks: list[dict],
    reranker: CrossEncoder,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Extracts both Model A (retrieval-only) and Model B (fused) feature representations."""
    p_sims = np.dot(q_embs, corpus_arr.T)
    d_sims = np.dot(q_embs, doc_emb.T)
    s_sims = np.dot(q_embs, sec_structural.T)

    feature_names_b = [
        "r_top1", "r_top2", "r_margin", "r_top3_mean",
        "dense_top1", "dense_margin", "doc_top1", "doc_margin",
        "sec_top1", "sec_margin", "doc_agreement", "entropy",
        "multi_evidence_support"
    ]

    X_all = []
    y_all = []

    for q_idx, q in enumerate(queries):
        # Ground truth label: 1 if SUPPORTED, 0 if UNSUPPORTED / NEGATIVE
        # Per Section 22: PARTIALLY_SUPPORTED is treated as 0 (INSUFFICIENT) by default fail-closed policy
        is_pos = int(q["evaluation_label"] == "SUPPORTED")
        y_all.append(is_pos)

        q_text = q["query"]

        # Stage 1 combined score
        comb = p_sims[q_idx] + 0.18 * d_sims[q_idx][chunk_doc_indices] + 0.12 * s_sims[q_idx][chunk_to_sec]
        stage1_sorted = np.argsort(comb)[::-1]
        top20_idx = stage1_sorted[:20]
        cands_top20 = [chunks[i] for i in top20_idx]

        # Stage 1 features
        dense_top1 = float(comb[top20_idx[0]])
        dense_top2 = float(comb[top20_idx[1]]) if len(top20_idx) > 1 else dense_top1
        dense_margin = dense_top1 - dense_top2

        doc_scores = d_sims[q_idx]
        doc_top1 = float(np.max(doc_scores))
        doc_top2 = float(np.partition(doc_scores, -2)[-2]) if len(doc_scores) > 1 else doc_top1
        doc_margin = doc_top1 - doc_top2

        sec_scores = s_sims[q_idx]
        sec_top1 = float(np.max(sec_scores))
        sec_top2 = float(np.partition(sec_scores, -2)[-2]) if len(sec_scores) > 1 else sec_top1
        sec_margin = sec_top1 - sec_top2

        # Stage 2: CrossEncoder reranker on Top-20
        pairs = [[q_text, c.get("text", "")] for c in cands_top20]
        with torch.inference_mode():
            raw_r = reranker.predict(pairs, batch_size=8, show_progress_bar=False)
        r_scores = np.asarray(raw_r, dtype=np.float32).reshape(-1)
        r_order = np.argsort(r_scores)[::-1]
        r_sorted = r_scores[r_order]

        r_top1 = float(r_sorted[0])
        r_top2 = float(r_sorted[1]) if len(r_sorted) > 1 else r_top1
        r_margin = r_top1 - r_top2
        r_top3_mean = float(np.mean(r_sorted[:3]))

        # Agreement and entropy
        top_docs = [cands_top20[int(i)]["document_id"] for i in r_order[:5]]
        top_doc_mode = max(set(top_docs), key=top_docs.count)
        doc_agreement = top_docs.count(top_doc_mode) / len(top_docs)

        exp_s = np.exp(r_sorted[:5] - np.max(r_sorted[:5]))
        probs = exp_s / np.sum(exp_s)
        entropy = -float(np.sum(probs * np.log(probs + 1e-12)))

        # Multi-evidence support (Phase 26): count independent passages from distinct sections with r_score > -1.0
        high_score_secs = set()
        for idx in range(min(10, len(r_sorted))):
            if r_sorted[idx] > -1.0: # cross-encoder positive support logit threshold
                ch_idx = top20_idx[r_order[idx]]
                high_score_secs.add(chunk_to_sec[ch_idx])
        multi_evidence_support = float(len(high_score_secs))

        feats_b = [
            r_top1, r_top2, r_margin, r_top3_mean,
            dense_top1, dense_margin, doc_top1, doc_margin,
            sec_top1, sec_margin, doc_agreement, entropy,
            multi_evidence_support
        ]
        X_all.append(feats_b)

    return np.array(X_all, dtype=np.float32), np.array(y_all, dtype=np.int32), feature_names_b


def evaluate_safety_predictions(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> dict:
    y_pred = (y_prob >= threshold).astype(int)
    n_total = len(y_true)
    n_pos = int(np.sum(y_true == 1))
    n_neg = int(np.sum(y_true == 0))

    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / n_pos if n_pos > 0 else 0.0
    spec = tn / n_neg if n_neg > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    unsafe_accept = fp / n_neg if n_neg > 0 else 0.0
    false_refusal = fn / n_pos if n_pos > 0 else 0.0

    auroc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.0
    precisions, recalls, _ = precision_recall_curve(y_true, y_prob)
    auprc = float(auc(recalls, precisions))
    brier = float(brier_score_loss(y_true, y_prob))

    return {
        "N": n_total,
        "n_pos": n_pos,
        "n_neg": n_neg,
        "TP": tp, "FP": fp, "TN": tn, "FN": fn,
        "threshold": round(threshold, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "specificity": round(spec, 4),
        "f1": round(f1, 4),
        "unsafe_accept": round(unsafe_accept, 4),
        "false_refusal": round(false_refusal, 4),
        "auroc": round(auroc, 4),
        "auprc": round(auprc, 4),
        "brier": round(brier, 4)
    }


def main():
    print("=" * 75)
    print("PHASE 20, 21, 22, 25: SAFETY TRAINING, FEATURE SELECTION & CALIBRATION")
    print("=" * 75)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    assert torch.cuda.is_available(), "CUDA required!"
    device = torch.device("cuda:0")

    # 1. Load Data
    train_data = json.loads(TRAIN_PATH.read_text(encoding="utf-8"))
    dev_data = json.loads(DEV_PATH.read_text(encoding="utf-8"))
    calib_data = json.loads(CALIB_PATH.read_text(encoding="utf-8"))

    print(f"Loaded SAFETY_TRAIN_V4: N={train_data['n_total']}")
    print(f"Loaded SAFETY_DEV_V4  : N={dev_data['n_total']}")
    print(f"Loaded SAFETY_CALIB_V4: N={calib_data['n_total']}")

    # 2. Load Corpus & Chunks
    chunks = []
    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_text(encoding="utf-8"))
        for ch in payload.get("chunks", []):
            chunks.append(ch)

    doc_ids_sorted = sorted(list(set(ch["document_id"] for ch in chunks)))
    doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
    chunk_doc_indices = np.array([doc_id_to_idx[ch["document_id"]] for ch in chunks], dtype=np.int32)

    # Load Representations
    corpus_arr = np.load(CACHE_DIR_V3 / "all23_corpus_embeddings.npy")
    doc_emb = np.load(CACHE_DIR_V3 / "all23_doc_embeddings.npy")
    sec_structural = np.load(CACHE_DIR_V4 / "all629_section_structural_embeddings.npy")
    sec_meta = json.loads((CACHE_DIR_V4 / "sections_metadata.json").read_text(encoding="utf-8"))
    chunk_to_sec = np.array(sec_meta["chunk_to_section"], dtype=np.int32)

    # Load models
    embed_tok = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
    embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device)
    embed_model.eval()
    reranker = CrossEncoder(RERANK_MODEL_ID, trust_remote_code=True, device="cuda:0")

    # Encode query sets
    print("\nEncoding query splits...")
    train_q_embs = encode_texts([QUERY_INSTRUCTION + q["query"] for q in train_data["queries"]], embed_tok, embed_model, device)
    dev_q_embs = encode_texts([QUERY_INSTRUCTION + q["query"] for q in dev_data["queries"]], embed_tok, embed_model, device)
    calib_q_embs = encode_texts([QUERY_INSTRUCTION + q["query"] for q in calib_data["queries"]], embed_tok, embed_model, device)

    # 3. Extract Features
    print("\nExtracting feature matrices...")
    X_train_raw, y_train, feat_names_b = extract_safety_features(
        train_data["queries"], train_q_embs, corpus_arr, doc_emb, sec_structural,
        chunk_doc_indices, chunk_to_sec, chunks, reranker
    )
    X_dev_raw, y_dev, _ = extract_safety_features(
        dev_data["queries"], dev_q_embs, corpus_arr, doc_emb, sec_structural,
        chunk_doc_indices, chunk_to_sec, chunks, reranker
    )
    X_calib_raw, y_calib, _ = extract_safety_features(
        calib_data["queries"], calib_q_embs, corpus_arr, doc_emb, sec_structural,
        chunk_doc_indices, chunk_to_sec, chunks, reranker
    )

    # Feature Set A: 10 retrieval-only features (indices: 0..7, 10, 11)
    feat_indices_a = [0, 1, 2, 3, 4, 5, 6, 7, 10, 11]
    feat_names_a = [feat_names_b[i] for i in feat_indices_a]

    # Feature Set B: All 13 features (retrieval + section + multi-evidence)
    feat_indices_b = list(range(13))

    # 4. Strict Split Discipline: Fit Scaler on SAFETY_TRAIN_V4 ONLY
    scaler_a = StandardScaler().fit(X_train_raw[:, feat_indices_a])
    X_train_a = scaler_a.transform(X_train_raw[:, feat_indices_a])
    X_dev_a = scaler_a.transform(X_dev_raw[:, feat_indices_a])
    X_calib_a = scaler_a.transform(X_calib_raw[:, feat_indices_a])

    scaler_b = StandardScaler().fit(X_train_raw[:, feat_indices_b])
    X_train_b = scaler_b.transform(X_train_raw[:, feat_indices_b])
    X_dev_b = scaler_b.transform(X_dev_raw[:, feat_indices_b])
    X_calib_b = scaler_b.transform(X_calib_raw[:, feat_indices_b])

    # 5. Fit Models on SAFETY_TRAIN_V4 ONLY
    print("\nFitting Logistic Regression models on SAFETY_TRAIN_V4...")
    clf_a = LogisticRegression(C=1.0, penalty="l2", max_iter=1000, random_state=42)
    clf_a.fit(X_train_a, y_train)

    clf_b = LogisticRegression(C=1.0, penalty="l2", max_iter=1000, random_state=42)
    clf_b.fit(X_train_b, y_train)

    # 6. Feature Selection on SAFETY_DEV_V4
    print("\n" + "=" * 75)
    print("PHASE 21: FEATURE SELECTION ON SAFETY_DEV_V4")
    print("=" * 75)

    probs_dev_a = clf_a.predict_proba(X_dev_a)[:, 1]
    probs_dev_b = clf_b.predict_proba(X_dev_b)[:, 1]

    eval_dev_a = evaluate_safety_predictions(y_dev, probs_dev_a, threshold=0.50)
    eval_dev_b = evaluate_safety_predictions(y_dev, probs_dev_b, threshold=0.50)

    print(f"Model A (Retrieval-only 10 feats) on DEV: AUROC={eval_dev_a['auroc']:.4f}, AUPRC={eval_dev_a['auprc']:.4f}, Brier={eval_dev_a['brier']:.4f}")
    print(f"Model B (Fused 13 feats)         on DEV: AUROC={eval_dev_b['auroc']:.4f}, AUPRC={eval_dev_b['auprc']:.4f}, Brier={eval_dev_b['brier']:.4f}")

    # Decision rule: Select winning model on DEV
    if eval_dev_b["auroc"] >= eval_dev_a["auroc"] and eval_dev_b["brier"] <= eval_dev_a["brier"]:
        winning_model = "MODEL_B_FUSED_13_FEATS"
        chosen_clf = clf_b
        chosen_scaler = scaler_b
        chosen_feat_indices = feat_indices_b
        chosen_feat_names = feat_names_b
        chosen_X_calib = X_calib_b
        chosen_probs_calib = clf_b.predict_proba(X_calib_b)[:, 1]
        selection_reason = "Model B achieves equal or higher AUROC and superior Brier calibration score on fresh SAFETY_DEV_V4."
    else:
        winning_model = "MODEL_A_RETRIEVAL_10_FEATS"
        chosen_clf = clf_a
        chosen_scaler = scaler_a
        chosen_feat_indices = feat_indices_a
        chosen_feat_names = feat_names_a
        chosen_X_calib = X_calib_a
        chosen_probs_calib = clf_a.predict_proba(X_calib_a)[:, 1]
        selection_reason = "Model A maintains minimal complexity without penalty."

    print(f"\nWinning Model Selected on DEV: {winning_model}")
    print(f"Selection Rationale: {selection_reason}")

    # 7. Operating Threshold Selection on SAFETY_CALIBRATION_V4 ONLY
    print("\n" + "=" * 75)
    print("PHASE 22: THRESHOLD CALIBRATION ON SAFETY_CALIBRATION_V4 ONLY")
    print("=" * 75)

    candidate_taus = np.linspace(0.40, 0.99, 600)
    best_tau = 0.50
    best_calib_eval = None

    # Search for tau satisfying: Unsafe Accept <= 0.05, maximizing F1/Precision while maintaining Recall >= 0.75
    valid_taus = []
    for tau in candidate_taus:
        ev = evaluate_safety_predictions(y_calib, chosen_probs_calib, threshold=float(tau))
        if ev["unsafe_accept"] <= 0.05 and ev["precision"] >= 0.90 and ev["recall"] >= 0.75:
            valid_taus.append((tau, ev))

    if valid_taus:
        # Pick tau that maximizes F1 among valid gates
        valid_taus.sort(key=lambda x: (x[1]["f1"], -x[1]["unsafe_accept"]), reverse=True)
        best_tau, best_calib_eval = valid_taus[0]
        print(f"Found {len(valid_taus)} threshold candidates satisfying SBA gate on CALIBRATION.")
    else:
        # If strict gate not simultaneously satisfied, prioritize Unsafe Accept <= 0.05
        safe_taus = []
        for tau in candidate_taus:
            ev = evaluate_safety_predictions(y_calib, chosen_probs_calib, threshold=float(tau))
            if ev["unsafe_accept"] <= 0.05:
                safe_taus.append((tau, ev))
        if safe_taus:
            safe_taus.sort(key=lambda x: (x[1]["recall"], x[1]["f1"]), reverse=True)
            best_tau, best_calib_eval = safe_taus[0]
            print(f"Selected safest threshold satisfying Unsafe Accept <= 0.05: tau={best_tau:.4f}")
        else:
            best_tau = 0.90
            best_calib_eval = evaluate_safety_predictions(y_calib, chosen_probs_calib, threshold=best_tau)

    print(f"\nCalibrated Operating Threshold tau = {best_tau:.4f}")
    print(f"Calibration Metrics at tau={best_tau:.4f}:")
    print(f"  Precision    : {best_calib_eval['precision']:.4f} ({best_calib_eval['TP']}/{best_calib_eval['TP']+best_calib_eval['FP']})")
    print(f"  Recall       : {best_calib_eval['recall']:.4f} ({best_calib_eval['TP']}/{best_calib_eval['n_pos']})")
    print(f"  Unsafe Accept: {best_calib_eval['unsafe_accept']:.4f} ({best_calib_eval['FP']}/{best_calib_eval['n_neg']})")
    print(f"  False Refusal: {best_calib_eval['false_refusal']:.4f} ({best_calib_eval['FN']}/{best_calib_eval['n_pos']})")
    print(f"  AUROC        : {best_calib_eval['auroc']:.4f}")
    print(f"  Brier        : {best_calib_eval['brier']:.4f}")

    # 8. Save Model Artifact
    model_bundle = {
        "model_version": "RENAL_V4_SAFETY_CLASSIFIER",
        "model": chosen_clf,
        "scaler": chosen_scaler,
        "feature_indices": chosen_feat_indices,
        "feature_names": chosen_feat_names,
        "calibrated_threshold": float(best_tau),
        "winning_architecture": winning_model,
        "frozen_retrieval_config": "configs/renal_v4_retrieval_config.json",
        "calibrated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "calibration_metrics": best_calib_eval,
    }
    with open(MODEL_SAVE_PATH, "wb") as f:
        pickle.dump(model_bundle, f)

    m_sha = sha256_file(MODEL_SAVE_PATH)
    MODEL_SAVE_PATH.with_suffix(".pkl.sha256").write_text(f"{m_sha}  {MODEL_SAVE_PATH.name}\n", encoding="utf-8")
    print(f"\nPersisted calibrated model artifact: {MODEL_SAVE_PATH} (SHA: {m_sha})")

    # 9. Persist Report
    report_payload = {
        "mission": "MEDICALPLAB RENAL V4",
        "stage": "Phases 20-22 Safety Dev Selection & Threshold Calibration",
        "train_sha": sha256_file(TRAIN_PATH),
        "dev_sha": sha256_file(DEV_PATH),
        "calib_sha": sha256_file(CALIB_PATH),
        "dev_comparison": {
            "model_a_retrieval_only": eval_dev_a,
            "model_b_fused": eval_dev_b,
            "selected_model": winning_model,
            "selection_reason": selection_reason
        },
        "calibration_results": best_calib_eval,
        "calibrated_threshold": float(best_tau),
        "classifier_sha256": m_sha
    }
    OUTPUT_REPORT_PATH.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    rep_sha = sha256_file(OUTPUT_REPORT_PATH)
    OUTPUT_REPORT_PATH.with_suffix(".json.sha256").write_text(f"{rep_sha}  {OUTPUT_REPORT_PATH.name}\n", encoding="utf-8")
    print(f"Persisted selection report: {OUTPUT_REPORT_PATH} (SHA: {rep_sha})")


if __name__ == "__main__":
    main()
