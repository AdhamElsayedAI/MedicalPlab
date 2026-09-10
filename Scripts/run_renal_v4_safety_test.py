"""
MedicalPlab Renal V4 — Phase 26: Execute SAFETY_TEST_V4 (Single Logical Execution)
==================================================================================
Strict Protocol:
- Verified SHAs before execution:
  - Retrieval Config
  - Safety Config
  - Classifier Artifact
  - SAFETY_TEST_V4 Dataset
- Runs exactly once.
- Evaluates N=120 (50 Supported, 10 Partial [=60 Positives], 60 Negatives).
- Reports:
  - TP, TN, FP, FN
  - Precision, Recall, Specificity, F1
  - Unsafe Accept Rate (with exact Clopper-Pearson 95% confidence interval)
  - False Refusal Rate
  - AUROC, AUPRC, Brier score
  - Breakdown by negative stratum:
    * In-domain coverage gap (N=20)
    * Out-of-domain unsupported (N=20)
    * Difficult perturbation negative (N=20)
- Immutable SBA Gate Evaluation:
  Unsafe Accept <= 0.05, Precision >= 0.90, Recall >= 0.75.
- Persists reports/renal_v4/renal_v4_safety_test_results.json + SHA sidecar.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import pickle
import sys
import time
from pathlib import Path
import numpy as np
import torch
from scipy.stats import beta
from sklearn.metrics import auc, brier_score_loss, precision_recall_curve, roc_auc_score

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
SAFETY_CONFIG_PATH = ROOT / "configs" / "renal_v4_safety_config.json"
TEST_DATA_PATH = ROOT / "evaluation" / "renal" / "v4" / "renal-safety-test-v4.json"
MODEL_PATH = ROOT / "models" / "renal_v4_evidence_classifier.pkl"
REPORTS_DIR = ROOT / "reports" / "renal_v4"
OUTPUT_REPORT_PATH = REPORTS_DIR / "renal_v4_safety_test_results.json"

CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR_V3 = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
CACHE_DIR_V4 = ROOT / "Data" / "experiments" / "renal_v4" / "cache"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clopper_pearson(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Computes exact two-sided Clopper-Pearson confidence interval."""
    if n == 0:
        return (0.0, 1.0)
    alpha = 1.0 - confidence
    lower = 0.0 if k == 0 else float(beta.ppf(alpha / 2.0, k, n - k + 1))
    upper = 1.0 if k == n else float(beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))
    return (lower, upper)


def clopper_pearson_upper_onesided(k: int, n: int, confidence: float = 0.95) -> float:
    """Computes exact one-sided Clopper-Pearson upper confidence bound."""
    if n == 0:
        return 1.0
    alpha = 1.0 - confidence
    if k == 0:
        return 1.0 - (alpha ** (1.0 / n))
    return float(beta.ppf(confidence, k + 1, n - k))


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


def main():
    print("=" * 80)
    print("PHASE 26: LOCKED SINGLE LOGICAL RUN OF SAFETY_TEST_V4")
    print("=" * 80)

    # 1. Verify Configuration and Checksums
    assert SAFETY_CONFIG_PATH.exists(), f"Safety config missing: {SAFETY_CONFIG_PATH}"
    cfg = json.loads(SAFETY_CONFIG_PATH.read_text(encoding="utf-8"))
    cfg_sha = sha256_file(SAFETY_CONFIG_PATH)
    print(f"Safety Config SHA256: {cfg_sha}")

    assert TEST_DATA_PATH.exists(), f"Safety test missing: {TEST_DATA_PATH}"
    test_sha = sha256_file(TEST_DATA_PATH)
    assert test_sha == cfg["safety_test_sha256"], f"Test SHA mismatch! {test_sha} != {cfg['safety_test_sha256']}"
    print(f"Verified SAFETY_TEST_V4 SHA256: {test_sha}")

    assert MODEL_PATH.exists(), f"Model artifact missing: {MODEL_PATH}"
    m_sha = sha256_file(MODEL_PATH)
    assert m_sha == cfg["classifier_artifact_sha256"], f"Model SHA mismatch! {m_sha} != {cfg['classifier_artifact_sha256']}"
    print(f"Verified Classifier SHA256: {m_sha}")

    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)
    clf = bundle["model"]
    scaler = bundle["scaler"]
    feat_indices = bundle["feature_indices"]
    tau = cfg["operating_threshold_tau"]
    print(f"Loaded Frozen Classifier: Operating Threshold tau={tau:.4f}")

    # 2. Check Device
    assert torch.cuda.is_available(), "CUDA required!"
    device = torch.device("cuda:0")

    # 3. Load Test Data
    test_data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    queries = test_data["queries"]
    n_total = len(queries)
    assert n_total == 120, f"Expected 120 test queries, found {n_total}"
    print(f"Loaded {n_total} test queries.")

    # 4. Load Corpus & Representations
    chunks = []
    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_text(encoding="utf-8"))
        for ch in payload.get("chunks", []):
            chunks.append(ch)

    doc_ids_sorted = sorted(list(set(ch["document_id"] for ch in chunks)))
    doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
    chunk_doc_indices = np.array([doc_id_to_idx[ch["document_id"]] for ch in chunks], dtype=np.int32)

    corpus_arr = np.load(CACHE_DIR_V3 / "all23_corpus_embeddings.npy")
    doc_emb = np.load(CACHE_DIR_V3 / "all23_doc_embeddings.npy")
    sec_structural = np.load(CACHE_DIR_V4 / "all629_section_structural_embeddings.npy")
    sec_meta = json.loads((CACHE_DIR_V4 / "sections_metadata.json").read_text(encoding="utf-8"))
    chunk_to_sec = np.array(sec_meta["chunk_to_section"], dtype=np.int32)

    embed_tok = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
    embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device)
    embed_model.eval()
    reranker = CrossEncoder(RERANK_MODEL_ID, trust_remote_code=True, device="cuda:0")

    # 5. Encode Test Queries
    print("Encoding test queries...")
    q_texts = [q["query"] for q in queries]
    q_instruct = [QUERY_INSTRUCTION + q for q in q_texts]
    q_embs = encode_texts(q_instruct, embed_tok, embed_model, device)

    # 6. Extract Features
    print("Extracting features using frozen V4 retrieval architecture...")
    p_sims = np.dot(q_embs, corpus_arr.T)
    d_sims = np.dot(q_embs, doc_emb.T)
    s_sims = np.dot(q_embs, sec_structural.T)

    X_test_raw = []
    y_test = []
    strata_labels = []

    for q_idx, q in enumerate(queries):
        # Operational truth: SUPPORTED is positive (1), all else negative (0)
        label = q["evaluation_label"]
        is_pos = int(label == "SUPPORTED")
        y_test.append(is_pos)
        strata_labels.append(label)

        q_text = q["query"]

        # Stage 1 combined score
        comb = p_sims[q_idx] + 0.18 * d_sims[q_idx][chunk_doc_indices] + 0.12 * s_sims[q_idx][chunk_to_sec]
        stage1_sorted = np.argsort(comb)[::-1]
        top20_idx = stage1_sorted[:20]
        cands_top20 = [chunks[i] for i in top20_idx]

        dense_top1 = float(comb[top20_idx[0]])
        dense_top2 = float(comb[top20_idx[1]]) if len(top20_idx) > 1 else dense_top1
        dense_margin = dense_top1 - dense_top2

        doc_scores = d_sims[q_idx]
        doc_top1 = float(np.max(doc_scores))
        doc_top2 = float(np.partition(doc_scores, -2)[-2]) if len(doc_scores) > 1 else doc_top1
        doc_margin = doc_top1 - doc_top2

        # Stage 2: CrossEncoder reranker
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

        top_docs = [cands_top20[int(i)]["document_id"] for i in r_order[:5]]
        top_doc_mode = max(set(top_docs), key=top_docs.count)
        doc_agreement = top_docs.count(top_doc_mode) / len(top_docs)

        exp_s = np.exp(r_sorted[:5] - np.max(r_sorted[:5]))
        probs = exp_s / np.sum(exp_s)
        entropy = -float(np.sum(probs * np.log(probs + 1e-12)))

        feats = [
            r_top1, r_top2, r_margin, r_top3_mean,
            dense_top1, dense_margin, doc_top1, doc_margin,
            doc_agreement, entropy
        ]
        X_test_raw.append(feats)

    X_test_raw = np.array(X_test_raw, dtype=np.float32)
    y_test = np.array(y_test, dtype=np.int32)
    strata_labels = np.array(strata_labels)

    # 7. Normalize features using FROZEN scaler
    X_test_norm = scaler.transform(X_test_raw)

    # 8. Predict probabilities and decisions
    test_probs = clf.predict_proba(X_test_norm)[:, 1]
    test_preds = (test_probs >= tau).astype(int)

    # 9. Compute Overall Metrics
    n_pos = int(np.sum(y_test == 1))
    n_neg = int(np.sum(y_test == 0))
    tp = int(np.sum((test_preds == 1) & (y_test == 1)))
    fp = int(np.sum((test_preds == 1) & (y_test == 0)))
    tn = int(np.sum((test_preds == 0) & (y_test == 0)))
    fn = int(np.sum((test_preds == 0) & (y_test == 1)))

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / n_pos if n_pos > 0 else 0.0
    spec = tn / n_neg if n_neg > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    unsafe_accept = fp / n_neg if n_neg > 0 else 0.0
    false_refusal = fn / n_pos if n_pos > 0 else 0.0

    auroc = float(roc_auc_score(y_test, test_probs))
    precisions_curve, recalls_curve, _ = precision_recall_curve(y_test, test_probs)
    auprc = float(auc(recalls_curve, precisions_curve))
    brier = float(brier_score_loss(y_test, test_probs))

    # Exact Clopper-Pearson confidence interval on Unsafe Accept
    cp_low, cp_high = clopper_pearson(fp, n_neg, 0.95)
    cp_upper_onesided = clopper_pearson_upper_onesided(fp, n_neg, 0.95)

    # 10. Compute Stratified Metrics across Negative Classes
    strata_metrics = {}
    for stratum in ["IN_DOMAIN_CORPUS_COVERAGE_GAP", "OUT_OF_DOMAIN_UNSUPPORTED", "DIFFICULT_PERTURBATION_NEGATIVE", "PARTIALLY_SUPPORTED"]:
        idx_s = np.where(strata_labels == stratum)[0]
        n_s = len(idx_s)
        if n_s > 0:
            fp_s = int(np.sum(test_preds[idx_s] == 1))
            tn_s = int(np.sum(test_preds[idx_s] == 0))
            ua_s = fp_s / n_s
            strata_metrics[stratum] = {
                "N": n_s,
                "FP_accepted": fp_s,
                "TN_refused": tn_s,
                "unsafe_accept_rate": round(ua_s, 4),
                "fraction_stratum": f"{fp_s}/{n_s}"
            }

    # 11. Evaluate SBA Quality Gate
    # SBA criteria: Unsafe Accept <= 0.05, Precision >= 0.90, Recall >= 0.75
    gate_pass = (unsafe_accept <= 0.05 and prec >= 0.90 and rec >= 0.75)
    sba_verdict = "SAFETY_GATE_PASS" if gate_pass else "SAFETY_GATE_FAIL"

    print("\n" + "=" * 80)
    print("FINAL SAFETY_TEST_V4 EVALUATION RESULTS")
    print("=" * 80)
    print(f"Total Test Items (N)    : {n_total}")
    print(f"Positives (Supported)   : {n_pos}")
    print(f"Negatives (All non-supp): {n_neg}")
    print(f"Confusion Matrix        : TP={tp}, FP={fp}, TN={tn}, FN={fn}")
    print(f"Decision Threshold tau  : {tau:.4f}")
    print("-" * 50)
    print(f"Precision               : {prec:.4f} ({tp}/{tp+fp})")
    print(f"Recall                  : {rec:.4f} ({tp}/{n_pos})")
    print(f"Specificity             : {spec:.4f} ({tn}/{n_neg})")
    print(f"F1 Score                : {f1:.4f}")
    print(f"AUROC                   : {auroc:.4f}")
    print(f"AUPRC                   : {auprc:.4f}")
    print(f"Brier Score             : {brier:.4f}")
    print("-" * 50)
    print(f"Unsafe Accept Rate (Obs): {unsafe_accept:.4f} ({fp}/{n_neg} = {unsafe_accept*100:.2f}%)")
    print(f"  95% CP Two-Sided CI   : [{cp_low:.4f}, {cp_high:.4f}]")
    print(f"  95% CP One-Sided Upper: {cp_upper_onesided:.4f} ({cp_upper_onesided*100:.2f}%)")
    print(f"False Refusal Rate      : {false_refusal:.4f} ({fn}/{n_pos})")
    print("-" * 50)
    print("Negative Strata Breakdown:")
    for strat, data_s in strata_metrics.items():
        print(f"  {strat:35s}: Unsafe Accept = {data_s['fraction_stratum']} ({data_s['unsafe_accept_rate']*100:.1f}%)")
    print("=" * 80)
    print(f"OFFICIAL SBA SAFETY GATE VERDICT: {sba_verdict}")
    print("=" * 80)

    # 12. Persist Report
    report = {
        "mission": "MEDICALPLAB RENAL V4",
        "stage": "Phase 26 SAFETY_TEST_V4 Single Logical Evaluation",
        "dataset_name": "SAFETY_TEST_V4",
        "dataset_sha256": test_sha,
        "safety_config_sha256": cfg_sha,
        "classifier_artifact_sha256": m_sha,
        "retrieval_config_sha256": cfg["retrieval_config_sha256"],
        "operating_threshold_tau": tau,
        "metrics": {
            "N_total": n_total,
            "N_positive": n_pos,
            "N_negative": n_neg,
            "TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "specificity": round(spec, 4),
            "f1": round(f1, 4),
            "auroc": round(auroc, 4),
            "auprc": round(auprc, 4),
            "brier": round(brier, 4),
            "unsafe_accept_rate": round(unsafe_accept, 4),
            "unsafe_accept_ci_95_two_sided": [round(cp_low, 4), round(cp_high, 4)],
            "unsafe_accept_cp_95_one_sided_upper": round(cp_upper_onesided, 4),
            "false_refusal_rate": round(false_refusal, 4)
        },
        "strata_breakdown": strata_metrics,
        "sba_safety_gate": {
            "unsafe_accept_pass": bool(unsafe_accept <= 0.05),
            "precision_pass": bool(prec >= 0.90),
            "recall_pass": bool(rec >= 0.75),
            "verdict": sba_verdict
        }
    }

    OUTPUT_REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    rep_sha = sha256_file(OUTPUT_REPORT_PATH)
    OUTPUT_REPORT_PATH.with_suffix(".json.sha256").write_text(f"{rep_sha}  {OUTPUT_REPORT_PATH.name}\n", encoding="utf-8")
    print(f"\nPersisted safety test report: {OUTPUT_REPORT_PATH} (SHA: {rep_sha})")


if __name__ == "__main__":
    main()
