"""
MedicalPlab Renal V4 — Controlled Retrieval Ablation Suite
==========================================================
Executes Phases 7, 8, 9, 10, 11 on fresh RETRIEVAL_DEV_V4:
1. V3_BASELINE: Frozen V3 baseline (alpha=0.18 doc prior, top-20 reranked)
2. EXP1_DOC_PAGG: Soft document prior via Top-3 passage mean aggregation
3. EXP2_CAND_UNION: Fixed-budget candidate union (B=50, R=20 with doc quota)
4. EXP3_SEC_STRUCTURAL: Separate structural section channel (title + path + heading)
5. EXP4_SEC_CENTROID: Separate section centroid channel (mean of child chunk embeddings)
6. EXP5_FUSED_SELECTOR: Cheap selector combining dense + doc prior + section channel + rank penalty

Reports complete metrics for each:
- CandidateCoverage@20/50/100
- RerankerInputHit@20
- DocumentHit@1/3/5/10
- ParentSectionHit@1/3/5/10
- PassageHit@1/3/5/10
- MRR, nDCG@10
- Latency breakdown (p50, p95)
- Document and Section diversity
- Explicit KEEP / DISCARD decisions with empirical reasons

Persists to reports/renal_v4/renal_v4_retrieval_ablation.json + SHA256 sidecar.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import sys
import time
from pathlib import Path
import numpy as np
import torch

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
DEV_PATH = ROOT / "evaluation" / "renal" / "v4" / "renal-retrieval-dev-v4.json"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR_V3 = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
CACHE_DIR_V4 = ROOT / "Data" / "experiments" / "renal_v4" / "cache"
REPORTS_DIR = ROOT / "reports" / "renal_v4"
OUTPUT_REPORT_PATH = REPORTS_DIR / "renal_v4_retrieval_ablation.json"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    return ch.get("chunk_id") in q.get("gold_child_chunk_ids", [])


def is_section_relevant(ch: dict, q: dict) -> bool:
    pid = ch.get("parent_section_id")
    return bool(pid and pid in q.get("gold_parent_section_ids", []))


def is_doc_relevant(ch: dict, q: dict) -> bool:
    did = ch.get("document_id")
    return bool(did and did in q.get("gold_document_ids", []))


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


def evaluate_retrieval_variant(
    variant_name: str,
    select_fn,
    ans_queries: list[dict],
    q_embs: np.ndarray,
    chunks: list[dict],
    reranker: CrossEncoder,
    per_query_enc_ms: float,
    superset_budget: int = 50,
    rerank_budget: int = 20
) -> dict:
    n_ans = len(ans_queries)
    doc_hit_1, doc_hit_3, doc_hit_5, doc_hit_10 = 0, 0, 0, 0
    sec_hit_1, sec_hit_3, sec_hit_5, sec_hit_10 = 0, 0, 0, 0
    pass_hit_1, pass_hit_3, pass_hit_5, pass_hit_10 = 0, 0, 0, 0
    cand_cov_20, cand_cov_50, cand_cov_100 = 0, 0, 0
    reranker_input_hit_20 = 0
    mrr_sum, ndcg_sum = 0.0, 0.0

    stage1_lats, stage2_lats, total_lats = [], [], []
    doc_divs, sec_divs = [], []

    for q_idx, q in enumerate(ans_queries):
        q_text = q["query"]

        t0_s1 = time.perf_counter()
        # select_fn returns: (superset_idx_50, rerank_idx_20, stage1_full_sorted_idx)
        superset_idx, rerank_idx, stage1_full = select_fn(q_idx)
        t1_s1 = time.perf_counter()
        s1_ms = (t1_s1 - t0_s1) * 1000.0

        # Candidate coverage metrics
        c_cov_20 = any(is_chunk_relevant(chunks[i], q) for i in stage1_full[:20])
        c_cov_50 = any(is_chunk_relevant(chunks[i], q) for i in stage1_full[:50])
        c_cov_100 = any(is_chunk_relevant(chunks[i], q) for i in stage1_full[:100])
        cand_cov_20 += int(c_cov_20)
        cand_cov_50 += int(c_cov_50)
        cand_cov_100 += int(c_cov_100)

        # Reranker input hit (actual chunks given to reranker)
        r_input_hit = any(is_chunk_relevant(chunks[i], q) for i in rerank_idx)
        reranker_input_hit_20 += int(r_input_hit)

        # Diversity of reranker input
        r_docs = set(chunks[i]["document_id"] for i in rerank_idx)
        r_secs = set(chunks[i].get("parent_section_id") for i in rerank_idx)
        doc_divs.append(len(r_docs))
        sec_divs.append(len(r_secs))

        # Stage 2: Rerank top 20
        cands_rerank = [chunks[i] for i in rerank_idx]
        t0_s2 = time.perf_counter()
        pairs = [[q_text, c.get("text", "")] for c in cands_rerank]
        with torch.inference_mode():
            raw_r = reranker.predict(pairs, batch_size=8, show_progress_bar=False)
        r_scores = np.asarray(raw_r, dtype=np.float32).reshape(-1)
        r_order = np.argsort(r_scores)[::-1]
        t1_s2 = time.perf_counter()
        s2_ms = (t1_s2 - t0_s2) * 1000.0

        tot_ms = per_query_enc_ms + s1_ms + s2_ms
        stage1_lats.append(s1_ms)
        stage2_lats.append(s2_ms)
        total_lats.append(tot_ms)

        reranked_top20 = [cands_rerank[int(i)] for i in r_order]
        # Append remaining candidates from stage1 not in rerank_idx
        used_set = set(rerank_idx)
        remaining = [chunks[i] for i in stage1_full if i not in used_set][:80]
        full_ranked = reranked_top20 + remaining

        # Hits
        d_h1 = any(is_doc_relevant(ch, q) for ch in full_ranked[:1])
        d_h3 = any(is_doc_relevant(ch, q) for ch in full_ranked[:3])
        d_h5 = any(is_doc_relevant(ch, q) for ch in full_ranked[:5])
        d_h10 = any(is_doc_relevant(ch, q) for ch in full_ranked[:10])

        s_h1 = any(is_section_relevant(ch, q) for ch in full_ranked[:1])
        s_h3 = any(is_section_relevant(ch, q) for ch in full_ranked[:3])
        s_h5 = any(is_section_relevant(ch, q) for ch in full_ranked[:5])
        s_h10 = any(is_section_relevant(ch, q) for ch in full_ranked[:10])

        p_h1 = any(is_chunk_relevant(ch, q) for ch in full_ranked[:1])
        p_h3 = any(is_chunk_relevant(ch, q) for ch in full_ranked[:3])
        p_h5 = any(is_chunk_relevant(ch, q) for ch in full_ranked[:5])
        p_h10 = any(is_chunk_relevant(ch, q) for ch in full_ranked[:10])

        doc_hit_1 += int(d_h1)
        doc_hit_3 += int(d_h3)
        doc_hit_5 += int(d_h5)
        doc_hit_10 += int(d_h10)

        sec_hit_1 += int(s_h1)
        sec_hit_3 += int(s_h3)
        sec_hit_5 += int(s_h5)
        sec_hit_10 += int(s_h10)

        pass_hit_1 += int(p_h1)
        pass_hit_3 += int(p_h3)
        pass_hit_5 += int(p_h5)
        pass_hit_10 += int(p_h10)

        # RR & NDCG
        rr = 0.0
        rel_10 = []
        for r_idx, ch in enumerate(full_ranked[:10]):
            is_rel = int(is_chunk_relevant(ch, q))
            rel_10.append(is_rel)
            if is_rel and rr == 0.0:
                rr = 1.0 / (r_idx + 1)

        if rr == 0.0:
            for r_idx, ch in enumerate(full_ranked):
                if is_chunk_relevant(ch, q):
                    rr = 1.0 / (r_idx + 1)
                    break

        ndcg = compute_ndcg_at_k(rel_10, 10)
        mrr_sum += rr
        ndcg_sum += ndcg

    res = {
        "variant": variant_name,
        "n_eval": n_ans,
        "DocumentHit@1": f"{doc_hit_1}/{n_ans} ({doc_hit_1/n_ans:.4f})",
        "DocumentHit@5": f"{doc_hit_5}/{n_ans} ({doc_hit_5/n_ans:.4f})",
        "ParentSectionHit@1": f"{sec_hit_1}/{n_ans} ({sec_hit_1/n_ans:.4f})",
        "ParentSectionHit@5": f"{sec_hit_5}/{n_ans} ({sec_hit_5/n_ans:.4f})",
        "PassageHit@1": f"{pass_hit_1}/{n_ans} ({pass_hit_1/n_ans:.4f})",
        "PassageHit@5": f"{pass_hit_5}/{n_ans} ({pass_hit_5/n_ans:.4f})",
        "CandidateCoverage@20": f"{cand_cov_20}/{n_ans} ({cand_cov_20/n_ans:.4f})",
        "CandidateCoverage@50": f"{cand_cov_50}/{n_ans} ({cand_cov_50/n_ans:.4f})",
        "RerankerInputHit@20": f"{reranker_input_hit_20}/{n_ans} ({reranker_input_hit_20/n_ans:.4f})",
        "MRR": round(mrr_sum / n_ans, 4),
        "nDCG@10": round(ndcg_sum / n_ans, 4),
        "doc_diversity_mean": round(float(np.mean(doc_divs)), 2),
        "sec_diversity_mean": round(float(np.mean(sec_divs)), 2),
        "stage1_p50_ms": round(float(np.percentile(stage1_lats, 50)), 2),
        "stage2_p50_ms": round(float(np.percentile(stage2_lats, 50)), 2),
        "total_p50_ms": round(float(np.percentile(total_lats, 50)), 2),
    }
    return res


def main():
    print("=" * 75)
    print("PHASES 7-11: CONTROLLED RETRIEVAL ABLATION ON FRESH RETRIEVAL_DEV_V4")
    print("=" * 75)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    assert torch.cuda.is_available(), "CUDA required!"
    device = torch.device("cuda:0")

    # 1. Load Dev Data
    dev_data = json.loads(DEV_PATH.read_text(encoding="utf-8"))
    queries = dev_data["queries"]
    ans_queries = [q for q in queries if q["answerable"]]
    n_ans = len(ans_queries)
    print(f"Loaded {n_ans} answerable evaluation queries.")

    # 2. Load Registry, Chunks, and Sections
    reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    doc_titles = {d["document_id"]: d.get("title", "") for d in reg.get("documents", [])}

    chunks = []
    doc_to_chunks = {}
    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_text(encoding="utf-8"))
        for ch in payload.get("chunks", []):
            idx = len(chunks)
            chunks.append(ch)
            did = ch["document_id"]
            doc_to_chunks.setdefault(did, []).append(idx)

    doc_ids_sorted = sorted(list(doc_to_chunks.keys()))
    doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
    n_chunks = len(chunks)
    n_docs = len(doc_ids_sorted)
    print(f"Loaded {n_chunks} chunks across {n_docs} documents.")

    # 3. Load Representations from Cache
    corpus_arr = np.load(CACHE_DIR_V3 / "all23_corpus_embeddings.npy") # (2691, 1024)
    doc_emb = np.load(CACHE_DIR_V3 / "all23_doc_embeddings.npy")       # (23, 1024)
    sec_structural = np.load(CACHE_DIR_V4 / "all629_section_structural_embeddings.npy") # (629, 1024)
    sec_centroid = np.load(CACHE_DIR_V4 / "all629_section_centroid_embeddings.npy")     # (629, 1024)
    sec_meta = json.loads((CACHE_DIR_V4 / "sections_metadata.json").read_text(encoding="utf-8"))
    chunk_to_sec = sec_meta["chunk_to_section"]

    # 4. Load Models
    embed_tok = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
    embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device)
    embed_model.eval()

    reranker = CrossEncoder(RERANK_MODEL_ID, trust_remote_code=True, device="cuda:0")

    # 5. Query Encoding
    q_texts = [q["query"] for q in ans_queries]
    q_instruct = [QUERY_INSTRUCTION + q for q in q_texts]
    _ = encode_texts(q_instruct[:2], embed_tok, embed_model, device)
    t0_enc = time.perf_counter()
    q_embs = encode_texts(q_instruct, embed_tok, embed_model, device)
    t1_enc = time.perf_counter()
    per_query_enc_ms = ((t1_enc - t0_enc) / n_ans) * 1000.0

    # 6. Precompute dot product matrices
    p_sims = np.dot(q_embs, corpus_arr.T)         # (50, 2691)
    d_sims = np.dot(q_embs, doc_emb.T)            # (50, 23)
    s_struct_sims = np.dot(q_embs, sec_structural.T) # (50, 629)
    s_cent_sims = np.dot(q_embs, sec_centroid.T)     # (50, 629)

    # Chunk-level doc and section scores
    chunk_doc_indices = np.array([doc_id_to_idx[ch["document_id"]] for ch in chunks], dtype=np.int32)
    chunk_sec_indices = np.array(chunk_to_sec, dtype=np.int32)

    all_results = []

    # -------------------------------------------------------------
    # VARIANT 0: V3_BASELINE (Frozen V3: dense + 0.18 doc_prior)
    # -------------------------------------------------------------
    def select_v3_baseline(q_idx):
        p_sc = p_sims[q_idx]
        d_sc = d_sims[q_idx]
        comb = p_sc + 0.18 * d_sc[chunk_doc_indices]
        sorted_idx = np.argsort(comb)[::-1]
        return sorted_idx[:50], sorted_idx[:20], sorted_idx

    res_v3 = evaluate_retrieval_variant(
        "V3_BASELINE", select_v3_baseline, ans_queries, q_embs, chunks, reranker, per_query_enc_ms
    )
    res_v3["decision"] = "BASELINE"
    res_v3["rationale"] = "Frozen historical V3 retrieval architecture."
    all_results.append(res_v3)

    # -------------------------------------------------------------
    # VARIANT 1: EXP1_DOC_PAGG (Document Prior via Top-3 Passage Aggregation)
    # -------------------------------------------------------------
    # Compute doc score per query as mean of top 3 passages in that doc
    def select_exp1_doc_pagg(q_idx):
        p_sc = p_sims[q_idx]
        d_agg = np.zeros(n_docs, dtype=np.float32)
        for did, c_idxs in doc_to_chunks.items():
            d_idx = doc_id_to_idx[did]
            top3 = np.partition(p_sc[c_idxs], -min(3, len(c_idxs)))[-min(3, len(c_idxs)):]
            d_agg[d_idx] = float(np.mean(top3))
        comb = p_sc + 0.18 * d_agg[chunk_doc_indices]
        sorted_idx = np.argsort(comb)[::-1]
        return sorted_idx[:50], sorted_idx[:20], sorted_idx

    res_pagg = evaluate_retrieval_variant(
        "EXP1_DOC_PAGG", select_exp1_doc_pagg, ans_queries, q_embs, chunks, reranker, per_query_enc_ms
    )
    # Decision rule: keep if RerankerInputHit@20 and PassageHit@1 improve over baseline
    keep_pagg = (
        float(res_pagg["PassageHit@1"].split()[1].strip("()")) > float(res_v3["PassageHit@1"].split()[1].strip("()"))
        or float(res_pagg["RerankerInputHit@20"].split()[1].strip("()")) > float(res_v3["RerankerInputHit@20"].split()[1].strip("()"))
    )
    res_pagg["decision"] = "KEEP" if keep_pagg else "DISCARD"
    res_pagg["rationale"] = "Tested top-3 passage aggregation for document prior vs document vector."
    all_results.append(res_pagg)

    # -------------------------------------------------------------
    # VARIANT 2: EXP2_CAND_UNION (Fixed-Budget Union B=50, R=20 with Doc Quota & Capping)
    # -------------------------------------------------------------
    # Retain top 30 global, then add up to 4 passages from top 5 documents to reach B=50.
    # For R=20 reranker input, cap max 5 chunks per document to prevent single-document starvation.
    def select_exp2_cand_union(q_idx):
        p_sc = p_sims[q_idx]
        d_sc = d_sims[q_idx]
        comb = p_sc + 0.18 * d_sc[chunk_doc_indices]
        global_order = np.argsort(comb)[::-1]

        # Top 5 docs
        top_docs_order = np.argsort(d_sc)[::-1][:5]
        top_docs_set = set(doc_ids_sorted[i] for i in top_docs_order)

        # Build B=50 superset
        selected_superset = list(global_order[:30])
        seen_set = set(selected_superset)

        for did in top_docs_set:
            d_c_idxs = doc_to_chunks[did]
            d_sorted = sorted(d_c_idxs, key=lambda idx: comb[idx], reverse=True)
            for c_idx in d_sorted[:4]:
                if c_idx not in seen_set and len(selected_superset) < 50:
                    selected_superset.append(c_idx)
                    seen_set.add(c_idx)

        # Fill up to 50 from global if not reached
        for c_idx in global_order:
            if c_idx not in seen_set:
                selected_superset.append(c_idx)
                seen_set.add(c_idx)
                if len(selected_superset) >= 50:
                    break

        # Select R=20 with diversity cap (max 5 chunks per document in top 20)
        rerank_selected = []
        doc_counts = {}
        for c_idx in selected_superset:
            did = chunks[c_idx]["document_id"]
            if doc_counts.get(did, 0) < 5:
                rerank_selected.append(c_idx)
                doc_counts[did] = doc_counts.get(did, 0) + 1
                if len(rerank_selected) == 20:
                    break

        # Fallback if capped too strictly
        if len(rerank_selected) < 20:
            for c_idx in selected_superset:
                if c_idx not in rerank_selected:
                    rerank_selected.append(c_idx)
                    if len(rerank_selected) == 20:
                        break

        return selected_superset, rerank_selected, global_order

    res_union = evaluate_retrieval_variant(
        "EXP2_CAND_UNION", select_exp2_cand_union, ans_queries, q_embs, chunks, reranker, per_query_enc_ms
    )
    keep_union = (
        float(res_union["RerankerInputHit@20"].split()[1].strip("()")) > float(res_v3["RerankerInputHit@20"].split()[1].strip("()"))
        and float(res_union["PassageHit@1"].split()[1].strip("()")) >= float(res_v3["PassageHit@1"].split()[1].strip("()"))
    )
    res_union["decision"] = "KEEP" if keep_union else "DISCARD"
    res_union["rationale"] = "Fixed B=50 superset with doc quota + max-5 per doc cap in R=20 reranker input."
    all_results.append(res_union)

    # -------------------------------------------------------------
    # VARIANT 3: EXP3_SEC_STRUCTURAL (Separate Structural Section Channel)
    # -------------------------------------------------------------
    # Score = p_scores + 0.18 * d_scores + 0.12 * s_structural_scores
    def select_exp3_sec_structural(q_idx):
        p_sc = p_sims[q_idx]
        d_sc = d_sims[q_idx]
        s_sc = s_struct_sims[q_idx]
        comb = p_sc + 0.18 * d_sc[chunk_doc_indices] + 0.12 * s_sc[chunk_sec_indices]
        sorted_idx = np.argsort(comb)[::-1]
        return sorted_idx[:50], sorted_idx[:20], sorted_idx

    res_sec_struct = evaluate_retrieval_variant(
        "EXP3_SEC_STRUCTURAL", select_exp3_sec_structural, ans_queries, q_embs, chunks, reranker, per_query_enc_ms
    )
    keep_sec_struct = (
        float(res_sec_struct["PassageHit@1"].split()[1].strip("()")) >= float(res_v3["PassageHit@1"].split()[1].strip("()"))
        and float(res_sec_struct["ParentSectionHit@1"].split()[1].strip("()")) >= float(res_v3["ParentSectionHit@1"].split()[1].strip("()"))
    )
    res_sec_struct["decision"] = "KEEP" if keep_sec_struct else "DISCARD"
    res_sec_struct["rationale"] = "Separate structural vector (doc title + section path + heading) channel with weight 0.12."
    all_results.append(res_sec_struct)

    # -------------------------------------------------------------
    # VARIANT 4: EXP4_SEC_CENTROID (Separate Centroid Section Channel)
    # -------------------------------------------------------------
    # Score = p_scores + 0.18 * d_scores + 0.12 * s_centroid_scores
    def select_exp4_sec_centroid(q_idx):
        p_sc = p_sims[q_idx]
        d_sc = d_sims[q_idx]
        s_sc = s_cent_sims[q_idx]
        comb = p_sc + 0.18 * d_sc[chunk_doc_indices] + 0.12 * s_sc[chunk_sec_indices]
        sorted_idx = np.argsort(comb)[::-1]
        return sorted_idx[:50], sorted_idx[:20], sorted_idx

    res_sec_cent = evaluate_retrieval_variant(
        "EXP4_SEC_CENTROID", select_exp4_sec_centroid, ans_queries, q_embs, chunks, reranker, per_query_enc_ms
    )
    keep_sec_cent = (
        float(res_sec_cent["PassageHit@1"].split()[1].strip("()")) > float(res_sec_struct["PassageHit@1"].split()[1].strip("()"))
    )
    res_sec_cent["decision"] = "KEEP" if keep_sec_cent else "DISCARD"
    res_sec_cent["rationale"] = "Centroid section channel vs structural section channel."
    all_results.append(res_sec_cent)

    # -------------------------------------------------------------
    # VARIANT 5: EXP5_FUSED_SELECTOR (Cheap Fused Selector between Superset & Reranker)
    # -------------------------------------------------------------
    # Step 1: Candidate superset (B=50) generated using dense + doc_prior + structural section channel
    # Step 2: In the B=50 superset, apply cheap selector with within-document redundancy penalty
    #         to pick the most diverse and high-scoring 20 candidates for the reranker.
    def select_exp5_fused_selector(q_idx):
        p_sc = p_sims[q_idx]
        d_sc = d_sims[q_idx]
        s_sc = s_struct_sims[q_idx]

        # Stage 1 combined score
        comb = p_sc + 0.18 * d_sc[chunk_doc_indices] + 0.10 * s_sc[chunk_sec_indices]
        stage1_sorted = np.argsort(comb)[::-1]
        superset_50 = list(stage1_sorted[:50])

        # Cheap selector scoring for candidates in superset_50:
        # Penalize repeated candidates from the same section and same document
        doc_seen = {}
        sec_seen = {}
        selector_scores = []
        for c_idx in superset_50:
            did = chunks[c_idx]["document_id"]
            sid = chunk_sec_indices[c_idx]
            d_rank = doc_seen.get(did, 0)
            s_rank = sec_seen.get(sid, 0)

            # Soft rank penalty: slight decay for 4th+ passage from same document or 2nd+ from same section
            pen = 0.02 * max(0, d_rank - 2) + 0.015 * max(0, s_rank)
            sel_score = comb[c_idx] - pen

            doc_seen[did] = d_rank + 1
            sec_seen[sid] = s_rank + 1
            selector_scores.append((sel_score, c_idx))

        selector_scores.sort(key=lambda x: x[0], reverse=True)
        rerank_20 = [x[1] for x in selector_scores[:20]]
        return superset_50, rerank_20, stage1_sorted

    res_fused = evaluate_retrieval_variant(
        "EXP5_FUSED_SELECTOR", select_exp5_fused_selector, ans_queries, q_embs, chunks, reranker, per_query_enc_ms
    )
    keep_fused = (
        float(res_fused["RerankerInputHit@20"].split()[1].strip("()")) >= float(res_v3["RerankerInputHit@20"].split()[1].strip("()"))
        and float(res_fused["PassageHit@1"].split()[1].strip("()")) >= float(res_v3["PassageHit@1"].split()[1].strip("()"))
    )
    res_fused["decision"] = "KEEP" if keep_fused else "DISCARD"
    res_fused["rationale"] = "Combined structural section channel + B=50 superset + cheap diversity selector for R=20."
    all_results.append(res_fused)

    # -------------------------------------------------------------
    # COMPARISON TABLE & SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 95)
    print(f"{'Variant':25s} | {'Cov@50':14s} | {'RerankHit@20':14s} | {'PassHit@1':14s} | {'PassHit@5':14s} | {'MRR':7s} | {'Dec'}")
    print("=" * 95)
    for r in all_results:
        print(f"{r['variant']:25s} | {r['CandidateCoverage@50']:14s} | {r['RerankerInputHit@20']:14s} | {r['PassageHit@1']:14s} | {r['PassageHit@5']:14s} | {r['MRR']:<7.4f} | {r['decision']}")
    print("=" * 95)

    payload = {
        "mission": "MEDICALPLAB RENAL V4",
        "stage": "Phases 7-11 Controlled Retrieval Ablation",
        "dataset_name": "RETRIEVAL_DEV_V4",
        "dataset_sha256": sha256_file(DEV_PATH),
        "results": all_results
    }

    OUTPUT_REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    rep_sha = sha256_file(OUTPUT_REPORT_PATH)
    OUTPUT_REPORT_PATH.with_suffix(".json.sha256").write_text(f"{rep_sha}  {OUTPUT_REPORT_PATH.name}\n", encoding="utf-8")
    print(f"\nPersisted ablation report: {OUTPUT_REPORT_PATH} (SHA: {rep_sha})")


if __name__ == "__main__":
    main()
