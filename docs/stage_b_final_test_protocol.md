# Independent Evidence Sufficiency test protocol

Blocked on candidate selection: first record a selected code SHA, prompt/config
fingerprint, model revision, complete calibration output and a failure taxonomy.
Do not use the existing frozen retrieval test for this purpose.

After locking the candidate, an independent author should create new cases from
corpus evidence with different facts and contrasts, not paraphrases of calibration.
Keep the verifier operator blind to labels until predictions are fixed. Each label
must have a rationale and exact corpus provenance; use two independent adjudicators
and record disagreements. Do not claim independent adjudication if unavailable.

Cover Arabic, English and mixed queries across direct facts, numeric facts,
multi-claim requests, source-specific requests, recommendations and clinical
education. Include wrong population, wrong condition, source miss, temporal scope,
related-but-unsupported, table rows and exact-fact negatives. Balance labels and
report the actual coverage matrix and counts; do not fill gaps by relabeling.

Generate retrieval packets with the unchanged source-aware Top-10 retriever before
evaluation. Record corpus, retrieval configuration, dataset and packet SHA-256
hashes in a freeze manifest. Store labels separately from runtime inputs. Sign off
and timestamp the manifest before invoking the selected candidate. Record predictions
and failures for all cases, compute the same metrics and publish the initial result.
Any subsequent tuning consumes that set as development data and needs a new test.
