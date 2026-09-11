"""
Tests for RenalQueryCanonicalizer
================================
Verifies:
1. Acronym expansion with exact word boundaries.
2. British/American spelling normalization.
3. Comparators and units preservation.
4. Strict negation preservation (zero polarity drop).
5. Controlled query rewrite consistency.
"""

import pytest
from medicalplab.learn.renal_canonicalizer import (
    RenalQueryCanonicalizer,
    canonicalize_query,
)


class TestRenalQueryCanonicalizer:
    def test_acronym_expansion(self):
        canonicalizer = RenalQueryCanonicalizer()
        res = canonicalizer.canonicalize("What is the KDIGO definition of AKI stage 3?")
        assert "Kidney Disease Improving Global Outcomes (KDIGO)" in res.canonical_query
        assert "acute kidney injury (AKI)" in res.canonical_query
        assert any("acronym_expanded" in t for t in res.transformations)

    def test_spelling_unification(self):
        canonicalizer = RenalQueryCanonicalizer()
        res = canonicalizer.canonicalize("Treatment of severe hyperkalemia with peripheral edema and hematuria")
        assert "hyperkalaemia" in res.canonical_query
        assert "oedema" in res.canonical_query
        assert "haematuria" in res.canonical_query

    def test_comparator_and_unit_normalization(self):
        canonicalizer = RenalQueryCanonicalizer()
        res = canonicalizer.canonicalize("Patients with eGFR less than 15 ml/min/1.73m2 and proteinuria at least 3.5 g/24h")
        assert "< 15" in res.canonical_query
        assert "mL/min/1.73m2" in res.canonical_query
        assert ">= 3.5" in res.canonical_query

    def test_strict_negation_preservation(self):
        canonicalizer = RenalQueryCanonicalizer()
        res = canonicalizer.canonicalize("Nephrotic syndrome without hypertension and no red blood cell casts")
        assert res.has_negation is True
        assert "without" in res.canonical_query
        assert "no" in res.canonical_query
        assert "negation_detected_and_preserved" in res.transformations

    def test_clinical_entity_recognition(self):
        canonicalizer = RenalQueryCanonicalizer()
        res = canonicalizer.canonicalize("Biopsy demonstrating podocyte foot process effacement and spike and dome deposits")
        assert "podocyte" in res.detected_entities
        assert "foot process effacement" in res.detected_entities
        assert "spike and dome" in res.detected_entities

    def test_controlled_rewrite(self):
        canonicalizer = RenalQueryCanonicalizer()
        res = canonicalizer.canonicalize("Emergency management of hyperkalemia")
        assert "hyperkalaemia" in res.canonical_query
        assert "(hyperkalemia)" in res.controlled_rewrite
