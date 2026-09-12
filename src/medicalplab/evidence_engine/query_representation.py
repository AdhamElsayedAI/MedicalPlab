"""
MedicalPlab Shared Evidence Engine V2 — Clinical Query Representation
=====================================================================
Generates exactly three auditable representations per query:
1. Original Query: Untouched clinical vignette/question.
2. Canonical Query: Deterministic normalization of acronyms, spelling, units, and negation.
3. Neutral Retrieval Target: Concise evidence target without answer prediction or fact leakage.
"""

import re
from typing import Sequence

from medicalplab.evidence_engine.models import QueryRepresentation
from medicalplab.learn.renal_canonicalizer import RenalQueryCanonicalizer

# Stopwords and vignette fluff that should be stripped for the neutral target
VIGNETTE_FLUFF_PATTERNS = [
    r"\b(?:a\s+\d+[- ]year[- ]old\s+(?:man|woman|male|female|boy|girl|patient|individual))\b",
    r"\b(?:attends?\s+(?:his|her|the)?\s*(?:gp\s+surgery|emergency\s+department|clinic|hospital|outpatient))\b",
    r"\b(?:presents?\s+(?:to|with)?)\b",
    r"\b(?:complaining\s+of|history\s+of|past\s+medical\s+history)\b",
    r"\b(?:routine\s+health\s+check|follow[- ]up|review)\b",
    r"\b(?:which\s+of\s+the\s+following\s+is\s+the\s+most\s+appropriate\s+(?:initial\s+)?(?:treatment|investigation|management|step|diagnosis|pharmacological\s+treatment))\b",
    r"\b(?:according\s+to\s+UK\s+clinical\s+practice\s+guidelines?\s*(?:\([^)]*\))?)\b",
    r"\b(?:what\s+is\s+the\s+most\s+likely\s+diagnosis)\b",
    r"\b(?:what\s+is\s+the\s+best\s+next\s+step)\b",
    r"\b(?:what\s+is\s+the\s+mechanism\s+of\s+action\s+of)\b",
    r"\b(?:which\s+drug|which\s+medication|which\s+agent)\b",
    r"\b(?:on\s+examination|vital\s+signs\s+show|physical\s+exam\s+reveals)\b",
]

TARGET_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for", "with", "by",
    "from", "his", "her", "their", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "can", "could", "should", "would",
    "what", "which", "who", "whom", "this", "that", "these", "those", "patient",
    "following", "appropriate", "initial", "most", "likely", "best", "next", "step",
    "routine", "measurement", "confirmed", "confirms", "normal", "negative", "reveals"
}


class ClinicalQueryProcessor:
    """Deterministic, leakage-free 3-representation query builder."""

    def __init__(self):
        self._canonicalizer = RenalQueryCanonicalizer()

    def process(self, query: str) -> QueryRepresentation:
        """Process clinical vignette into exactly three representations."""
        orig = query.strip()

        # 1. Deterministic canonical query
        canon_res = self._canonicalizer.canonicalize(orig)
        canonical = canon_res.canonical_query

        # 2. Neutral retrieval target (leakage-free target distillation)
        neutral = self._distill_neutral_target(canonical, canon_res.has_negation)

        return QueryRepresentation(
            original_query=orig,
            canonical_query=canonical,
            neutral_target=neutral,
            has_negation=canon_res.has_negation,
            detected_entities=canon_res.detected_entities,
            transformations=canon_res.transformations,
        )

    def process_query(self, query: str) -> QueryRepresentation:
        """Alias for process()."""
        return self.process(query)

    def _distill_neutral_target(self, text: str, has_negation: bool) -> str:
        """Distill clinical vignette into concise evidence target without answer leakage."""
        cleaned = text

        # Strip standard vignette formulaic fluff
        for pat in VIGNETTE_FLUFF_PATTERNS:
            cleaned = re.sub(pat, " ", cleaned, flags=re.IGNORECASE)

        # Retain medical concepts, comparators, numbers, units, and negation
        tokens = re.findall(r"\b[a-zA-Z0-9_\-\+/<>=]+(?:\.[a-zA-Z0-9_\-\+/<>=]+)*\b", cleaned)
        filtered_tokens = []

        for t in tokens:
            t_lower = t.lower()
            if t_lower in TARGET_STOPWORDS and not re.search(r"\d", t):
                continue
            filtered_tokens.append(t)

        target_str = " ".join(filtered_tokens)
        target_str = re.sub(r"\s+", " ", target_str).strip()

        # If stripping was too aggressive, fallback to canonical query words
        if len(target_str) < 5:
            target_str = text[:150].strip()

        return target_str
