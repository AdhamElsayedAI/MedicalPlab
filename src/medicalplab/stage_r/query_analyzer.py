"""Deterministic clinical query analyzer for Stage-R.

Extracts medical intent and clinical entities without relying on non-deterministic models.
"""

import re
from typing import Tuple

from medicalplab.stage_b.models import require, strings
from medicalplab.stage_b.evidence_policy import normalize
from .models import QueryIntent


KNOWN_MEDICAL_ENTITIES = [
    # Cardiovascular
    "acute coronary syndrome",
    "myocardial infarction",
    "hypertension management",
    "essential hypertension",
    "blood pressure",
    "hypertension",
    "heart failure",
    "arrhythmias",
    "arrhythmia",
    "atrial fibrillation",
    "ace inhibitors",
    "beta blockers",
    "calcium channel blockers",
    "thiazide-like diuretics",
    "thiazide diuretics",
    "loop diuretics",
    "statins",

    # Endocrinology
    "diabetic ketoacidosis",
    "diabetes mellitus",
    "type 2 diabetes",
    "type 1 diabetes",
    "diabetes",
    "thyroid disorders",
    "hypothyroidism",
    "hyperthyroidism",
    "pheochromocytoma",
    "metformin",
    "insulin",

    # Respiratory
    "chronic obstructive pulmonary disease",
    "respiratory failure",
    "asthma",
    "copd",
    "pneumonia",
    "bronchospasm",

    # Renal
    "chronic kidney disease",
    "acute kidney injury",
    "renal failure",
    "proteinuria",
]

INTENT_RULES = [
    (
        QueryIntent.DOSAGE,
        [
            r"\b(?:dose|dosage|dosing|how\s+much|mg|mcg|milligram|tablets?|frequency|titrat\w*)\b",
        ],
    ),
    (
        QueryIntent.TREATMENT,
        [
            r"\b(?:treat|treatment|medication|drug|therapy|therapies|manage|management|pharmacolog\w*|prescrib\w*|first-line)\b",
        ],
    ),
    (
        QueryIntent.SYMPTOM,
        [
            r"\b(?:symptom|symptoms|sign|signs|presentation|manifest\w*|complain\w*|presents\s+with)\b",
        ],
    ),
    (
        QueryIntent.DISEASE,
        [
            r"\b(?:disease|condition|disorder|etiology|pathology|cause|risk\s+factor)\b",
        ],
    ),
    (
        QueryIntent.GUIDELINE,
        [
            r"\b(?:guideline|guidelines|who|nice|recommend\w*|protocol|algorithm|consensus)\b",
        ],
    ),
    (
        QueryIntent.EDUCATIONAL,
        [
            r"\b(?:teach|tutorial|explain|study|quiz|breakdown|mechanism|pathophysiology)\b",
        ],
    ),
    (
        QueryIntent.DEFINITION,
        [
            r"\b(?:define|definition|criteria|threshold|cutoff|what\s+is\b|what\s+are\b|meaning\s+of)\b",
        ],
    ),
]


def extract_entities(text: str) -> tuple[str, ...]:
    """Identify recognized medical entities from text in order of decreasing phrase length."""
    norm = normalize(text)
    detected = []
    # Match longest multi-word entities first to avoid premature single-word matches
    sorted_entities = sorted(KNOWN_MEDICAL_ENTITIES, key=len, reverse=True)

    for entity in sorted_entities:
        pattern = r"\b" + re.escape(entity) + r"\b"
        if re.search(pattern, norm):
            detected.append(entity)

    return tuple(detected)


def detect_intent(text: str) -> QueryIntent:
    """Classify clinical intent deterministically based on priority regex rules."""
    norm = normalize(text)
    for intent, patterns in INTENT_RULES:
        for p in patterns:
            if re.search(p, norm):
                return intent

    return QueryIntent.DEFINITION


def analyze_query(query: str) -> Tuple[QueryIntent, tuple[str, ...], str]:
    """Perform deterministic analysis on a query string.
    
    Returns (intent, detected_entities, normalized_query).
    """
    strings(query)
    norm = normalize(query)
    require(len(norm.strip()) > 0, "Query cannot be empty")

    intent = detect_intent(norm)
    entities = extract_entities(norm)

    return intent, entities, norm
