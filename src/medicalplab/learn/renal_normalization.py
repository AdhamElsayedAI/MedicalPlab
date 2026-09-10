"""Auditable renal medical terminology normalization layer."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RenalNormalizationTrace:
    original_query: str
    normalized_query: str
    transformations: list[str] = field(default_factory=list)


# Acronym expansions using strict word boundaries to avoid false substring matches
ACRONYM_EXPANSIONS = [
    (r"\bAKI\b", "acute kidney injury (AKI)"),
    (r"\bCKD\b", "chronic kidney disease (CKD)"),
    (r"\beGFR\b", "estimated glomerular filtration rate (eGFR)"),
    (r"\bGFR\b", "glomerular filtration rate (GFR)"),
    (r"\bRAAS\b", "renin-angiotensin-aldosterone system (RAAS)"),
    (r"\bADH\b", "antidiuretic hormone (ADH / vasopressin)"),
    (r"\bUTI\b", "urinary tract infection (UTI)"),
    (r"\bRRT\b", "renal replacement therapy (RRT)"),
    (r"\bESRD\b", "end-stage kidney disease (ESRD)"),
    (r"\bESKD\b", "end-stage kidney disease (ESKD)"),
    (r"\bENaC\b", "epithelial sodium channel (ENaC)"),
    (r"\bROMK\b", "renal outer medullary potassium channel (ROMK)"),
    (r"\bSGLT2\b", "sodium-glucose cotransporter 2 (SGLT2)"),
    (r"\bSGLT1\b", "sodium-glucose cotransporter 1 (SGLT1)"),
    (r"\bSGK1\b", "serum and glucocorticoid-regulated kinase 1 (SGK1)"),
    (r"\bACR\b", "albumin-to-creatinine ratio (ACR)"),
    (r"\bKDIGO\b", "Kidney Disease Improving Global Outcomes (KDIGO)"),
]

# Spelling unification (maps British/American variants to dual or canonical forms)
SPELLING_UNIFICATIONS = [
    (r"\bhyperkalemia\b", "hyperkalaemia"),
    (r"\bhemolysis\b", "haemolysis"),
    (r"\bhematuria\b", "haematuria"),
    (r"\bhypovolemia\b", "hypovolaemia"),
    (r"\bhyperlipidemia\b", "hyperlipidaemia"),
    (r"\banemia\b", "anaemia"),
    (r"\bedema\b", "oedema"),
]


def normalize_renal_query(query: str) -> RenalNormalizationTrace:
    """Normalize a renal education query with full traceability."""
    current = query
    transformations: list[str] = []

    # 1. Spelling standardizations
    for pattern, replacement in SPELLING_UNIFICATIONS:
        match = re.search(pattern, current, flags=re.IGNORECASE)
        if match:
            current = re.sub(pattern, replacement, current, flags=re.IGNORECASE)
            transformations.append(f"spelling: {match.group(0)} -> {replacement}")

    # 2. Acronym expansions
    for pattern, replacement in ACRONYM_EXPANSIONS:
        # Check if already expanded in query
        match = re.search(pattern, current, flags=re.IGNORECASE)
        if match and replacement.lower() not in current.lower():
            current = re.sub(pattern, replacement, current, flags=re.IGNORECASE)
            transformations.append(f"acronym: {match.group(0)} -> {replacement}")

    # Clean whitespace
    current = " ".join(current.split())
    return RenalNormalizationTrace(
        original_query=query,
        normalized_query=current,
        transformations=transformations,
    )
