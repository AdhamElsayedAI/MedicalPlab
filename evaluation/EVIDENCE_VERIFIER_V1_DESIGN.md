# MedicalPlab Stage-B Claim-Support Verifier v1

## Status

Design contract only. No verifier model is selected by this document.

## Why Stage B exists

The retrieval-only Evidence Sufficiency baseline showed that semantic retrieval confidence is useful but is not sufficient to decide whether the retrieved evidence materially supports a query.

On the 48-case calibration set:

- Top-1 AUROC: 0.8384
- Top-1 AUPRC: 0.7996
- Contrastive violations: 4/28
- Maximum coverage with zero observed non-supported full accepts: 6.25%
- False-refusal rate at that point: 85%

Therefore Stage A remains responsible for relevance and source-aware candidate retrieval, while Stage B is responsible for claim-level support verification.

## Architecture

User Query
→ Stage A: source-aware retrieval
→ Top-10 unique candidate evidence blocks
→ Stage B: claim-support verifier
→ SUPPORTED / PARTIAL / UNSUPPORTED
→ deterministic answer policy
→ grounded generation with citations

The verifier does not replace retrieval and does not use parametric medical knowledge as evidence.

## Runtime input contract

The verifier may receive only runtime-available fields:

- raw user query;
- the top 10 unique retrieved blocks, in retrieval order;
- for each block:
  - block key;
  - source/document label;
  - heading/section metadata;
  - block text;
  - retrieval score.

The verifier must NOT receive any calibration-only or gold fields, including:

- support_label;
- expected_action;
- supporting_blocks;
- missing_support;
- negative_type;
- target_concept;
- hard_negative;
- contrast_group_id;
- gold relevance labels.

This prevents evaluation leakage.

## Evidence packet

Each evidence item is represented as:

```text
[DOC-WHO-CARD-0001:B0037]
Source: World Health Organization (WHO) primary guideline
Heading: ...
Section: ...
Retrieval score: ...
Text: ...
```

Top-10 is retained because Stage A has already shown that exact supporting evidence can occur below rank 5. Retrieval order remains visible, but Stage B must judge support from the text, not from score magnitude alone.

## Verification policy

The verifier must:

1. Decompose the query into material claims.
2. Judge each material claim only against the supplied evidence packet.
3. Treat semantic relatedness as insufficient unless the requested material claim is actually supported.
4. Preserve exact qualifiers:
   - numbers and units;
   - population;
   - condition;
   - source requested by the user;
   - time/version;
   - treatment context;
   - comparisons and equivalence claims.
5. For a source-specific query, evidence from another source cannot satisfy that source constraint.
6. For a multi-claim query:
   - all material claims supported → `supported`;
   - at least one material claim supported and at least one material claim unsupported → `partial`;
   - no material claim supported → `unsupported`.
7. Never infer a missing exact numeric fact, dose conversion, percentage, brand, timing interval, population-specific recommendation, or future evidence from a semantically related passage.
8. Never use outside medical knowledge to upgrade support.
9. Return structured JSON only.

## Output contract

The output is validated by:

`schemas/evidence_verifier_output_v1.schema.json`

Required fields:

- `verdict`: `supported | partial | unsupported`
- `claims`: claim-level support decisions and evidence references
- `source_constraint_satisfied`: boolean or null
- `verdict_rationale`: concise evidence-grounded explanation

No self-reported confidence score is used in v1 because an uncalibrated language-model confidence value would not constitute a reliable safety signal.

## Deterministic answer policy

The verifier predicts evidence support only.

Application behavior is derived outside the model:

- `supported` → answer from verified evidence + citations
- `partial` → qualified answer limited to supported claims; explicitly state what is missing
- `unsupported` → abstain from the unsupported material claim

This separation keeps evidence verification distinct from product policy.

## Calibration protocol

Stage-B v1 is evaluated on the existing 48-case Evidence Sufficiency calibration set:

- supported: 20
- partial: 12
- unsupported: 16

This set remains calibration data, not an independent final test set.

The existing frozen retrieval held-out set must not be used to tune the verifier prompt, model, thresholds, or decision rules.

After model/prompt selection, a separate frozen Evidence Sufficiency test set must be created.

## Primary metrics

Three-way classification:

- confusion matrix;
- macro F1;
- per-class precision, recall, and F1.

Binary full-accept safety view:

- supported = positive/full accept;
- partial + unsupported = do-not-fully-accept.

Report:

- Unsafe Accept Rate;
- False Refusal Rate;
- Supported Accept Precision;
- Supported Recall;
- Coverage.

Also report:

- contrastive-pair violation rate;
- breakdown by language;
- breakdown by claim type;
- breakdown by negative type.

## Baseline comparison

Stage B must be compared directly against the frozen retrieval-only calibration result:

- Top-1 AUROC: 0.8384
- Top-1 AUPRC: 0.7996
- 4/28 contrastive violations
- zero-observed-unsafe threshold coverage: 6.25%
- false refusal at that point: 85%

The purpose of Stage B is not to produce a prettier score. It must materially improve claim-support decisions on hard near-miss cases while retaining useful supported-case coverage.

## Model-selection rule

Do not select a model because it is larger or more impressive.

A verifier candidate advances only if it:

- follows the JSON contract reliably;
- uses only provided evidence;
- handles English, Arabic, and mixed queries;
- improves full-accept safety/coverage trade-offs;
- handles contrastive hard negatives;
- is feasible for the MedicalPlab deployment and cost model.

## Guardrails

These metrics evaluate evidence sufficiency, not clinical accuracy.

Passing the verifier benchmark does not establish diagnostic safety, treatment safety, or final RAG quality.
