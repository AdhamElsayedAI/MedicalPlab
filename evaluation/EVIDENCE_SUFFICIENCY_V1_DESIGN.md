# Evidence Sufficiency Calibration v1

## Status

Design accepted for implementation after the retrieval milestone.

## Objective

MedicalPlab must not answer merely because retrieval returned a semantically similar passage.

The Evidence Sufficiency layer decides whether the available corpus actually supports the claim requested by the learner.

The production decision is:

```text
retrieved evidence
      |
      v
evidence sufficiency gate
      |
      +--> supported   -> answer from evidence + citations
      |
      +--> partial     -> qualified answer only for supported parts
      |                  or abstain when the missing part is material
      |
      +--> unsupported -> abstain
```

This is an educational safety and reliability gate, not a diagnosis or treatment decision system.

## Why this is a separate layer

Retrieval similarity answers:

> "What passages are semantically close to the query?"

Evidence sufficiency answers:

> "Do those passages actually support the requested claim?"

These are different problems.

A high embedding score can still occur for a query whose exact fact, population, source constraint, or requested clinical claim is absent from the corpus.

Therefore MedicalPlab will not use an arbitrary embedding threshold as the final answerability rule.

## Dataset separation

The following datasets have different roles and must remain separate:

```text
retrieval DEV v2
    -> retrieval development

frozen retrieval held-out v1
    -> independent retrieval representation evaluation

evidence sufficiency calibration v1
    -> threshold / gate calibration

future frozen evidence-sufficiency test v1
    -> independent final gate evaluation
```

The frozen retrieval held-out set must not be edited or reused as the threshold-tuning set.

## Label policy

### supported

The corpus directly supports the material claim being requested.

Expected production action:

```text
answer
```

### partial

The corpus supports part of the request but a material component is missing.

Examples:

- one half of a multi-claim query is supported;
- the general recommendation exists but the exact requested numeric value does not;
- a closely related population is covered but the requested population is not.

Expected production action:

```text
qualified_answer
```

For the first conservative binary gate baseline, `partial` is grouped with `unsupported` as **do not fully accept**.

### unsupported

The corpus does not support the requested material claim.

Expected production action:

```text
abstain
```

## Hard-negative taxonomy

The calibration set should deliberately include semantically close negatives.

Supported and unsupported queries should often differ by only one material fact.

Negative types:

- `exact_fact_absent`
- `wrong_population`
- `wrong_condition`
- `out_of_corpus`
- `source_constraint_miss`
- `temporal_out_of_scope`
- `patient_specific`
- `semantically_related_but_unsupported`
- `multi_claim_partial`

This is important because easy off-topic negatives make a confidence gate look artificially strong.

## Contrast groups

`contrast_group_id` links a supported anchor with one or more near-miss cases.

Example pattern:

```text
CG-001
  supported anchor:
    asks for a claim explicitly present in the corpus

  near-miss:
    same wording and topic, but changes one material detail
    that is not supported by the corpus
```

Contrast groups directly test whether the gate detects evidence support rather than topic similarity.

## Calibration-set target

Initial target for the current two-document corpus:

```text
48 cases total

20 supported
12 partial
16 unsupported
```

Language target:

```text
20 English
16 Arabic
12 mixed
```

Design target:

- at least 12 contrast groups;
- supported cases across WHO and PMC;
- numeric facts;
- recommendations;
- source-specific questions;
- multi-claim questions;
- hard negatives that remain semantically close to hypertension content.

These are dataset-design targets, not performance claims.

## Retrieval-only baseline

Before adding any evidence verifier, establish how far retrieval-only signals can go.

Candidate runtime features:

```text
top1_score
top2_score
top1_top2_margin
top3_mean
top5_mean
top5_std
top1_minus_top5_mean
requested_source_present_at_1
requested_source_present_at_5
distinct_documents_in_top5
```

Gold labels are used only during offline calibration/evaluation.

Gold block identity is never available to the production gate.

## Threshold selection

Do not choose a threshold such as `0.65` by intuition.

For each candidate score or simple rule:

1. sweep thresholds on the dedicated calibration set;
2. measure unsafe accepts and false refusals;
3. inspect performance by language and negative type;
4. prefer the highest useful coverage under the safest observed behavior;
5. document the chosen rule and its limitations.

If retrieval-only features cannot separate supported from near-miss negatives, that is an important result.

It empirically justifies a second-stage evidence verifier.

## Required metrics

Primary safety metrics:

```text
unsafe_accept_rate
false_refusal_rate
supported_accept_precision
coverage
```

Diagnostic metrics:

```text
AUROC
AUPRC
risk-coverage curve
performance by language
performance by negative_type
performance by claim_type
```

For a small corpus and small evaluation set, report counts as well as rates.

Do not present these metrics as clinical accuracy.

## Escalation rule

The architecture is intentionally staged.

```text
Stage A
retrieval-only sufficiency baseline

if separation is strong enough:
    keep the simple interpretable gate

if hard negatives overlap materially:
    add Stage B evidence verifier
```

Potential Stage B:

```text
query
+
top retrieved evidence
      |
      v
claim-support verifier
      |
      +--> supported
      +--> partial
      +--> unsupported
```

The verifier should evaluate claim support from the retrieved evidence, not answer from its own parametric medical knowledge.

## Startup / judging value

This layer turns MedicalPlab from:

```text
"we added RAG"
```

into:

```text
"we independently measure whether the system has enough evidence to answer,
and it can abstain when the corpus does not support the claim."
```

For the startup MVP this creates a defensible product capability:

- evidence-aware answering;
- measurable abstention behavior;
- auditable failure modes;
- safer educational usage;
- clear path to quality monitoring in production.

## Next implementation step

Build the calibration set from the current evidence catalog.

Do not generate unsupported cases from memory alone.

Every `supported` and `partial` case must be checked against the source catalog, and every `unsupported` hard negative must be verified as absent for the requested material claim within the current corpus.
