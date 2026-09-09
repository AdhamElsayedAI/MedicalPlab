"""Neural dense retriever for Stage-R using Qwen3-Embedding.

Implements DenseRetrieverInterface with cosine-similarity semantic matching,
query instruction prompting, passage formatting, and passage embedding caching.
Provides deterministic fallback when PyTorch/SentenceTransformers is not available.
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

from medicalplab.stage_b.models import require
from medicalplab.stage_g.runtime import get_runtime_mode, strict_runtime_enabled
from .hybrid_retriever import DenseRetrieverInterface, StubDenseRetriever
from .models import EvidenceBlock, RetrievalQuery

logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"

DEFAULT_QUERY_INSTRUCTION = (
    "Instruct: Given a medical education query, retrieve the passages "
    "from the available medical sources that most directly support the "
    "requested claim. Respect any source explicitly requested by the "
    "query. Do not assume every query targets a guideline.\nQuery:"
)


class Qwen3DenseRetriever(DenseRetrieverInterface):
    """Dense retriever powered by Qwen3-Embedding-0.6B (or compatible SentenceTransformer)."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        device: str | None = None,
        instruction: str = DEFAULT_QUERY_INSTRUCTION,
        batch_size: int = 32,
        fallback_to_stub: bool | None = None,
    ):
        self.model_name = model_name
        self.device = device
        self.instruction = instruction
        self.batch_size = batch_size

        if strict_runtime_enabled():
            if fallback_to_stub is True:
                raise ValueError(
                    f"fallback_to_stub=True is forbidden in strict runtime mode ({get_runtime_mode().value}). Fail closed."
                )
            self.fallback_to_stub = False
        else:
            self.fallback_to_stub = True if fallback_to_stub is None else bool(fallback_to_stub)

        self._model = None
        self._load_failed = False
        self._embedding_cache: dict[str, Any] = {}
        self._stub_fallback: StubDenseRetriever | None = None

    def _get_model(self):
        """Lazy load model on first inference."""
        if self._model is not None:
            return self._model
        if self._load_failed:
            if strict_runtime_enabled():
                raise RuntimeError(
                    f"Dense retriever model '{self.model_name}' unavailable in strict runtime mode ({get_runtime_mode().value}). Fail closed."
                )
            return None

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"Loaded dense embedding model: {self.model_name} on {self.device or 'default'}")
            return self._model
        except Exception as exc:
            logger.warning(f"Could not load SentenceTransformer '{self.model_name}': {exc}")
            self._load_failed = True
            if strict_runtime_enabled() or not self.fallback_to_stub:
                raise RuntimeError(
                    f"Dense retriever model '{self.model_name}' failed to load in strict runtime mode ({get_runtime_mode().value}): {exc}. Fail closed."
                ) from exc
            if self.fallback_to_stub:
                self._stub_fallback = StubDenseRetriever()
            return None

    def format_passage(self, block: EvidenceBlock) -> str:
        """Standardized passage rendering matching benchmark format."""
        parts = []
        if block.heading:
            parts.append(f"Heading: {block.heading}")
        if block.section:
            parts.append(f"Section: {block.section}")
        parts.append(f"Content: {block.text}")
        return "\n".join(parts)

    def format_query(self, query: RetrievalQuery) -> str:
        """Prepend retrieval task instruction to the query."""
        raw = query.raw_query.strip()
        if self.instruction:
            return f"{self.instruction.strip()}\n{raw}"
        return raw

    def retrieve_dense(
        self,
        query: RetrievalQuery,
        corpus: Sequence[EvidenceBlock],
        top_k: int = 10,
    ) -> dict[str, float]:
        """Return a mapping of block.ref -> dense similarity score [0.0, 1.0]."""
        require(isinstance(query, RetrievalQuery), "query must be a RetrievalQuery instance")
        if not corpus:
            return {}

        model = self._get_model()
        if model is None:
            if self._stub_fallback:
                return self._stub_fallback.retrieve_dense(query, corpus, top_k=top_k)
            raise RuntimeError(f"Dense retriever model '{self.model_name}' could not be loaded")

        import numpy as np

        # 1. Encode query
        formatted_query = self.format_query(query)
        q_emb = model.encode(
            [formatted_query],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]  # shape: (dim,)

        # 2. Collect / encode corpus passages (with caching)
        uncached_blocks = []
        uncached_texts = []
        for block in corpus:
            cache_key = f"{block.ref}::{hash(block.text)}"
            if cache_key not in self._embedding_cache:
                uncached_blocks.append((cache_key, block))
                uncached_texts.append(self.format_passage(block))

        if uncached_texts:
            new_embs = model.encode(
                uncached_texts,
                batch_size=self.batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            for (ckey, _), emb in zip(uncached_blocks, new_embs):
                self._embedding_cache[ckey] = emb

        # 3. Compute cosine similarity for each block
        results: dict[str, float] = {}
        for block in corpus:
            cache_key = f"{block.ref}::{hash(block.text)}"
            p_emb = self._embedding_cache[cache_key]
            sim = float(np.dot(q_emb, p_emb))
            # Map cosine similarity [-1.0, 1.0] to [0.0, 1.0] (clamped)
            norm_score = max(0.0, min(1.0, sim))
            results[block.ref] = round(norm_score, 4)

        return results
