"""
MedicalPlab Renal V7 — Auditable Renal Query Canonicalizer
=========================================================
Implements deterministic, auditable query canonicalization for undergraduate renal education:
1. Acronym expansion and preservation
2. British/American spelling unification
3. Number, comparator, and unit preservation
4. Drug and disease entity recognition
5. Strict negation preservation (zero polarity loss)
6. Controlled, bounded query rewrite for multi-channel retrieval
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class RenalCanonicalizationResult:
    original_query: str
    canonical_query: str
    controlled_rewrite: str
    detected_entities: list[str] = field(default_factory=list)
    has_negation: bool = False
    transformations: list[str] = field(default_factory=list)


# 1. Acronym Dictionary (strict word boundary matching)
RENAL_ACRONYM_MAP: list[tuple[str, str]] = [
    (r"\bAKI\b", "acute kidney injury (AKI)"),
    (r"\bCKD\b", "chronic kidney disease (CKD)"),
    (r"\beGFR\b", "estimated glomerular filtration rate (eGFR)"),
    (r"\bGFR\b", "glomerular filtration rate (GFR)"),
    (r"\bRAAS\b", "renin-angiotensin-aldosterone system (RAAS)"),
    (r"\bADH\b", "antidiuretic hormone (ADH / vasopressin)"),
    (r"\bUTI\b", "urinary tract infection (UTI)"),
    (r"\bRRT\b", "renal replacement therapy (RRT)"),
    (r"\bESRD\b", "end-stage renal disease (ESRD / ESKD)"),
    (r"\bESKD\b", "end-stage kidney disease (ESKD)"),
    (r"\bFSGS\b", "focal segmental glomerulosclerosis (FSGS)"),
    (r"\bMCD\b", "minimal change disease (MCD)"),
    (r"\bMN\b", "membranous nephropathy (MN)"),
    (r"\bMPGN\b", "membranoproliferative glomerulonephritis (MPGN)"),
    (r"\bADPKD\b", "autosomal dominant polycystic kidney disease (ADPKD)"),
    (r"\bARPKD\b", "autosomal recessive polycystic kidney disease (ARPKD)"),
    (r"\bRTA\b", "renal tubular acidosis (RTA)"),
    (r"\bATN\b", "acute tubular necrosis (ATN)"),
    (r"\bAIN\b", "acute interstitial nephritis (AIN)"),
    (r"\bHUS\b", "hemolytic uremic syndrome (HUS)"),
    (r"\bTTP\b", "thrombotic thrombocytopenic purpura (TTP)"),
    (r"\bANCA\b", "anti-neutrophil cytoplasmic antibody (ANCA)"),
    (r"\bGBM\b", "glomerular basement membrane (GBM)"),
    (r"\banti-GBM\b", "anti-glomerular basement membrane (anti-GBM)"),
    (r"\bPLA2R\b", "phospholipase A2 receptor (PLA2R)"),
    (r"\bENaC\b", "epithelial sodium channel (ENaC)"),
    (r"\bROMK\b", "renal outer medullary potassium channel (ROMK)"),
    (r"\bNKCC2\b", "Na-K-2Cl cotransporter (NKCC2)"),
    (r"\bNCC\b", "Na-Cl cotransporter (NCC)"),
    (r"\bSGLT2\b", "sodium-glucose cotransporter 2 (SGLT2)"),
    (r"\bSGLT1\b", "sodium-glucose cotransporter 1 (SGLT1)"),
    (r"\bACR\b", "albumin-to-creatinine ratio (ACR)"),
    (r"\bPCR\b", "protein-to-creatinine ratio (PCR)"),
    (r"\bKDIGO\b", "Kidney Disease Improving Global Outcomes (KDIGO)"),
    (r"\bAVF\b", "arteriovenous fistula (AVF)"),
    (r"\bAVG\b", "arteriovenous graft (AVG)"),
]

# 2. British/American Spelling Pairs (normalize to canonical and dual representation)
SPELLING_NORMALIZATION: list[tuple[str, str, str]] = [
    (r"\bhyperkalemia\b", r"\bhyperkalaemia\b", "hyperkalaemia"),
    (r"\bhypokalemia\b", r"\bhypokalaemia\b", "hypokalaemia"),
    (r"\bhematuria\b", r"\bhaematuria\b", "haematuria"),
    (r"\bhemolysis\b", r"\bhaemolysis\b", "haemolysis"),
    (r"\bhypovolemia\b", r"\bhypovolaemia\b", "hypovolaemia"),
    (r"\bhypervolemia\b", r"\bhypervolaemia\b", "hypervolaemia"),
    (r"\bhyperlipidemia\b", r"\bhyperlipidaemia\b", "hyperlipidaemia"),
    (r"\banemia\b", r"\banaemia\b", "anaemia"),
    (r"\bedema\b", r"\boedema\b", "oedema"),
    (r"\buremia\b", r"\buraemia\b", "uraemia"),
    (r"\bdialyzer\b", r"\bdialyser\b", "dialyser"),
    (r"\bhemodialysis\b", r"\bhaemodialysis\b", "haemodialysis"),
    (r"\bhemofiltration\b", r"\bhaemofiltration\b", "haemofiltration"),
]

# 3. Units and Cutoff Expressions
UNIT_STANDARDIZATION: list[tuple[str, str]] = [
    (r"\bml/min(?:/1\.73m\^?2)?\b", "mL/min/1.73m2"),
    (r"\bml/min\b", "mL/min"),
    (r"\bmg/mmol\b", "mg/mmol"),
    (r"\bmg/dl\b", "mg/dL"),
    (r"\bmmol/l\b", "mmol/L"),
    (r"\bmeq/l\b", "mEq/L"),
    (r"\bg/24h\b", "g/24 hours"),
    (r"\bg/day\b", "g/24 hours"),
    (r"\bmmhg\b", "mmHg"),
]

# 4. Comparator Normalization
COMPARATOR_MAP: list[tuple[str, str]] = [
    (r"\b(?:greater than or equal to|at least)\b", ">="),
    (r"\b(?:less than or equal to|at most)\b", "<="),
    (r"\b(?:greater than|above|exceeding)\b", ">"),
    (r"\b(?:less than|below|under)\b", "<"),
]

# 5. Strict Negation Terms
NEGATION_PATTERNS: list[str] = [
    r"\bnot\b",
    r"\bno\b",
    r"\bwithout\b",
    r"\babsence of\b",
    r"\bnon-",
    r"\bnegative for\b",
    r"\bdoes not\b",
    r"\blacks\b",
    r"\bcontraindicated\b",
]

# 6. Key Renal Clinical Entities for Intent Preservation
RENAL_CLINICAL_ENTITIES: list[str] = [
    "podocyte",
    "foot process effacement",
    "glomerular basement membrane",
    "mesangial matrix",
    "endothelin",
    "nephrin",
    "podocin",
    "c3 nephritic factor",
    "spike and dome",
    "tram-track",
    "crescentic",
    "muddy brown casts",
    "red blood cell casts",
    "dysmorphic red cells",
    "fractional excretion of sodium",
    "ramipril",
    "lisinopril",
    "losartan",
    "dapagliflozin",
    "empagliflozin",
    "furosemide",
    "spironolactone",
    "tacrolimus",
    "ciclosporin",
    "prednisolone",
    "methylprednisolone",
    "patiromer",
    "calcium resonium",
]


class RenalQueryCanonicalizer:
    """Auditable query normalizer and canonicalizer for undergraduate renal queries."""

    def __init__(self, include_rewrite: bool = True):
        self.include_rewrite = include_rewrite

    def canonicalize(self, query: str) -> RenalCanonicalizationResult:
        if not query or not query.strip():
            return RenalCanonicalizationResult(
                original_query=query,
                canonical_query="",
                controlled_rewrite="",
                detected_entities=[],
                has_negation=False,
                transformations=["empty_query"],
            )

        current = query.strip()
        transformations: list[str] = []

        # Step 1: Detect Negation (Strictly Preserved)
        has_negation = any(re.search(pat, current, flags=re.IGNORECASE) for pat in NEGATION_PATTERNS)
        if has_negation:
            transformations.append("negation_detected_and_preserved")

        # Step 2: Spelling Normalization
        for us_pat, uk_pat, canonical in SPELLING_NORMALIZATION:
            match_us = re.search(us_pat, current, flags=re.IGNORECASE)
            if match_us:
                current = re.sub(us_pat, canonical, current, flags=re.IGNORECASE)
                transformations.append(f"spelling_unification: {match_us.group(0)} -> {canonical}")

        # Step 3: Comparators & Units
        for pattern, replacement in COMPARATOR_MAP:
            match = re.search(pattern, current, flags=re.IGNORECASE)
            if match:
                current = re.sub(pattern, replacement, current, flags=re.IGNORECASE)
                transformations.append(f"comparator_normalized: {match.group(0)} -> {replacement}")

        for pattern, replacement in UNIT_STANDARDIZATION:
            match = re.search(pattern, current, flags=re.IGNORECASE)
            if match:
                current = re.sub(pattern, replacement, current, flags=re.IGNORECASE)
                transformations.append(f"unit_standardized: {match.group(0)} -> {replacement}")

        # Step 4: Acronym Expansion
        for pattern, replacement in RENAL_ACRONYM_MAP:
            match = re.search(pattern, current)
            if match and replacement.lower() not in current.lower():
                current = re.sub(pattern, replacement, current)
                transformations.append(f"acronym_expanded: {match.group(0)} -> {replacement}")

        # Clean spaces
        canonical_query = " ".join(current.split())

        # Step 5: Entity Recognition
        detected_entities = []
        for entity in RENAL_CLINICAL_ENTITIES:
            if re.search(r"\b" + re.escape(entity) + r"\b", canonical_query, flags=re.IGNORECASE):
                detected_entities.append(entity)

        # Step 6: Controlled Rewrite (for sparse/dense hybrid recall)
        # Adds alternative British/American spellings and keywords without altering logic
        rewrite_tokens = [canonical_query]
        for us_pat, uk_pat, canonical in SPELLING_NORMALIZATION:
            if re.search(r"\b" + re.escape(canonical) + r"\b", canonical_query, flags=re.IGNORECASE):
                # Add the alternate US spelling into the rewrite pool
                alt_term = us_pat.replace(r"\b", "")
                if alt_term not in canonical_query.lower():
                    rewrite_tokens.append(f"({alt_term})")

        controlled_rewrite = " ".join(rewrite_tokens)

        return RenalCanonicalizationResult(
            original_query=query,
            canonical_query=canonical_query,
            controlled_rewrite=controlled_rewrite,
            detected_entities=detected_entities,
            has_negation=has_negation,
            transformations=transformations,
        )


def canonicalize_query(query: str) -> RenalCanonicalizationResult:
    """Convenience helper function for single query canonicalization."""
    return RenalQueryCanonicalizer().canonicalize(query)
