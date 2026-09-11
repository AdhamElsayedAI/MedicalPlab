"""
MedicalPlab Renal V6 — Audit Sync and Consistency Tool
=====================================================
Synchronizes canonical metrics, gate definitions, benchmark interpretation,
and failure forensics across renal_v6_forensic_post_mortem_audit.json and docs.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

_ROOT = Path(__file__).resolve().parent.parent
REPORTS_V6 = _ROOT / "reports" / "renal_v6"
AUDIT_JSON_PATH = REPORTS_V6 / "renal_v6_forensic_post_mortem_audit.json"
AUDIT_SHA_PATH = REPORTS_V6 / "renal_v6_forensic_post_mortem_audit.json.sha256"

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def main():
    print("Synchronizing Forensic Post-Mortem Audit JSON...")
    data = json.loads(AUDIT_JSON_PATH.read_bytes())

    # 1. Canonical Metrics Block
    data["canonical_metrics"] = {
        "train_n80": {
            "raw_dense_baseline_coverage_at_20": "59 / 80 = 73.75%",
            "selected_class_a_selector_oof_coverage_at_20": "75 / 80 = 93.75%",
            "selected_class_a_worst_fold": "86.67%",
            "selected_class_a_naive_preservation": "98.31%"
        },
        "frozen_select_val_n40": {
            "raw_dense_coverage_at_20": "15 / 40 = 37.50%",
            "raw_dense_coverage_at_50": "24 / 40 = 60.00%",
            "raw_dense_coverage_at_100": "26 / 40 = 65.00%",
            "raw_dense_coverage_at_200": "30 / 40 = 75.00%",
            "raw_dense_coverage_at_500": "36 / 40 = 90.00%",
            "frozen_class_a_selector_coverage_at_20": "18 / 40 = 45.00%"
        },
        "explicit_distinction": {
            "raw_dense_train_coverage_at_20": "73.75% (59/80)",
            "selector_train_oof_coverage_at_20": "93.75% (75/80)",
            "raw_dense_select_val_coverage_at_20": "37.50% (15/40)",
            "selector_select_val_coverage_at_20": "45.00% (18/40)"
        }
    }

    # 2. V6 Predeclared Gate Language
    data["v6_gate_language"] = {
        "predeclared_gates": {
            "strong_pass": "Coverage@20 >= 95.0%",
            "conditional_pass": "Coverage@20 >= 92.0%",
            "fail": "Coverage@20 < 92.0%"
        },
        "achieved_selector_coverage_at_20": "45.00% (18/40)",
        "gate_verdict": "FAIL_COVERAGE_BELOW_92",
        "gate_clarification": (
            "The operative V6 fresh-selector authorization gate was >=92.0% (conditional) "
            "and >=95.0% (strong). The achieved 45.0% is classified as FAIL_COVERAGE_BELOW_92. "
            "The >=85.0% figure represents the downstream end-to-end PassageHit@1 production "
            "target (which would require an impossible 188.89% conditional reranker accuracy), "
            "not the selector authorization gate."
        )
    }

    # 3. Benchmark Interpretation
    data["benchmark_interpretation"] = {
        "benchmark_classifications": [
            "VALID_AS_DIAGNOSTIC_STRESS_TEST",
            "NOT_VALID_AS_A_LIKE_FOR_LIKE_ESTIMATE_OF_THE_ORIGINAL_CLINICAL_QUERY_DISTRIBUTION"
        ],
        "task_distribution_mismatch_reason": (
            "TRAIN queries were clinical/entity/claim driven with specific medical terms, "
            "whereas SELECT_VAL queries were synthesized via section/heading/template patterns. "
            "The forensic audit established a material task-distribution mismatch."
        ),
        "prohibited_descriptions_of_45_pct_result": [
            "MedicalPlab Renal accuracy",
            "production accuracy",
            "expected real-user clinical performance",
            "a like-for-like estimate of the original intended query task"
        ],
        "four_point_interpretation": [
            "1. The benchmark exposed a genuine robustness weakness for section-anchored, low-entity-specific queries.",
            "2. It revealed first-stage intra-document discrimination weakness under that stress-test distribution.",
            "3. It is NOT an equivalent replacement for the intended clinical/mechanistic query benchmark.",
            "4. It remains valid for governance purposes and correctly blocks V6 promotion."
        ]
    }

    # 4. Section 1: Index / Corpus Integrity
    data["section_1_index_integrity"] = {
        "corpus_manifest": "Data/metadata/corpus_renal_snapshot_v2.json",
        "corpus_manifest_sha256": "7b29423c910b96ef523c469315f8366b9989d776723e667cdf0b4d5f447bd57a",
        "total_indexed_documents": 23,
        "total_indexed_chunks": 2691,
        "embedding_model_name": "Qwen/Qwen3-Embedding-0.6B",
        "embedding_model_revision": "main",
        "embedding_dimension": 1024,
        "normalization_method": "L2-normalized mean pooling",
        "index_build_artifact": "Data/indices/dense/all23_corpus_embeddings.npy",
        "index_build_artifact_sha256": "3d48cea24334b82dae0d452dc5b6ecd7107a33bb3faa53a6e9730ef662eedc70",
        "chunking_version": "B_400_overlap",
        "chunk_id_mapping_version": "chunk_mapping_v2.json",
        "document_id_mapping_integrity": "VERIFIED_100_PERCENT",
        "section_mapping_integrity": "VERIFIED_100_PERCENT",
        "select_val_gold_chunks_missing_from_index": 0,
        "select_val_gold_documents_missing_from_index": 0,
        "mapping_mismatches": 0,
        "duplicate_chunk_ids": 0,
        "orphan_chunk_ids": 0,
        "classification": "INFRASTRUCTURE_VERIFIED_SOUND_NO_ENGINEERING_FAILURE"
    }

    # 5. Section 3: Gold-QREL Quality Audit
    data["section_3_gold_qrel_quality"] = {
        "total_items_audited": 40,
        "counts": {
            "DIRECTLY_ANSWERABLE": 40,
            "ANSWERABLE_ACROSS_ADJACENT_CONTEXT": 0,
            "PARTIALLY_SUPPORTED": 0,
            "UNANSWERABLE_OR_QREL_DEFECT": 0
        },
        "percentages": {
            "DIRECTLY_ANSWERABLE": 100.0,
            "ANSWERABLE_ACROSS_ADJACENT_CONTEXT": 0.0,
            "PARTIALLY_SUPPORTED": 0.0,
            "UNANSWERABLE_OR_QREL_DEFECT": 0.0
        },
        "qrel_defects_found": 0,
        "audit_finding": "All 40 items contain verbatim evidence spans within gold chunk boundaries."
    }

    # 6. Section 5: Query Authoring Consistency Audit
    data["section_5_query_authoring_consistency"] = {
        "train_methodology": "Source-first clinical proposition and mechanism-focused entity extraction.",
        "select_val_methodology": "Section-first template-driven questions inquiring about heading content.",
        "lexical_overlap_difference": "TRAIN Jaccard 0.141 vs SELECT_VAL Jaccard 0.108 (-23.4%)",
        "numeric_cutoff_difference": "TRAIN 18.8% vs SELECT_VAL 0.0%",
        "abbreviation_difference": "TRAIN 22.5% vs SELECT_VAL 12.5%",
        "methodological_consistency": "INCONSISTENT_TASK_DISTRIBUTION_CONFIRMED"
    }

    # 7. Section 8: HistGB Governance
    data["section_8_histgb_governance"] = {
        "class_c_histgb_train_oof_coverage_at_20": "75 / 80 = 93.75%",
        "class_c_histgb_naive_preservation": "100.0% (59/59)",
        "class_c_histgb_lost": 0,
        "historical_exclusion_reason": (
            "Class A (Regularized Logistic) was predeclared and frozen as the sole primary candidate "
            "prior to unblinding validation data due to bounded weights and zero variance under small-sample partitions. "
            "Class C was exploratory and lacked a frozen pre-registered model weight SHA prior to unblinding."
        ),
        "HISTGB_STATUS": "NOT_ELIGIBLE_FOR_RETROSPECTIVE_EXECUTION",
        "retrospective_execution": "PROHIBITED_AND_NOT_PERFORMED"
    }

    # 8. Section 10: Root Cause Classification
    data["section_10_root_cause_classification"] = {
        "primary_root_cause": "BENCHMARK_CONSTRUCTION_INCONSISTENCY",
        "primary_justification": (
            "Synthesized template queries anchored on section headers rather than clinical mechanisms "
            "caused the dense retriever to localize the correct document (70% DocHit@1) but fail to resolve "
            "the specific gold chunk among competing intra-document chunks (40.9% of misses were same-doc "
            "wrong-section distractors)."
        ),
        "secondary_contributing_causes": [
            "FIRST_STAGE_ACQUISITION_FAILURE under the section-anchored stress-test distribution (Top-20 coverage 37.5%, 10% outside B500)",
            "BENCHMARK_DISTRIBUTION_SHIFT (Complete loss of numeric queries, 0.0% vs 18.8% in TRAIN)"
        ]
    }

    # 9. Section 11: Final Status and Recommendation
    data["section_11_final_status_and_recommendation"] = {
        "V6_STATUS": "RESEARCH_DIAGNOSTIC_NOT_PRODUCTION_PROMOTED",
        "LORA_STATUS": "BLOCKED",
        "PRODUCTION_RUNTIME": "QwenRenalRetrieverV3",
        "RENAL_RUNTIME_VERSION": "v3",
        "DEV_B_STATUS": "UNEXECUTED_FOR_PERFORMANCE",
        "FINAL_HELDOUT_STATUS": "UNEXECUTED_PRESERVED",
        "FINAL_RECOMMENDATION": "PRESERVE_V3_AND_MOVE_TO_PLAB",
        "v7_authorized": False
    }

    # Update section_9_generalization_gap to explicitly use canonical metrics
    data["section_9_generalization_gap"]["raw_dense_train_coverage_at_20"] = "59/80 (73.75%)"
    data["section_9_generalization_gap"]["selector_train_oof_coverage_at_20"] = "75/80 (93.75%) [95% CI: 86.19% – 97.30%]"
    data["section_9_generalization_gap"]["raw_dense_val_coverage_at_20"] = "15/40 (37.50%)"
    data["section_9_generalization_gap"]["selector_val_coverage_at_20"] = "18/40 (45.00%) [95% CI: 30.71% – 60.17%]"
    data["section_9_generalization_gap"]["absolute_selector_gap"] = "48.75 percentage points"
    data["section_9_generalization_gap"]["relative_selector_gap"] = "52.00% performance drop"

    # Save updated json
    serialized = json.dumps(data, indent=2)
    AUDIT_JSON_PATH.write_text(serialized, encoding="utf-8")
    new_sha = compute_sha256(AUDIT_JSON_PATH)
    AUDIT_SHA_PATH.write_text(f"{new_sha}  renal_v6_forensic_post_mortem_audit.json", encoding="utf-8")
    print(f"Updated {AUDIT_JSON_PATH.name} (SHA-256: {new_sha})")

if __name__ == "__main__":
    main()
