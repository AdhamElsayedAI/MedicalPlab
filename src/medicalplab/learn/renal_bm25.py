"""Self-contained Okapi BM25 implementation for Renal retrieval."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return re.findall(r"\b[a-zA-Z0-9]+(?:'[a-zA-Z]+)?\b", text.lower())


@dataclass
class BM25Hit:
    index: int
    score: float
    chunk: dict[str, Any]


class RenalBM25Index:
    """Fast in-memory Okapi BM25 index with inverted posting lists."""

    def __init__(
        self,
        chunks: list[dict[str, Any]],
        corpus_texts: list[str],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.n_docs = len(chunks)

        self.doc_lens: list[int] = []
        self.inverted_index: dict[str, list[tuple[int, int]]] = {}
        df: Counter[str] = Counter()

        for doc_idx, text in enumerate(corpus_texts):
            tokens = tokenize(text)
            self.doc_lens.append(len(tokens))
            term_counts = Counter(tokens)
            for term, count in term_counts.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = []
                self.inverted_index[term].append((doc_idx, count))
                df[term] += 1

        self.avg_dl = sum(self.doc_lens) / max(self.n_docs, 1)

        # Precompute Lucene/Robertson smoothed IDF
        self.idf: dict[str, float] = {}
        for term, freq in df.items():
            # Standard smoothed IDF
            self.idf[term] = math.log(1.0 + (self.n_docs - freq + 0.5) / (freq + 0.5))

    def search(self, query: str, top_k: int = 50) -> list[BM25Hit]:
        """Search the index for a query and return top_k hits."""
        query_tokens = tokenize(query)
        if not query_tokens or self.n_docs == 0:
            return []

        scores = [0.0] * self.n_docs
        for term in query_tokens:
            if term not in self.inverted_index:
                continue
            idf_val = self.idf[term]
            postings = self.inverted_index[term]
            for doc_idx, tf in postings:
                doc_len = self.doc_lens[doc_idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_dl))
                scores[doc_idx] += idf_val * (numerator / denominator)

        # Get top-k non-zero scored indices
        scored_indices = [i for i, s in enumerate(scores) if s > 0.0]
        if not scored_indices:
            # Fail closed. Returning arbitrary zero-score documents would manufacture
            # sparse evidence and can turn an unsupported query into a false accept.
            return []

        scored_indices.sort(key=lambda idx: scores[idx], reverse=True)
        top_indices = scored_indices[:top_k]

        return [BM25Hit(idx, scores[idx], self.chunks[idx]) for idx in top_indices]
