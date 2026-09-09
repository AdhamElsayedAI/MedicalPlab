"""Hybrid retrieval engine for Stage-R.

Combines sparse BM25 term matching with dense semantic retrieval using configurable alpha weighting.
Includes abstract interfaces for external embedding/dense backends.
"""

from abc import ABC, abstractmethod
from collections import Counter
import math
from typing import Sequence

from medicalplab.stage_b.models import require
from medicalplab.stage_b.evidence_policy import normalize
from medicalplab.stage_g.runtime import get_runtime_mode, strict_runtime_enabled
from .models import (
    EvidenceBlock,
    EvidenceCandidate,
    RetrievalQuery,
    ScoreBreakdown,
)


class DenseRetrieverInterface(ABC):
    """Abstract interface for dense/embedding retrieval backends."""

    @abstractmethod
    def retrieve_dense(
        self,
        query: RetrievalQuery,
        corpus: Sequence[EvidenceBlock],
        top_k: int = 10,
    ) -> dict[str, float]:
        """Return a mapping of block.ref -> dense similarity score [0.0, 1.0]."""
        raise NotImplementedError


class StubDenseRetriever(DenseRetrieverInterface):
    """Deterministic dense retriever for testing and CPU execution."""

    def __init__(self, scores: dict[str, float] | None = None):
        self.preset_scores = scores or {}

    def retrieve_dense(
        self,
        query: RetrievalQuery,
        corpus: Sequence[EvidenceBlock],
        top_k: int = 10,
    ) -> dict[str, float]:
        results = {}
        query_words = set(normalize(query.raw_query).split())
        for block in corpus:
            if block.ref in self.preset_scores:
                results[block.ref] = self.preset_scores[block.ref]
            else:
                # Default heuristic based on semantic heading + text overlap
                block_words = set(normalize(f"{block.heading} {block.text}").split())
                if not block_words:
                    results[block.ref] = 0.0
                else:
                    overlap = len(query_words.intersection(block_words))
                    results[block.ref] = round(min(1.0, overlap / max(1, len(query_words))), 4)
        return results


class SparseBM25Retriever:
    """Deterministic BM25 term frequency retriever."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def _tokenize(self, text: str) -> list[str]:
        return [w for w in normalize(text).split() if len(w) >= 2]

    def score(
        self,
        query: RetrievalQuery,
        corpus: Sequence[EvidenceBlock],
    ) -> dict[str, float]:
        """Compute normalized BM25 scores for all corpus blocks against query terms."""
        if not corpus:
            return {}

        # Combine raw query terms and expanded synonyms
        query_tokens = self._tokenize(query.normalized_query)
        for syn in query.expanded_terms:
            query_tokens.extend(self._tokenize(syn))
        query_terms = list(set(query_tokens))

        if not query_terms:
            return {b.ref: 0.0 for b in corpus}

        # Index corpus
        doc_tokens = {b.ref: self._tokenize(f"{b.heading} {b.section} {b.text}") for b in corpus}
        doc_lengths = {ref: len(tokens) for ref, tokens in doc_tokens.items()}
        avgdl = sum(doc_lengths.values()) / max(1, len(corpus))
        n_docs = len(corpus)

        # Compute document frequencies
        df = Counter()
        for tokens in doc_tokens.values():
            unique_terms = set(tokens)
            for t in query_terms:
                if t in unique_terms:
                    df[t] += 1

        # Compute IDF
        idf = {}
        for t in query_terms:
            doc_freq = df[t]
            # Standard Lucene/BM25 smoothed IDF
            idf[t] = math.log(1.0 + (n_docs - doc_freq + 0.5) / (doc_freq + 0.5))

        # Compute raw scores
        raw_scores = {}
        for b in corpus:
            ref = b.ref
            tokens = doc_tokens[ref]
            tf = Counter(tokens)
            doc_len = doc_lengths[ref]
            score = 0.0

            for t in query_terms:
                if t in tf:
                    term_freq = tf[t]
                    numerator = term_freq * (self.k1 + 1.0)
                    denominator = term_freq + self.k1 * (1.0 - self.b + self.b * (doc_len / avgdl))
                    score += idf[t] * (numerator / denominator)

            raw_scores[ref] = score

        # Min-max normalization to [0.0, 1.0]
        max_score = max(raw_scores.values()) if raw_scores else 0.0
        if max_score > 0:
            return {ref: round(score / max_score, 4) for ref, score in raw_scores.items()}
        return {ref: 0.0 for ref in raw_scores}


class HybridRetriever:
    """Configurable hybrid searcher blending dense and sparse BM25 retrieval."""

    def __init__(
        self,
        dense_retriever: DenseRetrieverInterface | None = None,
        alpha: float = 0.5,
    ):
        require(
            isinstance(alpha, (int, float)) and 0.0 <= alpha <= 1.0,
            "'alpha' must be between 0.0 and 1.0",
        )
        if strict_runtime_enabled():
            if dense_retriever is None:
                raise ValueError(
                    f"In strict runtime mode ({get_runtime_mode().value}), dense_retriever must be explicitly provided. Silent fallback to StubDenseRetriever is forbidden."
                )
            if isinstance(dense_retriever, StubDenseRetriever):
                raise ValueError(
                    f"StubDenseRetriever cannot be used in strict runtime mode ({get_runtime_mode().value}). Fail closed."
                )
        self.dense_retriever = dense_retriever or StubDenseRetriever()
        self.sparse_retriever = SparseBM25Retriever()
        self.alpha = float(alpha)

    def retrieve(
        self,
        query: RetrievalQuery,
        corpus: Sequence[EvidenceBlock],
        top_k: int = 5,
        alpha_override: float | None = None,
    ) -> tuple[EvidenceCandidate, ...]:
        """Perform hybrid retrieval over the corpus, returning ranked EvidenceCandidates."""
        require(isinstance(query, RetrievalQuery), "query must be a RetrievalQuery instance")
        require(top_k >= 1, "top_k must be >= 1")

        if not corpus:
            return ()

        effective_alpha = self.alpha if alpha_override is None else float(alpha_override)
        require(0.0 <= effective_alpha <= 1.0, "effective_alpha must be between 0.0 and 1.0")

        sparse_scores = self.sparse_retriever.score(query, corpus)
        dense_scores = self.dense_retriever.retrieve_dense(query, corpus, top_k=len(corpus))

        candidates: list[EvidenceCandidate] = []

        for block in corpus:
            s_score = sparse_scores.get(block.ref, 0.0)
            d_score = dense_scores.get(block.ref, 0.0)
            hybrid_score = round(effective_alpha * d_score + (1.0 - effective_alpha) * s_score, 4)

            breakdown = ScoreBreakdown(
                dense_score=round(d_score, 4),
                sparse_score=round(s_score, 4),
                alpha=round(effective_alpha, 4),
                hybrid_score=hybrid_score,
                rerank_score=0.0,
                final_score=hybrid_score,
            )

            candidates.append(
                EvidenceCandidate(
                    ref=block.ref,
                    document_id=block.document_id,
                    source=block.source,
                    heading=block.heading,
                    section=block.section,
                    text=block.text,
                    score=hybrid_score,
                    score_breakdown=breakdown,
                )
            )

        # Sort descending by hybrid score
        candidates.sort(key=lambda c: c.score, reverse=True)
        return tuple(candidates[:top_k])
