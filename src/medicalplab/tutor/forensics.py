"""Non-sensitive forensic audit capture for post-hoc live-veto diagnosis.

Captures enough per-proposition detail during a live request so that a future
audit can distinguish MODEL_GENERATION_ERROR / VERIFIER_FALSE_POSITIVE /
EVIDENCE_BINDING_ERROR / RETRIEVAL_MISMATCH without needing to re-run a live
provider call.

Hard exclusions (never captured here, and nothing below ever receives them):
- API keys, auth headers
- Hidden system prompts or chain-of-thought
- PII / real learner identity or history
- Restricted-publisher content (evidence excerpts are only stored when the
  source document's DisplayQuotationStatus is DISPLAY_ALLOWED)

This module is purely additive observability. It never influences
CentralClaimVerifier's decision, RAG ranking, or evidence thresholds.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Sequence

from medicalplab.tutor.models import ExtractedProposition, ForensicPropositionRecord
from medicalplab.tutor.rights import DisplayQuotationStatus, SourceRightsGate

logger = logging.getLogger(__name__)

EVIDENCE_EXCERPT_MAX_CHARS = 300


def stable_text_hash(text: str) -> str:
    """Short, stable, non-reversible-in-practice identifier for a piece of text."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


class ForensicAuditLogger:
    """In-memory collector of ForensicPropositionRecord entries for the current process."""

    def __init__(self, store_full_text: bool = True) -> None:
        # store_full_text=True is appropriate for synthetic/test evaluation traffic (no PII).
        # Set to False to retain only stable hashes + identifiers (e.g. for real learner traffic).
        self.store_full_text = store_full_text
        self._records: list[ForensicPropositionRecord] = []

    def capture_propositions(
        self,
        *,
        request_id: str,
        propositions: Sequence[ExtractedProposition],
        candidates: Sequence[Any],
        rights_gate: SourceRightsGate,
        requested_provider: str,
        requested_model: str,
        actual_generation_provider: str,
        actual_generation_model: str,
        provider_failover_applied: bool,
        support_status: str,
        reached_learner: bool,
    ) -> list[ForensicPropositionRecord]:
        """Build and store one ForensicPropositionRecord per SUBSTANTIVE_FACTUAL proposition."""
        cand_text_by_chunk: dict[str, str] = {}
        for cand in candidates:
            chunk_id = cand.chunk_id if hasattr(cand, "chunk_id") else cand.get("chunk_id")
            text = cand.text if hasattr(cand, "text") else cand.get("text", "")
            if chunk_id:
                cand_text_by_chunk[chunk_id] = text

        new_records: list[ForensicPropositionRecord] = []
        for prop in propositions:
            if prop.classification != "SUBSTANTIVE_FACTUAL":
                continue

            evidence_excerpt: str | None = None
            evidence_hash: str | None = None
            doc_id = prop.verified_document_id
            chunk_id = prop.verified_chunk_id
            evidence_text = cand_text_by_chunk.get(chunk_id) if chunk_id else None

            if evidence_text:
                evidence_hash = stable_text_hash(evidence_text)
                _, disp_status, _ = rights_gate.check_document(doc_id) if doc_id else (None, None, None)
                if disp_status == DisplayQuotationStatus.DISPLAY_ALLOWED:
                    evidence_excerpt = evidence_text[:EVIDENCE_EXCERPT_MAX_CHARS]

            veto_flags = prop.veto_trigger.split(",") if prop.veto_trigger else []

            record = ForensicPropositionRecord(
                request_id=request_id,
                proposition_id=prop.prop_id,
                source_field=prop.source_field,
                classification=prop.classification,
                category=getattr(prop, "category", "FACTUAL_CLAIM"),
                proposition_text=prop.text if self.store_full_text else None,
                proposition_text_hash=stable_text_hash(prop.text),
                evidence_document_id=doc_id,
                evidence_chunk_id=chunk_id,
                evidence_excerpt=evidence_excerpt,
                evidence_text_hash=evidence_hash,
                verifier_state=prop.verifier_state,
                verifier_confidence=prop.verifier_confidence,
                veto_flags=veto_flags,
                is_supported=prop.is_supported,
                requested_provider=requested_provider,
                requested_model=requested_model,
                actual_generation_provider=actual_generation_provider,
                actual_generation_model=actual_generation_model,
                provider_failover_applied=provider_failover_applied,
                support_status=support_status,
                reached_learner=reached_learner and prop.is_supported,
            )
            self._records.append(record)
            new_records.append(record)

            logger.info(
                f"ForensicAudit: req={request_id} prop={record.proposition_id} "
                f"state={record.verifier_state} veto={record.veto_flags} "
                f"reached_learner={record.reached_learner} "
                f"requested_model={record.requested_model} actual_model={record.actual_generation_model} "
                f"failover={record.provider_failover_applied} "
                f"evidence_doc={record.evidence_document_id} evidence_chunk={record.evidence_chunk_id}"
            )

        return new_records

    def get_records(self) -> list[ForensicPropositionRecord]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()
