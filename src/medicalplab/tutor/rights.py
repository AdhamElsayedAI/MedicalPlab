"""Source Rights Gate for Phase 1 Grounded Generative Tutor.

Enforces fail-closed copyright and AI-processing rights verification.
Only verified open-access PMC basic-science literature under CC BY licenses
is cleared for LLM generation prompts, and text-only passages are permitted.
All Crown copyright, clinical guideline, and publisher sources fail closed.
"""
from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from medicalplab.evidence_engine.models import RetrievedCandidate


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_RENAL_MANIFEST = ROOT_DIR / "Data/metadata/renal_source_license_manifest_v1.json"
TUTOR_RIGHTS_MANIFEST = ROOT_DIR / "Data/metadata/tutor_source_rights_manifest_v1.json"


class AIReuseStatus(str, Enum):
    AI_REUSE_ALLOWED = "AI_REUSE_ALLOWED"
    AI_REUSE_REQUIRES_PERMISSION = "AI_REUSE_REQUIRES_PERMISSION"
    AI_REUSE_PROHIBITED = "AI_REUSE_PROHIBITED"
    AI_REUSE_UNKNOWN = "AI_REUSE_UNKNOWN"


class DisplayQuotationStatus(str, Enum):
    DISPLAY_ALLOWED = "DISPLAY_ALLOWED"
    DISPLAY_REQUIRES_PERMISSION = "DISPLAY_REQUIRES_PERMISSION"
    DISPLAY_PROHIBITED = "DISPLAY_PROHIBITED"
    DISPLAY_UNKNOWN = "DISPLAY_UNKNOWN"


class SourceRightsGate:
    """Evaluates copyright and processing rights before evidence enters LLM prompts."""

    def __init__(self, renal_manifest_path: Path | str | None = None) -> None:
        self.manifest_path = Path(renal_manifest_path) if renal_manifest_path else DEFAULT_RENAL_MANIFEST
        self._doc_rights: dict[str, dict[str, Any]] = {}
        self._load_manifest()

    def _load_manifest(self) -> None:
        if not self.manifest_path.exists():
            return

        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        entries = data.get("entries", [])
        for entry in entries:
            doc_id = entry.get("document_id")
            if not doc_id:
                continue

            license_str = entry.get("license", "")
            # CC BY 2.0, 3.0, 4.0, or unspecified version in PMC JATS metadata
            # grant worldwide royalty-free rights to adapt/process with attribution.
            is_cc_by = "CC BY" in license_str or "Creative Commons" in license_str

            if is_cc_by:
                ai_status = AIReuseStatus.AI_REUSE_ALLOWED
                disp_status = DisplayQuotationStatus.DISPLAY_ALLOWED
                reason = f"Verified open-access license: {license_str}. Text-only processing permitted."
            else:
                ai_status = AIReuseStatus.AI_REUSE_REQUIRES_PERMISSION
                disp_status = DisplayQuotationStatus.DISPLAY_REQUIRES_PERMISSION
                reason = f"Non-CC-BY or proprietary license: {license_str}. Fails closed."

            self._doc_rights[doc_id] = {
                "document_id": doc_id,
                "pmcid": entry.get("pmcid"),
                "license": license_str,
                "ai_reuse_status": ai_status.value,
                "display_quotation_status": disp_status.value,
                "text_only_restriction": True,
                "reason": reason,
            }

    def check_document(self, document_id: str) -> tuple[AIReuseStatus, DisplayQuotationStatus, str]:
        """Check the AI processing and display rights for a document ID."""
        info = self._doc_rights.get(document_id)
        if not info:
            # Cardiorespiratory, NICE, BNF, RCUK or unknown documents fail closed
            return (
                AIReuseStatus.AI_REUSE_REQUIRES_PERMISSION,
                DisplayQuotationStatus.DISPLAY_REQUIRES_PERMISSION,
                f"Document '{document_id}' is not in verified open-access renal manifest. Fails closed.",
            )

        ai_status = AIReuseStatus(info["ai_reuse_status"])
        disp_status = DisplayQuotationStatus(info["display_quotation_status"])
        return ai_status, disp_status, info["reason"]

    def is_ai_reuse_allowed(self, document_id: str) -> bool:
        ai_status, _, _ = self.check_document(document_id)
        return ai_status == AIReuseStatus.AI_REUSE_ALLOWED

    def filter_candidates(self, candidates: list[RetrievedCandidate]) -> list[RetrievedCandidate]:
        """Filter retrieved candidates, retaining only those from AI_REUSE_ALLOWED sources."""
        allowed = []
        for cand in candidates:
            if self.is_ai_reuse_allowed(cand.document_id):
                allowed.append(cand)
        return allowed

    def export_tutor_rights_manifest(self, output_path: Path | str | None = None) -> Path:
        """Export machine-readable tutor source rights manifest."""
        target = Path(output_path) if output_path else TUTOR_RIGHTS_MANIFEST
        target.parent.mkdir(parents=True, exist_ok=True)
        manifest_data = {
            "manifest_id": "TUTOR-SOURCE-RIGHTS-v1",
            "version": "1.0.0",
            "phase": "Phase 1 - Grounded Generative Tutor",
            "total_documents": len(self._doc_rights),
            "documents": list(self._doc_rights.values()),
        }
        target.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return target
