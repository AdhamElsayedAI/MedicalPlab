"""Stage B — Controlled dense-pool reranker diagnostic.

Per mission spec §19:
- Use best dense config: B_400_overlap x content_only
- Measure candidate recall at Top10/20/30/50
- Test Qwen/Qwen3-Reranker-0.6B ONLY on dense candidates (no hybrid)
- Architecture: best dense candidates -> direct reranker -> Top10
- Mark results: PRE-GOLD-AUDIT / PRE-CORPUS-REPAIR DIAGNOSTIC

CUDA HARD GATE: Fails immediately if CUDA unavailable.
"""
from __future__ import annotations

import json
import math
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

# Set PYTHONPATH for renal_env and src before any imports
_ROOT = Path(__file__).resolve().parent.parent
_RENAL_ENV = _ROOT / ".renal_env"
_SRC = _ROOT / "src"
if str(_RENAL_ENV) not in sys.path:
    sys.path.insert(0, str(_RENAL_ENV))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np
import torch
from sentence_transformers import CrossEncoder

# Import matrix utilities after env setup
sys.path.insert(0, str(_ROOT / "Scripts"))
import run_renal_v2_matrix as matrix

ROOT = _ROOT
RERANK_MODEL_ID = "Qwen/Qwen3-Reranker-0.6B"
OUT_PATH = ROOT / "reports" / "renal_v2_reranker.json"
CANDIDATE_POOLS = [10, 20, 30, 50]


def candidate_recall(
    ranked_indices: list[list[int]],
    chunks: list[dict[str, Any]],
    queries: list[dict[str, Any]],
    k: int,
) -> dict[str, Any]:
    """Measure how many answerable queries have at least one relevant passage in top-k."""
    hits = 0
    n = len(queries)
    for query, ranking in zip(queries, ranked_indices):
        top = ranking[:k]
        if any(matrix.is_relevant(chunks[i], query) for i in top):
            hits += 1
    return {
        "k": k,
        "numerator": hits,
        "denominator": n,
        "value": hits / n if n else 0.0,
    }


def run_reranker_on_pool(
    reranker: CrossEncoder,
    chunks: list[dict[str, Any]],
    queries: list[dict[str, Any]],
    dense_indices: list[list[int]],
    pool_size: int,
    batch_size: int = 8,
) -> tuple[list[list[int]], list[list[tuple[int, float]]], float]:
    """Rerank top pool_size dense candidates for each query."""
    candidates = [ranking[:pool_size] for ranking in dense_indices]
    query_texts = [q["query"] for q in queries]

    pairs = [
        (query_texts[qi], str(chunks[ci].get("text", "")))
        for qi, ranking in enumerate(candidates)
        for ci in ranking
    ]
    offsets = [0]
    for ranking in candidates:
        offsets.append(offsets[-1] + len(ranking))

    t_start = time.perf_counter()
    current_batch = batch_size
    while True:
        try:
            with torch.inference_mode():
                raw_scores = reranker.predict(
                    pairs, batch_size=current_batch, show_progress_bar=True
                )
            elapsed = time.perf_counter() - t_start
            break
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if current_batch == 1:
                raise
            current_batch = max(1, current_batch // 2)
            print(f"  OOM: reducing reranker batch to {current_batch}", flush=True)

    pair_scores = np.asarray(raw_scores, dtype=np.float32).reshape(-1)
    reranked: list[list[int]] = []
    scored: list[list[tuple[int, float]]] = []
    for qi, ranking in enumerate(candidates):
        seg = pair_scores[offsets[qi] : offsets[qi + 1]]
        order = np.argsort(seg)[::-1]
        reranked.append([ranking[int(p)] for p in order])
        scored.append([(ranking[int(p)], float(seg[int(p)])) for p in order])
    return reranked, scored, elapsed


def compute_full_metrics(
    dense_indices: list[list[int]],
    chunks: list[dict[str, Any]],
    queries: list[dict[str, Any]],
    label: str,
) -> dict[str, Any]:
    ranked = [[chunks[i] for i in idxs[:10]] for idxs in dense_indices]
    m = matrix.compute_metrics(ranked, queries, chunks)
    print(f"  {label}: {matrix.metric_summary(m)}", flush=True)
    return m


def main() -> None:
    # ── CUDA HARD GATE ──────────────────────────────────────────────
    print(f"PYTHON={sys.executable}")
    print(f"PYTHON_VERSION={platform.python_version()}")
    print(f"TORCH={torch.__version__}")
    print(f"TORCH_CUDA={torch.version.cuda}")
    cuda_ok = torch.cuda.is_available()
    print(f"CUDA_AVAILABLE={cuda_ok}")
    if not cuda_ok:
        raise RuntimeError(
            "CUDA is required for Qwen reranker; CPU fallback is prohibited."
        )
    print(f"DEVICE={torch.cuda.get_device_name(0)}")
    mem_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"VRAM={mem_gb:.1f}GB")
    print()

    # ── LOAD DATA ───────────────────────────────────────────────────
    dev_sha = matrix.verified_dataset_sha(matrix.DEV_PATH)
    queries = matrix.load_queries()
    chunks = matrix.load_chunks("B_400_overlap")
    print(f"DEV_SHA={dev_sha[:16]}... N={len(queries)} CHUNKS={len(chunks)}")

    # ── LOAD EMBEDDING MODEL ─────────────────────────────────────────
    print(f"LOADING_EMBEDDING_MODEL={matrix.MODEL_ID}")
    model = torch.hub.load if False else None
    from sentence_transformers import SentenceTransformer
    embed_model = SentenceTransformer(matrix.MODEL_ID, device="cuda", local_files_only=True)
    embed_model.max_seq_length = matrix.MAX_SEQUENCE_LENGTH
    embed_model.eval()
    revision = matrix.model_revision(embed_model)
    print(f"MODEL_REVISION={revision}")

    # ── LOAD / COMPUTE EMBEDDINGS ────────────────────────────────────
    # Load corpus embeddings from matrix cache
    exp_report = json.loads(matrix.OUT_REPORT.read_text(encoding="utf-8"))
    best_entry = next(
        e for e in exp_report["results"]
        if e["chunking"] == "B_400_overlap" and e["representation"] == "content_only"
    )
    corpus_embs = matrix.load_embedding_cache(
        best_entry["embedding_cache_key"],
        [matrix.chunk_id(c) for c in chunks]
    )
    if corpus_embs is None:
        raise RuntimeError("Corpus embedding cache invalid for B_400_overlap/content_only")
    print("CORPUS_CACHE=HIT HASH_VERIFIED=true")

    # Query embeddings
    query_ids = [q["query_id"] for q in queries]
    query_texts = [matrix.QUERY_INSTRUCTION + q["query"] for q in queries]
    q_corpus_sha = matrix.canonical_sha(list(zip(query_ids, query_texts)))
    q_key = matrix.embedding_cache_key("queries", revision, "queries", "instruction-a", q_corpus_sha)
    query_embs = matrix.load_embedding_cache(q_key, query_ids)
    if query_embs is None:
        print("QUERY_CACHE=MISS — embedding queries...")
        query_embs, _ = matrix.encode_gpu(embed_model, query_texts, "QUERIES")
        matrix.save_embedding_cache(q_key, query_ids, query_embs, {"kind": "queries", "dataset_sha256": dev_sha})
    else:
        print("QUERY_CACHE=HIT")

    # Dense similarity ranking (all 50)
    sims = corpus_embs @ query_embs.T
    dense_indices_50 = [
        sorted(range(len(sims)), key=lambda i, q=qi: sims[i, q], reverse=True)[:50]
        for qi in range(len(queries))
    ]

    # ── CANDIDATE RECALL MEASUREMENT ─────────────────────────────────
    print("\nCANDIDATE RECALL MEASUREMENT:")
    candidate_recalls = []
    for k in CANDIDATE_POOLS:
        rec = candidate_recall(dense_indices_50, chunks, queries, k)
        candidate_recalls.append(rec)
        print(f"  Candidate Recall@{k}: {rec['numerator']}/{rec['denominator']} = {rec['value']:.4f}")

    # ── PRE-RERANKER METRICS (Top10) ──────────────────────────────────
    print("\nPRE-RERANKER (dense Top10):")
    pre_metrics = compute_full_metrics(dense_indices_50, chunks, queries, "dense_top10")

    # ── UNLOAD EMBEDDING MODEL ────────────────────────────────────────
    del embed_model
    torch.cuda.empty_cache()
    print("EMBEDDING_MODEL_UNLOADED (sequential GPU usage)")

    # ── LOAD RERANKER ────────────────────────────────────────────────
    print(f"\nLOADING_RERANKER={RERANK_MODEL_ID}")
    reranker = CrossEncoder(RERANK_MODEL_ID, device="cuda", local_files_only=True, trust_remote_code=True)
    print("RERANKER_LOADED")

    # Get reranker revision
    reranker_revision = "unavailable"
    try:
        reranker_revision = reranker.model.config._commit_hash or "unavailable"
    except (AttributeError, TypeError):
        pass
    print(f"RERANKER_REVISION={reranker_revision}")

    # ── RERANKER TRIALS: each candidate pool size ──────────────────────
    reranker_results = []
    for pool_size in CANDIDATE_POOLS:
        print(f"\nRERANKER pool={pool_size}...")
        t0 = time.perf_counter()
        reranked, scored, elapsed = run_reranker_on_pool(
            reranker, chunks, queries, dense_indices_50, pool_size
        )
        metrics = compute_full_metrics(reranked, chunks, queries, f"reranked_pool{pool_size}")
        # Also measure candidate recall ceiling for this pool
        ceiling = candidate_recall(dense_indices_50, chunks, queries, pool_size)
        reranker_results.append({
            "pool_size": pool_size,
            "candidate_recall_ceiling": ceiling,
            "elapsed_seconds": round(elapsed, 2),
            "metrics": metrics,
        })
        print(f"  Pool={pool_size} ceiling={ceiling['value']:.4f} elapsed={elapsed:.1f}s")

    # Best reranker result
    best = max(reranker_results, key=lambda r: (
        r["metrics"]["hit_at_1"]["value"],
        r["metrics"]["mrr"],
        r["metrics"]["ndcg_at_10"],
    ))
    print(f"\nBEST_POOL={best['pool_size']} Hit@1={best['metrics']['hit_at_1']['value']:.4f}")

    # ── WRITE REPORT ──────────────────────────────────────────────────
    report = {
        "report_id": "RENAL-V2-RERANKER-DIAGNOSTIC",
        "status": "PRE-GOLD-AUDIT / PRE-CORPUS-REPAIR DIAGNOSTIC",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset": "RENAL-DEV-v2",
        "dataset_sha256": dev_sha,
        "n_answerable": len(queries),
        "architecture": "B_400_overlap x content_only -> direct reranker (no hybrid)",
        "embedding_model": matrix.MODEL_ID,
        "embedding_model_revision": revision,
        "reranker_model": RERANK_MODEL_ID,
        "reranker_revision": reranker_revision,
        "pre_reranker_metrics": pre_metrics,
        "candidate_recalls": candidate_recalls,
        "reranker_results": reranker_results,
        "best_pool_size": best["pool_size"],
        "best_reranker_metrics": best["metrics"],
    }

    matrix.atomic_json(OUT_PATH, report)
    print(f"\nRERANKER_REPORT_WRITTEN={OUT_PATH}")

    # Summary
    print("\n" + "=" * 60)
    print("STAGE B RERANKER DIAGNOSTIC SUMMARY")
    print("=" * 60)
    m = pre_metrics
    print(f"Pre-reranker  H@1={m['hit_at_1']['numerator']}/{m['n']}={m['hit_at_1']['value']:.4f} "
          f"H@5={m['hit_at_5']['numerator']}/{m['n']}={m['hit_at_5']['value']:.4f} "
          f"MRR={m['mrr']:.4f} nDCG={m['ndcg_at_10']:.4f}")
    for r in reranker_results:
        rm = r["metrics"]
        print(f"Pool{r['pool_size']:>2} reranked H@1={rm['hit_at_1']['numerator']}/{rm['n']}={rm['hit_at_1']['value']:.4f} "
              f"H@5={rm['hit_at_5']['numerator']}/{rm['n']}={rm['hit_at_5']['value']:.4f} "
              f"MRR={rm['mrr']:.4f} nDCG={rm['ndcg_at_10']:.4f} "
              f"ceiling={r['candidate_recall_ceiling']['value']:.4f} t={r['elapsed_seconds']:.1f}s")


if __name__ == "__main__":
    main()
