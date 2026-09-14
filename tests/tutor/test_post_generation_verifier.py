"""Tests for Post-Generation Verifier and Safety Vetoes."""
from __future__ import annotations

import pytest
from medicalplab.evidence_engine.models import RetrievedCandidate
from medicalplab.tutor.models import ExtractedProposition
from medicalplab.tutor.verifier import TutorPostVerifier


def test_clinical_safety_vetoes_cure_claims():
    verifier = TutorPostVerifier()
    draft = {"message": "This medication permanently cures glomerulonephritis completely."}
    vetoes = verifier.check_clinical_safety(draft)
    assert "UNSUPPORTED_CURE_CLAIM" in vetoes


def test_clinical_safety_vetoes_drug_dosages():
    verifier = TutorPostVerifier()
    draft = {"message": "Administer 40 mg furosemide immediately."}
    vetoes = verifier.check_clinical_safety(draft)
    assert "UNAUTHORIZED_DRUG_DOSE" in vetoes


def test_clinical_safety_vetoes_prescriptions():
    verifier = TutorPostVerifier()
    draft = {"message": "Lisinopril should be prescribed as first-line treatment."}
    vetoes = verifier.check_clinical_safety(draft)
    assert "UNAUTHORIZED_PRESCRIPTION_RECOMMENDATION" in vetoes


def test_clinical_safety_vetoes_definitive_diagnoses():
    verifier = TutorPostVerifier()
    draft = {"message": "The patient definitively has diabetic nephropathy."}
    vetoes = verifier.check_clinical_safety(draft)
    assert "UNAUTHORIZED_DEFINITIVE_DIAGNOSIS" in vetoes


def test_citation_provenance_verbatim_quote():
    verifier = TutorPostVerifier()
    cand = RetrievedCandidate(
        chunk_id="c1",
        document_id="DOC-PMC-RENAL-0001",
        text="Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I.",
    )
    citations_valid = [{"document_id": "DOC-PMC-RENAL-0001", "chunk_id": "c1", "quote": "Active renin acts upon its substrate"}]
    ok, err = verifier.validate_provenance(citations_valid, [cand])
    assert ok is True
    assert err is None

    citations_fabricated = [{"document_id": "DOC-PMC-RENAL-0001", "chunk_id": "c1", "quote": "Fabricated quote not in text"}]
    ok2, err2 = verifier.validate_provenance(citations_fabricated, [cand])
    assert ok2 is False
    assert "QUOTE_NOT_FOUND" in err2


def test_verify_propositions_supported_vs_unsupported():
    verifier = TutorPostVerifier()
    cand = RetrievedCandidate(
        chunk_id="c1",
        document_id="DOC-PMC-RENAL-0001",
        text="Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I (Ang I).",
    )
    props = [
        ExtractedProposition(
            prop_id="P1",
            text="Active renin acts upon its substrate, angiotensinogen, to generate angiotensin I (Ang I).",
            source_field="message",
            classification="SUBSTANTIVE_FACTUAL",
        ),
        ExtractedProposition(
            prop_id="P2",
            text="Great observation!",
            source_field="message",
            classification="NON_FACTUAL_PEDAGOGICAL_LANGUAGE",
        ),
        ExtractedProposition(
            prop_id="P3",
            text="The glomerular filtration rate in healthy adults is normally 500 mL/min.",
            source_field="message",
            classification="SUBSTANTIVE_FACTUAL",
        ),
    ]
    summary, all_ok = verifier.verify_propositions(props, [cand])
    assert all_ok is False  # P3 is unsupported
    assert summary.supported_propositions == 1
    assert summary.non_factual_statements == 1
    assert summary.unsupported_propositions == 1
