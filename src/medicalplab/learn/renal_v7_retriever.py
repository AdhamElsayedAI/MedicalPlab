"""
MedicalPlab Renal V7 — Multi-Channel Retrieval Engine & Structured Reranker
===========================================================================
Implements product-grade multi-channel candidate acquisition and structured cross-encoder reranking:
1. Query canonicalization (acronyms, spelling, units, comparators, entities).
2. Multi-channel candidate acquisition:
   - Channel A: Qwen3-Embedding dense semantic dot-product with document prior
   - Channel B: RenalBM25Index Okapi BM25 lexical term matching
   - Channel C: Entity-weighted clinical sparse retrieval
   - Channel D: Structural section/heading matching
3. Reciprocal Rank Fusion (RRF, k=60) with channel provenance tracking.
4. Intra-section redundancy and crowding dampening.
5. Structured cross-encoder reranking:
   Title: ...
   Section Path: ...
   Heading: ...
   Evidence: ...
   with explicit medical claim support instruction.
"""

from __future__ import annotations

import json
import logging
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from medicalplab.learn.renal_bm25 import RenalBM25Index, tokenize
from medicalplab.learn.renal_canonicalizer import (
    RenalCanonicalizationResult,
    RenalQueryCanonicalizer,
)

logger = logging.getLogger(__name__)

RENAL_EMBEDDING_MODEL = "Qwen/Qwen3-Embedding-0.6B"
RENAL_RERANKER_MODEL = "Qwen/Qwen3-Reranker-0.6B"
DEFAULT_RRF_K = 60

MEDICAL_RERANKER_INSTRUCTION = (
    "Instruct: Determine whether the evidence passage directly supports the exact "
    "medical proposition requested in the query. Topical relevance without direct "
    "claim support is non-support.\nQuery: "
)

DENSE_QUERY_INSTRUCTION = (
    "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
)


@dataclass
class V7Candidate:
    chunk_id: str
    document_id: str
    chunk: dict[str, Any]
    fused_score: float = 0.0
    channel_ranks: dict[str, int] = field(default_factory=dict)
    channel_scores: dict[str, float] = field(default_factory=dict)
    rerank_score: float = 0.0


class RenalV7MultiChannelRetriever:
    """Product-grade multi-channel retriever for MedicalPlab Renal V7."""

    def __init__(
        self,
        data_root: Path | str,
        *,
        embedding_model_name: str = RENAL_EMBEDDING_MODEL,
        reranker_model_name: str = RENAL_RERANKER_MODEL,
        candidate_depth: int = 50,
        rrf_k: int = DEFAULT_RRF_K,
        alpha_doc_prior: float = 0.15,
        dense_weight: float = 1.0,
        bm25_weight: float = 1.0,
        entity_sparse_weight: float = 0.8,
        structural_weight: float = 0.6,
        max_chunks_per_section: int = 4,
    ):
        self.data_root = Path(data_root)
        self.embedding_model_name = embedding_model_name
        self.reranker_model_name = reranker_model_name
        self.candidate_depth = candidate_depth
        self.rrf_k = rrf_k
        self.alpha_doc_prior = alpha_doc_prior
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight
        self.entity_sparse_weight = entity_sparse_weight
        self.structural_weight = structural_weight
        self.max_chunks_per_section = max_chunks_per_section

        self.canonicalizer = RenalQueryCanonicalizer()

        self._model = None
        self._reranker = None
        self._chunks: list[dict[str, Any]] = []
        self._chunk_id_to_idx: dict[str, int] = {}
        self._doc_titles: dict[str, str] = {}
        self._doc_topics: dict[str, str] = {}
        self._doc_ids_sorted: list[str] = []
        self._doc_id_to_idx: dict[str, int] = {}

        self._embeddings: np.ndarray | None = None
        self._doc_embeddings: np.ndarray | None = None
        self._bm25_index: RenalBM25Index | None = None
        self._rendered_passages: list[str] = []

    def load(self):
        """Loads corpus, indexes, and precomputed embeddings."""
        if self._embeddings is not None and self._bm25_index is not None:
            return

        import sys
        sys.path.insert(0, ".renal_env")
        from sentence_transformers import CrossEncoder, SentenceTransformer

        registry_path = self.data_root / "metadata" / "renal_source_registry_v2.json"
        chunks_dir = self.data_root / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
        corpus_cache = self.data_root / "experiments" / "renal_v3" / "cache" / "all23_corpus_embeddings.npy"
        doc_cache = self.data_root / "experiments" / "renal_v3" / "cache" / "all23_doc_embeddings.npy"

        reg_data = json.loads(registry_path.read_bytes())
        self._doc_titles = {d["document_id"]: d.get("title", "") for d in reg_data.get("documents", [])}
        self._doc_topics = {d["document_id"]: ", ".join(d.get("topic_tags", [])) for d in reg_data.get("documents", [])}

        chunks = []
        for p in sorted(chunks_dir.glob("*.chunks.json")):
            data = json.loads(p.read_bytes())
            chunks.extend(data.get("chunks", []))

        self._chunks = chunks
        self._chunk_id_to_idx = {ch["chunk_id"]: idx for idx, ch in enumerate(chunks)}

        self._doc_ids_sorted = sorted(list(self._doc_titles.keys()))
        self._doc_id_to_idx = {did: i for i, did in enumerate(self._doc_ids_sorted)}

        # Render structured passage texts
        rendered = []
        corpus_texts = []
        for ch in chunks:
            did = ch.get("document_id", "")
            title = self._doc_titles.get(did, "")
            sec_path = " > ".join(ch.get("section_path", []))
            heading = ch.get("heading", "")
            text = ch.get("text", "")
            rendered_str = f"Title: {title}\nSection Path: {sec_path}\nHeading: {heading}\nEvidence: {text}"
            rendered.append(rendered_str)
            corpus_texts.append(f"{title} {sec_path} {heading} {text}")

        self._rendered_passages = rendered

        # Load BM25 index
        self._bm25_index = RenalBM25Index(chunks, corpus_texts, k1=1.5, b=0.75)

        # Load dense embeddings
        if corpus_cache.exists():
            self._embeddings = np.load(str(corpus_cache))
        else:
            dense_cache = self.data_root / "indices" / "dense" / "all23_corpus_embeddings.npy"
            if dense_cache.exists():
                self._embeddings = np.load(str(dense_cache))

        if doc_cache.exists():
            self._doc_embeddings = np.load(str(doc_cache))

        # Lazy load neural models
        try:
            self._model = SentenceTransformer(self.embedding_model_name, device="cuda")
        except Exception:
            self._model = SentenceTransformer(self.embedding_model_name)

        try:
            self._reranker = CrossEncoder(self.reranker_model_name, trust_remote_code=True, device="cuda")
        except Exception:
            self._reranker = CrossEncoder(self.reranker_model_name, trust_remote_code=True)

        logger.info(f"Loaded Renal V7 retriever: {len(self._chunks)} chunks, BM25 + Dense + Reranker ready.")

    def acquire_candidates(self, query: str, top_k: int | None = None) -> list[V7Candidate]:
        """Runs multi-channel acquisition and Reciprocal Rank Fusion."""
        self.load()
        assert self._model is not None and self._bm25_index is not None and self._embeddings is not None

        k_cand = top_k or self.candidate_depth
        norm_result = self.canonicalizer.canonicalize(query)
        canonical_q = norm_result.canonical_query
        rewrite_q = norm_result.controlled_rewrite

        # -------------------------------------------------------------
        # Channel A: Dense Semantic Dot-Product + Document Prior
        # -------------------------------------------------------------
        dense_q_text = DENSE_QUERY_INSTRUCTION + canonical_q
        q_emb = self._model.encode([dense_q_text], normalize_embeddings=True, show_progress_bar=False)[0]

        p_scores = self._embeddings @ q_emb
        combined_dense_scores = np.copy(p_scores)

        if self._doc_embeddings is not None:
            d_scores = self._doc_embeddings @ q_emb
            for i, ch in enumerate(self._chunks):
                did = ch.get("document_id")
                if did in self._doc_id_to_idx:
                    combined_dense_scores[i] += self.alpha_doc_prior * d_scores[self._doc_id_to_idx[did]]

        dense_ranked_indices = np.argsort(combined_dense_scores)[::-1][:200]

        # -------------------------------------------------------------
        # Channel B: Okapi BM25 Lexical Term Matching
        # -------------------------------------------------------------
        bm25_hits = self._bm25_index.search(rewrite_q, top_k=200)

        # -------------------------------------------------------------
        # Channel C: Entity-Weighted Sparse Retrieval
        # -------------------------------------------------------------
        entity_scores: dict[int, float] = {}
        if norm_result.detected_entities:
            for ent in norm_result.detected_entities:
                ent_tokens = tokenize(ent)
                for ent_tok in ent_tokens:
                    if ent_tok in self._bm25_index.inverted_index:
                        postings = self._bm25_index.inverted_index[ent_tok]
                        idf_val = self._bm25_index.idf.get(ent_tok, 1.0)
                        for doc_idx, tf in postings:
                            entity_scores[doc_idx] = entity_scores.get(doc_idx, 0.0) + idf_val * tf

        entity_ranked_indices = sorted(entity_scores.keys(), key=lambda idx: entity_scores[idx], reverse=True)[:200]

        # -------------------------------------------------------------
        # Channel D: Structural Section & Heading Term Match
        # -------------------------------------------------------------
        struct_scores: dict[int, float] = {}
        q_tokens = set(tokenize(canonical_q))
        for idx, ch in enumerate(self._chunks):
            heading_tokens = set(tokenize(ch.get("heading", "")))
            sec_tokens = set(tokenize(" ".join(ch.get("section_path", []))))
            overlap = len(q_tokens.intersection(heading_tokens)) * 2.0 + len(q_tokens.intersection(sec_tokens))
            if overlap > 0:
                struct_scores[idx] = overlap

        struct_ranked_indices = sorted(struct_scores.keys(), key=lambda idx: struct_scores[idx], reverse=True)[:200]

        # -------------------------------------------------------------
        # Reciprocal Rank Fusion (RRF) with Provenance Tracking
        # -------------------------------------------------------------
        candidate_map: dict[str, V7Candidate] = {}

        # Process Channel A (Dense)
        for rank, idx in enumerate(dense_ranked_indices):
            ch = self._chunks[int(idx)]
            cid = ch["chunk_id"]
            if cid not in candidate_map:
                candidate_map[cid] = V7Candidate(
                    chunk_id=cid,
                    document_id=ch.get("document_id", ""),
                    chunk=ch,
                )
            cand = candidate_map[cid]
            cand.channel_ranks["dense"] = rank + 1
            cand.channel_scores["dense"] = float(combined_dense_scores[int(idx)])
            cand.fused_score += self.dense_weight / (self.rrf_k + rank + 1)

        # Process Channel B (BM25)
        for rank, hit in enumerate(bm25_hits):
            cid = hit.chunk["chunk_id"]
            if cid not in candidate_map:
                candidate_map[cid] = V7Candidate(
                    chunk_id=cid,
                    document_id=hit.chunk.get("document_id", ""),
                    chunk=hit.chunk,
                )
            cand = candidate_map[cid]
            cand.channel_ranks["bm25"] = rank + 1
            cand.channel_scores["bm25"] = float(hit.score)
            cand.fused_score += self.bm25_weight / (self.rrf_k + rank + 1)

        # Process Channel C (Entity Sparse)
        for rank, idx in enumerate(entity_ranked_indices):
            ch = self._chunks[int(idx)]
            cid = ch["chunk_id"]
            if cid not in candidate_map:
                candidate_map[cid] = V7Candidate(
                    chunk_id=cid,
                    document_id=ch.get("document_id", ""),
                    chunk=ch,
                )
            cand = candidate_map[cid]
            cand.channel_ranks["entity_sparse"] = rank + 1
            cand.channel_scores["entity_sparse"] = float(entity_scores[int(idx)])
            cand.fused_score += self.entity_sparse_weight / (self.rrf_k + rank + 1)

        # Process Channel D (Structural)
        for rank, idx in enumerate(struct_ranked_indices):
            ch = self._chunks[int(idx)]
            cid = ch["chunk_id"]
            if cid not in candidate_map:
                candidate_map[cid] = V7Candidate(
                    chunk_id=cid,
                    document_id=ch.get("document_id", ""),
                    chunk=ch,
                )
            cand = candidate_map[cid]
            cand.channel_ranks["structural"] = rank + 1
            cand.channel_scores["structural"] = float(struct_scores[int(idx)])
            cand.fused_score += self.structural_weight / (self.rrf_k + rank + 1)

        # Sort by fused score
        ranked_candidates = sorted(candidate_map.values(), key=lambda c: c.fused_score, reverse=True)

        # -------------------------------------------------------------
        # Section-Level Diversity & Crowding Dampening
        # -------------------------------------------------------------
        section_counts: Counter[str] = Counter()
        diversified_candidates: list[V7Candidate] = []
        overflow_candidates: list[V7Candidate] = []

        for cand in ranked_candidates:
            sec_key = f"{cand.document_id}::" + " > ".join(cand.chunk.get("section_path", []))
            if section_counts[sec_key] < self.max_chunks_per_section:
                diversified_candidates.append(cand)
                section_counts[sec_key] += 1
            else:
                overflow_candidates.append(cand)

        # Fill remaining slots up to k_cand with overflow if needed
        final_candidates = diversified_candidates[:k_cand]
        if len(final_candidates) < k_cand and overflow_candidates:
            final_candidates.extend(overflow_candidates[: k_cand - len(final_candidates)])

        return final_candidates

    def retrieve(self, query: str, top_k: int = 5, candidate_pool_size: int | None = None) -> list[V7Candidate]:
        """End-to-end V7 retrieval with multi-channel acquisition and structured reranking."""
        candidates = self.acquire_candidates(query, top_k=candidate_pool_size or self.candidate_depth)
        if not candidates:
            return []

        assert self._reranker is not None

        # Build structured reranker input pairs
        instruction_query = MEDICAL_RERANKER_INSTRUCTION + query
        pairs = []
        for cand in candidates:
            idx = self._chunk_id_to_idx[cand.chunk_id]
            structured_passage = self._rendered_passages[idx]
            pairs.append([instruction_query, structured_passage])

        # Batch cross-encoder inference
        rerank_scores = self._reranker.predict(pairs, batch_size=8, show_progress_bar=False)
        r_scores = np.asarray(rerank_scores, dtype=np.float32).reshape(-1)

        for i, cand in enumerate(candidates):
            cand.rerank_score = float(r_scores[i])

        # Sort by reranker score
        reranked = sorted(candidates, key=lambda c: c.rerank_score, reverse=True)
        return reranked[:top_k]
