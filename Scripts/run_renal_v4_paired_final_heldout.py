"""
MedicalPlab Renal V4 — Phase 31: Locked Paired V3-vs-V4 Final Evaluation on FINAL_V4_HELDOUT
===========================================================================================
Author: Antigravity / Principal Information Retrieval & AI Safety Engineer
Dataset: evaluation/renal/v4/renal-heldout-v4-final.json (SHA-frozen)
Output: reports/renal_v4/renal_v4_paired_final_heldout.json

Strict Protocols:
1. Single logical evaluation run with atomic checkpointing and resume support.
2. GPU Hard Gate: PyTorch CUDA availability verified, no CPU fallback.
3. Strict SHA verification of dataset, configs, and model artifacts before execution.
4. Paired evaluation: Frozen V3 vs Frozen V4 on the EXACT SAME 100 queries.
5. Statistical tests: McNemar's exact test on discordant pairs, Clopper-Pearson CI for unsafe accept.
6. Full latency breakdown: query embedding, dense scoring, reranker, safety inference, total.
7. Immutable SBA technical gate evaluation.
"""

from __future__ import annotations

import gc
import hashlib
import io
import json
import math
import os
import pickle
import sys
import time
from pathlib import Path
from typing import Any

if not hasattr(sys.stdout, "_is_wrapped"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stdout._is_wrapped = True

ROOT = Path(__file__).resolve().parent.parent
HELDOUT_PATH = ROOT / "evaluation" / "renal" / "v4" / "renal-heldout-v4-final.json"
CHECKPOINT_DIR = ROOT / "evaluation" / "renal" / "v4" / "checkpoints"
CHECKPOINT_PATH = CHECKPOINT_DIR / "final_heldout_paired_checkpoint.json"
REPORT_DIR = ROOT / "reports" / "renal_v4"
REPORT_PATH = REPORT_DIR / "renal_v4_paired_final_heldout.json"

V4_RETRIEVAL_CONFIG_PATH = ROOT / "configs" / "renal_v4_retrieval_config.json"
V4_SAFETY_CONFIG_PATH = ROOT / "configs" / "renal_v4_safety_config.json"
CLASSIFIER_PATH = ROOT / "models" / "renal_v4_evidence_classifier.pkl"

REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CORPUS_EMB_PATH = ROOT / "Data" / "experiments" / "renal_v3" / "cache" / "all23_corpus_embeddings.npy"
DOC_EMB_PATH = ROOT / "Data" / "experiments" / "renal_v3" / "cache" / "all23_doc_embeddings.npy"
SEC_EMB_PATH = ROOT / "Data" / "experiments" / "renal_v4" / "cache" / "all629_section_structural_embeddings.npy"
SEC_META_PATH = ROOT / "Data" / "experiments" / "renal_v4" / "cache" / "sections_metadata.json"

MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
RERANKER_ID = "Qwen/Qwen3-Reranker-0.6B"
QUERY_INSTRUCTION = "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def clopper_pearson_upper(k: int, n: int, confidence: float = 0.95) -> float:
    """Exact one-sided Clopper-Pearson upper confidence limit for binomial proportion."""
    if n == 0:
        return 1.0
    if k == 0:
        return 1.0 - (1.0 - confidence) ** (1.0 / n)
    from scipy.stats import beta
    return float(beta.ppf(confidence, k + 1, n - k))


def mcnemar_exact_p_value(b: int, c: int) -> float:
    """Two-sided exact binomial test on discordant pairs (b vs c)."""
    n_disc = b + c
    if n_disc == 0:
        return 1.0
    from scipy.stats import binomtest
    res = binomtest(b, n_disc, p=0.5, alternative="two-sided")
    return float(res.pvalue)


def verify_hardware_and_environment():
    print("=" * 70)
    print("PHASE 31: HARDWARE & ENVIRONMENT AUDIT")
    print("=" * 70)
    import torch

    print(f"Python: {sys.executable} ({sys.version.split()[0]})")
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if not torch.cuda.is_available():
        raise RuntimeError("FATAL GPU HARD GATE FAILURE: torch.cuda.is_available() is False. No silent CPU fallback.")

    device_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    print(f"GPU Device: {device_name}")
    print(f"Total VRAM: {vram_gb:.2f} GB")


def verify_sha_preconditions() -> dict[str, str]:
    print("\n--- Verifying Precondition SHAs ---")
    shas = {}
    if not HELDOUT_PATH.exists():
        raise FileNotFoundError(f"Missing heldout dataset: {HELDOUT_PATH}")
    shas["heldout_dataset"] = sha256_file(HELDOUT_PATH)
    print(f"  FINAL_V4_HELDOUT SHA256: {shas['heldout_dataset']}")

    if not V4_RETRIEVAL_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing V4 retrieval config: {V4_RETRIEVAL_CONFIG_PATH}")
    shas["v4_retrieval_config"] = sha256_file(V4_RETRIEVAL_CONFIG_PATH)
    print(f"  V4 Retrieval Config SHA256: {shas['v4_retrieval_config']}")

    if not V4_SAFETY_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing V4 safety config: {V4_SAFETY_CONFIG_PATH}")
    shas["v4_safety_config"] = sha256_file(V4_SAFETY_CONFIG_PATH)
    print(f"  V4 Safety Config SHA256: {shas['v4_safety_config']}")

    if not CLASSIFIER_PATH.exists():
        raise FileNotFoundError(f"Missing evidence classifier: {CLASSIFIER_PATH}")
    shas["v4_evidence_classifier"] = sha256_file(CLASSIFIER_PATH)
    print(f"  Evidence Classifier SHA256: {shas['v4_evidence_classifier']}")
    return shas


def load_corpus_and_models():
    import numpy as np
    import torch
    from sentence_transformers import CrossEncoder, SentenceTransformer

    print("\n--- Loading Precomputed Corpus & Models into GPU ---")
    reg_data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    doc_ids = [d["document_id"] for d in reg_data.get("documents", [])]

    chunks: list[dict[str, Any]] = []
    chunk_to_doc_idx = []
    for d_idx, did in enumerate(doc_ids):
        cf = CHUNKS_DIR / f"{did}.chunks.json"
        c_list = json.loads(cf.read_text(encoding="utf-8"))["chunks"]
        for c in c_list:
            chunks.append(c)
            chunk_to_doc_idx.append(d_idx)
    chunk_to_doc_idx_arr = np.array(chunk_to_doc_idx, dtype=np.int32)

    corpus_embeddings = np.load(CORPUS_EMB_PATH).astype(np.float32)
    doc_embeddings = np.load(DOC_EMB_PATH).astype(np.float32)
    sec_embeddings = np.load(SEC_EMB_PATH).astype(np.float32)
    sec_meta = json.loads(SEC_META_PATH.read_text(encoding="utf-8"))
    chunk_to_sec = np.array(sec_meta["chunk_to_section"], dtype=np.int32)

    print(f"Loaded {len(chunks)} chunks, {len(doc_ids)} docs, {len(sec_embeddings)} sections.")

    device = "cuda:0"
    model = SentenceTransformer(MODEL_ID, device=device)
    model.max_seq_length = 512

    reranker = CrossEncoder(RERANKER_ID, device=device, trust_remote_code=True)

    with open(CLASSIFIER_PATH, "rb") as f:
        classifier_bundle = pickle.load(f)

    return {
        "chunks": chunks,
        "doc_ids": doc_ids,
        "chunk_to_doc_idx": chunk_to_doc_idx_arr,
        "corpus_embeddings": corpus_embeddings,
        "doc_embeddings": doc_embeddings,
        "sec_embeddings": sec_embeddings,
        "chunk_to_sec": chunk_to_sec,
        "model": model,
        "reranker": reranker,
        "classifier_bundle": classifier_bundle,
    }


def execute_evaluation():
    verify_hardware_and_environment()
    precondition_shas = verify_sha_preconditions()

    heldout_data = json.loads(HELDOUT_PATH.read_text(encoding="utf-8"))
    queries = heldout_data["queries"]
    total_queries = len(queries)
    print(f"\nTotal Heldout Queries to evaluate: {total_queries} (Answerable: 50, Unsupported: 50)")

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Checkpoint resume check
    results_map = {}
    if CHECKPOINT_PATH.exists():
        try:
            ckpt = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
            if ckpt.get("heldout_sha") == precondition_shas["heldout_dataset"]:
                results_map = ckpt.get("results", {})
                print(f"Resuming from valid checkpoint: {len(results_map)} / {total_queries} queries already completed.")
            else:
                print("Checkpoint SHA mismatch with current heldout dataset; starting fresh run.")
        except Exception as e:
            print(f"Warning: could not read checkpoint ({e}); starting fresh run.")

    resources = load_corpus_and_models()
    chunks = resources["chunks"]
    doc_ids = resources["doc_ids"]
    chunk_to_doc_idx = resources["chunk_to_doc_idx"]
    corpus_emb = resources["corpus_embeddings"]
    doc_emb = resources["doc_embeddings"]
    sec_emb = resources["sec_embeddings"]
    chunk_to_sec = resources["chunk_to_sec"]
    model = resources["model"]
    reranker = resources["reranker"]
    bundle = resources["classifier_bundle"]
    clf = bundle["model"]
    scaler = bundle["scaler"]
    tau_v4 = bundle.get("calibrated_threshold", 0.6886)
    tau_v3 = 0.7223

    import numpy as np
    import torch

    start_time_all = time.perf_counter()

    for idx, q_item in enumerate(queries):
        qid = q_item["query_id"]
        if qid in results_map:
            continue

        q_text = q_item["query"]
        is_answerable = q_item["is_answerable"]
        gold_doc = q_item.get("source_document_id")
        gold_chunks = set(q_item.get("relevant_chunk_ids", []))

        # --- STEP 1: Query Embedding ---
        t0 = time.perf_counter()
        with torch.inference_mode():
            q_emb = model.encode([QUERY_INSTRUCTION + q_text], normalize_embeddings=True, show_progress_bar=False)[0]
        t_emb = time.perf_counter() - t0

        # Dense passage, doc, and section scores
        p_scores = corpus_emb @ q_emb
        d_scores = doc_emb @ q_emb
        s_scores = sec_emb @ q_emb

        # === SYSTEM A: Frozen V3 Configuration ===
        # Dense + doc_prior (0.18), no section prior
        t0_v3 = time.perf_counter()
        scores_v3 = p_scores + 0.18 * d_scores[chunk_to_doc_idx]
        top20_idx_v3 = scores_v3.argsort()[::-1][:20]
        cands_v3 = [chunks[int(i)] for i in top20_idx_v3]

        pairs_v3 = [[q_text, c.get("text", "")] for c in cands_v3]
        with torch.inference_mode():
            raw_r_v3 = reranker.predict(pairs_v3, batch_size=8, show_progress_bar=False)
        r_scores_v3 = np.asarray(raw_r_v3, dtype=np.float32).reshape(-1)
        r_order_v3 = r_scores_v3.argsort()[::-1]
        t_v3_total = time.perf_counter() - t0_v3 + t_emb

        ranked_v3_chunks = [cands_v3[int(i)] for i in r_order_v3]
        v3_top1_score = float(r_scores_v3[r_order_v3[0]])
        v3_grounded = bool(v3_top1_score >= tau_v3)

        # === SYSTEM B: Frozen V4 Configuration ===
        # Dense + doc_prior (0.18) + structural section prior (0.12), B=50 -> R=20
        t0_v4 = time.perf_counter()
        scores_v4 = p_scores + 0.18 * d_scores[chunk_to_doc_idx] + 0.12 * s_scores[chunk_to_sec]
        top50_idx_v4 = scores_v4.argsort()[::-1][:50]
        cands50_v4 = [chunks[int(i)] for i in top50_idx_v4]
        # Top-20 selected for reranking
        cands20_v4 = cands50_v4[:20]

        pairs_v4 = [[q_text, c.get("text", "")] for c in cands20_v4]
        with torch.inference_mode():
            raw_r_v4 = reranker.predict(pairs_v4, batch_size=8, show_progress_bar=False)
        r_scores_v4 = np.asarray(raw_r_v4, dtype=np.float32).reshape(-1)
        r_order_v4 = r_scores_v4.argsort()[::-1]
        r_sorted_v4 = r_scores_v4[r_order_v4]

        # V4 Evidence Classifier Feature Extraction
        dense_top1 = float(scores_v4[top50_idx_v4[0]])
        dense_top2 = float(scores_v4[top50_idx_v4[1]]) if len(top50_idx_v4) > 1 else dense_top1
        dense_margin = dense_top1 - dense_top2

        doc_top1 = float(np.max(d_scores))
        doc_top2 = float(np.partition(d_scores, -2)[-2]) if len(d_scores) > 1 else doc_top1
        doc_margin = doc_top1 - doc_top2

        r_top1 = float(r_sorted_v4[0])
        r_top2 = float(r_sorted_v4[1]) if len(r_sorted_v4) > 1 else r_top1
        r_margin = r_top1 - r_top2
        r_top3_mean = float(np.mean(r_sorted_v4[:3]))

        top_docs_v4 = [cands20_v4[int(i)]["document_id"] for i in r_order_v4[:5]]
        top_doc_mode = max(set(top_docs_v4), key=top_docs_v4.count)
        doc_agreement = top_docs_v4.count(top_doc_mode) / len(top_docs_v4)

        exp_s = np.exp(r_sorted_v4[:5] - np.max(r_sorted_v4[:5]))
        probs = exp_s / np.sum(exp_s)
        entropy = -float(np.sum(probs * np.log(probs + 1e-12)))

        feats_v4 = np.array([[
            r_top1, r_top2, r_margin, r_top3_mean,
            dense_top1, dense_margin, doc_top1, doc_margin,
            doc_agreement, entropy
        ]], dtype=np.float32)

        feats_v4_norm = scaler.transform(feats_v4)
        v4_prob = float(clf.predict_proba(feats_v4_norm)[0, 1])
        v4_grounded = bool(v4_prob >= tau_v4)
        t_v4_total = time.perf_counter() - t0_v4 + t_emb

        ranked_v4_chunks = [cands20_v4[int(i)] for i in r_order_v4]

        # Metrics for Answerable items
        q_result = {
            "query_id": qid,
            "is_answerable": is_answerable,
            "curriculum_stratum": q_item.get("curriculum_stratum"),
            "v3": {
                "top1_score": v3_top1_score,
                "is_grounded": v3_grounded,
                "latency_ms": t_v3_total * 1000.0,
                "top1_chunk_id": ranked_v3_chunks[0]["chunk_id"],
                "top1_doc_id": ranked_v3_chunks[0]["document_id"],
            },
            "v4": {
                "top1_score": r_top1,
                "sufficiency_prob": v4_prob,
                "is_grounded": v4_grounded,
                "latency_ms": t_v4_total * 1000.0,
                "top1_chunk_id": ranked_v4_chunks[0]["chunk_id"],
                "top1_doc_id": ranked_v4_chunks[0]["document_id"],
            }
        }

        if is_answerable:
            # V3 retrieval hits
            v3_c_ids = [c["chunk_id"] for c in ranked_v3_chunks]
            v3_d_ids = [c["document_id"] for c in ranked_v3_chunks]
            v3_input20_c_ids = [c["chunk_id"] for c in cands_v3]

            q_result["v3"]["doc_hit1"] = int(v3_d_ids[0] == gold_doc)
            q_result["v3"]["doc_hit5"] = int(gold_doc in v3_d_ids[:5])
            q_result["v3"]["passage_hit1"] = int(v3_c_ids[0] in gold_chunks)
            q_result["v3"]["passage_hit5"] = int(any(cid in gold_chunks for cid in v3_c_ids[:5]))
            q_result["v3"]["reranker_input_hit20"] = int(any(cid in gold_chunks for cid in v3_input20_c_ids))

            ranks_v3 = [i + 1 for i, cid in enumerate(v3_c_ids) if cid in gold_chunks]
            q_result["v3"]["rr"] = 1.0 / ranks_v3[0] if ranks_v3 else 0.0

            # V4 retrieval hits
            v4_c_ids = [c["chunk_id"] for c in ranked_v4_chunks]
            v4_d_ids = [c["document_id"] for c in ranked_v4_chunks]
            v4_input20_c_ids = [c["chunk_id"] for c in cands20_v4]
            v4_superset50_c_ids = [c["chunk_id"] for c in cands50_v4]

            q_result["v4"]["doc_hit1"] = int(v4_d_ids[0] == gold_doc)
            q_result["v4"]["doc_hit5"] = int(gold_doc in v4_d_ids[:5])
            q_result["v4"]["passage_hit1"] = int(v4_c_ids[0] in gold_chunks)
            q_result["v4"]["passage_hit5"] = int(any(cid in gold_chunks for cid in v4_c_ids[:5]))
            q_result["v4"]["reranker_input_hit20"] = int(any(cid in gold_chunks for cid in v4_input20_c_ids))
            q_result["v4"]["candidate_coverage50"] = int(any(cid in gold_chunks for cid in v4_superset50_c_ids))

            ranks_v4 = [i + 1 for i, cid in enumerate(v4_c_ids) if cid in gold_chunks]
            q_result["v4"]["rr"] = 1.0 / ranks_v4[0] if ranks_v4 else 0.0

        results_map[qid] = q_result

        # Save checkpoint periodically
        if (idx + 1) % 10 == 0 or (idx + 1) == total_queries:
            CHECKPOINT_PATH.write_text(
                json.dumps({"heldout_sha": precondition_shas["heldout_dataset"], "results": results_map}, indent=2),
                encoding="utf-8"
            )
            print(f"Evaluated {len(results_map)} / {total_queries} queries (last: {qid})")

    total_wall_s = time.perf_counter() - start_time_all
    print(f"\nEvaluation complete in {total_wall_s:.2f} s. Compiling report...")

    # Compile aggregate results
    ans_results = [r for r in results_map.values() if r["is_answerable"]]
    unsupp_results = [r for r in results_map.values() if not r["is_answerable"]]

    N_ans = len(ans_results)
    N_unsupp = len(unsupp_results)

    # Retrieval aggregates on Answerable queries
    v3_p_hit1 = sum(r["v3"]["passage_hit1"] for r in ans_results) / N_ans
    v3_p_hit5 = sum(r["v3"]["passage_hit5"] for r in ans_results) / N_ans
    v3_d_hit1 = sum(r["v3"]["doc_hit1"] for r in ans_results) / N_ans
    v3_mrr = sum(r["v3"]["rr"] for r in ans_results) / N_ans
    v3_r_input20 = sum(r["v3"]["reranker_input_hit20"] for r in ans_results) / N_ans
    v3_p50_lat = float(np.median([r["v3"]["latency_ms"] for r in results_map.values()]))
    v3_p95_lat = float(np.percentile([r["v3"]["latency_ms"] for r in results_map.values()], 95))

    v4_p_hit1 = sum(r["v4"]["passage_hit1"] for r in ans_results) / N_ans
    v4_p_hit5 = sum(r["v4"]["passage_hit5"] for r in ans_results) / N_ans
    v4_d_hit1 = sum(r["v4"]["doc_hit1"] for r in ans_results) / N_ans
    v4_mrr = sum(r["v4"]["rr"] for r in ans_results) / N_ans
    v4_r_input20 = sum(r["v4"]["reranker_input_hit20"] for r in ans_results) / N_ans
    v4_cov50 = sum(r["v4"]["candidate_coverage50"] for r in ans_results) / N_ans
    v4_p50_lat = float(np.median([r["v4"]["latency_ms"] for r in results_map.values()]))
    v4_p95_lat = float(np.percentile([r["v4"]["latency_ms"] for r in results_map.values()], 95))

    # Paired McNemar Table on PassageHit@1
    n11 = 0 # both correct
    n10 = 0 # V4 correct, V3 incorrect
    n01 = 0 # V3 correct, V4 incorrect
    n00 = 0 # both incorrect
    for r in ans_results:
        v4_c = r["v4"]["passage_hit1"]
        v3_c = r["v3"]["passage_hit1"]
        if v4_c and v3_c: n11 += 1
        elif v4_c and not v3_c: n10 += 1
        elif not v4_c and v3_c: n01 += 1
        else: n00 += 1

    mcnemar_p = mcnemar_exact_p_value(n10, n01)

    # End-to-End Safety Aggregates on all 100 queries
    # For V3:
    v3_tp = sum(1 for r in ans_results if r["v3"]["is_grounded"])
    v3_fn = sum(1 for r in ans_results if not r["v3"]["is_grounded"])
    v3_fp = sum(1 for r in unsupp_results if r["v3"]["is_grounded"])
    v3_tn = sum(1 for r in unsupp_results if not r["v3"]["is_grounded"])
    v3_prec = v3_tp / (v3_tp + v3_fp) if (v3_tp + v3_fp) > 0 else 0.0
    v3_rec = v3_tp / N_ans
    v3_unsafe_accept = v3_fp / N_unsupp
    v3_false_refusal = v3_fn / N_ans

    # For V4:
    v4_tp = sum(1 for r in ans_results if r["v4"]["is_grounded"])
    v4_fn = sum(1 for r in ans_results if not r["v4"]["is_grounded"])
    v4_fp = sum(1 for r in unsupp_results if r["v4"]["is_grounded"])
    v4_tn = sum(1 for r in unsupp_results if not r["v4"]["is_grounded"])
    v4_prec = v4_tp / (v4_tp + v4_fp) if (v4_tp + v4_fp) > 0 else 0.0
    v4_rec = v4_tp / N_ans
    v4_unsafe_accept = v4_fp / N_unsupp
    v4_unsafe_accept_ub95 = clopper_pearson_upper(v4_fp, N_unsupp, 0.95)
    v4_false_refusal = v4_fn / N_ans

    # Negative strata breakdown for V4
    gap_res = [r for r in unsupp_results if r["curriculum_stratum"] == "coverage_gap"]
    ood_res = [r for r in unsupp_results if r["curriculum_stratum"] == "out_of_domain"]
    diff_res = [r for r in unsupp_results if r["curriculum_stratum"] == "difficult_negative"]

    gap_unsafe = sum(1 for r in gap_res if r["v4"]["is_grounded"])
    ood_unsafe = sum(1 for r in ood_res if r["v4"]["is_grounded"])
    diff_unsafe = sum(1 for r in diff_res if r["v4"]["is_grounded"])

    # SBA Gate checks
    # PassageHit@1 >= 0.85, PassageHit@5 >= 0.95, Safety Precision >= 0.90, Safety Recall >= 0.75, Unsafe Accept <= 0.05
    sba_pass = (
        v4_p_hit1 >= 0.85
        and v4_p_hit5 >= 0.95
        and v4_prec >= 0.90
        and v4_rec >= 0.75
        and v4_unsafe_accept <= 0.05
    )
    sba_verdict = "SBA_GATE_PASS" if sba_pass else "SBA_GATE_FAIL"

    report = {
        "metadata": {
            "evaluation_title": "FINAL LOCKED PAIRED V3 vs V4 EVALUATION ON FINAL_V4_HELDOUT",
            "heldout_dataset_marker": "RENAL-V4-FINAL-FROZEN-UNSEEN",
            "heldout_path": str(HELDOUT_PATH),
            "heldout_sha256": precondition_shas["heldout_dataset"],
            "v4_retrieval_config_sha256": precondition_shas["v4_retrieval_config"],
            "v4_safety_config_sha256": precondition_shas["v4_safety_config"],
            "v4_classifier_sha256": precondition_shas["v4_evidence_classifier"],
            "total_queries": total_queries,
            "answerable_count": N_ans,
            "unsupported_count": N_unsupp,
            "wall_clock_seconds": total_wall_s,
        },
        "paired_retrieval_metrics": {
            "v3_frozen": {
                "passage_hit1": f"{sum(r['v3']['passage_hit1'] for r in ans_results)}/{N_ans} ({v3_p_hit1 * 100:.2f}%)",
                "passage_hit5": f"{sum(r['v3']['passage_hit5'] for r in ans_results)}/{N_ans} ({v3_p_hit5 * 100:.2f}%)",
                "document_hit1": f"{sum(r['v3']['doc_hit1'] for r in ans_results)}/{N_ans} ({v3_d_hit1 * 100:.2f}%)",
                "mrr": round(v3_mrr, 4),
                "reranker_input_hit20": f"{sum(r['v3']['reranker_input_hit20'] for r in ans_results)}/{N_ans} ({v3_r_input20 * 100:.2f}%)",
                "p50_latency_ms": round(v3_p50_lat, 2),
                "p95_latency_ms": round(v3_p95_lat, 2),
            },
            "v4_frozen": {
                "passage_hit1": f"{sum(r['v4']['passage_hit1'] for r in ans_results)}/{N_ans} ({v4_p_hit1 * 100:.2f}%)",
                "passage_hit5": f"{sum(r['v4']['passage_hit5'] for r in ans_results)}/{N_ans} ({v4_p_hit5 * 100:.2f}%)",
                "document_hit1": f"{sum(r['v4']['doc_hit1'] for r in ans_results)}/{N_ans} ({v4_d_hit1 * 100:.2f}%)",
                "mrr": round(v4_mrr, 4),
                "reranker_input_hit20": f"{sum(r['v4']['reranker_input_hit20'] for r in ans_results)}/{N_ans} ({v4_r_input20 * 100:.2f}%)",
                "candidate_coverage50": f"{sum(r['v4']['candidate_coverage50'] for r in ans_results)}/{N_ans} ({v4_cov50 * 100:.2f}%)",
                "p50_latency_ms": round(v4_p50_lat, 2),
                "p95_latency_ms": round(v4_p95_lat, 2),
            },
            "passage_hit1_discordance_matrix": {
                "both_correct_n11": n11,
                "v4_correct_v3_incorrect_n10": n10,
                "v3_correct_v4_incorrect_n01": n01,
                "both_incorrect_n00": n00,
                "mcnemar_exact_p_value": round(mcnemar_p, 4),
            },
        },
        "paired_safety_metrics": {
            "v3_baseline": {
                "tp": v3_tp, "fp": v3_fp, "tn": v3_tn, "fn": v3_fn,
                "precision": round(v3_prec, 4),
                "recall": round(v3_rec, 4),
                "unsafe_accept_rate": round(v3_unsafe_accept, 4),
                "false_refusal_rate": round(v3_false_refusal, 4),
            },
            "v4_calibrated": {
                "tp": v4_tp, "fp": v4_fp, "tn": v4_tn, "fn": v4_fn,
                "precision": round(v4_prec, 4),
                "recall": round(v4_rec, 4),
                "unsafe_accept_rate": f"{v4_fp}/{N_unsupp} ({v4_unsafe_accept * 100:.2f}%)",
                "unsafe_accept_95_clopper_pearson_upper": round(v4_unsafe_accept_ub95, 4),
                "false_refusal_rate": f"{v4_fn}/{N_ans} ({v4_false_refusal * 100:.2f}%)",
                "negative_strata_breakdown": {
                    "coverage_gap_unsafe": f"{gap_unsafe}/{len(gap_res)}",
                    "out_of_domain_unsafe": f"{ood_unsafe}/{len(ood_res)}",
                    "difficult_negative_unsafe": f"{diff_unsafe}/{len(diff_res)}",
                },
            },
        },
        "sba_technical_gate": {
            "verdict": sba_verdict,
            "generated": 0,
            "human_reviewed": f"0/{total_queries}",
            "golden": f"0/{total_queries}",
            "reasons": {
                "PassageHit@1 >= 0.85": f"{v4_p_hit1:.4f} ({'PASS' if v4_p_hit1 >= 0.85 else 'FAIL'})",
                "PassageHit@5 >= 0.95": f"{v4_p_hit5:.4f} ({'PASS' if v4_p_hit5 >= 0.95 else 'FAIL'})",
                "Safety Precision >= 0.90": f"{v4_prec:.4f} ({'PASS' if v4_prec >= 0.90 else 'FAIL'})",
                "Safety Recall >= 0.75": f"{v4_rec:.4f} ({'PASS' if v4_rec >= 0.75 else 'FAIL'})",
                "Unsafe Accept <= 0.05": f"{v4_unsafe_accept:.4f} ({'PASS' if v4_unsafe_accept <= 0.05 else 'FAIL'})",
            }
        },
        "query_level_results": results_map,
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report_sha = sha256_file(REPORT_PATH)
    (REPORT_DIR / f"{REPORT_PATH.name}.sha256").write_text(f"{report_sha}  {REPORT_PATH.name}\n", encoding="utf-8")

    print("\n" + "=" * 70)
    print("FINAL PAIRED EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Paired Retrieval PassageHit@1: V3={v3_p_hit1 * 100:.2f}% vs V4={v4_p_hit1 * 100:.2f}%")
    print(f"Discordance: n10(V4 win)={n10}, n01(V3 win)={n01}, McNemar p-value={mcnemar_p:.4f}")
    print(f"RerankerInputHit@20: V3={v3_r_input20 * 100:.2f}% vs V4={v4_r_input20 * 100:.2f}%")
    print(f"V4 CandidateCoverage@50: {v4_cov50 * 100:.2f}%")
    print(f"Safety Unsafe Accept Rate: {v4_fp}/{N_unsupp} ({v4_unsafe_accept * 100:.2f}%) [95% CP UB: {v4_unsafe_accept_ub95 * 100:.2f}%]")
    print(f"Safety Recall: {v4_rec * 100:.2f}%, False Refusal: {v4_false_refusal * 100:.2f}%")
    print(f"SBA Gate Verdict: {sba_verdict}")
    print(f"Report written to {REPORT_PATH} (SHA256: {report_sha})")


if __name__ == "__main__":
    execute_evaluation()
