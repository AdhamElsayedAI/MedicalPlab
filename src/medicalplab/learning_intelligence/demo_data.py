"""Deterministic, isolated DEMO data fixtures for Phase 3 Learning Intelligence.

IMPORTANT:
All data here is purely synthetic educational demo fixtures for repeatable educator
evaluation and demonstrations. It does NOT represent real learners or live production usage.
"""
from __future__ import annotations

from typing import List
from medicalplab.remediation.models import (
    DetectedLearningGap,
    EpistemicType,
    DetectionStatus,
    EvidenceStrength,
    PatternHypothesis,
    ReasoningPatternCategory,
    ReasoningTimelineItem,
    RemediationLifecycleState,
    RemediationOutcome,
    RemediationSessionState,
    RemediationStatus,
    RemediationTurnRecord,
    SocraticStrategyType,
    TransferAttempt,
)

DEMO_COHORT_ID = "cohort_demo_renal_01"
DEMO_COHORT_NAME = "Preclinical Year 1 — Renal Physiology (Demo Cohort)"
DEMO_TOPIC = "preclinical_renal"
DEMO_SUBJECT = "Renal physiology"

DEMO_DISCLAIMER = (
    "DEMO / SYNTHETIC COHORT DATA: These records are deterministic demonstration fixtures "
    "used to evaluate cross-learner reasoning gap radar capabilities. No real student data is used."
)


def get_demo_sessions() -> List[RemediationSessionState]:
    """Generate deterministic synthetic demo sessions across 14 demo learners.

    Breakdown:
    - 6 learners with PATTERN-RAAS-SUB-01 (Substrate vs product inversion):
      - 4 demonstrated independent transfer
      - 1 failed independent transfer
      - 1 assisted transfer (correct, but assisted -> excluded from demonstrated count!)
    - 4 learners with PATTERN-RAAS-ENZ-01 (Enzymatic cleavage role reversal):
      - 3 demonstrated independent transfer
      - 1 failed independent transfer
    - 3 learners with PATTERN-RAAS-REC-01 (Receptor specificity confusion):
      - 2 demonstrated independent transfer
      - 1 failed independent transfer
    - 1 learner with SAFETY_FALLBACK (demonstrates safety exclusion)
    - 1 learner with INSUFFICIENT_EVIDENCE (demonstrates exclusion)
    Total unique eligible learners with valid reasoning gap signals: 13 (or 14 total in cohort).
    """
    sessions: list[RemediationSessionState] = []

    # 1. Pattern RAAS-SUB-01: Substrate vs product role inversion (6 learners)
    for i in range(1, 7):
        learner_id = f"demo_learner_{i:03d}"
        session_id = f"DEMO-SES-SUB-{i:03d}"

        # 4 demonstrated (1-4), 1 not confirmed (5), 1 assisted (6)
        if i <= 4:
            outcome = RemediationOutcome.TRANSFER_CONFIRMED
            t_attempt = TransferAttempt(
                question_id="UNI-RENAL-001-T",
                submitted_option="A",
                is_correct=True,
                was_assisted=False,
            )
            asst_invoked = False
        elif i == 5:
            outcome = RemediationOutcome.TRANSFER_NOT_CONFIRMED
            t_attempt = TransferAttempt(
                question_id="UNI-RENAL-001-T",
                submitted_option="C",
                is_correct=False,
                was_assisted=False,
            )
            asst_invoked = False
        else:  # i == 6
            outcome = RemediationOutcome.UNRESOLVED
            t_attempt = TransferAttempt(
                question_id="UNI-RENAL-001-T",
                submitted_option="A",
                is_correct=True,
                was_assisted=True,  # Assisted! Must be excluded from demonstrated transfer
            )
            asst_invoked = True

        sessions.append(RemediationSessionState(
            session_id=session_id,
            user_id=learner_id,
            question_id="UNI-RENAL-001",
            selected_option="B",
            topic=DEMO_TOPIC,
            turn_number=3,
            max_turns=3,
            is_complete=True,
            lifecycle_state=RemediationLifecycleState.COMPLETED,
            outcome=outcome,
            remediation_status=RemediationStatus.RESOLVED if outcome == RemediationOutcome.TRANSFER_CONFIRMED else RemediationStatus.UNRESOLVED,
            detected_gap=DetectedLearningGap(
                pattern_id="PATTERN-RAAS-SUB-01",
                topic="RAAS mechanisms",
                category=ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION,
                reasoning_pattern="Substrate versus product role inversion in enzymatic cascade",
                recommended_strategy=SocraticStrategyType.CONTRAST_CASE,
                confidence=0.85,
                detection_rationale="Learner selected precursor substrate rather than downstream effector product",
                evidence_references=["DOC-PMC-RENAL-0001:DOC-PMC-RENAL-0001-B0003-C01"],
            ),
            hypothesis=PatternHypothesis(
                hypothesis_id=f"HYP-SUB-{i:03d}",
                epistemic_type=EpistemicType.HYPOTHESIS,
                detection_status=DetectionStatus.POSSIBLE_PATTERN,
                category=ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION,
                pattern_id="PATTERN-RAAS-SUB-01",
                candidate_pattern="Substrate versus product role inversion in enzymatic cascade",
                evidence_strength=EvidenceStrength.MODERATE,
                detection_rationale="Selected distractor indicates substrate/product role reversal",
                supporting_signals=["distractor_b"],
            ),
            strategy=SocraticStrategyType.CONTRAST_CASE,
            timeline=ReasoningTimelineItem(
                initial_pattern="Initial option choice reversed substrate and product roles",
                learning_gap="Suspected gap in enzymatic cascade sequencing",
                guided_practice="3-turn Socratic dialogue completed",
                transfer_result="Transfer demonstrated on this question" if outcome == RemediationOutcome.TRANSFER_CONFIRMED else "Transfer attempt completed",
                status="COMPLETED",
            ),
            transfer_question_id="UNI-RENAL-001-T",
            transfer_attempt=t_attempt,
            assistance_invoked=asst_invoked,
        ))

    # 2. Pattern RAAS-ENZ-01: Enzymatic cleavage role reversal (4 learners: 7-10)
    for i in range(7, 11):
        learner_id = f"demo_learner_{i:03d}"
        session_id = f"DEMO-SES-ENZ-{i:03d}"

        # 3 demonstrated (7-9), 1 failed (10)
        if i <= 9:
            outcome = RemediationOutcome.TRANSFER_CONFIRMED
            t_attempt = TransferAttempt(
                question_id="UNI-RENAL-001-T",
                submitted_option="A",
                is_correct=True,
                was_assisted=False,
            )
        else:
            outcome = RemediationOutcome.TRANSFER_NOT_CONFIRMED
            t_attempt = TransferAttempt(
                question_id="UNI-RENAL-001-T",
                submitted_option="B",
                is_correct=False,
                was_assisted=False,
            )

        sessions.append(RemediationSessionState(
            session_id=session_id,
            user_id=learner_id,
            question_id="UNI-RENAL-001",
            selected_option="D",
            topic=DEMO_TOPIC,
            turn_number=3,
            max_turns=3,
            is_complete=True,
            lifecycle_state=RemediationLifecycleState.COMPLETED,
            outcome=outcome,
            remediation_status=RemediationStatus.RESOLVED if outcome == RemediationOutcome.TRANSFER_CONFIRMED else RemediationStatus.UNRESOLVED,
            detected_gap=DetectedLearningGap(
                pattern_id="PATTERN-RAAS-ENZ-01",
                topic="RAAS mechanisms",
                category=ReasoningPatternCategory.ENZYME_ROLE_INVERSION,
                reasoning_pattern="Enzymatic cleavage role reversal between cascade steps",
                recommended_strategy=SocraticStrategyType.STEPWISE_DECOMPOSITION,
                confidence=0.80,
                detection_rationale="Learner reversed the enzymatic cleavage actions of renin versus ACE",
                evidence_references=["DOC-PMC-RENAL-0001:DOC-PMC-RENAL-0001-B0003-C01"],
            ),
            hypothesis=PatternHypothesis(
                hypothesis_id=f"HYP-ENZ-{i:03d}",
                epistemic_type=EpistemicType.HYPOTHESIS,
                detection_status=DetectionStatus.POSSIBLE_PATTERN,
                category=ReasoningPatternCategory.ENZYME_ROLE_INVERSION,
                pattern_id="PATTERN-RAAS-ENZ-01",
                candidate_pattern="Enzymatic cleavage role reversal between cascade steps",
                evidence_strength=EvidenceStrength.MODERATE,
                detection_rationale="Selected distractor indicates enzyme action reversal",
                supporting_signals=["distractor_d"],
            ),
            strategy=SocraticStrategyType.STEPWISE_DECOMPOSITION,
            timeline=ReasoningTimelineItem(
                initial_pattern="Initial option conflated renin and ACE cleavage roles",
                learning_gap="Suspected gap in proteolytic cascade roles",
                guided_practice="Stepwise decomposition completed",
                transfer_result="Transfer demonstrated on this question" if outcome == RemediationOutcome.TRANSFER_CONFIRMED else "Transfer attempt completed",
                status="COMPLETED",
            ),
            transfer_question_id="UNI-RENAL-001-T",
            transfer_attempt=t_attempt,
            assistance_invoked=False,
        ))

    # 3. Pattern RAAS-REC-01: Receptor specificity confusion (3 learners: 11-13)
    for i in range(11, 14):
        learner_id = f"demo_learner_{i:03d}"
        session_id = f"DEMO-SES-REC-{i:03d}"

        # 2 demonstrated (11-12), 1 failed (13)
        if i <= 12:
            outcome = RemediationOutcome.TRANSFER_CONFIRMED
            t_attempt = TransferAttempt(
                question_id="UNI-RENAL-002-T",
                submitted_option="B",
                is_correct=True,
                was_assisted=False,
            )
        else:
            outcome = RemediationOutcome.TRANSFER_NOT_CONFIRMED
            t_attempt = TransferAttempt(
                question_id="UNI-RENAL-002-T",
                submitted_option="E",
                is_correct=False,
                was_assisted=False,
            )

        sessions.append(RemediationSessionState(
            session_id=session_id,
            user_id=learner_id,
            question_id="UNI-RENAL-002",
            selected_option="C",
            topic=DEMO_TOPIC,
            turn_number=3,
            max_turns=3,
            is_complete=True,
            lifecycle_state=RemediationLifecycleState.COMPLETED,
            outcome=outcome,
            remediation_status=RemediationStatus.RESOLVED if outcome == RemediationOutcome.TRANSFER_CONFIRMED else RemediationStatus.UNRESOLVED,
            detected_gap=DetectedLearningGap(
                pattern_id="PATTERN-RAAS-REC-01",
                topic="RAAS mechanisms",
                category=ReasoningPatternCategory.RECEPTOR_SPECIFICITY_CONFUSION,
                reasoning_pattern="Conflating vasoactive peptide target with metabolic or autonomic receptor pathways",
                recommended_strategy=SocraticStrategyType.CONTRAST_CASE,
                confidence=0.78,
                detection_rationale="Learner selected non-angiotensin receptor pathway",
                evidence_references=["DOC-PMC-RENAL-0001:DOC-PMC-RENAL-0001-B0003-C01"],
            ),
            hypothesis=PatternHypothesis(
                hypothesis_id=f"HYP-REC-{i:03d}",
                epistemic_type=EpistemicType.HYPOTHESIS,
                detection_status=DetectionStatus.POSSIBLE_PATTERN,
                category=ReasoningPatternCategory.RECEPTOR_SPECIFICITY_CONFUSION,
                pattern_id="PATTERN-RAAS-REC-01",
                candidate_pattern="Conflating vasoactive peptide target with metabolic or autonomic receptor pathways",
                evidence_strength=EvidenceStrength.MODERATE,
                detection_rationale="Receptor selection indicates pathway crossover",
                supporting_signals=["distractor_c"],
            ),
            strategy=SocraticStrategyType.CONTRAST_CASE,
            timeline=ReasoningTimelineItem(
                initial_pattern="Option choice conflated AT1 with beta-adrenergic pathways",
                learning_gap="Suspected gap in receptor selectivity",
                guided_practice="Contrast case completed",
                transfer_result="Transfer demonstrated on this question" if outcome == RemediationOutcome.TRANSFER_CONFIRMED else "Transfer attempt completed",
                status="COMPLETED",
            ),
            transfer_question_id="UNI-RENAL-002-T",
            transfer_attempt=t_attempt,
            assistance_invoked=False,
        ))

    # 4. Ineligible sessions for learner 14 (Safety fallback & Insufficient evidence)
    # Learner 14 - Safety fallback session (MUST be excluded by aggregator from pattern counts!)
    sessions.append(RemediationSessionState(
        session_id="DEMO-SES-FALLBACK-014",
        user_id="demo_learner_014",
        question_id="UNI-RENAL-001",
        selected_option="B",
        topic=DEMO_TOPIC,
        turn_number=1,
        max_turns=3,
        is_complete=True,
        lifecycle_state=RemediationLifecycleState.COMPLETED,
        outcome=RemediationOutcome.SAFETY_FALLBACK,
        remediation_status=RemediationStatus.UNRESOLVED,
        detected_gap=DetectedLearningGap(
            pattern_id="PATTERN-RAAS-SUB-01",
            topic="RAAS mechanisms",
            category=ReasoningPatternCategory.UPSTREAM_DOWNSTREAM_INVERSION,
            reasoning_pattern="Substrate versus product role inversion in enzymatic cascade",
            recommended_strategy=SocraticStrategyType.CONTRAST_CASE,
            confidence=0.85,
            detection_rationale="Substrate selection",
            evidence_references=[],
        ),
        timeline=ReasoningTimelineItem(
            initial_pattern="Initial selection",
            learning_gap="Unverified",
            guided_practice="Remediation concluded due to safety fallback",
            transfer_result="Remediation stopped safely; no transfer assessment performed.",
            status="SAFETY_FALLBACK",
        ),
        turns=[RemediationTurnRecord(
            turn_number=1,
            phase="PROBE",
            tutor_message="Remediation could not safely confirm clinical accuracy for this step. Please continue to other practice areas.",
            is_safety_fallback=True,
        )],
        transfer_question_id=None,
        transfer_attempt=None,
    ))

    return sessions
