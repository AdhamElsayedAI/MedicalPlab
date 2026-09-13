"""V6 Guideline Currency Engine.

Enforces:
1. Currentness derived from external official publishing events and verified receipts.
2. Default state is UNKNOWN (fail-closed).
3. RCUK 2025 guidelines (published 27 Oct 2025) supersede RCUK 2021 guidelines.
4. ESC/EACTS 2025 VHD guidelines supersede 2021 edition.
5. HISTORICAL_CONCORDANT requires claim-level comparison against verified current edition,
   never an assumed boolean parameter.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class GuidelineCurrency(str, Enum):
    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"
    PARTIALLY_SUPERSEDED = "PARTIALLY_SUPERSEDED"
    HISTORICAL_CONCORDANT = "HISTORICAL_CONCORDANT"
    UNKNOWN = "UNKNOWN"


@dataclass
class CurrencyEvaluationResult:
    source_id: str
    currency: GuidelineCurrency
    current_edition_id: Optional[str]
    superseded_by: Optional[str]
    policy_passes: bool
    is_concordant: bool
    reason: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "currency": self.currency.value,
            "current_edition_id": self.current_edition_id,
            "superseded_by": self.superseded_by,
            "policy_passes": self.policy_passes,
            "is_concordant": self.is_concordant,
            "reason": self.reason,
            "explanation": self.explanation,
        }


# Authoritative Publisher Editions and Successions Knowledge Graph
OFFICIAL_EDITION_SUCCESSIONS: Dict[str, Dict[str, Any]] = {
    # Resuscitation Council UK (RCUK)
    "SRC-RCUK-ALS-2021": {
        "status": GuidelineCurrency.SUPERSEDED,
        "superseded_by": "SRC-RCUK-ALS-2025",
        "superseded_date": "2025-10-27",
        "official_notice": "Resuscitation Council UK published 2025 Guidelines on 27 October 2025 updating ALS 2021.",
    },
    "SRC-RCUK-ALS-2025": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2025-10-27",
        "official_notice": "Current Resuscitation Council UK Adult Advanced Life Support Guidelines 2025.",
    },
    "SRC-RCUK-BRADY-2021": {
        "status": GuidelineCurrency.SUPERSEDED,
        "superseded_by": "SRC-RCUK-BRADY-2025",
        "superseded_date": "2025-10-27",
        "official_notice": "Resuscitation Council UK 2025 Peri-arrest Arrhythmias algorithm supersedes 2021 edition.",
    },
    "SRC-RCUK-BRADY-2025": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2025-10-27",
        "official_notice": "Current Resuscitation Council UK Peri-arrest Bradycardia Algorithm 2025.",
    },
    "SRC-RCUK-BLS-2025": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2025-10-27",
        "official_notice": "Current Resuscitation Council UK Adult Basic Life Support Guidelines 2025 (rate 100-120/min, depth 5-6 cm).",
    },
    "SRC-RCUK-ANAPHYLAXIS-2021": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2021-05-01",
        "official_notice": "Current Resuscitation Council UK Anaphylaxis Guidelines 2021.",
    },

    # European Society of Cardiology (ESC)
    "SRC-ESC-VHD-2021": {
        "status": GuidelineCurrency.SUPERSEDED,
        "superseded_by": "SRC-ESC-VHD-2025",
        "superseded_date": "2025-08-30",
        "official_notice": "2025 ESC/EACTS Guidelines for the management of valvular heart disease explicitly update the 2021 edition.",
    },
    "SRC-ESC-VHD-2025": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2025-08-30",
        "official_notice": "Current 2025 ESC/EACTS Guidelines for the management of valvular heart disease.",
    },
    "SRC-ESC-EACTS-VHD-2025": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2025-08-30",
        "official_notice": "Current 2025 ESC/EACTS Guidelines for the management of valvular heart disease.",
    },
    "SRC-ESC-PERI-2015": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2015-08-29",
        "official_notice": "Current ESC Guidelines on Pericardial Diseases.",
    },
    "SRC-ESC-ACS-2023": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2023-08-25",
        "official_notice": "Current ESC Guidelines on Acute Coronary Syndromes.",
    },

    # NICE UK National Guidelines (Current)
    "SRC-NICE-NG136": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2019-08-28",
        "latest_surveillance": "2023-12-05",
        "official_notice": "Current NICE NG136 Hypertension in adults: diagnosis and management.",
    },
    "SRC-NICE-NG196": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2021-04-27",
        "official_notice": "Current NICE NG196 Atrial fibrillation: diagnosis and management.",
    },
    "SRC-NICE-CG109": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2010-08-25",
        "latest_surveillance": "2014-09-01",
        "official_notice": "Current NICE CG109 Transient loss of consciousness in over 16s.",
    },
    "SRC-NICE-NG115": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2018-12-05",
        "latest_surveillance": "2019-07-26",
        "official_notice": "Current NICE NG115 COPD in over 16s: diagnosis and management.",
    },
    "SRC-NICE-CG64": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2008-03-17",
        "latest_surveillance": "2016-07-07",
        "official_notice": "Current NICE CG64 Prophylaxis against infective endocarditis.",
    },
    "SRC-NICE-NG208": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2021-11-18",
        "official_notice": "Current NICE NG208 Heart valve disease in adults: investigation and management.",
    },
    "SRC-NICE-NG106": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2018-09-12",
        "official_notice": "Current NICE NG106 Chronic heart failure in adults: diagnosis and management.",
    },
    "SRC-NICE-NG185": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2020-11-18",
        "official_notice": "Current NICE NG185 Acute coronary syndromes.",
    },
    "SRC-NICE-CG191": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2014-12-03",
        "latest_surveillance": "2023-01-15",
        "official_notice": "Current NICE CG191 Pneumonia in adults: diagnosis and management.",
    },
    "SRC-NICE-NG158": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2020-03-26",
        "official_notice": "Current NICE NG158 Venous thromboembolic diseases: diagnosis and management.",
    },
    "SRC-NICE-CG163": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2013-06-12",
        "official_notice": "Current NICE CG163 Idiopathic pulmonary fibrosis in adults.",
    },
    "SRC-NICE-NG202": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2021-08-20",
        "official_notice": "Current NICE NG202 Obstructive sleep apnoea/hypopnoea syndrome.",
    },
    "SRC-NICE-NG12": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2015-06-23",
        "latest_surveillance": "2023-11-01",
        "official_notice": "Current NICE NG12 Suspected cancer: recognition and referral.",
    },
    "SRC-NICE-TA504": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2018-01-24",
        "official_notice": "Current NICE TA504 Pirfenidone for treating idiopathic pulmonary fibrosis.",
    },

    # British Thoracic Society (BTS)
    "SRC-BTS-OXYGEN-2017": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2017-05-01",
        "official_notice": "Current British Thoracic Society Emergency Oxygen Guideline.",
    },
    "SRC-BTS-PLEURAL-2023": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2023-03-01",
        "official_notice": "Current British Thoracic Society Clinical Statement on Pleural Disease / Spontaneous Pneumothorax.",
    },
    "SRC-BTS-SIGN-ASTHMA": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2019-07-01",
        "official_notice": "Current BTS/SIGN British guideline on the management of asthma (SIGN 158).",
    },
    "SRC-BTS-SIGN-158": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2019-07-01",
        "official_notice": "Current BTS/SIGN British guideline on the management of asthma (SIGN 158).",
    },

    # Intensive Care
    "SRC-FICM-ICS-ARDS": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2019-01-01",
        "official_notice": "Current FICM/ICS Guideline for the Management of Acute Respiratory Distress Syndrome.",
    },

    # Peer-Reviewed Benchmarks (Active)
    "SRC-LAGHLAM-2024-PMC10980676": {
        "status": GuidelineCurrency.CURRENT,
        "publication_date": "2024-03-23",
        "official_notice": "Current 2024 Annals of Intensive Care narrative review on cardiogenic shock resuscitation (PMC10980676).",
    },
}


class V6GuidelineCurrencyEngine:
    """Evaluates guideline currency fail-closed."""

    @staticmethod
    def evaluate_currency(
        source_id: str,
        current_edition_evidence_text: Optional[str] = None,
        claim_text: Optional[str] = None,
    ) -> CurrencyEvaluationResult:
        """Evaluate currency of a source.
        
        Rules:
        - If not in official succession knowledge graph -> UNKNOWN (fail-closed).
        - If SUPERSEDED, can only pass as HISTORICAL_CONCORDANT if current edition evidence
          is provided and verified to support the claim.
        """
        if source_id not in OFFICIAL_EDITION_SUCCESSIONS:
            return CurrencyEvaluationResult(
                source_id=source_id,
                currency=GuidelineCurrency.UNKNOWN,
                current_edition_id=None,
                superseded_by=None,
                policy_passes=False,
                is_concordant=False,
                reason="CURRENCY_UNKNOWN_FAIL_CLOSED",
                explanation=f"Guideline currency status for '{source_id}' is not in authoritative official succession records.",
            )

        entry = OFFICIAL_EDITION_SUCCESSIONS[source_id]
        status = entry["status"]

        if status == GuidelineCurrency.CURRENT:
            return CurrencyEvaluationResult(
                source_id=source_id,
                currency=GuidelineCurrency.CURRENT,
                current_edition_id=source_id,
                superseded_by=None,
                policy_passes=True,
                is_concordant=True,
                reason="CURRENT_AUTHORITATIVE_EDITION",
                explanation=entry.get("official_notice", "Current active guideline edition."),
            )

        if status == GuidelineCurrency.SUPERSEDED:
            superseded_by = entry.get("superseded_by")
            # If current edition evidence is provided, check concordance
            if current_edition_evidence_text and claim_text:
                from medicalplab.plab.v6.span_verifier import V6SpanVerifier
                concordant, reason = V6SpanVerifier.verify_semantic_concordance(
                    claim_text, current_edition_evidence_text
                )
                if concordant:
                    return CurrencyEvaluationResult(
                        source_id=source_id,
                        currency=GuidelineCurrency.HISTORICAL_CONCORDANT,
                        current_edition_id=superseded_by,
                        superseded_by=superseded_by,
                        policy_passes=True,
                        is_concordant=True,
                        reason="HISTORICAL_CONCORDANT_VERIFIED",
                        explanation=(
                            f"Source is superseded by {superseded_by}, but claim '{claim_text[:50]}...' "
                            f"is verified concordant with current {superseded_by} guidance: {reason}"
                        ),
                    )

            return CurrencyEvaluationResult(
                source_id=source_id,
                currency=GuidelineCurrency.SUPERSEDED,
                current_edition_id=superseded_by,
                superseded_by=superseded_by,
                policy_passes=False,
                is_concordant=False,
                reason="GUIDELINE_SUPERSEDED_UNRESOLVED",
                explanation=f"Source is superseded by {superseded_by} and historical concordance was not proven.",
            )

        return CurrencyEvaluationResult(
            source_id=source_id,
            currency=status,
            current_edition_id=None,
            superseded_by=entry.get("superseded_by"),
            policy_passes=False,
            is_concordant=False,
            reason="CURRENCY_POLICY_REJECT",
            explanation=f"Source currency status {status.value} does not permit autonomous release.",
        )
