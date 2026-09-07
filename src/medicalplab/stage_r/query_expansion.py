"""Controlled medical query expansion layer for Stage-R.

Expands clinical queries using a strictly validated medical synonym ontology to prevent hallucination.
"""

from typing import Sequence

from medicalplab.stage_b.models import require, strings
from medicalplab.stage_b.evidence_policy import normalize
from .models import QueryIntent, RetrievalQuery
from .query_analyzer import analyze_query


CONTROLLED_SYNONYMS: dict[str, tuple[str, ...]] = {
    "hypertension": (
        "high blood pressure",
        "elevated blood pressure",
        "arterial hypertension",
        "blood pressure disorder",
    ),
    "hypertension management": (
        "blood pressure control",
        "antihypertensive therapy",
        "treatment of hypertension",
    ),
    "myocardial infarction": (
        "heart attack",
        "acute myocardial infarction",
        "coronary thrombosis",
    ),
    "acute coronary syndrome": (
        "unstable angina",
        "myocardial infarction",
        "acute coronary event",
    ),
    "heart failure": (
        "cardiac failure",
        "congestive heart failure",
        "chf",
    ),
    "arrhythmias": (
        "cardiac dysrhythmias",
        "irregular heartbeat",
        "arrhythmia",
    ),
    "arrhythmia": (
        "cardiac dysrhythmia",
        "irregular heart rhythm",
        "arrhythmias",
    ),
    "diabetes mellitus": (
        "type 2 diabetes",
        "hyperglycemia",
        "diabetic disorder",
    ),
    "diabetes": (
        "diabetes mellitus",
        "hyperglycemia",
        "high blood sugar",
    ),
    "diabetic ketoacidosis": (
        "dka",
        "diabetic acidosis",
        "ketoacidosis",
    ),
    "asthma": (
        "bronchial asthma",
        "reactive airway disease",
        "bronchospasm",
    ),
    "copd": (
        "chronic obstructive pulmonary disease",
        "chronic bronchitis",
        "emphysema",
    ),
    "chronic obstructive pulmonary disease": (
        "copd",
        "emphysema",
        "chronic bronchitis",
    ),
    "chronic kidney disease": (
        "ckd",
        "chronic renal failure",
        "chronic renal disease",
    ),
    "acute kidney injury": (
        "aki",
        "acute renal failure",
    ),
    "ace inhibitors": (
        "angiotensin converting enzyme inhibitors",
        "acei",
    ),
    "beta blockers": (
        "beta-adrenergic antagonists",
        "beta-blockers",
    ),
    "calcium channel blockers": (
        "ccb",
        "calcium antagonists",
    ),
    "statins": (
        "hmg-coa reductase inhibitors",
        "lipid-lowering therapy",
    ),
}


def get_synonyms(entity: str) -> tuple[str, ...]:
    """Retrieve controlled synonyms for an entity or an empty tuple if uncataloged."""
    return CONTROLLED_SYNONYMS.get(entity.strip().lower(), ())


def expand_query(
    raw_query: str,
    intent: QueryIntent | None = None,
    entities: Sequence[str] | None = None,
) -> RetrievalQuery:
    """Analyze query and expand with controlled medical synonyms."""
    strings(raw_query)

    if intent is None or entities is None:
        detected_intent, detected_entities, norm_query = analyze_query(raw_query)
        if intent is None:
            intent = detected_intent
        if entities is None:
            entities = detected_entities
    else:
        norm_query = normalize(raw_query)

    expanded: list[str] = []
    seen = set()

    for entity in entities:
        synonyms = get_synonyms(entity)
        for s in synonyms:
            s_clean = normalize(s)
            if s_clean not in seen and s_clean != norm_query:
                seen.add(s_clean)
                expanded.append(s_clean)

    return RetrievalQuery(
        raw_query=raw_query.strip(),
        normalized_query=norm_query,
        expanded_terms=tuple(expanded),
        intent=intent,
        entities=tuple(entities),
    )
