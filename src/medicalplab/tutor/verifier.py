"""Post-generation claim verification, provenance enforcement, and deterministic safety vetoes."""
from __future__ import annotations

import re
from typing import Any, Sequence
from medicalplab.evidence_engine.claim_verifier import CentralClaimVerifier
from medicalplab.evidence_engine.models import RetrievedCandidate, VerificationState
from medicalplab.stage_b.evidence_policy import normalize
from medicalplab.stage_d.validator import (
    CURE_PATTERNS,
    DOSE_PATTERNS,
    PRESCRIPTION_PATTERNS,
    DIAGNOSIS_PATTERNS,
)
from medicalplab.tutor.models import (
    ExtractedProposition,
    TutorVerificationSummaryDTO,
)


class TutorPostVerifier:
    """Verifies all generated tutor fields against evidence, provenance, and clinical safety."""

    def __init__(self, claim_verifier: CentralClaimVerifier | None = None) -> None:
        self.claim_verifier = claim_verifier or CentralClaimVerifier()
        self._cure_res = [re.compile(p, re.IGNORECASE) for p in CURE_PATTERNS]
        self._dose_res = [re.compile(p, re.IGNORECASE) for p in DOSE_PATTERNS]
        self._presc_res = [re.compile(p, re.IGNORECASE) for p in PRESCRIPTION_PATTERNS]
        self._diag_res = [re.compile(p, re.IGNORECASE) for p in DIAGNOSIS_PATTERNS]

    def validate_provenance(
        self,
        citations: Sequence[dict[str, Any]],
        candidates: Sequence[RetrievedCandidate],
    ) -> tuple[bool, str | None]:
        """Validate citation existence and verbatim quote matching in evidence."""
        if not citations:
            return False, "NO_CITATIONS_PROVIDED"

        doc_cand_map = {c.document_id: c for c in candidates}
        chunk_cand_map = {c.chunk_id: c for c in candidates}

        for idx, cit in enumerate(citations, 1):
            quote = cit.get("quote", "").strip()
            if not quote:
                return False, f"CITATION_{idx}_EMPTY_QUOTE"

            doc_id = cit.get("document_id")
            chunk_id = cit.get("chunk_id")

            target_cand = None
            if chunk_id and chunk_id in chunk_cand_map:
                target_cand = chunk_cand_map[chunk_id]
            elif doc_id and doc_id in doc_cand_map:
                target_cand = doc_cand_map[doc_id]
            elif candidates:
                target_cand = candidates[0]

            if not target_cand:
                return False, f"CITATION_{idx}_TARGET_CANDIDATE_NOT_FOUND"

            norm_quote = normalize(quote)
            norm_cand = normalize(target_cand.text)

            # Require verbatim normalized substring matching
            if norm_quote not in norm_cand:
                # Also check all candidates in packet
                found_in_any = any(norm_quote in normalize(c.text) for c in candidates)
                if not found_in_any:
                    return False, f"CITATION_{idx}_QUOTE_NOT_FOUND_IN_EVIDENCE"

        return True, None

    def check_clinical_safety(self, generated_dict: dict[str, Any]) -> list[str]:
        """Check for unauthorized clinical assertions (cures, doses, prescriptions, diagnoses)."""
        veto_flags: list[str] = []

        all_text_parts: list[str] = []
        for key in ["message", "socratic_question", "hints", "misconception", "mechanistic_explanation", "revision_summary"]:
            val = generated_dict.get(key)
            if isinstance(val, str):
                all_text_parts.append(val)
            elif isinstance(val, list):
                for v in val:
                    if isinstance(v, str):
                        all_text_parts.append(v)

        combined = " ".join(all_text_parts)
        norm_text = normalize(combined)

        for pat in self._cure_res:
            if pat.search(norm_text):
                veto_flags.append("UNSUPPORTED_CURE_CLAIM")
                break

        for pat in self._dose_res:
            if pat.search(norm_text):
                veto_flags.append("UNAUTHORIZED_DRUG_DOSE")
                break

        for pat in self._presc_res:
            if pat.search(norm_text):
                veto_flags.append("UNAUTHORIZED_PRESCRIPTION_RECOMMENDATION")
                break

        for pat in self._diag_res:
            if pat.search(norm_text):
                veto_flags.append("UNAUTHORIZED_DEFINITIVE_DIAGNOSIS")
                break

        return veto_flags

    def verify_propositions(
        self,
        propositions: Sequence[ExtractedProposition],
        candidates: Sequence[RetrievedCandidate],
    ) -> tuple[TutorVerificationSummaryDTO, bool]:
        """Verify each substantive proposition against evidence passages."""
        summary = TutorVerificationSummaryDTO(
            total_propositions=len(propositions),
            supported_propositions=0,
            unsupported_propositions=0,
            non_factual_statements=0,
            veto_flags=[],
        )

        all_supported = True
        eval_candidates = candidates[:5] if candidates else []

        for prop in propositions:
            if prop.classification == "NON_FACTUAL_PEDAGOGICAL_LANGUAGE":
                summary.non_factual_statements += 1
                prop.is_supported = True
                continue

            # Verify substantive claim against candidates individually
            supported = False
            last_res = None
            last_chunk_id = None
            last_doc_id = None
            for cand in eval_candidates:
                cand_text = cand.text if hasattr(cand, "text") else cand.get("text", "")
                cand_chunk_id = cand.chunk_id if hasattr(cand, "chunk_id") else cand.get("chunk_id")
                cand_doc_id = cand.document_id if hasattr(cand, "document_id") else cand.get("document_id")
                res = self.claim_verifier.verify_claim(
                    claim_id=prop.prop_id,
                    claim_text=prop.text,
                    evidence_text=cand_text,
                    cited_chunk_id=cand_chunk_id,
                    cited_document_id=cand_doc_id,
                )
                last_res = res
                last_chunk_id = cand_chunk_id
                last_doc_id = cand_doc_id
                if res.state == VerificationState.SUPPORTED and not res.veto_flags:
                    supported = True
                    prop.is_supported = True
                    summary.supported_propositions += 1
                    break

            # Forensic metadata capture (additive only - does not affect the decision above):
            # records which evidence candidate was actually evaluated and the raw verifier
            # result, so a later audit can distinguish model/verifier/evidence-binding/retrieval
            # failure modes without needing another live provider call.
            if last_res is not None:
                prop.verified_document_id = last_doc_id
                prop.verified_chunk_id = last_chunk_id
                prop.verifier_state = last_res.state.value
                prop.verifier_confidence = last_res.confidence

            if not supported:
                prop.is_supported = False
                summary.unsupported_propositions += 1
                all_supported = False
                if last_res:
                    prop.verification_reason = f"State: {last_res.state.value} (Confidence: {last_res.confidence})"
                    if last_res.veto_flags:
                        prop.veto_trigger = ",".join(last_res.veto_flags)
                        summary.veto_flags.extend(last_res.veto_flags)

        return summary, all_supported
