"""
MedicalPlab Renal V4 — Phase 10: Build and Cache Section Representations
========================================================================
Builds two source-derived section representations for all 629 unique sections:
A. Centroid / aggregate of the section's existing child body embeddings
B. Structural vector: Document Title + Full Section Path + Section Heading

Persists to Data/experiments/renal_v4/cache/ with metadata and SHA256 checksums.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
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

from transformers import AutoModel, AutoTokenizer

ROOT = _ROOT
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
REGISTRY_PATH = ROOT / "Data" / "metadata" / "renal_source_registry_v2.json"
CORPUS_CACHE_PATH = ROOT / "Data" / "experiments" / "renal_v3" / "cache" / "all23_corpus_embeddings.npy"
OUT_CACHE_DIR = ROOT / "Data" / "experiments" / "renal_v4" / "cache"

EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"


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


def main():
    print("=" * 70)
    print("PHASE 10: BUILDING SECTION REPRESENTATIONS FOR RENAL V4")
    print("=" * 70)

    OUT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    assert torch.cuda.is_available(), "CUDA required!"
    device = torch.device("cuda:0")

    # Load corpus embeddings
    assert CORPUS_CACHE_PATH.exists(), f"Corpus embeddings missing: {CORPUS_CACHE_PATH}"
    corpus_embs = np.load(CORPUS_CACHE_PATH)
    print(f"Loaded corpus embeddings: {corpus_embs.shape}")

    # Load registry
    reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    doc_titles = {d["document_id"]: d.get("title", "") for d in reg.get("documents", [])}

    # Load chunks and map to sections
    chunks = []
    sections = {} # (did, path_tuple) -> dict
    chunk_to_section = []

    for p in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        payload = json.loads(p.read_text(encoding="utf-8"))
        for ch in payload.get("chunks", []):
            c_idx = len(chunks)
            chunks.append(ch)
            did = ch["document_id"]
            sp = tuple(ch.get("section_path", []))
            sec_key = (did, sp)
            if sec_key not in sections:
                sections[sec_key] = {
                    "sec_idx": len(sections),
                    "document_id": did,
                    "doc_title": doc_titles.get(did, ""),
                    "heading": ch.get("heading", ""),
                    "section_path": list(sp),
                    "chunk_indices": []
                }
            sections[sec_key]["chunk_indices"].append(c_idx)
            chunk_to_section.append(sections[sec_key]["sec_idx"])

    sec_list = sorted(list(sections.values()), key=lambda x: x["sec_idx"])
    n_sections = len(sec_list)
    print(f"Loaded {len(chunks)} chunks mapped to {n_sections} unique sections.")

    # 1. Centroid representations
    print("Computing section centroid embeddings from child chunks...")
    centroid_embs = np.zeros((n_sections, 1024), dtype=np.float32)
    for s in sec_list:
        idx = s["sec_idx"]
        c_idxs = s["chunk_indices"]
        mean_emb = np.mean(corpus_embs[c_idxs], axis=0)
        norm = np.linalg.norm(mean_emb)
        centroid_embs[idx] = mean_emb / max(norm, 1e-9)

    centroid_path = OUT_CACHE_DIR / "all629_section_centroid_embeddings.npy"
    np.save(centroid_path, centroid_embs)
    print(f"Saved centroid embeddings: {centroid_embs.shape} -> {centroid_path}")

    # 2. Structural text representations
    print("Encoding structural section texts (Doc Title + Section Path + Heading)...")
    embed_tok = AutoTokenizer.from_pretrained(EMBED_MODEL_ID, local_files_only=True)
    embed_model = AutoModel.from_pretrained(EMBED_MODEL_ID, local_files_only=True).to(device)
    embed_model.eval()

    structural_texts = []
    for s in sec_list:
        path_str = " > ".join(s["section_path"]) if s["section_path"] else s["heading"]
        text = f"Document: {s['doc_title']}\nSection: {path_str}\nHeading: {s['heading']}"
        structural_texts.append(text)

    structural_embs = encode_texts(structural_texts, embed_tok, embed_model, device)
    structural_path = OUT_CACHE_DIR / "all629_section_structural_embeddings.npy"
    np.save(structural_path, structural_embs)
    print(f"Saved structural embeddings: {structural_embs.shape} -> {structural_path}")

    # 3. Metadata
    meta_payload = {
        "n_sections": n_sections,
        "n_chunks": len(chunks),
        "sections": sec_list,
        "chunk_to_section": chunk_to_section,
        "centroid_sha256": sha256_file(centroid_path),
        "structural_sha256": sha256_file(structural_path)
    }
    meta_path = OUT_CACHE_DIR / "sections_metadata.json"
    meta_path.write_text(json.dumps(meta_payload, indent=2), encoding="utf-8")
    meta_sha = sha256_file(meta_path)
    meta_path.with_suffix(".json.sha256").write_text(f"{meta_sha}  {meta_path.name}\n", encoding="utf-8")
    print(f"Saved section metadata: {meta_path} (SHA: {meta_sha})")


if __name__ == "__main__":
    main()
