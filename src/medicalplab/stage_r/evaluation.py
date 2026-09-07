"""Retrieval evaluation metrics module for Stage-R.

Computes standard Information Retrieval benchmarks: Recall@K, Precision@K, Hit Rate, and MRR.
"""

from typing import Sequence, Set

from medicalplab.stage_b.models import require
from .models import EvaluationResult


def compute_hit_rate(
    retrieved_refs: Sequence[str],
    relevant_refs: Set[str],
    k: int = 5,
) -> float:
    """Return 1.0 if at least one relevant document is in top-k, else 0.0."""
    require(k >= 1, "'k' must be >= 1")
    top_k = retrieved_refs[:k]
    return 1.0 if any(r in relevant_refs for r in top_k) else 0.0


def compute_recall_at_k(
    retrieved_refs: Sequence[str],
    relevant_refs: Set[str],
    k: int = 5,
) -> float:
    """Proportion of relevant documents retrieved in top-k."""
    require(k >= 1, "'k' must be >= 1")
    if not relevant_refs:
        return 0.0
    top_k_set = set(retrieved_refs[:k])
    hits = len(top_k_set.intersection(relevant_refs))
    return round(hits / len(relevant_refs), 4)


def compute_precision_at_k(
    retrieved_refs: Sequence[str],
    relevant_refs: Set[str],
    k: int = 5,
) -> float:
    """Proportion of retrieved top-k documents that are relevant."""
    require(k >= 1, "'k' must be >= 1")
    top_k = retrieved_refs[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for r in top_k if r in relevant_refs)
    return round(hits / len(top_k), 4)


def compute_mrr(
    retrieved_refs: Sequence[str],
    relevant_refs: Set[str],
    k: int = 5,
) -> float:
    """Mean Reciprocal Rank: reciprocal of the rank of the first relevant document in top-k."""
    require(k >= 1, "'k' must be >= 1")
    for rank, ref in enumerate(retrieved_refs[:k], 1):
        if ref in relevant_refs:
            return round(1.0 / rank, 4)
    return 0.0


def evaluate_retrieval(
    test_cases: Sequence[tuple[Sequence[str], Set[str]]],
    k: int = 5,
) -> EvaluationResult:
    """Compute aggregate retrieval benchmarks across multiple test queries."""
    require(k >= 1, "'k' must be >= 1")
    if not test_cases:
        return EvaluationResult(
            recall_at_k=0.0,
            precision_at_k=0.0,
            hit_rate=0.0,
            mrr=0.0,
            k=k,
        )

    recalls: list[float] = []
    precisions: list[float] = []
    hits: list[float] = []
    mrrs: list[float] = []

    for retrieved, relevant in test_cases:
        recalls.append(compute_recall_at_k(retrieved, relevant, k=k))
        precisions.append(compute_precision_at_k(retrieved, relevant, k=k))
        hits.append(compute_hit_rate(retrieved, relevant, k=k))
        mrrs.append(compute_mrr(retrieved, relevant, k=k))

    n = len(test_cases)
    return EvaluationResult(
        recall_at_k=round(sum(recalls) / n, 4),
        precision_at_k=round(sum(precisions) / n, 4),
        hit_rate=round(sum(hits) / n, 4),
        mrr=round(sum(mrrs) / n, 4),
        k=k,
    )
