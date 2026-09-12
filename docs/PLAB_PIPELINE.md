# PLAB content and review pipeline

The active engineering checkpoint is
`Data/questions/versions/cardiorespiratory_batch_1_source_audit_v2.json`.
It preserves all 36 questions from the previously committed source audit. Its
manifest records 7 historically AI-verified candidates and 29 requiring source
repair. Those labels are engineering evidence, not clinician validation. None
is automatically Golden.

The original v1 batch is archived byte-for-byte as
`Data/questions/versions/cardiorespiratory_batch_1_frozen_v1.json`, matching the
unchanged `cardiorespiratory_batch_1_v1.manifest.json`. The original batch path,
review queue and historical reports remain intact. The active version has its
own manifest and hash; it is not a new clinical release. Version files bypass
Git line-ending conversion. `Scripts/version_plab_repair_checkpoint.py`
reproduces this one-time migration from the pinned Git history and refuses any
existing destination.

The workflow is source evidence → candidate → source/AI audit → clinician review
→ explicit Golden promotion. Approval through the review API or import CLI saves
an approved review with `golden_status=false`. An authorized operator must invoke
`Scripts/promote_golden.py promote QUESTION_ID` separately; the gate rechecks
content version/hash, all clinical review findings, identity, timestamp and
citations. Questions marked `NEEDS_SOURCE_REPAIR` remain blocked. Quote presence
alone does not prove that the answer or distractors are medically correct.

Source-grounded, AI-reviewed and clinician-reviewed are distinct assertions.
Historical AI labels are retained as such. The review token protects an internal
operator interface; verification of actual clinician credentials is an external
institutional responsibility. Do not import model-generated reviews as clinicians.

SQLite stores complete attempt envelopes, retry keys, revisions, current reviews
and append-only review events. A revision and invalidation of its old approval
commit in one transaction. Storage failures return errors instead of successful
responses backed only by memory. Retry responses and progress survive restart.
Legacy attempts without full metadata retain an explicit unknown-topic fallback.

Use a durable local disk and a single API worker for the pilot. Multi-host
deployment requires a shared transactional store and concurrency control for
review assignment; SQLite plus per-process caches is not such a deployment.

`Scripts/repair_plab_cardiorespiratory.py --output-dir NEW_DIRECTORY` creates a
new AI-only candidate/audit directory. It never updates the input batch.
`write_freeze` writes a new Golden package with exclusive creation; existing
freeze files are never replaced. Freezes include detached question copies,
review identities and timestamps in their content identity.

Clinical release is blocked until source repairs and actual clinician review
are complete. The upstream retrieval and evidence gates remain prerequisites
for scaling content generation.
