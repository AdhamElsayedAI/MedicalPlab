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
