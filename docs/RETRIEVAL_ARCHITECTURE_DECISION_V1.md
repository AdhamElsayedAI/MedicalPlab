# MedicalPlab Retrieval Architecture Decision v1

**Status:** Accepted for the current startup MVP
**Decision scope:** Retrieval representation before RAG generation
**Model:** `Qwen/Qwen3-Embedding-0.6B`
**Corpus:** 227 validated chunks from 2 medical sources
**Date:** 2026-09-05

---

## 1. Decision

MedicalPlab will use **source-aware dense retrieval** as the current retrieval representation:

- Base model: `Qwen/Qwen3-Embedding-0.6B`
- Dense cosine-similarity retrieval
- Existing semantic metadata:
  - medical specialty
  - topics
  - retrieval section path
  - heading
  - evidence type
  - content
- Explicit source-document identity included in the retrieval representation

This is selected over the content-only representation because the source-aware variant improved source selection on both DEV and frozen held-out evaluation without reducing overall held-out Hit@1.

This does **not** mean source authority is fully solved. A separate source/authority policy layer remains required for explicit source requests and evidence-conflict handling.

---

## 2. Evaluation protocol

Two representations were evaluated.

### A — Content-only

The retrieval text did not contain an explicit source-document description.

### B — Source-aware

The same retrieval text additionally included the document identity, for example:

- WHO primary hypertension guideline
- PMC scientific review article

No model fine-tuning, source score boosting, reranking, or query-specific weights were used.

---

## 3. DEV v2

Evaluation set:

`medicalplab-retrieval-multisource-dev-v2`

- 30 total cases
- 26 answerable
- 4 unsupported
- 18 single-source
- 4 multi-source
- 4 authority-sensitive
- 4 unsupported

### Overall DEV comparison

| Metric | Content-only | Source-aware |
|---|---:|---:|
| Hit@1 | 0.9231 | 0.9231 |
| Recall@3 | 0.8686 | 0.8878 |
| Hit@5 | 0.9615 | 1.0000 |
| Recall@5 | 0.9103 | 0.9872 |
| MRR | 0.9487 | 0.9500 |
| nDCG@10 | 0.9261 | 0.9302 |
| GoldSourceRecall@5 | 0.9423 | 1.0000 |
| PreferredDoc@1 | 0.7500 | 1.0000 |

### Authority-sensitive DEV comparison

| Metric | Content-only | Source-aware |
|---|---:|---:|
| Hit@1 | 0.7500 | 1.0000 |
| Recall@1 | 0.6250 | 0.8750 |
| MRR | 0.8750 | 1.0000 |
| nDCG@10 | 0.8846 | 0.9794 |
| PreferredDoc@1 | 0.7500 | 1.0000 |

DEV suggested that explicit source identity materially improves primary-source selection.

---

## 4. Frozen held-out v1

Evaluation set:

`medicalplab-retrieval-multisource-heldout-v1`

Frozen SHA-256:

`59956d5179f62795d1a1b28384090c2170959641ed555053dec81e5218afcdfe`

- 24 total cases
- 20 answerable
- 4 unsupported
- 12 single-source
- 4 multi-source
- 4 authority-sensitive
- 4 unsupported

The held-out file was validated and hashed before either model run.

### Overall held-out comparison

| Metric | Content-only | Source-aware |
|---|---:|---:|
| Hit@1 | 0.9500 | 0.9500 |
| Recall@1 | 0.8500 | 0.8500 |
| Hit@3 | 0.9500 | 0.9500 |
| Recall@3 | 0.8750 | 0.8750 |
| Hit@5 | 0.9500 | 0.9500 |
| Recall@5 | 0.9250 | 0.9250 |
| Hit@10 | 0.9500 | 1.0000 |
| Recall@10 | 0.9500 | 0.9750 |
| MRR | 0.9542 | 0.9563 |
| nDCG@10 | 0.9299 | 0.9357 |
| GoldSourceRecall@10 | 0.9500 | 0.9750 |
| PreferredDoc@1 | 0.7500 | 1.0000 |

### Held-out single-source

Both variants achieved:

- Hit@1 = 1.0000
- Recall@1 = 1.0000
- MRR = 1.0000
- nDCG@10 = 1.0000

### Held-out authority-sensitive

| Metric | Content-only | Source-aware |
|---|---:|---:|
| Hit@1 | 0.7500 | 0.7500 |
| Hit@10 | 0.7500 | 1.0000 |
| MRR | 0.7708 | 0.7812 |
| nDCG@10 | 0.7500 | 0.8289 |
| GoldSourceRecall@10 | 0.7500 | 1.0000 |
| PreferredDoc@1 | 0.7500 | 1.0000 |

### Held-out multi-source

At Top-5, both variants had the same:

- Hit@5 = 1.0000
- Recall@5 = 0.8750
- GoldSourceRecall@5 = 0.8750

At Top-10, source-aware retrieval lost some multi-source coverage:

- Content-only Recall@10 = 1.0000
- Source-aware Recall@10 = 0.8750

This trade-off is documented and must not be hidden.

---

## 5. Important failure case

`HOLD-018` remained difficult.

Query:

> من الـWHO primary guideline تحديدًا، إمتى نعتبر beta-blocker اختيار مناسب بسبب ischemic heart disease؟

Gold evidence:

`DOC-WHO-CARD-0001:B0028`

The content-only representation placed the first gold block around rank 12.

The source-aware representation improved this to around rank 8 and moved a WHO block to rank 1, but the exact gold evidence was still not in the Top-5.

Interpretation:

**Source identity helped the retriever select the correct document family, but did not fully solve exact passage selection inside that document.**

Therefore MedicalPlab must distinguish:

1. semantic passage relevance;
2. source authority / source constraints;
3. exact evidence sufficiency.

These should not be collapsed into one embedding score.

---

## 6. Architecture implication

The current retrieval architecture is:

```text
User Query
   |
   v
Query Understanding
   |
   v
Source-Aware Dense Retrieval
Qwen3-Embedding-0.6B
   |
   v
Candidate Evidence
   |
   +--> Source / Authority Policy
   |
   +--> Evidence Sufficiency
   |
   v
Grounded RAG Generation
```

The source-aware embedding is the selected baseline, but explicit requests such as:

- "according to WHO"
- "from the primary guideline"
- "compare the guideline with the review"

should eventually be handled by a dedicated source-policy / metadata layer rather than relying only on semantic similarity.

---

## 7. What the results do NOT prove

These results are retrieval results only.

They do **not** prove:

- clinical accuracy;
- diagnostic accuracy;
- treatment safety;
- final RAG answer quality;
- production performance at larger corpus scale;
- evidence abstention performance.

The current unsupported cases are diagnostic only because no evidence-sufficiency threshold has yet been calibrated.

---

## 8. Fine-tuning decision

No fine-tuning is justified at this stage.

Current evidence shows that the pretrained Qwen3 embedding model already has strong retrieval performance.

The next bottlenecks are:

1. evidence sufficiency / abstention;
2. authority-aware source policy;
3. grounded answer generation;
4. adaptive-learning logic.

Fine-tuning should only be considered if a later, larger benchmark demonstrates a persistent retrieval error class that cannot be fixed more cleanly with data, metadata, policy, or retrieval architecture.

---

## 9. Next phase

**Evidence Sufficiency Calibration v1**

Goal:

Determine when MedicalPlab has enough retrieved evidence to answer and when it should abstain.

The calibration phase must use a dedicated calibration set rather than modifying the frozen held-out benchmark.

After evidence sufficiency is calibrated:

```text
Retrieval
   -> Evidence Sufficiency
   -> Grounded RAG
   -> Citation verification
   -> Adaptive Learning
```

---

## 10. Startup-track interpretation

The value of this work is not that MedicalPlab "uses an LLM."

The technical differentiation is the controlled evidence pipeline:

- governed medical sources;
- provenance-preserving ingestion;
- validated chunking;
- multilingual retrieval;
- document-aware evaluation;
- source-authority awareness;
- frozen held-out benchmarking;
- planned evidence abstention;
- grounded generation;
- adaptive learning.

This is the foundation for a defensible medical-education AI product rather than a generic chatbot.
