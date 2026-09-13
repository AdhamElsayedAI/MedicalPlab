"""V6 Source Rights and Permissions Engine.

Separates medical/clinical authority from intellectual property / licensing rights.
Tracks permissions for storage, deterministic processing, LLM evaluation, clinician review,
and product redistribution.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class PermissionStatus(str, Enum):
    ALLOWED = "ALLOWED"
    RESTRICTED = "RESTRICTED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class SourceRightsRecord:
    source_id: str
    license_type: str
    storage_permission: PermissionStatus
    deterministic_processing_permission: PermissionStatus
    llm_processing_permission: PermissionStatus
    review_excerpt_permission: PermissionStatus
    product_redistribution_permission: PermissionStatus
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "license_type": self.license_type,
            "storage_permission": self.storage_permission.value,
            "deterministic_processing_permission": self.deterministic_processing_permission.value,
            "llm_processing_permission": self.llm_processing_permission.value,
            "review_excerpt_permission": self.review_excerpt_permission.value,
            "product_redistribution_permission": self.product_redistribution_permission.value,
            "notes": self.notes,
        }


class V6SourceRightsEngine:
    """Evaluates rights and permissions for evidence usage."""

    @staticmethod
    def evaluate_rights(source_id: str, source_type: str, organization: str) -> SourceRightsRecord:
        sid = source_id.upper()
        org = organization.upper()

        # UK National Guidance (NICE, RCUK, BTS, NHS, FICM)
        if "NICE" in sid or "NICE" in org or "OGL" in sid or "CROWN" in sid:
            return SourceRightsRecord(
                source_id=source_id,
                license_type="UK_OPEN_GOVERNMENT_LICENCE_V3",
                storage_permission=PermissionStatus.ALLOWED,
                deterministic_processing_permission=PermissionStatus.ALLOWED,
                llm_processing_permission=PermissionStatus.ALLOWED,
                review_excerpt_permission=PermissionStatus.ALLOWED,
                product_redistribution_permission=PermissionStatus.RESTRICTED,
                notes="NICE guidance published under Crown Copyright / UK Open Government Licence v3. Excerpting for clinical validation permitted.",
            )

        if "RCUK" in sid or "RESUS" in org or "BTS" in sid or "THORACIC" in org or "FICM" in sid:
            return SourceRightsRecord(
                source_id=source_id,
                license_type="UK_PROFESSIONAL_SOCIETY_CLINICAL_GUIDANCE",
                storage_permission=PermissionStatus.ALLOWED,
                deterministic_processing_permission=PermissionStatus.ALLOWED,
                llm_processing_permission=PermissionStatus.ALLOWED,
                review_excerpt_permission=PermissionStatus.ALLOWED,
                product_redistribution_permission=PermissionStatus.RESTRICTED,
                notes="UK specialty society clinical practice statement. Permitted for clinical education and non-commercial validation review.",
            )

        # PMC Open Access / Creative Commons
        if "PMC" in sid:
            return SourceRightsRecord(
                source_id=source_id,
                license_type="PMC_OPEN_ACCESS_CC_BY",
                storage_permission=PermissionStatus.ALLOWED,
                deterministic_processing_permission=PermissionStatus.ALLOWED,
                llm_processing_permission=PermissionStatus.ALLOWED,
                review_excerpt_permission=PermissionStatus.ALLOWED,
                product_redistribution_permission=PermissionStatus.ALLOWED,
                notes="PMC Open Access subset article with CC-BY licensing.",
            )

        # International Guidelines (ESC, etc.)
        if "ESC" in sid:
            return SourceRightsRecord(
                source_id=source_id,
                license_type="EUROPEAN_SOCIETY_CARDIOLOGY_COPYRIGHT",
                storage_permission=PermissionStatus.ALLOWED,
                deterministic_processing_permission=PermissionStatus.ALLOWED,
                llm_processing_permission=PermissionStatus.RESTRICTED,
                review_excerpt_permission=PermissionStatus.ALLOWED,
                product_redistribution_permission=PermissionStatus.RESTRICTED,
                notes="ESC copyright applies. Short factual quotation permitted for validation; full reproduction or LLM training restricted.",
            )

        # Default fallback
        return SourceRightsRecord(
            source_id=source_id,
            license_type="STANDARD_COPYRIGHT_RESTRICTED",
            storage_permission=PermissionStatus.ALLOWED,
            deterministic_processing_permission=PermissionStatus.ALLOWED,
            llm_processing_permission=PermissionStatus.RESTRICTED,
            review_excerpt_permission=PermissionStatus.ALLOWED,
            product_redistribution_permission=PermissionStatus.RESTRICTED,
            notes="Standard copyright applies. Review excerpts only.",
        )
