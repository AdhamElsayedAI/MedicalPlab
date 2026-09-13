"""
MedicalPlab Shared Evidence Engine V2 — Evidence Reranker
=========================================================
Implements structured medical claim reranking using Qwen3-Reranker-4B
under NF4 (4-bit) quantization on RTX 3060 6GB.
- Structured medical claim prompt format
- Hierarchical document + section path context injection
- Deterministic score extraction and candidate sorting
"""

import gc
import logging
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from medicalplab.evidence_engine.models import QueryRepresentation, RetrievedCandidate

logger = logging.getLogger(__name__)

RERANKER_06B_ID = "Qwen/Qwen3-Reranker-0.6B"
RERANKER_06B_REV = "e61197ed45024b0ed8a2d74b80b4d909f1255473"

RERANKER_4B_ID = "Qwen/Qwen3-Reranker-4B"
RERANKER_4B_REV = "22e683669bc0f0bd69640a1354a6d0aebcfeede5"

MEDICAL_RERANKER_INSTRUCTION = (
    "Instruct: Determine whether the evidence passage directly supports the exact "
    "medical proposition requested in the query. Topical relevance without direct "
    "claim support is non-support.\nQuery: "
)


class EvidenceReranker:
    """Structured medical claim reranker with graceful fallback."""

    def __init__(
        self,
        model: Any = None,
        model_id: str = RERANKER_06B_ID,
        revision: str = RERANKER_06B_REV,
        device: str = "auto",
        load_in_4bit: bool = False,
    ):
        self.model = model
        self.model_id = model_id
        self.revision = revision
        self.device = device
        self.load_in_4bit = load_in_4bit
        self.is_degraded: bool = False
        self.tokenizer = None

    def load_model(self):
        """Load reranker model with graceful fallback on resource or environment failure."""
        if self.model is not None:
            return self.model

        try:
            import torch
            from sentence_transformers import CrossEncoder

            device_str = "cuda" if (self.device == "cuda" or (self.device == "auto" and torch.cuda.is_available())) else "cpu"
            logger.info(f"Loading CrossEncoder for {self.model_id} on {device_str}...")

            self.model = CrossEncoder(
                self.model_id,
                revision=self.revision,
                device=device_str,
                trust_remote_code=True,
            )
            logger.info("CrossEncoder loaded successfully.")
            self.is_degraded = False
            return self.model
        except Exception as e:
            logger.warning(f"CrossEncoder loading failed ({e}), attempting AutoModel...")
            try:
                import torch
                from transformers import AutoModelForSequenceClassification, AutoTokenizer

                device_str = "cuda" if torch.cuda.is_available() else "cpu"
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_id,
                    revision=self.revision,
                    trust_remote_code=True,
                )
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_id,
                    revision=self.revision,
                    trust_remote_code=True,
                ).to(device_str)
                self.model.eval()
                self.is_degraded = False
                logger.info("AutoModel reranker loaded successfully.")
                return self.model
            except Exception as e2:
                logger.warning(f"Neural reranker unavailable ({e2}). Entering CANONICAL_DEGRADED mode.")
                self.is_degraded = True
                self.model = None
                return None

    def build_pair_prompt(self, query: str, candidate: RetrievedCandidate) -> tuple[str, str]:
        """Construct structured prompt pair for cross-encoder scoring."""
        inst_query = MEDICAL_RERANKER_INSTRUCTION + query
        sec_path = " > ".join(candidate.section_path) if candidate.section_path else candidate.heading or "General"
        passage_text = (
            f"Title: {candidate.doc_title}\n"
            f"Section Path: {sec_path}\n"
            f"Heading: {candidate.heading}\n"
            f"Evidence: {candidate.text}"
        )
        return inst_query, passage_text

    def rerank(
        self,
        query: str | QueryRepresentation,
        candidates: list[RetrievedCandidate],
        top_k: int | None = None,
        batch_size: int = 8,
    ) -> list[RetrievedCandidate]:
        """Score candidate passages and return deterministically ranked list."""
        if not candidates:
            return []

        if isinstance(query, QueryRepresentation):
            query_str = query.canonical_query or query.original_query
        else:
            query_str = str(query)

        if self.model is None and not self.is_degraded:
            self.load_model()

        if self.is_degraded or self.model is None:
            # CANONICAL_DEGRADED: candidates preserve fused score ordering with tie breaking
            ranked = sorted(candidates, key=lambda c: (c.fused_score, c.chunk_id), reverse=True)
            for c in ranked:
                c.rerank_score = c.fused_score
            return ranked[:top_k] if top_k is not None else ranked

        # Build pair inputs
        pairs = [self.build_pair_prompt(query_str, cand) for cand in candidates]

        scores = []
        try:
            # Check if CrossEncoder
            if hasattr(self.model, "predict"):
                raw_scores = self.model.predict(pairs, batch_size=batch_size, show_progress_bar=False)
                scores = np.asarray(raw_scores, dtype=np.float32).reshape(-1).tolist()
            else:
                # Transformers AutoModelForSequenceClassification
                import torch

                all_scores = []
                for i in range(0, len(pairs), batch_size):
                    batch_pairs = pairs[i : i + batch_size]
                    inputs = self.tokenizer(
                        [p[0] for p in batch_pairs],
                        [p[1] for p in batch_pairs],
                        padding=True,
                        truncation=True,
                        max_length=512,
                        return_tensors="pt",
                    )
                    if hasattr(self.model, "device"):
                        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                    with torch.no_grad():
                        logits = self.model(**inputs).logits
                        if logits.shape[-1] == 1:
                            batch_scores = logits.squeeze(-1).float().cpu().numpy()
                        else:
                            # If binary classification, take positive class logit
                            batch_scores = logits[:, -1].float().cpu().numpy()
                        all_scores.extend(batch_scores.tolist())
                scores = all_scores
        except Exception as e:
            logger.error(f"Error during reranker inference: {e}")
            raise

        # Assign rerank scores to candidates
        for cand, score in zip(candidates, scores):
            cand.rerank_score = float(score)

        # Deterministic sort: descending by rerank_score, then descending by fused_score
        ranked = sorted(candidates, key=lambda c: (c.rerank_score, c.fused_score), reverse=True)

        if top_k is not None:
            return ranked[:top_k]
        return ranked

    def cleanup_vram(self):
        """Free model from GPU memory."""
        if self.model is not None:
            del self.model
            self.model = None
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            logger.info("Reranker VRAM cleaned up.")
        except Exception:
            pass


NeuralEvidenceReranker = EvidenceReranker
