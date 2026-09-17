"""Transfer Assessment Service for MedicalPlab Phase 2B.

Selects, administers, and deterministically scores independent held-out transfer items
following completion of Socratic remediation practice.

HARD INVARIANTS:
1. Independent transfer items are stripped of answer keys, explanations, and distractor annotations.
2. Server-side deterministic scoring only; client-submitted correctness is rejected.
3. Assisted attempts (was_assisted=True) are strictly disqualified from TRANSFER_CONFIRMED.
4. Prior exposure to the original question or items during remediation excludes selection.
5. If no eligible item exists, reports unavailable and records UNRESOLVED (never auto-generates items).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from medicalplab.remediation.models import (
    RemediationOutcome,
    TransferAttempt,
    TransferItemDTO,
)

logger = logging.getLogger(__name__)

# Reviewed Held-out Transfer Item Registry (Synthetic fixtures for automated testing)
TRANSFER_ITEM_REGISTRY: Dict[str, Dict[str, Any]] = {
    "UNI-RENAL-001": {
        "question_id": "UNI-RENAL-001-T",
        "paired_original_id": "UNI-RENAL-001",
        "subject": "Renal physiology",
        "topic": "RAAS mechanisms",
        "target_concept": "Renin substrate (Angiotensinogen)",
        "stem": (
            "In an investigation of renovascular regulation, an elevated plasma renin activity is observed. "
            "Which circulating hepatic globular glycoprotein serves as the direct cleavage substrate for active renin?"
        ),
        "options": {
            "A": "Angiotensinogen",
            "B": "Angiotensin II",
            "C": "Aldosterone",
            "D": "Bradykinin",
        },
        "correct_answer": "A",
        "explanation": (
            "Active renin specifically cleaves the peptide bond in circulating angiotensinogen (synthesized by the liver) "
            "to release the decapeptide angiotensin I. Angiotensin II is produced downstream by ACE."
        ),
        "difficulty": "medium",
        "content_kind": "SYNTHETIC_TEST_FIXTURE",
        "status": "TEST_FIXTURE_ONLY",
        "evidence": {
            "document_id": "DOC-PMC-RENAL-0001",
            "chunk_id": "DOC-PMC-RENAL-0001-B0003-C01",
            "title": "The Renin-Angiotensin-aldosterone system in vascular inflammation and remodeling.",
            "license": "CC BY 3.0",
        },
    },
    "UNI-RENAL-002": {
        "question_id": "UNI-RENAL-002-T",
        "paired_original_id": "UNI-RENAL-002",
        "subject": "Renal physiology",
        "topic": "RAAS mechanisms",
        "target_concept": "Angiotensin conversion enzyme (ACE)",
        "stem": (
            "During pulmonary transit, the decapeptide angiotensin I is converted into the potent octapeptide vasoconstrictor. "
            "Which endothelial-bound peptidyldipeptidase catalyzes this specific transformation?"
        ),
        "options": {
            "A": "Renin",
            "B": "Angiotensin-converting enzyme (ACE)",
            "C": "Chymase",
            "D": "Neprilysin",
        },
        "correct_answer": "B",
        "explanation": (
            "Angiotensin-converting enzyme (ACE), predominantly anchored to the pulmonary vascular endothelium, "
            "cleaves the C-terminal dipeptide from angiotensin I to produce angiotensin II."
        ),
        "difficulty": "medium",
        "content_kind": "SYNTHETIC_TEST_FIXTURE",
        "status": "TEST_FIXTURE_ONLY",
        "evidence": {
            "document_id": "DOC-PMC-RENAL-0001",
            "chunk_id": "DOC-PMC-RENAL-0001-B0003-C01",
            "title": "The Renin-Angiotensin-aldosterone system in vascular inflammation and remodeling.",
            "license": "CC BY 3.0",
        },
    },
    "PLAB-CARD-0001": {
        "question_id": "PLAB-CARD-0001-T",
        "paired_original_id": "PLAB-CARD-0001",
        "subject": "Cardiology",
        "topic": "Hypertension (Essential & Secondary)",
        "target_concept": "Step 1 antihypertensive in patients >=55 or of African origin (CCB)",
        "stem": (
            "A 62-year-old Afro-Caribbean woman with newly confirmed stage 1 hypertension and no comorbidities "
            "requires initiation of antihypertensive therapy according to UK NICE NG136 guidance. Which class of medication is the most appropriate first-line choice?"
        ),
        "options": {
            "A": "Calcium channel blocker (e.g. Amlodipine)",
            "B": "ACE inhibitor (e.g. Ramipril)",
            "C": "Angiotensin II receptor blocker (e.g. Losartan)",
            "D": "Thiazide-like diuretic (e.g. Indapamide)",
        },
        "correct_answer": "A",
        "explanation": "NICE NG136 specifies that for patients aged 55 or older or of Black African or African-Caribbean origin, Step 1 treatment is a calcium channel blocker.",
        "difficulty": "medium",
        "content_kind": "SYNTHETIC_TEST_FIXTURE",
        "status": "TEST_FIXTURE_ONLY",
        "evidence": {
            "document_id": "DOC-PMC-CARD-0002",
            "chunk_id": "DOC-PMC-CARD-0002-B0001-C01",
            "title": "Hypertension management in adults: summary of updated NICE guidance",
            "license": "CC BY 4.0",
        },
    },
}



class TransferAssessmentService:
    """Selects, validates, and grades independent held-out transfer items."""

    def __init__(self, registry: Dict[str, Dict[str, Any]] | None = None) -> None:
        self._registry = registry or TRANSFER_ITEM_REGISTRY

    def get_eligible_transfer_item(
        self,
        original_question_id: str,
        exposed_item_ids: Optional[List[str]] = None,
    ) -> Optional[TransferItemDTO]:
        """Select an eligible held-out item testing the same concept without prior exposure."""
        exposed = set(exposed_item_ids or [])
        exposed.add(original_question_id)

        item = self._registry.get(original_question_id)
        if not item:
            logger.warning("No transfer item registered for original question %s", original_question_id)
            return None

        if item["question_id"] in exposed:
            logger.warning(
                "Transfer item %s already exposed to learner; disqualified",
                item["question_id"],
            )
            return None

        # Return public DTO stripped of answer key and explanation
        return TransferItemDTO(
            question_id=item["question_id"],
            stem=item["stem"],
            options=item["options"],
            subject=item["subject"],
            topic=item["topic"],
            difficulty=item["difficulty"],
            evidence_title=item.get("evidence", {}).get("title"),
            evidence_license=item.get("evidence", {}).get("license"),
        )

    def score_transfer_submission(
        self,
        original_question_id: str,
        question_id: str,
        selected_option: str,
        was_assisted: bool = False,
    ) -> tuple[RemediationOutcome, TransferAttempt, str, list[dict[str, Any]]]:
        """Score transfer submission deterministically server-side.

        Returns:
            Tuple[outcome, TransferAttempt, explanation, citations]
        """
        item = self._registry.get(original_question_id)
        if not item or item["question_id"] != question_id:
            logger.error("Scoring mismatch: item %s does not match original %s", question_id, original_question_id)
            attempt = TransferAttempt(
                question_id=question_id,
                submitted_option=selected_option,
                is_correct=False,
                was_assisted=was_assisted,
            )
            return RemediationOutcome.UNRESOLVED, attempt, "Assessment item could not be verified.", []

        correct_answer = item["correct_answer"]
        is_correct = (selected_option == correct_answer)

        attempt = TransferAttempt(
            question_id=question_id,
            submitted_option=selected_option,
            is_correct=is_correct,
            was_assisted=was_assisted,
        )

        citations = []
        if "evidence" in item:
            citations.append({
                "ref": item["evidence"].get("title", ""),
                "quote": item.get("explanation", "")[:200],
                "chunk_id": item["evidence"].get("chunk_id", ""),
                "license": item["evidence"].get("license", ""),
            })

        # CRITICAL INVARIANT: Assisted success cannot confirm transfer!
        if was_assisted:
            logger.info("Transfer attempt for %s was assisted; outcome is UNRESOLVED", question_id)
            return (
                RemediationOutcome.UNRESOLVED,
                attempt,
                item["explanation"],
                citations,
            )

        if is_correct:
            logger.info("Transfer confirmed unassisted for %s", question_id)
            return (
                RemediationOutcome.TRANSFER_CONFIRMED,
                attempt,
                item["explanation"],
                citations,
            )
        else:
            logger.info("Transfer not confirmed for %s (incorrect option %s)", question_id, selected_option)
            return (
                RemediationOutcome.TRANSFER_NOT_CONFIRMED,
                attempt,
                item["explanation"],
                citations,
            )
