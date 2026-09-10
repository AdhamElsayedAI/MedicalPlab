"""Phase 11: Controlled Contextual Representation Experiment on GPU.

Compares:
  A. content_only baseline
  B. contextual_path_prefix: Document: {title}\nSection: {section_path}\n\n{text}

Evaluates against frozen V3 DEV qrels (N=69).
Interruption-safe: caches embeddings in Data/experiments/renal_v3/cache/.
Hard gate: CUDA only.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent
DEV_QRELS = ROOT / "evaluation" / "renal" / "v3" / "renal-dev-v3-qrels.json"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
CACHE_DIR = ROOT / "Data" / "experiments" / "renal_v3" / "cache"
REPORTS_DIR = ROOT / "reports" / "renal_v3"

MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
MODEL_REVISION = "97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3"
BATCH_SIZE = 16


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def render_contextual_chunk(chunk: dict, doc_title: str) -> str:
    sec_path = " > ".join(chunk.get("section_path", []))
    text = chunk.get("text", "")
    return f"Document: {doc_title}\nSection: {sec_path}\n\n{text}"


def load_dev_corpus() -> tuple[list[dict], list[str]]:
    reg_data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    doc_titles = {d["document_id"]: d.get("title", "") for d in reg_data.get("documents", [])}
    
    # DEV only spans DOC-0001 through DOC-0023
    chunks = []
    rendered_texts = []
    for f in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        doc_id = f.name.replace(".chunks.json", "")
        # Match the 21 DEV evaluation documents (DOC-0001 to DOC-0023, excluding 0024 and 0025 for DEV parity)
        if doc_id in ("DOC-PMC-RENAL-0024", "DOC-PMC-RENAL-0025"):
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        title = doc_titles.get(doc_id, "")
        for ch in data.get("chunks", []):
            chunks.append(ch)
            rendered_texts.append(render_contextual_chunk(ch, title))
    return chunks, rendered_texts


def encode_texts(texts: list[str], tokenizer, model, device: torch.device) -> np.ndarray:
    all_embeddings = []
    batch_size = BATCH_SIZE
    n = len(texts)
    
    print(f"Encoding {n} texts with batch size {batch_size} on {device}...")
    start_time = time.time()
    
    with torch.inference_mode():
        for i in range(0, n, batch_size):
            batch = texts[i : i + batch_size]
            try:
                encoded = tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                ).to(device)
                
                outputs = model(**encoded)
                # Mean pooling with attention mask
                mask = encoded["attention_mask"].unsqueeze(-1)
                emb = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
                # L2 normalize
                emb = torch.nn.functional.normalize(emb, p=2, dim=1)
                all_embeddings.append(emb.cpu().numpy())
            except torch.cuda.OutOfMemoryError:
                print(f"CUDA OOM at batch {i}. Halving batch size to {batch_size // 2}...")
                torch.cuda.empty_cache()
                batch_size = max(1, batch_size // 2)
                # Retry single item or smaller batch
                sub_batch = batch[:batch_size]
                encoded = tokenizer(sub_batch, padding=True, truncation=True, max_length=512, return_tensors="pt").to(device)
                outputs = model(**encoded)
                mask = encoded["attention_mask"].unsqueeze(-1)
                emb = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
                emb = torch.nn.functional.normalize(emb, p=2, dim=1)
                all_embeddings.append(emb.cpu().numpy())
                
            if (i // batch_size) % 20 == 0:
                elapsed = time.time() - start_time
                rate = (i + len(batch)) / elapsed if elapsed > 0 else 0
                print(f"  Progress: {i + len(batch)}/{n} chunks ({rate:.1f} chunks/sec)")
                
    elapsed = time.time() - start_time
    print(f"Completed encoding in {elapsed:.2f}s ({n / elapsed:.1f} chunks/sec).")
    return np.vstack(all_embeddings).astype(np.float32)


def main():
    print("=" * 70)
    print("PHASE 11: CONTEXTUAL REPRESENTATION EXPERIMENT")
    print("=" * 70)
    
    # Hard CUDA gate
    print(f"Python: {sys.executable}")
    print(f"Torch version: {torch.__version__}")
    print(f"CUDA version: {torch.version.cuda}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if not torch.cuda.is_available():
        print("HARD GATE FAILED: CUDA not available. Terminating compute stage.")
        sys.exit(1)
        
    device = torch.device("cuda:0")
    print(f"Device: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / (1024**2):.1f} MiB")
    
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load chunks and render
    chunks, rendered_texts = load_dev_corpus()
    print(f"Loaded {len(chunks)} chunks for contextual representation.")
    
    # Check cache
    cache_key = f"b400_contextual_{sha256_text(''.join(rendered_texts[:50]))[:16]}"
    npy_path = CACHE_DIR / f"{cache_key}.npy"
    json_path = CACHE_DIR / f"{cache_key}.json"
    
    if npy_path.exists() and json_path.exists():
        print(f"Loading cached embeddings from {npy_path}...")
        contextual_embeddings = np.load(npy_path)
    else:
        print(f"Loading tokenizer & model: {MODEL_ID} (rev: {MODEL_REVISION[:12]})...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION, trust_remote_code=True)
        model = AutoModel.from_pretrained(MODEL_ID, revision=MODEL_REVISION, trust_remote_code=True, torch_dtype=torch.float16)
        model = model.to(device).eval()
        
        contextual_embeddings = encode_texts(rendered_texts, tokenizer, model, device)
        
        # Save cache atomically
        np.save(npy_path, contextual_embeddings)
        json_path.write_text(json.dumps({
            "cache_key": cache_key,
            "kind": "corpus",
            "chunking": "B_400_overlap",
            "representation": "contextual_path_prefix",
            "n_chunks": len(chunks),
            "model_id": MODEL_ID,
            "model_revision": MODEL_REVISION,
            "created_at": time.time()
        }, indent=2), encoding="utf-8")
        print(f"Saved cache to {npy_path}")
        
    # Load query embeddings from existing V2 cache
    v2_cache = ROOT / "Data" / "experiments" / "renal_v2" / "cache"
    query_arr = None
    for f in v2_cache.glob("*.json"):
        meta = json.loads(f.read_text(encoding="utf-8"))
        if meta.get("kind") == "queries":
            query_arr = np.load(v2_cache / f"{meta['cache_key']}.npy")
            break
            
    if query_arr is None:
        raise RuntimeError("Missing query embeddings in V2 cache")
        
    print(f"Query embeddings shape: {query_arr.shape}")
    print(f"Contextual corpus embeddings shape: {contextual_embeddings.shape}")
    
    # Evaluate against frozen V3 DEV qrels
    qrels_data = json.loads(DEV_QRELS.read_text(encoding="utf-8"))
    queries = [q for q in qrels_data["queries"] if q.get("answerable")]
    n_queries = len(queries)
    
    sims = np.dot(contextual_embeddings, query_arr.T) # shape: (2558, 69)
    
    k_list = [1, 3, 5, 10]
    cand_k_list = [10, 20, 30, 50, 100]
    
    doc_hits = {k: 0 for k in k_list}
    parent_hits = {k: 0 for k in k_list}
    passage_hits = {k: 0 for k in k_list}
    candidate_hits = {k: 0 for k in cand_k_list}
    
    reciprocal_ranks = []
    ndcg_list = []
    
    for q_idx, q in enumerate(queries):
        gold_docs = set(q.get("gold_document_ids", []))
        gold_parents = set(q.get("gold_parent_section_ids", []))
        gold_chunks = set(q.get("gold_child_chunk_ids", []))
        
        scores = sims[:, q_idx]
        top100_idx = np.argsort(scores)[::-1][:100]
        ranked_chunks = [chunks[i] for i in top100_idx if i < len(chunks)]
        
        for k in k_list:
            if any(item.get("document_id") in gold_docs for item in ranked_chunks[:k]):
                doc_hits[k] += 1
            if any(item.get("parent_section_id") in gold_parents for item in ranked_chunks[:k]):
                parent_hits[k] += 1
                
        first_rel_rank = None
        for rank, item in enumerate(ranked_chunks[:10], start=1):
            if item.get("chunk_id") in gold_chunks:
                if first_rel_rank is None:
                    first_rel_rank = rank
                for k in k_list:
                    if rank <= k:
                        passage_hits[k] += 1
                break
                
        if first_rel_rank is not None:
            reciprocal_ranks.append(1.0 / first_rel_rank)
            ndcg_list.append(1.0 / np.log2(first_rel_rank + 1))
        else:
            reciprocal_ranks.append(0.0)
            ndcg_list.append(0.0)
            
        for ck in cand_k_list:
            if any(item.get("chunk_id") in gold_chunks for item in ranked_chunks[:ck]):
                candidate_hits[ck] += 1
                
    mrr = float(np.mean(reciprocal_ranks))
    ndcg10 = float(np.mean(ndcg_list))
    
    # Load baseline results for direct comparison
    base_rep = json.loads((REPORTS_DIR / "renal_v3_baseline_evaluation.json").read_text(encoding="utf-8"))
    bm = base_rep["metrics"]
    
    print("\n" + "=" * 70)
    print("REPRESENTATION COMPARISON ON FROZEN V3 DEV QRELS (N=69)")
    print("=" * 70)
    print(f"{'Metric':<25} {'Baseline (content_only)':>25} {'Contextual Prefix':>20} {'Delta':>10}")
    print("-" * 80)
    
    for k in [1, 3, 5, 10]:
        b_val = bm["passage_retrieval"][f"PassageHit@{k}"]["value"]
        c_val = passage_hits[k] / n_queries
        delta = c_val - b_val
        print(f"{f'PassageHit@{k}':<25} {b_val:>25.4f} {c_val:>20.4f} {delta:>+10.4f}")
        
    b_mrr = bm["mrr"]
    d_mrr = mrr - b_mrr
    print(f"{'MRR':<25} {b_mrr:>25.4f} {mrr:>20.4f} {d_mrr:>+10.4f}")
    
    b_ndcg = bm["ndcg_at_10"]
    d_ndcg = ndcg10 - b_ndcg
    print(f"{'nDCG@10':<25} {b_ndcg:>25.4f} {ndcg10:>20.4f} {d_ndcg:>+10.4f}")
    
    print("-" * 80)
    for ck in cand_k_list:
        b_cand = bm["candidate_recall"][f"CandidateHit@{ck}"]["value"]
        c_cand = candidate_hits[ck] / n_queries
        d_cand = c_cand - b_cand
        print(f"{f'CandidateHit@{ck}':<25} {b_cand:>25.4f} {c_cand:>20.4f} {d_cand:>+10.4f}")
        
    # Decision
    decision = "KEEP" if (passage_hits[1]/n_queries >= bm["passage_retrieval"]["PassageHit@1"]["value"] or mrr >= b_mrr) else "DISCARD"
    print(f"\nDecision: {decision}")
    
    out_payload = {
        "report_id": "RENAL-V3-CONTEXTUAL-REPRESENTATION",
        "representation": "contextual_path_prefix",
        "chunking": "B_400_overlap",
        "n_queries": n_queries,
        "metrics": {
            "document_hit": {f"DocumentHit@{k}": doc_hits[k] / n_queries for k in k_list},
            "parent_section_hit": {f"ParentSectionHit@{k}": parent_hits[k] / n_queries for k in k_list},
            "passage_hit": {f"PassageHit@{k}": passage_hits[k] / n_queries for k in k_list},
            "candidate_hit": {f"CandidateHit@{ck}": candidate_hits[ck] / n_queries for ck in cand_k_list},
            "mrr": mrr,
            "ndcg_at_10": ndcg10
        },
        "baseline_metrics": bm,
        "delta": {
            "passage_hit_at_1": passage_hits[1] / n_queries - bm["passage_retrieval"]["PassageHit@1"]["value"],
            "mrr": mrr - b_mrr,
            "ndcg_at_10": ndcg10 - b_ndcg,
            "candidate_hit_at_50": candidate_hits[50] / n_queries - bm["candidate_recall"]["CandidateHit@50"]["value"]
        },
        "decision": decision
    }
    
    out_path = REPORTS_DIR / "renal_v3_contextual_representation.json"
    out_path.write_text(json.dumps(out_payload, indent=2), encoding="utf-8")
    print(f"Wrote report: {out_path}")


if __name__ == "__main__":
    main()
