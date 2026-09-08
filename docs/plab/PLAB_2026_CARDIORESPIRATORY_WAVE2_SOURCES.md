# PLAB 2026 Cardiorespiratory — Wave 2 Source Set

**Branch:** `ai-data-execution-v1`  
**Verified on:** 2026-09-09  
**Goal:** close the highest-priority P0/P1 gaps identified after the first 702-chunk Cardiorespiratory checkpoint without weakening licensing or provenance standards.

## Selection rule

Every topic requires two independent layers whenever possible:

1. **UK ground truth** for current UK/PLAB clinical practice.
2. **Commercial-compatible supporting evidence** that MedicalPlab may legally ingest into RAG/question generation.

A strong UK guideline is not automatically an ingestible AI source. A CC BY review is not automatically UK clinical ground truth.

## UK ground-truth additions

| Source ID | Source | Current role | Licence / AI status | Main coverage |
|---|---|---|---|---|
| SRC-NICE-NG196 | NICE NG196 — Atrial fibrillation: diagnosis and management | UK ground truth | PERMISSION_REQUIRED | AF detection, diagnosis, stroke prevention, rate/rhythm control |
| SRC-NICE-CG109 | NICE CG109 — Transient loss of consciousness ('blackouts') in over 16s | UK ground truth | PERMISSION_REQUIRED | syncope/TLoC assessment and referral |
| SRC-NICE-NG208 | NICE NG208 — Heart valve disease presenting in adults | UK ground truth | PERMISSION_REQUIRED | murmurs, aortic/mitral valve disease, echo/intervention |
| SRC-NICE-CG50 | NICE CG50 — Acutely ill adults in hospital: recognising and responding to deterioration | UK ground truth with freshness caveat | PERMISSION_REQUIRED | deteriorating patient / escalation / track-and-trigger |
| SRC-RCUK-ALS-2025 | Resuscitation Council UK — Adult advanced life support Guidelines | current UK resuscitation ground truth | REFERENCE_ONLY; reuse licence for MedicalPlab AI not verified | cardiac arrest / ALS |
| SRC-BTS-PLEURAL-2023 | British Thoracic Society Guideline for pleural disease | UK specialty ground truth | REFERENCE_ONLY; explicit no-commercial-reuse without permission | pneumothorax / pleural disease |

### Licensing notes

- Current NICE reuse terms state that AI uses are outside the ordinary open-content permission path and require approval/licensing. These sources remain external verification references, not RAG text.
- The BTS pleural guideline copyright page states **no commercial re-use** without permission; MedicalPlab must not ingest the full guideline into its commercial corpus.
- Resuscitation Council UK 2025 ALS is the correct current UK clinical reference for arrest, but its MedicalPlab AI/commercial reuse permission has not been independently established in this wave, therefore it stays reference-only.

## Commercial-compatible supporting candidates

All candidates below were independently checked on their PMC records and showed **CC BY 4.0** terms compatible with commercial reuse subject to attribution. They are approved for acquisition into the existing MedicalPlab ingestion pipeline, but are **not marked downloaded or validated in this remote session**.

| Document ID | PMCID | Exact title | Primary gap | Licence | Acquisition state |
|---|---|---|---|---|---|
| DOC-PMC-CARD-0008 | PMC11678337 | Advances in Atrial Fibrillation Management: A Guide for General Internists | AF / tachyarrhythmia | CC BY 4.0 | VERIFIED_CANDIDATE |
| DOC-PMC-CARD-0009 | PMC10856004 | Recent Advances and Future Directions in Syncope Management: A Comprehensive Narrative Review | syncope | CC BY 4.0 | VERIFIED_CANDIDATE |
| DOC-PMC-RESP-0003 | PMC11179745 | Phenotype to Treatable Traits-Based Management in Chronic Obstructive Pulmonary Disease | COPD | CC BY 4.0 | VERIFIED_CANDIDATE |
| DOC-PMC-EMERG-0001 | PMC11084294 | Cardiopulmonary Resuscitation: Clinical Updates and Perspectives | cardiac arrest / CPR | CC BY 4.0 | VERIFIED_CANDIDATE |
| DOC-PMC-RESP-0004 | PMC11097702 | Comparison of Observation Alone Versus Interventional Procedures in Hemodynamically Stable Patients With Pneumothorax: A Systematic Review and Meta-Analysis | pneumothorax | CC BY 4.0 | VERIFIED_CANDIDATE |
| DOC-PMC-RESP-0005 | PMC7762111 | Diagnosis and Management of Acute Respiratory Distress Syndrome in a Time of COVID-19 | ARDS / respiratory failure | CC BY 4.0 | VERIFIED_CANDIDATE_WITH_FRESHNESS_CAVEAT |
| DOC-PMC-CARD-0010 | PMC10980676 | Management of cardiogenic shock: a narrative review | shock | CC BY 4.0 | VERIFIED_CANDIDATE |
| DOC-PMC-CARD-0011 | PMC11278776 | Native Infective Endocarditis: A State-of-the-Art-Review | infective endocarditis | CC BY 4.0 | VERIFIED_CANDIDATE |
| DOC-PMC-CARD-0012 | PMC11267218 | Implantable Cardiac Devices in Patients with Brady- and Tachy-Arrhythmias: An Update of the Literature | bradyarrhythmia / AV block / device therapy | CC BY 4.0 | VERIFIED_CANDIDATE |
| DOC-PMC-CARD-0013 | PMC11203729 | Diagnostic Challenges in Aortic Stenosis | aortic valve disease | CC BY 4.0 | VERIFIED_CANDIDATE |
| DOC-PMC-CARD-0014 | PMC11172680 | Functional Mitral Valve Regurgitation: Mitral Valve Repair or Replacement? Our “Road Map” for the Appropriate Strategy | mitral valve disease | CC BY 4.0 | VERIFIED_CANDIDATE |

## Quality caveats before ingestion

### AF
`DOC-PMC-CARD-0008` is supporting evidence only. PLAB answers about diagnosis, anticoagulation, and rate/rhythm control must be reconciled with NICE NG196 before approval.

### Syncope
`DOC-PMC-CARD-0009` is a broad narrative review. NICE CG109 remains the UK assessment/referral authority.

### COPD
`DOC-PMC-RESP-0003` supports contemporary phenotype/treatable-trait management but does not replace NICE NG115. It should be paired with the existing UK COPD reference before question acceptance.

### Cardiac arrest
`DOC-PMC-EMERG-0001` is an overview rather than the UK ALS algorithm. It must never be used to fabricate RCUK timing, sequence, drug or defibrillation recommendations. RCUK 2025 remains the external ground truth.

### Pneumothorax
`DOC-PMC-RESP-0004` provides commercial-safe evidence around conservative versus interventional management in stable patients. BTS 2023 remains the external UK guideline and cannot be commercially ingested under the currently verified terms.

### ARDS / respiratory failure
`DOC-PMC-RESP-0005` is CC BY and broadly useful but was published in 2020 in the COVID era. It is acceptable as supporting pathophysiology/management evidence only with an explicit freshness penalty. A newer broad commercial-safe ARDS source remains desirable before large-scale PLAB generation.

### Shock
`DOC-PMC-CARD-0010` is cardiogenic-shock-specific. It does not close septic, hypovolaemic, obstructive or distributive shock coverage. The generic `Shock` MLA presentation therefore remains only partially covered after this wave.

### Infective endocarditis
`DOC-PMC-CARD-0011` closes the licence-safe supporting-evidence gap but **does not close the UK ground-truth gap**. Broad PLAB question generation for IE must wait for a verified current UK management source or a documented UK-reference strategy.

### Bradyarrhythmias
`DOC-PMC-CARD-0012` is useful for conduction/device therapy but is not a complete acute-bradycardia algorithm. Additional acute-management evidence remains desirable.

### Valve disease
`DOC-PMC-CARD-0013` and `DOC-PMC-CARD-0014` provide ingestible aortic/mitral supporting evidence. NICE NG208 remains the UK clinical verification spine.

## Wave 2 coverage effect

After acquisition/validation of these documents, the expected status changes are:

| Gap | Before Wave 2 | After validated ingestion |
|---|---|---|
| AF / tachyarrhythmia | GAP | PARTIAL/STRONG SUPPORT — AF specifically improved; SVT/VT/VF still need dedicated evidence |
| Bradyarrhythmia / AV block | GAP | PARTIAL — device/conduction evidence added; acute algorithm still incomplete |
| Cardiac arrest | GAP | PARTIAL — supporting evidence + RCUK reference; UK source not ingestible |
| Syncope | GAP | STRONG SUPPORT + UK reference |
| COPD | GAP | STRONG SUPPORT + existing NICE NG115 reference |
| Pneumothorax | GAP | STRONG SUPPORT + BTS reference-only |
| ARDS / respiratory failure | GAP | PARTIAL — freshness caveat remains |
| Shock | PARTIAL | PARTIAL/STRONG for cardiogenic shock only |
| Aortic valve disease | GAP | STRONG SUPPORT + NICE NG208 reference |
| Mitral valve disease | GAP | STRONG SUPPORT + NICE NG208 reference |
| Infective endocarditis | GAP | SUPPORTING EVIDENCE ONLY — UK authority still unresolved |

## Existing pipeline to use

No new ingestion path is permitted. Each PMC document must use the repository's existing JATS route:

`download_pmc_xml.py → inspect_pmc_jats.py → extract_pmc_jats.py → inspect_pmc_extraction.py → adapt_pmc_to_canonical.py → chunk_sections.py → validate_chunks.py → validate_chunk_integrity.py`

For every completed acquisition capture:

- immutable raw JATS
- canonical URL / PMCID / DOI when available
- licence node
- retrieval timestamp
- SHA-256
- section count
- chunk count
- schema result
- integrity result

## Release gate

A candidate moves from `VERIFIED_CANDIDATE` to `LOCAL_VALIDATED` only after its actual local artifact passes all existing validators. Web licence verification alone is not an ingestion PASS.

Question generation may begin on a topic only when:

1. ingestible supporting evidence is locally validated;
2. a current UK ground-truth source is identified;
3. the generated answer is reconciled against that UK source;
4. the five-option PLAB contract and citation validator pass;
5. no official GMC question wording has been copied.
