"""Phase 13, 14 & 15: Structural Representations, Soft Fusion Trained on TRAIN, and DEV Selection.

Per Mission Section 19, 20, 21, 22, 23:
1. Phase 13: Build Document and Section representations & encode on GPU.
2. Phase 14: Fit soft fusion model strictly on TRAIN (never DEV).
3. Phase 15: Evaluate on DEV:
   - Flat Dense Baseline
   - Hard Hierarchical Cascade (Diagnostic only per Section 23)
   - Global Dense + Document Prior
   - Global Dense + Section Prior
   - Global Dense + Document + Section Soft Fusion
4. Save report to reports/renal_v3/renal_v3_structural_fusion.json.
"""
from __future__ import annotations

import hashlib
import json
import pickle
import sys
import time
from pathlib import Path
import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from transformers import AutoModel, AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent
TRAIN_PATH = ROOT / "evaluation" / "renal" / "v3" / "renal-train-v3.json"
DEV_QRELS = ROOT / "evaluation" / "renal" / "v3" / "renal-dev-v3-qrels.json"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
REPORTS_DIR = ROOT / "reports" / "renal_v3"
MODELS_DIR = ROOT / "models"

MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
MODEL_REVISION = "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3"
BATCH_SIZE = 16


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def encode_texts(texts: list[str], tokenizer, model, device: torch.device) -> np.ndarray:
    all_embeddings = []
    batch_size = BATCH_SIZE
    n = len(texts)
    
    with torch.inference_mode():
        for i in range(0, n, batch_size):
            batch = texts[i : i + batch_size]
            encoded = tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
            outputs = model(**encoded)
            mask = encoded["attention_mask"].unsqueeze(-1)
            emb = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            emb = torch.nn.functional.normalize(emb, p=2, dim=1)
            all_embeddings.append(emb.cpu().numpy())
    return np.vstack(all_embeddings).astype(np.float32)


def main():
    print("=" * 70)
    print("PHASE 13, 14, 15: STRUCTURAL ENCODING, TRAIN FUSION & DEV SELECTION")
    print("=" * 70)
    
    if not torch.cuda.is_available():
        print("HARD GATE FAILED: CUDA not available.")
        sys.exit(1)
        
    device = torch.device("cuda:0")
    print(f"Device: {torch.cuda.get_device_name(0)}")
    
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Registry & Corpus Chunks (DEV 21 documents)
    reg_data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    doc_titles = {d["document_id"]: d.get("title", "") for d in reg_data.get("documents", [])}
    doc_topics = {d["document_id"]: ", ".join(d.get("topic_tags", [])) for d in reg_data.get("documents", [])}
    
    chunks = []
    doc_to_chunks = {}
    sec_to_chunks = {}
    sections_info = {}
    doc_first_text = {}
    
    for f in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        doc_id = f.name.replace(".chunks.json", "")
        if doc_id in ("DOC-PMC-RENAL-0024", "DOC-PMC-RENAL-0025"):
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for ch in data.get("chunks", []):
            chunks.append(ch)
            doc_to_chunks.setdefault(doc_id, []).append(len(chunks) - 1)
            pid = ch.get("parent_section_id")
            if pid:
                sec_to_chunks.setdefault(pid, []).append(len(chunks) - 1)
                if pid not in sections_info:
                    sections_info[pid] = {
                        "parent_section_id": pid,
                        "document_id": doc_id,
                        "heading": ch.get("heading", ""),
                        "section_path": ch.get("section_path", []),
                        "sample_text": ch.get("text", "")[:400]
                    }
            if doc_id not in doc_first_text:
                doc_first_text[doc_id] = ch.get("text", "")[:400]
                
    doc_ids_sorted = sorted(list(doc_to_chunks.keys()))
    sec_ids_sorted = sorted(list(sections_info.keys()))
    
    print(f"Loaded DEV corpus: {len(doc_ids_sorted)} documents, {len(sec_ids_sorted)} sections, {len(chunks)} chunks.")
    
    # 2. Render Document and Section representations
    doc_texts = [f"Title: {doc_titles.get(did, '')}\nTopics: {doc_topics.get(did, '')}\nOverview: {doc_first_text.get(did, '')}" for did in doc_ids_sorted]
    sec_texts = [f"Document: {doc_titles.get(sections_info[sid]['document_id'], '')}\nSection: {' > '.join(sections_info[sid]['section_path'])}\nHeading: {sections_info[sid]['heading']}\nContent: {sections_info[sid]['sample_text']}" for sid in sec_ids_sorted]
    
    # 3. Encode or Load Cached Document & Section Embeddings
    doc_cache_path = CACHE_DIR / "dev_doc_embeddings.npy"
    sec_cache_path = CACHE_DIR / "dev_sec_embeddings.npy"
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION, trust_remote_code=True)
    model = AutoModel.from_pretrained(MODEL_ID, revision=MODEL_REVISION, trust_remote_code=True, torch_dtype=torch.float16).to(device).eval()
    
    if doc_cache_path.exists():
        doc_embeddings = np.load(doc_cache_path)
    else:
        print(f"Encoding {len(doc_texts)} document representations...")
        doc_embeddings = encode_texts(doc_texts, tokenizer, model, device)
        np.save(doc_cache_path, doc_embeddings)
        
    if sec_cache_path.exists():
        sec_embeddings = np.load(sec_cache_path)
    else:
        print(f"Encoding {len(sec_texts)} section representations...")
        sec_embeddings = encode_texts(sec_texts, tokenizer, model, device)
        np.save(sec_cache_path, sec_embeddings)
        
    print(f"Doc embeddings: {doc_embeddings.shape}, Sec embeddings: {sec_embeddings.shape}")
    
    # Load corpus chunks embedding
    v2_cache = ROOT / "Data" / "experiments" / "renal_v2" / "cache"
    corpus_arr = None
    dev_query_arr = None
    for f in v2_cache.glob("*.json"):
        meta = json.loads(f.read_text(encoding="utf-8"))
        if meta.get("kind") == "queries":
            dev_query_arr = np.load(v2_cache / f"{meta['cache_key']}.npy")
        elif meta.get("chunking") == "B_400_overlap" and meta.get("representation") == "content_only":
            corpus_arr = np.load(v2_cache / f"{meta['cache_key']}.npy")
            
    # Load TRAIN queries
    train_data = json.loads(TRAIN_PATH.read_text(encoding="utf-8"))
    train_ans = [q for q in train_data["queries"] if q.get("answerable")]
    print(f"Loaded {len(train_ans)} answerable TRAIN queries for soft fusion fitting.")
    
    train_query_texts = [q["query"] for q in train_ans]
    print(f"Encoding {len(train_query_texts)} TRAIN queries...")
    train_query_arr = encode_texts(train_query_texts, tokenizer, model, device)
    
    # 4. PHASE 14: Fit Soft Fusion Model STRICTLY ON TRAIN
    print("\n" + "=" * 60)
    print("PHASE 14: FITTING SOFT FUSION MODEL ON TRAIN (ZERO DEV EXPOSURE)")
    print("=" * 60)
    
    # Compute similarity matrices for TRAIN:
    # train_query_arr: (40, 1024)
    # corpus_arr: (2558, 1024)
    # doc_embeddings: (21, 1024)
    # sec_embeddings: (2535, 1024)
    
    train_sims_chunks = np.dot(train_query_arr, corpus_arr.T) # (40, 2558)
    train_sims_docs = np.dot(train_query_arr, doc_embeddings.T) # (40, 21)
    train_sims_secs = np.dot(train_query_arr, sec_embeddings.T) # (40, 2535)
    
    doc_id_to_idx = {did: idx for idx, did in enumerate(doc_ids_sorted)}
    sec_id_to_idx = {sid: idx for idx, sid in enumerate(sec_ids_sorted)}
    
    X_train = []
    y_train = []
    
    for q_idx, q in enumerate(train_ans):
        gold_chunks = set(q.get("gold_child_chunk_ids", []))
        # Top 30 passage candidates from global dense
        scores = train_sims_chunks[q_idx]
        top30_idx = np.argsort(scores)[::-1][:30]
        
        # doc scores for this query
        doc_scores = train_sims_docs[q_idx]
        top_doc_idx = np.argsort(doc_scores)[::-1]
        doc_ranks = {doc_ids_sorted[d_idx]: r for r, d_idx in enumerate(top_doc_idx, start=1)}
        doc_top1_score = doc_scores[top_doc_idx[0]]
        doc_top2_score = doc_scores[top_doc_idx[1]] if len(top_doc_idx) > 1 else doc_top1_score
        
        # sec scores for this query
        sec_scores = train_sims_secs[q_idx]
        top_sec_idx = np.argsort(sec_scores)[::-1]
        sec_ranks = {sec_ids_sorted[s_idx]: r for r, s_idx in enumerate(top_sec_idx, start=1)}
        sec_top1_score = sec_scores[top_sec_idx[0]]
        sec_top2_score = sec_scores[top_sec_idx[1]] if len(top_sec_idx) > 1 else sec_top1_score
        
        top1_p_score = scores[top30_idx[0]]
        top2_p_score = scores[top30_idx[1]] if len(top30_idx) > 1 else top1_p_score
        
        for p_rank, c_idx in enumerate(top30_idx, start=1):
            ch = chunks[c_idx]
            cid = ch["chunk_id"]
            did = ch["document_id"]
            pid = ch.get("parent_section_id")
            
            p_score = float(scores[c_idx])
            d_score = float(doc_scores[doc_id_to_idx[did]]) if did in doc_id_to_idx else 0.0
            s_score = float(sec_scores[sec_id_to_idx[pid]]) if pid in sec_id_to_idx else 0.0
            
            d_rank = doc_ranks.get(did, 21)
            s_rank = sec_ranks.get(pid, len(sec_ids_sorted))
            
            feat = [
                p_score,                          # passage similarity
                d_score,                          # document similarity
                s_score,                          # section similarity
                1.0 / p_rank,                     # passage rank inv
                1.0 / d_rank,                     # doc rank inv
                1.0 / s_rank,                     # sec rank inv
                p_score - top2_p_score,           # passage margin
                d_score - doc_top2_score,         # doc margin
                s_score - sec_top2_score,         # sec margin
            ]
            
            is_gold = 1 if cid in gold_chunks else 0
            X_train.append(feat)
            y_train.append(is_gold)
            
    X_train = np.array(X_train, dtype=np.float32)
    y_train = np.array(y_train, dtype=np.int32)
    print(f"X_train shape: {X_train.shape}, Positives: {np.sum(y_train)}, Negatives: {len(y_train) - np.sum(y_train)}")
    
    # Train regularized Logistic Regression scoring model
    fusion_model = LogisticRegression(C=1.0, max_iter=500, random_state=42, class_weight="balanced")
    fusion_model.fit(X_train, y_train)
    
    print("Learned feature weights:")
    feature_names = [
        "passage_sim", "doc_sim", "sec_sim",
        "passage_rank_inv", "doc_rank_inv", "sec_rank_inv",
        "passage_margin", "doc_margin", "sec_margin"
    ]
    for name, weight in zip(feature_names, fusion_model.coef_[0]):
        print(f"  {name:<20}: {weight:>+8.4f}")
    print(f"  Intercept: {fusion_model.intercept_[0]:>+8.4f}")
    
    # Save model
    model_save_path = MODELS_DIR / "renal_v3_soft_fusion.pkl"
    with open(model_save_path, "wb") as f:
        pickle.dump({
            "model": fusion_model,
            "feature_names": feature_names,
            "fitted_on": "RENAL-TRAIN-V3 (N=40)",
            "timestamp": time.time()
        }, f)
    print(f"Saved soft fusion model to {model_save_path}")
    
    # 5. PHASE 15: EVALUATE & SELECT ON DEV (N=69)
    print("\n" + "=" * 60)
    print("PHASE 15: DEV EVALUATION & SELECTION (FROZEN V3 QRELS, N=69)")
    print("=" * 60)
    
    qrels_data = json.loads(DEV_QRELS.read_text(encoding="utf-8"))
    dev_queries = [q for q in qrels_data["queries"] if q.get("answerable")]
    n_dev = len(dev_queries)
    
    # DEV similarity matrices
    dev_sims_chunks = np.dot(dev_query_arr, corpus_arr.T) # (69, 2558)
    dev_sims_docs = np.dot(dev_query_arr, doc_embeddings.T) # (69, 21)
    dev_sims_secs = np.dot(dev_query_arr, sec_embeddings.T) # (69, 2535)
    
    # Helper to evaluate rankings
    def eval_rankings(rankings: list[list[dict]]) -> dict:
        hits = {1: 0, 3: 0, 5: 0, 10: 0}
        cands = {10: 0, 20: 0, 30: 0, 50: 0, 100: 0}
        p_hits = {1: 0, 3: 0, 5: 0, 10: 0}
        d_hits = {1: 0, 3: 0, 5: 0, 10: 0}
        rr_list = []
        ndcg_list = []
        
        for q_idx, q in enumerate(dev_queries):
            gold_chunks = set(q.get("gold_child_chunk_ids", []))
            gold_parents = set(q.get("gold_parent_section_ids", []))
            gold_docs = set(q.get("gold_document_ids", []))
            
            ranked = rankings[q_idx]
            
            for k in [1, 3, 5, 10]:
                if any(item.get("document_id") in gold_docs for item in ranked[:k]):
                    d_hits[k] += 1
                if any(item.get("parent_section_id") in gold_parents for item in ranked[:k]):
                    p_hits[k] += 1
                    
            first_rel_rank = None
            for r, item in enumerate(ranked[:10], start=1):
                if item.get("chunk_id") in gold_chunks:
                    if first_rel_rank is None:
                        first_rel_rank = r
                    for k in [1, 3, 5, 10]:
                        if r <= k:
                            hits[k] += 1
                    break
                    
            if first_rel_rank is not None:
                rr_list.append(1.0 / first_rel_rank)
                ndcg_list.append(1.0 / np.log2(first_rel_rank + 1))
            else:
                rr_list.append(0.0)
                ndcg_list.append(0.0)
                
            for ck in [10, 20, 30, 50, 100]:
                if any(item.get("chunk_id") in gold_chunks for item in ranked[:ck]):
                    cands[ck] += 1
                    
        return {
            "hit_at_1": hits[1] / n_dev,
            "hit_at_3": hits[3] / n_dev,
            "hit_at_5": hits[5] / n_dev,
            "hit_at_10": hits[10] / n_dev,
            "parent_hit_at_1": p_hits[1] / n_dev,
            "parent_hit_at_5": p_hits[5] / n_dev,
            "doc_hit_at_1": d_hits[1] / n_dev,
            "doc_hit_at_10": d_hits[10] / n_dev,
            "candidate_hit_at_50": cands[50] / n_dev,
            "mrr": float(np.mean(rr_list)),
            "ndcg_at_10": float(np.mean(ndcg_list))
        }

    # Configuration 1: Flat Dense Baseline
    rankings_flat = []
    for q_idx in range(n_dev):
        scores = dev_sims_chunks[q_idx]
        top_idx = np.argsort(scores)[::-1][:100]
        rankings_flat.append([chunks[i] for i in top_idx])
    m_flat = eval_rankings(rankings_flat)
    
    # Configuration 2: Hard Hierarchical Cascade (Diagnostic only per Section 23)
    # Top 3 docs -> Top 5 sections per doc -> passages
    rankings_hard = []
    for q_idx in range(n_dev):
        top_d_idx = np.argsort(dev_sims_docs[q_idx])[::-1][:3]
        allowed_docs = set(doc_ids_sorted[i] for i in top_d_idx)
        
        # filtered chunks
        cand_chunks = [ch for ch in chunks if ch["document_id"] in allowed_docs]
        cand_indices = [i for i, ch in enumerate(chunks) if ch["document_id"] in allowed_docs]
        cand_scores = dev_sims_chunks[q_idx, cand_indices]
        
        top_cand_idx = np.argsort(cand_scores)[::-1][:100]
        rankings_hard.append([cand_chunks[i] for i in top_cand_idx])
    m_hard = eval_rankings(rankings_hard)
    
    # Configuration 3: Global Dense + Document Prior (soft additive)
    # Score = passage_score + alpha * doc_score
    rankings_doc_prior = []
    alpha_doc = 0.15
    for q_idx in range(n_dev):
        p_scores = dev_sims_chunks[q_idx].copy()
        d_scores = dev_sims_docs[q_idx]
        combined = np.zeros_like(p_scores)
        for i, ch in enumerate(chunks):
            did = ch["document_id"]
            d_s = d_scores[doc_id_to_idx[did]] if did in doc_id_to_idx else 0.0
            combined[i] = p_scores[i] + alpha_doc * d_s
        top_idx = np.argsort(combined)[::-1][:100]
        rankings_doc_prior.append([chunks[i] for i in top_idx])
    m_doc_prior = eval_rankings(rankings_doc_prior)
    
    # Configuration 4: Global Dense + Section Prior (soft additive)
    # Score = passage_score + beta * sec_score
    rankings_sec_prior = []
    beta_sec = 0.20
    for q_idx in range(n_dev):
        p_scores = dev_sims_chunks[q_idx].copy()
        s_scores = dev_sims_secs[q_idx]
        combined = np.zeros_like(p_scores)
        for i, ch in enumerate(chunks):
            pid = ch.get("parent_section_id")
            s_s = s_scores[sec_id_to_idx[pid]] if pid in sec_id_to_idx else 0.0
            combined[i] = p_scores[i] + beta_sec * s_s
        top_idx = np.argsort(combined)[::-1][:100]
        rankings_sec_prior.append([chunks[i] for i in top_idx])
    m_sec_prior = eval_rankings(rankings_sec_prior)
    
    # Configuration 5: Global Dense + Soft Fusion (Trained Logistic Regression)
    # Reranks Top-50 global candidates using TRAIN-learned model
    rankings_soft_fusion = []
    for q_idx in range(n_dev):
        scores = dev_sims_chunks[q_idx]
        top50_idx = np.argsort(scores)[::-1][:50]
        
        doc_scores = dev_sims_docs[q_idx]
        top_doc_idx = np.argsort(doc_scores)[::-1]
        doc_ranks = {doc_ids_sorted[d_idx]: r for r, d_idx in enumerate(top_doc_idx, start=1)}
        doc_top2_score = doc_scores[top_doc_idx[1]] if len(top_doc_idx) > 1 else doc_scores[top_doc_idx[0]]
        
        sec_scores = dev_sims_secs[q_idx]
        top_sec_idx = np.argsort(sec_scores)[::-1]
        sec_ranks = {sec_ids_sorted[s_idx]: r for r, s_idx in enumerate(top_sec_idx, start=1)}
        sec_top2_score = sec_scores[top_sec_idx[1]] if len(top_sec_idx) > 1 else sec_scores[top_sec_idx[0]]
        
        top2_p_score = scores[top50_idx[1]] if len(top50_idx) > 1 else scores[top50_idx[0]]
        
        cand_feats = []
        for p_rank, c_idx in enumerate(top50_idx, start=1):
            ch = chunks[c_idx]
            did = ch["document_id"]
            pid = ch.get("parent_section_id")
            
            p_score = float(scores[c_idx])
            d_score = float(doc_scores[doc_id_to_idx[did]]) if did in doc_id_to_idx else 0.0
            s_score = float(sec_scores[sec_id_to_idx[pid]]) if pid in sec_id_to_idx else 0.0
            
            d_rank = doc_ranks.get(did, 21)
            s_rank = sec_ranks.get(pid, len(sec_ids_sorted))
            
            cand_feats.append([
                p_score,
                d_score,
                s_score,
                1.0 / p_rank,
                1.0 / d_rank,
                1.0 / s_rank,
                p_score - top2_p_score,
                d_score - doc_top2_score,
                s_score - sec_top2_score,
            ])
            
        cand_feats = np.array(cand_feats, dtype=np.float32)
        # Score via probability of relevant class
        rerank_scores = fusion_model.predict_proba(cand_feats)[:, 1]
        rerank_order = np.argsort(rerank_scores)[::-1]
        
        ranked_50 = [chunks[top50_idx[i]] for i in rerank_order]
        # Append remaining candidates beyond 50
        remaining = [chunks[i] for i in np.argsort(scores)[::-1][50:100]]
        rankings_soft_fusion.append(ranked_50 + remaining)
        
    m_soft_fusion = eval_rankings(rankings_soft_fusion)
    
    # 6. Comparison Table
    print("\n" + "=" * 95)
    print("PHASE 15 DEV ARCHITECTURE COMPARISON TABLE (N=69)")
    print("=" * 95)
    print(f"{'Configuration':<35} {'H@1':>6} {'H@3':>6} {'H@5':>6} {'H@10':>6} {'MRR':>7} {'nDCG':>7} {'Cand@50':>8} {'Status'}")
    print("-" * 95)
    
    configs = [
        ("Flat Dense Baseline", m_flat, "BASELINE"),
        ("Hard Hierarchical Cascade (Diag)", m_hard, "DISCARD (destroys recall)" if m_hard["hit_at_1"] < m_flat["hit_at_1"] else "CHECK"),
        ("Global Dense + Document Prior", m_doc_prior, "TESTED"),
        ("Global Dense + Section Prior", m_sec_prior, "TESTED"),
        ("Global Dense + Soft Fusion (TRAIN)", m_soft_fusion, "WINNER" if m_soft_fusion["hit_at_1"] >= m_flat["hit_at_1"] else "DISCARD"),
    ]
    
    for name, m, status in configs:
        print(f"{name:<35} {m['hit_at_1']:>6.4f} {m['hit_at_3']:>6.4f} {m['hit_at_5']:>6.4f} {m['hit_at_10']:>6.4f} {m['mrr']:>7.4f} {m['ndcg_at_10']:>7.4f} {m['candidate_hit_at_50']:>8.4f} {status}")
        
    # Save report
    out_payload = {
        "report_id": "RENAL-V3-STRUCTURAL-FUSION-SELECTION",
        "description": "Controlled evaluation of structural priors and soft fusion trained on TRAIN",
        "dataset_name": "RENAL-DEV-V3-QRELS",
        "n_queries": n_dev,
        "results": {
            "flat_dense_baseline": m_flat,
            "hard_hierarchical_cascade": m_hard,
            "dense_plus_document_prior": m_doc_prior,
            "dense_plus_section_prior": m_sec_prior,
            "dense_plus_soft_fusion": m_soft_fusion
        },
        "soft_fusion_model": {
            "model_type": "LogisticRegression (L2)",
            "trained_on": "RENAL-TRAIN-V3",
            "n_train_samples": len(X_train),
            "feature_weights": dict(zip(feature_names, [float(w) for w in fusion_model.coef_[0]])),
            "intercept": float(fusion_model.intercept_[0])
        }
    }
    
    report_path = REPORTS_DIR / "renal_v3_structural_fusion.json"
    report_path.write_text(json.dumps(out_payload, indent=2), encoding="utf-8")
    print(f"\nWrote selection report: {report_path}")


if __name__ == "__main__":
    main()
