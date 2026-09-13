"""V6 Numeric & Specificity Monotonicity Engine.

Enforces:
1. Specificity Monotonicity:
   Specificity(Evidence) >= Specificity(Claim) >= Specificity(Answer).
   Broad evidence (e.g. "Offer a CCB") cannot ground specific drug/dose/frequency
   claims (e.g. "Amlodipine 5 mg once daily").
2. Numeric & Unit Exactness:
   Values, ranges, units, comparison operators (<, <=, >, >=, =), drug identity, route,
   frequency, timing, and population must align without semantic discrepancy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ClaimSupportStatus(str, Enum):
    DIRECT_SUPPORT = "DIRECT_SUPPORT"
    DETERMINISTIC_DERIVATION = "DETERMINISTIC_DERIVATION"
    CLINICAL_INTERPRETATION_REQUIRED = "CLINICAL_INTERPRETATION_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    CONFLICTING = "CONFLICTING"
    UNCERTAIN = "UNCERTAIN"


class EntityGateStatus(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    SAFE_EQUIVALENT_CONVERSION = "SAFE_EQUIVALENT_CONVERSION"
    MISSING_IN_EVIDENCE = "MISSING_IN_EVIDENCE"
    VALUE_MISMATCH = "VALUE_MISMATCH"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    OPERATOR_MISMATCH = "OPERATOR_MISMATCH"
    RANGE_MISMATCH = "RANGE_MISMATCH"
    DRUG_MISMATCH = "DRUG_MISMATCH"
    ROUTE_MISMATCH = "ROUTE_MISMATCH"
    FREQUENCY_MISMATCH = "FREQUENCY_MISMATCH"
    TIMING_MISMATCH = "TIMING_MISMATCH"
    POPULATION_MISMATCH = "POPULATION_MISMATCH"
    ANSWER_SPECIFICITY_UNSUPPORTED = "ANSWER_SPECIFICITY_UNSUPPORTED"


@dataclass
class ClinicalEntitySpec:
    drug: Optional[str] = None
    drug_class: Optional[str] = None
    numeric_value: Optional[float] = None
    numeric_unit: Optional[str] = None
    comparator: Optional[str] = None  # "<", "<=", ">", ">=", "="
    numeric_range: Optional[Tuple[float, float]] = None
    route: Optional[str] = None  # "IV", "oral", "IM", "sublingual", "IO"
    frequency: Optional[str] = None  # "once daily", "twice daily", "every 3-5 minutes"
    duration: Optional[str] = None  # "16 hours", "3 months", "12 months"
    population: Optional[str] = None  # "adult", "pediatric", "elderly"
    vital_thresholds: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.numeric_value is not None:
            try:
                self.numeric_value = float(self.numeric_value)
            except (ValueError, TypeError):
                self.numeric_value = None
        if self.numeric_range is not None:
            try:
                self.numeric_range = (float(self.numeric_range[0]), float(self.numeric_range[1]))
            except (ValueError, TypeError, IndexError):
                self.numeric_range = None


@dataclass
class EntityComparisonResult:
    status: EntityGateStatus
    passes: bool
    reasons: List[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "passes": self.passes,
            "reasons": self.reasons,
            "explanation": self.explanation,
        }


def safe_float(v: Any) -> Optional[float]:
    """Safely convert any numeric value or string to float."""
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def normalize_unit(u: Optional[str]) -> Optional[str]:
    """Standardize clinical unit representations."""
    if not u:
        return None
    u_clean = u.strip().lower()
    mapping = {
        "mmhg": "mmHg",
        "kpa": "kPa",
        "mg": "mg",
        "milligrams": "mg",
        "mcg": "mcg",
        "micrograms": "mcg",
        "ug": "mcg",
        "g": "g",
        "grams": "g",
        "ml/kg": "mL/kg",
        "ml": "mL",
        "cm": "cm",
        "cmh2o": "cmH2O",
        "breaths/min": "breaths/min",
        "bpm": "bpm",
        "beats/min": "bpm",
        "%": "%",
        "percent": "%",
        "mmol/l": "mmol/L",
        "hours": "hours",
        "months": "months",
        "ratio": "ratio",
    }
    return mapping.get(u_clean, u.strip())


class V6NumericSpecificityEngine:
    """Evaluates specificity monotonicity and numeric exactness."""

    @staticmethod
    def extract_entities_from_text(text: str) -> ClinicalEntitySpec:
        """Heuristic entity extractor from clinical text."""
        spec = ClinicalEntitySpec()
        text_lower = text.lower()

        # Drug and drug classes
        common_drugs = [
            "amlodipine", "ramipril", "lisinopril", "losartan", "bendroflumethiazide",
            "spironolactone", "bisoprolol", "metoprolol", "atenolol", "diltiazem", "verapamil",
            "adrenaline", "epinephrine", "atropine", "amiodarone", "digoxin", "adenosine",
            "apixaban", "rivaroxaban", "edoxaban", "dabigatran", "warfarin",
            "salbutamol", "ipratropium", "tiotropium", "salmeterol", "formoterol",
            "prednisolone", "hydrocortisone", "dexamethasone",
            "amoxicillin", "clarithromycin", "doxycycline", "co-amoxiclav", "ceftriaxone",
            "norepinephrine", "noradrenaline", "dobutamine", "dopamine",
            "pirfenidone", "nintedanib", "furosemide",
        ]
        for d in common_drugs:
            if re.search(r"\b" + re.escape(d) + r"\b", text_lower):
                spec.drug = d.capitalize()
                break

        classes = {
            "calcium-channel blocker": "CCB",
            "calcium channel blocker": "CCB",
            "ccb": "CCB",
            "ace inhibitor": "ACEi",
            "acei": "ACEi",
            "angiotensin receptor blocker": "ARB",
            "arb": "ARB",
            "beta-blocker": "Beta-blocker",
            "thiazide": "Thiazide-like diuretic",
            "vasopressor": "Vasopressor",
            "inotrope": "Inotrope",
            "doac": "DOAC",
            "anticoagulant": "Anticoagulation",
            "corticosteroid": "Corticosteroid",
            "antifibrotic": "Antifibrotic",
        }
        for k, v in classes.items():
            if k in text_lower:
                spec.drug_class = v
                break

        # Numbers and units
        m_num = re.search(r"\b(\d+(?:\.\d+)?)\s*(mg|mcg|micrograms|g|kpa|mmhg|ml/kg|cmh2o|cm|breaths/min|bpm|beats/min|%|mmol/l)\b", text_lower)
        if m_num:
            spec.numeric_value = safe_float(m_num.group(1))
            spec.numeric_unit = normalize_unit(m_num.group(2))

        # Ranges
        m_range = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(mg|mcg|kpa|mmhg|ml/kg|cm|breaths/min|bpm|%)\b", text_lower)
        if m_range:
            low = safe_float(m_range.group(1))
            high = safe_float(m_range.group(2))
            if low is not None and high is not None:
                spec.numeric_range = (low, high)
                spec.numeric_unit = normalize_unit(m_range.group(3))

        # Comparators
        if "<=" in text or "≤" in text or "less than or equal" in text:
            spec.comparator = "<="
        elif ">=" in text or "≥" in text or "greater than or equal" in text or "at least" in text:
            spec.comparator = ">="
        elif "<" in text or "less than" in text:
            spec.comparator = "<"
        elif ">" in text or "greater than" in text or "more than" in text:
            spec.comparator = ">"
        elif "=" in text:
            spec.comparator = "="

        # Route
        for r in ["oral", "iv", "im", "io", "sublingual", "inhaled"]:
            if re.search(r"\b" + r + r"\b", text_lower):
                spec.route = r.upper()
                break

        # Frequency
        if "once daily" in text_lower:
            spec.frequency = "once daily"
        elif "twice daily" in text_lower:
            spec.frequency = "twice daily"
        elif "every 3-5 minutes" in text_lower or "every 3 to 5 minutes" in text_lower:
            spec.frequency = "every 3-5 minutes"

        return spec

    @staticmethod
    def compare_entities(
        claim_spec: ClinicalEntitySpec,
        evidence_text: str,
        answer_text: Optional[str] = None,
        claim_text: Optional[str] = None,
    ) -> EntityComparisonResult:
        """Evaluate specificity monotonicity, exact entity match, claim-answer concordance, and grounding."""
        reasons: List[str] = []
        ev_lower = evidence_text.lower()
        ev_spec = V6NumericSpecificityEngine.extract_entities_from_text(evidence_text)

        # 1. Answer Specificity & Concordance Gate (Specificity Monotonicity)
        if answer_text:
            ans_lower = answer_text.lower()
            ans_spec = V6NumericSpecificityEngine.extract_entities_from_text(answer_text)

            # Specific drug vs class
            if ans_spec.drug and not ev_spec.drug:
                reasons.append(
                    f"ANSWER_SPECIFICITY_UNSUPPORTED: Answer specifies drug '{ans_spec.drug}' "
                    f"but evidence only provides class guidance ('{ev_spec.drug_class or 'class'}')."
                )

            # Drug class present in answer but missing in evidence
            if ans_spec.drug_class and not ev_spec.drug_class and ans_spec.drug_class.lower() not in ev_lower:
                reasons.append(
                    f"ANSWER_SPECIFICITY_UNSUPPORTED: Answer specifies drug class '{ans_spec.drug_class}' "
                    f"which is absent in evidence span."
                )

            # Numeric dose/value present in answer but missing in evidence
            if ans_spec.numeric_value is not None and ev_spec.numeric_value is None and ev_spec.numeric_range is None:
                reasons.append(
                    f"ANSWER_SPECIFICITY_UNSUPPORTED: Answer specifies numeric dose/value '{ans_spec.numeric_value}' "
                    f"which is completely absent in evidence span."
                )

            # Claim-Answer Concordance Check
            if claim_text:
                clm_lower = claim_text.lower()
                # Stop words to exclude when checking substantive domain overlap
                stop_words = {
                    "this", "that", "with", "from", "what", "most", "appropriate", "first", "line",
                    "step", "therapy", "treatment", "management", "patient", "patients", "recommended",
                    "indicate", "indicated", "gives", "prescribe", "prescribed", "daily", "dose",
                    "administration", "administer", "only", "should", "could", "would", "take",
                    "taken", "offer", "routine", "routinely", "people", "adults", "initial", "oral",
                }
                ans_tokens = {w for w in re.findall(r"\b[a-z]{4,}\b", ans_lower) if w not in stop_words}
                clm_tokens = {w for w in re.findall(r"\b[a-z]{4,}\b", clm_lower) if w not in stop_words}

                # Check if answer has substantive clinical keywords and zero overlap with claim
                if ans_tokens and clm_tokens and not (ans_tokens & clm_tokens):
                    reasons.append(
                        f"CLAIM_ANSWER_MISMATCH: Claim terms ({', '.join(sorted(clm_tokens)[:3])}) do not substantiate "
                        f"keyed answer option terms ({', '.join(sorted(ans_tokens)[:3])})."
                    )

        # 2. Claim-Evidence Semantic Grounding (Disparate Topic Filter)
        if claim_text:
            clm_lower = claim_text.lower()
            domain_stop_words = {
                "this", "that", "with", "from", "what", "most", "appropriate", "first", "line",
                "step", "therapy", "treatment", "management", "patient", "patients", "recommended",
                "indicate", "indicated", "gives", "prescribe", "prescribed", "daily", "dose",
                "administration", "administer", "only", "should", "could", "would", "take",
                "taken", "offer", "routine", "routinely", "people", "adults", "initial", "causes",
                "associated", "clinical", "hospital", "guideline", "guidelines", "following",
            }
            # Identify core clinical nouns/terms in claim
            clm_substantive = [w for w in re.findall(r"\b[a-z]{4,}\b", clm_lower) if w not in domain_stop_words]
            if clm_substantive:
                # Find how many substantive claim words appear in the evidence text
                found_in_ev = [w for w in clm_substantive if w in ev_lower]
                # If key clinical nouns are present in claim but literally none or <20% appear in evidence
                if len(clm_substantive) >= 2 and len(found_in_ev) == 0:
                    reasons.append(
                        f"MISSING_IN_EVIDENCE: Core clinical concept(s) ({', '.join(clm_substantive[:3])}) "
                        f"from claim are completely absent in cited evidence quote (TOPIC_RELATED_BUT_CLAIM_UNSUPPORTED)."
                    )

        # 3. Claim Drug Match
        if claim_spec.drug:
            d_clean = claim_spec.drug.lower()
            if d_clean not in ev_lower:
                # Check if evidence mentions drug class
                if claim_spec.drug_class and claim_spec.drug_class.lower() in ev_lower:
                    reasons.append(
                        f"DRUG_SPECIFICITY_MISMATCH: Claim requires specific drug '{claim_spec.drug}' "
                        f"but evidence only supports class '{claim_spec.drug_class}'."
                    )
                else:
                    reasons.append(f"DRUG_MISMATCH: Required drug '{claim_spec.drug}' not found in evidence.")

        # 3. Numeric Value & Range Match
        if claim_spec.numeric_value is not None:
            c_val = claim_spec.numeric_value
            # Check exact string presence
            c_val_str = str(int(c_val)) if c_val.is_integer() else str(c_val)
            val_present = (
                re.search(r"\b" + re.escape(c_val_str) + r"\b", ev_lower) is not None
                or (ev_spec.numeric_value is not None and abs(ev_spec.numeric_value - c_val) < 1e-4)
                or (ev_spec.numeric_range and ev_spec.numeric_range[0] <= c_val <= ev_spec.numeric_range[1])
            )
            if not val_present:
                reasons.append(
                    f"VALUE_MISMATCH: Required numeric value {c_val} not supported by evidence "
                    f"(found val={ev_spec.numeric_value}, range={ev_spec.numeric_range})."
                )

        if claim_spec.numeric_range:
            low, high = claim_spec.numeric_range
            low_str = str(int(low)) if low.is_integer() else str(low)
            high_str = str(int(high)) if high.is_integer() else str(high)
            if not (re.search(r"\b" + re.escape(low_str) + r"\b", ev_lower) and re.search(r"\b" + re.escape(high_str) + r"\b", ev_lower)):
                reasons.append(f"RANGE_MISMATCH: Required range [{low}..{high}] not found in evidence.")

        # 4. Unit Match
        if claim_spec.numeric_unit:
            c_unit = normalize_unit(claim_spec.numeric_unit)
            e_unit = normalize_unit(ev_spec.numeric_unit)
            unit_str = claim_spec.numeric_unit.lower()
            unit_found = (
                unit_str in ev_lower
                if not unit_str.isalnum()
                else bool(re.search(r"\b" + re.escape(unit_str) + r"\b", ev_lower))
            )
            if e_unit and c_unit and c_unit.lower() != e_unit.lower():
                reasons.append(f"UNIT_MISMATCH: Unit '{c_unit}' does not match evidence unit '{e_unit}'.")
            elif not unit_found:
                reasons.append(f"UNIT_MISMATCH: Required unit '{claim_spec.numeric_unit}' missing in evidence.")

        # 5. Comparator Match
        if claim_spec.comparator:
            c_op = claim_spec.comparator
            e_op = ev_spec.comparator
            if e_op and c_op != e_op:
                # Allow safe <= inside < if stated
                reasons.append(f"OPERATOR_MISMATCH: Claim operator '{c_op}' does not match evidence operator '{e_op}'.")

        # 6. Route & Frequency Match
        if claim_spec.route and claim_spec.route.lower() not in ev_lower:
            reasons.append(f"ROUTE_MISMATCH: Required route '{claim_spec.route}' not found in evidence.")

        if claim_spec.frequency and claim_spec.frequency.lower() not in ev_lower:
            reasons.append(f"FREQUENCY_MISMATCH: Required frequency '{claim_spec.frequency}' not found in evidence.")

        if reasons:
            # Determine specific primary gate status
            primary_status = EntityGateStatus.MISSING_IN_EVIDENCE
            for r in reasons:
                for status_enum in EntityGateStatus:
                    if status_enum.name in r:
                        primary_status = status_enum
                        break
            return EntityComparisonResult(
                status=primary_status,
                passes=False,
                reasons=reasons,
                explanation="; ".join(reasons),
            )

        return EntityComparisonResult(
            status=EntityGateStatus.EXACT_MATCH,
            passes=True,
            reasons=[],
            explanation="All numeric, unit, drug, and specificity constraints verified against evidence.",
        )
