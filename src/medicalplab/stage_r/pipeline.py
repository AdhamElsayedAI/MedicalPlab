"""Stage-R Pipeline: Advanced Medical Retrieval Intelligence Layer.

Orchestrates query analysis, synonym expansion, hybrid retrieval, clinical reranking,
extractive context compression, and evidence packet construction.
"""

import time
from typing import Sequence
import uuid

from medicalplab.stage_b.models import require, strings
from .context_compressor import ContextCompressor
from .evidence_builder import build_evidence_packet
from .hybrid_retriever import DenseRetrieverInterface, HybridRetriever
from .models import (
    EvidenceBlock,
    EvidencePacket,
    RetrievalQuery,
)
from .query_expansion import expand_query
from .reranker import MedicalReranker, RerankerInterface


class StageRPipeline:
    """Production-grade medical RAG retrieval pipeline."""

    def __init__(
        self,
        dense_retriever: DenseRetrieverInterface | None = None,
        reranker: RerankerInterface | None = None,
        alpha: float = 0.5,
        top_k: int = 5,
        compress: bool = True,
    ):
        require(0.0 <= alpha <= 1.0, "'alpha' must be between 0.0 and 1.0")
        require(top_k >= 1, "'top_k' must be >= 1")

        self.retriever = HybridRetriever(dense_retriever=dense_retriever, alpha=alpha)
        self.reranker = reranker or MedicalReranker()
        self.compressor = ContextCompressor(max_sentences_per_block=3)
        self.default_top_k = top_k
        self.compress = compress
        self.trace: list[dict] = []

    def retrieve(
        self,
        query_str: str,
        corpus: Sequence[EvidenceBlock],
        top_k: int | None = None,
        alpha_override: float | None = None,
    ) -> EvidencePacket:
        """Execute the end-to-end medical retrieval pipeline."""
        strings(query_str)
        clean_query = query_str.strip()
        effective_k = top_k if top_k is not None else self.default_top_k
        require(effective_k >= 1, "'top_k' must be >= 1")

        start_time = time.perf_counter()
        run_id = str(uuid.uuid4())

        # 1. Query Analysis & Controlled Synonym Expansion
        retrieval_query = expand_query(clean_query)

        # 2. Hybrid Retrieval (fetch extra candidates for reranking)
        retrieval_limit = max(effective_k * 3, 10)
        candidates = self.retriever.retrieve(
            query=retrieval_query,
            corpus=corpus,
            top_k=retrieval_limit,
            alpha_override=alpha_override,
        )

        # 3. Medical Multi-Factor Reranking
        reranked = self.reranker.rerank(
            query=retrieval_query,
            candidates=candidates,
            top_k=effective_k,
        )

        # 4. Extractive Context Compression (optional)
        if self.compress:
            final_blocks = self.compressor.compress(
                query=retrieval_query,
                evidence=reranked,
            )
        else:
            final_blocks = reranked

        # 5. Evidence Packet Assembly & Deduplication
        packet = build_evidence_packet(
            query=clean_query,
            evidence=final_blocks,
            top_k=effective_k,
            metadata={
                "intent": retrieval_query.intent.value,
                "entities": ",".join(retrieval_query.entities),
                "alpha": str(alpha_override if alpha_override is not None else self.retriever.alpha),
            },
        )

        elapsed = time.perf_counter() - start_time

        self.trace.append(
            {
                "run_id": run_id,
                "query": clean_query,
                "intent": retrieval_query.intent.value,
                "entities_count": len(retrieval_query.entities),
                "candidates_retrieved": len(candidates),
                "blocks_delivered": len(packet.blocks),
                "seconds": round(elapsed, 6),
            }
        )

        return packet
