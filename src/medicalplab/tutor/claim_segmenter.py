"""Proposition segmentation and classification across all generated tutor fields."""
from __future__ import annotations

import re
from typing import Any, Literal
from medicalplab.tutor.models import ExtractedProposition, PropositionCategory


# Domain terminology indicating substantive basic science / physiological factual content
PHYSIOLOGICAL_KEYWORDS = {
    "renin", "angiotensin", "angiotensinogen", "aldosterone", "ace", "at1r", "at2r",
    "gfr", "rbf", "filtration", "glomerular", "glomerulus", "podocyte", "podocytes",
    "slit", "diaphragm", "basement", "membrane", "gbm", "endothelial", "endothelium",
    "fenestrated", "fenestrations", "arteriole", "arterioles", "afferent", "efferent",
    "hydrostatic", "oncotic", "starling", "heparan", "sulfate", "proteoglycan",
    "tubule", "tubular", "nephron", "proximal", "distal", "collecting", "duct",
    "loop", "henle", "macula", "densa", "juxtaglomerular", "reabsorption", "secretion",
    "sodium", "potassium", "chloride", "bicarbonate", "osmolarity", "vasoconstriction",
    "vasodilation", "resistance", "cleave", "cleaves", "cleaved", "enzyme", "substrate",
    "protease", "peptide", "decapeptide", "octapeptide", "hormone", "receptor", "cortex",
    "medulla", "capillary", "capillaries", "permeability", "charge", "barrier", "anionic",
    "polyanionic", "albumin", "proteinuria", "albuminuria", "excretion", "clearance",
}

# Mechanistic/relational verb forms (including common inflections) that indicate an
# asserted physiological relationship, even when no PHYSIOLOGICAL_KEYWORDS term is present
# and even when the assertion is wrapped in a question, hint, or generic pedagogical framing.
MECHANISTIC_VERB_PATTERN = re.compile(
    r"\b("
    r"increase[sd]?|increasing|"
    r"decrease[sd]?|decreasing|"
    r"inhibit(?:s|ed|ing)?|"
    r"stimulat(?:es?|ed|ing)|"
    r"convert(?:s|ed|ing)?|"
    r"cleave[sd]?|cleaving|"
    r"regulat(?:es?|ed|ing)|"
    r"caus(?:es?|ed|ing)|"
    r"produc(?:es?|ed|ing)|"
    r"maintain(?:s|ed|ing)?|"
    r"interact(?:s|ed|ing)?|"
    r"leads?\s+to"
    r")\b",
    re.IGNORECASE,
)


PREMISE_MARKERS = re.compile(
    r"\b(?:given\s+that|knowing\s+that|recall(?:ing)?\s+that|since|because|note\s+that|assuming\s+that)\b",
    re.IGNORECASE,
)

CONVERSATIONAL_META_PATTERNS = [
    re.compile(r"^(?:welcome|hello|great\s+(?:work|question|observation)|let's\s+(?:think|explore|analyze|work)|let\s+us\s+(?:think|explore|analyze|work))\b", re.IGNORECASE),
    re.compile(r"^(?:to\s+(?:determine|find|answer|identify|approach|understand|trace))\b.*?\b(?:let's|let\s+us|think|consider|look|reflect)\b", re.IGNORECASE),
    re.compile(r"^(?:try\s+identifying|compare\s+each\s+option|revisit\s+your\s+course|what\s+do\s+you\s+already\s+know)\b", re.IGNORECASE),
    re.compile(r"^(?:what|which)\s+is\s+the\s+name\s+of\b", re.IGNORECASE),
    re.compile(r"^(?:i\s+couldn't\s+verify|no\s+verified\s+basic-science)\b", re.IGNORECASE),
]

DIRECTIONAL_HINT_PATTERNS = [
    re.compile(r"^(?:(?:Level|Hint|Tier|Step)\s*\d*[:.-]\s*)?(?:consider|think\s+(?:about|of)|focus\s+on|reflect\s+on|remember)\s+.*?\b(?:the\s+naming|the\s+name|the\s+clues?|what\s+precursor|which\s+precursor|the\s+plasma|a\s+suffix|substrate|denotes)\b", re.IGNORECASE),
]


def is_socratic_question(text: str) -> bool:
    cleaned = text.strip()
    return cleaned.endswith("?") or re.match(r"^(?:what|which|how|why|can\s+you|could\s+you|where|is\s+it|does|do)\b", cleaned, re.IGNORECASE) is not None


class PropositionSegmenter:
    """Extracts and classifies propositions across all generated fields."""

    def _split_into_sentences(self, text: str) -> list[str]:
        # Split on sentence boundaries while handling abbreviations
        raw_chunks = re.split(r"(?<=[.?!])\s+", text.strip())
        sentences = []
        for c in raw_chunks:
            c = c.strip()
            if c:
                sentences.append(c)
        return sentences

    def classify_segment(
        self,
        field_name: str,
        text: str,
    ) -> tuple[PropositionCategory, Literal["SUBSTANTIVE_FACTUAL", "NON_FACTUAL_PEDAGOGICAL_LANGUAGE"]]:
        """Explicitly distinguish between:
        1. factual medical claims (FACTUAL_CLAIM -> SUBSTANTIVE_FACTUAL)
        2. Socratic questions (SOCRATIC_QUESTION -> NON_FACTUAL_PEDAGOGICAL_LANGUAGE)
        3. educational hints (EDUCATIONAL_HINT -> NON_FACTUAL_PEDAGOGICAL_LANGUAGE)
        4. conversational/meta text (CONVERSATIONAL_META -> NON_FACTUAL_PEDAGOGICAL_LANGUAGE)

        Questions and conversational guidance are NOT verified as factual propositions.
        """
        cleaned = text.strip()
        lowered = cleaned.casefold()

        # 1. Pure conversational or meta guidance
        for pat in CONVERSATIONAL_META_PATTERNS:
            if pat.search(cleaned):
                if not PREMISE_MARKERS.search(cleaned):
                    return "CONVERSATIONAL_META", "NON_FACTUAL_PEDAGOGICAL_LANGUAGE"

        # 2. Socratic Questions:
        # Questions asking the learner to deduce an answer without asserting a declarative premise
        # are pedagogical inquiries, not factual medical assertions.
        if field_name == "socratic_question" or is_socratic_question(cleaned):
            if PREMISE_MARKERS.search(cleaned):
                return "FACTUAL_CLAIM", "SUBSTANTIVE_FACTUAL"
            return "SOCRATIC_QUESTION", "NON_FACTUAL_PEDAGOGICAL_LANGUAGE"

        # 3. Educational Hints:
        # Directional hints and hints field items directing learner attention.
        if field_name == "hints":
            if PREMISE_MARKERS.search(cleaned):
                return "FACTUAL_CLAIM", "SUBSTANTIVE_FACTUAL"
            return "EDUCATIONAL_HINT", "NON_FACTUAL_PEDAGOGICAL_LANGUAGE"

        for pat in DIRECTIONAL_HINT_PATTERNS:
            if pat.search(cleaned):
                if not PREMISE_MARKERS.search(cleaned):
                    return "EDUCATIONAL_HINT", "NON_FACTUAL_PEDAGOGICAL_LANGUAGE"

        # 4. Factual medical claims (keywords, units, mechanistic relationships)
        words = set(re.findall(r"\b[a-z0-9-]+\b", lowered))
        if words.intersection(PHYSIOLOGICAL_KEYWORDS):
            return "FACTUAL_CLAIM", "SUBSTANTIVE_FACTUAL"

        stemmed_words = {w[:-1] for w in words if w.endswith("s") and len(w) > 4}
        if stemmed_words.intersection(PHYSIOLOGICAL_KEYWORDS):
            return "FACTUAL_CLAIM", "SUBSTANTIVE_FACTUAL"

        if re.search(r"\b\d+(?:\.\d+)?\s*(?:mmhg|ml/min|%|kpa|mosm)\b", lowered):
            return "FACTUAL_CLAIM", "SUBSTANTIVE_FACTUAL"

        if MECHANISTIC_VERB_PATTERN.search(lowered):
            return "FACTUAL_CLAIM", "SUBSTANTIVE_FACTUAL"

        return "CONVERSATIONAL_META", "NON_FACTUAL_PEDAGOGICAL_LANGUAGE"

    def _is_substantive_factual(self, text: str, field_name: str = "") -> bool:
        _, classification = self.classify_segment(field_name, text)
        return classification == "SUBSTANTIVE_FACTUAL"

    def extract_declarative_core(self, text: str) -> str:
        """Strip conversational, interrogative, or hint framing to isolate the asserted medical claim."""
        cleaned = text.strip()
        cleaned = re.sub(r"^(?:Level|Hint|Tier|Step)\s*\d*[:.-]\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^(?:consider|think\s+about|recall|reflect\s+on|focus\s+on|remember)\s+(?:that\s+|how\s+|what\s+|which\s+)?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^(?:what|which|how|why)\s+(?:protein|substrate|enzyme|layer|structure|force|mechanism|factor)?\s*(?:does|is|are|cleaves|acts\s+upon)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.rstrip("?.!").strip()
        return cleaned

    def segment_field(self, field_name: str, field_value: Any, cited_ref: str | None = None) -> list[ExtractedProposition]:
        propositions: list[ExtractedProposition] = []
        if not field_value:
            return propositions

        texts_to_process: list[str] = []
        if isinstance(field_value, str):
            texts_to_process.append(field_value)
        elif isinstance(field_value, list):
            for item in field_value:
                if isinstance(item, str):
                    texts_to_process.append(item)
                elif isinstance(item, dict):
                    why = item.get("why_incorrect")
                    if why:
                        texts_to_process.append(str(why))

        prop_counter = 1
        for block in texts_to_process:
            sentences = self._split_into_sentences(block)
            for sent in sentences:
                sent_clean = sent.strip()
                if not sent_clean:
                    continue

                category, classification = self.classify_segment(field_name, sent_clean)
                is_factual = (classification == "SUBSTANTIVE_FACTUAL")
                pid = f"PROP-{field_name[:4].upper()}-{prop_counter:03d}"
                prop_counter += 1

                # If substantive, extract the declarative core for precise entailment checking
                core_text = self.extract_declarative_core(sent_clean) if is_factual else sent_clean
                eval_text = core_text if len(core_text.split()) >= 3 else sent_clean

                propositions.append(
                    ExtractedProposition(
                        prop_id=pid,
                        text=eval_text,
                        source_field=field_name,
                        classification=classification,
                        category=category,
                        cited_ref=cited_ref,
                    )
                )

        return propositions

    def segment_all_fields(self, generated_dict: dict[str, Any], default_ref: str | None = None) -> list[ExtractedProposition]:
        """Inspect all fields of the generated response and extract all atomic propositions."""
        fields_to_check = [
            "message",
            "socratic_question",
            "hints",
            "misconception",
            "mechanistic_explanation",
            "distractor_analysis",
            "revision_summary",
        ]

        all_props: list[ExtractedProposition] = []
        citations = generated_dict.get("citations", [])
        first_ref = citations[0].get("ref") if citations and isinstance(citations[0], dict) else default_ref

        for field in fields_to_check:
            val = generated_dict.get(field)
            if val:
                field_props = self.segment_field(field, val, cited_ref=first_ref)
                all_props.extend(field_props)

        return all_props

    def extract_propositions(self, draft: Any, default_ref: str | None = None) -> list[ExtractedProposition]:
        """Convenience wrapper accepting TutorDraftOutput or dictionary."""
        if hasattr(draft, "model_dump"):
            data = draft.model_dump()
        elif isinstance(draft, dict):
            data = draft
        else:
            data = {}
        return self.segment_all_fields(data, default_ref=default_ref)
