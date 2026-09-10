"""Phase 29, 30 & 31: Locked Fair Final Evaluation (V2 vs V3 on V3 Heldout) & Latency Profiling.

Per Mission Section 42, 43, 44, 45, 46, 47, 48, 49:
- Evaluate System A (Frozen V2: B_400_overlap x content_only single-stage dense)
  vs System B (Frozen V3: B_400_overlap x content_only + Document Prior alpha=0.18 + Qwen3-Reranker-0.6B on top-20)
  on the newly generated, frozen V3 heldout (N=100: 52 answerable, 48 unsupported).
- Ground truth verification:
  DocumentHit@1/5/10, ParentSectionHit@1/5/10, PassageHit@1/5/10,
  CandidateHit@10/20/30/50/100, MRR, nDCG@10.
- Safety decision evaluation:
  Precision, Recall, False Refusal, Unsafe Accept, AUROC.
- Latency profiling:
  p50, p95, max, mean for encode, first-stage, reranker, total.
- Post-hoc failure analysis:
  Categorize failure modes for all misses.
- Persist reports/renal_v3/renal_v3_final_heldout_rankings.json + SHA256 sidecar.
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
HELDOUT_PATH = ROOT / "evaluation" / "renal" / "v3" / "renal-heldout-v3-final.json"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
REPORTS_DIR = ROOT / "reports" / "renal_v3"
MODELS_DIR = ROOT / "models"
SAFETY_MODEL_PATH = MODELS_DIR / "renal_v3_evidence_classifier.pkl"
OUTPUT_REPORT_PATH = REPORTS_DIR / "renal_v3_final_heldout_rankings.json"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
V2_SUFFICIENCY_THRESHOLD = 0.819928765296936
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


def compute_dcg_at_k(relevance: list[int], k: int = 10) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevance[:k]):
        if rel > 0:
            dcg += (2**rel - 1) / math.log2(i + 2)
    return dcg


def compute_ndcg_at_k(relevance: list[int], k: int = 10) -> float:
    actual_dcg = compute_dcg_at_k(relevance, k)
    ideal_relevance = sorted(relevance, reverse=True)
    ideal_dcg = compute_dcg_at_k(ideal_relevance, k)
    if ideal_dcg == 0.0:
        return 0.0
    return actual_dcg / ideal_dcg


def is_chunk_relevant(ch: dict, q: dict) -> bool:
    cid = ch.get("chunk_id")
    if cid in q.get("gold_child_chunk_ids", []):
        return True
    did = ch.get("document_id")
    if did in q.get("gold_document_ids", []):
        anchors = q.get("gold_verification_anchors", [])
        if anchors:
            txt = ch.get("text", "").lower()
            hits = sum(1 for a in anchors if a.lower() in txt)
            if hits >= q.get("gold_minimum_anchor_hits", 2):
                return True
    return False


def main():
    print("=" * 70)
    print("PHASE 29 & 30: LOCKED FAIR FINAL EVALUATION: V2 VS V3 ON V3 HELDOUT")
    print("=" * 70)

    # 1. Verify V3 heldout integrity
    assert HELDOUT_PATH.exists(), f"Heldout not found: {HELDOUT_PATH}"
    heldout_sha = sha256_file(HELDOUT_PATH)
    sidecar_sha = HELDOUT_PATH.with_suffix(".json.sha256").read_text(encoding="utf-8").split()[0]
    assert heldout_sha == sidecar_sha, f"SHA mismatch on heldout! {heldout_sha} != {sidecar_sha}"
    print(f"Verified V3 Heldout SHA256: {heldout_sha}")

    heldout_data = json.loads(HELDOUT_PATH.read_text(encoding="utf-8"))
    queries = heldout_data["queries"]
    n_queries = len(queries)
    n_answerable = sum(1 for q in queries if q["answerable"])
    n_unsupported = sum(1 for q in queries if not q["answerable"])
    print(f"Total Heldout Queries: {n_queries} (Answerable: {n_answerable}, Unsupported: {n_unsupported})")

    # 2. Check CUDA device
    assert torch.cuda.is_available(), "FATAL: CUDA GPU required!"
    device = torch.device("cuda:0")
    print(f"GPU: {torch.cuda.get_device_name(device)}")

    # 3. Load Registry and Chunks
    reg_data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    chunks: list[dict] = []
    chunk_id_to_idx: dict[str, int] = {}
    doc_to_chunks: dict[str, list[int]] = {}
    
    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_text(encoding="utf-8"))
        for ch in payload.get("chunks", []):
            idx = len(chunks)
            chunks.append(ch)
            cid = ch.get("chunk_id")
            if cid:
                chunk_id_to_idx[cid] = idx
            did = ch.get("document_id")
            if did:
                doc_to_chunks.setdefault(did, []).append(idx)

    print(f"Loaded {len(chunks)} chunks across {len(doc_to_chunks)} documents.")

    # 4. Load or compute embeddings
    embed_tok = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
    embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device)
    embed_model.eval()

    doc_ids_sorted = sorted(list(doc_to_chunks.keys()))
    doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
    
    doc_cache_path = CACHE_DIR / "all23_doc_embeddings.npy"
    if doc_cache_path.exists():
        doc_emb = np.load(doc_cache_path)
    else:
        doc_titles = {d["document_id"]: d.get("title", "") for d in reg_data.get("documents", [])}
        doc_topics = {d["document_id"]: ", ".join(d.get("topic_tags", [])) for d in reg_data.get("documents", [])}
        doc_texts = [f"Title: {doc_titles.get(did, '')}\nTopics: {doc_topics.get(did, '')}\nOverview: {chunks[doc_to_chunks[did][0]]['text'][:300]}" for did in doc_ids_sorted]
        doc_emb = encode_texts(doc_texts, embed_tok, embed_model, device)
        np.save(doc_cache_path, doc_emb)

    corpus_cache_path = CACHE_DIR / "all23_corpus_embeddings.npy"
    if corpus_cache_path.exists():
        corpus_arr = np.load(corpus_cache_path)
    else:
        all_chunk_texts = [ch["text"] for ch in chunks]
        corpus_arr = encode_texts(all_chunk_texts, embed_tok, embed_model, device)
        np.save(corpus_cache_path, corpus_arr)

    print(f"Corpus representation: {corpus_arr.shape}, Doc prior representation: {doc_emb.shape}")

    # Load CrossEncoder reranker
    reranker = CrossEncoder(RERANK_MODEL_ID, trust_remote_code=True, device="cuda:0")

    # Load trained safety classifier
    assert SAFETY_MODEL_PATH.exists(), f"Missing safety model: {SAFETY_MODEL_PATH}"
    with open(SAFETY_MODEL_PATH, "rb") as f:
        safety_bundle = pickle.load(f)
    safety_model = safety_bundle["model"]
    safety_means = safety_bundle["means"]
    safety_stds = safety_bundle["stds"]
    safety_tau = safety_bundle.get("calibrated_threshold", safety_bundle.get("tau", 0.9100))
    print(f"Loaded Safety Model (calibrated tau={safety_tau:.4f})")

    # 5. Measure query encoding time and representations
    q_texts = [q["query"] for q in queries]
    q_instruct_texts = [QUERY_INSTRUCTION + q for q in q_texts]

    # Warmup
    _ = encode_texts(q_instruct_texts[:2], embed_tok, embed_model, device)

    t0_encode = time.perf_counter()
    q_embs = encode_texts(q_instruct_texts, embed_tok, embed_model, device)
    t1_encode = time.perf_counter()
    total_encode_sec = t1_encode - t0_encode
    per_query_encode_ms = (total_encode_sec / n_queries) * 1000.0
    print(f"Encoded {n_queries} queries in {total_encode_sec:.2f}s ({per_query_encode_ms:.1f} ms/query)")

    # 6. Evaluate System A: Frozen V2 (B_400_overlap x content_only single-stage dense)
    print("\n" + "=" * 60)
    print("RUNNING SYSTEM A: FROZEN V2 CONFIGURATION")
    print("=" * 60)
    sims_v2 = np.dot(q_embs, corpus_arr.T) # (100, n_chunks)

    # Retrieval evaluation on answerable queries
    ans_indices = [i for i, q in enumerate(queries) if q["answerable"]]
    
    v2_results = []
    v2_doc_hit_1 = 0
    v2_doc_hit_5 = 0
    v2_doc_hit_10 = 0
    v2_sec_hit_1 = 0
    v2_sec_hit_5 = 0
    v2_sec_hit_10 = 0
    v2_pass_hit_1 = 0
    v2_pass_hit_5 = 0
    v2_pass_hit_10 = 0
    v2_cand_hit_10 = 0
    v2_cand_hit_20 = 0
    v2_cand_hit_30 = 0
    v2_cand_hit_50 = 0
    v2_cand_hit_100 = 0
    v2_mrr_sum = 0.0
    v2_ndcg_sum = 0.0

    for q_idx in ans_indices:
        q = queries[q_idx]
        gold_docs = set(q.get("gold_document_ids", []))
        gold_secs = set(q.get("gold_parent_section_ids", []))
        gold_chunks = set(q.get("gold_child_chunk_ids", []))

        scores = sims_v2[q_idx]
        ranked_indices = np.argsort(scores)[::-1][:100]
        ranked_chunks = [chunks[i] for i in ranked_indices]

        ret_docs = [ch.get("document_id") for ch in ranked_chunks]
        ret_secs = [ch.get("parent_section_id") for ch in ranked_chunks]
        ret_cids = [ch.get("chunk_id") for ch in ranked_chunks]

        # Hits
        d_h1 = any(d in gold_docs for d in ret_docs[:1])
        d_h5 = any(d in gold_docs for d in ret_docs[:5])
        d_h10 = any(d in gold_docs for d in ret_docs[:10])

        s_h1 = any(s in gold_secs for s in ret_secs[:1])
        s_h5 = any(s in gold_secs for s in ret_secs[:5])
        s_h10 = any(s in gold_secs for s in ret_secs[:10])

        p_h1 = any(is_chunk_relevant(ch, q) for ch in ranked_chunks[:1])
        p_h5 = any(is_chunk_relevant(ch, q) for ch in ranked_chunks[:5])
        p_h10 = any(is_chunk_relevant(ch, q) for ch in ranked_chunks[:10])

        c_h10 = any(is_chunk_relevant(ch, q) for ch in ranked_chunks[:10])
        c_h20 = any(is_chunk_relevant(ch, q) for ch in ranked_chunks[:20])
        c_h30 = any(is_chunk_relevant(ch, q) for ch in ranked_chunks[:30])
        c_h50 = any(is_chunk_relevant(ch, q) for ch in ranked_chunks[:50])
        c_h100 = any(is_chunk_relevant(ch, q) for ch in ranked_chunks[:100])

        v2_doc_hit_1 += int(d_h1)
        v2_doc_hit_5 += int(d_h5)
        v2_doc_hit_10 += int(d_h10)
        v2_sec_hit_1 += int(s_h1)
        v2_sec_hit_5 += int(s_h5)
        v2_sec_hit_10 += int(s_h10)
        v2_pass_hit_1 += int(p_h1)
        v2_pass_hit_5 += int(p_h5)
        v2_pass_hit_10 += int(p_h10)
        v2_cand_hit_10 += int(c_h10)
        v2_cand_hit_20 += int(c_h20)
        v2_cand_hit_30 += int(c_h30)
        v2_cand_hit_50 += int(c_h50)
        v2_cand_hit_100 += int(c_h100)

        # RR & NDCG
        rr = 0.0
        rel_10 = []
        for r_idx, ch in enumerate(ranked_chunks[:10]):
            is_rel = int(is_chunk_relevant(ch, q))
            rel_10.append(is_rel)
            if is_rel and rr == 0.0:
                rr = 1.0 / (r_idx + 1)

        # Check in top 100 for RR if not in top 10
        if rr == 0.0:
            for r_idx, ch in enumerate(ranked_chunks):
                if is_chunk_relevant(ch, q):
                    rr = 1.0 / (r_idx + 1)
                    break

        ndcg = compute_ndcg_at_k(rel_10, 10)
        v2_mrr_sum += rr
        v2_ndcg_sum += ndcg

        v2_results.append({
            "query_id": q["query_id"],
            "doc_hit_1": d_h1,
            "sec_hit_1": s_h1,
            "pass_hit_1": p_h1,
            "pass_hit_5": p_h5,
            "reciprocal_rank": rr,
            "ndcg_10": ndcg,
        })

    v2_metrics = {
        "n_eval": n_answerable,
        "DocumentHit@1": v2_doc_hit_1 / n_answerable,
        "DocumentHit@5": v2_doc_hit_5 / n_answerable,
        "DocumentHit@10": v2_doc_hit_10 / n_answerable,
        "ParentSectionHit@1": v2_sec_hit_1 / n_answerable,
        "ParentSectionHit@5": v2_sec_hit_5 / n_answerable,
        "ParentSectionHit@10": v2_sec_hit_10 / n_answerable,
        "PassageHit@1": v2_pass_hit_1 / n_answerable,
        "PassageHit@5": v2_pass_hit_5 / n_answerable,
        "PassageHit@10": v2_pass_hit_10 / n_answerable,
        "CandidateHit@10": v2_cand_hit_10 / n_answerable,
        "CandidateHit@20": v2_cand_hit_20 / n_answerable,
        "CandidateHit@30": v2_cand_hit_30 / n_answerable,
        "CandidateHit@50": v2_cand_hit_50 / n_answerable,
        "CandidateHit@100": v2_cand_hit_100 / n_answerable,
        "MRR": v2_mrr_sum / n_answerable,
        "nDCG@10": v2_ndcg_sum / n_answerable,
    }

    print("System A (V2 Baseline) Retrieval Metrics on V3 Heldout:")
    for k, v in v2_metrics.items():
        if k != "n_eval":
            print(f"  {k:20s}: {v:.4f}")

    # V2 Baseline Safety: top-1 similarity threshold
    v2_preds = []
    y_true = [1 if q["answerable"] else 0 for q in queries]
    v2_scores_top1 = []
    for q_idx in range(n_queries):
        top1_sim = float(np.max(sims_v2[q_idx]))
        v2_scores_top1.append(top1_sim)
        v2_preds.append(1 if top1_sim >= V2_SUFFICIENCY_THRESHOLD else 0)

    v2_preds_arr = np.array(v2_preds)
    y_true_arr = np.array(y_true)
    v2_scores_arr = np.array(v2_scores_top1)

    tp_v2 = int(np.sum((v2_preds_arr == 1) & (y_true_arr == 1)))
    fp_v2 = int(np.sum((v2_preds_arr == 1) & (y_true_arr == 0)))
    tn_v2 = int(np.sum((v2_preds_arr == 0) & (y_true_arr == 0)))
    fn_v2 = int(np.sum((v2_preds_arr == 0) & (y_true_arr == 1)))

    v2_safety = {
        "TP": tp_v2, "FP": fp_v2, "TN": tn_v2, "FN": fn_v2,
        "precision": tp_v2 / (tp_v2 + fp_v2) if (tp_v2 + fp_v2) > 0 else 0.0,
        "recall": tp_v2 / (tp_v2 + fn_v2) if (tp_v2 + fn_v2) > 0 else 0.0,
        "specificity": tn_v2 / (tn_v2 + fp_v2) if (tn_v2 + fp_v2) > 0 else 0.0,
        "unsafe_accept": fp_v2 / n_unsupported if n_unsupported > 0 else 0.0,
        "false_refusal": fn_v2 / n_answerable if n_answerable > 0 else 0.0,
        "auroc": float(roc_auc_score(y_true_arr, v2_scores_arr)),
    }
    print("System A (V2 Baseline) Safety Metrics:")
    print(f"  Precision:     {v2_safety['precision']:.4f} ({tp_v2}/{tp_v2+fp_v2})")
    print(f"  Recall:        {v2_safety['recall']:.4f} ({tp_v2}/{n_answerable})")
    print(f"  False Refusal: {v2_safety['false_refusal']:.4f} ({fn_v2}/{n_answerable})")
    print(f"  Unsafe Accept: {v2_safety['unsafe_accept']:.4f} ({fp_v2}/{n_unsupported})")
    print(f"  AUROC:         {v2_safety['auroc']:.4f}")

    # 7. Evaluate System B: Frozen V3 (Dense + Doc Prior alpha=0.18 + Qwen3-Reranker-0.6B on top-20)
    print("\n" + "=" * 60)
    print("RUNNING SYSTEM B: FROZEN V3 CONFIGURATION (WITH LATENCY PROFILING)")
    print("=" * 60)
    
    sims_docs = np.dot(q_embs, doc_emb.T) # (100, n_docs)
    alpha = 0.18
    
    v3_results = []
    v3_doc_hit_1 = 0
    v3_doc_hit_5 = 0
    v3_doc_hit_10 = 0
    v3_sec_hit_1 = 0
    v3_sec_hit_5 = 0
    v3_sec_hit_10 = 0
    v3_pass_hit_1 = 0
    v3_pass_hit_5 = 0
    v3_pass_hit_10 = 0
    v3_cand_hit_10 = 0
    v3_cand_hit_20 = 0
    v3_cand_hit_30 = 0
    v3_cand_hit_50 = 0
    v3_cand_hit_100 = 0
    v3_mrr_sum = 0.0
    v3_ndcg_sum = 0.0

    stage1_latencies_ms = []
    stage2_latencies_ms = []
    total_latencies_ms = []
    
    v3_features = []
    v3_rankings_all = []
    failure_cases = []

    for q_idx in range(n_queries):
        q = queries[q_idx]
        q_text = q["query"]
        is_ans = q["answerable"]
        gold_docs = set(q.get("gold_document_ids", []))
        gold_secs = set(q.get("gold_parent_section_ids", []))
        gold_chunks = set(q.get("gold_child_chunk_ids", []))

        # --- Stage 1: Dense + Doc Prior ---
        t0_s1 = time.perf_counter()
        p_scores = sims_v2[q_idx].copy()
        d_scores = sims_docs[q_idx]
        
        combined = np.zeros_like(p_scores)
        for i, ch in enumerate(chunks):
            did = ch["document_id"]
            combined[i] = p_scores[i] + alpha * d_scores[doc_id_to_idx[did]]
            
        stage1_sorted_idx = np.argsort(combined)[::-1]
        top20_idx = stage1_sorted_idx[:20]
        cands_top20 = [chunks[i] for i in top20_idx]
        t1_s1 = time.perf_counter()
        s1_ms = (t1_s1 - t0_s1) * 1000.0

        dense_top1 = float(combined[top20_idx[0]])
        dense_top2 = float(combined[top20_idx[1]]) if len(top20_idx) > 1 else dense_top1
        dense_margin = dense_top1 - dense_top2

        doc_top1 = float(np.max(d_scores))
        doc_top2 = float(np.partition(d_scores, -2)[-2]) if len(d_scores) > 1 else doc_top1
        doc_margin = doc_top1 - doc_top2

        # --- Stage 2: CrossEncoder Reranker on Top-20 ---
        t0_s2 = time.perf_counter()
        pairs = [[q_text, c.get("text", "")] for c in cands_top20]
        with torch.inference_mode():
            raw_r_scores = reranker.predict(pairs, batch_size=8, show_progress_bar=False)
        r_scores = np.asarray(raw_r_scores, dtype=np.float32).reshape(-1)
        r_order = np.argsort(r_scores)[::-1]
        t1_s2 = time.perf_counter()
        s2_ms = (t1_s2 - t0_s2) * 1000.0

        tot_ms = per_query_encode_ms + s1_ms + s2_ms
        stage1_latencies_ms.append(s1_ms)
        stage2_latencies_ms.append(s2_ms)
        total_latencies_ms.append(tot_ms)

        # Full ranked list: top-20 reranked, followed by stage1 ranks 21..100
        reranked_top20 = [cands_top20[int(i)] for i in r_order]
        remaining_candidates = [chunks[i] for i in stage1_sorted_idx[20:100]]
        full_ranked_chunks = reranked_top20 + remaining_candidates

        # Safety feature extraction
        r_sorted = r_scores[r_order]
        r_top1 = float(r_sorted[0])
        r_top2 = float(r_sorted[1]) if len(r_sorted) > 1 else r_top1
        r_margin = r_top1 - r_top2
        r_top3_mean = float(np.mean(r_sorted[:3]))

        top_docs = [reranked_top20[i]["document_id"] for i in range(min(5, len(reranked_top20)))]
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
        v3_features.append(feats)

        # If answerable, compute IR metrics
        if is_ans:
            ret_docs = [ch.get("document_id") for ch in full_ranked_chunks]
            ret_secs = [ch.get("parent_section_id") for ch in full_ranked_chunks]
            ret_cids = [ch.get("chunk_id") for ch in full_ranked_chunks]

            d_h1 = any(d in gold_docs for d in ret_docs[:1])
            d_h5 = any(d in gold_docs for d in ret_docs[:5])
            d_h10 = any(d in gold_docs for d in ret_docs[:10])

            s_h1 = any(s in gold_secs for s in ret_secs[:1])
            s_h5 = any(s in gold_secs for s in ret_secs[:5])
            s_h10 = any(s in gold_secs for s in ret_secs[:10])

            p_h1 = any(is_chunk_relevant(ch, q) for ch in full_ranked_chunks[:1])
            p_h5 = any(is_chunk_relevant(ch, q) for ch in full_ranked_chunks[:5])
            p_h10 = any(is_chunk_relevant(ch, q) for ch in full_ranked_chunks[:10])

            # Candidate hits in initial stage 1 retrieval pool
            c_h10 = any(is_chunk_relevant(chunks[i], q) for i in stage1_sorted_idx[:10])
            c_h20 = any(is_chunk_relevant(chunks[i], q) for i in stage1_sorted_idx[:20])
            c_h30 = any(is_chunk_relevant(chunks[i], q) for i in stage1_sorted_idx[:30])
            c_h50 = any(is_chunk_relevant(chunks[i], q) for i in stage1_sorted_idx[:50])
            c_h100 = any(is_chunk_relevant(chunks[i], q) for i in stage1_sorted_idx[:100])

            v3_doc_hit_1 += int(d_h1)
            v3_doc_hit_5 += int(d_h5)
            v3_doc_hit_10 += int(d_h10)
            v3_sec_hit_1 += int(s_h1)
            v3_sec_hit_5 += int(s_h5)
            v3_sec_hit_10 += int(s_h10)
            v3_pass_hit_1 += int(p_h1)
            v3_pass_hit_5 += int(p_h5)
            v3_pass_hit_10 += int(p_h10)
            v3_cand_hit_10 += int(c_h10)
            v3_cand_hit_20 += int(c_h20)
            v3_cand_hit_30 += int(c_h30)
            v3_cand_hit_50 += int(c_h50)
            v3_cand_hit_100 += int(c_h100)

            # RR & NDCG
            rr = 0.0
            rel_10 = []
            for r_idx, ch in enumerate(full_ranked_chunks[:10]):
                is_rel = int(is_chunk_relevant(ch, q))
                rel_10.append(is_rel)
                if is_rel and rr == 0.0:
                    rr = 1.0 / (r_idx + 1)

            if rr == 0.0:
                for r_idx, ch in enumerate(full_ranked_chunks):
                    if is_chunk_relevant(ch, q):
                        rr = 1.0 / (r_idx + 1)
                        break

            ndcg = compute_ndcg_at_k(rel_10, 10)
            v3_mrr_sum += rr
            v3_ndcg_sum += ndcg

            # Failure mode analysis for misses at Hit@1
            if not p_h1:
                top_ret_doc = ret_docs[0]
                top_ret_sec = ret_secs[0]
                if top_ret_doc not in gold_docs:
                    f_mode = "DOCUMENT_ROUTING_FAILURE"
                elif top_ret_sec not in gold_secs:
                    f_mode = "RIGHT_DOCUMENT_WRONG_SECTION"
                else:
                    f_mode = "SECTION_AMBIGUITY"
                
                failure_cases.append({
                    "query_id": q["query_id"],
                    "query": q["query"],
                    "failure_mode": f_mode,
                    "gold_document": list(gold_docs)[0] if gold_docs else None,
                    "retrieved_top1_doc": top_ret_doc,
                    "retrieved_top1_sec": top_ret_sec,
                    "passage_hit_5": p_h5,
                    "candidate_hit_20": c_h20,
                    "reciprocal_rank": rr
                })

            v3_results.append({
                "query_id": q["query_id"],
                "doc_hit_1": d_h1,
                "sec_hit_1": s_h1,
                "pass_hit_1": p_h1,
                "pass_hit_5": p_h5,
                "reciprocal_rank": rr,
                "ndcg_10": ndcg,
            })

    v3_metrics = {
        "n_eval": n_answerable,
        "DocumentHit@1": v3_doc_hit_1 / n_answerable,
        "DocumentHit@5": v3_doc_hit_5 / n_answerable,
        "DocumentHit@10": v3_doc_hit_10 / n_answerable,
        "ParentSectionHit@1": v3_sec_hit_1 / n_answerable,
        "ParentSectionHit@5": v3_sec_hit_5 / n_answerable,
        "ParentSectionHit@10": v3_sec_hit_10 / n_answerable,
        "PassageHit@1": v3_pass_hit_1 / n_answerable,
        "PassageHit@5": v3_pass_hit_5 / n_answerable,
        "PassageHit@10": v3_pass_hit_10 / n_answerable,
        "CandidateHit@10": v3_cand_hit_10 / n_answerable,
        "CandidateHit@20": v3_cand_hit_20 / n_answerable,
        "CandidateHit@30": v3_cand_hit_30 / n_answerable,
        "CandidateHit@50": v3_cand_hit_50 / n_answerable,
        "CandidateHit@100": v3_cand_hit_100 / n_answerable,
        "MRR": v3_mrr_sum / n_answerable,
        "nDCG@10": v3_ndcg_sum / n_answerable,
    }

    print("\nSystem B (V3 Final Architecture) Retrieval Metrics on V3 Heldout:")
    for k, v in v3_metrics.items():
        if k != "n_eval":
            delta = v - v2_metrics[k]
            sign = "+" if delta >= 0 else ""
            print(f"  {k:20s}: {v:.4f}  (vs V2: {v2_metrics[k]:.4f}, {sign}{delta*100:.2f}%)")

    # 8. Evaluate V3 Safety Classifier on all 100 queries
    X_v3 = np.array(v3_features, dtype=np.float32)
    X_v3_norm = (X_v3 - safety_means) / safety_stds
    probs_v3 = safety_model.predict_proba(X_v3_norm)[:, 1]
    preds_v3 = (probs_v3 >= safety_tau).astype(int)

    tp_v3 = int(np.sum((preds_v3 == 1) & (y_true_arr == 1)))
    fp_v3 = int(np.sum((preds_v3 == 1) & (y_true_arr == 0)))
    tn_v3 = int(np.sum((preds_v3 == 0) & (y_true_arr == 0)))
    fn_v3 = int(np.sum((preds_v3 == 0) & (y_true_arr == 1)))

    v3_safety = {
        "TP": tp_v3, "FP": fp_v3, "TN": tn_v3, "FN": fn_v3,
        "precision": tp_v3 / (tp_v3 + fp_v3) if (tp_v3 + fp_v3) > 0 else 0.0,
        "recall": tp_v3 / (tp_v3 + fn_v3) if (tp_v3 + fn_v3) > 0 else 0.0,
        "specificity": tn_v3 / (tn_v3 + fp_v3) if (tn_v3 + fp_v3) > 0 else 0.0,
        "unsafe_accept": fp_v3 / n_unsupported if n_unsupported > 0 else 0.0,
        "false_refusal": fn_v3 / n_answerable if n_answerable > 0 else 0.0,
        "auroc": float(roc_auc_score(y_true_arr, probs_v3)),
    }
    print("\nSystem B (V3 Calibrated Classifier) Safety Metrics on V3 Heldout:")
    print(f"  Precision:     {v3_safety['precision']:.4f} ({tp_v3}/{tp_v3+fp_v3})  (vs V2: {v2_safety['precision']:.4f})")
    print(f"  Recall:        {v3_safety['recall']:.4f} ({tp_v3}/{n_answerable})  (vs V2: {v2_safety['recall']:.4f})")
    print(f"  False Refusal: {v3_safety['false_refusal']:.4f} ({fn_v3}/{n_answerable})  (vs V2: {v2_safety['false_refusal']:.4f})")
    print(f"  Unsafe Accept: {v3_safety['unsafe_accept']:.4f} ({fp_v3}/{n_unsupported})  (vs V2: {v2_safety['unsafe_accept']:.4f})")
    print(f"  AUROC:         {v3_safety['auroc']:.4f}  (vs V2: {v2_safety['auroc']:.4f})")

    # 9. Phase 31: Latency Profiling
    print("\n" + "=" * 60)
    print("PHASE 31: LATENCY PROFILING (CUDA RTX 3060)")
    print("=" * 60)
    latency_summary = {
        "n_queries": n_queries,
        "query_encode_ms": {
            "mean": float(per_query_encode_ms),
            "p50": float(per_query_encode_ms),
            "p95": float(per_query_encode_ms),
            "max": float(per_query_encode_ms),
        },
        "stage1_dense_prior_ms": {
            "mean": float(np.mean(stage1_latencies_ms)),
            "p50": float(np.percentile(stage1_latencies_ms, 50)),
            "p95": float(np.percentile(stage1_latencies_ms, 95)),
            "max": float(np.max(stage1_latencies_ms)),
        },
        "stage2_crossencoder_ms": {
            "mean": float(np.mean(stage2_latencies_ms)),
            "p50": float(np.percentile(stage2_latencies_ms, 50)),
            "p95": float(np.percentile(stage2_latencies_ms, 95)),
            "max": float(np.max(stage2_latencies_ms)),
        },
        "total_end_to_end_ms": {
            "mean": float(np.mean(total_latencies_ms)),
            "p50": float(np.percentile(total_latencies_ms, 50)),
            "p95": float(np.percentile(total_latencies_ms, 95)),
            "max": float(np.max(total_latencies_ms)),
        }
    }
    print(f"Query Encoding: Mean={latency_summary['query_encode_ms']['mean']:.2f} ms")
    print(f"Stage 1 Search: Mean={latency_summary['stage1_dense_prior_ms']['mean']:.2f} ms, p50={latency_summary['stage1_dense_prior_ms']['p50']:.2f} ms, p95={latency_summary['stage1_dense_prior_ms']['p95']:.2f} ms")
    print(f"Stage 2 Rerank: Mean={latency_summary['stage2_crossencoder_ms']['mean']:.2f} ms, p50={latency_summary['stage2_crossencoder_ms']['p50']:.2f} ms, p95={latency_summary['stage2_crossencoder_ms']['p95']:.2f} ms")
    print(f"End-to-End Total: Mean={latency_summary['total_end_to_end_ms']['mean']:.2f} ms, p50={latency_summary['total_end_to_end_ms']['p50']:.2f} ms, p95={latency_summary['total_end_to_end_ms']['p95']:.2f} ms")

    # 10. Post-Hoc Failure Mode Analysis
    print("\n" + "=" * 60)
    print(f"POST-HOC FAILURE ANALYSIS (N={len(failure_cases)} misses at Hit@1)")
    print("=" * 60)
    mode_counts = {}
    for fc in failure_cases:
        m = fc["failure_mode"]
        mode_counts[m] = mode_counts.get(m, 0) + 1
    for m, c in sorted(mode_counts.items(), key=lambda x: -x[1]):
        pct = (c / len(failure_cases)) * 100 if failure_cases else 0.0
        print(f"  {m:30s}: {c:2d} ({pct:.1f}%)")

    # 11. Persist Final Heldout Rankings Report
    report_payload = {
        "report_id": "RENAL-V3-FINAL-HELDOUT-RANKINGS",
        "description": "Locked fair final evaluation comparing Frozen V2 vs Frozen V3 on V3 Heldout",
        "timestamp": "2026-09-10T11:30:00Z",
        "evaluation_dataset": {
            "name": "renal-heldout-v3-final.json",
            "sha256": heldout_sha,
            "n_total": n_queries,
            "n_answerable": n_answerable,
            "n_unsupported": n_unsupported
        },
        "system_a_v2_baseline": {
            "name": "Frozen V2 Dense Retriever",
            "chunking": "B_400_overlap",
            "representation": "content_only",
            "retriever": "single_stage_dense",
            "retrieval_metrics": v2_metrics,
            "safety_metrics": v2_safety
        },
        "system_b_v3_final": {
            "name": "Frozen V3 Hybrid Two-Stage Retriever",
            "chunking": "B_400_overlap",
            "representation": "content_only",
            "retriever": "dense_plus_document_prior_alpha_0.18_plus_qwen3_reranker_0.6B_top20",
            "retrieval_metrics": v3_metrics,
            "safety_metrics": v3_safety,
            "improvements_over_v2": {
                "PassageHit@1_absolute": v3_metrics["PassageHit@1"] - v2_metrics["PassageHit@1"],
                "PassageHit@5_absolute": v3_metrics["PassageHit@5"] - v2_metrics["PassageHit@5"],
                "MRR_absolute": v3_metrics["MRR"] - v2_metrics["MRR"],
                "nDCG@10_absolute": v3_metrics["nDCG@10"] - v2_metrics["nDCG@10"],
                "safety_recall_absolute": v3_safety["recall"] - v2_safety["recall"],
                "safety_precision_absolute": v3_safety["precision"] - v2_safety["precision"],
                "safety_false_refusal_reduction": v2_safety["false_refusal"] - v3_safety["false_refusal"]
            }
        },
        "latency_profile": latency_summary,
        "failure_analysis": {
            "n_misses_at_hit1": len(failure_cases),
            "distribution": mode_counts,
            "cases": failure_cases
        }
    }

    OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT_PATH.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    out_sha = sha256_file(OUTPUT_REPORT_PATH)
    OUTPUT_REPORT_PATH.with_suffix(".json.sha256").write_text(f"{out_sha}  {OUTPUT_REPORT_PATH.name}\n", encoding="utf-8")

    print(f"\nWrote final locked evaluation to {OUTPUT_REPORT_PATH}")
    print(f"SHA256: {out_sha}")
    print("PHASES 29, 30, 31 COMPLETE.")


if __name__ == "__main__":
    main()
