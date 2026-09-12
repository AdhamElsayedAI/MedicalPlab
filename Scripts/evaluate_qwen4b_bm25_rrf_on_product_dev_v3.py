"""
Evaluate Frozen Retrieval Stage: Qwen3-Embedding-4B + BM25 -> Fixed RRF on PRODUCT_DEV_V3
========================================================================================
Frozen Architecture Retrieval Stage:
- Channel A: Qwen/Qwen3-Embedding-4B (4-bit NF4, rev 5cf2132abc99cad020ac570b19d031efec650f2b)
  Evaluated against 2,691 precomputed corpus embeddings (.cache/evidence_engine/corpus_embeddings_2691.npy).
- Channel B: Okapi BM25 (k1=1.5, b=0.75) across 2,691 corpus chunks.
- Fusion: Fixed Reciprocal Rank Fusion (k=60, equal weighting w_dense=1.0, w_bm25=1.0).

Evaluates on PRODUCT_DEV_V3 (N=100) clean benchmark.
Computes:
- Semantic Recall@1, @5, @10, @20, @50, @100, @200
- Exact-Gold Recall@1, @5, @10, @20, @50, @100, @200
- Passage DocHit@1, @5, @10
- Passage SectionHit@1, @5, @10
- MRR, nDCG@10
- Rank distribution (median, p75, p90, max)
- 95% Wilson confidence intervals
"""

import gc
import hashlib
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / ".renal_env"))
sys.path.insert(0, str(_ROOT / "src"))

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import BitsAndBytesConfig

from medicalplab.evidence_engine.query_representation import ClinicalQueryProcessor

DEV3_PATH = _ROOT / "evaluation" / "evidence_engine" / "product_dev_v3.json"
CHUNKS_DIR = _ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CORPUS_EMB_PATH = _ROOT / ".cache" / "evidence_engine" / "corpus_embeddings_2691.npy"
REPORT_PATH = _ROOT / "reports" / "evidence_engine" / "product_dev_v3_qwen4b_rrf_report.json"
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

EMB_4B_ID = "Qwen/Qwen3-Embedding-4B"
EMB_4B_REV = "5cf2132abc99cad020ac570b19d031efec650f2b"
RRF_K = 60


def wilson_score_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z * math.sqrt((p * (1 - p) / total) + (z**2) / (4 * (total**2)))) / denom
    return max(0.0, center - spread), min(1.0, center + spread)


def make_stat(count: int, n: int) -> dict[str, Any]:
    low, high = wilson_score_interval(count, n)
    return {
        "count": count,
        "total": n,
        "rate": round(count / n, 4) if n > 0 else 0.0,
        "pct": f"{(count / n) * 100:.2f}%" if n > 0 else "0.0%",
        "ci_95_wilson": [round(low, 4), round(high, 4)],
    }


def compute_dcg(relevances: list[int], k: int = 10) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevances[:k], 1):
        if rel > 0:
            dcg += (2**rel - 1) / math.log2(i + 1)
    return dcg


def compute_ndcg(retrieved_ids: list[str], gold_ids: set[str], k: int = 10) -> float:
    rels = [1 if cid in gold_ids else 0 for cid in retrieved_ids[:k]]
    actual_dcg = compute_dcg(rels, k)
    ideal_rels = sorted(rels, reverse=True)
    ideal_dcg = compute_dcg(ideal_rels, k)
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(w) > 2]


def main():
    print("=" * 70)
    print("FROZEN RETRIEVAL EVALUATION: QWEN3-EMBEDDING-4B + BM25 -> FIXED RRF")
    print("=" * 70)

    # 1. Load benchmark
    items = json.loads(DEV3_PATH.read_bytes())
    n = len(items)
    print(f"Loaded {n} benchmark queries from {DEV3_PATH.name}")

    query_processor = ClinicalQueryProcessor()
    query_reps = [query_processor.process_query(it["query"]) for it in items]

    # 2. Load corpus chunks
    chunks = {}
    ordered_cids = []
    chunk_docs = {}
    chunk_sections = {}

    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        file_data = json.loads(p.read_bytes())
        doc_id = file_data.get("document_id")
        for ch in file_data.get("chunks", []):
            cid = ch.get("chunk_id")
            chunks[cid] = ch
            ordered_cids.append(cid)
            chunk_docs[cid] = doc_id
            chunk_sections[cid] = (doc_id, ch.get("heading") or "General")

    print(f"Loaded {len(ordered_cids)} corpus chunks from {len(set(chunk_docs.values()))} documents")

    # 3. Load precomputed Qwen3-Embedding-4B corpus embeddings
    assert CORPUS_EMB_PATH.exists(), f"Corpus embeddings not found at {CORPUS_EMB_PATH}"
    corpus_embs = np.load(CORPUS_EMB_PATH)
    print(f"Loaded corpus embeddings: {corpus_embs.shape} (dtype: {corpus_embs.dtype})")
    assert len(corpus_embs) == len(ordered_cids), "Corpus embeddings dimension mismatch with chunk count!"

    # Ensure unit normalization of corpus embeddings
    norms = np.linalg.norm(corpus_embs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    corpus_embs = corpus_embs / norms

    # 4. Build BM25 index
    print("\nBuilding Okapi BM25 index across 2,691 chunks...")
    t0_bm25 = time.perf_counter()
    corpus_tokens = {}
    doc_lens = {}
    df = Counter()
    n_chunks = len(ordered_cids)

    for cid in ordered_cids:
        ch = chunks[cid]
        text = f"{ch.get('doc_title', '')} {ch.get('heading', '')} {ch.get('text', '')}"
        toks = tokenize(text)
        corpus_tokens[cid] = toks
        doc_lens[cid] = len(toks)
        for w in set(toks):
            df[w] += 1

    avgdl = sum(doc_lens.values()) / max(1, len(doc_lens))
    idf = {w: math.log((n_chunks - freq + 0.5) / (freq + 0.5) + 1.0) for w, freq in df.items()}
    tf = {cid: Counter(corpus_tokens[cid]) for cid in ordered_cids}
    k1 = 1.5
    b = 0.75
    print(f"BM25 index built in {time.perf_counter() - t0_bm25:.2f}s (vocab: {len(idf)}, avgdl: {avgdl:.1f})")

    # 5. Load Qwen3-Embedding-4B in 4-bit NF4 to encode queries
    print("\nLoading Qwen3-Embedding-4B under 4-bit NF4 to encode queries...")
    t0_load = time.perf_counter()
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    emb_model = SentenceTransformer(
        EMB_4B_ID,
        revision=EMB_4B_REV,
        model_kwargs={
            "quantization_config": bnb_config,
            "device_map": "auto",
            "torch_dtype": torch.float16,
        },
        trust_remote_code=True,
    )
    print(f"Loaded {EMB_4B_ID} in {time.perf_counter() - t0_load:.1f}s")
    vram_mb = torch.cuda.memory_allocated() / (1024**2) if torch.cuda.is_available() else 0.0
    print(f"VRAM Allocated: {vram_mb:.1f} MB")

    # 6. Encode all 100 queries
    query_texts = [
        q_rep.neutral_target or q_rep.canonical_query or q_rep.original_query
        for q_rep in query_reps
    ]
    prompt = "Instruct: Given a medical query, retrieve relevant clinical evidence passages.\nQuery: "
    print(f"\nEncoding {len(query_texts)} queries with medical retrieval instruction...")
    t0_enc = time.perf_counter()
    q_embs_raw = emb_model.encode(query_texts, prompt=prompt, batch_size=16, show_progress_bar=False)
    q_embs = np.asarray(q_embs_raw, dtype=np.float32)
    q_norms = np.linalg.norm(q_embs, axis=1, keepdims=True)
    q_norms[q_norms == 0] = 1.0
    q_embs = q_embs / q_norms
    print(f"Encoded queries in {time.perf_counter() - t0_enc:.2f}s (shape: {q_embs.shape})")

    # 7. Immediately unload embedding model to maintain hardware discipline
    print("Freeing Qwen3-Embedding-4B from VRAM...")
    del emb_model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("VRAM flushed.")

    # 8. Evaluate Configurations
    configs = ["DENSE_ONLY", "BM25_ONLY", "FIXED_RRF"]
    eval_results = {}

    for cfg_name in configs:
        print(f"\nEvaluating configuration: {cfg_name}...")
        depths = [1, 5, 10, 20, 50, 100, 200]
        rec_sem = {k: 0 for k in depths}
        rec_exact = {k: 0 for k in depths}
        doc_hit = {k: 0 for k in [1, 5, 10]}
        sec_hit = {k: 0 for k in [1, 5, 10]}
        mrr_sum = 0.0
        ndcg_sum = 0.0
        ranks_sem = []

        for idx, (item, q_text, q_vec) in enumerate(zip(items, query_texts, q_embs)):
            qid = item["query_id"]
            exact_golds = set(item.get("exact_gold_chunk_ids", []))
            sem_golds = set(item.get("semantic_support_chunk_ids", exact_golds))
            gold_doc = item.get("gold_document_id", "")
            gold_sec = item.get("gold_section", "")

            # A. Dense scores across all chunks
            dense_scores = np.dot(corpus_embs, q_vec)

            # B. BM25 scores across all chunks
            q_toks = tokenize(q_text)
            bm25_scores = np.zeros(n_chunks, dtype=np.float32)
            for i, cid in enumerate(ordered_cids):
                c_tf = tf[cid]
                L = doc_lens[cid]
                s = sum(
                    idf.get(w, 0.0) * (c_tf[w] * (k1 + 1.0)) / (c_tf[w] + k1 * (1.0 - b + b * (L / avgdl)))
                    for w in q_toks
                    if w in c_tf
                )
                bm25_scores[i] = s

            # Scoring based on config
            if cfg_name == "DENSE_ONLY":
                ranked_indices = np.argsort(dense_scores)[::-1]
            elif cfg_name == "BM25_ONLY":
                ranked_indices = np.argsort(bm25_scores)[::-1]
            elif cfg_name == "FIXED_RRF":
                # Dense ranking
                dense_order = np.argsort(dense_scores)[::-1]
                dense_rank_map = {idx: r for r, idx in enumerate(dense_order, 1)}

                # BM25 ranking
                bm25_order = np.argsort(bm25_scores)[::-1]
                bm25_rank_map = {idx: r for r, idx in enumerate(bm25_order, 1)}

                # RRF computation for top candidates
                rrf_scores = np.zeros(n_chunks, dtype=np.float32)
                for i in range(n_chunks):
                    r_d = dense_rank_map[i]
                    r_b = bm25_rank_map[i]
                    # Compute RRF for top 500 in either channel to conserve computation
                    if r_d <= 500 or r_b <= 500:
                        rrf_scores[i] = (1.0 / (RRF_K + r_d)) + (1.0 / (RRF_K + r_b))
                ranked_indices = np.argsort(rrf_scores)[::-1]

            ranked_cids = [ordered_cids[i] for i in ranked_indices]

            # Metric accounting
            # Semantic Recall
            r_sem = next((r for r, cid in enumerate(ranked_cids, 1) if cid in sem_golds), None)
            if r_sem is not None:
                ranks_sem.append(r_sem)
                mrr_sum += 1.0 / r_sem
                for k in depths:
                    if r_sem <= k:
                        rec_sem[k] += 1
            else:
                ranks_sem.append(len(ordered_cids) + 1)

            # Exact Gold Recall
            r_exact = next((r for r, cid in enumerate(ranked_cids, 1) if cid in exact_golds), None)
            if r_exact is not None:
                for k in depths:
                    if r_exact <= k:
                        rec_exact[k] += 1

            # nDCG@10
            ndcg_sum += compute_ndcg(ranked_cids, sem_golds, k=10)

            # Passage DocHit
            top_docs = [chunk_docs[cid] for cid in ranked_cids]
            for k in [1, 5, 10]:
                if gold_doc in top_docs[:k]:
                    doc_hit[k] += 1

            # Passage SectionHit
            top_sections = [chunk_sections[cid] for cid in ranked_cids]
            for k in [1, 5, 10]:
                if any(sec[0] == gold_doc and (gold_sec == "" or sec[1] == gold_sec) for sec in top_sections[:k]):
                    sec_hit[k] += 1

        eval_results[cfg_name] = {
            "semantic_recall": {f"recall_at_{k}": make_stat(rec_sem[k], n) for k in depths},
            "exact_recall": {f"recall_at_{k}": make_stat(rec_exact[k], n) for k in depths},
            "passage_doc_hit": {f"hit_at_{k}": make_stat(doc_hit[k], n) for k in [1, 5, 10]},
            "passage_section_hit": {f"hit_at_{k}": make_stat(sec_hit[k], n) for k in [1, 5, 10]},
            "mrr": round(mrr_sum / n, 4),
            "ndcg_at_10": round(ndcg_sum / n, 4),
            "rank_distribution": {
                "median": float(np.median(ranks_sem)),
                "p75": float(np.percentile(ranks_sem, 75)),
                "p90": float(np.percentile(ranks_sem, 90)),
                "max": int(np.max(ranks_sem)),
            },
        }

    # 9. Format Report
    rrf_res = eval_results["FIXED_RRF"]
    r20_rate = rrf_res["semantic_recall"]["recall_at_20"]["rate"]
    r50_rate = rrf_res["semantic_recall"]["recall_at_50"]["rate"]

    # Predefined gates assessment
    gate_r20_passed = r20_rate >= 0.95
    gate_r50_passed = r50_rate >= 0.98

    if not gate_r20_passed or not gate_r50_passed:
        gate_verdict = "GENUINE_RETRIEVAL_GAP_CONFIRMED"
    else:
        gate_verdict = "RETRIEVAL_TARGET_CEILING_REACHED"

    report = {
        "benchmark": "PRODUCT_DEV_V3",
        "benchmark_file": str(DEV3_PATH.relative_to(_ROOT)),
        "n_queries": n,
        "models": {
            "dense_model": EMB_4B_ID,
            "dense_revision": EMB_4B_REV,
            "dense_quantization": "4-bit NF4, fp16 compute",
            "lexical_model": "Okapi BM25 (k1=1.5, b=0.75)",
            "fusion": "Fixed Reciprocal Rank Fusion (k=60, equal weighting)",
        },
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "predefined_gates": {
            "gate_recall_at_20_gte_95": {
                "threshold": 0.95,
                "observed": r20_rate,
                "passed": gate_r20_passed,
            },
            "gate_recall_at_50_gte_98": {
                "threshold": 0.98,
                "observed": r50_rate,
                "passed": gate_r50_passed,
            },
            "gate_verdict": gate_verdict,
        },
        "configurations": eval_results,
    }

    out_bytes = json.dumps(report, indent=2).encode("utf-8")
    REPORT_PATH.write_bytes(out_bytes)
    sha = hashlib.sha256(out_bytes).hexdigest()
    (REPORT_PATH.with_suffix(".json.sha256")).write_text(f"{sha}  {REPORT_PATH.name}\n", encoding="utf-8")

    print("\n" + "=" * 70)
    print("RESULTS: RETRIEVAL STAGE ON PRODUCT_DEV_V3 (N=100)")
    print("=" * 70)
    for cfg_name in configs:
        res = eval_results[cfg_name]
        print(f"\n--- {cfg_name} ---")
        print(f"  Semantic Recall@20 : {res['semantic_recall']['recall_at_20']['pct']} ({res['semantic_recall']['recall_at_20']['count']}/100) [95% CI: {res['semantic_recall']['recall_at_20']['ci_95_wilson']}]")
        print(f"  Semantic Recall@50 : {res['semantic_recall']['recall_at_50']['pct']} ({res['semantic_recall']['recall_at_50']['count']}/100) [95% CI: {res['semantic_recall']['recall_at_50']['ci_95_wilson']}]")
        print(f"  Semantic Recall@100: {res['semantic_recall']['recall_at_100']['pct']} ({res['semantic_recall']['recall_at_100']['count']}/100)")
        print(f"  Exact-Gold Recall@20: {res['exact_recall']['recall_at_20']['pct']}")
        print(f"  Exact-Gold Recall@50: {res['exact_recall']['recall_at_50']['pct']}")
        print(f"  MRR                : {res['mrr']:.4f}")
        print(f"  nDCG@10            : {res['ndcg_at_10']:.4f}")
        print(f"  DocHit@1 / @5      : {res['passage_doc_hit']['hit_at_1']['pct']} / {res['passage_doc_hit']['hit_at_5']['pct']}")
        print(f"  SectionHit@1 / @5  : {res['passage_section_hit']['hit_at_1']['pct']} / {res['passage_section_hit']['hit_at_5']['pct']}")
        print(f"  Rank Distribution  : median={res['rank_distribution']['median']}, p75={res['rank_distribution']['p75']}, p90={res['rank_distribution']['p90']}, max={res['rank_distribution']['max']}")

    print("\n" + "=" * 70)
    print("PREDEFINED GATE ASSESSMENT & DECISION TREE VERDICT:")
    print("=" * 70)
    print(f"Fixed RRF Recall@20 : {r20_rate*100:.2f}% (Threshold: >=95.0%) -> Passed: {gate_r20_passed}")
    print(f"Fixed RRF Recall@50 : {r50_rate*100:.2f}% (Threshold: >=98.0%) -> Passed: {gate_r50_passed}")
    print(f"Decision Tree Verdict: {gate_verdict}")
    print(f"\nSaved report to {REPORT_PATH.name} (SHA-256: {sha})")


if __name__ == "__main__":
    main()
