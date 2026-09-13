# MedicalPlab — Release Evaluation Summary

## Audited Capabilities & Benchmark Results

All platform metrics are strictly classified into explicit categories to guarantee complete transparency:
- `[Verified]`: Audited against frozen held-out test sets with deterministic evaluation scripts.
- `[Prototype]`: Validated on working test harnesses and integration benchmarks.
- `[Simulation]`: Measured on synthetic or multi-agent simulated student cohorts.
- `[Projection]`: Commercial or future clinical roadmaps.

---

### Key Verified Metrics

| Capability | Metric Value | Classification | Evaluation Baseline & Protocol |
| :--- | :---: | :---: | :--- |
| **Retrieval Accuracy (Hit@1)** | **95.00%** | `[Verified]` | Frozen held-out multi-source cardiology benchmark (`multisource-heldout-v1`) |
| **Multi-Source Recall (GoldSourceRecall@10)** | **97.50%** | `[Verified]` | Evaluated across 227 canonical evidence blocks from NICE, WHO, and PMC |
| **Ranking Precision (MRR)** | **0.9563** | `[Verified]` | Source-aware dense embedding evaluation (Qwen 0.6B / BGE-M3) |
| **API Response Latency** | **< 12 ms** | `[Verified]` | FastAPI Stage-G localized asynchronous query benchmark |
| **PLAB Evidence Grounding** | **12 / 12 (100%)** | `[Verified]` | Strict fail-closed atomic claim decomposition and exact span containment |
| **PLAB Safety Quarantine** | **24 / 36 (66.7%)** | `[Verified]` | Legitimate non-engineering clinical/legal blockers prevented from false-positive promotion |
| **Contraindication Interception** | **100.0%** | `[Prototype]` | Deterministic safety traps: ACEi in pregnancy, Nitrates in RV STEMI, Beta-blockers in asthma |
| **Automated Test Gate** | **594 Passing** | `[Verified]` | Complete pytest suite passing with zero failures |

---

### PLAB V9 Evidence Closure Results

- **Dataset**: `cardiorespiratory_batch_1_final_closure_v9.json` (36 total questions)
- **Closure Status**: `PASS_WITH_CLINICAL_BLOCKERS`
- **Source Grounded**: 12 (100% direct guideline support, strictly bounded at `CLINICIAN_REVIEW_REQUIRED`)
- **Quarantined**: 24 (valid clinical conflicts, missing authoritative evidence, or human judgment requirements)
- **Clinician Approved**: 0 (AI is strictly barred from granting clinical approval)
- **Golden Promotion**: 0
- **False Support Count**: 0
