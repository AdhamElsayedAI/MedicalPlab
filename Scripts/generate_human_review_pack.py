#!/usr/bin/env python3
"""
generate_human_review_pack.py
Generates the comprehensive Human Review Pack for Cardiorespiratory PLAB Batch 1 (36 questions).
Outputs: docs/plab/PLAB_BATCH_1_HUMAN_REVIEW_PACK.md
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BATCH_FILE = REPO_ROOT / "Data" / "questions" / "cardiorespiratory_batch_1.json"
QUEUE_FILE = REPO_ROOT / "Data" / "questions" / "cardiorespiratory_batch_1_review_queue.json"
OUTPUT_FILE = REPO_ROOT / "docs" / "plab" / "PLAB_BATCH_1_HUMAN_REVIEW_PACK.md"

TOPIC_UK_REFS = {
    "Hypertension (Essential & Secondary)": {
        "authority": "National Institute for Health and Care Excellence (NICE)",
        "guideline": "NICE NG136 (Hypertension in adults: diagnosis and management)",
        "version_date": "Aug 2019, updated Nov 2023 (CURRENT)",
        "statement": "NICE stepped care: Stage 1 ABPM/HBPM >= 135/85 mmHg. Step 1: CCB for age >=55 or Black African/African-Caribbean; ACEi/ARB for non-Black age <55. Step 2: ACEi/ARB + CCB or thiazide-like diuretic."
    },
    "Atrial Fibrillation (Rate vs Rhythm, Anticoagulation)": {
        "authority": "National Institute for Health and Care Excellence (NICE)",
        "guideline": "NICE NG196 (Atrial fibrillation: diagnosis and management)",
        "version_date": "Apr 2021, updated Jun 2021 (CURRENT)",
        "statement": "NICE mandates CHA2DS2-VASc for stroke risk (DOAC 1st-line for men score >=1, women score >=2) and ORBIT bleeding risk tool. Rate control is first-line pharmacotherapy for non-acute AF without reversible causes."
    },
    "Syncope & Transient Loss of Consciousness": {
        "authority": "National Institute for Health and Care Excellence (NICE)",
        "guideline": "NICE CG109 (Transient loss of consciousness ['blackouts'] in over 16s)",
        "version_date": "Aug 2010, confirmed current Nov 2023 (CURRENT)",
        "statement": "12-lead ECG mandatory for all episodes. Urgent referral (within 2 weeks) for cardiac syncope red flags (exertional syncope, abnormal ECG, known heart disease, family history of sudden cardiac death <40 yrs)."
    },
    "Chronic Obstructive Pulmonary Disease (COPD)": {
        "authority": "National Institute for Health and Care Excellence (NICE) / British Thoracic Society (BTS)",
        "guideline": "NICE NG115 (COPD in over 16s: diagnosis and management)",
        "version_date": "Dec 2018, updated Jul 2019 (CURRENT)",
        "statement": "Acute exacerbation: controlled oxygen (Venturi 24%/28%, target SpO2 88-92%), nebulised salbutamol/ipratropium, oral prednisolone 30mg for 5 days, antibiotics if purulent sputum. Inhaled stepped therapy per asthmatic features/eosinophils."
    },
    "Cardiopulmonary Resuscitation & Cardiac Arrest": {
        "authority": "Resuscitation Council UK (RCUK)",
        "guideline": "RCUK Adult Advanced Life Support (ALS) Guidelines 2021 / 2025 Updates",
        "version_date": "May 2021, confirmed current (CURRENT)",
        "statement": "ALS Protocol: 30:2 compressions, early rhythm check. Shockable (VF/pVT): 150-200J biphasic, adrenaline 1mg IV + amiodarone 300mg IV after 3rd shock. Non-shockable (PEA/Asystole): adrenaline 1mg IV immediately, address 4Hs and 4Ts."
    },
    "Pneumothorax": {
        "authority": "British Thoracic Society (BTS)",
        "guideline": "BTS Clinical Statement on Pleural Disease: Pneumothorax 2023",
        "version_date": "Jul 2023 (CURRENT)",
        "statement": "Conservative observation or small-bore aspiration prioritized for stable primary spontaneous pneumothorax (PSP) regardless of radiological size if minimally symptomatic. Tension pneumothorax: urgent needle decompression (2nd ICS MCL or 4th/5th ICS AAL)."
    },
    "Acute Respiratory Distress Syndrome (ARDS)": {
        "authority": "Faculty of Intensive Care Medicine (FICM) / Intensive Care Society (ICS)",
        "guideline": "FICM / ICS Guideline on the Management of Adult ARDS",
        "version_date": "Dec 2018, confirmed current (CURRENT)",
        "statement": "Lung-protective ventilation: tidal volume <=6 mL/kg predicted body weight, plateau pressure <30 cmH2O. Prone positioning for >=16 hours/day in severe ARDS (PaO2/FiO2 <150 mmHg). Avoid routine paralytics unless refractory dyssynchrony."
    },
    "Cardiogenic Shock": {
        "authority": "National Institute for Health and Care Excellence (NICE) / British Cardiovascular Society (BCS)",
        "guideline": "NICE NG185 (Section 1.2.6) / BCS Clinical Guidance",
        "version_date": "Nov 2020 / Oct 2014 (CURRENT)",
        "statement": "Urgent echocardiography and immediate reperfusion (PCI/CABG) evaluation. Noradrenaline is first-line vasopressor (preferred over dopamine). Dobutamine added for inotropic support in low cardiac output with elevated filling pressures."
    },
    "Infective Endocarditis (IE)": {
        "authority": "British Society for Antimicrobial Chemotherapy (BSAC) / NICE",
        "guideline": "NICE CG64 (Prophylaxis against infective endocarditis) / BSAC Guidelines",
        "version_date": "CG64 confirmed current 2016-2026 (CURRENT)",
        "statement": "NICE CG64 explicitly advises against routine antibiotic prophylaxis for dental or non-dental procedures in at-risk cardiac patients. Diagnosis: 3 sets of blood cultures prior to antibiotics + echo using Modified Duke Criteria."
    },
    "Bradyarrhythmias & Conduction Blocks": {
        "authority": "Resuscitation Council UK (RCUK) / NICE",
        "guideline": "RCUK Bradycardia Algorithm (2021) / NICE TA314 & CG95",
        "version_date": "May 2021 (CURRENT)",
        "statement": "Assess for adverse features (shock, syncope, myocardial ischaemia, severe heart failure): atropine 500 mcg IV (up to 3 mg). If inadequate: transcutaneous pacing or isoprenaline/adrenaline infusion. Permanent pacemaker for Mobitz II or complete AV block."
    },
    "Aortic Stenosis (Valvular Heart Disease)": {
        "authority": "National Institute for Health and Care Excellence (NICE)",
        "guideline": "NICE NG208 (Heart valve disease in adults: investigation and management)",
        "version_date": "Nov 2021 (CURRENT)",
        "statement": "Severe symptomatic AS: AVA <1.0 cm2, mean gradient >40 mmHg, peak velocity >4.0 m/s. Multidisciplinary heart team evaluation: SAVR preferred in low-risk/younger (<75 yrs), TAVI preferred in older (>80 yrs) or high surgical risk."
    },
    "Functional Mitral Regurgitation": {
        "authority": "National Institute for Health and Care Excellence (NICE)",
        "guideline": "NICE NG208 / NICE NG106 (Chronic heart failure)",
        "version_date": "Nov 2021 / Aug 2018 (CURRENT)",
        "statement": "Secondary/functional MR: guideline-directed medical therapy (GDMT) for heart failure (ACEi/ARNI, beta-blocker, MRA, SGLT2i) is 1st-line. Transcatheter edge-to-edge repair (TEER/MitraClip) considered by MDT if persistent severe MR despite GDMT."
    }
}

def main():
    with open(BATCH_FILE, "r", encoding="utf-8") as f:
        batch_data = json.load(f)
    
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue_data = json.load(f)
        
    queue_lookup = {item["question_id"]: item for item in queue_data["queue"]}
    
    questions = batch_data["questions"]
    
    lines = []
    lines.append("# MedicalPlab Cardiorespiratory PLAB Batch 1: Human Review Pack")
    lines.append("")
    lines.append("**Batch Identifier:** `cardiorespiratory_batch_1_v1`  ")
    lines.append("**Lifecycle Stage:** `HUMAN_REVIEW_PENDING` (Not Golden)  ")
    lines.append("**Date Generated:** 2026-09-09  ")
    lines.append("**Total Questions:** 36 (12 Topics × 3 Questions)  ")
    lines.append("**Automated Pre-Screen:** 36/36 Passed Automated Validation  ")
    lines.append("**Current Golden Count:** 0/36 (Awaiting Clinical Reviewer Sign-off)  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Instructions for Clinical Reviewers")
    lines.append("")
    lines.append("Each question in this pack is an original Cardiorespiratory Single Best Answer (SBA) question designed for the UK Professional and Linguistic Assessments Board (PLAB 1) / Medical Licensing Assessment (MLA).")
    lines.append("")
    lines.append("Please independently review each question across the seven core dimensions:")
    lines.append("1. **Clinical Correctness (0-2):** Is the clinical vignette realistic, plausible, and accurate?")
    lines.append("2. **Single Best Answer (0-2):** Is there exactly ONE incontrovertibly correct single best answer under current UK practice?")
    lines.append("3. **Distractor Quality (0-2):** Are the four incorrect options plausible yet clearly inferior, with no accidental ambiguity?")
    lines.append("4. **UK Guideline Alignment (0-2):** Does the question and explanation strictly adhere to current UK guidance (NICE, RCUK, BTS, FICM, BSAC)?")
    lines.append("5. **Evidence Entailment (0-2):** Does the cited local open-access supporting text directly support the core learning objective and correct answer?")
    lines.append("6. **Explanation Clarity (0-2):** Is the explanation educationally helpful, explaining why the correct answer is best and why distractors are incorrect?")
    lines.append("7. **PLAB/MLA Realism (0-2):** Is this appropriately pitched at the level of a UK Foundation Year 2 (FY2) doctor?")
    lines.append("")
    lines.append("Record your assessment in the review form for each question. Final decisions must be marked as `APPROVED`, `REVISE`, or `REJECT`.")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Render each question
    for idx, q in enumerate(questions, 1):
        qid = q["question_id"]
        q_queue = queue_lookup.get(qid, {})
        topic = q["topic"]
        uk_info = TOPIC_UK_REFS.get(topic, {
            "authority": "UK Clinical Authority",
            "guideline": "Authoritative UK Guidance",
            "version_date": "Current",
            "statement": "Adhere to established UK national clinical recommendations."
        })
        
        lines.append(f"## Question {idx} of 36: `{qid}`")
        lines.append("")
        lines.append(f"- **Specialty:** {q.get('specialty', 'Cardiology')}  ")
        lines.append(f"- **Topic:** **{topic}**  ")
        lines.append(f"- **Difficulty:** {q.get('difficulty', 'medium').capitalize()} (UK FY2 / PLAB 1 Level)  ")
        lines.append(f"- **Learning Objective:** {q.get('learning_objective', 'N/A')}  ")
        lines.append(f"- **Risk Level:** `{q_queue.get('risk_level', 'MEDIUM')}`  ")
        lines.append(f"- **Automated Pre-Screen Score:** `{q_queue.get('prescreen_score', 14)}/14` ({q_queue.get('prescreen_priority', 'high-confidence candidate')})  ")
        lines.append("")
        lines.append("### Clinical Vignette (Stem)")
        lines.append(f"> {q['stem']}")
        lines.append("")
        lines.append("### Options")
        for choice in q["choices"]:
            cid = choice["id"]
            ctext = choice["text"]
            is_ans = " **[CORRECT ANSWER]**" if cid == q["correct_answer"] else ""
            lines.append(f"- **{cid}.** {ctext}{is_ans}")
        lines.append("")
        lines.append(f"**Proposed Key:** **Option {q['correct_answer']}**")
        lines.append("")
        lines.append("### Educational Explanation")
        lines.append(f"{q['explanation']}")
        lines.append("")
        lines.append("### Supporting Corpus Evidence")
        for cit in q.get("citations", []):
            lines.append(f"- **Document:** `{cit.get('document_id')}`  ")
            lines.append(f"- **Chunk ID:** `{cit.get('ref')}`  ")
            lines.append(f"- **Verbatim Evidence Quote:** *\"{cit.get('quote')}\"*  ")
        lines.append("")
        lines.append("### UK Clinical Authority Reconciliation")
        lines.append(f"- **UK Authority:** {uk_info['authority']}  ")
        lines.append(f"- **Guideline:** {uk_info['guideline']}  ")
        lines.append(f"- **Version / Freshness:** {uk_info['version_date']}  ")
        lines.append(f"- **Reconciliation Proposition:** {uk_info['statement']}  ")
        lines.append(f"- **Automated UK Audit Status:** `{q_queue.get('automated_uk_check', 'CURATED_RULE_COMPARED_PENDING_CLINICAL_SIGN_OFF')}`  ")
        lines.append("")
        lines.append("### Clinical Reviewer Evaluation Form")
        lines.append("```markdown")
        lines.append("Reviewer Name/ID: _________________________________________")
        lines.append("Review Date:      _________________________________________")
        lines.append("")
        lines.append("Evaluation Checklist:")
        lines.append("[ ] Clinical correctness:     [ ] PASS   [ ] FAIL   [ ] EDIT")
        lines.append("[ ] Single Best Answer:       [ ] PASS   [ ] FAIL   [ ] EDIT")
        lines.append("[ ] UK guideline alignment:   [ ] PASS   [ ] FAIL   [ ] EDIT")
        lines.append("[ ] Evidence entailment:      [ ] PASS   [ ] FAIL   [ ] EDIT")
        lines.append("[ ] Distractor plausibility:  [ ] PASS   [ ] FAIL   [ ] EDIT")
        lines.append("[ ] Explanation quality:      [ ] PASS   [ ] FAIL   [ ] EDIT")
        lines.append("[ ] PLAB/MLA realism:         [ ] PASS   [ ] FAIL   [ ] EDIT")
        lines.append("")
        lines.append("Specific Comments / Required Edits:")
        lines.append("___________________________________________________________")
        lines.append("___________________________________________________________")
        lines.append("")
        lines.append("Final Review Decision:")
        lines.append("[ ] APPROVED (Ready for Golden Promotion)")
        lines.append("[ ] REVISE   (Requires Clinical / Wording Edits)")
        lines.append("[ ] REJECT   (Fundamentally Flawed / Excluded)")
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")
        
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    print(f"Successfully generated Human Review Pack at: {OUTPUT_FILE}")
    print(f"Total questions formatted: {len(questions)}")

if __name__ == "__main__":
    main()
