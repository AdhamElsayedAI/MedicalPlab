import unittest
from medicalplab.stage_b.models import ContractError
from medicalplab.stage_f.case_simulation import (
    ClinicalCaseSimulationEngine,
    validate_case_clinical_safety,
)
from medicalplab.stage_f.models import CaseSimulationResult


class DummyBlock:

    def __init__(self, ref: str, text: str):
        self.ref = ref
        self.text = text


class TestStageFSimulation(unittest.TestCase):

    def setUp(self):
        self.simulator = ClinicalCaseSimulationEngine()
        self.valid_evidence = [
            DummyBlock(
                ref="WHO-CARD-001",
                text="Hypertension is defined as blood pressure >= 140/90 mmHg. Pharmacological treatment is recommended for confirmed hypertension.",
            ),
        ]

    def test_simulation_grounded_success(self):
        vignette = "A 62-year-old male presents with persistent blood pressure 155/95 mmHg on 3 visits."
        result = self.simulator.run_simulation(
            student_id="STU-001",
            topic="Hypertension",
            vignette=vignette,
            evidence_blocks=self.valid_evidence,
        )
        self.assertIsInstance(result, CaseSimulationResult)
        self.assertTrue(result.clinical_safety_verified)
        self.assertEqual(len(result.steps), 1)
        self.assertEqual(result.steps[0].citations, ("WHO-CARD-001",))

    def test_simulation_veto_unsupported_cure(self):
        evidence_text = "Hypertension requires blood pressure monitoring."
        bad_action = "This treatment completely cures hypertension permanently."
        with self.assertRaises(ContractError) as ctx:
            validate_case_clinical_safety(bad_action, evidence_text)
        self.assertIn("cure", str(ctx.exception).lower())

    def test_simulation_veto_invented_dosage(self):
        evidence_text = "Pharmacological treatment is recommended for hypertension."
        bad_action = "Initiate therapy with amlodipine 50 mg daily."
        with self.assertRaises(ContractError) as ctx:
            validate_case_clinical_safety(bad_action, evidence_text)
        self.assertIn("50 mg", str(ctx.exception))

    def test_simulation_veto_unsupported_diagnosis(self):
        evidence_text = "Hypertension criteria are systolic >= 140 or diastolic >= 90."
        bad_action = "The patient has pheochromocytoma definitively based on blood pressure."
        with self.assertRaises(ContractError) as ctx:
            validate_case_clinical_safety(bad_action, evidence_text)
        self.assertIn("diagnosis", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
