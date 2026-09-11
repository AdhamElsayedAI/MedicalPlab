"""
MedicalPlab Renal V6 — Phase 6: Fresh Selector Confirmation Execution
======================================================================
Executes ONE-SHOT confirmation of the frozen selector on the newly constructed,
frozen, independent validation benchmark:
evaluation/renal/v6/renal-selector-validation-v6-clean.json (N=40, SHA pre-frozen).

Models evaluated strictly one-shot:
1. Dense baseline (Qwen3-Embedding-0.6B)
2. Class A: Regularized Logistic Selector (fit on all 80 clean train queries)
3. Class B: Deterministic Hybrid RRF (Dense + 1.5 * BM25 Body + 0.2 * Section)

Predeclared Gates:
- STRONG PASS: Coverage@20 >= 95.0% (>= 38 / 40)
- CONDITIONAL PASS: Coverage@20 >= 92.0% (>= 37 / 40)
- FAIL: Coverage@20 < 92.0% (< 37 / 40)
- Naive relevant preservation >= 95.0%
- Multiple rank21+ rescues
"""

import hashlib
import json
import math
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SCRIPTS = _ROOT / "Scripts"
_SRC = _ROOT / "src"
for p in [_RENAL_ENV, _SCRIPTS, _SRC]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer
from sklearn.linear_model import LogisticRegression

CHUNKS_DIR = _ROOT / "Data/experiments/renal_v2/chunking/B_400_overlap"
CACHE_DIR = _ROOT / "Data/experiments/renal_v3/cache"
V5_DIR = _ROOT / "evaluation/renal/v5"
V6_DIR = _ROOT / "evaluation/renal/v6"
REPORTS_V6_DIR = _ROOT / "reports/renal_v6"
REPORTS_V6_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_PATH = V5_DIR / "renal-rerank-train-v5-clean-v1.json"
VAL_PATH = V6_DIR / "renal-selector-validation-v6-clean.json"

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
}

def tokenize(text: str):
    return [w for w in re.findall(r"\b[a-zA-Z0-9_\-\.\/]+\b", text.lower()) if w not in STOPWORDS]

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def main():
    print("Executing Renal V6 Phase 6: Fresh Selector Confirmation Execution (One-Shot)...")

    # Verify input benchmark SHA256
    val_sha = compute_sha256(VAL_PATH)
    val_sha_sidecar = (V6_DIR / "renal-selector-validation-v6-clean.json.sha256").read_text(encoding="utf-8").strip()
    assert val_sha == val_sha_sidecar, f"Benchmark SHA mismatch! Actual: {val_sha}, Expected: {val_sha_sidecar}"
    print(f"Verified pre-frozen benchmark SHA256: {val_sha}")

    # 1. Load datasets
    train_items = json.loads(TRAIN_PATH.read_bytes())
    val_items = json.loads(VAL_PATH.read_bytes())
    n_train = len(train_items)
    n_val = len(val_items)
    print(f"Loaded {n_train} training items and {n_val} fresh validation items.")

    # 2. Load corpus chunks and metadata
    chunks = []
    chunk_doc_ids = []
    chunk_sec_ids = []
    chunk_texts = []
    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_bytes())
        for ch in payload.get("chunks", []):
            chunks.append(ch)
            chunk_doc_ids.append(ch["document_id"])
            sec_id = ch.get("parent_section_id") or f"{ch['document_id']}_{'_'.join(ch.get('section_path', []))}"
            chunk_sec_ids.append(sec_id)
            chunk_texts.append(ch.get("text", ""))

    n_chunks = len(chunks)

    # 3. Load precomputed embeddings
    corpus_embs = np.load(CACHE_DIR / "all23_corpus_embeddings.npy").astype(np.float32)

    # Section Centroids
    sec_ids_unique = sorted(list(set(chunk_sec_ids)))
    sec_id_to_idx = {sid: i for i, sid in enumerate(sec_ids_unique)}
    sec_chunk_indices = defaultdict(list)
    for c_idx, sid in enumerate(chunk_sec_ids):
        sec_chunk_indices[sid].append(c_idx)

    sec_centroids = np.zeros((len(sec_ids_unique), corpus_embs.shape[1]), dtype=np.float32)
    for sid, c_indices in sec_chunk_indices.items():
        s_idx = sec_id_to_idx[sid]
        centroid = corpus_embs[c_indices].mean(axis=0)
        sec_centroids[s_idx] = centroid / np.linalg.norm(centroid)

    # 4. BM25 Body Index
    tokenized_body = [tokenize(t) for t in chunk_texts]
    body_lens = [len(doc) for doc in tokenized_body]
    avgdl_body = sum(body_lens) / n_chunks
    df_body = Counter()
    for doc in tokenized_body:
        df_body.update(set(doc))
    idf_body = {t: math.log(1.0 + (n_chunks - f + 0.5) / (f + 0.5)) for t, f in df_body.items()}

    def bm25_score_tokens(q_tokens, doc_idx):
        doc_tokens = tokenized_body[doc_idx]
        dl = body_lens[doc_idx]
        if dl == 0: return 0.0
        tf = Counter(doc_tokens)
        score = 0.0
        k1, b = 1.2, 0.75
        for t in q_tokens:
            if t in tf:
                freq = tf[t]
                num = idf_body.get(t, 0.0) * freq * (k1 + 1.0)
                denom = freq + k1 * (1.0 - b + b * (dl / avgdl_body))
                score += num / denom
        return score

    # 5. Embed train and validation queries on CUDA
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True)
    mod = AutoModel.from_pretrained("Qwen/Qwen3-Embedding-0.6B", local_files_only=True).to(device).eval()

    QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "

    def embed_queries(text_list):
        formatted = [QUERY_INSTRUCTION + t for t in text_list]
        embs = []
        batch_size = 16
        with torch.no_grad():
            for i in range(0, len(formatted), batch_size):
                batch = formatted[i:i + batch_size]
                encoded = tok(batch, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
                out = mod(**encoded)
                mask = encoded["attention_mask"].unsqueeze(-1).expand(out.last_hidden_state.size()).float()
                pooled = torch.sum(out.last_hidden_state * mask, 1) / torch.clamp(mask.sum(1), min=1e-9)
                normed = torch.nn.functional.normalize(pooled, p=2, dim=1)
                embs.append(normed.cpu().numpy())
        return np.vstack(embs)

    print("Embedding train and validation queries...")
    train_embs = embed_queries([it["query"] for it in train_items])
    val_embs = embed_queries([it["query"] for it in val_items])

    # 6. Extract candidate features and train model on ALL 80 training queries
    print("Extracting training candidates and fitting Class A selector...")
    X_train = []
    y_train = []

    for q_idx, it in enumerate(train_items):
        q_emb = train_embs[q_idx]
        q_tokens = tokenize(it["query"])
        q_token_set = set(q_tokens)
        gold_cids = set(it.get("gold_chunk_ids", []))

        dense_sims = np.dot(corpus_embs, q_emb)
        top500_indices = np.argsort(-dense_sims)[:500]
        sec_sims = np.dot(sec_centroids, q_emb)

        cand_data = []
        for rank_zero, c_idx in enumerate(top500_indices):
            cid = chunks[c_idx]["chunk_id"]
            sid = chunk_sec_ids[c_idx]
            d_rank = rank_zero + 1
            d_score = float(dense_sims[c_idx])
            bm_score = bm25_score_tokens(q_tokens, c_idx)
            sec_score = float(sec_sims[sec_id_to_idx[sid]])
            cand_tokens = set(tokenized_body[c_idx])
            inter = len(q_token_set & cand_tokens)
            containment = inter / max(len(q_token_set), 1)
            jaccard = inter / max(len(q_token_set | cand_tokens), 1)
            is_gold = cid in gold_cids

            cand_data.append({
                "dense_score": d_score,
                "dense_rank": d_rank,
                "bm25_score": bm_score,
                "sec_score": sec_score,
                "containment": containment,
                "jaccard": jaccard,
                "is_gold": is_gold
            })

        by_bm = sorted(cand_data, key=lambda c: -c["bm25_score"])
        for r, c in enumerate(by_bm):
            c["bm25_rank"] = r + 1

        by_sec = sorted(cand_data, key=lambda c: -c["sec_score"])
        for r, c in enumerate(by_sec):
            c["sec_rank"] = r + 1

        scores_dense = np.array([c["dense_score"] for c in cand_data])
        scores_bm25 = np.array([c["bm25_score"] for c in cand_data])
        scores_sec = np.array([c["sec_score"] for c in cand_data])

        sd_d = np.std(scores_dense) or 1.0
        sd_b = np.std(scores_bm25) or 1.0
        sd_s = np.std(scores_sec) or 1.0

        for c in cand_data:
            feat_vec = np.array([
                (c["dense_score"] - np.mean(scores_dense)) / sd_d,
                (c["bm25_score"] - np.mean(scores_bm25)) / sd_b,
                (c["sec_score"] - np.mean(scores_sec)) / sd_s,
                1.0 / (60.0 + c["dense_rank"]),
                1.0 / (60.0 + c["bm25_rank"]),
                1.0 / (60.0 + c["sec_rank"]),
                c["containment"],
                c["jaccard"]
            ], dtype=np.float32)
            X_train.append(feat_vec)
            y_train.append(1 if c["is_gold"] else 0)

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    clf_a = LogisticRegression(C=0.5, class_weight="balanced", max_iter=200, random_state=42)
    clf_a.fit(X_train, y_train)
    print("Class A Logistic Selector successfully fit on N=80 clean train queries.")

    # 7. Evaluate on Fresh Validation (N=40) - ONE-SHOT EXECUTION
    print("\nExecuting ONE-SHOT confirmation evaluation on N=40 fresh validation benchmark...")
    t0 = time.time()

    val_dense_ranks = []
    val_class_a_ranks = []
    val_class_b_ranks = []
    val_dense_rr = []
    val_class_a_rr = []
    val_class_b_rr = []

    dense_top20_total = 0
    class_a_preserved = 0
    class_a_rescues = 0
    class_a_lost = 0

    class_b_preserved = 0
    class_b_rescues = 0
    class_b_lost = 0

    per_query_results = []

    for q_idx, it in enumerate(val_items):
        q_emb = val_embs[q_idx]
        q_tokens = tokenize(it["query"])
        q_token_set = set(q_tokens)
        gold_cids = set(it["gold_chunk_ids"])

        dense_sims = np.dot(corpus_embs, q_emb)
        top500_indices = np.argsort(-dense_sims)[:500]
        sec_sims = np.dot(sec_centroids, q_emb)

        cand_list = []
        for rank_zero, c_idx in enumerate(top500_indices):
            cid = chunks[c_idx]["chunk_id"]
            sid = chunk_sec_ids[c_idx]
            d_rank = rank_zero + 1
            d_score = float(dense_sims[c_idx])
            bm_score = bm25_score_tokens(q_tokens, c_idx)
            sec_score = float(sec_sims[sec_id_to_idx[sid]])
            cand_tokens = set(tokenized_body[c_idx])
            inter = len(q_token_set & cand_tokens)
            containment = inter / max(len(q_token_set), 1)
            jaccard = inter / max(len(q_token_set | cand_tokens), 1)
            is_gold = cid in gold_cids

            cand_list.append({
                "chunk_id": cid,
                "dense_score": d_score,
                "dense_rank": d_rank,
                "bm25_score": bm_score,
                "sec_score": sec_score,
                "containment": containment,
                "jaccard": jaccard,
                "is_gold": is_gold
            })

        by_bm = sorted(cand_list, key=lambda c: -c["bm25_score"])
        for r, c in enumerate(by_bm):
            c["bm25_rank"] = r + 1

        by_sec = sorted(cand_list, key=lambda c: -c["sec_score"])
        for r, c in enumerate(by_sec):
            c["sec_rank"] = r + 1

        scores_dense = np.array([c["dense_score"] for c in cand_list])
        scores_bm25 = np.array([c["bm25_score"] for c in cand_list])
        scores_sec = np.array([c["sec_score"] for c in cand_list])

        sd_d = np.std(scores_dense) or 1.0
        sd_b = np.std(scores_bm25) or 1.0
        sd_s = np.std(scores_sec) or 1.0

        for c in cand_list:
            c["feat_vec"] = np.array([
                (c["dense_score"] - np.mean(scores_dense)) / sd_d,
                (c["bm25_score"] - np.mean(scores_bm25)) / sd_b,
                (c["sec_score"] - np.mean(scores_sec)) / sd_s,
                1.0 / (60.0 + c["dense_rank"]),
                1.0 / (60.0 + c["bm25_rank"]),
                1.0 / (60.0 + c["sec_rank"]),
                c["containment"],
                c["jaccard"]
            ], dtype=np.float32)

            # Class B deterministic score
            c["class_b_score"] = 1.0 / (60.0 + c["dense_rank"]) + 1.5 / (60.0 + c["bm25_rank"]) + 0.2 / (60.0 + c["sec_rank"])

        # Dense Gold Rank
        d_gold_rank = min((c["dense_rank"] for c in cand_list if c["is_gold"]), default=999)
        val_dense_ranks.append(d_gold_rank)
        val_dense_rr.append(1.0 / d_gold_rank if d_gold_rank <= 500 else 0.0)

        # Class A Predict
        X_val_q = np.array([c["feat_vec"] for c in cand_list])
        probs_a = clf_a.predict_proba(X_val_q)[:, 1]
        ranked_a = sorted(zip(cand_list, probs_a), key=lambda x: -x[1])
        class_a_rank = min((r + 1 for r, (c, p) in enumerate(ranked_a) if c["is_gold"]), default=999)
        val_class_a_ranks.append(class_a_rank)
        val_class_a_rr.append(1.0 / class_a_rank if class_a_rank <= 500 else 0.0)

        # Class B Rank
        ranked_b = sorted(cand_list, key=lambda c: -c["class_b_score"])
        class_b_rank = min((r + 1 for r, c in enumerate(ranked_b) if c["is_gold"]), default=999)
        val_class_b_ranks.append(class_b_rank)
        val_class_b_rr.append(1.0 / class_b_rank if class_b_rank <= 500 else 0.0)

        # Rescues and Preservation tracking
        is_dense_in_20 = d_gold_rank <= 20
        if is_dense_in_20:
            dense_top20_total += 1
            if class_a_rank <= 20: class_a_preserved += 1
            else: class_a_lost += 1
            if class_b_rank <= 20: class_b_preserved += 1
            else: class_b_lost += 1
        else:
            if class_a_rank <= 20: class_a_rescues += 1
            if class_b_rank <= 20: class_b_rescues += 1

        per_query_results.append({
            "query_id": it["query_id"],
            "source_document_id": it["source_document_id"],
            "dense_rank": d_gold_rank,
            "class_a_rank": class_a_rank,
            "class_b_rank": class_b_rank,
            "rescued_by_class_a": (d_gold_rank > 20 and class_a_rank <= 20),
            "lost_by_class_a": (d_gold_rank <= 20 and class_a_rank > 20)
        })

    elapsed_ms = (time.time() - t0) * 1000.0 / n_val

    # Aggregate Metrics
    dense_cov20 = sum(1 for r in val_dense_ranks if r <= 20)
    dense_cov20_pct = round(dense_cov20 / n_val * 100.0, 2)

    class_a_cov20 = sum(1 for r in val_class_a_ranks if r <= 20)
    class_a_cov20_pct = round(class_a_cov20 / n_val * 100.0, 2)

    class_b_cov20 = sum(1 for r in val_class_b_ranks if r <= 20)
    class_b_cov20_pct = round(class_b_cov20 / n_val * 100.0, 2)

    class_a_pres_pct = round(class_a_preserved / max(dense_top20_total, 1) * 100.0, 2)
    class_b_pres_pct = round(class_b_preserved / max(dense_top20_total, 1) * 100.0, 2)

    # Predeclared Gates:
    # Strong Pass: Cov@20 >= 95.0%
    # Conditional Pass: Cov@20 >= 92.0%
    # Fail: Cov@20 < 92.0%
    if class_a_cov20_pct >= 95.0:
        gate_verdict = "STRONG_PASS"
    elif class_a_cov20_pct >= 92.0:
        gate_verdict = "CONDITIONAL_PASS"
    else:
        gate_verdict = "FAIL"

    print("\n" + "=" * 80)
    print("FRESH SELECTOR CONFIRMATION RESULTS (N=40 ONE-SHOT)")
    print("=" * 80)
    print(f"Dense Baseline OutputCoverage@20:       {dense_cov20}/40 ({dense_cov20_pct}%) | MRR: {np.mean(val_dense_rr):.4f}")
    print(f"Class A (Logistic) OutputCoverage@20:    {class_a_cov20}/40 ({class_a_cov20_pct}%) | MRR: {np.mean(val_class_a_rr):.4f}")
    print(f"Class B (Hybrid RRF) OutputCoverage@20:  {class_b_cov20}/40 ({class_b_cov20_pct}%) | MRR: {np.mean(val_class_b_rr):.4f}")
    print(f"Class A Naive Preservation:             {class_a_preserved}/{dense_top20_total} ({class_a_pres_pct}%)")
    print(f"Class A Rescues (rank 21+ -> <=20):     {class_a_rescues}")
    print(f"Class A Lost (rank <=20 -> >20):        {class_a_lost}")
    print(f"Average Latency:                        {elapsed_ms:.2f} ms/query")
    print(f"PREDECLARED GATE VERDICT:               {gate_verdict}")
    print("=" * 80)

    report = {
        "report_type": "MEDICALPLAB_RENAL_V6_PHASE6_FRESH_SELECTOR_CONFIRMATION",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mission": "RENAL_V6_PERFORMANCE_FEASIBILITY",
        "benchmark_file": str(VAL_PATH),
        "benchmark_sha256": val_sha,
        "n_validation_queries": n_val,
        "predeclared_gates": {
            "strong_pass": ">= 95.0%",
            "conditional_pass": ">= 92.0%",
            "fail": "< 92.0%"
        },
        "results": {
            "dense_baseline": {
                "coverage_at_20_count": dense_cov20,
                "coverage_at_20_percent": dense_cov20_pct,
                "mrr": round(float(np.mean(val_dense_rr)), 4),
                "median_gold_rank": float(np.median(val_dense_ranks))
            },
            "class_a_regularized_logistic": {
                "coverage_at_20_count": class_a_cov20,
                "coverage_at_20_percent": class_a_cov20_pct,
                "mrr": round(float(np.mean(val_class_a_rr)), 4),
                "median_gold_rank": float(np.median(val_class_a_ranks)),
                "naive_relevant_total": dense_top20_total,
                "naive_relevant_preserved": class_a_preserved,
                "naive_preservation_pct": class_a_pres_pct,
                "rank21_plus_rescues": class_a_rescues,
                "lost_relevant_cases": class_a_lost,
                "latency_ms_per_query": round(elapsed_ms, 2)
            },
            "class_b_deterministic_hybrid_rrf": {
                "coverage_at_20_count": class_b_cov20,
                "coverage_at_20_percent": class_b_cov20_pct,
                "mrr": round(float(np.mean(val_class_b_rr)), 4),
                "median_gold_rank": float(np.median(val_class_b_ranks)),
                "naive_relevant_total": dense_top20_total,
                "naive_relevant_preserved": class_b_preserved,
                "naive_preservation_pct": class_b_pres_pct,
                "rank21_plus_rescues": class_b_rescues,
                "lost_relevant_cases": class_b_lost
            }
        },
        "gate_verdict": gate_verdict,
        "per_query_diagnostics": per_query_results
    }

    report_path = REPORTS_V6_DIR / "renal_v6_phase6_confirmation_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report_sha = compute_sha256(report_path)
    (REPORTS_V6_DIR / "renal_v6_phase6_confirmation_report.json.sha256").write_text(report_sha + "\n", encoding="utf-8")

    print(f"Report written to {report_path}")
    print(f"Report SHA256: {report_sha}")

if __name__ == "__main__":
    main()
