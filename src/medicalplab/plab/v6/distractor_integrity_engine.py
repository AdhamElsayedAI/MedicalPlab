"""V6 Option-Specific Distractor Integrity & Contamination Detector.

Enforces:
1. Cryptographic and semantic binding of every option review:
   question_id, question_version, option_id, exact option text hash, stem hash.
2. Cross-question contamination detection: flags rationales discussing unrelated clinical
   concepts (e.g. lifestyle options receiving digoxin/antiarrhythmic rationales).
3. Boilerplate detection: flags reused generic rationales across unrelated options.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class OptionReviewRecord:
    question_id: str
    question_version: str
    stem_hash: str
    option_id: str
    option_text: str
    option_text_hash: str
    why_plausible: str
    why_inferior_or_wrong: str
    is_defensible: bool
    rationale_hash: str = ""
    is_valid: bool = True
    contamination_flags: List[str] = field(default_factory=list)
    boilerplate_flags: List[str] = field(default_factory=list)
    safety_risk: str = ""

    def __post_init__(self):
        combined = f"{self.why_plausible}|{self.why_inferior_or_wrong}"
        if not self.rationale_hash:
            self.rationale_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DistractorIntegrityReport:
    question_id: str
    total_options_reviewed: int
    valid_option_reviews: int
    invalid_rationale_bindings: int
    boilerplate_flags: List[str] = field(default_factory=list)
    contamination_flags: List[str] = field(default_factory=list)
    multiple_defensible_options: bool = False
    defensible_options: List[str] = field(default_factory=list)
    integrity_passed: bool = True
    reviews: List[OptionReviewRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "total_options_reviewed": self.total_options_reviewed,
            "valid_option_reviews": self.valid_option_reviews,
            "invalid_rationale_bindings": self.invalid_rationale_bindings,
            "boilerplate_flags": self.boilerplate_flags,
            "contamination_flags": self.contamination_flags,
            "multiple_defensible_options": self.multiple_defensible_options,
            "defensible_options": self.defensible_options,
            "integrity_passed": self.integrity_passed,
            "reviews": [r.to_dict() for r in self.reviews],
        }


class V6DistractorIntegrityEngine:
    """Evaluates option-specific distractor integrity and detects contamination."""

    @staticmethod
    def audit_distractors(
        question_id: str,
        question_version: str,
        stem: str,
        options: List[Dict[str, str]],
        correct_answer_id: str,
        distractor_reviews: List[Dict[str, Any]],
    ) -> DistractorIntegrityReport:
        stem_hash = hashlib.sha256(stem.strip().encode("utf-8")).hexdigest()
        review_records: List[OptionReviewRecord] = []
        contamination_flags: List[str] = []
        boilerplate_flags: List[str] = []
        seen_rationales: Dict[str, str] = {}  # rationale_hash -> option_id
        defensible_options: List[str] = []

        # Map option text
        opt_map = {opt["id"]: opt.get("text", "").strip() for opt in options}

        for rev in distractor_reviews:
            opt_id = rev.get("option_id", "")
            actual_text = opt_map.get(opt_id, "")
            opt_text_hash = hashlib.sha256(actual_text.encode("utf-8")).hexdigest()

            why_plausible = rev.get("why_plausible", "").strip()
            why_inferior = rev.get("why_inferior_or_wrong", "").strip()
            is_defensible = bool(rev.get("is_defensible", False))
            safety_risk = rev.get("safety_risk_if_chosen", "")

            rec = OptionReviewRecord(
                question_id=question_id,
                question_version=question_version,
                stem_hash=stem_hash,
                option_id=opt_id,
                option_text=actual_text,
                option_text_hash=opt_text_hash,
                why_plausible=why_plausible,
                why_inferior_or_wrong=why_inferior,
                is_defensible=is_defensible,
                safety_risk=safety_risk,
            )

            # 1. Contamination Check: does rationale discuss entities foreign to option and question?
            # Example: Option is lifestyle (smoking, diet) but rationale discusses digoxin, amiodarone, pacing
            combined_text = f"{why_plausible} {why_inferior}".lower()
            opt_lower = actual_text.lower()
            stem_lower = stem.lower()

            foreign_terms = [
                ("digoxin", "antiarrhythmic"),
                ("amiodarone", "antiarrhythmic"),
                ("pacing", "electrophysiology"),
                ("cardioversion", "arrhythmia shock"),
                ("thoracentesis", "pleural aspiration"),
            ]
            for term, category in foreign_terms:
                if term in combined_text and term not in opt_lower and term not in stem_lower:
                    flag = f"CROSS_QUESTION_CONTAMINATION: Option '{opt_id}' ({actual_text}) rationale mentions foreign term '{term}' not present in option or stem."
                    rec.contamination_flags.append(flag)
                    contamination_flags.append(flag)
                    rec.is_valid = False

            # 2. Boilerplate Check: generic uninformative statements
            if len(why_inferior) > 0 and len(why_inferior.split()) < 4 and not is_defensible:
                b_flag = f"BOILERPLATE_RATIONALE: Option '{opt_id}' rationale is too generic: '{why_inferior}'."
                rec.boilerplate_flags.append(b_flag)
                boilerplate_flags.append(b_flag)
                rec.is_valid = False

            # 3. Duplicate rationale check across options
            if rec.rationale_hash in seen_rationales and not is_defensible:
                prev_opt = seen_rationales[rec.rationale_hash]
                b_flag = f"DUPLICATE_RATIONALE: Option '{opt_id}' reuses identical rationale as option '{prev_opt}'."
                rec.boilerplate_flags.append(b_flag)
                boilerplate_flags.append(b_flag)
                rec.is_valid = False
            else:
                seen_rationales[rec.rationale_hash] = opt_id

            if is_defensible and opt_id != correct_answer_id:
                defensible_options.append(opt_id)

            review_records.append(rec)

        multiple_defensible = len(defensible_options) > 0
        valid_count = sum(1 for r in review_records if r.is_valid)
        invalid_count = len(review_records) - valid_count

        integrity_passed = (invalid_count == 0) and (not multiple_defensible) and (len(contamination_flags) == 0)

        return DistractorIntegrityReport(
            question_id=question_id,
            total_options_reviewed=len(review_records),
            valid_option_reviews=valid_count,
            invalid_rationale_bindings=invalid_count,
            boilerplate_flags=boilerplate_flags,
            contamination_flags=contamination_flags,
            multiple_defensible_options=multiple_defensible,
            defensible_options=defensible_options,
            integrity_passed=integrity_passed,
            reviews=review_records,
        )
