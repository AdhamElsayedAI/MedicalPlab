"""
MedicalPlab Shared Evidence Engine V2 — Service Orchestration
============================================================
Coordinates the end-to-end evidence lifecycle:
1. Query Representation (original, canonical, neutral target).
2. Deterministic Document Routing (16 extractive document cards).
3. 4-Route Candidate Retrieval (Global dense, Doc-local, Section-local, BM25F) + RRF.
4. Structured Medical Cross-Encoder Reranking (Qwen3-Reranker-0.6B).
5. Central Claim-Evidence Verification & Veto Checks (CentralClaimVerifier).
6. EvidencePacket compilation for Course Learning, PLAB, Tutor, and Clinical Reasoning.
"""

import logging
from pathlib import Path
from typing import Any, Sequence

from medicalplab.evidence_engine.candidate_retriever import CandidateRetriever
from medicalplab.evidence_engine.claim_verifier import CentralClaimVerifier
from medicalplab.evidence_engine.document_router import DeterministicDocumentRouter
from medicalplab.evidence_engine.models import (
    ClaimVerificationResult,
    EvidencePacket,
    QueryRepresentation,
    RetrievedCandidate,
    VerificationState,
)
from medicalplab.evidence_engine.query_representation import ClinicalQueryProcessor
from medicalplab.evidence_engine.reranker import EvidenceReranker

logger = logging.getLogger(__name__)

ARCHITECTURE_ID = "MEDICALPLAB_EVIDENCE_ENGINE_V1_1"
MIN_RERANK_SUPPORT_SCORE = 7.0
MIN_RETRIEVAL_CHANNEL_AGREEMENT = 2


class SharedEvidenceEngineV2:
    """Shared Evidence Engine V2 for MedicalPlab.
    
    Orchestrates routing, retrieval, reranking, and verification across specialties.
    """

    def __init__(
        self,
        data_root: Path | str | None = None,
        embedder: Any = None,
        reranker: Any = None,
        router: DeterministicDocumentRouter | None = None,
        claim_verifier: CentralClaimVerifier | None = None,
    ):
        self.data_root = Path(data_root) if data_root else Path("Data")
        self.query_processor = ClinicalQueryProcessor()
        self.router = router or DeterministicDocumentRouter(data_root=self.data_root)
        self.router.build_or_load_cards()

        self.retriever = CandidateRetriever(
            data_root=self.data_root,
            embedder=embedder,
            router=self.router,
        )
        self.reranker = reranker if isinstance(reranker, EvidenceReranker) else EvidenceReranker(model=reranker)
        self.verifier = claim_verifier or CentralClaimVerifier(reranker=self.reranker.model if hasattr(self.reranker, "model") else None)

    def process_and_retrieve(
        self,
        query: str | QueryRepresentation,
        mode: str = "TUTOR",
        top_candidates: int = 50,
        rerank_top_k: int = 25,
    ) -> tuple[QueryRepresentation, list[str], list[RetrievedCandidate]]:
        """Run Stages 2, 3, 4, and 8 to retrieve and rerank candidate passages."""
        if isinstance(query, str):
            q_rep = self.query_processor.process_query(query)
        else:
            q_rep = query

        # Document routing
        routed_doc_ids = self.router.route_documents(q_rep.canonical_query, top_k=8)

        # 4-route candidate retrieval
        cands = self.retriever.retrieve_candidates(q_rep, top_k=top_candidates)

        # Cross-encoder reranking
        if self.reranker.model is not None or hasattr(self.reranker, "load_model"):
            try:
                ranked = self.reranker.rerank(q_rep, cands[:rerank_top_k], top_k=rerank_top_k)
                # Combine reranked with remaining un-reranked candidates
                cands = ranked + cands[rerank_top_k:]
            except Exception as exc:
                logger.warning(f"Reranking fell back to fused scores: {exc}")

        return q_rep, routed_doc_ids, cands

    def verify_claims_against_evidence(
        self,
        claims: Sequence[str | dict[str, Any]],
        evidence_candidate: RetrievedCandidate,
    ) -> list[ClaimVerificationResult]:
        """Verify candidate claims against a single retrieved evidence candidate."""
        results = []
        for idx, claim_item in enumerate(claims, 1):
            if isinstance(claim_item, dict):
                cid = claim_item.get("claim_id", f"CLAIM-{idx:03d}")
                ctext = claim_item.get("text", claim_item.get("claim_text", ""))
                auth = claim_item.get("authority", None)
            else:
                cid = f"CLAIM-{idx:03d}"
                ctext = str(claim_item)
                auth = None

            sec_str = " > ".join(evidence_candidate.section_path) if evidence_candidate.section_path else evidence_candidate.heading
            res = self.verifier.verify_claim(
                claim_id=cid,
                claim_text=ctext,
                evidence_text=evidence_candidate.text,
                cited_chunk_id=evidence_candidate.chunk_id,
                cited_document_id=evidence_candidate.document_id,
                cited_section=sec_str,
                authority=auth,
            )
            results.append(res)
        return results

    def query(
        self,
        query: str,
        claims_to_verify: Sequence[str | dict[str, Any]] | None = None,
        mode: str = "TUTOR",
        top_candidates: int = 50,
        rerank_top_k: int = 25,
    ) -> EvidencePacket:
        """Complete end-to-end evidence packet generation under canonical mode policy."""
        q_rep, routed_doc_ids, candidates = self.process_and_retrieve(
            query=query,
            mode=mode,
            top_candidates=top_candidates,
            rerank_top_k=rerank_top_k,
        )

        top_passage = candidates[0] if candidates else None

        # Verify explicit claims if provided.
        claim_results = []
        if claims_to_verify and top_passage:
            claim_results = self.verify_claims_against_evidence(claims_to_verify, top_passage)

        # Safety & Abstention Gate
        abstain = False
        abstain_reason = None
        is_degraded = getattr(self.reranker, "is_degraded", False)

        if not candidates:
            abstain = True
            abstain_reason = "NO_CANDIDATES_RETRIEVED"
        elif top_passage is not None:
            # Source eligibility is independent of retrieval relevance.
            source_eligible = (
                top_passage.document_id in self.router.cards
                and top_passage.chunk_id in self.retriever.chunks
                and self.retriever.chunks[top_passage.chunk_id].get("document_id") == top_passage.document_id
            )
            if not source_eligible:
                abstain = True
                abstain_reason = "INELIGIBLE_EVIDENCE_SOURCE"

            # DEV-only calibration requires a high direct-support score and
            # agreement from at least two distinct candidate channels.
            channel_agreement = len(top_passage.channel_ranks)
            if not abstain and not is_degraded:
                if (
                    top_passage.rerank_score < MIN_RERANK_SUPPORT_SCORE
                    or channel_agreement < MIN_RETRIEVAL_CHANNEL_AGREEMENT
                ):
                    abstain = True
                    abstain_reason = "LOW_RETRIEVAL_CONFIDENCE"
            elif not abstain and (
                top_passage.fused_score < 0.01
                or channel_agreement < MIN_RETRIEVAL_CHANNEL_AGREEMENT
            ):
                abstain = True
                abstain_reason = "LOW_RETRIEVAL_CONFIDENCE"

            # The reranker is explicitly prompted for direct proposition
            # support, not topical relevance. In degraded mode that claim-level
            # signal is unavailable, so query-only serving fails closed.
            if not claim_results and is_degraded:
                abstain = True
                abstain_reason = "CLAIM_SUPPORT_UNAVAILABLE"

            # Explicit answer claims require complete verifier support. Partial
            # or ambiguous support is never sufficient for product serving.
            for result in claim_results:
                if result.state == VerificationState.CONTRADICTED:
                    abstain = True
                    abstain_reason = "CLAIM_CONTRADICTED_BY_EVIDENCE"
                    break
                if result.state != VerificationState.SUPPORTED:
                    abstain = True
                    abstain_reason = (
                        "HIGH_RISK_CLAIM_UNSUPPORTED"
                        if result.is_high_risk
                        else "CLAIM_NOT_DIRECTLY_SUPPORTED"
                    )
                    break

        # Apply mode policy constraints
        if mode == "PLAB":
            # PLAB strict boundary: never bypass clinician review or claim sufficiency
            if top_passage and top_passage.fused_score < 0.01 and not claim_results:
                abstain = True
                abstain_reason = "PLAB_EVIDENCE_INSUFFICIENT"
        elif mode == "UNI":
            # Educational mode: educational explanation policy
            pass

        return EvidencePacket(
            query=q_rep,
            routed_document_ids=routed_doc_ids,
            candidates=candidates,
            top_passage=top_passage,
            claim_verifications=claim_results,
            abstain=abstain,
            abstain_reason=abstain_reason,
            retrieval_mode=mode,
            is_degraded=is_degraded,
        )


# Canonical alias for MedicalPlab Evidence Engine V1.1
CanonicalEvidenceEngine = SharedEvidenceEngineV2
