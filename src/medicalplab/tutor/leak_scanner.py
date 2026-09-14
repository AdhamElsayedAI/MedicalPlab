"""Pre-submission answer leakage detection scanner."""
from __future__ import annotations

import re
from typing import Any
from medicalplab.stage_b.evidence_policy import normalize


LEAK_PATTERNS = [
    r"\b(?:the\s+)?(?:correct\s+)?answer\s+is\s+(?:option\s+|choice\s+)?([A-E])\b",
    r"\b(?:option|choice)\s+([A-E])\s+(?:is\s+correct|is\s+the\s+answer)\b",
    r"\bselect\s+(?:option\s+|choice\s+)?([A-E])\b",
    r"\b(?:choose|pick)\s+(?:option\s+|choice\s+)?([A-E])\b",
    r"\bthe\s+correct\s+(?:option|choice|answer)\b",
]


class AnswerLeakScanner:
    """Scans tutor output for premature disclosure of University question answers."""

    def __init__(self) -> None:
        self._leak_res = [re.compile(p, re.IGNORECASE) for p in LEAK_PATTERNS]

    def _tokenize(self, text: str) -> set[str]:
        words = re.findall(r"\b[a-zA-Z0-9-]+\b", normalize(text))
        return {w for w in words if len(w) >= 3}

    def _jaccard_similarity(self, s1: str, s2: str) -> float:
        t1 = self._tokenize(s1)
        t2 = self._tokenize(s2)
        if not t1 or not t2:
            return 0.0
        return len(t1.intersection(t2)) / len(t1.union(t2))

    def scan_for_leaks(
        self,
        generated_dict: dict[str, Any],
        question: dict[str, Any] | None = None,
    ) -> tuple[bool, str | None]:
        """Scan generated dictionary for direct answer leaks or high similarity to official explanation.

        Returns (True, reason) if leak is detected, or (False, None) if clean.
        """
        # Aggregate all text from generated response
        text_parts = []
        for k in ["message", "socratic_question", "hints", "misconception", "mechanistic_explanation", "revision_summary"]:
            val = generated_dict.get(k)
            if isinstance(val, str):
                text_parts.append(val)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict) and "why_incorrect" in item:
                        text_parts.append(str(item["why_incorrect"]))

        combined_text = " ".join(text_parts)
        norm_combined = normalize(combined_text)

        # 1. Regex indicator detection
        for pat in self._leak_res:
            match = pat.search(combined_text)
            if match:
                return True, f"DIRECT_ANSWER_PATTERN_MATCHED: '{match.group(0)}'"

        if not question:
            return False, None

        correct_opt = question.get("correct_answer")
        options = question.get("options", {})
        correct_text = options.get(correct_opt, "") if correct_opt and isinstance(options, dict) else ""
        explanation = question.get("explanation", "")

        # 2. Check if the model explicitly names "Option {correct_opt}"
        if correct_opt:
            specific_pat = re.compile(rf"\b(?:option|choice)\s+{correct_opt}\b", re.IGNORECASE)
            if specific_pat.search(combined_text):
                return True, f"EXPLICIT_CORRECT_OPTION_LETTER_LEAK: '{correct_opt}'"

        # 3. Check verbatim match of full correct answer text if sufficiently distinct
        if correct_text and len(correct_text.strip()) > 10:
            norm_correct = normalize(correct_text)
            # If the complete correct option string appears verbatim as a stand-alone assertion
            if f" {norm_correct} " in f" {norm_combined} ":
                # Verify if it's accompanied by giveaway phrasing
                giveaway = re.search(rf"\b(?:is|means|select)\s+{re.escape(norm_correct)}\b", norm_combined)
                if giveaway:
                    return True, f"VERBATIM_CORRECT_OPTION_GIVEAWAY: '{correct_text}'"

        # 4. Check high Jaccard similarity with the question's official explanation
        if explanation:
            sim = self._jaccard_similarity(combined_text, explanation)
            if sim > 0.65:
                return True, f"HIGH_EXPLANATION_TOKEN_OVERLAP (Jaccard: {sim:.2f})"

        return False, None
