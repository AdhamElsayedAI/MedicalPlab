"""Intent classifier for Stage-D Medical Tutor.

Uses fast rule-based heuristics first, with optional LLM fallback for ambiguous queries.
"""

import json
import re

from medicalplab.stage_b.models import exact_keys, strict_json
from medicalplab.stage_b.evidence_policy import normalize
from .models import TutorMode
from .prompts import INTENT_CLASSIFIER_PROMPT


CASE_PATTERNS = [
    r"\b\d{1,3}\s*[-–]?\s*year\s*[-–]?\s*old\b",
    r"\b\d{1,3}\s*(?:yo|y/o)\b",
    r"\bpatient\s+(?:presents|has|is\s+a|admitted|complains|with)\b",
    r"\bclinical\s+(?:case|scenario|vignette)\b",
    r"\b(?:bp|blood\s+pressure)\s+(?:of\s+)?\d{2,3}/\d{2,3}\b",
    r"\bnext\s+step\s+in\s+management\b",
    r"\bfor\s+this\s+patient\b",
    r"\bmanagement\s+of\s+this\s+case\b",
]

TEACHING_PATTERNS = [
    r"\bteach\s+me\b",
    r"\bwalk\s+me\s+through\b",
    r"\bstep\s*[-–]?\s*by\s*[-–]?\s*step\b",
    r"\btutorial\b",
    r"\bstudy\s+guide\b",
    r"\bquiz\s+me\b",
    r"\btest\s+my\s+knowledge\b",
    r"\bhow\s+should\s+i\s+approach\b",
    r"\bguide\s+me\s+through\b",
    r"\bpedagogical\b",
    r"\bbreak\s+(?:this\s+)?down\s+for\s+a\s+student\b",
]

EXPLANATION_PATTERNS = [
    r"\bwhat\s+is\b",
    r"\bwhy\s+is\b",
    r"\bhow\s+is\b",
    r"\bwhat\s+(?:does|do)\s+the\s+guideline\b",
    r"\bexplain\b",
    r"\bdefinition\s+of\b",
    r"\bcriteria\s+(?:for|to|used)\b",
    r"\bcan\s+(?:you|we)\s+define\b",
    r"\bis\s+.*?\s+(?:considered|defined|classified)\b",
]


def rule_based_intent(query: str, context: str | None = None) -> TutorMode | None:
    """Classify query intent using regex patterns. Returns None if ambiguous."""
    full_text = normalize(f"{query} {context or ''}")

    # Check case_discussion first (patient findings are most distinct)
    for pattern in CASE_PATTERNS:
        if re.search(pattern, full_text):
            return TutorMode.CASE_DISCUSSION

    # Check teaching requests next
    for pattern in TEACHING_PATTERNS:
        if re.search(pattern, full_text):
            return TutorMode.TEACHING

    # Check explanation questions
    for pattern in EXPLANATION_PATTERNS:
        if re.search(pattern, full_text):
            return TutorMode.EXPLANATION

    return None


def classify_intent(
    query: str,
    context: str | None = None,
    backend=None,
) -> TutorMode:
    """Classify query intent with rule-based heuristics first, then optional LLM fallback."""
    # 1. Fast rule-based check
    mode = rule_based_intent(query, context)
    if mode is not None:
        return mode

    # 2. LLM fallback if backend available
    if backend is not None and hasattr(backend, "generate"):
        try:
            payload = json.dumps(
                {"query": query, "context": context or ""},
                ensure_ascii=False,
            )
            raw = backend.generate(INTENT_CLASSIFIER_PROMPT, payload)
            if isinstance(raw, dict) and "text" in raw:
                obj = strict_json(raw["text"])
                exact_keys(obj, ["mode"])
                target_mode = str(obj["mode"]).strip().lower()
                if target_mode in {m.value for m in TutorMode}:
                    return TutorMode(target_mode)
        except Exception:
            # If backend or parse fails, gracefully fall back to default
            pass

    # 3. Default fallback
    return TutorMode.EXPLANATION
