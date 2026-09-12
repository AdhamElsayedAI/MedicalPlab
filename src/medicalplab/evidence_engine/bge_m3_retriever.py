"""
MedicalPlab Shared Evidence Engine V2 — BGE-M3 Exhaustive Retriever
===================================================================
Precomputes and persists representations for EVERY Renal evidence passage:
A. Dense representation (dim 1024)
B. Learned sparse representation (lexical weights)
C. Multi-vector / ColBERT-style representation (late interaction)

Scores ALL 2,691 passages in the corpus exhaustively for every query:
- No document gates
- No section gates
- No dense Top-K starvation
"""

import gc
import json
import logging
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

from medicalplab.evidence_engine.models import QueryRepresentation, RetrievedCandidate

logger = logging.getLogger(__name__)

BGE_M3_ID = "BAAI/bge-m3"
BGE_M3_REV = "5617a9f61b028005a4858fdac845db406aefb181"
_LOCAL_SNAP = Path.home() / ".cache" / "huggingface" / "hub" / "models--BAAI--bge-m3" / "snapshots" / BGE_M3_REV


class BGEM3ExhaustiveRetriever:
    """Exhaustive all-passage retriever using BAAI/bge-m3 multi-vector representation."""

    def __init__(
        self,
        data_root: Path | str,
        model: Any = None,
        model_id: str | None = None,
        revision: str = BGE_M3_REV,
        cache_dir: Path | str | None = None,
        device: str | None = None,
    ):
        self.data_root = Path(data_root)
        self.model = model
        if model_id is not None:
            self.model_id = model_id
        elif _LOCAL_SNAP.exists():
            self.model_id = str(_LOCAL_SNAP)
        else:
            self.model_id = BGE_M3_ID
        self.revision = revision
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.cache_dir = Path(cache_dir) if cache_dir else (self.data_root.parent / ".cache" / "evidence_engine" / "bge_m3_corpus")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.chunks: dict[str, dict[str, Any]] = {}
        self.ordered_chunk_ids: list[str] = []
        self.corpus_dense: np.ndarray | None = None
        self.corpus_sparse: list[dict[str, float]] | None = None
        self.corpus_colbert: list[np.ndarray | torch.Tensor] | None = None

        self._load_corpus_chunks()

    def _load_corpus_chunks(self):
        chunks_dir = self.data_root / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
        chunk_files = sorted(chunks_dir.glob("*.chunks.json"))
        for p in chunk_files:
            try:
                data = json.loads(p.read_bytes())
                doc_id = data.get("document_id", "")
                title = data.get("document_title", data.get("title", doc_id))
                for ch in data.get("chunks", []):
                    cid = ch.get("chunk_id")
                    ch["document_id"] = doc_id
                    ch["doc_title"] = title
                    self.chunks[cid] = ch
                    self.ordered_chunk_ids.append(cid)
            except Exception as e:
                logger.warning(f"Error loading {p}: {e}")

        logger.info(f"Loaded {len(self.chunks)} corpus chunks for BGE-M3 retrieval.")

    def load_model(self):
        if self.model is not None:
            return self.model

        from FlagEmbedding import BGEM3FlagModel
        logger.info(f"Loading {self.model_id} (revision {self.revision[:10]})...")
        t0 = time.perf_counter()
        self.model = BGEM3FlagModel(
            self.model_id,
            use_fp16=True,
            device=self.device,
        )
        logger.info(f"Loaded BGE-M3 in {time.perf_counter() - t0:.2f}s")
        return self.model

    def ensure_corpus_representations(self, batch_size: int = 16):
        """Precomputes and persists dense, sparse, and ColBERT representations on disk."""
        meta_path = self.cache_dir / "corpus_metadata.json"
        dense_path = self.cache_dir / "dense_embeddings.npy"
        sparse_path = self.cache_dir / "sparse_weights.json"
        colbert_path = self.cache_dir / "colbert_vecs.pt"

        if meta_path.exists() and dense_path.exists() and sparse_path.exists() and colbert_path.exists():
            logger.info("Loading precomputed BGE-M3 representations from disk cache...")
            t0 = time.perf_counter()
            self.corpus_dense = np.load(dense_path)
            self.corpus_sparse = json.loads(sparse_path.read_text(encoding="utf-8"))
            self.corpus_colbert = torch.load(colbert_path, map_location="cpu")
            logger.info(f"Loaded BGE-M3 cached representations in {time.perf_counter() - t0:.2f}s.")
            return

        logger.info(f"Precomputing BGE-M3 representations for {len(self.ordered_chunk_ids)} passages...")
        if self.model is None:
            self.load_model()

        texts = []
        metadata = []
        for cid in self.ordered_chunk_ids:
            ch = self.chunks[cid]
            sec_str = " > ".join(ch.get("section_path", [])) if ch.get("section_path") else (ch.get("heading") or "General")
            passage_text = f"{ch.get('doc_title', '')} | {sec_str} | {ch.get('heading', '')}\n{ch.get('text', '')}"
            texts.append(passage_text)
            metadata.append({
                "chunk_id": cid,
                "document_id": ch.get("document_id"),
                "doc_title": ch.get("doc_title"),
                "section_path": ch.get("section_path", []),
                "heading": ch.get("heading", ""),
                "text": ch.get("text", ""),
            })

        t0 = time.perf_counter()
        output = self.model.encode(
            texts,
            batch_size=batch_size,
            max_length=512,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=True,
        )
        logger.info(f"Encoded all passages in {time.perf_counter() - t0:.1f}s.")

        self.corpus_dense = output["dense_vecs"].astype(np.float32)
        self.corpus_sparse = [{k: float(v) for k, v in d.items()} for d in output["lexical_weights"]]
        # Convert colbert vectors to float16 tensors for compact storage
        self.corpus_colbert = [torch.tensor(vec, dtype=torch.float16) for vec in output["colbert_vecs"]]

        # Persist to disk
        meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
        np.save(dense_path, self.corpus_dense)
        sparse_path.write_text(json.dumps(self.corpus_sparse, ensure_ascii=False), encoding="utf-8")
        torch.save(self.corpus_colbert, colbert_path)
        logger.info(f"Persisted BGE-M3 artifacts to {self.cache_dir}")

    def retrieve_exhaustive(
        self,
        query: str | QueryRepresentation,
        top_k: int = 100,
        mode: str = "hybrid",
    ) -> list[RetrievedCandidate]:
        """Exhaustively score all 2,691 passages against the query."""
        if isinstance(query, QueryRepresentation):
            query_str = query.canonical_query or query.original_query
        else:
            query_str = str(query)

        if self.corpus_dense is None:
            self.ensure_corpus_representations()

        if self.model is None:
            self.load_model()

        # Encode query
        q_out = self.model.encode(
            [query_str],
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=True,
        )
        q_dense = q_out["dense_vecs"][0].astype(np.float32)
        q_sparse = q_out["lexical_weights"][0]
        q_colbert = q_out["colbert_vecs"][0]

        # 1. Dense scoring (vectorized inner product)
        dense_scores = np.dot(self.corpus_dense, q_dense)

        # 2. Sparse lexical matching score
        sparse_scores = np.array([
            self.model.compute_lexical_matching_score(q_sparse, p_sp)
            for p_sp in self.corpus_sparse
        ], dtype=np.float32)

        # 3. ColBERT multi-vector late-interaction score
        colbert_scores = np.array([
            float(self.model.colbert_score(q_colbert, p_col.cpu().float().numpy() if hasattr(p_col, "cpu") else p_col))
            for p_col in self.corpus_colbert
        ], dtype=np.float32)

        # Score fusion
        if mode == "colbert":
            final_scores = colbert_scores
        else:
            # Official BGE-M3 hybrid weighting
            final_scores = 0.4 * dense_scores + 0.2 * sparse_scores + 0.4 * colbert_scores

        # Rank all passages
        ranked_indices = np.argsort(final_scores)[::-1]
        if top_k is not None and top_k > 0:
            ranked_indices = ranked_indices[:top_k]

        candidates = []
        for idx in ranked_indices:
            cid = self.ordered_chunk_ids[idx]
            ch = self.chunks[cid]
            candidates.append(RetrievedCandidate(
                chunk_id=cid,
                document_id=ch.get("document_id", ""),
                section_path=ch.get("section_path", []),
                heading=ch.get("heading", ""),
                text=ch.get("text", ""),
                doc_title=ch.get("doc_title", ""),
                fused_score=float(final_scores[idx]),
                channel_scores={
                    "dense": float(dense_scores[idx]),
                    "sparse": float(sparse_scores[idx]),
                    "colbert": float(colbert_scores[idx]),
                },
            ))

        return candidates
