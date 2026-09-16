"""Tests for Phase 2B data contracts, schemas, and feature gating."""
import os
import pytest
from medicalplab.remediation.config import is_remediation_enabled
from medicalplab.remediation.models import (
    DetectionStatus,
    EpistemicType,
    EvidenceStrength,
    PatternHypothesis,
    ReasoningPatternCategory,
    ReasoningPatternTaxonomyItem,
    RemediationLifecycleState,
    RemediationOutcome,
    RemediationSessionState,
    SocraticStrategyType,
    TransferItemDTO,
    TransferAttempt,
)


def test_feature_flag_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MEDICALPLAB_PHASE_2B_ENABLED", raising=False)
    assert is_remediation_enabled() is False

    monkeypatch.setenv("MEDICALPLAB_PHASE_2B_ENABLED", "false")
    assert is_remediation_enabled() is False

    monkeypatch.setenv("MEDICALPLAB_PHASE_2B_ENABLED", "0")
    assert is_remediation_enabled() is False


def test_feature_flag_enabled_explicitly(monkeypatch):
    monkeypatch.setenv("MEDICALPLAB_PHASE_2B_ENABLED", "true")
    assert is_remediation_enabled() is True

    monkeypatch.setenv("MEDICALPLAB_PHASE_2B_ENABLED", "1")
    assert is_remediation_enabled() is True

    monkeypatch.setenv("MEDICALPLAB_PHASE_2B_ENABLED", "yes")
    assert is_remediation_enabled() is True


def test_epistemic_hypothesis_contract():
    hypothesis = PatternHypothesis(
        hypothesis_id="HYP-001",
        epistemic_type=EpistemicType.HYPOTHESIS,
        detection_status=DetectionStatus.POSSIBLE_PATTERN,
        category=ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION,
        pattern_id="PATTERN-RAAS-SUB-01",
        candidate_pattern="Substrate versus product role inversion",
        evidence_strength=EvidenceStrength.MODERATE,
        detection_rationale="Selected Angiotensin II instead of Angiotensinogen",
        rule_version="1.0.0",
        taxonomy_version="1.0.0",
    )
    assert hypothesis.epistemic_type == EpistemicType.HYPOTHESIS
    assert hypothesis.detection_status == DetectionStatus.POSSIBLE_PATTERN
    assert hypothesis.evidence_strength == EvidenceStrength.MODERATE


def test_transfer_dto_excludes_answer_keys():
    """TransferItemDTO must not leak correct_answer or explanations to client."""
    dto = TransferItemDTO(
        question_id="UNI-RENAL-001-T",
        stem="Which precursor is cleaved by renin?",
        options={"A": "Angiotensinogen", "B": "Angiotensin II"},
        subject="Renal physiology",
        topic="RAAS mechanisms",
        difficulty="easy",
    )
    data = dto.model_dump()
    assert "correct_answer" not in data
    assert "explanation" not in data
    assert "distractor_mappings" not in data


def test_remediation_lifecycle_and_outcomes():
    """Verify lifecycle states and outcomes are distinct enums."""
    assert RemediationLifecycleState.CREATED.value == "CREATED"
    assert RemediationLifecycleState.AWAITING_TRANSFER.value == "AWAITING_TRANSFER"
    assert RemediationLifecycleState.COMPLETED.value == "COMPLETED"

    assert RemediationOutcome.TRANSFER_CONFIRMED.value == "TRANSFER_CONFIRMED"
    assert RemediationOutcome.TRANSFER_NOT_CONFIRMED.value == "TRANSFER_NOT_CONFIRMED"
    assert RemediationOutcome.UNRESOLVED.value == "UNRESOLVED"
    assert RemediationOutcome.SAFETY_FALLBACK.value == "SAFETY_FALLBACK"
