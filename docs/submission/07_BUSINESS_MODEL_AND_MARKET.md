# Business Model & Market Strategy

> **A sustainable, phased go-to-market approach grounded in real educational demand.**

---

## 1. Market Opportunity & Beachhead

Medical education is undergoing a structural shift. With medical licensing examinations increasingly prioritizing applied clinical reasoning over rote memorization, students and institutions require active learning tools that diagnose cognitive gaps.

### Beachhead Market: Preclinical & Licensing Exam Candidates
- **Target:** Medical undergraduates preparing for preclinical exams and international medical graduates studying for standardized licensing exams (UK PLAB / MLA and USMLE Step 1).
- **Rationale:** High willingness-to-pay among candidates facing high-stakes examinations where an incorrect answer can delay career progression by months or years.

### Expansion Markets:
1. **Clinical Rotations & Specialty Colleges:** Postgraduates revising for specialty membership exams (e.g. MRCP, MRCGP, USMLE Step 2 CK).
2. **Institutional Curriculum Integration:** Medical universities looking to replace static question banks with cognitive tutoring integrated into formal learning management systems (LMS).
3. **Allied Health & Nursing Programs:** Extending physiological and anatomical reasoning frameworks to broader healthcare disciplines.

---

## 2. Proposed Business Models (Hypotheses)

*(Note: All pricing tiers and commercial terms represent proposed business model hypotheses for future evaluation. MedicalPlab does not claim existing commercial revenue or signed contracts.)*

```
                     ┌────────────────────────────────────────┐
                     │          MedicalPlab Revenue           │
                     └────────────────────────────────────────┘
                                /                  \
                               /                    \
              ┌──────────────────────┐        ┌──────────────────────┐
              │ B2C: Direct Learner  │        │   B2B: Institutional  │
              └──────────────────────┘        └──────────────────────┘
                         │                               │
            ┌────────────┴────────────┐             ┌────┴─────────────────┐
            │                         │             │                      │
       [ Monthly ]               [ Annual ]    [ Seat Licenses ]    [ Cohort Analytics ]
       (Flexible)                (Discounted)  (Medical Schools)    (Educator Insights)
```

### B2C: Direct-to-Student Subscription
- **Freemium Core:** Access to University question bank, basic progress metrics, and standard clinical rationales.
- **Premium Tier (Proposed $15–$25 / month):** Unlocks bounded Socratic remediation, independent held-out transfer challenges, the 3D Cognitive Anatomy Lab, and unlimited Grounded Tutor queries backed by PubMed Central literature.

### B2B: Institutional Curriculum & Seat Licensing
- **University Seat Licenses:** Sold directly to medical school departments on an annual per-student basis (proposed $80–$120 / student / year).
- **Educator Analytics Tier:** Provides medical school faculty with the **Cohort Reasoning-Gap Radar**, enabling course leaders to visualize systematic cohort misconceptions ($N \ge 3$) to inform lecture topics and tutorial sessions.

---

## 3. Go-to-Market Strategy

### Phase 1: Grassroots Student Adoption (Direct-to-Consumer)
- Open-source, local-first developer release to build community trust and gather developer/educator feedback.
- Targeted outreach across medical student societies, examination preparation forums, and residency applicant networks.
- Distribution of high-yield clinical case breakdowns demonstrating Socratic remediation vs. generic chatbot output.

### Phase 2: Academic Department Co-Design & Pilots
- Partner with clinical educators to author and validate golden exam question sets.
- Offer free academic pilot access to preclinical module leads in exchange for usability feedback and efficacy data.

### Phase 3: Enterprise & Licensing Integration
- Package the platform as a SCORM / LTI-compliant module integrable into university platforms (Canvas, Blackboard, Moodle).
- Formalize institutional contracts backed by data security compliance and privacy guarantees.

---

## 4. Startup Defensibility & Moat

In modern software development, **the underlying foundation model is a commodity**. Building a sustainable edtech startup cannot rely on an LLM wrapper. 

MedicalPlab’s defensibility is established by the **specialized cognitive system around the model**:

| Defensibility Pillar | Why It Is Hard to Replicate |
| :--- | :--- |
| **Reasoning-Pattern Taxonomy** | Curated mappings linking diagnostic distractor choices directly to specific cognitive error archetypes (e.g. `PATTERN-RAAS-SUB-01`). |
| **Paired Held-Out Transfer Bank** | A proprietary catalog of validated question-transfer pairs where understanding of Question A is independently tested by Question B without leakage. |
| **Verified Evidence Architecture** | Automated PubMed Central rights validation, semantic chunking, and NLI entailment checking with safe abstention protocols. |
| **Spatial Anatomy Integration** | Bidirectional mapping between Socratic educational intent and 3D Three.js mesh entities mapped to UBERON anatomical ontologies. |
| **Privacy-Preserving Cohort Telemetry** | A privacy-safe aggregation engine ($N \ge 3$) translating individual learner signals into macro-level curriculum insights for institutions. |
| **Local-First Trust & Transparency** | A fully auditable, reproducible codebase that clinical institutions can inspect and run on-premise without vendor lock-in. |
