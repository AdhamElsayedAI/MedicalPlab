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

RERANKER_4B_ID = "Qwen/Qwen3-Reranker-4B"
RERANKER_4B_REV = "22e683669bc0f0bd69640a1354a6d0aebcfeede5"

STRUCTURED_RERANK_PROMPT = (
    "Instruct: Given a medical education or clinical licensing query, determine whether the "
    "following candidate reference passage contains direct, factual clinical evidence "
    "supporting the medical claim or correct answer.\n"
    "Query: {query}\n"
    "Candidate Evidence:\n"
    "Document: {doc_title}\n"
    "Section: {section_path}\n"
    "Text: {text}"
)


class EvidenceReranker:
    """Structured medical claim reranker with 4-bit quantization support."""

    def __init__(
        self,
        model: Any = None,
        model_id: str = RERANKER_4B_ID,
        revision: str = RERANKER_4B_REV,
        device: str = "cuda",
        load_in_4bit: bool = True,
    ):
        self.model = model
        self.model_id = model_id
        self.revision = revision
        self.device = device
        self.load_in_4bit = load_in_4bit

    def load_model(self):
        """Load reranker with NF4 quantization if not already supplied."""
        if self.model is not None:
            return self.model

        try:
            import torch
            from sentence_transformers import CrossEncoder
            from transformers import BitsAndBytesConfig

            bnb_config = None
            if self.load_in_4bit and torch.cuda.is_available():
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                )

            logger.info(f"Loading CrossEncoder for {self.model_id} (revision {self.revision[:10]})...")
            model_kwargs = {
                "quantization_config": bnb_config,
                "device_map": "auto",
                "torch_dtype": torch.float16,
            }
            self.model = CrossEncoder(
                self.model_id,
                revision=self.revision,
                model_kwargs=model_kwargs,
                trust_remote_code=True,
            )
            logger.info("CrossEncoder loaded successfully.")
            return self.model
        except Exception as e:
            logger.warning(f"CrossEncoder with model_kwargs failed ({e}), attempting AutoModel...")
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, BitsAndBytesConfig

            bnb_config = None
            if self.load_in_4bit and torch.cuda.is_available():
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                )

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                revision=self.revision,
                trust_remote_code=True,
            )

            kwargs = {
                "revision": self.revision,
                "trust_remote_code": True,
            }
            if bnb_config is not None:
                kwargs["quantization_config"] = bnb_config
                kwargs["device_map"] = "auto"
                kwargs["torch_dtype"] = torch.float16

            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_id, **kwargs)
            self.model.eval()
            logger.info("AutoModel reranker loaded successfully.")
            return self.model

    def build_pair_prompt(self, query: str, candidate: RetrievedCandidate) -> tuple[str, str]:
        """Construct structured prompt pair for cross-encoder scoring without double-prompt defect."""
        sec_path = " > ".join(candidate.section_path) if candidate.section_path else candidate.heading or "General"
        passage_text = f"{candidate.doc_title} | {sec_path} | {candidate.heading}\n{candidate.text}"
        return query, passage_text

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

        if self.model is None:
            self.load_model()

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
