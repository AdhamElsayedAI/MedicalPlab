"""Extensible Intelligence Router for Stage-F.

Classifies incoming student interactions into platform intents and routes them to appropriate subsystems.
"""

import re
from typing import Sequence

from medicalplab.stage_b.models import require, strings
from medicalplab.stage_b.evidence_policy import normalize
from .models import PlatformIntent, SessionContext


DEFAULT_ROUTER_PATTERNS: list[tuple[PlatformIntent, list[str]]] = [
    (
        PlatformIntent.EXAM,
        [
            r"\b(?:mock\s+exam|practice\s+exam|timed\s+test|exam\s+mode|start\s+exam|take\s+(?:an\s+)?exam|plab\s+exam|test\s+session)\b",
        ],
    ),
    (
        PlatformIntent.CASE_SIMULATION,
        [
            r"\b(?:simulate\s+(?:a\s+)?patient|case\s+simulation|clinical\s+vignette|case\s+study|simulate\s+case|patient\s+scenario|vignette\s+simulation)\b",
            r"\bpatient\s+presents\s+with\b",
        ],
    ),
    (
        PlatformIntent.LEARNING_ANALYSIS,
        [
            r"\b(?:learning\s+analysis|my\s+progress|my\s+performance|weak\s+topics|show\s+weaknesses|learning\s+report|how\s+am\s+i\s+doing|knowledge\s+gaps|study\s+plan|curriculum\s+review)\b",
        ],
    ),
    (
        PlatformIntent.ASSESSMENT,
        [
            r"\b(?:quiz\s+me|test\s+me|practice\s+question|generate\s+questions?|give\s+me\s+a\s+question|mcqs?|assessment|check\s+my\s+knowledge)\b",
        ],
    ),
    (
        PlatformIntent.TEACHING,
        [
            r"\b(?:teach\s+me|walk\s+me\s+through|explain|tutorial|how\s+to\s+diagnose|treatment\s+protocol|guideline\s+steps|study\s+guide|what\s+is|what\s+are)\b",
        ],
    ),
]


class IntelligenceRouter:
    """Extensible multi-intent classifier and platform router."""

    def __init__(self, custom_rules: Sequence[tuple[PlatformIntent, list[str]]] | None = None):
        self.rules: list[tuple[PlatformIntent, list[str]]] = list(DEFAULT_ROUTER_PATTERNS)
        if custom_rules:
            for intent, patterns in custom_rules:
                self.register_rule(intent, patterns)

    def register_rule(self, intent: PlatformIntent, patterns: Sequence[str]) -> None:
        """Register custom routing patterns for an intent."""
        require(isinstance(intent, PlatformIntent), f"Invalid intent: {intent}")
        require(isinstance(patterns, (list, tuple)), "patterns must be a list or tuple")
        self.rules.insert(0, (intent, list(patterns)))

    def classify_intent(
        self,
        query: str,
        session: SessionContext | None = None,
    ) -> PlatformIntent:
        """Classify user query into PlatformIntent."""
        strings(query)
        norm = normalize(query)
        require(len(norm.strip()) > 0, "Query cannot be empty")

        for intent, patterns in self.rules:
            for p in patterns:
                if re.search(p, norm):
                    return intent

        # Context-aware fallback: if session has a learning objective, default to TEACHING
        if session and "exam" in session.learning_objective.lower():
            return PlatformIntent.EXAM

        return PlatformIntent.TEACHING

    def extract_topic_hint(self, query: str) -> str | None:
        """Extract medical topic mentioned in query, if present."""
        norm = normalize(query)
        candidates = [
            "hypertension management",
            "essential hypertension",
            "blood pressure",
            "hypertension",
            "diabetes mellitus",
            "diabetic ketoacidosis",
            "diabetes",
            "acute coronary syndrome",
            "myocardial infarction",
            "heart failure",
            "arrhythmias",
            "arrhythmia",
            "asthma",
            "copd",
            "chronic kidney disease",
            "acute kidney injury",
            "pneumonia",
        ]
        for c in candidates:
            if re.search(r"\b" + re.escape(c) + r"\b", norm):
                return c.title()
        return None
