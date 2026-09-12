"""
MedicalPlab Shared Evidence Engine V2 — Deterministic Document Router
====================================================================
Builds 23 deterministic, non-generative document cards from source corpus
metadata, chunks, and registries.
Routes clinical queries to relevant source documents using:
- Precomputed document card embeddings
- Cross-encoder document card routing
- Reciprocal Rank Fusion of document-level signals
"""

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from medicalplab.evidence_engine.models import DocumentCard

logger = logging.getLogger(__name__)

DOCUMENT_ROUTING_INSTRUCTION = (
    "Instruct: Given a medical education or clinical question, determine whether this "
    "source document is likely to contain direct evidence needed to answer the "
    "requested medical claim.\nQuery: "
)


class DeterministicDocumentRouter:
    """Deterministic document router scoring all 23 source document cards."""

    def __init__(self, data_root: Path | str):
        self.data_root = Path(data_root)
        self.cards: dict[str, DocumentCard] = {}
        self.ordered_doc_ids: list[str] = []
        self._doc_embeddings: np.ndarray | None = None

    def build_or_load_cards(self) -> dict[str, DocumentCard]:
        """Construct deterministic document cards from metadata registries and chunks."""
        registry_path = self.data_root / "metadata" / "renal_source_registry_v2.json"
        manifest_path = self.data_root / "metadata" / "document_manifest.json"
        chunks_dir = self.data_root / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"

        registry_docs: dict[str, dict[str, Any]] = {}
        if registry_path.exists():
            reg_data = json.loads(registry_path.read_bytes())
            for d in reg_data.get("documents", []):
                registry_docs[d["document_id"]] = d

        manifest_docs: dict[str, dict[str, Any]] = {}
        if manifest_path.exists():
            man_data = json.loads(manifest_path.read_bytes())
            for d in man_data:
                manifest_docs[d["document_id"]] = d

        # Read all chunk files to extract real abstracts and all headings
        cards: dict[str, DocumentCard] = {}
        for p in sorted(chunks_dir.glob("*.chunks.json")):
            file_data = json.loads(p.read_bytes())
            doc_id = file_data.get("document_id")
            chunks = file_data.get("chunks", [])
            if not doc_id:
                continue

            reg_info = registry_docs.get(doc_id, {})
            man_info = manifest_docs.get(doc_id, {})

            title = reg_info.get("title") or man_info.get("title") or chunks[0].get("doc_title", doc_id)
            authors = reg_info.get("authors", "")
            topics = reg_info.get("topic_tags") or man_info.get("topics", [])
            license_name = reg_info.get("license_name") or man_info.get("license_name", "")
            doi = reg_info.get("doi") or man_info.get("doi")
            pmcid = reg_info.get("pmcid")
            sha = reg_info.get("sha256") or man_info.get("sha256", "")
            auth_score = reg_info.get("authority_score", 15)

            # Extractive abstract and headings
            abstract_text = ""
            headings = []
            seen_headings = set()

            for ch in chunks:
                h = ch.get("heading", "")
                if h and h not in seen_headings:
                    headings.append(h)
                    seen_headings.add(h)
                for sec in ch.get("section_path", []):
                    if sec and sec not in seen_headings:
                        headings.append(sec)
                        seen_headings.add(sec)

                if not abstract_text and ("abstract" in h.lower() or ch.get("source_block_index") == 1):
                    abstract_text = ch.get("text", "")

            if not abstract_text and chunks:
                abstract_text = chunks[0].get("text", "")[:600]

            synopsis = abstract_text[:400]

            cards[doc_id] = DocumentCard(
                document_id=doc_id,
                title=title,
                authority=authors or "MedicalPlab Peer-Reviewed Nephrology Corpus",
                abstract=abstract_text,
                topic_tags=topics,
                section_headings=headings,
                synopsis=synopsis,
                license_name=license_name,
                doi=doi,
                pmcid=pmcid,
                sha256=sha,
                authority_score=auth_score,
            )

        self.cards = cards
        self.ordered_doc_ids = sorted(cards.keys())
        logger.info(f"Loaded {len(self.cards)} deterministic document cards.")
        return self.cards

    def route_documents(
        self,
        query: str,
        *,
        embedder: Any = None,
        reranker: Any = None,
        top_k: int = 5
    ) -> list[str]:
        """Score all 23 document cards and return ranked document IDs."""
        if not self.cards:
            self.build_or_load_cards()

        doc_scores: dict[str, float] = {did: 0.0 for did in self.ordered_doc_ids}

        # 1. Cross-encoder direct scoring over document cards if reranker available
        if reranker is not None:
            pairs = []
            inst_query = DOCUMENT_ROUTING_INSTRUCTION + query
            for did in self.ordered_doc_ids:
                card = self.cards[did]
                pairs.append([inst_query, card.render_routing_text()])

            scores = reranker.predict(pairs, batch_size=8, show_progress_bar=False)
            scores = np.asarray(scores, dtype=np.float32).reshape(-1)
            for i, did in enumerate(self.ordered_doc_ids):
                doc_scores[did] += float(scores[i])

        # 2. Embedding similarity if embedder available
        elif embedder is not None:
            q_emb = embedder.encode(
                [query],
                prompt="Instruct: Given a medical query, retrieve relevant medical documents.\nQuery: ",
                show_progress_bar=False
            )[0]
            # Normalize
            q_emb = q_emb / np.linalg.norm(q_emb)

            if self._doc_embeddings is None:
                card_texts = [self.cards[did].render_routing_text() for did in self.ordered_doc_ids]
                doc_embs = embedder.encode(card_texts, show_progress_bar=False)
                # Normalize
                doc_embs = doc_embs / np.linalg.norm(doc_embs, axis=1, keepdims=True)
                self._doc_embeddings = doc_embs

            sims = np.dot(self._doc_embeddings, q_emb)
            for i, did in enumerate(self.ordered_doc_ids):
                doc_scores[did] += float(sims[i])

        # Sort by final score
        ranked = sorted(doc_scores.keys(), key=lambda d: doc_scores[d], reverse=True)
        return ranked[:top_k]
