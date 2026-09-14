"""
MedicalPlab Shared Evidence Engine V2 — Candidate Retriever
===========================================================
Implements multi-channel four-route candidate retrieval:
- Route A: Global corpus dense retrieval (top 50)
- Route B: Document-local filtered retrieval across top 8 routed documents (top 10 per doc)
- Route C: Section-local retrieval matching query representation to section paths
- Route D: Lexical BM25 retrieval across all corpus chunks (top 50)
- Fusion: Weighted Reciprocal Rank Fusion (RRF k=60) producing fused candidate rankings
"""

import hashlib
import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from medicalplab.evidence_engine.document_router import DeterministicDocumentRouter
from medicalplab.evidence_engine.models import QueryRepresentation, RetrievedCandidate

logger = logging.getLogger(__name__)

RRF_K = 60


@dataclass(frozen=True)
class RetrievalConfig:
    """Auditable retrieval controls used by production and DEV ablations."""

    use_field_aware_bm25: bool = True
    bm25_title_weight: float = 1.0
    bm25_heading_weight: float = 2.0
    bm25_body_weight: float = 1.0
    use_full_section_path: bool = False
    section_overlap_bonus: float = 0.05
    noise_section_penalty: float = 1.0
    rrf_k: int = RRF_K
    rrf_weights: tuple[float, float, float, float] = (1.0, 1.3, 1.1, 1.3)

    @classmethod
    def v1(cls) -> "RetrievalConfig":
        """Exact canonical V1 retrieval settings for controlled comparison."""
        return cls(
            use_field_aware_bm25=False,
            bm25_title_weight=1.0,
            bm25_heading_weight=3.0,
            bm25_body_weight=1.0,
            use_full_section_path=False,
            section_overlap_bonus=0.05,
            noise_section_penalty=1.0,
            rrf_k=RRF_K,
            rrf_weights=(1.0, 1.5, 1.0, 1.2),
        )


class CandidateRetriever:
    """Four-route multi-channel candidate retriever with reciprocal rank fusion."""

    def __init__(
        self,
        data_root: Path | str,
        embedder: Any = None,
        router: DeterministicDocumentRouter | None = None,
        cache_dir: Path | str | None = None,
        config: RetrievalConfig | None = None,
    ):
        self.data_root = Path(data_root)
        self.embedder = embedder
        self.router = router or DeterministicDocumentRouter(self.data_root)
        self.cache_dir = Path(cache_dir) if cache_dir else (self.data_root.parent / ".cache" / "evidence_engine")
        self.config = config or RetrievalConfig()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.chunks: dict[str, dict[str, Any]] = {}
        self.ordered_chunk_ids: list[str] = []
        self.doc_to_chunk_indices: dict[str, list[int]] = {}
        self.section_to_chunk_indices: dict[tuple[str, str], list[int]] = {}
        self.section_path_to_chunk_indices: dict[tuple[str, tuple[str, ...]], list[int]] = {}
        self.corpus_embeddings: np.ndarray | None = None

        # BM25 index data structures
        self.doc_len: dict[str, int] = {}
        self.avgdl: float = 1.0
        self.idf: dict[str, float] = {}
        self.tf: dict[str, Counter] = {}
        self.field_doc_len: dict[str, dict[str, int]] = {}
        self.field_avgdl: dict[str, float] = {}
        self.field_tf: dict[str, dict[str, Counter]] = {}

        self._load_corpus()

    def _resolve_chunks_dir(self) -> Path:
        """Dynamically resolve the chunks directory from available candidates."""
        candidates = [
            self.data_root / "experiments" / "renal" / "chunking" / "B_400_10pct_overlap",
            self.data_root / "experiments" / "renal_v2" / "chunking" / "B_400_overlap",
            self.data_root / "processed" / "renal_v1",
            self.data_root / "experiments" / "renal" / "chunking" / "C_section_aware",
        ]
        for c in candidates:
            if c.exists() and any(c.glob("*.chunks.json")):
                return c
        return candidates[0]

    # Sections that may receive a small DEV-validated soft penalty. They are
    # never excluded because clinically relevant evidence can occur in them.
    _NOISE_SECTION_PREFIXES: tuple[str, ...] = (
        "method", "result", "material", "reference", "supplementary",
        "acknowledgement", "acknowledgment", "author contribution",
        "conflict of interest", "data availability",
    )

    def _tokenize(self, text: str) -> list[str]:
        """Extractive tokenization for lexical indexing."""
        return [w for w in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(w) > 2]

    def _is_noise_section(self, section_path: list[str]) -> bool:
        """Return True if the section path indicates a noise section (Methods/Results/etc.)."""
        if not section_path:
            return False
        for section in section_path:
            normalized = re.sub(r"^\s*\d+(?:\.\d+)*[.)]?\s*", "", section.lower()).strip()
            if any(normalized.startswith(pfx) for pfx in self._NOISE_SECTION_PREFIXES):
                return True
        return False

    def _load_corpus(self):
        """Load all chunks, build document/section index mappings, and construct BM25 index."""
        chunks_dir = self._resolve_chunks_dir()
        chunks = {}
        ordered_ids = []

        chunk_files = sorted(chunks_dir.glob("*.chunks.json")) if chunks_dir.exists() else []
        for p in chunk_files:
            file_data = json.loads(p.read_bytes())
            doc_id = file_data.get("document_id")
            for ch in file_data.get("chunks", []):
                cid = ch.get("chunk_id")
                ch["document_id"] = doc_id
                if not ch.get("doc_title") and doc_id in self.router.cards:
                    ch["doc_title"] = self.router.cards[doc_id].title
                chunks[cid] = ch
                ordered_ids.append(cid)

        self.chunks = chunks
        self.ordered_chunk_ids = ordered_ids

        # Build index maps
        self.doc_to_chunk_indices = {}
        self.section_to_chunk_indices = {}
        self.section_path_to_chunk_indices = {}
        for idx, cid in enumerate(self.ordered_chunk_ids):
            ch = self.chunks[cid]
            doc_id = ch["document_id"]
            self.doc_to_chunk_indices.setdefault(doc_id, []).append(idx)

            sec = ch.get("heading") or "General"
            self.section_to_chunk_indices.setdefault((doc_id, sec), []).append(idx)
            path = tuple(ch.get("section_path", [])) or (sec,)
            self.section_path_to_chunk_indices.setdefault((doc_id, path), []).append(idx)

        # Preserve the exact V1 concatenated index and build separate fields for
        # true BM25F scoring. This avoids token-duplication approximations and
        # permits like-for-like V1/V2 ablation with one implementation.
        corpus_tokens: dict[str, list[str]] = {}
        field_tokens: dict[str, dict[str, list[str]]] = {
            "title": {},
            "heading": {},
            "body": {},
        }
        for cid in self.ordered_chunk_ids:
            ch = self.chunks[cid]
            title_tokens = self._tokenize(ch.get("doc_title", ""))
            heading_tokens = self._tokenize(ch.get("heading", ""))
            body_tokens = self._tokenize(ch.get("text", ""))
            corpus_tokens[cid] = title_tokens + heading_tokens + body_tokens
            field_tokens["title"][cid] = title_tokens
            field_tokens["heading"][cid] = heading_tokens
            field_tokens["body"][cid] = body_tokens

        self.doc_len = {cid: len(corpus_tokens[cid]) for cid in self.ordered_chunk_ids}
        self.avgdl = (sum(self.doc_len.values()) / len(self.doc_len)) if self.doc_len else 1.0
        n_docs = len(self.ordered_chunk_ids)

        df = Counter()
        for cid in self.ordered_chunk_ids:
            for w in set(corpus_tokens[cid]):
                df[w] += 1

        self.idf = {w: math.log((n_docs - n + 0.5) / (n + 0.5) + 1.0) for w, n in df.items()}
        self.tf = {cid: Counter(corpus_tokens[cid]) for cid in self.ordered_chunk_ids}
        self.field_doc_len = {
            field: {cid: len(tokens[cid]) for cid in self.ordered_chunk_ids}
            for field, tokens in field_tokens.items()
        }
        self.field_avgdl = {
            field: (sum(lengths.values()) / len(lengths) if lengths else 1.0)
            for field, lengths in self.field_doc_len.items()
        }
        self.field_tf = {
            field: {cid: Counter(tokens[cid]) for cid in self.ordered_chunk_ids}
            for field, tokens in field_tokens.items()
        }

        logger.info(
            f"Loaded {len(self.chunks)} corpus chunks across {len(self.doc_to_chunk_indices)} documents from {chunks_dir}. "
            f"BM25 index built (vocab size: {len(self.idf)})."
        )

    def ensure_corpus_embeddings(self, embedding_dim: int | None = None) -> np.ndarray | None:
        """Compute or load normalized corpus embeddings with cache integrity."""
        if not self.ordered_chunk_ids:
            return None

        # Hash chunk IDs to guarantee cache integrity
        corpus_hash = hashlib.sha256("".join(self.ordered_chunk_ids).encode("utf-8")).hexdigest()[:12]
        cache_file = self.cache_dir / f"corpus_embeddings_{len(self.ordered_chunk_ids)}_{corpus_hash}.npy"

        if cache_file.exists() and self.corpus_embeddings is None:
            try:
                embs = np.load(cache_file)
                if len(embs) == len(self.ordered_chunk_ids):
                    self.corpus_embeddings = embs
                    logger.info(f"Loaded cached corpus embeddings: {self.corpus_embeddings.shape}")
                    return self.corpus_embeddings
            except Exception as e:
                logger.warning(f"Could not load cached embeddings: {e}")

        # Check existing fallback cache
        legacy_cache = self.cache_dir / f"corpus_embeddings_{len(self.ordered_chunk_ids)}.npy"
        if legacy_cache.exists() and self.corpus_embeddings is None:
            try:
                embs = np.load(legacy_cache)
                if len(embs) == len(self.ordered_chunk_ids):
                    self.corpus_embeddings = embs
                    return self.corpus_embeddings
            except Exception:
                pass

        if self.corpus_embeddings is None and self.embedder is not None:
            logger.info("Computing dense embeddings for all corpus chunks...")
            texts = [
                f"{self.chunks[cid].get('doc_title', '')} | {self.chunks[cid].get('heading', '')}\n{self.chunks[cid].get('text', '')}"
                for cid in self.ordered_chunk_ids
            ]
            embs = self.embedder.encode(texts, batch_size=8, show_progress_bar=False)
            embs = np.asarray(embs, dtype=np.float32)
            norms = np.linalg.norm(embs, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            embs = embs / norms
            self.corpus_embeddings = embs

            try:
                np.save(cache_file, self.corpus_embeddings)
                logger.info(f"Saved corpus embeddings to {cache_file.name}")
            except Exception as e:
                logger.warning(f"Could not cache corpus embeddings: {e}")

        return self.corpus_embeddings

    def encode_query(self, query_text: str) -> np.ndarray | None:
        """Encode query into unit-normalized embedding."""
        if self.embedder is None:
            return None
        emb = self.embedder.encode(
            [query_text],
            prompt="Instruct: Given a medical query, retrieve relevant clinical evidence passages.\nQuery: ",
            show_progress_bar=False,
        )[0]
        emb = np.asarray(emb, dtype=np.float32)
        norm = np.linalg.norm(emb)
        return emb / norm if norm > 0 else emb

    def _bm25_score(self, cid: str, q_tokens: list[str]) -> float:
        """Score one chunk with exact V1 BM25 or configured BM25F fields."""
        k1 = 1.5
        b = 0.75
        if not self.config.use_field_aware_bm25:
            c_tf = self.tf[cid]
            length = self.doc_len[cid]
            return sum(
                self.idf.get(word, 0.0)
                * (c_tf[word] * (k1 + 1.0))
                / (c_tf[word] + k1 * (1.0 - b + b * (length / self.avgdl)))
                for word in q_tokens
                if word in c_tf
            )

        weights = {
            "title": self.config.bm25_title_weight,
            "heading": self.config.bm25_heading_weight,
            "body": self.config.bm25_body_weight,
        }
        score = 0.0
        for word in q_tokens:
            weighted_tf = 0.0
            for field, weight in weights.items():
                tf = self.field_tf[field][cid][word]
                if not tf or weight <= 0.0:
                    continue
                length = self.field_doc_len[field][cid]
                avgdl = self.field_avgdl[field] or 1.0
                weighted_tf += weight * tf / (1.0 - b + b * (length / avgdl))
            if weighted_tf > 0.0:
                score += self.idf.get(word, 0.0) * (weighted_tf * (k1 + 1.0)) / (weighted_tf + k1)
        return score

    def retrieve_candidates(
        self,
        query_rep: QueryRepresentation,
        top_k: int = 50,
        route_a_k: int = 50,
        route_b_docs: int = 8,
        route_b_per_doc: int = 10,
        route_c_k: int = 30,
        route_d_k: int = 50,
    ) -> list[RetrievedCandidate]:
        """Execute four-route retrieval and weighted reciprocal rank fusion."""
        target_text = query_rep.neutral_target or query_rep.canonical_query or query_rep.original_query
        q_tokens = self._tokenize(target_text)

        # Dense similarity prep
        has_dense = False
        global_sims = None
        if self.embedder is not None:
            self.ensure_corpus_embeddings()
            if self.corpus_embeddings is not None:
                q_emb = self.encode_query(target_text)
                if q_emb is not None:
                    global_sims = np.dot(self.corpus_embeddings, q_emb)
                    has_dense = True

        # -------------------------------------------------------------
        # Route A: Global Corpus Dense Retrieval (top 50)
        # -------------------------------------------------------------
        route_a_candidates: dict[str, tuple[int, float]] = {}
        if has_dense and global_sims is not None:
            top_a_indices = np.argsort(global_sims)[::-1][:route_a_k]
            for rank, idx in enumerate(top_a_indices, start=1):
                cid = self.ordered_chunk_ids[idx]
                route_a_candidates[cid] = (rank, float(global_sims[idx]))

        # -------------------------------------------------------------
        # Route B: Document-Local Filtered Retrieval (top 8 docs)
        # -------------------------------------------------------------
        routed_docs = self.router.route_documents(
            query_rep.canonical_query,
            embedder=self.embedder,
            top_k=route_b_docs,
        )

        route_b_candidates: dict[str, tuple[int, float]] = {}
        route_b_pool: list[tuple[str, float]] = []
        for doc_id in routed_docs:
            doc_chunk_indices = self.doc_to_chunk_indices.get(doc_id, [])
            if not doc_chunk_indices:
                continue
            if has_dense and global_sims is not None:
                doc_sims = global_sims[doc_chunk_indices]
                top_local = np.argsort(doc_sims)[::-1][:route_b_per_doc]
                for local_idx in top_local:
                    actual_idx = doc_chunk_indices[local_idx]
                    cid = self.ordered_chunk_ids[actual_idx]
                    route_b_pool.append((cid, float(global_sims[actual_idx])))
            else:
                for actual_idx in doc_chunk_indices[:route_b_per_doc]:
                    cid = self.ordered_chunk_ids[actual_idx]
                    route_b_pool.append((cid, 1.0))

        route_b_pool.sort(key=lambda x: x[1], reverse=True)
        for rank, (cid, score) in enumerate(route_b_pool, start=1):
            if cid not in route_b_candidates:
                route_b_candidates[cid] = (rank, score)

        # -------------------------------------------------------------
        # Route C: Section-Local Matching (top 30)
        # Full section paths are available for DEV ablation, but the default
        # retains heading-local matching because it generalized better.
        # -------------------------------------------------------------
        route_c_candidates: dict[str, tuple[int, float]] = {}
        route_c_pool: list[tuple[str, float]] = []

        section_index = (
            self.section_path_to_chunk_indices
            if self.config.use_full_section_path
            else self.section_to_chunk_indices
        )
        for doc_id in routed_docs:
            for (sec_doc_id, section_key), c_indices in section_index.items():
                if sec_doc_id != doc_id:
                    continue
                if self.config.use_full_section_path:
                    section_tokens = set(self._tokenize(" ".join(section_key)))
                else:
                    section_tokens = set(self._tokenize(section_key))
                overlap = sum(1 for word in section_tokens if word in q_tokens)
                if overlap > 0:
                    for c_idx in c_indices[:3]:
                        cid = self.ordered_chunk_ids[c_idx]
                        base_score = float(global_sims[c_idx]) if (has_dense and global_sims is not None) else 0.5
                        bonus_score = base_score + (self.config.section_overlap_bonus * overlap)
                        route_c_pool.append((cid, bonus_score))

        route_c_pool.sort(key=lambda x: x[1], reverse=True)
        for rank, (cid, score) in enumerate(route_c_pool[:route_c_k], start=1):
            if cid not in route_c_candidates:
                route_c_candidates[cid] = (rank, score)

        # -------------------------------------------------------------
        # Route D: Corpus BM25 Lexical Retrieval (top 50)
        # -------------------------------------------------------------
        route_d_candidates: dict[str, tuple[int, float]] = {}
        bm25_scores: dict[str, float] = {}
        for cid in self.ordered_chunk_ids:
            s = self._bm25_score(cid, q_tokens)
            if s > 0:
                bm25_scores[cid] = s

        top_d_cids = sorted(bm25_scores.keys(), key=lambda c: bm25_scores[c], reverse=True)[:route_d_k]
        for rank, cid in enumerate(top_d_cids, start=1):
            route_d_candidates[cid] = (rank, bm25_scores[cid])

        # -------------------------------------------------------------
        # Weighted Reciprocal Rank Fusion (RRF k=60)
        # -------------------------------------------------------------
        all_candidate_ids = (
            set(route_a_candidates.keys())
            | set(route_b_candidates.keys())
            | set(route_c_candidates.keys())
            | set(route_d_candidates.keys())
        )
        fused_scores: dict[str, float] = {}

        w_a, w_b, w_c, w_d = self.config.rrf_weights

        for cid in all_candidate_ids:
            score = 0.0
            if cid in route_a_candidates:
                score += w_a / (self.config.rrf_k + route_a_candidates[cid][0])
            if cid in route_b_candidates:
                score += w_b / (self.config.rrf_k + route_b_candidates[cid][0])
            if cid in route_c_candidates:
                score += w_c / (self.config.rrf_k + route_c_candidates[cid][0])
            if cid in route_d_candidates:
                score += w_d / (self.config.rrf_k + route_d_candidates[cid][0])

            # Optional soft penalty only; production default is 1.0 because
            # DEV showed no stable gain and relevant evidence may live here.
            sp = self.chunks[cid].get("section_path", [])
            if self._is_noise_section(sp):
                score *= self.config.noise_section_penalty

            fused_scores[cid] = score

        sorted_cids = sorted(all_candidate_ids, key=lambda c: (fused_scores[c], c), reverse=True)[:top_k]

        candidates = []
        for cid in sorted_cids:
            raw = self.chunks[cid]
            ranks = {}
            scores = {}
            if cid in route_a_candidates:
                ranks["ROUTE_A"] = route_a_candidates[cid][0]
                scores["ROUTE_A"] = route_a_candidates[cid][1]
            if cid in route_b_candidates:
                ranks["ROUTE_B"] = route_b_candidates[cid][0]
                scores["ROUTE_B"] = route_b_candidates[cid][1]
            if cid in route_c_candidates:
                ranks["ROUTE_C"] = route_c_candidates[cid][0]
                scores["ROUTE_C"] = route_c_candidates[cid][1]
            if cid in route_d_candidates:
                ranks["ROUTE_D"] = route_d_candidates[cid][0]
                scores["ROUTE_D"] = route_d_candidates[cid][1]

            candidates.append(
                RetrievedCandidate(
                    chunk_id=cid,
                    document_id=raw["document_id"],
                    section_path=raw.get("section_path", []),
                    heading=raw.get("heading", ""),
                    text=raw.get("text", ""),
                    doc_title=raw.get("doc_title", ""),
                    fused_score=fused_scores[cid],
                    channel_ranks=ranks,
                    channel_scores=scores,
                )
            )

        return candidates
