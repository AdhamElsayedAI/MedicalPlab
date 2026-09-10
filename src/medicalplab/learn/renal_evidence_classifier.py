"""Multi-signal evidence sufficiency model and feature extractor."""

from __future__ import annotations

import json
import math
import pickle
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression

from medicalplab.learn.renal_bm25 import tokenize
from medicalplab.learn.renal_normalization import normalize_renal_query


@dataclass
class RenalEvidenceFeatures:
    dense_top1: float
    dense_top2: float
    dense_margin: float
    dense_top5_mean: float
    bm25_top1: float
    bm25_top2: float
    bm25_margin: float
    bm25_top5_mean: float
    rrf_top1: float
    rrf_margin: float
    reranker_top1: float
    reranker_top2: float
    reranker_margin: float
    reranker_top5_mean: float
    lexical_overlap: float
    medical_term_overlap: float
    n_supporting_sections: int
    n_supporting_docs: int
    dense_sparse_agreement: float
    is_core_educational_source: float

    def to_array(self) -> np.ndarray:
        return np.array([
            self.dense_top1,
            self.dense_top2,
            self.dense_margin,
            self.dense_top5_mean,
            self.bm25_top1,
            self.bm25_top2,
            self.bm25_margin,
            self.bm25_top5_mean,
            self.rrf_top1,
            self.rrf_margin,
            self.reranker_top1,
            self.reranker_top2,
            self.reranker_margin,
            self.reranker_top5_mean,
            self.lexical_overlap,
            self.medical_term_overlap,
            float(self.n_supporting_sections),
            float(self.n_supporting_docs),
            self.dense_sparse_agreement,
            self.is_core_educational_source,
        ], dtype=np.float32)


def extract_evidence_features(
    query: str,
    dense_hits: list[tuple[dict[str, Any], float]],
    bm25_hits: list[tuple[dict[str, Any], float]],
    rrf_hits: list[tuple[dict[str, Any], float]],
    reranked_hits: list[tuple[dict[str, Any], float]],
    registry: dict[str, dict[str, Any]],
) -> RenalEvidenceFeatures:
    """Extract 20 multi-signal runtime features for evidence sufficiency decision."""
    # Dense features
    d_scores = [score for _, score in dense_hits[:5]] or [0.0]
    dense_top1 = d_scores[0]
    dense_top2 = d_scores[1] if len(d_scores) > 1 else d_scores[0]
    dense_margin = dense_top1 - dense_top2
    dense_top5_mean = float(np.mean(d_scores))

    # BM25 features
    b_scores = [score for _, score in bm25_hits[:5]] or [0.0]
    bm25_top1 = b_scores[0]
    bm25_top2 = b_scores[1] if len(b_scores) > 1 else 0.0
    bm25_margin = bm25_top1 - bm25_top2
    bm25_top5_mean = float(np.mean(b_scores))

    # RRF features
    r_scores = [score for _, score in rrf_hits[:5]] or [0.0]
    rrf_top1 = r_scores[0]
    rrf_top2 = r_scores[1] if len(r_scores) > 1 else 0.0
    rrf_margin = rrf_top1 - rrf_top2

    # Reranker features
    rk_scores = [score for _, score in reranked_hits[:5]] or [-10.0]
    reranker_top1 = rk_scores[0]
    reranker_top2 = rk_scores[1] if len(rk_scores) > 1 else rk_scores[0]
    reranker_margin = reranker_top1 - reranker_top2
    reranker_top5_mean = float(np.mean(rk_scores))

    # Lexical overlap
    top1_chunk = reranked_hits[0][0] if reranked_hits else (dense_hits[0][0] if dense_hits else {})
    top1_text = top1_chunk.get("text", "").lower()
    q_tokens = set(tokenize(query))
    top1_tokens = set(tokenize(top1_text))
    lexical_overlap = len(q_tokens & top1_tokens) / max(len(q_tokens), 1)

    # Medical term overlap
    trace = normalize_renal_query(query)
    med_terms = [t.split("->")[-1].strip().lower() for t in trace.transformations]
    if med_terms:
        med_hits = sum(1 for term in med_terms if any(w in top1_text for w in tokenize(term)))
        med_overlap = med_hits / len(med_terms)
    else:
        med_overlap = lexical_overlap

    # Structural consensus in top 5 reranked
    top5_chunks = [c for c, _ in reranked_hits[:5]]
    sections = {c.get("parent_section_id") for c in top5_chunks if c.get("parent_section_id")}
    docs = {c.get("document_id") for c in top5_chunks if c.get("document_id")}
    n_supporting_sections = len(sections)
    n_supporting_docs = len(docs)

    # Dense and Sparse top-5 agreement
    dense_top5_ids = {c.get("child_chunk_id") or c.get("chunk_id") for c, _ in dense_hits[:5]}
    bm25_top5_ids = {c.get("child_chunk_id") or c.get("chunk_id") for c, _ in bm25_hits[:5]}
    overlap_count = len(dense_top5_ids & bm25_top5_ids)
    agreement = overlap_count / 5.0

    # Source educational role
    doc_id = top1_chunk.get("document_id", "")
    doc_meta = registry.get(doc_id, {})
    role = doc_meta.get("educational_classification", "SUPPORTING")
    if role == "CORE_EDUCATIONAL":
        edu_score = 1.0
    elif role == "SUPPORTING":
        edu_score = 0.5
    else:
        edu_score = 0.0

    return RenalEvidenceFeatures(
        dense_top1=dense_top1,
        dense_top2=dense_top2,
        dense_margin=dense_margin,
        dense_top5_mean=dense_top5_mean,
        bm25_top1=bm25_top1,
        bm25_top2=bm25_top2,
        bm25_margin=bm25_margin,
        bm25_top5_mean=bm25_top5_mean,
        rrf_top1=rrf_top1,
        rrf_margin=rrf_margin,
        reranker_top1=reranker_top1,
        reranker_top2=reranker_top2,
        reranker_margin=reranker_margin,
        reranker_top5_mean=reranker_top5_mean,
        lexical_overlap=lexical_overlap,
        medical_term_overlap=med_overlap,
        n_supporting_sections=n_supporting_sections,
        n_supporting_docs=n_supporting_docs,
        dense_sparse_agreement=agreement,
        is_core_educational_source=edu_score,
    )


class RenalEvidenceClassifier:
    """Calibrated evidence sufficiency decision model."""

    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold
        self.model = LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.model.fit(X, y)
        self.is_fitted = True

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict_proba")
        return self.model.predict_proba(X)[:, 1]

    def decide(self, features: RenalEvidenceFeatures) -> tuple[str, float]:
        """Classify into GROUNDED, INSUFFICIENT_EVIDENCE, or UNSUPPORTED."""
        if not self.is_fitted:
            # Fallback heuristic if unfitted
            prob = 1.0 / (1.0 + math.exp(-features.reranker_top1))
        else:
            prob = float(self.predict_proba(features.to_array().reshape(1, -1))[0])

        if prob >= self.threshold:
            return "GROUNDED", prob
        elif prob >= self.threshold * 0.6:
            return "INSUFFICIENT_EVIDENCE", prob
        else:
            return "UNSUPPORTED", prob

    def save(self, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "threshold": self.threshold,
            "model": self.model,
            "is_fitted": self.is_fitted,
        }
        with open(p, "wb") as f:
            pickle.dump(payload, f)

    @classmethod
    def load(cls, path: Path | str) -> RenalEvidenceClassifier:
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls(threshold=data["threshold"])
        obj.model = data["model"]
        obj.is_fitted = data["is_fitted"]
        return obj
