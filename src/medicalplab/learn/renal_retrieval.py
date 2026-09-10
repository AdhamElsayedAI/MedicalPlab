"""Frozen Renal v1 dense-retrieval contract and optional local implementation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


RENAL_MODEL = "Qwen/Qwen3-Embedding-0.6B"
RENAL_REPRESENTATION = "metadata_aware"
RENAL_CHUNKING = "C_section_aware"
RENAL_MAX_SEQUENCE_LENGTH = 512
RENAL_SUFFICIENCY_THRESHOLD = 0.819928765296936
RENAL_QUERY_INSTRUCTION = (
    "Instruct: Retrieve the medical evidence passage that directly supports this renal education query.\nQuery: "
)


@dataclass(frozen=True)
class RenalRetrievalHit:
    chunk: dict[str, Any]
    score: float


class RenalRetriever(Protocol):
    def retrieve(self, query: str, top_k: int = 5) -> list[RenalRetrievalHit]: ...


class RenalRetrieverUnavailable(RuntimeError):
    """The frozen dense retriever cannot be loaded in the current runtime."""


class QwenRenalRetriever:
    """Lazy, offline-only implementation of the frozen Renal v1 configuration.

    The optional ``renal-ml`` dependency group is deliberately not imported at
    module import time, keeping the base product API lightweight and fail-closed.
    """

    def __init__(self, data_root: Path | str, *, model_name: str = RENAL_MODEL) -> None:
        self.data_root = Path(data_root)
        self.model_name = model_name
        self._model: Any | None = None
        self._chunks: list[dict[str, Any]] | None = None
        self._embeddings: Any | None = None

    def _load(self) -> None:
        if self._embeddings is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RenalRetrieverUnavailable(
                "Renal dense retrieval requires the optional 'renal-ml' dependencies."
            ) from exc

        registry_path = self.data_root / "metadata" / "renal_source_registry_v1.json"
        chunks_dir = self.data_root / "experiments" / "renal" / "chunking" / RENAL_CHUNKING
        if not registry_path.exists() or not chunks_dir.exists():
            raise RenalRetrieverUnavailable("Frozen Renal v1 registry or chunks are unavailable.")

        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        metadata = {
            str(item["document_id"]): item
            for item in registry.get("documents", [])
            if item.get("status") == "accepted"
        }
        chunks: list[dict[str, Any]] = []
        for path in sorted(chunks_dir.glob("*.chunks.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            chunks.extend(payload.get("chunks", []))
        if not chunks:
            raise RenalRetrieverUnavailable("Frozen Renal v1 contains no chunks.")

        rendered: list[str] = []
        for chunk in chunks:
            doc = metadata.get(str(chunk.get("document_id")))
            if doc is None:
                raise RenalRetrieverUnavailable("A renal chunk does not resolve to the accepted registry.")
            rendered.append(
                f"Topics: {', '.join(doc.get('topic_tags', []))}\n"
                f"Section: {' > '.join(chunk.get('section_path', []))}\n"
                f"Source: {doc.get('title')} [{chunk.get('document_id')}]\n{chunk.get('text', '')}"
            )

        try:
            model = SentenceTransformer(self.model_name, local_files_only=True)
            model.max_seq_length = RENAL_MAX_SEQUENCE_LENGTH
            embeddings = model.encode(rendered, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
        except Exception as exc:
            raise RenalRetrieverUnavailable(f"Frozen renal model could not be loaded offline: {exc}") from exc
        self._model = model
        self._chunks = chunks
        self._embeddings = embeddings

    def retrieve(self, query: str, top_k: int = 5) -> list[RenalRetrievalHit]:
        self._load()
        assert self._model is not None and self._chunks is not None and self._embeddings is not None
        query_embedding = self._model.encode(
            [RENAL_QUERY_INSTRUCTION + query], normalize_embeddings=True, show_progress_bar=False
        )[0]
        scores = self._embeddings @ query_embedding
        ranked = scores.argsort()[::-1][:top_k]
        return [RenalRetrievalHit(self._chunks[int(index)], float(scores[int(index)])) for index in ranked]


class QwenRenalRetrieverV2:
    """Frozen Renal V2 dense retriever (B_400_overlap x content_only).

    Empirically validated offline dense retriever using Qwen3-Embedding-0.6B
    over the 23-source undergraduate renal corpus.
    """

    def __init__(self, data_root: Path | str, *, model_name: str = RENAL_MODEL) -> None:
        self.data_root = Path(data_root)
        self.model_name = model_name
        self._model: Any | None = None
        self._chunks: list[dict[str, Any]] | None = None
        self._embeddings: Any | None = None

    def _load(self) -> None:
        if self._embeddings is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RenalRetrieverUnavailable(
                "Renal dense retrieval requires the optional 'renal-ml' dependencies."
            ) from exc

        registry_path = self.data_root / "metadata" / "renal_source_registry_v2.json"
        chunks_dir = self.data_root / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
        if not registry_path.exists() or not chunks_dir.exists():
            raise RenalRetrieverUnavailable("Frozen Renal v2 registry or chunks are unavailable.")

        chunks: list[dict[str, Any]] = []
        for path in sorted(chunks_dir.glob("*.chunks.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            chunks.extend(payload.get("chunks", []))
        if not chunks:
            raise RenalRetrieverUnavailable("Frozen Renal v2 contains no chunks.")

        rendered = [chunk.get("text", "") for chunk in chunks]

        try:
            model = SentenceTransformer(self.model_name, local_files_only=True)
            model.max_seq_length = RENAL_MAX_SEQUENCE_LENGTH
            embeddings = model.encode(rendered, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
        except Exception as exc:
            raise RenalRetrieverUnavailable(f"Frozen renal v2 model could not be loaded offline: {exc}") from exc
        self._model = model
        self._chunks = chunks
        self._embeddings = embeddings

    def retrieve(self, query: str, top_k: int = 5) -> list[RenalRetrievalHit]:
        self._load()
        assert self._model is not None and self._chunks is not None and self._embeddings is not None
        query_embedding = self._model.encode(
            [RENAL_QUERY_INSTRUCTION + query], normalize_embeddings=True, show_progress_bar=False
        )[0]
        scores = self._embeddings @ query_embedding
        ranked = scores.argsort()[::-1][:top_k]
        return [RenalRetrievalHit(self._chunks[int(index)], float(scores[int(index)])) for index in ranked]


class QwenRenalRetrieverV3:
    """Frozen Renal V3 retriever with Global Dense + Document Prior + CrossEncoder Reranking.

    Validated offline two-stage retriever using Qwen3-Embedding-0.6B and Qwen3-Reranker-0.6B
    over the 23-source undergraduate renal corpus.
    """

    def __init__(
        self,
        data_root: Path | str,
        *,
        model_name: str = RENAL_MODEL,
        reranker_name: str = "Qwen/Qwen3-Reranker-0.6B",
        alpha_doc_prior: float = 0.18,
        candidate_depth: int = 20,
    ) -> None:
        self.data_root = Path(data_root)
        self.model_name = model_name
        self.reranker_name = reranker_name
        self.alpha_doc_prior = alpha_doc_prior
        self.candidate_depth = candidate_depth
        self._model: Any | None = None
        self._reranker: Any | None = None
        self._chunks: list[dict[str, Any]] | None = None
        self._embeddings: Any | None = None
        self._doc_embeddings: Any | None = None
        self._doc_ids_sorted: list[str] | None = None
        self._doc_id_to_idx: dict[str, int] | None = None

    def _load(self) -> None:
        if self._embeddings is not None and self._reranker is not None:
            return
        try:
            from sentence_transformers import CrossEncoder, SentenceTransformer
        except ImportError as exc:
            raise RenalRetrieverUnavailable(
                "Renal V3 retrieval requires 'sentence_transformers' and 'renal-ml' dependencies."
            ) from exc

        registry_path = self.data_root / "metadata" / "renal_source_registry_v2.json"
        chunks_dir = self.data_root / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"
        if not registry_path.exists() or not chunks_dir.exists():
            raise RenalRetrieverUnavailable("Frozen Renal v3 registry or chunks are unavailable.")

        reg_data = json.loads(registry_path.read_text(encoding="utf-8"))
        doc_titles = {d["document_id"]: d.get("title", "") for d in reg_data.get("documents", [])}
        doc_topics = {d["document_id"]: ", ".join(d.get("topic_tags", [])) for d in reg_data.get("documents", [])}

        chunks: list[dict[str, Any]] = []
        doc_first_texts: dict[str, str] = {}
        for path in sorted(chunks_dir.glob("*.chunks.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for ch in payload.get("chunks", []):
                chunks.append(ch)
                did = ch.get("document_id")
                if did and did not in doc_first_texts:
                    doc_first_texts[did] = ch.get("text", "")[:300]

        if not chunks:
            raise RenalRetrieverUnavailable("Frozen Renal v3 contains no chunks.")

        doc_ids_sorted = sorted(list(doc_first_texts.keys()))
        doc_id_to_idx = {did: i for i, did in enumerate(doc_ids_sorted)}
        doc_texts = [
            f"Title: {doc_titles.get(did, '')}\nTopics: {doc_topics.get(did, '')}\nOverview: {doc_first_texts.get(did, '')}"
            for did in doc_ids_sorted
        ]

        rendered = [chunk.get("text", "") for chunk in chunks]

        try:
            model = SentenceTransformer(self.model_name, local_files_only=True)
            model.max_seq_length = RENAL_MAX_SEQUENCE_LENGTH
            embeddings = model.encode(rendered, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
            doc_embeddings = model.encode(doc_texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
            reranker = CrossEncoder(self.reranker_name, trust_remote_code=True)
        except Exception as exc:
            raise RenalRetrieverUnavailable(f"Frozen renal v3 models could not be loaded offline: {exc}") from exc

        self._model = model
        self._reranker = reranker
        self._chunks = chunks
        self._embeddings = embeddings
        self._doc_embeddings = doc_embeddings
        self._doc_ids_sorted = doc_ids_sorted
        self._doc_id_to_idx = doc_id_to_idx

    def retrieve(self, query: str, top_k: int = 5) -> list[RenalRetrievalHit]:
        self._load()
        assert (
            self._model is not None
            and self._reranker is not None
            and self._chunks is not None
            and self._embeddings is not None
            and self._doc_embeddings is not None
            and self._doc_id_to_idx is not None
        )
        import numpy as np

        query_emb = self._model.encode(
            [RENAL_QUERY_INSTRUCTION + query], normalize_embeddings=True, show_progress_bar=False
        )[0]
        # First-stage dense dot products
        p_scores = self._embeddings @ query_emb
        d_scores = self._doc_embeddings @ query_emb

        combined_scores = np.zeros_like(p_scores)
        for i, ch in enumerate(self._chunks):
            did = ch.get("document_id")
            doc_boost = d_scores[self._doc_id_to_idx[did]] if did in self._doc_id_to_idx else 0.0
            combined_scores[i] = p_scores[i] + self.alpha_doc_prior * doc_boost

        cand_indices = combined_scores.argsort()[::-1][: self.candidate_depth]
        candidate_chunks = [self._chunks[int(idx)] for idx in cand_indices]

        # Second-stage cross-encoder reranking
        pairs = [[query, ch.get("text", "")] for ch in candidate_chunks]
        raw_rerank_scores = self._reranker.predict(pairs, batch_size=8, show_progress_bar=False)
        r_scores = np.asarray(raw_rerank_scores, dtype=np.float32).reshape(-1)
        rerank_order = r_scores.argsort()[::-1][:top_k]

        return [
            RenalRetrievalHit(candidate_chunks[int(idx)], float(r_scores[int(idx)]))
            for idx in rerank_order
        ]
