"""
MedicalPlab Shared Evidence Engine V2 — Service Orchestration
============================================================
Coordinates the end-to-end evidence lifecycle:
1. Query Representation (original, canonical, neutral target).
2. Deterministic Document Routing (23 extractive document cards).
3. 4-Route Candidate Retrieval (Global dense, Doc-local, Section-local, BM25) + RRF.
4. Structured Medical Cross-Encoder Reranking (Qwen3-Reranker-4B NF4).
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
        top_candidates: int = 50,
        rerank_top_k: int = 25,
    ) -> EvidencePacket:
        """Complete end-to-end evidence packet generation."""
        q_rep, routed_doc_ids, candidates = self.process_and_retrieve(
            query=query,
            top_candidates=top_candidates,
            rerank_top_k=rerank_top_k,
        )

        top_passage = candidates[0] if candidates else None

        # Verify claims if provided
        claim_results = []
        if claims_to_verify and top_passage:
            claim_results = self.verify_claims_against_evidence(claims_to_verify, top_passage)

        # Safety / Abstention Gate
        abstain = False
        abstain_reason = None
        if not candidates:
            abstain = True
            abstain_reason = "NO_CANDIDATES_RETRIEVED"
        elif top_passage and top_passage.rerank_score < -15.0 and top_passage.fused_score < 0.01:
            abstain = True
            abstain_reason = "CONFIDENCE_BELOW_RELIABILITY_THRESHOLD"

        return EvidencePacket(
            query=q_rep,
            routed_document_ids=routed_doc_ids,
            candidates=candidates,
            top_passage=top_passage,
            claim_verifications=claim_results,
            abstain=abstain,
            abstain_reason=abstain_reason,
        )
