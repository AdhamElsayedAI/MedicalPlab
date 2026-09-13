# Clinical Safety & Risk Management Framework

## 1. Safety Philosophy: Fail-Closed Medical AI

Medical education software directly influences clinical decision-making habits of future doctors. A hallucination in an exam prep application is not an inconvenience; it can translate into diagnostic error or dangerous prescribing in clinical practice.

MedicalPlab adheres to three fundamental clinical safety tenets:

1. **Fail-Closed by Default**: When confidence is below threshold, when a guideline has been updated, or when evidence provenance is incomplete, the system refuses to serve the item to learners and routes it to quarantine.
2. **Zero Autonomous Clinical Approval**: An LLM cannot evaluate medical truth or clinical appropriateness. All clinical validation requires GMC-licensed medical practitioners.
3. **Deterministic Traceability**: Every explanation, clinical pearl, and distractor rejection is bound to exact character-spans within authoritative peer-reviewed guidelines or NHS/NICE guidance.

---

## 2. NHS DCB0129 Risk Governance Alignment

MedicalPlab is designed to conform to the requirements of **DCB0129 (Clinical Risk Management: Its Application in the Deployment and Use of Health IT Systems)**:

| Hazard ID | Clinical Hazard | Cause | Mitigation in MedicalPlab | Safety State |
| :--- | :--- | :--- | :--- | :--- |
| **HAZ-01** | Learner taught outdated clinical guideline | Guideline updated or retired by NICE/SIGN | Guideline Currency Engine & automated deprecation scanner | Fail-closed quarantine |
| **HAZ-02** | Model hallucinated dosage or treatment algorithm | Generative hallucination in unconstrained LLM | Multi-source RAG with exact-span verification; zero free-form fact generation | Character-exact matching |
| **HAZ-03** | Ambiguous distractor confuses exam candidate | Multiple viable treatment options in real life | Adversarial Distractor Ambiguity Engine with cross-source contrastive scoring | Distractor quarantine |
| **HAZ-04** | Unauthorized tampering of question content | Pipeline mutation or cache inconsistency | Deterministic SHA-256 integrity trees across question, options, and rationale | Pipeline abort on mismatch |
| **HAZ-05** | Unvetted question served to live candidates | Premature publishing without clinician audit | Strict runtime gating: Golden status requires explicit human clinician review | `golden = false` default |

---

## 3. Systematic Blocker Taxonomy (A through I)

MedicalPlab categorizes all content safety blockers into an explicit taxonomy:

| Blocker Category | Description | Trigger Condition | Automated Action |
| :--- | :--- | :--- | :--- |
| **Blocker A: Source Identity** | Source not authenticated in UK registry | Publisher or URI not in verified registry | Quarantine |
| **Blocker B: Currency & Validity** | Guideline status retired, updated, or superseded | Source date precedes current GMC MLA content map | Quarantine |
| **Blocker C: Decisive Claim Support** | Rationale assertion lacks direct source proof | Claim not matched to verified source excerpt | Quarantine |
| **Blocker D: Decisive Fragment Coverage** | Reasoning step missing evidence citation | Explanation includes unanchored medical assertions | Quarantine |
| **Blocker E: Span Integrity** | Excerpt does not match source text verbatim | Character sequence differs from normalized source | Pipeline Error |
| **Blocker F: Hash Divergence** | Checksum mismatch across stages | Content SHA-256 altered post-ingestion | Hard Rejection |
| **Blocker G: Distractor Ambiguity** | Distractor might be clinically defendable | Source evidence gives borderline support to distractor | Quarantine |
| **Blocker H: Clinician Review Pending** | Technical verification complete, awaiting physician | All technical gates clear, awaiting human sign-off | Review Queue |
| **Blocker I: Engineering & Schema** | Schema violation, malformed JSON, or broken types | Pydantic / TypeScript validator failure | CI / Runtime Failure |

---

## 4. Quarantine Lifecycle & Clinician Review Queue

Questions do not exist in a binary "valid / invalid" state. They follow a rigorous state transition machine:

```text
[DRAFT / GENERATED]
         │
         ▼
[TECHNICAL VERIFICATION] ──── (Fails any A-G, I gate) ───► [QUARANTINE]
         │                                                      │
         ▼ (Passes all technical gates)                         │ (Manual audit)
[CLINICIAN_REVIEW_REQUIRED]                                     ▼
         │                                            [REPAIR OR ARCHIVE]
         ▼ (GMC-licensed clinician sign-off)
     [GOLDEN]
         │
         ▼
[PRODUCTION SERVING]
```

### Reviewer Interface Security
- Clinician endpoints (`/api/v1/review/*`) require high-entropy bearer token authentication (`MEDICALPLAB_INTERNAL_REVIEW_TOKEN`).
- Audit trails record reviewer identity, timestamp, decision rationale, and cryptographic snapshot of reviewed content.
- Clinical review overrides are forbidden from bypassing technical schema or hash integrity gates.

---

## 5. Dynamic AI Safety Traps in Interactive Tutoring

During active tutoring sessions (Stage-B and Stage-E adaptive modules), the AI tutor employs real-time safety guardrails:

- **Red Flag Escalation**: If a learner question touches upon acute emergent presentations (e.g., stridor, tearing chest pain, acute anaphylaxis, cauda equina symptoms), the tutor instantly injects standard emergency clinical management warnings (ABCDE approach, immediate senior consultation, 999/resuscitation call).
- **Prohibited Prescribing**: The tutor is hardwired never to provide personalized medical advice or prescription recommendations to real patients; it operates strictly within medical student simulated education.
- **Unanswerable Questions**: If a medical student asks a query outside the authoritative corpus, the tutor states explicitly: *"This question cannot be definitively answered from current verified UK clinical guidelines."*
