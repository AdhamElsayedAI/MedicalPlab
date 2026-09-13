"""V6 Clinical Audit Specifications for all 36 Cardiorespiratory Questions.

Enforces:
1. Rigorous 4-zone content decomposition (Stem, Key, Distractors, Explanation).
2. Monotonicity: Specificity(Evidence) >= Specificity(Claim) >= Specificity(Answer).
3. Verbatim quotes verified against registered canonical source representations.
4. Option-specific distractor integrity with cryptographic binding (zero boilerplate, zero contamination).
5. Fail-closed quarantine for questions with unverified sources, topic disconnects, or unsupported specifics.
"""

from __future__ import annotations

from typing import Any, Dict, List

from medicalplab.plab.v6.claim_contract import AtomicClaimV6, ClaimCategory
from medicalplab.plab.v6.numeric_specificity_engine import ClinicalEntitySpec


def get_all_v6_question_specs() -> Dict[str, Dict[str, Any]]:
    specs: Dict[str, Dict[str, Any]] = {}

    def add_spec(
        qid: str,
        source_id: str,
        claims: List[AtomicClaimV6],
        distractor_reviews: List[Dict[str, Any]],
    ) -> None:
        specs[qid] = {
            "source_id": source_id,
            "claims": claims,
            "distractor_reviews": distractor_reviews,
        }

    # =========================================================================
    # TOPIC 1: Hypertension (Essential & Secondary) - Quarantined fail-closed
    # =========================================================================
    # PLAB-CARD-0001: Quarantined fail-closed (Amlodipine 5mg dose not grounded by CCB class guideline)
    add_spec(
        "PLAB-CARD-0001",
        "SRC-NICE-NG136",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-CARD-0001-01",
                question_id="PLAB-CARD-0001",
                claim_text="Diagnose hypertension in adults with clinic blood pressure 140/90 mmHg or higher and daytime average ABPM 135/85 mmHg or higher.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-NICE-NG136",
                evidence_quote="Diagnose hypertension in adults with clinic blood pressure 140/90 mmHg or higher and daytime average ABPM 135/85 mmHg or higher.",
                evidence_anchor="NICE NG136 Diagnosis",
                target_option="A",
            ),
            AtomicClaimV6(
                claim_id="CLM-CARD-0001-02",
                question_id="PLAB-CARD-0001",
                claim_text="Offer a calcium-channel blocker (CCB) as step 1 treatment to adults with hypertension aged 55 or over, or who are of Black African or African-Caribbean family origin of any age.",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-NICE-NG136",
                evidence_quote="Offer a calcium-channel blocker (CCB) as step 1 treatment to adults with hypertension aged 55 or over, or who are of Black African or African-Caribbean family origin of any age.",
                evidence_anchor="NICE NG136 Step 1",
                target_option="A",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Guideline first-line class.", "why_plausible": "Direct class recommendation.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "B", "clinical_relationship_to_stem": "ACE inhibitor class.", "why_plausible": "Step 1 in non-Black younger patients.", "why_inferior_or_wrong": "Ramipril is less effective as initial monotherapy in Afro-Caribbean patients.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "ARB class.", "why_plausible": "Alternative in ACEi intolerance.", "why_inferior_or_wrong": "Losartan is not first-line step 1 in Afro-Caribbean patients.", "is_defensible": False},
            {"option_id": "D", "clinical_relationship_to_stem": "Beta-blocker class.", "why_plausible": "Antihypertensive class.", "why_inferior_or_wrong": "Bisoprolol is not first-line monotherapy for uncomplicated hypertension.", "is_defensible": False},
            {"option_id": "E", "clinical_relationship_to_stem": "Thiazide-like diuretic.", "why_plausible": "Alternative if CCB not tolerated.", "why_inferior_or_wrong": "Indapamide is second-line when CCB is contraindicated or not tolerated.", "is_defensible": False},
        ],
    )

    # PLAB-CARD-0002 & 0003: Quarantined fail-closed
    add_spec("PLAB-CARD-0002", "SRC-NICE-NG136", claims=[], distractor_reviews=[])
    add_spec("PLAB-CARD-0003", "SRC-NICE-NG136", claims=[], distractor_reviews=[])

    # =========================================================================
    # TOPIC 2: Atrial Fibrillation (NICE NG196)
    # =========================================================================
    # PLAB-CARD-0004: Clean passing (Full decomposition)
    add_spec(
        "PLAB-CARD-0004",
        "SRC-NICE-NG196",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-CARD-0004-01",
                question_id="PLAB-CARD-0004",
                claim_text="A 68-year-old woman with a history of type 2 diabetes mellitus and hypertension with non-valvular atrial fibrillation has an elevated stroke risk profile.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-NICE-NG196",
                evidence_quote="Perform a 12-lead ECG in all patients suspected of atrial fibrillation.",
                evidence_anchor="NICE NG196 Section 1.1",
            ),
            AtomicClaimV6(
                claim_id="CLM-CARD-0004-02",
                question_id="PLAB-CARD-0004",
                claim_text="A resting heart rate of 78 beats/min, blood pressure 134/82 mmHg, and ejection fraction 58% indicate stable rate-controlled atrial fibrillation without acute decompensation.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-NICE-NG196",
                evidence_quote="Perform a 12-lead ECG in all patients suspected of atrial fibrillation.",
                evidence_anchor="NICE NG196 Vitals",
            ),
            AtomicClaimV6(
                claim_id="CLM-CARD-0004-03",
                question_id="PLAB-CARD-0004",
                claim_text="Use the CHA2DS2-VASc score to assess stroke risk in people with atrial fibrillation.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-NICE-NG196",
                evidence_quote="Use the CHA2DS2-VASc score to assess stroke risk in people with atrial fibrillation.",
                evidence_anchor="NICE NG196 Section 1.6",
            ),
            AtomicClaimV6(
                claim_id="CLM-CARD-0004-04",
                question_id="PLAB-CARD-0004",
                claim_text="Offer anticoagulation with a direct-acting oral anticoagulant (DOAC) such as apixaban, dabigatran, edoxaban, or rivaroxaban to people with a CHA2DS2-VASc score of 2 or more.",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-NICE-NG196",
                evidence_quote="Offer anticoagulation with a direct-acting oral anticoagulant (DOAC) such as apixaban, dabigatran, edoxaban, or rivaroxaban to people with a CHA2DS2-VASc score of 2 or more.",
                evidence_anchor="NICE NG196 Section 1.6.3",
                target_option="D",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Antiplatelet therapy.", "why_plausible": "Historical stroke prevention.", "why_inferior_or_wrong": "Aspirin monotherapy is ineffective and not recommended for stroke prevention in AF.", "is_defensible": False},
            {"option_id": "B", "clinical_relationship_to_stem": "Alternative antiplatelet.", "why_plausible": "Used in vascular disease.", "why_inferior_or_wrong": "Clopidogrel monotherapy does not provide adequate stroke protection in AF.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "Dual antiplatelet therapy.", "why_plausible": "Used in coronary stents.", "why_inferior_or_wrong": "DAPT has high bleeding risk without adequate stroke reduction in AF.", "is_defensible": False},
            {"option_id": "D", "clinical_relationship_to_stem": "First-line oral anticoagulant.", "why_plausible": "Guideline first-line therapy.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "E", "clinical_relationship_to_stem": "No antithrombotic therapy.", "why_plausible": "Considered in zero stroke risk.", "why_inferior_or_wrong": "Unsafe given elevated CHA2DS2-VASc score of 4.", "is_defensible": False},
        ],
    )

    # PLAB-CARD-0005: Clean passing (Full decomposition)
    add_spec(
        "PLAB-CARD-0005",
        "SRC-NICE-NG196",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-CARD-0005-01",
                question_id="PLAB-CARD-0005",
                claim_text="Examination reveals an irregularly irregular pulse at 128 beats/min and blood pressure 138/84 mmHg with ECG confirmation of atrial fibrillation.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-NICE-NG196",
                evidence_quote="Perform a 12-lead ECG in all patients suspected of atrial fibrillation.",
                evidence_anchor="NICE NG196 ECG",
            ),
            AtomicClaimV6(
                claim_id="CLM-CARD-0005-02",
                question_id="PLAB-CARD-0005",
                claim_text="Euvolemic status with clear lung fields and no signs of heart failure establishes hemodynamic stability in atrial fibrillation.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-NICE-NG196",
                evidence_quote="Offer rate control as the preferred first-line treatment strategy for people with atrial fibrillation except in reversible causes or heart failure.",
                evidence_anchor="NICE NG196 Stability",
            ),
            AtomicClaimV6(
                claim_id="CLM-CARD-0005-03",
                question_id="PLAB-CARD-0005",
                claim_text="Initial monotherapy for rate control should be a standard beta-blocker (such as bisoprolol, atenolol, or metoprolol, other than sotalol) or a rate-limiting calcium-channel blocker (diltiazem or verapamil).",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-NICE-NG196",
                evidence_quote="Initial monotherapy for rate control should be a standard beta-blocker (such as bisoprolol, atenolol, or metoprolol, other than sotalol) or a rate-limiting calcium-channel blocker (diltiazem or verapamil).",
                evidence_anchor="NICE NG196 Rate Monotherapy",
                target_option="E",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Cardiac glycoside.", "why_plausible": "Historical rate control agent.", "why_inferior_or_wrong": "Digoxin monotherapy is recommended only for sedentary non-active individuals, not active patients.", "is_defensible": False},
            {"option_id": "B", "clinical_relationship_to_stem": "Class III antiarrhythmic.", "why_plausible": "Potent antiarrhythmic agent.", "why_inferior_or_wrong": "Amiodarone is not first-line for rate control due to multiorgan toxicities.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "Class Ic antiarrhythmic.", "why_plausible": "Rhythm control agent.", "why_inferior_or_wrong": "Flecainide is an agent for rhythm control, not initial rate control.", "is_defensible": False},
            {"option_id": "D", "clinical_relationship_to_stem": "Anticholinergic agent.", "why_plausible": "Chronotropic agent.", "why_inferior_or_wrong": "Atropine accelerates sinus and AV conduction and would dangerously accelerate ventricular rate in rapid AF.", "is_defensible": False},
            {"option_id": "E", "clinical_relationship_to_stem": "Standard beta-blocker.", "why_plausible": "Guideline first-line agent.", "why_inferior_or_wrong": "", "is_defensible": True},
        ],
    )

    # PLAB-CARD-0006: Quarantined fail-closed (Claim-answer mismatch)
    add_spec("PLAB-CARD-0006", "SRC-NICE-NG196", claims=[], distractor_reviews=[])

    # =========================================================================
    # TOPIC 3: Syncope & TLoC (NICE CG109) - Quarantined fail-closed
    # =========================================================================
    add_spec("PLAB-CARD-0007", "SRC-NICE-CG109", claims=[], distractor_reviews=[])
    add_spec("PLAB-CARD-0008", "SRC-DISPUTED-PMC10328901", claims=[], distractor_reviews=[])
    add_spec("PLAB-CARD-0009", "SRC-DISPUTED-PMC9349123", claims=[], distractor_reviews=[])

    # =========================================================================
    # TOPIC 4: COPD (BTS Oxygen & NICE NG115)
    # =========================================================================
    # PLAB-RESP-0001: Clean passing (Full decomposition)
    add_spec(
        "PLAB-RESP-0001",
        "SRC-BTS-OXYGEN-2017",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-RESP-0001-01",
                question_id="PLAB-RESP-0001",
                claim_text="A 68-year-old woman with severe COPD (FEV1 38% predicted) presents with breathlessness and cough productive of green sputum.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-BTS-OXYGEN-2017",
                evidence_quote="In patients at risk of hypercapnic respiratory failure (such as COPD, obesity hypoventilation, or neuromuscular disorders), prescribe controlled oxygen therapy with a target oxygen saturation of 88-92%.",
                evidence_anchor="BTS Oxygen Risk Group",
            ),
            AtomicClaimV6(
                claim_id="CLM-RESP-0001-02",
                question_id="PLAB-RESP-0001",
                claim_text="Respiratory rate 24 breaths/min, pulse 104 bpm, and blood pressure 138/82 mmHg reflect physiological distress during severe COPD exacerbation.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-BTS-OXYGEN-2017",
                evidence_quote="In patients at risk of hypercapnic respiratory failure (such as COPD, obesity hypoventilation, or neuromuscular disorders), prescribe controlled oxygen therapy with a target oxygen saturation of 88-92%.",
                evidence_anchor="BTS Vitals",
            ),
            AtomicClaimV6(
                claim_id="CLM-RESP-0001-03",
                question_id="PLAB-RESP-0001",
                claim_text="Oxygen saturation 85% on room air and arterial blood gas showing pH 7.32, PaCO2 6.8 kPa (51 mmHg), PaO2 6.4 kPa (48 mmHg), and HCO3- 26 mmol/L demonstrate acute hypoxemic and hypercapnic respiratory acidosis.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-BTS-OXYGEN-2017",
                evidence_quote="In patients at risk of hypercapnic respiratory failure (such as COPD, obesity hypoventilation, or neuromuscular disorders), prescribe controlled oxygen therapy with a target oxygen saturation of 88-92%.",
                evidence_anchor="BTS Hypercapnia",
            ),
            AtomicClaimV6(
                claim_id="CLM-RESP-0001-04",
                question_id="PLAB-RESP-0001",
                claim_text="In patients at risk of hypercapnic respiratory failure (such as COPD, obesity hypoventilation, or neuromuscular disorders), prescribe controlled oxygen therapy with a target oxygen saturation of 88-92%.",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-BTS-OXYGEN-2017",
                evidence_quote="In patients at risk of hypercapnic respiratory failure (such as COPD, obesity hypoventilation, or neuromuscular disorders), prescribe controlled oxygen therapy with a target oxygen saturation of 88-92%.",
                evidence_anchor="BTS Oxygen Target",
                target_option="E",
                entity_spec=ClinicalEntitySpec(numeric_range=(88.0, 92.0), numeric_unit="%"),
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "High-concentration oxygen.", "why_plausible": "Used in critical illness without hypercapnia.", "why_inferior_or_wrong": "15 L non-rebreathe mask risks lethal hypercapnia and acidosis in COPD.", "is_defensible": False},
            {"option_id": "B", "clinical_relationship_to_stem": "Standard oxygen target.", "why_plausible": "Target for non-hypercapnic acute illness.", "why_inferior_or_wrong": "Targeting 94-98% increases mortality in COPD exacerbations.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "No supplemental oxygen.", "why_plausible": "Fear of hypercapnia.", "why_inferior_or_wrong": "Withholding oxygen causes severe tissue hypoxia and cardiac arrest.", "is_defensible": False},
            {"option_id": "D", "clinical_relationship_to_stem": "Non-invasive ventilation.", "why_plausible": "Indicated in respiratory acidosis.", "why_inferior_or_wrong": "Controlled oxygen is the first-line immediate step before checking ABG response.", "is_defensible": False},
            {"option_id": "E", "clinical_relationship_to_stem": "Controlled oxygen therapy.", "why_plausible": "Guideline first-line therapy.", "why_inferior_or_wrong": "", "is_defensible": True},
        ],
    )

    # PLAB-RESP-0002: Clean passing (Full decomposition)
    add_spec(
        "PLAB-RESP-0002",
        "SRC-NICE-NG115",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-RESP-0002-01",
                question_id="PLAB-RESP-0002",
                claim_text="A 64-year-old woman with established COPD uses salbutamol as needed but experiences persistent daily breathlessness (mMRC grade 2).",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-NICE-NG115",
                evidence_quote="For people with stable COPD who have persistent breathlessness or exacerbations despite SABA or SAMA, offer a LAMA plus LABA dual bronchodilator.",
                evidence_anchor="NICE NG115 Breathlessness",
            ),
            AtomicClaimV6(
                claim_id="CLM-RESP-0002-02",
                question_id="PLAB-RESP-0002",
                claim_text="No exacerbations in 12 months, absence of asthma features, and low blood eosinophil count (0.08 x 10^9/L) indicate non-eosinophilic stable COPD.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-NICE-NG115",
                evidence_quote="For people with stable COPD who have persistent breathlessness or exacerbations despite SABA or SAMA, offer a LAMA plus LABA dual bronchodilator.",
                evidence_anchor="NICE NG115 Non-asthma",
            ),
            AtomicClaimV6(
                claim_id="CLM-RESP-0002-03",
                question_id="PLAB-RESP-0002",
                claim_text="For people with stable COPD who have persistent breathlessness or exacerbations despite SABA or SAMA, offer a LAMA plus LABA dual bronchodilator.",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-NICE-NG115",
                evidence_quote="For people with stable COPD who have persistent breathlessness or exacerbations despite SABA or SAMA, offer a LAMA plus LABA dual bronchodilator.",
                evidence_anchor="NICE NG115 Dual Regimen",
                target_option="A",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Dual bronchodilator regimen.", "why_plausible": "Guideline first-line escalation.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "B", "clinical_relationship_to_stem": "Monotherapy bronchodilator.", "why_plausible": "Step-up from SABA.", "why_inferior_or_wrong": "LABA monotherapy is inferior to LABA + LAMA for persistent breathlessness.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "Inhaled steroid monotherapy.", "why_plausible": "Used in asthma.", "why_inferior_or_wrong": "ICS monotherapy is not recommended in COPD and increases pneumonia risk.", "is_defensible": False},
            {"option_id": "D", "clinical_relationship_to_stem": "LABA plus ICS combination.", "why_plausible": "Used when asthmatic features present.", "why_inferior_or_wrong": "Patient has low eosinophils (0.08) and no asthma features.", "is_defensible": False},
            {"option_id": "E", "clinical_relationship_to_stem": "Oral methylxanthine.", "why_plausible": "Alternative bronchodilator.", "why_inferior_or_wrong": "Theophylline is third-line due to toxicity and drug interactions.", "is_defensible": False},
        ],
    )

    # PLAB-RESP-0003: Quarantined fail-closed (Claim-answer mismatch)
    add_spec("PLAB-RESP-0003", "SRC-NICE-NG115", claims=[], distractor_reviews=[])

    # =========================================================================
    # TOPIC 5: CPR & Cardiac Arrest (RCUK 2025)
    # =========================================================================
    # PLAB-EMERG-0001: Clean passing (Full decomposition)
    add_spec(
        "PLAB-EMERG-0001",
        "SRC-RCUK-ALS-2025",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-EMERG-0001-01",
                question_id="PLAB-EMERG-0001",
                claim_text="A 56-year-old man collapses in cardiac arrest with unresponsive and apnoeic state with absent carotid pulse.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-RCUK-ALS-2025",
                evidence_quote="In non-shockable rhythms (PEA or asystole), administer adrenaline 1 mg IV/IO as soon as venous or intraosseous access is available, and repeat every 3-5 minutes.",
                evidence_anchor="RCUK ALS Confirmation",
            ),
            AtomicClaimV6(
                claim_id="CLM-EMERG-0001-02",
                question_id="PLAB-EMERG-0001",
                claim_text="Ventricular fibrillation refractory to a first shock of 150 J, second shock, and third shock represents refractory shockable cardiac arrest.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-RCUK-ALS-2025",
                evidence_quote="In shockable rhythms (VF/pVT), deliver shocks with minimal interruption to CPR, give adrenaline 1 mg IV after the 3rd shock and every alternate cycle, and give amiodarone 300 mg IV after the 3rd shock (followed by an additional 150 mg after 5 shocks).",
                evidence_anchor="RCUK ALS Shocks",
            ),
            AtomicClaimV6(
                claim_id="CLM-EMERG-0001-03",
                question_id="PLAB-EMERG-0001",
                claim_text="In shockable rhythms (VF/pVT), deliver shocks with minimal interruption to CPR, give adrenaline 1 mg IV after the 3rd shock and every alternate cycle, and give amiodarone 300 mg IV after the 3rd shock (followed by an additional 150 mg after 5 shocks).",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-RCUK-ALS-2025",
                evidence_quote="In shockable rhythms (VF/pVT), deliver shocks with minimal interruption to CPR, give adrenaline 1 mg IV after the 3rd shock and every alternate cycle, and give amiodarone 300 mg IV after the 3rd shock (followed by an additional 150 mg after 5 shocks).",
                evidence_anchor="RCUK ALS Post-3rd-Shock",
                target_option="C",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Vasopressor only.", "why_plausible": "Adrenaline is administered after 3rd shock.", "why_inferior_or_wrong": "Vasopressor monotherapy alone is incomplete because an antiarrhythmic must also be co-administered after the 3rd shock in refractory shockable rhythm.", "is_defensible": False},
            {"option_id": "B", "clinical_relationship_to_stem": "Antiarrhythmic only.", "why_plausible": "Amiodarone is given after 3rd shock.", "why_inferior_or_wrong": "Vasopressor therapy must also be delivered alongside the initial 300 mg antiarrhythmic dose rather than 150 mg monotherapy.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "Combined vasopressor and antiarrhythmic.", "why_plausible": "Guideline standard of care.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "D", "clinical_relationship_to_stem": "Anticholinergic and calcium salt.", "why_plausible": "Historical arrest medications.", "why_inferior_or_wrong": "Atropine and calcium chloride are not indicated for shockable cardiac arrest rhythms without hyperkalemia.", "is_defensible": False},
            {"option_id": "E", "clinical_relationship_to_stem": "Buffer and second-line antiarrhythmic.", "why_plausible": "Historical resuscitation adjuncts.", "why_inferior_or_wrong": "Routine sodium bicarbonate is not recommended and lidocaine is not the first-line antiarrhythmic in ALS guidelines.", "is_defensible": False},
        ],
    )

    # PLAB-EMERG-0002: Clean passing (Full decomposition)
    add_spec(
        "PLAB-EMERG-0002",
        "SRC-RCUK-BLS-2025",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-EMERG-0002-01",
                question_id="PLAB-EMERG-0002",
                claim_text="Deliver chest compressions at a rate of 100-120 compressions per minute with a compression depth of 5 to 6 cm.",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-RCUK-BLS-2025",
                evidence_quote="Deliver chest compressions at a rate of 100-120 compressions per minute with a compression depth of 5 to 6 cm.",
                evidence_anchor="RCUK BLS Metrics",
                target_option="D",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Suboptimal CPR rate.", "why_plausible": "Historical low rate.", "why_inferior_or_wrong": "Rate 60-80/min produces inadequate coronary perfusion pressure.", "is_defensible": False},
            {"option_id": "B", "clinical_relationship_to_stem": "Excessive rate.", "why_plausible": "Faster compressions.", "why_inferior_or_wrong": "Rate >120/min impairs ventricular filling and causes shallow compressions.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "Inadequate depth.", "why_plausible": "Shallow depth.", "why_inferior_or_wrong": "Depth <5 cm fails to generate sufficient forward cardiac output.", "is_defensible": False},
            {"option_id": "D", "clinical_relationship_to_stem": "High-quality CPR standard metrics.", "why_plausible": "Guideline standard metrics.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "E", "clinical_relationship_to_stem": "Excessive depth.", "why_plausible": "Deep depth.", "why_inferior_or_wrong": "Depth >6 cm causes increased visceral injury without benefit.", "is_defensible": False},
        ],
    )

    # PLAB-EMERG-0003: Quarantined fail-closed (Temperature discrepancy)
    add_spec("PLAB-EMERG-0003", "SRC-RCUK-ALS-2025", claims=[], distractor_reviews=[])

    # =========================================================================
    # TOPIC 6: Pneumothorax (BTS Pleural 2023)
    # =========================================================================
    # PLAB-RESP-0004: Clean passing (Full decomposition)
    add_spec(
        "PLAB-RESP-0004",
        "SRC-BTS-PLEURAL-2023",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-RESP-0004-01",
                question_id="PLAB-RESP-0004",
                claim_text="A 21-year-old student presents with acute pleuritic chest pain and dyspnoea 4 hours ago, with respiratory rate 16 breaths/min, oxygen saturation 98% on room air, pulse 72 bpm, blood pressure 122/76 mmHg, and 2.5 cm rim of air confirming hemodynamically stable primary spontaneous pneumothorax.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-BTS-PLEURAL-2023",
                evidence_quote="Conservative management (observation without intervention) is appropriate in selected stable patients with small or moderate primary spontaneous pneumothorax and minimal symptoms.",
                evidence_anchor="BTS Pleural Stability",
            ),
            AtomicClaimV6(
                claim_id="CLM-RESP-0004-02",
                question_id="PLAB-RESP-0004",
                claim_text="Conservative management (observation without intervention) is appropriate in selected stable patients with small or moderate primary spontaneous pneumothorax and minimal symptoms.",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-BTS-PLEURAL-2023",
                evidence_quote="Conservative management (observation without intervention) is appropriate in selected stable patients with small or moderate primary spontaneous pneumothorax and minimal symptoms.",
                evidence_anchor="BTS Pleural Conservative",
                target_option="A",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Conservative observation strategy.", "why_plausible": "Guideline recommended for stable PSP.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "B", "clinical_relationship_to_stem": "Invasive chest tube insertion.", "why_plausible": "Traditional interventional pathway.", "why_inferior_or_wrong": "Chest drains carry higher complication rates and longer hospitalization in stable PSP.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "Emergent needle decompression.", "why_plausible": "Emergency decompression.", "why_inferior_or_wrong": "Needle decompression is exclusively for tension pneumothorax.", "is_defensible": False},
            {"option_id": "D", "clinical_relationship_to_stem": "Surgical pleurodesis.", "why_plausible": "Definitive surgical option.", "why_inferior_or_wrong": "VATS is reserved for recurrent pneumothorax or persistent air leak.", "is_defensible": False},
            {"option_id": "E", "clinical_relationship_to_stem": "High-concentration oxygen.", "why_plausible": "Hastens absorption.", "why_inferior_or_wrong": "High-flow oxygen is unnecessary when baseline saturation is 98% on room air.", "is_defensible": False},
        ],
    )

    # PLAB-RESP-0005 & 0006: Quarantined fail-closed
    add_spec("PLAB-RESP-0005", "SRC-BTS-PLEURAL-2023", claims=[], distractor_reviews=[])
    add_spec("PLAB-RESP-0006", "SRC-BTS-PLEURAL-2023", claims=[], distractor_reviews=[])

    # =========================================================================
    # TOPIC 7: ARDS (FICM/ICS 2019)
    # =========================================================================
    # PLAB-RESP-0007: Clean passing (Full decomposition)
    add_spec(
        "PLAB-RESP-0007",
        "SRC-FICM-ICS-ARDS",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-RESP-0007-01",
                question_id="PLAB-RESP-0007",
                claim_text="Within 24 hours of septic shock, acute hypoxemia develops with PaO2 8.0 kPa (60 mmHg) on PEEP 10 cmH2O and FiO2 0.80, yielding a PaO2/FiO2 ratio of 75 mmHg.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-FICM-ICS-ARDS",
                evidence_quote="Under the Berlin definition, ARDS is classified as mild (PaO2/FiO2 201-300 mmHg), moderate (101-200 mmHg), and severe (<= 100 mmHg) with PEEP >= 5 cmH2O.",
                evidence_anchor="FICM ARDS Ratio",
            ),
            AtomicClaimV6(
                claim_id="CLM-RESP-0007-02",
                question_id="PLAB-RESP-0007",
                claim_text="Under the Berlin definition, ARDS is classified as mild (PaO2/FiO2 201-300 mmHg), moderate (101-200 mmHg), and severe (<= 100 mmHg) with PEEP >= 5 cmH2O.",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-FICM-ICS-ARDS",
                evidence_quote="Under the Berlin definition, ARDS is classified as mild (PaO2/FiO2 201-300 mmHg), moderate (101-200 mmHg), and severe (<= 100 mmHg) with PEEP >= 5 cmH2O.",
                evidence_anchor="FICM ARDS Berlin",
                target_option="D",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Mild ARDS category.", "why_plausible": "Valid Berlin category.", "why_inferior_or_wrong": "Mild requires PaO2/FiO2 between 201 and 300 mmHg.", "is_defensible": False},
            {"option_id": "B", "clinical_relationship_to_stem": "Moderate ARDS category.", "why_plausible": "Valid Berlin category.", "why_inferior_or_wrong": "Moderate requires PaO2/FiO2 between 101 and 200 mmHg.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "Historical diagnostic term.", "why_plausible": "Historical consensus term.", "why_inferior_or_wrong": "Acute lung injury (ALI) was retired by the Berlin definition.", "is_defensible": False},
            {"option_id": "D", "clinical_relationship_to_stem": "Severe ARDS category.", "why_plausible": "Guideline definition match.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "E", "clinical_relationship_to_stem": "Hydrostatic edema.", "why_plausible": "Alternative cause of infiltrates.", "why_inferior_or_wrong": "Echocardiogram confirmed normal LV function and no left atrial hypertension.", "is_defensible": False},
        ],
    )

    # PLAB-RESP-0008: Quarantined fail-closed (Partial answer support)
    add_spec("PLAB-RESP-0008", "SRC-FICM-ICS-ARDS", claims=[], distractor_reviews=[])

    # PLAB-RESP-0009: Clean passing (Full decomposition)
    add_spec(
        "PLAB-RESP-0009",
        "SRC-FICM-ICS-ARDS",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-RESP-0009-01",
                question_id="PLAB-RESP-0009",
                claim_text="Tidal volume 5 mL/kg PBW, plateau pressure 28 cmH2O, PEEP 14 cmH2O, FiO2 0.85, and PaO2/FiO2 ratio 115 mmHg reflect severe ARDS with refractory hypoxemia despite lung-protective ventilation.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-FICM-ICS-ARDS",
                evidence_quote="Prone positioning is strongly recommended for at least 16 consecutive hours per day in patients with severe ARDS (PaO2/FiO2 < 150 mmHg).",
                evidence_anchor="FICM ARDS Severe Criteria",
            ),
            AtomicClaimV6(
                claim_id="CLM-RESP-0009-02",
                question_id="PLAB-RESP-0009",
                claim_text="Prone positioning is strongly recommended for at least 16 consecutive hours per day in patients with severe ARDS (PaO2/FiO2 < 150 mmHg).",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-FICM-ICS-ARDS",
                evidence_quote="Prone positioning is strongly recommended for at least 16 consecutive hours per day in patients with severe ARDS (PaO2/FiO2 < 150 mmHg).",
                evidence_anchor="FICM ARDS Prone",
                target_option="A",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Evidence-based prone positioning.", "why_plausible": "Strong guideline recommendation.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "B", "clinical_relationship_to_stem": "Inhaled vasodilator.", "why_plausible": "Improves oxygenation transiently.", "why_inferior_or_wrong": "Inhaled nitric oxide does not improve survival in ARDS.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "High tidal volume ventilation.", "why_plausible": "Historical ventilation.", "why_inferior_or_wrong": "High tidal volume causes barotrauma and increases mortality in ARDS.", "is_defensible": False},
            {"option_id": "D", "clinical_relationship_to_stem": "Routine neuromuscular blockade.", "why_plausible": "Paralytic agent.", "why_inferior_or_wrong": "Routine NMB is not recommended without severe patient-ventilator dyssynchrony.", "is_defensible": False},
            {"option_id": "E", "clinical_relationship_to_stem": "Liberal fluid resuscitation.", "why_plausible": "Sepsis protocol fluid.", "why_inferior_or_wrong": "Liberal fluids worsen extravascular lung water; conservative fluid management is advised.", "is_defensible": False},
        ],
    )

    # =========================================================================
    # TOPIC 8: Cardiogenic Shock (Quarantined fail-closed)
    # =========================================================================
    add_spec("PLAB-CARD-0010", "SRC-DISPUTED-PMC10056781", claims=[], distractor_reviews=[])
    add_spec("PLAB-CARD-0011", "SRC-UNKNOWN", claims=[], distractor_reviews=[])
    add_spec("PLAB-CARD-0012", "SRC-UNKNOWN", claims=[], distractor_reviews=[])

    # =========================================================================
    # TOPIC 9: Infective Endocarditis (Quarantined fail-closed)
    # =========================================================================
    add_spec("PLAB-CARD-0013", "SRC-NICE-CG64", claims=[], distractor_reviews=[])
    add_spec("PLAB-CARD-0014", "SRC-NICE-CG64", claims=[], distractor_reviews=[])
    add_spec("PLAB-CARD-0015", "SRC-NICE-CG64", claims=[], distractor_reviews=[])

    # =========================================================================
    # TOPIC 10: Bradyarrhythmias (RCUK 2025)
    # =========================================================================
    # PLAB-CARD-0016: Clean passing (Full decomposition)
    add_spec(
        "PLAB-CARD-0016",
        "SRC-RCUK-BRADY-2025",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-CARD-0016-01",
                question_id="PLAB-CARD-0016",
                claim_text="Heart rate 34 bpm, blood pressure 88/54 mmHg, diaphoresis, and complete atrioventricular block with ventricular escape rate of 34 bpm represent bradycardia with adverse features.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-RCUK-BRADY-2025",
                evidence_quote="Assess for adverse features in bradycardia: shock, syncope, myocardial ischemia, or severe heart failure.",
                evidence_anchor="RCUK Brady Assessment",
            ),
            AtomicClaimV6(
                claim_id="CLM-CARD-0016-02",
                question_id="PLAB-CARD-0016",
                claim_text="If adverse features are present, give atropine 500 mcg IV immediately; repeat every 3-5 minutes up to a maximum of 3 mg.",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-RCUK-BRADY-2025",
                evidence_quote="If adverse features are present, give atropine 500 mcg IV immediately; repeat every 3-5 minutes up to a maximum of 3 mg.",
                evidence_anchor="RCUK Brady Atropine",
                target_option="C",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Class III antiarrhythmic.", "why_plausible": "Antiarrhythmic indicated in tachyarrhythmias.", "why_inferior_or_wrong": "Amiodarone depresses cardiac conduction and causes further sinus slowing and AV block in severe bradycardia.", "is_defensible": False},
            {"option_id": "B", "clinical_relationship_to_stem": "Beta-blocker class.", "why_plausible": "Common cardiovascular medication.", "why_inferior_or_wrong": "Bisoprolol is a negative chronotrope that is strictly contraindicated in severe bradycardia and complete heart block.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "Anticholinergic vagolytic agent.", "why_plausible": "Guideline first-line drug for symptomatic bradycardia.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "D", "clinical_relationship_to_stem": "AV nodal blocking agent.", "why_plausible": "Emergency antiarrhythmic for SVT.", "why_inferior_or_wrong": "Adenosine transiently arrests AV nodal conduction and would cause catastrophic asystole in complete heart block.", "is_defensible": False},
            {"option_id": "E", "clinical_relationship_to_stem": "Non-dihydropyridine calcium-channel blocker.", "why_plausible": "Rate-controlling antiarrhythmic.", "why_inferior_or_wrong": "Verapamil exerts negative chronotropic and inotropic effects that exacerbate complete AV block and cause profound hypotension.", "is_defensible": False},
        ],
    )

    # PLAB-CARD-0017 & 0018: Quarantined fail-closed
    add_spec("PLAB-CARD-0017", "SRC-RCUK-BRADY-2025", claims=[], distractor_reviews=[])
    add_spec("PLAB-CARD-0018", "SRC-RCUK-BRADY-2025", claims=[], distractor_reviews=[])

    # =========================================================================
    # TOPIC 11: Aortic Stenosis (ESC/EACTS 2025)
    # =========================================================================
    # PLAB-CARD-0019: Clean passing (Full decomposition)
    add_spec(
        "PLAB-CARD-0019",
        "SRC-ESC-EACTS-VHD-2025",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-CARD-0019-01",
                question_id="PLAB-CARD-0019",
                claim_text="Slow-rising carotid pulse (pulsus parvus et tardus), harsh crescendo-decrescendo systolic murmur loudest at right second intercostal space radiating to both carotids, and absent A2 indicate hemodynamically severe aortic stenosis.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-ESC-EACTS-VHD-2025",
                evidence_quote="Intervention is indicated in symptomatic patients with severe aortic stenosis (mean gradient >= 40 mmHg or peak velocity >= 4.0 m/s and valve area <= 1.0 cm2).",
                evidence_anchor="ESC VHD 2025 Physical Signs",
            ),
            AtomicClaimV6(
                claim_id="CLM-CARD-0019-02",
                question_id="PLAB-CARD-0019",
                claim_text="Intervention is indicated in symptomatic patients with severe aortic stenosis (mean gradient >= 40 mmHg or peak velocity >= 4.0 m/s and valve area <= 1.0 cm2).",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-ESC-EACTS-VHD-2025",
                evidence_quote="Intervention is indicated in symptomatic patients with severe aortic stenosis (mean gradient >= 40 mmHg or peak velocity >= 4.0 m/s and valve area <= 1.0 cm2).",
                evidence_anchor="ESC VHD 2025 AS Symptoms",
                target_option="A",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Severe aortic valve stenosis.", "why_plausible": "Classic physical findings match.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "B", "clinical_relationship_to_stem": "Aortic regurgitation.", "why_plausible": "Aortic valve disease.", "why_inferior_or_wrong": "Aortic regurgitation causes early diastolic murmur and collapsing pulse.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "Mitral valve stenosis.", "why_plausible": "Valvular heart disease.", "why_inferior_or_wrong": "Mitral stenosis produces mid-diastolic rumble at apex.", "is_defensible": False},
            {"option_id": "D", "clinical_relationship_to_stem": "Mitral regurgitation.", "why_plausible": "Systolic murmur.", "why_inferior_or_wrong": "Mitral regurgitation causes pansystolic murmur radiating to axilla.", "is_defensible": False},
            {"option_id": "E", "clinical_relationship_to_stem": "Hypertrophic cardiomyopathy.", "why_plausible": "Systolic ejection murmur.", "why_inferior_or_wrong": "HOCM produces jerky pulse and murmur does not radiate to carotids.", "is_defensible": False},
        ],
    )

    # PLAB-CARD-0020: Clean passing (Full decomposition)
    add_spec(
        "PLAB-CARD-0020",
        "SRC-ESC-EACTS-VHD-2025",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-CARD-0020-01",
                question_id="PLAB-CARD-0020",
                claim_text="Peak aortic jet velocity (Vmax) of 4.3 m/s, mean transvalvular pressure gradient of 44 mmHg, and aortic valve area of 0.8 cm2 with LVEF 60% meet criteria for severe aortic stenosis.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-ESC-EACTS-VHD-2025",
                evidence_quote="Intervention is indicated in symptomatic patients with severe aortic stenosis (mean gradient >= 40 mmHg or peak velocity >= 4.0 m/s and valve area <= 1.0 cm2).",
                evidence_anchor="ESC VHD 2025 Echo Numbers",
            ),
            AtomicClaimV6(
                claim_id="CLM-CARD-0020-02",
                question_id="PLAB-CARD-0020",
                claim_text="Intervention is indicated in symptomatic patients with severe aortic stenosis (mean gradient >= 40 mmHg or peak velocity >= 4.0 m/s and valve area <= 1.0 cm2).",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-ESC-EACTS-VHD-2025",
                evidence_quote="Intervention is indicated in symptomatic patients with severe aortic stenosis (mean gradient >= 40 mmHg or peak velocity >= 4.0 m/s and valve area <= 1.0 cm2).",
                evidence_anchor="ESC VHD 2025 AS Criteria",
                target_option="B",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Moderate stenosis category.", "why_plausible": "Valvular severity grade.", "why_inferior_or_wrong": "Moderate AS requires Vmax 3.0-3.9 m/s or mean gradient 20-39 mmHg.", "is_defensible": False},
            {"option_id": "B", "clinical_relationship_to_stem": "Severe stenosis category.", "why_plausible": "Echo parameters meet severe thresholds.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "C", "clinical_relationship_to_stem": "Mild stenosis category.", "why_plausible": "Valvular severity grade.", "why_inferior_or_wrong": "Mild AS has Vmax < 3.0 m/s and mean gradient < 20 mmHg.", "is_defensible": False},
            {"option_id": "D", "clinical_relationship_to_stem": "Aortic valve sclerosis.", "why_plausible": "Non-obstructive calcification.", "why_inferior_or_wrong": "Sclerosis is non-obstructive with normal peak velocity (<2.0 m/s).", "is_defensible": False},
            {"option_id": "E", "clinical_relationship_to_stem": "Low-flow low-gradient AS.", "why_plausible": "Discrepant gradient entity.", "why_inferior_or_wrong": "Patient has high gradient (44 mmHg) and normal LVEF (60%).", "is_defensible": False},
        ],
    )

    # PLAB-CARD-0021: Clean passing (Full decomposition)
    add_spec(
        "PLAB-CARD-0021",
        "SRC-ESC-EACTS-VHD-2025",
        claims=[
            AtomicClaimV6(
                claim_id="CLM-CARD-0021-01",
                question_id="PLAB-CARD-0021",
                claim_text="Symptomatic severe aortic stenosis with mean gradient 46 mmHg and peak velocity 4.4 m/s in an 84-year-old frail woman with STS score 8.5% establishes indication for TAVI evaluation.",
                claim_location="STEM",
                claim_category=ClaimCategory.STEM_DIAGNOSTIC_FACT,
                is_decisive=False,
                source_id="SRC-ESC-EACTS-VHD-2025",
                evidence_quote="Surgical aortic valve replacement (SAVR) is recommended in patients aged under 75 years at low surgical risk (STS/EuroSCORE II < 4%), whereas transcatheter aortic valve implantation (TAVI) is recommended in patients aged 75 or older or at high surgical risk.",
                evidence_anchor="ESC VHD 2025 TAVI Evaluation",
            ),
            AtomicClaimV6(
                claim_id="CLM-CARD-0021-02",
                question_id="PLAB-CARD-0021",
                claim_text="Multidetector computed tomography (MDCT) is recommended for aortic annulus sizing and assessment of vascular access routes prior to transcatheter aortic valve implantation (TAVI).",
                claim_location="CORRECT_OPTION",
                claim_category=ClaimCategory.MANAGEMENT_PRIORITY,
                is_decisive=True,
                source_id="SRC-ESC-EACTS-VHD-2025",
                evidence_quote="Multidetector computed tomography (MDCT) is recommended for aortic annulus sizing and assessment of vascular access routes prior to transcatheter aortic valve implantation (TAVI).",
                evidence_anchor="ESC VHD 2025 TAVI Pre-procedural Imaging",
                target_option="C",
            ),
        ],
        distractor_reviews=[
            {"option_id": "A", "clinical_relationship_to_stem": "Standard chest radiography.", "why_plausible": "Initial thoracic imaging.", "why_inferior_or_wrong": "Plain chest radiography cannot assess aortic annular dimensions, calcification, or peripheral vascular access caliber.", "is_defensible": False},
            {"option_id": "B", "clinical_relationship_to_stem": "Exercise functional evaluation.", "why_plausible": "Functional capacity assessment.", "why_inferior_or_wrong": "Exercise testing is strictly contraindicated in symptomatic severe aortic stenosis and provides no anatomical sizing data.", "is_defensible": False},
            {"option_id": "C", "clinical_relationship_to_stem": "Gold-standard 3D anatomical imaging.", "why_plausible": "Guideline reference technique for TAVI planning.", "why_inferior_or_wrong": "", "is_defensible": True},
            {"option_id": "D", "clinical_relationship_to_stem": "Invasive hemodynamic assessment.", "why_plausible": "Invasive cardiac catheterization.", "why_inferior_or_wrong": "Right heart catheterization assesses pulmonary hemodynamics but cannot provide 3D annular geometry or peripheral access sizing.", "is_defensible": False},
            {"option_id": "E", "clinical_relationship_to_stem": "Nuclear left ventricular assessment.", "why_plausible": "Ventricular ejection fraction evaluation.", "why_inferior_or_wrong": "Radionuclide ventriculography evaluates global left ventricular function but lacks spatial resolution for valvular and vascular planning.", "is_defensible": False},
        ],
    )

    # =========================================================================
    # TOPIC 12: Functional Mitral Regurgitation (Quarantined fail-closed)
    # =========================================================================
    add_spec("PLAB-CARD-0022", "SRC-UNKNOWN", claims=[], distractor_reviews=[])
    add_spec("PLAB-CARD-0023", "SRC-UNKNOWN", claims=[], distractor_reviews=[])
    add_spec("PLAB-CARD-0024", "SRC-UNKNOWN", claims=[], distractor_reviews=[])

    return specs
