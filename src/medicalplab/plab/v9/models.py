"""Data models for V9 source-proof evidence, canonical organizations, and provenance."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SpanType(str, Enum):
    EXACT_SOURCE_SPAN = "EXACT_SOURCE_SPAN"
    NORMALIZED_SOURCE_SPAN = "NORMALIZED_SOURCE_SPAN"
    PARAPHRASE = "PARAPHRASE"


class SupportStatus(str, Enum):
    DIRECT_SUPPORT = "DIRECT_SUPPORT"
    TOPIC_RELATED_ONLY = "TOPIC_RELATED_ONLY"
    CONTRADICTED = "CONTRADICTED"
    UNSUPPORTED = "UNSUPPORTED"


class TrustState(str, Enum):
    CLINICIAN_REVIEW_REQUIRED = "CLINICIAN_REVIEW_REQUIRED"
    QUARANTINED = "QUARANTINED"
    DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"


class OrganizationRole(str, Enum):
    ISSUING_ORGANIZATION = "ISSUING_ORGANIZATION"
    AUTHORITATIVE_HOST = "AUTHORITATIVE_HOST"
    JOURNAL_PUBLISHER = "JOURNAL_PUBLISHER"
    SUPPORTING_ORGANIZATION = "SUPPORTING_ORGANIZATION"


class RedistributionReadiness(str, Enum):
    PUBLIC_REDISTRIBUTION_VERIFIED = "PUBLIC_REDISTRIBUTION_VERIFIED"
    PRIVATE_EVIDENCE_ONLY = "PRIVATE_EVIDENCE_ONLY"
    REDISTRIBUTION_UNKNOWN = "REDISTRIBUTION_UNKNOWN"


@dataclass
class OrganizationIdentity:
    organization_id: str
    canonical_name: str
    aliases: List[str]
    roles: List[str]
    approved_hosts: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceSpan:
    span_id: str
    span_type: SpanType
    exact_text: str
    exact_text_sha256: str
    source_id: str
    start_char: int
    end_char: int
    line_number: Optional[int] = None
    locator_type: str = "CHAR_OFFSET"
    normalization_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["span_type"] = self.span_type.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceSpan:
        d = dict(data)
        d["span_type"] = SpanType(d["span_type"])
        return cls(**d)


@dataclass
class SourcePacket:
    source_id: str
    canonical_identifier: str
    canonical_title: str
    issuing_organization_id: str
    canonical_organization: str
    canonical_url: str
    final_resolved_url: str
    edition: str
    retrieval_timestamp: str
    http_status: int
    raw_snapshot_path: str
    raw_snapshot_sha256: str
    raw_snapshot_hash_basis: str = "RAW_BYTES_SHA256"
    response_byte_length: int = 0
    normalized_representation_path: str = ""
    normalized_representation_sha256: str = ""
    normalized_representation_hash_basis: str = "UTF8_LF_CANONICAL_TEXT"
    currentness_basis: str = ""
    currentness_evidence: Dict[str, Any] = field(default_factory=dict)
    identity_evidence: Dict[str, Any] = field(default_factory=dict)
    redistribution_readiness: str = "PRIVATE_EVIDENCE_ONLY"
    acquisition_method: str = "LIVE_PRIMARY_SOURCE_HTTP_AND_DURABLE_SNAPSHOT"
    evidence_spans: List[EvidenceSpan] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["evidence_spans"] = [
            s.to_dict() if isinstance(s, EvidenceSpan) else s for s in self.evidence_spans
        ]
        return d


@dataclass
class AtomicClaim:
    claim_id: str
    claim_text: str
    is_decisive: bool
    source_id: str
    evidence_span_ids: List[str]
    evidence_quotes: List[str]
    support_status: str
    specificity_dimensions: Dict[str, str]
    evidence_binding_sha256: str
    source_identity_pass: bool = True
    source_currentness_pass: bool = True
    span_verification_pass: bool = True
    specificity_pass: bool = True
    final_claim_pass: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
