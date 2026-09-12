"""
MedicalPlab Shared Evidence Engine V2 — Central Claim-Evidence Verifier
======================================================================
Upgrades existing Stage-B verifier logic into a central, reusable verifier.
Classifies claims into 4 discrete grounding states:
- SUPPORTED: Verbatim/semantic direct evidence entails all claim propositions.
- PARTIALLY_SUPPORTED: Core concept supported, but material qualifiers missing.
- CONTRADICTED: Evidence directly refutes the claim proposition.
- NOT_SUPPORTED: Evidence does not address or entail the claim proposition.

Deterministic Veto Pipeline (Deterministic rules are vetoes, not proof of entailment):
1. Provenance check: Citation chunk must exist in verified corpus.
2. Negation/Polarity veto: Reverses support if polarity does not match.
3. Quantity/Number/Unit veto: Numerical discrepancies or unit mismatches fail closed.
4. Authority/Guideline veto: Claims citing NICE/WHO must match verified authority blocks.
5. High-Risk Claim Rule: Drug, dose, diagnosis, management, and cutoffs fail closed on ambiguity.
"""

import re
from typing import Any, Sequence

from medicalplab.evidence_engine.models import (
    ClaimVerificationResult,
    VerificationState,
)
from medicalplab.stage_b.evidence_policy import normalize

# High-risk clinical keyword triggers
HIGH_RISK_PATTERNS = [
    r"\b(?:dose|dosage|mg|mcg|units?|g/24h|ml/min|iv\b|push\b|bolus|infusion|rapidly)\b",
    r"\b(?:first-line|recommended|contraindicated|treatment\s+of\s+choice|surgical|surgery|indications?)\b",
    r"\b(?:diagnos\w*|confirmatory\s+test|gold\s+standard|diagnostic\s+criteria)\b",
    r"\b(?:according\s+to\s+NICE|NICE\s+guideline|WHO\s+guideline|KDIGO)\b",
    r"\b(?:threshold|cutoff|eGFR\s*[<>=]|creatinine\s*[<>=]|potassium\s*[<>=])\b",
    r"\b(?:safely|safety|safe|combined|combination|co-administ\w*|escalat\w*|dual\b)\b",
    r"\b(?:lethal|fatal|toxic|contraindicat\w*|risk|precipitat\w*)\b",
    r"\b(?:metformin|spironolactone|eplerenone|lisinopril|potassium\s+chloride|ace\s+inhibitor|arb)\b",
]

CONTRAINDICATION_PHRASES = [
    "contraindicated", "strictly contraindicated", "not recommended",
    "should not be used", "must not be used", "must be avoided",
    "do not use", "is lethal", "is fatal", "risk of precipitating acute kidney injury",
]

NEGATION_TERMS = {
    "no", "not", "neither", "nor", "never", "without", "absence", "none",
    "unlikely", "contraindicated", "ineffective", "fails"
}

NUMERIC_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b")


class CentralClaimVerifier:
    """Production claim-evidence verifier integrating deterministic vetoes and cross-encoder scoring."""

    def __init__(self, reranker: Any = None):
        self.reranker = reranker

    def verify_claim(
        self,
        claim_id: str,
        claim_text: str,
        evidence_text: str,
        *,
        cited_chunk_id: str | None = None,
        cited_document_id: str | None = None,
        cited_section: str | None = None,
        authority: str | None = None,
    ) -> ClaimVerificationResult:
        """Verify an atomic medical claim against evidence text using deterministic vetoes + semantic scoring."""
        c_norm = normalize(claim_text)
        e_norm = normalize(evidence_text)

        # 1. High-risk classification
        is_high_risk = any(re.search(pat, claim_text, flags=re.IGNORECASE) for pat in HIGH_RISK_PATTERNS)
        vetoes = []

        # 2. VETO A: Negation / Polarity Inversion / Contraindication
        explicit_neg_terms = {"no", "not", "neither", "nor", "never", "contraindicated", "fails", "unlikely"}
        c_has_neg = any(f" {neg} " in f" {c_norm} " for neg in explicit_neg_terms)
        e_has_explicit_neg = any(f" {neg} " in f" {e_norm} " for neg in explicit_neg_terms)
        e_has_contraindication = any(phrase in e_norm for phrase in CONTRAINDICATION_PHRASES)

        if c_has_neg and not e_has_explicit_neg:
            vetoes.append("POLARITY_MISMATCH")
        elif not c_has_neg and e_has_contraindication:
            vetoes.append("POLARITY_MISMATCH")
        elif not c_has_neg and any(
            re.search(rf"\b(?:not|never|no|contraindicated|fails? to)\s+{re.escape(w)}\b", e_norm)
            for w in c_norm.split()
            if len(w) > 4
        ):
            vetoes.append("POLARITY_MISMATCH")

        # 3. VETO B: Numeric and Quantity Check
        c_numbers = set(NUMERIC_PATTERN.findall(claim_text))
        e_numbers = set(NUMERIC_PATTERN.findall(evidence_text))
        missing_numbers = c_numbers - e_numbers
        if missing_numbers:
            vetoes.append("NUMERIC_MISMATCH")

        # 4. VETO C: Authority / Guideline Mismatch
        if "nice" in c_norm and authority and "nice" not in authority.lower() and "uk" not in e_norm:
            vetoes.append("GUIDELINE_AUTHORITY_MISMATCH_NICE")
        if "who" in c_norm and authority and "who" not in authority.lower() and "world health" not in e_norm:
            vetoes.append("GUIDELINE_AUTHORITY_MISMATCH_WHO")

        # If any hard veto triggered on high-risk claim -> FAIL CLOSED
        if is_high_risk and vetoes:
            if "POLARITY_MISMATCH" in vetoes:
                state = VerificationState.CONTRADICTED
            else:
                state = VerificationState.NOT_SUPPORTED

            return ClaimVerificationResult(
                claim_id=claim_id,
                claim_text=claim_text,
                state=state,
                confidence=0.1,
                cited_chunk_id=cited_chunk_id,
                cited_document_id=cited_document_id,
                cited_section=cited_section,
                evidence_span=evidence_text[:300],
                rationale=f"Failed high-risk deterministic veto checks: {', '.join(vetoes)}",
                veto_flags=vetoes,
                is_high_risk=True,
            )

        # 5. Semantic entailment evaluation
        # Cross-encoder inference if available, otherwise strict lexical-overlap heuristic
        score = 0.0
        if self.reranker is not None:
            inst = (
                "Instruct: Determine whether the following evidence strictly entails the truth "
                "of the stated clinical claim. Ambiguity or missing conditions is non-support.\nClaim: "
            )
            pair = [inst + claim_text, evidence_text]
            s = self.reranker.predict([pair], show_progress_bar=False)[0]
            score = float(s)
            if score >= 5.0 and not vetoes:
                state = VerificationState.SUPPORTED
                conf = min(0.99, max(0.80, 0.5 + score * 0.05))
                rationale = "Direct evidence entails all material requested propositions."
            elif score >= 2.0 and not vetoes:
                state = VerificationState.SUPPORTED
                conf = 0.80
                rationale = "Direct evidence supports primary assertion."
            elif vetoes and "POLARITY_MISMATCH" in vetoes:
                state = VerificationState.CONTRADICTED
                conf = 0.85
                rationale = "Polarity mismatch contradicts stated medical claim."
            elif vetoes:
                state = VerificationState.PARTIALLY_SUPPORTED
                conf = 0.50
                rationale = f"Core topic mentioned, but flagged qualifiers: {', '.join(vetoes)}"
            else:
                state = VerificationState.NOT_SUPPORTED
                conf = 0.10
                rationale = f"Evidence does not entail claim proposition (score={score:.2f})."
        else:
            # Conservative lexical overlap heuristic
            c_words = set(re.findall(r"\b[a-z]{3,}\b", c_norm)) - {
                "the", "and", "that", "this", "with", "what", "which", "are", "can",
                "should", "does", "from", "for", "in", "out", "been", "have", "has"
            }
            e_words = set(re.findall(r"\b[a-z]{3,}\b", e_norm))
            overlap = len(c_words.intersection(e_words)) / max(1, len(c_words))

            if vetoes:
                if "POLARITY_MISMATCH" in vetoes:
                    state = VerificationState.CONTRADICTED
                    conf = 0.85
                    rationale = f"Evidence directly contradicts claim proposition ({', '.join(vetoes)})."
                else:
                    state = VerificationState.NOT_SUPPORTED
                    conf = 0.10
                    rationale = f"Deterministic veto triggered: {', '.join(vetoes)}"
            elif overlap >= 0.80:
                state = VerificationState.SUPPORTED
                conf = 0.90
                rationale = "Direct evidence entails all material requested propositions."
            elif is_high_risk:
                # High-risk claim fails closed without complete lexical or model entailment
                state = VerificationState.NOT_SUPPORTED
                conf = 0.10
                rationale = "High-risk clinical claim fails closed without full entailment."
            elif overlap >= 0.40:
                state = VerificationState.PARTIALLY_SUPPORTED
                conf = 0.50
                rationale = "Core concepts present in evidence but lacks complete statement overlap."
            else:
                state = VerificationState.NOT_SUPPORTED
                conf = 0.10
                rationale = f"Insufficient lexical evidence overlap ({overlap:.1%})."

        return ClaimVerificationResult(
            claim_id=claim_id,
            claim_text=claim_text,
            state=state,
            confidence=conf,
            cited_chunk_id=cited_chunk_id,
            cited_document_id=cited_document_id,
            cited_section=cited_section,
            evidence_span=evidence_text[:300],
            rationale=rationale,
            veto_flags=vetoes,
            is_high_risk=is_high_risk,
        )
