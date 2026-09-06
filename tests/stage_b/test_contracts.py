from dataclasses import replace
import json
import unittest
from medicalplab.stage_b.models import *
from medicalplab.stage_b.aggregator import aggregate
from medicalplab.stage_b.claim_planner import parse_plan
from medicalplab.stage_b.evidence_policy import normalize, validate_and_apply
from medicalplab.stage_b.verifier import parse_verification
from medicalplab.stage_b.pipeline import StageBPipeline


def claim(text="Dose?", exact=False, source=None):
    return MaterialClaim("C1", text, ClaimOrigin.REQUESTED_FACT, text, source, exact)


def block(
    text="Drug: Labetalol | Dose: 200–1200 mg/day in 2–3 divided doses", kind="table"
):
    return EvidenceBlock("D:B0001", "D", "Source", "Heading", "Section", text, kind)


def supported(c, b, bindings=()):
    return VerifierResult(
        c.claim_id,
        c.text,
        ClaimSupport.SUPPORTED,
        (Citation(b.ref, b.text),),
        bindings,
        "Direct evidence",
    )


class Contracts(unittest.TestCase):
    def test_aggregation(self):
        s = supported(claim(), block())
        u = replace(s, claim_id="C2", status=ClaimSupport.UNSUPPORTED)
        self.assertEqual(aggregate((s,)), "supported")
        self.assertEqual(aggregate((u,)), "unsupported")
        self.assertEqual(aggregate((s, u)), "partial")

    def test_empty_and_duplicate_claims(self):
        s = supported(claim(), block())
        for rows in [(), (s, s)]:
            with self.assertRaises(ContractError):
                aggregate(rows)

    def test_supported_requires_evidence(self):
        with self.assertRaises(ContractError):
            VerifierResult("C1", "x", ClaimSupport.SUPPORTED, (), (), "x")

    def test_ref_restriction(self):
        b = block()
        result = replace(
            supported(claim(), b), citations=(Citation("X:B9999", b.text),)
        )
        with self.assertRaises(ContractError):
            validate_and_apply(claim(), result, (b,))

    def test_wrong_block_quote(self):
        b = block()
        r = replace(
            supported(claim(), b), citations=(Citation(b.ref, "invented text"),)
        )
        with self.assertRaises(ContractError):
            validate_and_apply(claim(), r, (b,))

    def test_unicode(self):
        self.assertEqual(normalize("٣–٦\u00a0months"), normalize("3-6 months"))
        b = block("3–6 months", "text")
        r = replace(supported(claim(), b), citations=(Citation(b.ref, "3-6 months"),))
        self.assertFalse(validate_and_apply(claim(), r, (b,))[1])

    def test_source_constraint(self):
        c, b = claim(source="OTHER"), block()
        r, why = validate_and_apply(c, supported(c, b), (b,))
        self.assertEqual(r.status, ClaimSupport.UNSUPPORTED)
        self.assertIn("source_constraint_miss", why)

    def test_fixed_text(self):
        c, b = claim(), block()
        with self.assertRaises(ContractError):
            validate_and_apply(c, replace(supported(c, b), text="changed"), (b,))

    def test_exact_without_binding(self):
        c, b = claim(exact=True), block()
        self.assertIn(
            "exact_binding_missing", validate_and_apply(c, supported(c, b), (b,))[1]
        )

    def test_structured_row(self):
        c, b = claim("What labetalol dose?", True), block()
        binding = ExactBinding(
            b.ref, b.text, "Labetalol", "Dose", "200–1200", "mg/day", "dose"
        )
        self.assertFalse(validate_and_apply(c, supported(c, b, (binding,)), (b,))[1])

    def test_canonical_corpus_table_row(self):
        c = claim("What labetalol dose?", True)
        b = block(
            "Table 6. Summary of antihypertensive agents used in pregnancy. — Category: First-line agents — Drug: Labetalol; Class: Combined alpha and beta blocker; Dose: 200–1200 mg/day in 2–3 divided doses; FDA Risk: C; Additional Information: May be associated with fetal growth restriction",
            "table_row",
        )
        binding = ExactBinding(
            b.ref, b.text, "Labetalol", "Dose", "200–1200", "mg/day", "dose"
        )
        self.assertFalse(validate_and_apply(c, supported(c, b, (binding,)), (b,))[1])

    def test_interval_not_visits(self):
        c, b = (
            claim("3–6 consecutive visits", True),
            block("Follow up every 3–6 months", "text"),
        )
        binding = ExactBinding(
            b.ref, b.text, "Follow up", "every", "3–6", "months", "interval"
        )
        self.assertIn(
            "quantitative_role_mismatch",
            validate_and_apply(c, supported(c, b, (binding,)), (b,))[1],
        )

    def test_lab_repeat_not_followup(self):
        c, b = (
            claim("Repeat HbA1c monthly?", True),
            block("HbA1c at baseline; medication follow-up monthly", "text"),
        )
        binding = ExactBinding(
            b.ref, b.text, "HbA1c", "follow-up", "monthly", "monthly", "interval"
        )
        reasons = validate_and_apply(c, supported(c, b, (binding,)), (b,))[1]
        self.assertIn("repeat_relation_missing", reasons)
        self.assertIn("cross_sentence_binding", reasons)

    def test_dose_equivalence(self):
        c, b = (
            claim("HCTZ to furosemide dose equivalence?", True),
            block("Furosemide dose 20 mg", "text"),
        )
        binding = ExactBinding(b.ref, b.text, "Furosemide", "dose", "20", "mg", "dose")
        self.assertIn(
            "quantitative_role_mismatch",
            validate_and_apply(c, supported(c, b, (binding,)), (b,))[1],
        )

    def test_categorical_preference(self):
        c, b = (
            claim("Which drug class is preferred?", False),
            block("Loop diuretics preferred over thiazides below eGFR 30", "text"),
        )
        self.assertFalse(validate_and_apply(c, supported(c, b), (b,))[1])

    def test_no_substring_number_match(self):
        c, b = claim("Dose 3 mg", True), block("Drug dose 30 mg", "text")
        binding = ExactBinding(b.ref, b.text, "Drug", "dose", "3", "mg", "dose")
        self.assertIn(
            "binding_span_absent",
            validate_and_apply(c, supported(c, b, (binding,)), (b,))[1],
        )

    def test_binding_wrong_ref(self):
        c, b = claim(exact=True), block()
        binding = ExactBinding(
            "outside", b.text, "Labetalol", "Dose", "200", "mg", "dose"
        )
        with self.assertRaises(ContractError):
            validate_and_apply(c, supported(c, b, (binding,)), (b,))

    def test_no_table_cross_row(self):
        c, b = claim(exact=True), block("Drug A | 10 mg\nDrug B | 20 mg")
        binding = ExactBinding(b.ref, b.text, "Drug A", "Drug", "20", "mg", "dose")
        self.assertIn(
            "cross_sentence_binding",
            validate_and_apply(c, supported(c, b, (binding,)), (b,))[1],
        )

    def test_schema_rejects_overall_verdict(self):
        with self.assertRaises(ContractError):
            parse_verification('{"claims":[],"verdict":"supported"}', ())

    def test_duplicate_json_keys(self):
        with self.assertRaises(ContractError):
            strict_json('{"claims":[],"claims":[]}')

    def test_plan_origins(self):
        query = "The review says ABPM measures every 30 minutes. What manufacturer? My eGFR is 22."
        claims = [
            dict(
                claim_id=f"C{i}",
                text=span,
                origin=origin,
                query_span=span,
                source_document=None,
                exact=False,
            )
            for i, span, origin in [
                (
                    1,
                    "The review says ABPM measures every 30 minutes.",
                    "source_premise",
                ),
                (2, "What manufacturer?", "requested_fact"),
                (3, "My eGFR is 22.", "personal_context"),
            ]
        ]
        parsed = parse_plan(json.dumps({"claims": claims}), query, {"D": "Source"})
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0].origin, ClaimOrigin.SOURCE_PREMISE)

    def test_arabic_open_slot(self):
        for query in [
            "كام زيارة؟",
            "thiazides below كام",
            "إيه الدواء؟",
            "Which model?",
        ]:
            data = dict(
                claim_id="C1",
                text=query,
                query_span=query,
                origin="requested_fact",
                source_document=None,
                exact=True,
            )
            self.assertEqual(
                len(parse_plan(json.dumps({"claims": [data]}), query, {})), 1
            )
            data["origin"] = "source_premise"
            with self.assertRaises(ContractError):
                parse_plan(json.dumps({"claims": [data]}), query, {})

    def test_duplicate_plan_ids(self):
        data = dict(
            claim_id="C1",
            text="what?",
            query_span="what?",
            origin="requested_fact",
            source_document=None,
            exact=False,
        )
        with self.assertRaises(ContractError):
            parse_plan(json.dumps({"claims": [data, data]}), "what?", {})

    def test_unknown_source(self):
        data = dict(
            claim_id="C1",
            text="what?",
            query_span="what?",
            origin="requested_fact",
            source_document="X",
            exact=False,
        )
        with self.assertRaises(ContractError):
            parse_plan(json.dumps({"claims": [data]}), "what?", {})

    def test_top_ten_required_before_inference(self):
        with self.assertRaises(ContractError):
            StageBPipeline(None).run("query", (block(),))
