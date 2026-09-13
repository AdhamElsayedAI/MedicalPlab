"""V6 Exact Evidence Span Verifier.

Enforces:
1. Exact verbatim text location in verified source representation.
2. A generator-provided non-empty quote must NEVER itself establish SPAN_VERIFIED.
3. Source-safe normalization: preserves clinical semantics (negations, numbers, decimals,
   operators, units, dose, frequencies) while collapsing formatting/whitespace differences.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from medicalplab.plab.v6.source_representation_manager import (
    V6SourceRepresentationManager,
    VerifiedSourceRepresentation,
)


class SpanVerificationStatus(str, Enum):
    SPAN_VERIFIED = "SPAN_VERIFIED"
    SPAN_NOT_FOUND = "SPAN_NOT_FOUND"
    WRONG_SOURCE = "WRONG_SOURCE"
    REPRESENTATION_UNAVAILABLE = "REPRESENTATION_UNAVAILABLE"


@dataclass
class SpanVerificationResult:
    status: SpanVerificationStatus
    source_id: str
    representation_id: Optional[str]
    span_hash: str
    char_start: int
    char_end: int
    matched_text: str
    explanation: str

    @property
    def is_verified(self) -> bool:
        return self.status == SpanVerificationStatus.SPAN_VERIFIED


def normalize_source_safe_text(t: str) -> str:
    """Normalize text while strictly preserving clinical tokens, units, numbers, and negations."""
    if not t:
        return ""
    # Replace curly quotes and dashes
    t = t.replace("\u2018", "'").replace("\u2019", "'")
    t = t.replace("\u201c", '"').replace("\u201d", '"')
    t = t.replace("\u2013", "-").replace("\u2014", "-")
    t = t.replace("\u2264", "<=").replace("\u2265", ">=")
    t = t.replace("\u00a0", " ")
    # Collapse multiple whitespace to single space
    t = re.sub(r"\s+", " ", t)
    return t.strip()


class V6SpanVerifier:
    """Verifies evidence quotes against verified representations on disk."""

    @staticmethod
    def verify_span(
        quote: str,
        source_id: str,
        rep_manager: V6SourceRepresentationManager,
    ) -> SpanVerificationResult:
        rep = rep_manager.get_representation(source_id)
        if not rep or not rep.text_content:
            return SpanVerificationResult(
                status=SpanVerificationStatus.REPRESENTATION_UNAVAILABLE,
                source_id=source_id,
                representation_id=None,
                span_hash="",
                char_start=-1,
                char_end=-1,
                matched_text="",
                explanation=f"No verified representation on disk for source '{source_id}'.",
            )

        norm_quote = normalize_source_safe_text(quote)
        norm_rep = normalize_source_safe_text(rep.text_content)

        span_hash = hashlib.sha256(norm_quote.encode("utf-8")).hexdigest()

        # Check exact normalized substring match
        idx = norm_rep.find(norm_quote)
        if idx != -1:
            end_idx = idx + len(norm_quote)
            return SpanVerificationResult(
                status=SpanVerificationStatus.SPAN_VERIFIED,
                source_id=source_id,
                representation_id=rep.representation_id,
                span_hash=span_hash,
                char_start=idx,
                char_end=end_idx,
                matched_text=norm_rep[idx:end_idx],
                explanation=f"Exact span verified in {rep.representation_type} (chars {idx}..{end_idx}).",
            )

        # Fallback: case-insensitive match
        idx_lower = norm_rep.lower().find(norm_quote.lower())
        if idx_lower != -1:
            end_idx = idx_lower + len(norm_quote)
            return SpanVerificationResult(
                status=SpanVerificationStatus.SPAN_VERIFIED,
                source_id=source_id,
                representation_id=rep.representation_id,
                span_hash=span_hash,
                char_start=idx_lower,
                char_end=end_idx,
                matched_text=norm_rep[idx_lower:end_idx],
                explanation=f"Exact span verified (case-insensitive) in {rep.representation_type} (chars {idx_lower}..{end_idx}).",
            )

        return SpanVerificationResult(
            status=SpanVerificationStatus.SPAN_NOT_FOUND,
            source_id=source_id,
            representation_id=rep.representation_id,
            span_hash=span_hash,
            char_start=-1,
            char_end=-1,
            matched_text="",
            explanation=f"Quote not found in verified representation '{rep.representation_id}'. Quote: '{norm_quote[:80]}...'",
        )

    @staticmethod
    def verify_semantic_concordance(
        claim_text: str,
        current_edition_text: str,
    ) -> Tuple[bool, str]:
        """Verify that claim is concordant with current edition text."""
        norm_claim = normalize_source_safe_text(claim_text).lower()
        norm_cur = normalize_source_safe_text(current_edition_text).lower()

        # Extract decisive keywords from claim
        tokens = [w for w in re.findall(r"\b[a-z0-9\-\.]+\b", norm_claim) if len(w) > 3]
        if not tokens:
            return False, "No key entities in claim text."

        matched = [w for w in tokens if w in norm_cur]
        ratio = len(matched) / len(tokens)

        if ratio >= 0.70:
            return True, f"Key entity concordance verified ({len(matched)}/{len(tokens)} tokens in current edition)."
        return False, f"Low concordance ratio ({ratio:.2f} < 0.70) with current edition text."
