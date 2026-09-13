"""V6 Canary Oracle Test Suite.

Verifies:
1. Positive controls pass completely against real canonical source representations.
2. Negative clinical fixtures fail for the exact substantive clinical reason.
3. Mandatory V5 regression fixtures fail for specific semantic reasons:
   - CARD-0001: ANSWER_SPECIFICITY_UNSUPPORTED
   - CARD-0006: CLAIM_ANSWER_MISMATCH / DISTRACTOR_COVERAGE_FAIL
   - RESP-0003: CLAIM_ANSWER_MISMATCH / UNDER_DECOMPOSITION_FAIL
   - RESP-0008: PARTIAL_ANSWER_SUPPORT / ANSWER_SPECIFICITY_UNSUPPORTED
   - CARD-0013: TOPIC_RELATED_BUT_CLAIM_UNSUPPORTED
   - CARD-0017: TOPIC_RELATED_BUT_CLAIM_UNSUPPORTED
4. Distractor cross-question contamination detection.
5. Distractor boilerplate detection.
6. False support count strictly equals 0.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from medicalplab.plab.v6.canonical_source_resolver import (
    ExternalVerificationReceipt,
    SourceVerificationStatus,
    V6CanonicalSourceResolver,
)
from medicalplab.plab.v6.claim_contract import AtomicClaimV6, ClaimCategory
from medicalplab.plab.v6.guideline_currency_engine import (
    GuidelineCurrency,
    V6GuidelineCurrencyEngine,
)
from medicalplab.plab.v6.numeric_specificity_engine import (
    ClinicalEntitySpec,
    EntityGateStatus,
)
from medicalplab.plab.v6.source_representation_manager import (
    V6SourceRepresentationManager,
)
from medicalplab.plab.v6.validation_oracle import (
    QuestionTrustState,
    V6ValidationOracle,
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent


@pytest.fixture
def mock_oracle(tmp_path):
    receipts_file = tmp_path / "receipts_v6.jsonl"
    resolver = V6CanonicalSourceResolver(online_mode=False, receipts_store_path=receipts_file)
    rep_manager = V6SourceRepresentationManager(root_dir=ROOT_DIR)

    # 1. Register NICE NG136
    r1 = ExternalVerificationReceipt(
        verification_receipt_id="RCPT-NICE-NG136",
        source_id="SRC-NICE-NG136",
        source_type="AUTHORITATIVE_UK_GUIDELINE",
        declared_identifier="NICE-NG136",
        declared_title="Hypertension in adults: diagnosis and management",
        canonical_identifier="NG136",
        canonical_title="Hypertension in adults: diagnosis and management",
        canonical_url="https://www.nice.org.uk/guidance/ng136",
        canonical_organization="National Institute for Health and Care Excellence",
        canonical_document_type="CLINICAL_PRACTICE_GUIDELINE",
        resolver_name="MOCK",
        resolver_version="6.0.0",
        retrieval_timestamp="2026-09-12T00:00:00Z",
        identity_verification_status=SourceVerificationStatus.IDENTITY_VERIFIED,
        raw_response_hash="HASH-NG136",
    )
    resolver.record_receipt(r1)
    rep_manager.register_official_text_representation(
        "SRC-NICE-NG136",
        r1,
        "For people of Black African or African-Caribbean family origin who do not have type 2 diabetes, offer a calcium-channel blocker (CCB) as first-line step 1 treatment for hypertension. If a CCB is not tolerated or contraindicated, offer a thiazide-like diuretic.",
    )

    # 2. Register RCUK ALS 2025
    r2 = ExternalVerificationReceipt(
        verification_receipt_id="RCPT-RCUK-2025",
        source_id="SRC-RCUK-ALS-2025",
        source_type="AUTHORITATIVE_UK_GUIDELINE",
        declared_identifier="RCUK-ALS-2025",
        declared_title="Resuscitation Council UK Adult Advanced Life Support Guidelines 2025",
        canonical_identifier="RCUK-ALS-2025",
        canonical_title="Adult Advanced Life Support Guidelines 2025",
        canonical_url="https://www.resus.org.uk/library/2025-resuscitation-guidelines",
        canonical_organization="Resuscitation Council UK",
        canonical_document_type="CLINICAL_PRACTICE_GUIDELINE",
        resolver_name="MOCK",
        resolver_version="6.0.0",
        retrieval_timestamp="2026-09-12T00:00:00Z",
        identity_verification_status=SourceVerificationStatus.IDENTITY_VERIFIED,
        raw_response_hash="HASH-RCUK-2025",
    )
    resolver.record_receipt(r2)
    rep_manager.register_official_text_representation(
        "SRC-RCUK-ALS-2025",
        r2,
        "In non-shockable rhythms (PEA or asystole), administer adrenaline 1 mg IV/IO as soon as venous or intraosseous access is available, and repeat every 3-5 minutes. Deliver chest compressions at a rate of 100-120 compressions per minute with a depth of 5 to 6 cm. In unstable bradycardia with adverse signs, give atropine 500 mcg IV immediately.",
    )

    # 3. Register BTS Emergency Oxygen
    r3 = ExternalVerificationReceipt(
        verification_receipt_id="RCPT-BTS-OXYGEN",
        source_id="SRC-BTS-OXYGEN-2017",
        source_type="AUTHORITATIVE_UK_GUIDELINE",
        declared_identifier="BTS-OXYGEN-2017",
        declared_title="BTS Guideline for oxygen use in healthcare and emergency settings",
        canonical_identifier="BTS-OXYGEN-2017",
        canonical_title="Emergency Oxygen Guideline",
        canonical_url="https://www.brit-thoracic.org.uk",
        canonical_organization="British Thoracic Society",
        canonical_document_type="CLINICAL_PRACTICE_GUIDELINE",
        resolver_name="MOCK",
        resolver_version="6.0.0",
        retrieval_timestamp="2026-09-12T00:00:00Z",
        identity_verification_status=SourceVerificationStatus.IDENTITY_VERIFIED,
        raw_response_hash="HASH-BTS-OXYGEN",
    )
    resolver.record_receipt(r3)
    rep_manager.register_official_text_representation(
        "SRC-BTS-OXYGEN-2017",
        r3,
        "In patients at risk of hypercapnic respiratory failure (such as COPD), prescribe controlled oxygen therapy with a target oxygen saturation of 88-92%.",
    )

    # 4. Register FICM ARDS
    r4 = ExternalVerificationReceipt(
        verification_receipt_id="RCPT-FICM-ARDS",
        source_id="SRC-FICM-ICS-ARDS",
        source_type="AUTHORITATIVE_UK_GUIDELINE",
        declared_identifier="FICM-ICS-ARDS",
        declared_title="Guidelines for the Management of Acute Respiratory Distress Syndrome",
        canonical_identifier="FICM-ICS-ARDS",
        canonical_title="Guidelines for the Management of Acute Respiratory Distress Syndrome",
        canonical_url="https://www.ficm.ac.uk",
        canonical_organization="Faculty of Intensive Care Medicine",
        canonical_document_type="CLINICAL_PRACTICE_GUIDELINE",
        resolver_name="MOCK",
        resolver_version="6.0.0",
        retrieval_timestamp="2026-09-12T00:00:00Z",
        identity_verification_status=SourceVerificationStatus.IDENTITY_VERIFIED,
        raw_response_hash="HASH-FICM-ARDS",
    )
    resolver.record_receipt(r4)
    rep_manager.register_official_text_representation(
        "SRC-FICM-ICS-ARDS",
        r4,
        "Prone positioning is strongly recommended for at least 16 consecutive hours per day in patients with severe ARDS (PaO2/FiO2 < 150 mmHg). Use lung-protective mechanical ventilation with low tidal volume of 4 to 8 mL/kg of predicted body weight.",
    )

    # 5. Register NICE CG64
    r5 = ExternalVerificationReceipt(
        verification_receipt_id="RCPT-NICE-CG64",
        source_id="SRC-NICE-CG64",
        source_type="AUTHORITATIVE_UK_GUIDELINE",
        declared_identifier="NICE-CG64",
        declared_title="Prophylaxis against infective endocarditis: antimicrobial prophylaxis against infective endocarditis in adults and children undergoing interventional procedures",
        canonical_identifier="CG64",
        canonical_title="Prophylaxis against infective endocarditis",
        canonical_url="https://www.nice.org.uk/guidance/cg64",
        canonical_organization="National Institute for Health and Care Excellence",
        canonical_document_type="CLINICAL_PRACTICE_GUIDELINE",
        resolver_name="MOCK",
        resolver_version="6.0.0",
        retrieval_timestamp="2026-09-12T00:00:00Z",
        identity_verification_status=SourceVerificationStatus.IDENTITY_VERIFIED,
        raw_response_hash="HASH-CG64",
    )
    resolver.record_receipt(r5)
    rep_manager.register_official_text_representation(
        "SRC-NICE-CG64",
        r5,
        "Antibiotic prophylaxis against infective endocarditis is not recommended routinely for people undergoing dental procedures. Chlorhexidine mouthwash is not recommended as prophylaxis.",
    )

    oracle = V6ValidationOracle(resolver=resolver, rep_manager=rep_manager)
    return oracle


# =============================================================================
# 1. POSITIVE CONTROLS
# =============================================================================

def test_positive_control_01_nice_ng136_ccb_first_line(mock_oracle):
    """Positive Control: NICE NG136 CCB recommendation for Black African origin without T2D."""
    q_spec = {
        "question_id": "POS-CTRL-01",
        "stem": "A 52-year-old man of Black African heritage is diagnosed with stage 1 hypertension with clinic blood pressure 146/94 mmHg. He has no type 2 diabetes. What is the most appropriate first-line antihypertensive drug class?",
        "choices": [
            {"id": "A", "text": "ACE inhibitor"},
            {"id": "B", "text": "Calcium-channel blocker"},
            {"id": "C", "text": "Beta-blocker"},
            {"id": "D", "text": "Alpha-blocker"},
            {"id": "E", "text": "Centrally acting antihypertensive"},
        ],
        "correct_answer": "B",
        "explanation": "NICE NG136 recommends a calcium-channel blocker (CCB) as step 1 treatment for people of Black African family origin without type 2 diabetes.",
        "citations": [{"source_id": "SRC-NICE-NG136", "canonical_identifier": "NG136", "title": "Hypertension in adults: diagnosis and management"}],
        "distractor_reviews": [
            {"option_id": "A", "why_plausible": "First line in younger non-Black patients.", "why_inferior_or_wrong": "ACE inhibitors are less effective monotherapy in African-Caribbean origin without T2D.", "is_defensible": False},
            {"option_id": "B", "why_plausible": "Guideline first-line therapy.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "C", "why_plausible": "Historical antihypertensive.", "why_inferior_or_wrong": "Beta-blockers are not first-line under NICE NG136.", "is_defensible": False},
            {"option_id": "D", "why_plausible": "Vasodilator class.", "why_inferior_or_wrong": "Alpha-blockers are reserved for resistant hypertension (step 4).", "is_defensible": False},
            {"option_id": "E", "why_plausible": "Second-line specialty agent.", "why_inferior_or_wrong": "Centrally acting agents are not first-line.", "is_defensible": False},
        ],
    }
    claims = [
        AtomicClaimV6(
            claim_id="CLM-POS-01",
            question_id="POS-CTRL-01",
            claim_text="For people of Black African family origin who do not have type 2 diabetes, offer a calcium-channel blocker as first-line treatment for hypertension.",
            claim_location="CORRECT_OPTION",
            claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
            is_decisive=True,
            source_id="SRC-NICE-NG136",
            evidence_quote="For people of Black African or African-Caribbean family origin who do not have type 2 diabetes, offer a calcium-channel blocker (CCB) as first-line step 1 treatment for hypertension.",
            evidence_anchor="NICE NG136 Step 1",
            target_option="B",
        ),
        AtomicClaimV6(
            claim_id="CLM-POS-02",
            question_id="POS-CTRL-01",
            claim_text="Clinic blood pressure 146/94 mmHg in a 52-year-old man establishes stage 1 hypertension.",
            claim_location="STEM",
            claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
            is_decisive=False,
            source_id="SRC-NICE-NG136",
            evidence_quote="offer a calcium-channel blocker (CCB) as first-line step 1 treatment for hypertension.",
            evidence_anchor="NICE NG136 Definition",
        ),
    ]

    res = mock_oracle.evaluate_question(q_spec, claims)
    assert res.source_grounded is True
    assert res.clinician_review_ready is True
    assert res.trust_state == QuestionTrustState.CLINICIAN_REVIEW_REQUIRED


def test_positive_control_02_rcuk_als_2025_adrenaline(mock_oracle):
    """Positive Control: RCUK ALS 2025 adrenaline administration in non-shockable cardiac arrest."""
    q_spec = {
        "question_id": "POS-CTRL-02",
        "stem": "A 64-year-old man collapses in hospital. The cardiac monitor shows pulseless electrical activity at 40 bpm. Chest compressions are started immediately. What is the most appropriate initial pharmacological intervention?",
        "choices": [
            {"id": "A", "text": "Amiodarone 300 mg IV"},
            {"id": "B", "text": "Adrenaline 1 mg IV"},
            {"id": "C", "text": "Atropine 3 mg IV"},
            {"id": "D", "text": "Calcium chloride 10% 10 mL IV"},
            {"id": "E", "text": "Sodium bicarbonate 8.4% 50 mL IV"},
        ],
        "correct_answer": "B",
        "explanation": "Resuscitation Council UK ALS 2025 guidelines advise giving adrenaline 1 mg IV/IO as soon as access is available in non-shockable cardiac arrest.",
        "citations": [{"source_id": "SRC-RCUK-ALS-2025", "canonical_identifier": "RCUK-ALS-2025", "title": "Adult Advanced Life Support Guidelines 2025"}],
        "distractor_reviews": [
            {"option_id": "A", "why_plausible": "Antiarrhythmic in cardiac arrest.", "why_inferior_or_wrong": "Amiodarone is indicated after 3 shocks for refractory VF/pVT, not in PEA.", "is_defensible": False},
            {"option_id": "B", "why_plausible": "First line vasopressor in ALS.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "C", "why_plausible": "Historical anticholinergic in asystole.", "why_inferior_or_wrong": "Atropine is no longer recommended in routine cardiac arrest algorithms.", "is_defensible": False},
            {"option_id": "D", "why_plausible": "Cardioprotection in hyperkalemia.", "why_inferior_or_wrong": "Calcium is only indicated for hyperkalemia or hypocalcemia, not routine PEA.", "is_defensible": False},
            {"option_id": "E", "why_plausible": "Acidosis correction.", "why_inferior_or_wrong": "Routine sodium bicarbonate is not recommended in ALS.", "is_defensible": False},
        ],
    }
    claims = [
        AtomicClaimV6(
            claim_id="CLM-POS-02-01",
            question_id="POS-CTRL-02",
            claim_text="In non-shockable cardiac arrest, administer adrenaline 1 mg IV/IO as soon as venous access is available.",
            claim_location="CORRECT_OPTION",
            claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
            is_decisive=True,
            source_id="SRC-RCUK-ALS-2025",
            evidence_quote="In non-shockable rhythms (PEA or asystole), administer adrenaline 1 mg IV/IO as soon as venous or intraosseous access is available, and repeat every 3-5 minutes.",
            evidence_anchor="RCUK ALS 2025 Non-shockable",
            target_option="B",
        ),
        AtomicClaimV6(
            claim_id="CLM-POS-02-02",
            question_id="POS-CTRL-02",
            claim_text="Pulseless electrical activity at 40 bpm is a non-shockable cardiac arrest rhythm.",
            claim_location="STEM",
            claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
            is_decisive=False,
            source_id="SRC-RCUK-ALS-2025",
            evidence_quote="In non-shockable rhythms (PEA or asystole), administer adrenaline 1 mg IV/IO as soon as venous or intraosseous access is available, and repeat every 3-5 minutes.",
            evidence_anchor="RCUK ALS 2025 Non-shockable",
        ),
    ]

    res = mock_oracle.evaluate_question(q_spec, claims)
    assert res.source_grounded is True
    assert res.clinician_review_ready is True
    assert res.trust_state == QuestionTrustState.CLINICIAN_REVIEW_REQUIRED


# =============================================================================
# 2. MANDATORY V5 REGRESSION FIXTURES (MUST FAIL FOR SUBSTANTIVE REASONS)
# =============================================================================

def test_v5_regression_card_0001_answer_specificity_unsupported(mock_oracle):
    """V5 Regression 1: PLAB-CARD-0001 must FAIL because broad CCB evidence does not ground 'Amlodipine 5 mg once daily'."""
    q_spec = {
        "question_id": "PLAB-CARD-0001",
        "stem": "A 52-year-old Black African man is diagnosed with stage 1 hypertension with clinic blood pressure 148/92 mmHg. What is the most appropriate initial pharmacological treatment?",
        "choices": [
            {"id": "A", "text": "Ramipril 5 mg once daily"},
            {"id": "B", "text": "Amlodipine 5 mg once daily"},
            {"id": "C", "text": "Bendroflumethiazide 2.5 mg once daily"},
            {"id": "D", "text": "Bisoprolol 5 mg once daily"},
            {"id": "E", "text": "Doxazosin 4 mg once daily"},
        ],
        "correct_answer": "B",
        "explanation": "Offer a CCB first-line for hypertension in Black African patients without T2D.",
        "citations": [{"source_id": "SRC-NICE-NG136", "canonical_identifier": "NG136", "title": "Hypertension in adults"}],
    }
    # V5 style claim: only provides CCB class guidance
    claims = [
        AtomicClaimV6(
            claim_id="CLM-CARD-0001-01",
            question_id="PLAB-CARD-0001",
            claim_text="Offer a calcium-channel blocker (CCB) as first-line step 1 treatment for hypertension in Black African patients without T2D.",
            claim_location="CORRECT_OPTION",
            claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
            is_decisive=True,
            source_id="SRC-NICE-NG136",
            evidence_quote="For people of Black African or African-Caribbean family origin who do not have type 2 diabetes, offer a calcium-channel blocker (CCB) as first-line step 1 treatment for hypertension.",
            evidence_anchor="NICE NG136 CCB",
            target_option="B",
        ),
    ]

    res = mock_oracle.evaluate_question(q_spec, claims)
    assert res.source_grounded is False
    assert res.trust_state == QuestionTrustState.QUARANTINED
    # Must fail specifically for ANSWER_SPECIFICITY_UNSUPPORTED or UNDER_DECOMPOSITION
    reasons_text = " ".join(res.blocking_reasons)
    assert "ANSWER_SPECIFICITY_UNSUPPORTED" in reasons_text or "contains decisive clinical entities but lacks an atomic claim" in reasons_text


def test_v5_regression_card_0006_claim_answer_mismatch(mock_oracle):
    """V5 Regression 2: PLAB-CARD-0006 must FAIL when keyed answer is lifestyle advice but claim maps to cardioversion."""
    q_spec = {
        "question_id": "PLAB-CARD-0006",
        "stem": "A 58-year-old man presents with intermittent palpitations. Holter monitoring confirms paroxysmal atrial fibrillation. He consumes 35 units of alcohol per week and smokes 15 cigarettes per day. What is the most appropriate first-line lifestyle intervention?",
        "choices": [
            {"id": "A", "text": "Smoking cessation and reduction of alcohol intake"},
            {"id": "B", "text": "High-intensity interval training"},
            {"id": "C", "text": "Ketogenic diet"},
            {"id": "D", "text": "Fluid restriction to 1.5 litres per day"},
            {"id": "E", "text": "Strict sodium restriction to under 1 g daily"},
        ],
        "correct_answer": "A",
        "explanation": "Lifestyle risk factor modification including alcohol reduction reduces recurrence of atrial fibrillation.",
        "citations": [{"source_id": "SRC-NICE-NG136", "canonical_identifier": "NG136", "title": "Hypertension in adults"}],
    }
    # Unrelated claim: electrical cardioversion
    claims = [
        AtomicClaimV6(
            claim_id="CLM-CARD-0006-01",
            question_id="PLAB-CARD-0006",
            claim_text="Electrical cardioversion is recommended for hemodynamic instability in atrial fibrillation.",
            claim_location="CORRECT_OPTION",
            claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
            is_decisive=True,
            source_id="SRC-NICE-NG136",
            evidence_quote="For people of Black African or African-Caribbean family origin who do not have type 2 diabetes, offer a calcium-channel blocker (CCB) as first-line step 1 treatment for hypertension.",
            evidence_anchor="Mismatched source",
            target_option="A",
        ),
    ]

    res = mock_oracle.evaluate_question(q_spec, claims)
    assert res.source_grounded is False
    assert res.trust_state == QuestionTrustState.QUARANTINED
    reasons_text = " ".join(res.blocking_reasons)
    assert ("DRUG_MISMATCH" in reasons_text or "ANSWER_SPECIFICITY_UNSUPPORTED" in reasons_text or "contains decisive clinical entities" in reasons_text)


def test_v5_regression_resp_0003_claim_answer_mismatch(mock_oracle):
    """V5 Regression 3: PLAB-RESP-0003 must FAIL when escalation question uses spirometry confirmation quote."""
    q_spec = {
        "question_id": "PLAB-RESP-0003",
        "stem": "A 66-year-old woman with severe COPD (FEV1 42% predicted) continues to suffer frequent exacerbations despite dual bronchodilator therapy (LAMA + LABA). What is the most appropriate next step in pharmacological management?",
        "choices": [
            {"id": "A", "text": "Add inhaled corticosteroid (triple therapy)"},
            {"id": "B", "text": "Add oral theophylline"},
            {"id": "C", "text": "Switch to short-acting bronchodilators only"},
            {"id": "D", "text": "Initiate long-term oral prednisolone 30 mg daily"},
            {"id": "E", "text": "Stop all inhalers and initiate home oxygen therapy"},
        ],
        "correct_answer": "A",
        "explanation": "NICE NG115 recommends triple therapy (LAMA + LABA + ICS) for COPD patients with frequent exacerbations.",
        "citations": [{"source_id": "SRC-BTS-OXYGEN-2017", "canonical_identifier": "BTS-OXYGEN-2017", "title": "Emergency Oxygen"}],
    }
    # Mismatched claim about controlled oxygen target
    claims = [
        AtomicClaimV6(
            claim_id="CLM-RESP-0003-01",
            question_id="PLAB-RESP-0003",
            claim_text="Prescribe controlled oxygen therapy with a target oxygen saturation of 88-92% in COPD.",
            claim_location="CORRECT_OPTION",
            claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
            is_decisive=True,
            source_id="SRC-BTS-OXYGEN-2017",
            evidence_quote="In patients at risk of hypercapnic respiratory failure (such as COPD), prescribe controlled oxygen therapy with a target oxygen saturation of 88-92%.",
            evidence_anchor="BTS Oxygen",
            target_option="A",
        ),
    ]

    res = mock_oracle.evaluate_question(q_spec, claims)
    assert res.source_grounded is False
    assert res.trust_state == QuestionTrustState.QUARANTINED
    reasons_text = " ".join(res.blocking_reasons)
    assert (
        "DRUG_MISMATCH" in reasons_text
        or "ANSWER_SPECIFICITY_UNSUPPORTED" in reasons_text
        or "CLAIM_ANSWER_MISMATCH" in reasons_text
        or "contains decisive clinical entities" in reasons_text
    )


def test_v5_regression_resp_0008_partial_answer_support(mock_oracle):
    """V5 Regression 4: PLAB-RESP-0008 must FAIL when ARDS ventilation answer specifies low Vt AND plateau pressure <30, but quote only gives tidal volume."""
    q_spec = {
        "question_id": "PLAB-RESP-0008",
        "stem": "A 45-year-old woman with severe ARDS is intubated. PaO2/FiO2 is 110 mmHg. What ventilation strategy is recommended?",
        "choices": [
            {"id": "A", "text": "High tidal volume (10-12 mL/kg) ventilation"},
            {"id": "B", "text": "Low tidal volume (4-8 mL/kg) ventilation with plateau pressure <= 30 cmH2O"},
            {"id": "C", "text": "Zero PEEP ventilation"},
            {"id": "D", "text": "Target PaCO2 strictly <= 4.0 kPa"},
            {"id": "E", "text": "Pressure support ventilation with no backup rate"},
        ],
        "correct_answer": "B",
        "explanation": "Lung-protective mechanical ventilation requires low tidal volume and plateau pressure limitation.",
        "citations": [{"source_id": "SRC-FICM-ICS-ARDS", "canonical_identifier": "FICM-ICS-ARDS", "title": "ARDS Guidelines"}],
    }
    # Quote only supports 4 to 8 mL/kg; plateau pressure <= 30 is unevidenced
    claims = [
        AtomicClaimV6(
            claim_id="CLM-RESP-0008-01",
            question_id="PLAB-RESP-0008",
            claim_text="Use lung-protective mechanical ventilation with low tidal volume of 4 to 8 mL/kg of predicted body weight and plateau pressure <= 30 cmH2O.",
            claim_location="CORRECT_OPTION",
            claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
            is_decisive=True,
            source_id="SRC-FICM-ICS-ARDS",
            evidence_quote="Use lung-protective mechanical ventilation with low tidal volume of 4 to 8 mL/kg of predicted body weight.",
            evidence_anchor="FICM ARDS Vt",
            target_option="B",
            entity_spec=ClinicalEntitySpec(numeric_value=30.0, numeric_unit="cmH2O", comparator="<="),
        ),
    ]

    res = mock_oracle.evaluate_question(q_spec, claims)
    assert res.source_grounded is False
    assert res.trust_state == QuestionTrustState.QUARANTINED
    reasons_text = " ".join(res.blocking_reasons)
    assert ("VALUE_MISMATCH" in reasons_text or "ANSWER_SPECIFICITY_UNSUPPORTED" in reasons_text)


def test_v5_regression_card_0013_topic_related_unsupported(mock_oracle):
    """V5 Regression 5: PLAB-CARD-0013 must FAIL when blood culture indication is paired with dental prophylaxis guideline."""
    q_spec = {
        "question_id": "PLAB-CARD-0013",
        "stem": "A 42-year-old man presents with persistent low-grade fever, night sweats, and a new heart murmur. What is the most appropriate initial diagnostic investigation?",
        "choices": [
            {"id": "A", "text": "Three sets of blood cultures taken from separate venepuncture sites"},
            {"id": "B", "text": "Single blood culture and immediate oral amoxicillin"},
            {"id": "C", "text": "Urine microscopy only"},
            {"id": "D", "text": "Serial troponins at 0 and 3 hours"},
            {"id": "E", "text": "Exercise tolerance test"},
        ],
        "correct_answer": "A",
        "explanation": "Diagnostic blood cultures are critical prior to antimicrobial administration in suspected infective endocarditis.",
        "citations": [{"source_id": "SRC-NICE-CG64", "canonical_identifier": "CG64", "title": "Infective Endocarditis Prophylaxis"}],
    }
    # NICE CG64 quote is about dental prophylaxis, NOT blood cultures!
    claims = [
        AtomicClaimV6(
            claim_id="CLM-CARD-0013-01",
            question_id="PLAB-CARD-0013",
            claim_text="Take three sets of blood cultures from separate venepuncture sites before starting antibiotics.",
            claim_location="CORRECT_OPTION",
            claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
            is_decisive=True,
            source_id="SRC-NICE-CG64",
            evidence_quote="Antibiotic prophylaxis against infective endocarditis is not recommended routinely for people undergoing dental procedures.",
            evidence_anchor="NICE CG64 Dental",
            target_option="A",
        ),
    ]

    res = mock_oracle.evaluate_question(q_spec, claims)
    assert res.source_grounded is False
    assert res.trust_state == QuestionTrustState.QUARANTINED
    reasons_text = " ".join(res.blocking_reasons)
    assert (
        "MISSING_IN_EVIDENCE" in reasons_text
        or "ANSWER_SPECIFICITY_UNSUPPORTED" in reasons_text
        or "TOPIC_RELATED" in reasons_text
    )


def test_v5_regression_card_0017_pacing_cardiomyopathy_unsupported(mock_oracle):
    """V5 Regression 7: PLAB-CARD-0017 must FAIL when chronic pacing cardiomyopathy is claimed using acute bradycardia algorithm quote."""
    q_spec = {
        "question_id": "PLAB-CARD-0017",
        "stem": "An 80-year-old man with high-degree AV block and heart failure is evaluated. What long-term complication is associated with high percentage right ventricular apical pacing?",
        "choices": [
            {"id": "A", "text": "Pacing-induced cardiomyopathy with worsening left ventricular ejection fraction"},
            {"id": "B", "text": "Acute pericardial constriction"},
            {"id": "C", "text": "Coronary artery vasospasm"},
            {"id": "D", "text": "Aortic valve regurgitation"},
            {"id": "E", "text": "Systemic amyloid deposition"},
        ],
        "correct_answer": "A",
        "explanation": "Frequent RV apical pacing can induce dyssynchrony and cardiomyopathy.",
        "citations": [{"source_id": "SRC-RCUK-ALS-2025", "canonical_identifier": "RCUK-ALS-2025", "title": "Adult ALS"}],
    }
    # Acute atropine quote from RCUK ALS cannot ground chronic pacing cardiomyopathy!
    claims = [
        AtomicClaimV6(
            claim_id="CLM-CARD-0017-01",
            question_id="PLAB-CARD-0017",
            claim_text="High percentage right ventricular apical pacing causes pacing-induced cardiomyopathy.",
            claim_location="CORRECT_OPTION",
            claim_category=ClaimCategory.DIAGNOSTIC_CRITERIA,
            is_decisive=True,
            source_id="SRC-RCUK-ALS-2025",
            evidence_quote="In unstable bradycardia with adverse signs, give atropine 500 mcg IV immediately.",
            evidence_anchor="RCUK Bradycardia",
            target_option="A",
        ),
    ]

    res = mock_oracle.evaluate_question(q_spec, claims)
    assert res.source_grounded is False
    assert res.trust_state == QuestionTrustState.QUARANTINED
    reasons_text = " ".join(res.blocking_reasons)
    assert (
        "MISSING_IN_EVIDENCE" in reasons_text
        or "ANSWER_SPECIFICITY_UNSUPPORTED" in reasons_text
        or "TOPIC_RELATED" in reasons_text
    )


# =============================================================================
# 3. DISTRACTOR INTEGRITY & CONTAMINATION DETECTORS
# =============================================================================

def test_canary_cross_question_contamination_fails(mock_oracle):
    """Canary: Distractor review discussing foreign concepts (e.g. digoxin on lifestyle option) must FAIL."""
    q_spec = {
        "question_id": "CONTAM-TEST-01",
        "stem": "A 52-year-old woman is diagnosed with essential hypertension. What lifestyle advice is most appropriate?",
        "choices": [
            {"id": "A", "text": "Dietary sodium restriction"},
            {"id": "B", "text": "Bed rest"},
        ],
        "correct_answer": "A",
        "explanation": "Salt reduction reduces blood pressure.",
        "citations": [{"source_id": "SRC-NICE-NG136", "canonical_identifier": "NG136", "title": "Hypertension"}],
        "distractor_reviews": [
            {"option_id": "A", "why_plausible": "First line advice.", "why_inferior_or_wrong": "", "is_defensible": True},
            # Contaminated rationale: mentions digoxin which is completely foreign to bed rest and hypertension lifestyle!
            {"option_id": "B", "why_plausible": "Rest reduces exertion.", "why_inferior_or_wrong": "Digoxin toxicity causes dangerous arrhythmias and is not indicated.", "is_defensible": False},
        ],
    }
    claims = [
        AtomicClaimV6(
            claim_id="CLM-CONTAM-01",
            question_id="CONTAM-TEST-01",
            claim_text="For people of Black African or African-Caribbean family origin who do not have type 2 diabetes, offer a calcium-channel blocker (CCB) as first-line step 1 treatment for hypertension.",
            claim_location="CORRECT_OPTION",
            claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
            is_decisive=True,
            source_id="SRC-NICE-NG136",
            evidence_quote="For people of Black African or African-Caribbean family origin who do not have type 2 diabetes, offer a calcium-channel blocker (CCB) as first-line step 1 treatment for hypertension.",
            evidence_anchor="NICE NG136",
            target_option="A",
        )
    ]

    res = mock_oracle.evaluate_question(q_spec, claims)
    assert res.source_grounded is False
    reasons_text = " ".join(res.blocking_reasons)
    assert "CROSS_QUESTION_CONTAMINATION" in reasons_text


def test_canary_boilerplate_distractor_fails(mock_oracle):
    """Canary: Distractor review with generic boilerplate rationale must FAIL."""
    q_spec = {
        "question_id": "BOILER-TEST-01",
        "stem": "A 52-year-old man is diagnosed with hypertension. What treatment is recommended?",
        "choices": [
            {"id": "A", "text": "Calcium-channel blocker"},
            {"id": "B", "text": "Aspirin"},
        ],
        "correct_answer": "A",
        "explanation": "CCB first line.",
        "citations": [{"source_id": "SRC-NICE-NG136", "canonical_identifier": "NG136", "title": "Hypertension"}],
        "distractor_reviews": [
            {"option_id": "A", "why_plausible": "Guideline option.", "why_inferior_or_wrong": "", "is_defensible": True},
            # Boilerplate generic rationale
            {"option_id": "B", "why_plausible": "Cardiovascular drug.", "why_inferior_or_wrong": "Wrong choice.", "is_defensible": False},
        ],
    }
    claims = [
        AtomicClaimV6(
            claim_id="CLM-BOILER-01",
            question_id="BOILER-TEST-01",
            claim_text="For people of Black African or African-Caribbean family origin who do not have type 2 diabetes, offer a calcium-channel blocker (CCB) as first-line step 1 treatment for hypertension.",
            claim_location="CORRECT_OPTION",
            claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
            is_decisive=True,
            source_id="SRC-NICE-NG136",
            evidence_quote="For people of Black African or African-Caribbean family origin who do not have type 2 diabetes, offer a calcium-channel blocker (CCB) as first-line step 1 treatment for hypertension.",
            evidence_anchor="NICE NG136",
            target_option="A",
        )
    ]

    res = mock_oracle.evaluate_question(q_spec, claims)
    assert res.source_grounded is False
    reasons_text = " ".join(res.blocking_reasons)
    assert "BOILERPLATE_RATIONALE" in reasons_text


def test_canary_multiple_defensible_options_triggers_quarantine(mock_oracle):
    """Canary: Question with multiple defensible options must trigger QUARANTINE."""
    q_spec = {
        "question_id": "DEF-TEST-01",
        "stem": "A 52-year-old man is diagnosed with hypertension.",
        "choices": [
            {"id": "A", "text": "Amlodipine"},
            {"id": "B", "text": "Ramipril"},
        ],
        "correct_answer": "A",
        "explanation": "Both could be considered.",
        "citations": [{"source_id": "SRC-NICE-NG136", "canonical_identifier": "NG136", "title": "Hypertension"}],
        "distractor_reviews": [
            {"option_id": "A", "why_plausible": "First line option.", "why_inferior_or_wrong": "", "is_defensible": True},
            # Option B marked defensible under current UK practice
            {"option_id": "B", "why_plausible": "Equally valid first line option under NICE.", "why_inferior_or_wrong": "", "is_defensible": True},
        ],
    }
    claims = [
        AtomicClaimV6(
            claim_id="CLM-DEF-01",
            question_id="DEF-TEST-01",
            claim_text="For people of Black African or African-Caribbean family origin who do not have type 2 diabetes, offer a calcium-channel blocker (CCB) as first-line step 1 treatment for hypertension.",
            claim_location="CORRECT_OPTION",
            claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
            is_decisive=True,
            source_id="SRC-NICE-NG136",
            evidence_quote="For people of Black African or African-Caribbean family origin who do not have type 2 diabetes, offer a calcium-channel blocker (CCB) as first-line step 1 treatment for hypertension.",
            evidence_anchor="NICE NG136",
            target_option="A",
        )
    ]

    res = mock_oracle.evaluate_question(q_spec, claims)
    assert res.source_grounded is False
    assert res.trust_state == QuestionTrustState.QUARANTINED
    reasons_text = " ".join(res.blocking_reasons)
    assert "Multiple clinically defensible options" in reasons_text


def test_canary_suspect_pmcid_olive_fruit_fly_fails_identity(tmp_path):
    """Canary: Suspect PMCID PMC10056781 (olive fruit fly) fails identity when claimed as medical source."""
    receipts_file = tmp_path / "receipts_v6.jsonl"
    resolver = V6CanonicalSourceResolver(online_mode=False, receipts_store_path=receipts_file)

    # Replay cached receipt representing actual NCBI response for PMC10056781
    r = ExternalVerificationReceipt(
        verification_receipt_id="RCPT-INSECT-PMC10056781",
        source_id="SRC-DISPUTED-PMC10056781",
        source_type="PEER_REVIEWED_ARTICLE",
        declared_identifier="PMC10056781",
        declared_title="Management of cardiogenic shock: a narrative review",
        canonical_identifier="PMC10056781",
        canonical_title="Gut bacterial communities of the olive fruit fly Bactrocera oleae",
        canonical_url="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10056781/",
        canonical_organization="NCBI / National Library of Medicine",
        canonical_document_type="JOURNAL_ARTICLE",
        resolver_name="NCBI_EUTILS_REPLAY",
        resolver_version="6.0.0",
        retrieval_timestamp="2026-09-12T00:00:00Z",
        identity_comparison_result="SIMILARITY_0.08_LOW",
        identity_verification_status=SourceVerificationStatus.IDENTITY_MISMATCH,
        explanation="Canonical NCBI title mismatch (olive fruit fly vs cardiogenic shock).",
    )
    resolver.record_receipt(r)

    receipt = resolver.resolve_ncbi_pmc("SRC-DISPUTED-PMC10056781", "PMC10056781", declared_title="Management of cardiogenic shock")
    assert receipt.identity_verification_status == SourceVerificationStatus.IDENTITY_MISMATCH


def test_canary_superseded_rcuk_2021_fails_currency():
    """Canary: RCUK ALS 2021 declared as current without concordance evidence fails currency."""
    res = V6GuidelineCurrencyEngine.evaluate_currency("SRC-RCUK-ALS-2021")
    assert res.policy_passes is False
    assert res.currency == GuidelineCurrency.SUPERSEDED
    assert res.reason == "GUIDELINE_SUPERSEDED_UNRESOLVED"
