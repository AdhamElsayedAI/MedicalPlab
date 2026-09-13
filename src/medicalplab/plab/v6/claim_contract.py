"""V6 Atomic Claim Contract and Audit Record.

Enforces:
1. Every claim must contain actual claim text, location, category, entity spec, and source fragment bindings.
2. Side-by-side inspectability: claim text and evidence quote always preserved together.
3. No opaque PASS verdicts without explicit evidence anchors and reasons.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from medicalplab.plab.v6.numeric_specificity_engine import (
    ClaimSupportStatus,
    ClinicalEntitySpec,
)


class ClaimCategory(str, Enum):
    STEM_DIAGNOSTIC_FACT = "STEM_DIAGNOSTIC_FACT"
    DIAGNOSTIC_CRITERIA = "DIAGNOSTIC_CRITERIA"
    MANAGEMENT_PRIORITY = "MANAGEMENT_PRIORITY"
    DOSE_AND_THRESHOLD = "DOSE_AND_THRESHOLD"
    ANSWER_SPECIFICITY_CLAIM = "ANSWER_SPECIFICITY_CLAIM"
    CONTRAINDICATION = "CONTRAINDICATION"
    DISTRACTOR_DECISIVE_CLAIM = "DISTRACTOR_DECISIVE_CLAIM"
    UK_NATIONAL_GUIDELINE_CLAIM = "UK_NATIONAL_GUIDELINE_CLAIM"


@dataclass
class AtomicClaimV6:
    claim_id: str
    question_id: str
    claim_text: str
    claim_location: str
    claim_category: ClaimCategory
    is_decisive: bool
    source_id: str
    evidence_quote: str
    evidence_anchor: str
    question_version: str = "v6"
    claim_text_hash: str = ""
    source_fragment_ids: List[str] = field(default_factory=list)
    target_option: Optional[str] = None
    risk_level: str = "R2"
    required_jurisdiction: str = "UK"
    entity_spec: Optional[ClinicalEntitySpec] = None

    # Multi-gate verification fields
    source_identity_pass: bool = False
    source_currency_pass: bool = False
    source_representation_pass: bool = False
    span_verification_pass: bool = False
    specificity_pass: bool = False
    numeric_entity_pass: bool = False
    claim_support_status: ClaimSupportStatus = ClaimSupportStatus.UNSUPPORTED
    final_claim_pass: bool = False
    reasons: List[str] = field(default_factory=list)
    explanation: str = ""

    def __post_init__(self):
        if not self.claim_text_hash and self.claim_text:
            self.claim_text_hash = hashlib.sha256(self.claim_text.strip().encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["claim_category"] = self.claim_category.value
        d["claim_support_status"] = self.claim_support_status.value
        return d
