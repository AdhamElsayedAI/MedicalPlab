"""Provenance and conservative quantitative vetoes, NEVER a proof of entailment.

The model remains responsible for semantic interpretation. These checks reject
demonstrable inconsistencies; they cannot establish general semantic correctness.
"""

from dataclasses import replace
import re
import unicodedata
from .models import ClaimSupport, require


def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(str.maketrans("–—−’‘“”٠١٢٣٤٥٦٧٨٩", "---''\"\"0123456789"))
    return " ".join(text.split()).casefold()


def contains(span, text):
    # Word boundaries prevent 3 being accepted as 30, or mg as mcg.
    return (
        re.search(r"(?<!\w)" + re.escape(normalize(span)) + r"(?!\w)", normalize(text))
        is not None
    )


def role(text):
    t = normalize(text)
    if re.search(r"equival|conversion|convert|يعادل|تكافؤ", t):
        return "equivalence"
    if re.search(r"visits?|زيارات|زياره|زيارة", t):
        return "visit_count"
    return None


def validate_and_apply(claim, result, packet):
    require(
        result.claim_id == claim.claim_id and result.text == claim.text,
        "Verification changed the fixed claim",
    )
    blocks = {b.ref: b for b in packet}
    for c in result.citations:
        require(c.ref in blocks, "Evidence reference outside supplied packet")
        require(
            normalize(c.quote) in normalize(blocks[c.ref].text),
            "Quote not present in cited block",
        )
    for b in result.bindings:
        require(b.ref in blocks, "Binding reference outside packet")
        require(
            any(
                c.ref == b.ref and normalize(b.context) in normalize(c.quote)
                for c in result.citations
            ),
            "Binding context must be grounded in a citation",
        )
    if result.status == ClaimSupport.UNSUPPORTED:
        return result, ()
    reasons = []
    if claim.source_document and any(
        blocks[c.ref].document_id != claim.source_document for c in result.citations
    ):
        reasons.append("source_constraint_miss")
    if claim.exact and not result.bindings:
        reasons.append("exact_binding_missing")
    for b in result.bindings:
        block = blocks[b.ref]
        # A row is legitimate only when it exists as a complete line in a table.
        is_row = block.block_type in {"table", "table_row"} and any(
            normalize(b.context) == normalize(line) for line in block.text.splitlines()
        )
        if not is_row and (
            "\n" in b.context.strip() or re.search(r"[.!?;]\s+\S", b.context)
        ):
            reasons.append("cross_sentence_binding")
        if not all(
            contains(s, b.context) for s in (b.entity, b.relation, b.quantity, b.unit)
        ):
            reasons.append("binding_span_absent")
        expected_role = role(claim.text)
        if expected_role and b.role != expected_role:
            reasons.append("quantitative_role_mismatch")
        if b.role == "visit_count" and not re.search(r"visit|زيار", normalize(b.unit)):
            reasons.append("visit_unit_mismatch")
        if b.role == "equivalence" and not re.search(
            r"equival|convert|يعادل|تكافؤ", normalize(b.relation)
        ):
            reasons.append("equivalence_relation_missing")
        if re.search(
            r"repeat|retest|إعادة|تكرار", normalize(claim.text)
        ) and not re.search(r"repeat|retest|إعادة|تكرار", normalize(b.relation)):
            reasons.append("repeat_relation_missing")
        # Values explicitly asserted in a claim must be present; no conversion or rounding.
        # Requested slots need not contain a number, so this does not fill unknowns.
        numbers = re.findall(r"(?<!\w)\d+(?:\.\d+)?", normalize(claim.text))
        if any(
            not contains(n, " ".join(x.context for x in result.bindings))
            for n in numbers
        ):
            reasons.append("asserted_quantity_missing")
    reasons = tuple(sorted(set(reasons)))
    if reasons:
        return replace(
            result,
            status=ClaimSupport.UNSUPPORTED,
            reason=result.reason + " [policy downgrade]",
        ), reasons
    return result, ()
