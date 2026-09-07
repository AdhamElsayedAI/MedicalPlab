import unittest
from medicalplab.stage_b.models import ContractError
from medicalplab.stage_d.models import (
    ConfidenceLevel,
    EvidenceBlock,
    TutorCitation,
    TutorMode,
    TutorResponse,
    TutorSection,
)
from medicalplab.stage_d.validator import (
    is_valid_tutor_response,
    validate_citation_provenance,
    validate_clinical_safety,
    validate_semantic_grounding,
    validate_tutor_response,
)


class TestStageDValidator(unittest.TestCase):

    def setUp(self):
        self.block_criteria = EvidenceBlock(
            ref="DOC-WHO-001:B0001",
            document_id="DOC-WHO-001",
            source="WHO",
            heading="Hypertension Definition",
            section="Section 1",
            text="Hypertension is defined as persistent systolic blood pressure of 140 mmHg or higher, or diastolic blood pressure of 90 mmHg or higher. Repeated measurements are required for diagnosis.",
        )
        self.block_treatment = EvidenceBlock(
            ref="DOC-WHO-001:B0002",
            document_id="DOC-WHO-001",
            source="WHO",
            heading="Hypertension Management",
            section="Section 2",
            text="Pharmacological treatment is recommended for individuals with confirmed hypertension. First-line therapy includes thiazide-like diuretics and ACE inhibitors.",
        )
        self.packet = (self.block_criteria, self.block_treatment)

        self.valid_response = TutorResponse(
            query="How is hypertension diagnosed according to WHO guidelines?",
            mode=TutorMode.EXPLANATION,
            answer="Hypertension is diagnosed when systolic blood pressure is 140 mmHg or higher, or diastolic is 90 mmHg or higher, confirmed by repeated measurements.",
            sections=(
                TutorSection(
                    heading="Diagnostic Thresholds",
                    content="A persistent systolic reading of 140 mmHg or higher or diastolic of 90 mmHg or higher establishes the diagnosis across repeated clinical visits.",
                ),
            ),
            citations=(
                TutorCitation(
                    ref="DOC-WHO-001:B0001",
                    quote="persistent systolic blood pressure of 140 mmHg or higher, or diastolic blood pressure of 90 mmHg or higher",
                ),
            ),
            confidence=ConfidenceLevel.HIGH,
            unsupported_aspects=(),
        )

    def test_valid_response_passes_all_validations(self):
        validate_tutor_response(self.valid_response, self.packet)
        ok, errors = is_valid_tutor_response(self.valid_response, self.packet)
        self.assertTrue(ok)
        self.assertEqual(len(errors), 0)

    # ----------------- DEDICATED CLINICAL SAFETY TESTS -----------------

    def test_safety_unsupported_cure_claim_rejected(self):
        """Clinical Safety: The tutor must never claim a condition can be cured unless evidence says so."""
        bad_response = TutorResponse(
            query="Can hypertension be treated?",
            mode=TutorMode.EXPLANATION,
            answer="Hypertension is diagnosed with blood pressure 140/90, and modern medications completely cure this condition permanently.",
            sections=(
                TutorSection(
                    heading="Prognosis",
                    content="Therapy provides a permanent cure for high blood pressure.",
                ),
            ),
            citations=(
                TutorCitation(
                    ref="DOC-WHO-001:B0001",
                    quote="Hypertension is defined as persistent systolic blood pressure of 140 mmHg or higher",
                ),
            ),
            confidence=ConfidenceLevel.HIGH,
        )
        with self.assertRaises(ContractError) as ctx:
            validate_clinical_safety(bad_response, self.packet)
        self.assertIn("cure", str(ctx.exception).lower())

        ok, errors = is_valid_tutor_response(bad_response, self.packet)
        self.assertFalse(ok)
        self.assertTrue(any("cure" in e.lower() for e in errors))

    def test_safety_unsupported_drug_dosage_rejected(self):
        """Clinical Safety: The tutor must never invent specific dosages not stated in evidence."""
        bad_response = TutorResponse(
            query="What dose should be used?",
            mode=TutorMode.TEACHING,
            answer="Pharmacological treatment is recommended with an initial dose of 50 mg daily.",
            sections=(
                TutorSection(
                    heading="Dosing Schedule",
                    content="Start the patient on 50 mg once daily every morning.",
                ),
            ),
            citations=(
                TutorCitation(
                    ref="DOC-WHO-001:B0002",
                    quote="Pharmacological treatment is recommended for individuals with confirmed hypertension.",
                ),
            ),
            confidence=ConfidenceLevel.MEDIUM,
        )
        with self.assertRaises(ContractError) as ctx:
            validate_clinical_safety(bad_response, self.packet)
        self.assertIn("50 mg", str(ctx.exception))

        ok, errors = is_valid_tutor_response(bad_response, self.packet)
        self.assertFalse(ok)
        self.assertTrue(any("50 mg" in e for e in errors))

    def test_safety_unsupported_treatment_recommendation_rejected(self):
        """Clinical Safety: Recommendations must not be fabricated if evidence does not cover treatment."""
        packet_diagnostic_only = (self.block_criteria,)  # block_criteria mentions only criteria, no treatments
        bad_response = TutorResponse(
            query="What should we prescribe?",
            mode=TutorMode.CASE_DISCUSSION,
            answer="Based on blood pressure 140/90, beta blockers should be prescribed immediately.",
            sections=(
                TutorSection(
                    heading="Management",
                    content="Beta blocker therapy should be prescribed for this patient.",
                ),
            ),
            citations=(
                TutorCitation(
                    ref="DOC-WHO-001:B0001",
                    quote="Hypertension is defined as persistent systolic blood pressure of 140 mmHg or higher",
                ),
            ),
            confidence=ConfidenceLevel.MEDIUM,
        )
        with self.assertRaises(ContractError) as ctx:
            validate_clinical_safety(bad_response, packet_diagnostic_only)
        self.assertIn("treatment recommendation", str(ctx.exception).lower())

    def test_safety_unsupported_diagnosis_claim_rejected(self):
        """Clinical Safety: Tutor must not declare unsupported definitive diagnoses."""
        bad_response = TutorResponse(
            query="Does this patient have pheochromocytoma?",
            mode=TutorMode.CASE_DISCUSSION,
            answer="The patient has pheochromocytoma definitively based on systolic blood pressure of 140 mmHg.",
            sections=(
                TutorSection(
                    heading="Clinical Evaluation",
                    content="Evaluation shows the patient has pheochromocytoma.",
                ),
            ),
            citations=(
                TutorCitation(
                    ref="DOC-WHO-001:B0001",
                    quote="systolic blood pressure of 140 mmHg or higher",
                ),
            ),
            confidence=ConfidenceLevel.LOW,
        )
        with self.assertRaises(ContractError) as ctx:
            validate_clinical_safety(bad_response, self.packet)
        self.assertIn("diagnosis", str(ctx.exception).lower())

    def test_safety_supported_treatment_accepted(self):
        """Supported clinical guidance in evidence should be permitted."""
        valid_treatment_response = TutorResponse(
            query="What therapy is recommended for confirmed hypertension?",
            mode=TutorMode.TEACHING,
            answer="Pharmacological treatment is recommended for individuals with confirmed hypertension, including thiazide-like diuretics.",
            sections=(
                TutorSection(
                    heading="First-Line Options",
                    content="First-line therapy includes thiazide-like diuretics and ACE inhibitors as recommended.",
                ),
            ),
            citations=(
                TutorCitation(
                    ref="DOC-WHO-001:B0002",
                    quote="Pharmacological treatment is recommended for individuals with confirmed hypertension.",
                ),
            ),
            confidence=ConfidenceLevel.HIGH,
        )
        validate_clinical_safety(valid_treatment_response, self.packet)

    # ----------------- PROVENANCE & GROUNDING TESTS -----------------

    def test_invalid_citation_ref_rejected(self):
        bad_response = TutorResponse(
            query=self.valid_response.query,
            mode=self.valid_response.mode,
            answer=self.valid_response.answer,
            sections=self.valid_response.sections,
            citations=(
                TutorCitation(
                    ref="NONEXISTENT-REF:9999",
                    quote="persistent systolic blood pressure of 140 mmHg or higher",
                ),
            ),
            confidence=ConfidenceLevel.HIGH,
        )
        with self.assertRaises(ContractError) as ctx:
            validate_citation_provenance(bad_response.citations, self.packet)
        self.assertIn("not found in supplied evidence packet", str(ctx.exception))

    def test_verbatim_quote_mismatch_rejected(self):
        bad_response = TutorResponse(
            query=self.valid_response.query,
            mode=self.valid_response.mode,
            answer=self.valid_response.answer,
            sections=self.valid_response.sections,
            citations=(
                TutorCitation(
                    ref="DOC-WHO-001:B0001",
                    quote="completely fabricated quote that does not appear anywhere in block",
                ),
            ),
            confidence=ConfidenceLevel.HIGH,
        )
        with self.assertRaises(ContractError) as ctx:
            validate_citation_provenance(bad_response.citations, self.packet)
        self.assertIn("not present in cited block", str(ctx.exception))

    def test_no_semantic_overlap_rejected(self):
        bad_response = TutorResponse(
            query="Tell me about hypertension",
            mode=TutorMode.EXPLANATION,
            answer="Ophthalmology cataracts require surgical lens extraction immediately.",
            sections=(
                TutorSection(
                    heading="Cataracts",
                    content="Ophthalmology cataracts require surgical lens extraction immediately.",
                ),
            ),
            citations=(
                TutorCitation(
                    ref="DOC-WHO-001:B0001",
                    quote="Hypertension is defined as persistent systolic blood pressure of 140 mmHg or higher",
                ),
            ),
            confidence=ConfidenceLevel.HIGH,
        )
        with self.assertRaises(ContractError) as ctx:
            validate_semantic_grounding(bad_response, self.packet)
        self.assertIn("no semantic overlap", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
