import unittest
from medicalplab.stage_b.models import ContractError
from medicalplab.stage_d.models import (
    ConfidenceLevel,
    EvidenceBlock,
    TutorCitation,
    TutorMode,
    TutorRequest,
    TutorResponse,
    TutorSection,
)


class TestStageDModels(unittest.TestCase):

    def setUp(self):
        self.block = EvidenceBlock(
            ref="DOC-001:B0001",
            document_id="DOC-001",
            source="WHO",
            heading="Hypertension Guidelines",
            section="Diagnostic Criteria",
            text="Hypertension is defined as persistent blood pressure of 140/90 mmHg or higher.",
        )
        self.citation = TutorCitation(
            ref="DOC-001:B0001",
            quote="persistent blood pressure of 140/90 mmHg or higher",
        )
        self.section = TutorSection(
            heading="Diagnostic Criteria",
            content="According to WHO, hypertension is diagnosed at persistent systolic levels of 140 or higher.",
        )

    def test_valid_tutor_response_creation(self):
        resp = TutorResponse(
            query="What is the definition of hypertension?",
            mode=TutorMode.EXPLANATION,
            answer="Hypertension is defined as persistent blood pressure of 140/90 mmHg or higher.",
            sections=(self.section,),
            citations=(self.citation,),
            confidence=ConfidenceLevel.HIGH,
            unsupported_aspects=(),
        )
        self.assertEqual(resp.query, "What is the definition of hypertension?")
        self.assertEqual(resp.mode, TutorMode.EXPLANATION)
        self.assertEqual(resp.confidence, ConfidenceLevel.HIGH)
        self.assertEqual(len(resp.sections), 1)
        self.assertEqual(len(resp.citations), 1)

    def test_immutability_frozen(self):
        resp = TutorResponse(
            query="What is the definition of hypertension?",
            mode=TutorMode.EXPLANATION,
            answer="Hypertension is defined as persistent blood pressure of 140/90 mmHg or higher.",
            sections=(self.section,),
            citations=(self.citation,),
            confidence=ConfidenceLevel.HIGH,
        )
        with self.assertRaises(Exception):
            resp.answer = "New answer"

    def test_confidence_level_enum_enforcement(self):
        with self.assertRaises(ContractError):
            TutorResponse(
                query="Query",
                mode=TutorMode.EXPLANATION,
                answer="Answer",
                sections=(self.section,),
                citations=(self.citation,),
                confidence="high",  # Free string must be rejected; must be ConfidenceLevel enum
            )

    def test_tutor_mode_enum_enforcement(self):
        with self.assertRaises(ContractError):
            TutorResponse(
                query="Query",
                mode="explanation",  # Free string must be rejected; must be TutorMode enum
                answer="Answer",
                sections=(self.section,),
                citations=(self.citation,),
                confidence=ConfidenceLevel.HIGH,
            )

    def test_citation_quote_too_short_rejected(self):
        with self.assertRaises(ContractError):
            TutorCitation(
                ref="DOC-001:B0001",
                quote="too short",  # Only 2 words (< 3 words)
            )

    def test_empty_citations_rejected(self):
        with self.assertRaises(ContractError):
            TutorResponse(
                query="Query",
                mode=TutorMode.EXPLANATION,
                answer="Answer",
                sections=(self.section,),
                citations=(),  # Empty citations
                confidence=ConfidenceLevel.HIGH,
            )

    def test_empty_sections_rejected(self):
        with self.assertRaises(ContractError):
            TutorResponse(
                query="Query",
                mode=TutorMode.EXPLANATION,
                answer="Answer",
                sections=(),  # Empty sections
                citations=(self.citation,),
                confidence=ConfidenceLevel.HIGH,
            )

    def test_valid_tutor_request(self):
        req = TutorRequest(
            query="How should I approach a patient with elevated blood pressure?",
            evidence=(self.block,),
            mode=TutorMode.TEACHING,
            context="Step-by-step guideline overview",
        )
        self.assertEqual(req.mode, TutorMode.TEACHING)
        self.assertEqual(len(req.evidence), 1)

    def test_tutor_request_requires_evidence(self):
        with self.assertRaises(ContractError):
            TutorRequest(
                query="Query",
                evidence=(),  # Empty evidence packet
            )


if __name__ == "__main__":
    unittest.main()
