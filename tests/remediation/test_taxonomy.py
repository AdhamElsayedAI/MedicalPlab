"""Tests for Reasoning Pattern Taxonomy Registry.

MANDATORY INVARIANTS:
1. Taxonomy must store: reasoning pattern, category, strategy, evidence references.
2. Zero medical truth stored in taxonomy (factual claims come from Evidence Engine).
"""
import pytest
from medicalplab.remediation.models import (
    ReasoningPatternCategory,
    SocraticStrategyType,
)
from medicalplab.remediation.taxonomy import (
    ReasoningPatternTaxonomyRegistry,
    get_taxonomy_registry,
)


def test_taxonomy_loads_successfully():
    registry = get_taxonomy_registry()
    patterns = registry.all_patterns()
    mappings = registry.all_mappings()

    assert len(patterns) >= 7
    assert len(mappings) >= 15


def test_zero_medical_truth_in_taxonomy():
    """Verify that taxonomy entries store only patterns, categories, strategies, and evidence refs."""
    registry = get_taxonomy_registry()

    for pattern in registry.all_patterns():
        # Assert required fields
        assert pattern.pattern_id.startswith("PATTERN-")
        assert pattern.topic
        assert isinstance(pattern.category, ReasoningPatternCategory)
        assert isinstance(pattern.recommended_strategy, SocraticStrategyType)
        assert isinstance(pattern.evidence_references, list)
        assert len(pattern.evidence_references) > 0

        # Assert no factual medical truth is stored in pattern schema
        pattern_dict = pattern.model_dump()
        for forbidden_key in ["medical_truth", "correct_fact", "clinical_fact", "gold_truth", "answer"]:
            assert forbidden_key not in pattern_dict, f"Forbidden medical truth key found: {forbidden_key}"


def test_distractor_mapping_retrieval():
    registry = get_taxonomy_registry()

    # Test UNI-RENAL-001 Option B
    mapping = registry.get_mapping("UNI-RENAL-001", "B")
    assert mapping is not None
    assert mapping.pattern_id == "PATTERN-RAAS-SUB-01"
    assert mapping.confidence_weight >= 0.90
    assert "Selected Angiotensin II" in mapping.detection_rationale

    # Test pattern retrieval
    pattern = registry.get_pattern(mapping.pattern_id)
    assert pattern is not None
    assert pattern.category == ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION
    assert pattern.recommended_strategy == SocraticStrategyType.CONTRAST_CASE
    assert "DOC-PMC-RENAL-0001" in pattern.evidence_references[0]


def test_topic_lookup():
    registry = get_taxonomy_registry()
    raas_patterns = registry.get_patterns_for_topic("RAAS mechanisms")
    assert len(raas_patterns) >= 3
    for p in raas_patterns:
        assert p.topic == "RAAS mechanisms"
