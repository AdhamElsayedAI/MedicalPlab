"""V6 Clinical Evidence Validation Oracle.

Coordinates the 8 fail-closed gates:
1. Real Canonical Source Identity Gate
2. Guideline Currency Gate
3. Verified Source Representation Gate
4. Exact Span Verification Gate
5. Content Coverage Accounting Gate
6. Specificity Monotonicity & Numeric Exactness Gate
7. Distractor Integrity & Contamination Gate
8. Strict Governance & Risk Gate
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from medicalplab.plab.v6.adversarial_review_engine import (
    AdversarialReviewResult,
    V6AdversarialReviewEngine,
)
from medicalplab.plab.v6.canonical_source_resolver import (
    ExternalVerificationReceipt,
    SourceVerificationStatus,
    V6CanonicalSourceResolver,
)
from medicalplab.plab.v6.claim_contract import AtomicClaimV6, ClaimCategory
from medicalplab.plab.v6.distractor_integrity_engine import (
    DistractorIntegrityReport,
    V6DistractorIntegrityEngine,
)
from medicalplab.plab.v6.guideline_currency_engine import (
    CurrencyEvaluationResult,
    GuidelineCurrency,
    V6GuidelineCurrencyEngine,
)
from medicalplab.plab.v6.numeric_specificity_engine import (
    ClaimSupportStatus,
    ClinicalEntitySpec,
    EntityGateStatus,
    V6NumericSpecificityEngine,
)
from medicalplab.plab.v6.question_coverage_engine import (
    QuestionCoverageReport,
    V6QuestionCoverageEngine,
)
from medicalplab.plab.v6.source_representation_manager import (
    V6SourceRepresentationManager,
)
from medicalplab.plab.v6.source_rights_engine import (
    SourceRightsRecord,
    V6SourceRightsEngine,
)
from medicalplab.plab.v6.span_verifier import SpanVerificationStatus, V6SpanVerifier


class QuestionTrustState(str, Enum):
    CLINICIAN_REVIEW_REQUIRED = "CLINICIAN_REVIEW_REQUIRED"
    QUARANTINED = "QUARANTINED"
    DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"


@dataclass
class QuestionValidationResult:
    question_id: str
    source_grounded: bool
    clinician_review_ready: bool
    trust_state: QuestionTrustState
    action_recommendation: str
    decisive_claims_total: int
    decisive_claims_passed: int
    blocking_reasons: List[str] = field(default_factory=list)
    all_claims: List[AtomicClaimV6] = field(default_factory=list)
    coverage_report: Optional[QuestionCoverageReport] = None
    distractor_report: Optional[DistractorIntegrityReport] = None
    adversarial_report: Optional[AdversarialReviewResult] = None
    source_receipts: Dict[str, ExternalVerificationReceipt] = field(default_factory=dict)
    currency_results: Dict[str, CurrencyEvaluationResult] = field(default_factory=dict)
    rights_records: Dict[str, SourceRightsRecord] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "source_grounded": self.source_grounded,
            "clinician_review_ready": self.clinician_review_ready,
            "trust_state": self.trust_state.value,
            "action_recommendation": self.action_recommendation,
            "decisive_claims_total": self.decisive_claims_total,
            "decisive_claims_passed": self.decisive_claims_passed,
            "blocking_reasons": self.blocking_reasons,
            "claims": [c.to_dict() for c in self.all_claims],
            "coverage": self.coverage_report.to_dict() if self.coverage_report else None,
            "distractor_review": self.distractor_report.to_dict() if self.distractor_report else None,
            "adversarial_review": self.adversarial_report.to_dict() if self.adversarial_report else None,
            "source_receipts": {k: v.to_dict() for k, v in self.source_receipts.items()},
            "currency_results": {k: v.to_dict() for k, v in self.currency_results.items()},
            "rights_records": {k: v.to_dict() for k, v in self.rights_records.items()},
        }


class V6ValidationOracle:
    """Production Clinical Validation Oracle for PLAB Evidence Truth."""

    def __init__(
        self,
        resolver: V6CanonicalSourceResolver,
        rep_manager: V6SourceRepresentationManager,
    ):
        self.resolver = resolver
        self.rep_manager = rep_manager

    def evaluate_question(
        self,
        question_spec: Dict[str, Any],
        claims: List[AtomicClaimV6],
        custom_distractor_reviews: Optional[List[Dict[str, Any]]] = None,
    ) -> QuestionValidationResult:
        qid = question_spec["question_id"]
        stem = question_spec.get("stem", "")
        choices = question_spec.get("choices", [])
        correct_answer = question_spec.get("correct_answer", "")
        explanation = question_spec.get("explanation", "")
        citations = question_spec.get("citations", [])
        custom_distractor_reviews = custom_distractor_reviews or question_spec.get("distractor_reviews", [])

        source_receipts: Dict[str, ExternalVerificationReceipt] = {}
        source_rights: Dict[str, SourceRightsRecord] = {}
        currency_results: Dict[str, CurrencyEvaluationResult] = {}
        blocking_reasons: List[str] = []

        # Find keyed answer text
        keyed_answer_text = ""
        for ch in choices:
            if ch.get("id") == correct_answer:
                keyed_answer_text = ch.get("text", "")
                break

        # ---------------------------------------------------------------------
        # 1. Audit all cited sources (Identity, Rights, Currency, Representation)
        # ---------------------------------------------------------------------
        # Collect all sources referenced either in citations or in claims
        cited_sources: Dict[str, Dict[str, Any]] = {}
        for cit in citations:
            sid = cit.get("source_id") or cit.get("document_id") or ""
            if sid:
                cited_sources[sid] = cit

        for clm in claims:
            if clm.source_id and clm.source_id not in cited_sources:
                cited_sources[clm.source_id] = {"source_id": clm.source_id}

        for sid, cit in cited_sources.items():
            pmcid = cit.get("pmcid") or cit.get("canonical_identifier") or sid
            url = cit.get("canonical_url", "")
            title = cit.get("title", "")
            org = cit.get("organization", "")

            # Gate 1: Source Identity (check cache first)
            cached_receipt = self.resolver._cached_receipts.get(sid) or self.resolver._cached_receipts.get(pmcid)
            if cached_receipt:
                receipt = cached_receipt
            elif "PMC" in sid.upper() or (isinstance(pmcid, str) and "PMC" in pmcid.upper()):
                receipt = self.resolver.resolve_ncbi_pmc(sid, pmcid, declared_title=title)
            else:
                receipt = self.resolver.resolve_official_guideline(
                    source_id=sid,
                    canonical_identifier=pmcid,
                    canonical_url=url,
                    declared_title=title,
                    organization=org,
                )
            source_receipts[sid] = receipt
            if receipt.identity_verification_status != SourceVerificationStatus.IDENTITY_VERIFIED:
                blocking_reasons.append(f"Source identity failed for '{sid}': {receipt.explanation}")

            # Rights
            rights = V6SourceRightsEngine.evaluate_rights(sid, receipt.source_type, receipt.canonical_organization)
            source_rights[sid] = rights

            # Gate 2: Currency
            curr = V6GuidelineCurrencyEngine.evaluate_currency(sid)
            currency_results[sid] = curr
            if not curr.policy_passes:
                blocking_reasons.append(f"Guideline currency policy failed for '{sid}': {curr.explanation}")

            # Gate 3: Representation on disk
            rep_ok, rep_msg = self.rep_manager.verify_representation_exists(sid)
            if not rep_ok:
                blocking_reasons.append(rep_msg)

        # ---------------------------------------------------------------------
        # 2. Gate 4 & 5 & 6: Audit Each Atomic Claim
        # ---------------------------------------------------------------------
        decisive_total = 0
        decisive_passed = 0

        for clm in claims:
            sid = clm.source_id
            receipt = source_receipts.get(sid)
            curr = currency_results.get(sid)
            claim_reasons: List[str] = []

            # 1. Source Identity
            if not receipt or receipt.identity_verification_status != SourceVerificationStatus.IDENTITY_VERIFIED:
                clm.source_identity_pass = False
                claim_reasons.append("SOURCE_NOT_RESOLVED")
            else:
                clm.source_identity_pass = True

            # 2. Currency
            if not curr or not curr.policy_passes:
                clm.source_currency_pass = False
                claim_reasons.append(curr.reason if curr else "CURRENCY_CHECK_FAILED")
            else:
                clm.source_currency_pass = True

            # 3. Representation on disk
            rep = self.rep_manager.get_representation(sid)
            if not rep:
                clm.source_representation_pass = False
                claim_reasons.append("MISSING_SOURCE_REPRESENTATION")
            else:
                clm.source_representation_pass = True

            # 4. Exact Span Verification
            if rep:
                span_res = V6SpanVerifier.verify_span(clm.evidence_quote, sid, self.rep_manager)
                clm.span_verification_pass = span_res.is_verified
                if not span_res.is_verified:
                    claim_reasons.append("QUOTE_NOT_IN_VERIFIED_REPRESENTATION")
            else:
                clm.span_verification_pass = False
                claim_reasons.append("NO_VERIFIED_SOURCE_REPRESENTATION")

            # 5. Specificity Monotonicity & Numeric Gate
            entity_spec = clm.entity_spec or V6NumericSpecificityEngine.extract_entities_from_text(clm.claim_text)
            clm.entity_spec = entity_spec

            comp_res = V6NumericSpecificityEngine.compare_entities(
                claim_spec=entity_spec,
                evidence_text=clm.evidence_quote,
                answer_text=keyed_answer_text if clm.claim_location in ("CORRECT_OPTION", "KEYED_ANSWER") else None,
                claim_text=clm.claim_text,
            )
            clm.numeric_entity_pass = comp_res.passes
            if not comp_res.passes:
                claim_reasons.extend(comp_res.reasons)

            # Support status determination
            all_gates_pass = (
                clm.source_identity_pass
                and clm.source_currency_pass
                and clm.source_representation_pass
                and clm.span_verification_pass
                and clm.numeric_entity_pass
            )
            clm.specificity_pass = clm.numeric_entity_pass

            if all_gates_pass:
                clm.claim_support_status = ClaimSupportStatus.DIRECT_SUPPORT
                clm.final_claim_pass = True
                clm.reasons = []
                clm.explanation = "DIRECT_SUPPORT: Exact span verified in authoritative canonical source."
            else:
                clm.claim_support_status = ClaimSupportStatus.UNSUPPORTED
                clm.final_claim_pass = False
                clm.reasons = claim_reasons
                clm.explanation = f"EVIDENCE_INSUFFICIENT: {', '.join(claim_reasons)}"

            if clm.is_decisive:
                decisive_total += 1
                if clm.final_claim_pass:
                    decisive_passed += 1
                else:
                    blocking_reasons.append(f"Decisive claim '{clm.claim_id}' failed: {', '.join(claim_reasons)}")

        # ---------------------------------------------------------------------
        # 3. Gate 5: Content Coverage Accounting Gate
        # ---------------------------------------------------------------------
        coverage_report = V6QuestionCoverageEngine.audit_coverage(
            question_id=qid,
            stem=stem,
            keyed_answer_id=correct_answer,
            options=choices,
            explanation=explanation,
            claims=claims,
        )
        if not coverage_report.coverage_passed:
            blocking_reasons.extend(coverage_report.under_decomposition_failures)

        # ---------------------------------------------------------------------
        # 4. Gate 7: Distractor Integrity & Contamination Gate
        # ---------------------------------------------------------------------
        distractor_report = None
        if custom_distractor_reviews:
            distractor_report = V6DistractorIntegrityEngine.audit_distractors(
                question_id=qid,
                question_version="v6",
                stem=stem,
                options=choices,
                correct_answer_id=correct_answer,
                distractor_reviews=custom_distractor_reviews,
            )
            if not distractor_report.integrity_passed:
                if distractor_report.multiple_defensible_options:
                    blocking_reasons.append(
                        f"Multiple clinically defensible options detected: {distractor_report.defensible_options}"
                    )
                if distractor_report.contamination_flags:
                    blocking_reasons.extend(distractor_report.contamination_flags)
                if distractor_report.boilerplate_flags:
                    blocking_reasons.extend(distractor_report.boilerplate_flags)

        # Adversarial Review
        adversarial_report = None
        if custom_distractor_reviews:
            adversarial_report = V6AdversarialReviewEngine.review_one_best_answer(
                question_id=qid,
                keyed_answer_id=correct_answer,
                options=choices,
                option_reviews=custom_distractor_reviews,
            )
            if adversarial_report.multiple_defensible_options:
                blocking_reasons.append(adversarial_report.explanation)

        # ---------------------------------------------------------------------
        # 5. Final Derivation of Question Readiness
        # ---------------------------------------------------------------------
        # Decisive claims must exist and all must pass
        has_supported_decisive = (decisive_total > 0) and (decisive_passed == decisive_total)
        no_blocking_reasons = (len(blocking_reasons) == 0)
        coverage_clean = coverage_report.coverage_passed

        source_grounded = has_supported_decisive and no_blocking_reasons and coverage_clean
        clinician_review_ready = source_grounded

        if clinician_review_ready:
            trust_state = QuestionTrustState.CLINICIAN_REVIEW_REQUIRED
            action_rec = "SUBMIT_FOR_CLINICIAN_REVIEW"
        else:
            trust_state = QuestionTrustState.QUARANTINED
            action_rec = "QUARANTINE"

        return QuestionValidationResult(
            question_id=qid,
            source_grounded=source_grounded,
            clinician_review_ready=clinician_review_ready,
            trust_state=trust_state,
            action_recommendation=action_rec,
            decisive_claims_total=decisive_total,
            decisive_claims_passed=decisive_passed,
            blocking_reasons=blocking_reasons,
            all_claims=claims,
            coverage_report=coverage_report,
            distractor_report=distractor_report,
            adversarial_report=adversarial_report,
            source_receipts=source_receipts,
            currency_results=currency_results,
            rights_records=source_rights,
        )
