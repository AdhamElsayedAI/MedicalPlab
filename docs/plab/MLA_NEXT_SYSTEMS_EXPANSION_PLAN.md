# MLA Expansion Planning: Next Clinical Systems Post-Cardiorespiratory

**Status:** PLANNING ONLY — NO INGESTION OR GENERATION EXECUTED  
**Date:** 2026-09-09  
**Policy Reminder:** Adhere strictly to the frozen Cardiorespiratory quality gate. This document outlines the strategic roadmap for expanding the MedicalPlab evidence-grounded SBA pipeline to subsequent systems in the UK Medical Licensing Assessment (MLA) content map once Cardiorespiratory Batch 1 receives human clinician sign-off.

---

## 1. System Ranking & Strategic Evaluation

Systems are ranked based on six weighted criteria:
1. **PLAB / UK MLA Frequency & Clinical Relevance (30%)**
2. **Authoritative UK Clinical Guidance Availability (NICE, Royal Colleges, Specialist Societies) (20%)**
3. **Open-Access Commercial-Compatible PMC Corpus Availability (CC BY 4.0) (20%)**
4. **Interactive Demo & Architectural Value (10%)**
5. **Stage-B/R/C/G Pipeline Reuse (10%)**
6. **Clinical Safety & Conflict Nuance Complexity (10%)**

| Rank | Clinical System | MLA Weight | Key UK Authorities | Open Corpus Availability | Pipeline Fit | Recommendation |
|---|---|---|---|---|---|---|
| **1** | **Neurology & Stroke** | Very High (P0) | NICE (NG128, NG240), ABN, RCUK | High (PMC open reviews) | High (Stage-R dense) | **Next Immediate Expansion (Wave 3)** |
| **2** | **Gastroenterology & Hepatology** | High (P0) | NICE (CG141, NG50, NG130), BSG | High (PMC open reviews) | High (Stage-R dense) | **Subsequent Expansion (Wave 4)** |
| **3** | **Endocrinology & Diabetes** | High (P0/P1) | JBDS-IP, NICE (NG28, NG145), SfE | Very High (JBDS / PMC) | High (Stage-R dense) | **Subsequent Expansion (Wave 5)** |

---

## 2. Priority 1: Neurology & Stroke (Wave 3 Candidate)

### Target Core Topics (12 Topics × 3 Questions = 36 Questions)
1. **Acute Ischaemic Stroke:** Thrombolysis (alteplase <=4.5h) vs mechanical thrombectomy (<=6h/24h), antiplatelet timing.
2. **Transient Ischaemic Attack (TIA):** Immediate aspirin 300 mg, specialist TIA clinic assessment within 24 hours.
3. **Subarachnoid Haemorrhage (SAH):** Non-contrast CT head within 6 hours, lumbar puncture timing (>=12h for xanthochromia), nimodipine.
4. **Status Epilepticus:** Pre-hospital buccal midazolam/rectal diazepam, IV lorazepam (4 mg), second-line levetiracetam/phenytoin/valproate.
5. **Bacterial Meningitis:** Immediate pre-hospital IV/IM benzylpenicillin (GP), hospital empirical cefotriaxone + dexamethasone (before or with first dose).
6. **Intracranial Hypertension & Space-Occupying Lesions:** Cushing's triad, mannitol/hypertonic saline, neurosurgical referral.
7. **Parkinson's Disease:** Clinical diagnosis, dopaminergic therapy initiation, drug-induced parkinsonism.
8. **Multiple Sclerosis (MS):** McDonald criteria, acute relapse treatment (high-dose methylprednisolone).
9. **Peripheral Neuropathy & Guillain-Barré Syndrome:** Ascending weakness, albuminocytological dissociation, IVIG vs plasma exchange (avoid steroids).
10. **Myasthenia Gravis:** Tensilon/antibody testing, pyridostigmine, myasthenic crisis vs cholinergic crisis.
11. **Headache Disorders:** Migraine stepped management (triptans), cluster headache (100% O2 + subcutaneous sumatriptan), temporal arteritis urgent high-dose steroids.
12. **Spinal Cord Compression:** Urgent whole-spine MRI, high-dose dexamethasone, oncological/neurosurgical emergency referral.

### UK Authoritative References
- NICE NG128: *Stroke and transient ischaemic attack in over 16s: diagnosis and initial management*
- NICE NG240: *Meningitis (bacterial) and meningococcal disease: recognition, diagnosis and management*
- Association of British Neurologists (ABN) Clinical Guidelines (Status epilepticus, GBS, Myasthenia)
- NICE CG109: *Transient loss of consciousness ('blackouts') in over 16s*

### Open-Access Source Strategy & First Corpus Estimate
- **Corpus Target:** 12–15 verified open-access CC BY 4.0 PMC review articles (~750–900 chunks).
- Focus on acute neuro-critical care, stroke algorithms, and emergency neurology pathways.
- Exclude commercial question banks and copyrighted NHS Trust protocols.

### Evaluation & QA Plan
- 20 held-out clinical retrieval queries spanning stroke windows, lumbar puncture timing, and anticonvulsant dosing.
- Benchmark Qwen3 dense retriever vs hybrid on frozen neurology snapshot.
- Calibrate evidence sufficiency threshold before SBA generation.

---

## 3. Priority 2: Gastroenterology & Hepatology (Wave 4 Candidate)

### Target Core Topics (10–12 Topics)
1. **Acute Upper GI Bleeding:** Resuscitation, restrictive transfusion (Hb <70 g/L), Blatchford risk score, urgent endoscopy within 24h, IV terlipressin + antibiotics in suspected variceal bleeding.
2. **Decompensated Cirrhosis & Ascites:** Diagnostic paracentesis (rule out SBP: neutrophil count >250/mm3), empirical cefotaxime/ciprofloxacin, albumin with large-volume paracentesis.
3. **Acute Pancreatitis:** Modified Glasgow-Imrie score, aggressive crystalloid hydration, ultrasound for gallstones, avoiding prophylactic antibiotics.
4. **Inflammatory Bowel Disease (Ulcerative Colitis & Crohn's):** Truelove-Witts severity criteria, acute severe colitis IV hydrocortisone, rescue therapy (infliximab/cyclosporin).
5. **Coeliac Disease:** Anti-tTG IgA + total IgA, duodenal biopsy on gluten-containing diet.
6. **Jaundice & Biliary Sepsis:** Charcot's triad, Reynolds' pentad, urgent ERCP decompression for acute cholangitis.
7. **Clostridioides difficile Infection:** Oral fidaxomicin or vancomycin, isolation, avoidance of antimotility agents.
8. **Malabsorption & Chronic Diarrhoea:** Faecal calprotectin in primary care to distinguish IBD from IBS.
9. **Dysphagia & Oesophageal Cancer:** Two-week-wait urgent endoscopy criteria (NICE NG12).
10. **Acute Liver Failure:** King's College Hospital criteria for liver transplantation, paracetamol toxicity N-acetylcysteine protocol.

### UK Authoritative References
- NICE CG141: *Acute upper gastrointestinal bleeding in over 16s: management*
- NICE NG50: *Cirrhosis in over 16s: assessment and management*
- British Society of Gastroenterology (BSG) Guidelines: Acute pancreatitis, Acute lower GI bleeding, IBD.

---

## 4. Priority 3: Endocrinology & Diabetes (Wave 5 Candidate)

### Target Core Topics (10 Topics)
1. **Diabetic Ketoacidosis (DKA):** Diagnostic triad, 0.9% NaCl fluid resuscitation, fixed-rate IV insulin infusion (0.1 units/kg/h), potassium replacement algorithms, resolution criteria.
2. **Hyperosmolar Hyperglycaemic State (HHS):** Gradual rehydration with 0.9% NaCl, slow osmolality decline, prophylactic LMWH.
3. **Hypoglycaemia:** Conscious (fast-acting carbohydrate) vs unconscious (IV 20% glucose or IM glucagon).
4. **Type 2 Diabetes Stepped Pharmacotherapy:** NICE NG28 (Metformin + SGLT2i for high CVD risk, HbA1c targets).
5. **Thyroid Disorders:** Thyrotoxicosis diagnosis, carbimazole agranulocytosis warning, thyroid storm management.
6. **Hypothyroidism & Myxoedema Coma:** Levothyroxine monitoring, TSH target ranges, subclinical hypothyroidism.
7. **Adrenal Insufficiency & Addisonian Crisis:** Immediate IV hydrocortisone 100 mg + IV fluids, short Synacthen test.
8. **Cushing's Syndrome:** Screening (overnight dexamethasone suppression test, 24h urinary free cortisol), localisation.
9. **Primary Hyperaldosteronism (Conn's Syndrome):** Refractory hypertension, hypokalaemia, aldosterone-to-renin ratio.
10. **Disorders of Calcium Metabolism:** Hypercalcaemia (IV saline rehydration + bisphosphonates), hypocalcaemic tetany (IV calcium gluconate).

### UK Authoritative References
- Joint British Diabetes Societies for Inpatient Care (JBDS-IP) Guidelines: DKA, HHS, Inpatient Hypoglycaemia.
- NICE NG28: *Type 2 diabetes in adults: management*
- NICE NG145: *Thyroid disease: assessment and management*
- Society for Endocrinology (SfE) Emergency Endocrine Guidelines

---

## 5. Execution Preconditions Before Expansion

Under no circumstances will Wave 3 ingestion begin until:
1. Cardiorespiratory Batch 1 receives formal, independent clinical review from a registered UK medical practitioner (0/36 $\rightarrow$ approved).
2. The Golden dataset promotion gate is validated with real clinician sign-off.
3. The pilot backend is deployed and tested with real learners.
