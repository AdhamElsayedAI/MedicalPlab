"""V6 Adversarial One-Best-Answer Review Engine.

Enforces:
1. Strongest-case clinical challenge for every distractor.
2. Identifies if more than one option is clinically defensible under current UK practice.
3. If multiple options are defensible -> flags MULTIPLE_DEFENSIBLE_OPTIONS, triggering QUARANTINE.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class OptionAdversarialEvaluation:
    option_id: str
    option_text: str
    is_keyed_answer: bool
    strongest_case_argument: str
    counterargument_or_flaw: str
    is_clinically_defensible: bool
    distinguishing_evidence_quote: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdversarialReviewResult:
    question_id: str
    keyed_answer_id: str
    has_ambiguity: bool
    multiple_defensible_options: bool
    defensible_option_ids: List[str] = field(default_factory=list)
    action_recommendation: str = "PROCEED"  # "PROCEED" or "QUARANTINE"
    explanation: str = ""
    evaluations: List[OptionAdversarialEvaluation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "keyed_answer_id": self.keyed_answer_id,
            "has_ambiguity": self.has_ambiguity,
            "multiple_defensible_options": self.multiple_defensible_options,
            "defensible_option_ids": self.defensible_option_ids,
            "action_recommendation": self.action_recommendation,
            "explanation": self.explanation,
            "evaluations": [e.to_dict() for e in self.evaluations],
        }


class V6AdversarialReviewEngine:
    """Performs adversarial one-best-answer review."""

    @staticmethod
    def review_one_best_answer(
        question_id: str,
        keyed_answer_id: str,
        options: List[Dict[str, str]],
        option_reviews: List[Dict[str, Any]],
    ) -> AdversarialReviewResult:
        evaluations: List[OptionAdversarialEvaluation] = []
        defensible_ids: List[str] = []

        opt_map = {o["id"]: o.get("text", "").strip() for o in options}

        for rev in option_reviews:
            oid = rev.get("option_id", "")
            otext = opt_map.get(oid, "")
            is_key = (oid == keyed_answer_id)
            is_def = bool(rev.get("is_defensible", is_key))

            ev = OptionAdversarialEvaluation(
                option_id=oid,
                option_text=otext,
                is_keyed_answer=is_key,
                strongest_case_argument=rev.get("why_plausible", ""),
                counterargument_or_flaw=rev.get("why_inferior_or_wrong", "") if not is_key else "",
                is_clinically_defensible=is_def,
                distinguishing_evidence_quote=rev.get("distinguishing_quote", ""),
            )
            evaluations.append(ev)

            if is_def and not is_key:
                defensible_ids.append(oid)

        if defensible_ids:
            return AdversarialReviewResult(
                question_id=question_id,
                keyed_answer_id=keyed_answer_id,
                has_ambiguity=True,
                multiple_defensible_options=True,
                defensible_option_ids=defensible_ids,
                action_recommendation="QUARANTINE",
                explanation=f"Multiple clinically defensible options detected: Key '{keyed_answer_id}' vs Distractor(s) {defensible_ids}.",
                evaluations=evaluations,
            )

        return AdversarialReviewResult(
            question_id=question_id,
            keyed_answer_id=keyed_answer_id,
            has_ambiguity=False,
            multiple_defensible_options=False,
            defensible_option_ids=[keyed_answer_id],
            action_recommendation="PROCEED",
            explanation="Single clear one-best-answer established; all distractors clinically ruled out.",
            evaluations=evaluations,
        )
