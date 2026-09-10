"""Run the resumable 4 x 4 Qwen Renal V2 DEV retrieval matrix.

This runner is intentionally CUDA-only. Corpus embeddings are content-addressed,
verified before reuse, and each completed configuration is checkpointed atomically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data"
META = DATA / "metadata"
CHUNKS_ROOT = DATA / "experiments" / "renal_v2" / "chunking"
CACHE_ROOT = DATA / "experiments" / "renal_v2" / "cache"
DEV_PATH = ROOT / "evaluation" / "renal" / "renal-dev-v2.json"
CHECKPOINT_PATH = ROOT / "reports" / "renal_v2_experiments_checkpoint.json"
OUT_REPORT = ROOT / "reports" / "renal_v2_experiments.json"

MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
QUERY_INSTRUCTION = (
    "Instruct: Retrieve the medical evidence passage that directly supports this "
    "renal education query.\nQuery: "
)
MAX_SEQUENCE_LENGTH = 512
NORMALIZATION_VERSION = "none-v1"
RENDER_VERSION = "renal-v2-render-v1"
INITIAL_BATCH_SIZE = 16
CHUNKINGS = ("A_250", "B_400_overlap", "C_section_aware", "D_parent_child_v2", "E_sentence_evidence_300")
REPRESENTATIONS = ("content_only", "source_aware", "metadata_aware", "metadata_aware_v2")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic_npy(path: Path, value: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("wb") as handle:
        np.save(handle, value, allow_pickle=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def verified_dataset_sha(path: Path) -> str:
    sidecar = path.with_suffix(path.suffix + ".sha256")
    if not sidecar.is_file():
        raise RuntimeError(f"Missing dataset SHA sidecar: {sidecar}")
    expected = sidecar.read_text(encoding="utf-8").strip().split()[0].lower()
    actual = sha256_file(path)
    if actual != expected:
        raise RuntimeError(f"Dataset hash mismatch for {path.name}: expected {expected}, got {actual}")
    return actual


def load_queries() -> list[dict[str, Any]]:
    payload = json.loads(DEV_PATH.read_text(encoding="utf-8"))
    queries = [query for query in payload["queries"] if query.get("answerable")]
    if not queries:
        raise RuntimeError("RENAL-DEV-v2 contains no answerable queries")
    return queries


def load_registry() -> dict[str, dict[str, Any]]:
    payload = json.loads((META / "renal_source_registry_v2.json").read_text(encoding="utf-8"))
    return {
        item["document_id"]: item
        for item in payload["documents"]
        if item.get("v2_active", True)
    }


def load_chunks(chunking: str) -> list[dict[str, Any]]:
    folder = CHUNKS_ROOT / chunking
    chunks: list[dict[str, Any]] = []
    pattern = "*.json" if chunking == "D_parent_child_v2" else "*.chunks.json"
    collection = "children" if chunking == "D_parent_child_v2" else "chunks"
    for path in sorted(folder.glob(pattern)):
        chunks.extend(json.loads(path.read_text(encoding="utf-8")).get(collection, []))
    if not chunks:
        raise RuntimeError(f"No chunks found for {chunking} in {folder}")
    return chunks


def chunk_id(chunk: dict[str, Any]) -> str:
    value = chunk.get("child_chunk_id") or chunk.get("chunk_id")
    if not value:
        raise RuntimeError(f"Chunk lacks an identifier: {chunk}")
    return str(value)


def render_chunk(chunk: dict[str, Any], doc: dict[str, Any], representation: str) -> str:
    text = str(chunk.get("text", ""))
    title = str(doc.get("title", ""))
    document_id = str(chunk.get("document_id", ""))
    section_path = " > ".join(map(str, chunk.get("section_path", [])))
    topic_tags = ", ".join(map(str, doc.get("topic_tags", [])))
    role = str(doc.get("educational_classification", "SUPPORTING"))
    if representation == "content_only":
        return text
    if representation == "source_aware":
        return f"Source: {title} [{document_id}]\n{text}"
    if representation == "metadata_aware":
        return f"Topics: {topic_tags}\nSection: {section_path}\nSource: {title} [{document_id}]\n{text}"
    if representation == "metadata_aware_v2":
        return (
            "Specialty: Renal Medicine\n"
            f"Educational Role: {role}\nTopics: {topic_tags}\nSection: {section_path}\n"
            f"Source: {title} [{document_id}]\n{text}"
        )
    raise ValueError(f"Unknown representation: {representation}")


def parent_id(chunk: dict[str, Any]) -> str | None:
    if chunk.get("parent_section_id"):
        return str(chunk["parent_section_id"])
    if "source_block_index" in chunk:
        return f"{chunk['document_id']}-P{int(chunk['source_block_index']):04d}"
    return None


def is_relevant(chunk: dict[str, Any], query: dict[str, Any]) -> bool:
    if chunk.get("document_id") not in set(query.get("gold_document_ids", [])):
        return False
    if chunk_id(chunk) in set(query.get("gold_child_chunk_ids", [])):
        return True
    if parent_id(chunk) in set(query.get("gold_parent_section_ids", [])):
        return True
    gold_sections = {str(value).casefold() for value in query.get("gold_section_ids", [])}
    actual_sections = {str(value).casefold() for value in chunk.get("section_path", [])}
    return bool(gold_sections and gold_sections.intersection(actual_sections))


def metric_fraction(numerator: int, denominator: int) -> dict[str, float | int]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else 0.0,
    }


def compute_metrics(
    rankings: list[list[dict[str, Any]]],
    queries: list[dict[str, Any]],
    corpus: list[dict[str, Any]],
) -> dict[str, Any]:
    n = len(queries)
    hits = {1: 0, 3: 0, 5: 0, 10: 0}
    source_hits = 0
    authority_hits = 0
    authority_total = 0
    reciprocal_rank_sum = 0.0
    ndcg_sum = 0.0
    relevance_counts = [sum(is_relevant(chunk, query) for chunk in corpus) for query in queries]
    if any(count == 0 for count in relevance_counts):
        missing = [queries[index]["query_id"] for index, count in enumerate(relevance_counts) if count == 0]
        raise RuntimeError(f"Gold evidence cannot map to this chunking: {missing[:10]}")
    for query, ranked, relevant_total in zip(queries, rankings, relevance_counts):
        gold_docs = set(query.get("gold_document_ids", []))
        if any(chunk.get("document_id") in gold_docs for chunk in ranked[:10]):
            source_hits += 1
        if query.get("authority_sensitive", False):
            authority_total += 1
            if any(chunk.get("document_id") in gold_docs for chunk in ranked[:5]):
                authority_hits += 1
        first_rank: int | None = None
        dcg = 0.0
        for rank, chunk in enumerate(ranked[:10], 1):
            if is_relevant(chunk, query):
                if first_rank is None:
                    first_rank = rank
                dcg += 1.0 / math.log2(rank + 1)
        ideal_count = min(relevant_total, 10)
        idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_count + 1))
        ndcg_sum += dcg / idcg
        if first_rank is not None:
            reciprocal_rank_sum += 1.0 / first_rank
            for cutoff in hits:
                hits[cutoff] += int(first_rank <= cutoff)
    return {
        "n": n,
        "hit_at_1": metric_fraction(hits[1], n),
        "hit_at_3": metric_fraction(hits[3], n),
        "hit_at_5": metric_fraction(hits[5], n),
        "hit_at_10": metric_fraction(hits[10], n),
        "mrr": reciprocal_rank_sum / n,
        "ndcg_at_10": ndcg_sum / n,
        "gold_source_recall_at_10": metric_fraction(source_hits, n),
        "authority_sensitive_at_5": metric_fraction(authority_hits, authority_total),
    }


def model_revision(model: SentenceTransformer) -> str:
    try:
        revision = model[0].auto_model.config._commit_hash
        if revision:
            return str(revision)
    except (AttributeError, IndexError, TypeError):
        pass
    return "unavailable-local-cache"


def encode_gpu(
    model: SentenceTransformer,
    texts: list[str],
    label: str,
    initial_batch_size: int = INITIAL_BATCH_SIZE,
) -> tuple[np.ndarray, int]:
    batch_size = initial_batch_size
    while True:
        started = time.perf_counter()
        print(
            f"{label} ENCODE_START PASSAGES={len(texts)} BATCH_SIZE={batch_size}",
            flush=True,
        )
        try:
            with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.float16):
                matrix = model.encode(
                    texts,
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=True,
                    device="cuda",
                )
            elapsed = time.perf_counter() - started
            print(
                f"{label} ENCODE_COMPLETE PASSAGES={len(texts)}/{len(texts)} "
                f"BATCH_SIZE={batch_size} ELAPSED={elapsed:.1f}s",
                flush=True,
            )
            return np.asarray(matrix, dtype=np.float32), batch_size
        except torch.OutOfMemoryError:
            torch.cuda.empty_cache()
            if batch_size == 1:
                raise
            batch_size = max(1, batch_size // 2)
            print(f"{label} CUDA_OOM reducing batch size to {batch_size}", flush=True)


def embedding_cache_key(
    kind: str,
    revision: str,
    chunking: str,
    representation: str,
    corpus_sha: str,
) -> str:
    return canonical_sha(
        {
            "kind": kind,
            "model_id": MODEL_ID,
            "model_revision": revision,
            "chunking": chunking,
            "representation": representation,
            "render_version": RENDER_VERSION,
            "corpus_sha": corpus_sha,
            "max_sequence_length": MAX_SEQUENCE_LENGTH,
            "normalization_version": NORMALIZATION_VERSION,
        }
    )


def load_embedding_cache(key: str, expected_ids: list[str]) -> np.ndarray | None:
    matrix_path = CACHE_ROOT / f"{key}.npy"
    metadata_path = CACHE_ROOT / f"{key}.json"
    if not matrix_path.is_file() or not metadata_path.is_file():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata["cache_key"] != key or metadata["ordered_ids"] != expected_ids:
            return None
        if metadata["embedding_sha256"] != sha256_file(matrix_path):
            return None
        matrix = np.load(matrix_path, allow_pickle=False)
        if list(matrix.shape) != metadata["shape"] or matrix.shape[0] != len(expected_ids):
            return None
        return np.asarray(matrix, dtype=np.float32)
    except (KeyError, OSError, ValueError, json.JSONDecodeError):
        return None


def save_embedding_cache(key: str, ids: list[str], matrix: np.ndarray, metadata: dict[str, Any]) -> None:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    matrix_path = CACHE_ROOT / f"{key}.npy"
    atomic_npy(matrix_path, matrix)
    atomic_json(
        CACHE_ROOT / f"{key}.json",
        {
            **metadata,
            "cache_key": key,
            "ordered_ids": ids,
            "shape": list(matrix.shape),
            "dtype": str(matrix.dtype),
            "embedding_sha256": sha256_file(matrix_path),
        },
    )


def load_checkpoint(dataset_sha: str, revision: str) -> dict[str, Any]:
    if CHECKPOINT_PATH.is_file():
        value = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
        if value.get("dataset_sha256") != dataset_sha or value.get("model_revision") != revision:
            raise RuntimeError("Existing matrix checkpoint belongs to different immutable inputs")
        return value
    return {
        "report_id": "RENAL-V2-EXPERIMENT-MATRIX-CHECKPOINT",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_sha256": dataset_sha,
        "model_id": MODEL_ID,
        "model_revision": revision,
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "query_instruction": QUERY_INSTRUCTION,
        "results": [],
    }


def requested_configs(only: str | None, smoke: bool) -> list[tuple[str, str]]:
    if smoke:
        return [("D_parent_child_v2", "metadata_aware_v2")]
    if only:
        try:
            chunking, representation = only.split(":", 1)
        except ValueError as exc:
            raise ValueError("--only must be CHUNKING:REPRESENTATION") from exc
        if chunking not in CHUNKINGS or representation not in REPRESENTATIONS:
            raise ValueError(f"Unknown configuration: {only}")
        return [(chunking, representation)]
    return [(chunking, representation) for chunking in CHUNKINGS for representation in REPRESENTATIONS]


def top_rankings(similarities: np.ndarray, chunks: list[dict[str, Any]], count: int) -> list[list[dict[str, Any]]]:
    rankings: list[list[dict[str, Any]]] = []
    for query_index in range(similarities.shape[1]):
        scores = similarities[:, query_index]
        candidate_count = min(count, len(scores))
        indices = np.argpartition(scores, -candidate_count)[-candidate_count:]
        ordered = indices[np.argsort(scores[indices])[::-1]]
        rankings.append([chunks[int(index)] for index in ordered])
    return rankings


def metric_summary(metrics: dict[str, Any]) -> str:
    return (
        f"Hit@1={metrics['hit_at_1']['numerator']}/{metrics['n']}="
        f"{metrics['hit_at_1']['value']:.4f} "
        f"Hit@5={metrics['hit_at_5']['numerator']}/{metrics['n']}="
        f"{metrics['hit_at_5']['value']:.4f} MRR={metrics['mrr']:.4f} "
        f"nDCG@10={metrics['ndcg_at_10']:.4f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Run the representative D x metadata-v2 config")
    parser.add_argument("--only", help="Run one CHUNKING:REPRESENTATION configuration")
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for Renal V2 Qwen experiments; CPU fallback is prohibited")
    print(f"PYTHON={sys.executable}", flush=True)
    print(f"PYTHON_VERSION={platform.python_version()}", flush=True)
    print(f"TORCH={torch.__version__}", flush=True)
    print(f"TORCH_CUDA={torch.version.cuda}", flush=True)
    print(f"DEVICE={torch.cuda.get_device_name(0)}", flush=True)
    dataset_sha = verified_dataset_sha(DEV_PATH)
    queries = load_queries()
    registry = load_registry()
    print(f"DEV_SHA256={dataset_sha} ANSWERABLE_N={len(queries)} DOCUMENTS={len(registry)}", flush=True)
    print(f"LOADING_MODEL={MODEL_ID} OFFLINE=true", flush=True)
    model = SentenceTransformer(MODEL_ID, device="cuda", local_files_only=True)
    model.max_seq_length = MAX_SEQUENCE_LENGTH
    model.eval()
    revision = model_revision(model)
    print(f"MODEL_REVISION={revision}", flush=True)
    query_texts = [QUERY_INSTRUCTION + query["query"] for query in queries]
    query_ids = [query["query_id"] for query in queries]
    query_corpus_sha = canonical_sha(list(zip(query_ids, query_texts)))
    query_key = embedding_cache_key("queries", revision, "queries", "instruction-a", query_corpus_sha)
    query_embeddings = load_embedding_cache(query_key, query_ids)
    if query_embeddings is None:
        print(f"QUERY_CACHE=MISS KEY={query_key}", flush=True)
        query_embeddings, query_batch = encode_gpu(model, query_texts, "QUERIES")
        save_embedding_cache(
            query_key,
            query_ids,
            query_embeddings,
            {"kind": "queries", "dataset_sha256": dataset_sha, "batch_size": query_batch},
        )
    else:
        print(f"QUERY_CACHE=HIT KEY={query_key} HASH_VERIFIED=true", flush=True)
    checkpoint = load_checkpoint(dataset_sha, revision)
    completed = {(item["chunking"], item["representation"]) for item in checkpoint["results"]}
    configs = requested_configs(args.only, args.smoke)
    for config_index, (chunking, representation) in enumerate(configs, 1):
        if (chunking, representation) in completed:
            print(f"CONFIG {config_index:02d}/{len(configs):02d} RESUME=SKIP {chunking} x {representation}", flush=True)
            continue
        started = time.perf_counter()
        chunks = load_chunks(chunking)
        ids = [chunk_id(chunk) for chunk in chunks]
        rendered = [render_chunk(chunk, registry.get(str(chunk["document_id"]), {}), representation) for chunk in chunks]
        corpus_sha = canonical_sha(list(zip(ids, rendered)))
        key = embedding_cache_key("corpus", revision, chunking, representation, corpus_sha)
        print(
            f"CONFIG {config_index:02d}/{len(configs):02d} CHUNKING={chunking} "
            f"REPRESENTATION={representation} DEVICE=cuda PASSAGES={len(chunks)}",
            flush=True,
        )
        embeddings = load_embedding_cache(key, ids)
        cache_hit = embeddings is not None
        if embeddings is None:
            print(f"CACHE=MISS KEY={key}", flush=True)
            embeddings, final_batch = encode_gpu(model, rendered, f"CONFIG {config_index:02d}/{len(configs):02d}")
            save_embedding_cache(
                key,
                ids,
                embeddings,
                {
                    "kind": "corpus",
                    "model_id": MODEL_ID,
                    "model_revision": revision,
                    "chunking": chunking,
                    "representation": representation,
                    "render_version": RENDER_VERSION,
                    "corpus_sha256": corpus_sha,
                    "max_sequence_length": MAX_SEQUENCE_LENGTH,
                    "normalization_version": NORMALIZATION_VERSION,
                    "batch_size": final_batch,
                },
            )
        else:
            final_batch = None
            print(f"CACHE=HIT KEY={key} HASH_VERIFIED=true", flush=True)
        similarities = embeddings @ query_embeddings.T
        rankings = top_rankings(similarities, chunks, 10)
        metrics = compute_metrics(rankings, queries, chunks)
        elapsed = time.perf_counter() - started
        entry = {
            "chunking": chunking,
            "representation": representation,
            "model": MODEL_ID,
            "model_revision": revision,
            "dataset_sha256": dataset_sha,
            "corpus_sha256": corpus_sha,
            "device": f"cuda:0 ({torch.cuda.get_device_name(0)})",
            "precision": "fp16 autocast; float32 normalized embedding cache",
            "max_sequence_length": MAX_SEQUENCE_LENGTH,
            "chunk_count": len(chunks),
            "elapsed_wall_seconds": round(elapsed, 3),
            "embedding_cache_key": key,
            "cache_hit": cache_hit,
            "batch_size": final_batch,
            "metrics": metrics,
        }
        checkpoint["results"].append(entry)
        checkpoint["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        atomic_json(CHECKPOINT_PATH, checkpoint)
        print(f"CHECKPOINT_WRITTEN={CHECKPOINT_PATH} {metric_summary(metrics)} ELAPSED={elapsed:.1f}s", flush=True)
    if len(checkpoint["results"]) == len(CHUNKINGS) * len(REPRESENTATIONS):
        report = {**checkpoint, "report_id": "RENAL-V2-EXPERIMENT-MATRIX", "complete": True}
        atomic_json(OUT_REPORT, report)
        print(f"MATRIX_COMPLETE={OUT_REPORT}", flush=True)
    else:
        print(f"CHECKPOINT_COMPLETE_CONFIGS={len(checkpoint['results'])}/16", flush=True)


if __name__ == "__main__":
    main()
