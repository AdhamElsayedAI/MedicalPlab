"""
MedicalPlab Renal V5 — Phases 5, 6, 7 Runner
==============================================
Phase 5: Fresh Frozen-V3 Baseline on RERANK_DEV_A_V5
Phase 6: Gold Rank Movement & Miss Classification Diagnostic
Phase 7: Reranker Candidate Depth Diagnostic (Top20, Top30, Top50)
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

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import numpy as np
import torch

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from sentence_transformers import CrossEncoder
from transformers import AutoModel, AutoTokenizer

ROOT = _ROOT
DEV_A_PATH = ROOT / "evaluation" / "renal" / "v5" / "renal-rerank-dev-a-v5.json"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
REPORTS_DIR = ROOT / "reports" / "renal_v5"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
QUERY_INSTRUCTION = (
    "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
)
ALPHA_DOC_PRIOR = 0.18


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


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


def main():
    print("=" * 70)
    print("MEDICALPLAB RENAL V5 — PHASES 5, 6, 7 EXECUTION")
    print("=" * 70)

    # 1. Verify CUDA
    assert torch.cuda.is_available(), "CUDA is required for authoritative V5 evaluation!"
    device = torch.device("cuda:0")
    gpu_name = torch.cuda.get_device_name(0)
    total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print(f"GPU: {gpu_name} ({total_vram_gb:.2f} GB VRAM)")

    # 2. Load DEV-A dataset
    dev_a_bytes = DEV_A_PATH.read_bytes()
    dev_a_sha = sha256_bytes(dev_a_bytes)
    sidecar_sha = (DEV_A_PATH.parent / (DEV_A_PATH.name + ".sha256")).read_text().strip().split()[0]
    assert dev_a_sha == sidecar_sha, f"DEV-A SHA mismatch! {dev_a_sha} vs {sidecar_sha}"
    dev_a = json.loads(dev_a_bytes.decode("utf-8"))
    n_dev = len(dev_a)
    print(f"Loaded DEV-A: N={n_dev} queries (SHA: {dev_a_sha[:16]}...)")

    # 3. Load Registry and Chunks
    reg_data = json.loads(REGISTRY_PATH.read_bytes())
    doc_meta = {d["document_id"]: d for d in reg_data.get("documents", []) if d.get("status") == "accepted"}
    doc_titles = {did: d.get("title", "") for did, d in doc_meta.items()}
    doc_topics = {did: ", ".join(d.get("topic_tags", [])) for did, d in doc_meta.items()}

    chunks = []
    doc_first_texts = {}
    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_bytes())
        for ch in payload.get("chunks", []):
            chunks.append(ch)
            did = ch.get("document_id")
            if did and did not in doc_first_texts:
                doc_first_texts[did] = ch.get("text", "")[:300]
    n_chunks = len(chunks)
    print(f"Corpus chunks loaded: {n_chunks} from {len(doc_meta)} documents")

    doc_ids_sorted = sorted(list(doc_first_texts.keys()))
    doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
    chunk_doc_ids = [ch.get("document_id") for ch in chunks]
    chunk_id_to_chunk = {ch["chunk_id"]: ch for ch in chunks}

    # 4. Load Cached Embeddings
    corpus_emb_path = CACHE_DIR / "all23_corpus_embeddings.npy"
    doc_emb_path = CACHE_DIR / "all23_doc_embeddings.npy"
    assert corpus_emb_path.exists(), f"Missing cache: {corpus_emb_path}"
    assert doc_emb_path.exists(), f"Missing cache: {doc_emb_path}"

    corpus_embeddings = np.load(corpus_emb_path).astype(np.float32)
    doc_embeddings = np.load(doc_emb_path).astype(np.float32)
    print(f"Loaded corpus embeddings: {corpus_embeddings.shape}")
    print(f"Loaded doc embeddings: {doc_embeddings.shape}")

    # 5. Load Models
    print("\nLoading Qwen3-Embedding-0.6B...")
    tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
    embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device).eval()

    print("Loading Qwen3-Reranker-0.6B...")
    reranker = CrossEncoder(RERANK_MODEL_ID, device="cuda:0", trust_remote_code=True)
    print("Models successfully loaded onto GPU.")

    # 6. Query Encoding & First-Stage Retrieval
    print("\nEncoding queries and computing first-stage scores...")
    query_texts = [QUERY_INSTRUCTION + item["query"] for item in dev_a]

    t0_enc = time.perf_counter()
    with torch.inference_mode():
        encoded = tokenizer(query_texts, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
        outputs = embed_model(**encoded)
        mask = encoded["attention_mask"].unsqueeze(-1)
        q_emb = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        q_emb = torch.nn.functional.normalize(q_emb, p=2, dim=1).cpu().numpy().astype(np.float32)
    t_enc = (time.perf_counter() - t0_enc) / n_dev

    # First-stage dot products
    first_stage_results = []
    t_first_stage_list = []
    for i, item in enumerate(dev_a):
        t0_fs = time.perf_counter()
        q_vec = q_emb[i]
        p_scores = corpus_embeddings @ q_vec
        d_scores = doc_embeddings @ q_vec

        comb_scores = p_scores.copy()
        for c_idx, did in enumerate(chunk_doc_ids):
            if did in doc_id_to_idx:
                comb_scores[c_idx] += ALPHA_DOC_PRIOR * d_scores[doc_id_to_idx[did]]

        # Top-100 candidate indices
        top100_idx = comb_scores.argsort()[::-1][:100]
        t_first_stage_list.append(time.perf_counter() - t0_fs)
        first_stage_results.append({
            "query_idx": i,
            "top100_idx": top100_idx,
            "comb_scores": comb_scores,
        })

    # =========================================================================
    # PHASE 5: BASELINE EVALUATION (Depth K=20)
    # =========================================================================
    print("\n" + "=" * 70)
    print("RUNNING PHASE 5: FROZEN V3 BASELINE EVALUATION (DEPTH K=20)")
    print("=" * 70)

    # Warmup reranker before timed loop
    torch.cuda.synchronize()
    _ = reranker.predict([["warmup query", "warmup text"] for _ in range(2)], batch_size=2, show_progress_bar=False)
    torch.cuda.synchronize()

    p5_per_query = []
    rerank_latencies_20 = []

    doc_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    sec_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    pas_hits = {1: 0, 3: 0, 5: 0, 10: 0}
    cand_cov = {20: 0, 30: 0, 50: 0, 100: 0}
    mrr_list = []
    ndcg_list = []

    # Store for Phase 6
    diagnostic_records = []

    for i, item in enumerate(dev_a):
        gold_cids = set(item["gold_chunk_ids"])
        gold_did = item["gold_doc_id"]
        gold_sec = item["gold_section_path"]
        top100_idx = first_stage_results[i]["top100_idx"]

        # Resolve actual gold section prefixes from corpus chunks
        gold_chunk_objs = [chunk_id_to_chunk[cid] for cid in gold_cids if cid in chunk_id_to_chunk]
        gold_sec_prefixes = set(tuple(c.get("section_path", [])[:2]) for c in gold_chunk_objs if c.get("section_path"))

        # Candidate coverage at various depths
        for k in [20, 30, 50, 100]:
            if any(chunks[idx]["chunk_id"] in gold_cids for idx in top100_idx[:k]):
                cand_cov[k] += 1

        # Reranker input at depth 20
        cands_20 = [chunks[idx] for idx in top100_idx[:20]]
        pairs_20 = [[item["query"], ch["text"]] for ch in cands_20]

        torch.cuda.synchronize()
        t0_rr = time.perf_counter()
        raw_scores = reranker.predict(pairs_20, batch_size=20, show_progress_bar=False)
        torch.cuda.synchronize()
        r_scores = np.asarray(raw_scores, dtype=np.float32).reshape(-1)
        rerank_latencies_20.append(time.perf_counter() - t0_rr)

        # Rerank ordering
        order_20 = r_scores.argsort()[::-1]
        reranked_chunks_20 = [cands_20[idx] for idx in order_20]
        reranked_scores_20 = [float(r_scores[idx]) for idx in order_20]

        # Evaluate Top-10 hits
        top10_chunks = reranked_chunks_20[:10]

        # Doc hits
        for k in [1, 3, 5, 10]:
            if any(ch["document_id"] == gold_did for ch in top10_chunks[:k]):
                doc_hits[k] += 1

        # Section hits (chunk is in gold document and matches any gold section prefix)
        for k in [1, 3, 5, 10]:
            if any(ch.get("document_id") == gold_did and tuple(ch.get("section_path", [])[:2]) in gold_sec_prefixes for ch in top10_chunks[:k]):
                sec_hits[k] += 1

        # Passage hits
        for k in [1, 3, 5, 10]:
            if any(ch["chunk_id"] in gold_cids for ch in top10_chunks[:k]):
                pas_hits[k] += 1

        # MRR (first gold chunk rank in top-20)
        gold_rank = None
        for r, ch in enumerate(reranked_chunks_20):
            if ch["chunk_id"] in gold_cids:
                gold_rank = r + 1
                break
        mrr_list.append(1.0 / gold_rank if gold_rank else 0.0)

        # nDCG@10
        relevance_binary = [1 if ch["chunk_id"] in gold_cids else 0 for ch in top10_chunks]
        ndcg_list.append(compute_ndcg_at_k(relevance_binary, k=10))

        # --- Phase 6 Diagnostic Details ---
        # Pre-reranker rank of best gold chunk
        pre_rank = None
        for r, idx in enumerate(top100_idx):
            if chunks[idx]["chunk_id"] in gold_cids:
                pre_rank = r + 1
                break

        # Scores of relevant vs non-relevant within top-20
        rel_scores = [reranked_scores_20[r] for r, ch in enumerate(reranked_chunks_20) if ch["chunk_id"] in gold_cids]
        non_rel_scores = [reranked_scores_20[r] for r, ch in enumerate(reranked_chunks_20) if ch["chunk_id"] not in gold_cids]

        best_rel_score = max(rel_scores) if rel_scores else None
        best_non_rel_score = max(non_rel_scores) if non_rel_scores else None
        margin = (best_rel_score - best_non_rel_score) if (best_rel_score is not None and best_non_rel_score is not None) else None

        winning_ch = reranked_chunks_20[0]
        winning_did = winning_ch.get("document_id")
        winning_sec = winning_ch.get("section_path", [])

        # Miss classification
        is_hit_1 = (winning_ch["chunk_id"] in gold_cids)
        if is_hit_1:
            miss_class = "HIT_AT_1"
            wrong_rel = "NONE_HIT"
        elif pre_rank is None or pre_rank > 100:
            miss_class = "CANDIDATE_SUPERSET_MISS"
            wrong_rel = "SUPERSET_MISS"
        elif pre_rank > 20:
            miss_class = "RERANKER_INPUT_MISS"
            wrong_rel = "OUTSIDE_TOP20"
        else:
            # Gold was in top-20 candidates, but reranker ranked something else at #1
            if winning_did != gold_did:
                miss_class = "DOCUMENT_ROUTING_FAILURE"
                wrong_rel = "DIFF_DOC"
            elif tuple(winning_sec[:2]) not in gold_sec_prefixes:
                miss_class = "RIGHT_DOCUMENT_WRONG_SECTION"
                wrong_rel = "SAME_DOC_DIFF_SECTION"
            else:
                miss_class = "RIGHT_SECTION_WRONG_PASSAGE"
                wrong_rel = "SAME_SECTION_NEIGHBOR"

        diagnostic_records.append({
            "query_id": item["query_id"],
            "query": item["query"],
            "curriculum_stratum": item["curriculum_stratum"],
            "query_style": item["query_style"],
            "gold_doc_id": gold_did,
            "gold_section_path": gold_sec,
            "gold_chunk_ids": list(gold_cids),
            "enters_top20": (pre_rank is not None and pre_rank <= 20),
            "pre_reranker_rank": pre_rank,
            "post_reranker_rank": gold_rank,
            "rank_movement": (pre_rank - gold_rank) if (pre_rank and gold_rank) else None,
            "best_relevant_score": best_rel_score,
            "best_non_relevant_score": best_non_rel_score,
            "score_margin": margin,
            "winning_chunk_id": winning_ch["chunk_id"],
            "winning_doc_id": winning_did,
            "winning_section_path": winning_sec,
            "wrong_winner_relationship": wrong_rel,
            "failure_classification": miss_class,
        })

    # Summary metrics for Phase 5
    m_p1 = pas_hits[1] / n_dev
    m_p3 = pas_hits[3] / n_dev
    m_p5 = pas_hits[5] / n_dev
    m_p10 = pas_hits[10] / n_dev

    m_d1 = doc_hits[1] / n_dev
    m_d3 = doc_hits[3] / n_dev
    m_d5 = doc_hits[5] / n_dev
    m_d10 = doc_hits[10] / n_dev

    m_s1 = sec_hits[1] / n_dev
    m_s3 = sec_hits[3] / n_dev
    m_s5 = sec_hits[5] / n_dev
    m_s10 = sec_hits[10] / n_dev

    m_cov20 = cand_cov[20] / n_dev
    m_cov30 = cand_cov[30] / n_dev
    m_cov50 = cand_cov[50] / n_dev
    m_cov100 = cand_cov[100] / n_dev

    m_mrr = float(np.mean(mrr_list))
    m_ndcg = float(np.mean(ndcg_list))

    lat_enc_p50 = float(np.percentile([t_enc], 50)) * 1000
    lat_fs_p50 = float(np.percentile(t_first_stage_list, 50)) * 1000
    lat_fs_p95 = float(np.percentile(t_first_stage_list, 95)) * 1000
    lat_rr_p50 = float(np.percentile(rerank_latencies_20, 50)) * 1000
    lat_rr_p95 = float(np.percentile(rerank_latencies_20, 95)) * 1000
    total_lats = [t_enc + t_first_stage_list[i] + rerank_latencies_20[i] for i in range(n_dev)]
    lat_tot_p50 = float(np.percentile(total_lats, 50)) * 1000
    lat_tot_p95 = float(np.percentile(total_lats, 95)) * 1000

    print("\n--- PHASE 5 SUMMARY METRICS ---")
    print(f"PassageHit@1:  {pas_hits[1]}/{n_dev} ({m_p1*100:.1f}%)")
    print(f"PassageHit@3:  {pas_hits[3]}/{n_dev} ({m_p3*100:.1f}%)")
    print(f"PassageHit@5:  {pas_hits[5]}/{n_dev} ({m_p5*100:.1f}%)")
    print(f"PassageHit@10: {pas_hits[10]}/{n_dev} ({m_p10*100:.1f}%)")
    print(f"DocumentHit@1: {doc_hits[1]}/{n_dev} ({m_d1*100:.1f}%)")
    print(f"ParentSectionHit@1: {sec_hits[1]}/{n_dev} ({m_s1*100:.1f}%)")
    print(f"RerankerInputHit@20 (CandidateCoverage@20): {cand_cov[20]}/{n_dev} ({m_cov20*100:.1f}%)")
    print(f"CandidateCoverage@30: {cand_cov[30]}/{n_dev} ({m_cov30*100:.1f}%)")
    print(f"CandidateCoverage@50: {cand_cov[50]}/{n_dev} ({m_cov50*100:.1f}%)")
    print(f"CandidateCoverage@100: {cand_cov[100]}/{n_dev} ({m_cov100*100:.1f}%)")
    print(f"MRR: {m_mrr:.4f}, nDCG@10: {m_ndcg:.4f}")
    print(f"Latency: Total p50={lat_tot_p50:.1f}ms, p95={lat_tot_p95:.1f}ms (Reranker p50={lat_rr_p50:.1f}ms)")

    phase5_report = {
        "benchmark": "MEDICALPLAB_RENAL_V5_BASELINE_DEV_A",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset": "evaluation/renal/v5/renal-rerank-dev-a-v5.json",
        "dataset_sha256": dev_a_sha,
        "n_queries": n_dev,
        "model_architecture": "QwenRenalRetrieverV3",
        "embedding_model": EMBED_MODEL_ID,
        "reranker_model": RERANK_MODEL_ID,
        "candidate_depth": 20,
        "alpha_doc_prior": ALPHA_DOC_PRIOR,
        "metrics": {
            "passage_hit_at_1": {"numerator": pas_hits[1], "denominator": n_dev, "rate": m_p1},
            "passage_hit_at_3": {"numerator": pas_hits[3], "denominator": n_dev, "rate": m_p3},
            "passage_hit_at_5": {"numerator": pas_hits[5], "denominator": n_dev, "rate": m_p5},
            "passage_hit_at_10": {"numerator": pas_hits[10], "denominator": n_dev, "rate": m_p10},
            "document_hit_at_1": {"numerator": doc_hits[1], "denominator": n_dev, "rate": m_d1},
            "document_hit_at_3": {"numerator": doc_hits[3], "denominator": n_dev, "rate": m_d3},
            "document_hit_at_5": {"numerator": doc_hits[5], "denominator": n_dev, "rate": m_d5},
            "document_hit_at_10": {"numerator": doc_hits[10], "denominator": n_dev, "rate": m_d10},
            "parent_section_hit_at_1": {"numerator": sec_hits[1], "denominator": n_dev, "rate": m_s1},
            "parent_section_hit_at_3": {"numerator": sec_hits[3], "denominator": n_dev, "rate": m_s3},
            "parent_section_hit_at_5": {"numerator": sec_hits[5], "denominator": n_dev, "rate": m_s5},
            "parent_section_hit_at_10": {"numerator": sec_hits[10], "denominator": n_dev, "rate": m_s10},
            "reranker_input_hit_at_20": {"numerator": cand_cov[20], "denominator": n_dev, "rate": m_cov20},
            "candidate_coverage_at_30": {"numerator": cand_cov[30], "denominator": n_dev, "rate": m_cov30},
            "candidate_coverage_at_50": {"numerator": cand_cov[50], "denominator": n_dev, "rate": m_cov50},
            "candidate_coverage_at_100": {"numerator": cand_cov[100], "denominator": n_dev, "rate": m_cov100},
            "mrr": m_mrr,
            "ndcg_at_10": m_ndcg,
        },
        "latency_ms": {
            "query_encoding_p50": lat_enc_p50,
            "first_stage_p50": lat_fs_p50,
            "first_stage_p95": lat_fs_p95,
            "reranker_p50": lat_rr_p50,
            "reranker_p95": lat_rr_p95,
            "total_p50": lat_tot_p50,
            "total_p95": lat_tot_p95,
        },
    }
    p5_out = REPORTS_DIR / "renal_v5_baseline_dev_a.json"
    p5_bytes = json.dumps(phase5_report, indent=2, ensure_ascii=False).encode("utf-8")
    p5_out.write_bytes(p5_bytes)
    (REPORTS_DIR / "renal_v5_baseline_dev_a.json.sha256").write_text(f"{sha256_bytes(p5_bytes)}  renal_v5_baseline_dev_a.json\n", encoding="utf-8")
    print(f"Phase 5 report saved to {p5_out.name}")

    # =========================================================================
    # PHASE 6: GOLD RANK MOVEMENT DIAGNOSTIC
    # =========================================================================
    print("\n" + "=" * 70)
    print("RUNNING PHASE 6: GOLD RANK MOVEMENT & MISS CLASSIFICATION DIAGNOSTIC")
    print("=" * 70)

    classification_counts = {}
    for r in diagnostic_records:
        c = r["failure_classification"]
        classification_counts[c] = classification_counts.get(c, 0) + 1

    theoretical_ceiling = cand_cov[20] / n_dev
    actual_hit1 = pas_hits[1] / n_dev
    reranking_loss = theoretical_ceiling - actual_hit1

    print(f"Theoretical Reranking Ceiling (RerankerInputHit@20): {cand_cov[20]}/{n_dev} ({theoretical_ceiling*100:.1f}%)")
    print(f"Actual PassageHit@1: {pas_hits[1]}/{n_dev} ({actual_hit1*100:.1f}%)")
    print(f"Reranking Failure Gap: {cand_cov[20] - pas_hits[1]} queries ({reranking_loss*100:.1f}%)")
    print("Failure Classifications:")
    for k, v in sorted(classification_counts.items()):
        print(f"  {k}: {v} queries ({v/n_dev*100:.1f}%)")

    phase6_report = {
        "benchmark": "MEDICALPLAB_RENAL_V5_GOLD_RANK_DIAGNOSTIC",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_sha256": dev_a_sha,
        "n_queries": n_dev,
        "theoretical_ceiling_hit1": {"numerator": cand_cov[20], "denominator": n_dev, "rate": theoretical_ceiling},
        "actual_hit1": {"numerator": pas_hits[1], "denominator": n_dev, "rate": actual_hit1},
        "reranking_failure_gap": {"queries": cand_cov[20] - pas_hits[1], "rate": reranking_loss},
        "classification_summary": classification_counts,
        "detailed_query_diagnostics": diagnostic_records,
    }
    p6_out = REPORTS_DIR / "renal_v5_gold_rank_diagnostic.json"
    p6_bytes = json.dumps(phase6_report, indent=2, ensure_ascii=False).encode("utf-8")
    p6_out.write_bytes(p6_bytes)
    (REPORTS_DIR / "renal_v5_gold_rank_diagnostic.json.sha256").write_text(f"{sha256_bytes(p6_bytes)}  renal_v5_gold_rank_diagnostic.json\n", encoding="utf-8")
    print(f"Phase 6 diagnostic saved to {p6_out.name}")

    # =========================================================================
    # PHASE 7: RERANKER DEPTH DIAGNOSTIC (Top20, Top30, Top50)
    # =========================================================================
    print("\n" + "=" * 70)
    print("RUNNING PHASE 7: DEPTH DIAGNOSTIC BEFORE TRAINING (Top20, Top30, Top50)")
    print("=" * 70)

    p7_out = REPORTS_DIR / "renal_v5_depth_diagnostic.json"
    if p7_out.exists() and "--rerun-depth" not in sys.argv:
        print(f"Phase 7 depth diagnostic already exists at {p7_out.name}. Preserving verified depth results per protocol.")
        phase7_report = json.loads(p7_out.read_text(encoding="utf-8"))
        depth_results = phase7_report["results_by_depth"]
        for depth_str, d_res in depth_results.items():
            print(f"  K={depth_str}: InputHit={d_res['reranker_input_hit']['numerator']}/{n_dev} ({d_res['reranker_input_hit']['rate']*100:.1f}%), Hit@1={d_res['passage_hit_at_1']['numerator']}/{n_dev} ({d_res['passage_hit_at_1']['rate']*100:.1f}%), MRR={d_res['mrr']:.4f}, Latency p50={d_res['reranker_latency_p50_ms']:.1f}ms")
        print(f"Depth recommendation: {phase7_report['depth_recommendation']} ({phase7_report['rationale']})")
    else:
        depth_results = {}
        depth_records = {20: [], 30: [], 50: []}

        for depth in [20, 30, 50]:
            print(f"\nEvaluating candidate depth K={depth}...")
            d_pas_hits = {1: 0, 5: 0, 10: 0}
            d_input_hit = 0
            d_mrr = []
            d_ndcg = []
            d_rerank_times = []

            torch.cuda.reset_peak_memory_stats(device)

            for i, item in enumerate(dev_a):
                gold_cids = set(item["gold_chunk_ids"])
                top100_idx = first_stage_results[i]["top100_idx"]

                if any(chunks[idx]["chunk_id"] in gold_cids for idx in top100_idx[:depth]):
                    d_input_hit += 1

                cands_k = [chunks[idx] for idx in top100_idx[:depth]]
                pairs_k = [[item["query"], ch["text"]] for ch in cands_k]

                torch.cuda.synchronize()
                t0 = time.perf_counter()
                raw_scores = reranker.predict(pairs_k, batch_size=depth, show_progress_bar=False)
                torch.cuda.synchronize()
                d_rerank_times.append(time.perf_counter() - t0)

                order_k = r_scores.argsort()[::-1]
                reranked_k = [cands_k[idx] for idx in order_k]

                top10_k = reranked_k[:10]
                for h in [1, 5, 10]:
                    if any(ch["chunk_id"] in gold_cids for ch in top10_k[:h]):
                        d_pas_hits[h] += 1

                gold_rank = None
                for r, ch in enumerate(reranked_k):
                    if ch["chunk_id"] in gold_cids:
                        gold_rank = r + 1
                        break
                d_mrr.append(1.0 / gold_rank if gold_rank else 0.0)

                rel_bin = [1 if ch["chunk_id"] in gold_cids else 0 for ch in top10_k]
                d_ndcg.append(compute_ndcg_at_k(rel_bin, k=10))

                depth_records[depth].append({
                    "query_id": item["query_id"],
                    "gold_rank": gold_rank,
                    "hit1": (gold_rank == 1),
                })

            peak_vram_mb = torch.cuda.max_memory_allocated(device) / (1024**2)

            depth_results[depth] = {
                "depth_k": depth,
                "reranker_input_hit": {"numerator": d_input_hit, "denominator": n_dev, "rate": d_input_hit / n_dev},
                "passage_hit_at_1": {"numerator": d_pas_hits[1], "denominator": n_dev, "rate": d_pas_hits[1] / n_dev},
                "passage_hit_at_5": {"numerator": d_pas_hits[5], "denominator": n_dev, "rate": d_pas_hits[5] / n_dev},
                "passage_hit_at_10": {"numerator": d_pas_hits[10], "denominator": n_dev, "rate": d_pas_hits[10] / n_dev},
                "mrr": float(np.mean(d_mrr)),
                "ndcg_at_10": float(np.mean(d_ndcg)),
                "reranker_latency_p50_ms": float(np.percentile(d_rerank_times, 50)) * 1000,
                "reranker_latency_p95_ms": float(np.percentile(d_rerank_times, 95)) * 1000,
                "peak_vram_mb": peak_vram_mb,
            }

            print(f"  K={depth}: InputHit={d_input_hit}/{n_dev} ({d_input_hit/n_dev*100:.1f}%), Hit@1={d_pas_hits[1]}/{n_dev} ({d_pas_hits[1]/n_dev*100:.1f}%), MRR={np.mean(d_mrr):.4f}, Latency p50={np.percentile(d_rerank_times,50)*1000:.1f}ms")

        hit1_20_set = set(r["query_id"] for r in depth_records[20] if r["hit1"])
        hit1_30_set = set(r["query_id"] for r in depth_records[30] if r["hit1"])
        hit1_50_set = set(r["query_id"] for r in depth_records[50] if r["hit1"])

        recovered_at_30 = hit1_30_set - hit1_20_set
        lost_at_30 = hit1_20_set - hit1_30_set
        recovered_at_50 = hit1_50_set - hit1_20_set
        lost_at_50 = hit1_20_set - hit1_50_set

        delta_30 = depth_results[30]["passage_hit_at_1"]["numerator"] - depth_results[20]["passage_hit_at_1"]["numerator"]
        delta_50 = depth_results[50]["passage_hit_at_1"]["numerator"] - depth_results[20]["passage_hit_at_1"]["numerator"]

        if delta_30 >= 2:
            depth_recommendation = "CANDIDATE_DEPTH_30"
        elif delta_50 >= 2:
            depth_recommendation = "CANDIDATE_DEPTH_50"
        else:
            depth_recommendation = "KEEP_DEPTH_20_DEFAULT"

        phase7_report = {
            "benchmark": "MEDICALPLAB_RENAL_V5_DEPTH_DIAGNOSTIC",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "dataset_sha256": dev_a_sha,
            "n_queries": n_dev,
            "results_by_depth": depth_results,
            "pairwise_transitions": {
                "depth_30_vs_20": {"recovered_queries": list(recovered_at_30), "lost_queries": list(lost_at_30), "net_delta": delta_30},
                "depth_50_vs_20": {"recovered_queries": list(recovered_at_50), "lost_queries": list(lost_at_50), "net_delta": delta_50},
            },
            "depth_recommendation": depth_recommendation,
            "rationale": f"Net delta at depth 30: {delta_30:+d} queries; Net delta at depth 50: {delta_50:+d} queries.",
        }
        p7_bytes = json.dumps(phase7_report, indent=2, ensure_ascii=False).encode("utf-8")
        p7_out.write_bytes(p7_bytes)
        (REPORTS_DIR / "renal_v5_depth_diagnostic.json.sha256").write_text(f"{sha256_bytes(p7_bytes)}  renal_v5_depth_diagnostic.json\n", encoding="utf-8")
        print(f"Phase 7 diagnostic saved to {p7_out.name}")

    print("\n" + "=" * 70)
    print("PHASES 5, 6, 7 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
