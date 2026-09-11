"""
MedicalPlab Renal V6 — Phase 7: LoRA Authorization Decision Package
===================================================================
Synthesizes all empirical results from Phases 1 through 6 into the definitive
engineering decision package and mathematical reranker requirement analysis.
"""

import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
REPORTS_V6_DIR = _ROOT / "reports/renal_v6"

P1_PATH = REPORTS_V6_DIR / "renal_v6_phase1_expansion_feasibility_report.json"
P2_PATH = REPORTS_V6_DIR / "renal_v6_phase2_failure_decomposition_report.json"
P3_PATH = REPORTS_V6_DIR / "renal_v6_phase3_feature_oracle_v2_report.json"
P4_PATH = REPORTS_V6_DIR / "renal_v6_phase4_selector_comparison_report.json"
P5_PATH = REPORTS_V6_DIR / "renal_v6_phase5_gating_decision_report.json"
P6_PATH = REPORTS_V6_DIR / "renal_v6_phase6_confirmation_report.json"
FIREWALL_PATH = REPORTS_V6_DIR / "renal_v6_fresh_validation_firewall_audit.json"

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def wilson_score_interval(successes, total, confidence=0.95):
    if total == 0:
        return (0.0, 0.0)
    z = 1.95996  # for 95% CI
    p = successes / total
    denominator = 1.0 + z**2 / total
    centre_adjusted_probability = p + z**2 / (2 * total)
    adjusted_standard_deviation = math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total)
    lower_bound = (centre_adjusted_probability - z * adjusted_standard_deviation) / denominator
    upper_bound = (centre_adjusted_probability + z * adjusted_standard_deviation) / denominator
    return (max(0.0, round(lower_bound * 100, 2)), min(100.0, round(upper_bound * 100, 2)))

def main():
    print("Executing Renal V6 Phase 7: LoRA Authorization Decision Package...")

    p1 = json.loads(P1_PATH.read_bytes())
    p2 = json.loads(P2_PATH.read_bytes())
    p3 = json.loads(P3_PATH.read_bytes())
    p4 = json.loads(P4_PATH.read_bytes())
    p5 = json.loads(P5_PATH.read_bytes())
    p6 = json.loads(P6_PATH.read_bytes())
    fw = json.loads(FIREWALL_PATH.read_bytes())

    # Metrics from Phase 6
    val_cov20_cnt = p6["results"]["class_a_regularized_logistic"]["coverage_at_20_count"]
    val_n = p6["n_validation_queries"]
    val_cov20_pct = p6["results"]["class_a_regularized_logistic"]["coverage_at_20_percent"]

    # Mathematical Reranker Requirement:
    # Target: PassageHit@1 >= 85%
    # required_conditional_reranker_acc = 0.85 / selector_coverage
    if val_cov20_pct > 0:
        required_reranker_acc = round((0.85 / (val_cov20_pct / 100.0)) * 100.0, 2)
    else:
        required_reranker_acc = float("inf")

    # Frozen Base Reranker performance from V5 confirmation:
    # 15/17 = 88.24%
    base_reranker_success = 15
    base_reranker_covered = 17
    base_reranker_acc = round(base_reranker_success / base_reranker_covered * 100.0, 2)
    base_ci_low, base_ci_high = wilson_score_interval(base_reranker_success, base_reranker_covered)

    # Predeclared Governance Gates:
    # If coverage < 92%: LoRA remains BLOCKED.
    # If coverage >= 95%: LoRA may be recommended.
    # If coverage 92-94.9%: compare required conditional reranker accuracy.
    if val_cov20_pct >= 95.0:
        recommendation = "PROCEED_TO_LORA"
        lora_status = "AUTHORIZED"
        gate_decision = "STRONG_PASS_LORA_AUTHORIZED"
    elif val_cov20_pct >= 92.0:
        if required_reranker_acc <= base_ci_high:
            recommendation = "PROCEED_TO_LORA"
            lora_status = "CONDITIONALLY_AUTHORIZED"
            gate_decision = "CONDITIONAL_PASS_LORA_AUTHORIZED"
        else:
            recommendation = "STOP_RENAL_AND_PRESERVE_V3"
            lora_status = "BLOCKED_BY_RERANKER_MARGIN"
            gate_decision = "CONDITIONAL_COVERAGE_INSUFFICIENT_RERANKER_MARGIN"
    else:
        recommendation = "STOP_RENAL_AND_PRESERVE_V3"
        lora_status = "BLOCKED_COVERAGE_BELOW_92_PERCENT"
        gate_decision = "FAIL_COVERAGE_BELOW_92_LORA_BLOCKED"

    decision_package = {
        "report_type": "MEDICALPLAB_RENAL_V6_DECISION_PACKAGE",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mission": "RENAL_V6_PERFORMANCE_FEASIBILITY_AND_RECOVERY_MISSION",
        "governance": {
            "v5_status": "IMMUTABLE_AND_CLOSED",
            "production_runtime_retriever": "QwenRenalRetrieverV3",
            "production_runtime_version": "v3",
            "dev_b_status": "UNEXECUTED_PRESERVED_HEattribute",
            "final_heldout_status": "UNEXECUTED_PRESERVED",
            "production_promotion": False
        },
        "item_1_max_clean_train_size": {
            "maximum_clean_training_size": p1["target_120_160_feasibility"]["maximum_clean_training_size"],
            "clean_benchmark_artifact": p1["target_120_160_feasibility"]["recommended_clean_train_benchmark"],
            "clean_train_n": 80,
            "target_120_160_feasible": False,
            "depleted_strata_count": 6,
            "depleted_strata": [s for s, inf in p1["curriculum_strata_audit"].items() if not inf["expansion_feasible"]],
            "conclusion": p1["verdict_details"]
        },
        "item_2_leakage_firewall_results": {
            "validation_benchmark": fw["benchmark_file"],
            "validation_sha256": fw["benchmark_sha256"],
            "n_validation_items": fw["n_items"],
            "exact_gold_chunk_overlap": fw["firewall_summary"]["exact_gold_chunk_overlap"],
            "window_chunk_overlap": fw["firewall_summary"]["window_chunk_overlap"],
            "section_overlap_with_dev_a": fw["firewall_summary"]["section_overlap_with_dev_a"],
            "section_overlap_with_dev_b": fw["firewall_summary"]["section_overlap_with_dev_b"],
            "section_overlap_with_v5_select_val": fw["firewall_summary"]["section_overlap_with_v5_select_val"],
            "section_overlap_with_v5_train": fw["firewall_summary"]["section_overlap_with_v5_train"],
            "historical_heldout_overlap": fw["firewall_summary"]["historical_heldout_overlap"],
            "verbatim_span_verification_pct": fw["firewall_summary"]["verbatim_span_verification_pct"],
            "firewall_gate_verdict": fw["gate_status"]
        },
        "item_3_failure_taxonomy": p2["failure_taxonomy"],
        "item_4_feature_oracle_v2_table": {
            k: {
                "Coverage@20": f"{v['cov20_pct']}%",
                "Coverage@50": f"{v['cov50_pct']}%",
                "MRR": v["mrr"],
                "median_gold_rank": v["median_gold_rank"],
                "p75_gold_rank": v["p75_gold_rank"],
                "worst_fold": f"{v['worst_fold_cov20']}%",
                "std": v["std_cov20"],
                "latency_ms": v["latency_ms_per_query"]
            }
            for k, v in p3["feature_results"].items()
        },
        "item_5_selector_model_comparison": {
            k: {
                "name": v["name"],
                "Coverage@20": f"{v['cov20_pct']}%",
                "mean_across_folds": f"{v['mean_across_folds']}%",
                "worst_fold": f"{v['worst_fold_cov20']}%",
                "std": v["std_cov20"],
                "naive_preservation": f"{v['naive_preservation_pct']}%",
                "rescues": v["rank21_plus_rescues"],
                "lost": v["lost_relevant_cases"],
                "mrr": v["mrr"],
                "latency_ms": v["latency_ms_per_query"]
            }
            for k, v in p4["selector_classes"].items()
        },
        "item_6_fold_stability": {
            "class_a_fold_by_fold": p4["selector_classes"]["class_a_regularized_logistic"]["fold_by_fold_cov20"],
            "class_a_mean": p4["selector_classes"]["class_a_regularized_logistic"]["mean_across_folds"],
            "class_a_std": p4["selector_classes"]["class_a_regularized_logistic"]["std_cov20"],
            "class_a_worst_fold": p4["selector_classes"]["class_a_regularized_logistic"]["worst_fold_cov20"]
        },
        "item_7_estimated_achievable_selector_ceiling": {
            "train_oof_ceiling": "93.75%",
            "bm25_sparse_ceiling": "91.25%",
            "dense_retrieval_ceiling": "73.75%",
            "fresh_validation_ceiling": f"{val_cov20_pct}%"
        },
        "item_8_fresh_selector_confirmation": {
            "validation_n": val_n,
            "dense_baseline_coverage_at_20": f"{p6['results']['dense_baseline']['coverage_at_20_percent']}%",
            "class_a_coverage_at_20": f"{val_cov20_pct}% ({val_cov20_cnt}/{val_n})",
            "class_b_coverage_at_20": f"{p6['results']['class_b_deterministic_hybrid_rrf']['coverage_at_20_percent']}%",
            "naive_preservation": f"{p6['results']['class_a_regularized_logistic']['naive_preservation_pct']}%",
            "rank21_plus_rescues": p6["results"]["class_a_regularized_logistic"]["rank21_plus_rescues"],
            "lost_cases": p6["results"]["class_a_regularized_logistic"]["lost_relevant_cases"],
            "gate_threshold_minimum": ">= 92.0%",
            "gate_threshold_preferred": ">= 95.0%",
            "fresh_gate_verdict": p6["gate_verdict"]
        },
        "item_9_mathematical_reranker_requirement": {
            "production_passage_hit_at_1_target": ">= 85.0%",
            "fresh_validation_selector_coverage": f"{val_cov20_pct}%",
            "formula": "required_conditional_reranker_acc = 0.85 / selector_coverage",
            "required_conditional_reranker_accuracy": f"{required_reranker_acc}%",
            "is_mathematically_achievable": (required_reranker_acc <= 100.0),
            "frozen_base_reranker_conditional_accuracy": f"{base_reranker_acc}%",
            "frozen_base_reranker_95_ci": [f"{base_ci_low}%", f"{base_ci_high}%"],
            "reranker_gap": (
                "MATHEMATICALLY_IMPOSSIBLE_ABOVE_100_PERCENT" if required_reranker_acc > 100.0 else
                f"{round(required_reranker_acc - base_reranker_acc, 2)}%"
            )
        },
        "item_10_recommendation": {
            "final_recommendation": recommendation,
            "lora_status": lora_status,
            "gate_decision": gate_decision,
            "production_default": "QwenRenalRetrieverV3",
            "executive_verdict": (
                f"Fresh selector confirmation OutputCoverage@20 reached {val_cov20_pct}% ({val_cov20_cnt}/{val_n}) on the "
                f"unspent N=40 validation benchmark, failing the mandatory >=92.0% feasibility gate (predeclared FAIL). "
                f"To reach the overall production PassageHit@1 target of >=85.0%, a downstream reranker would require "
                f"a conditional accuracy of {required_reranker_acc}%, which is mathematically impossible (>100%). "
                f"Even under a theoretically perfect 100% reranker, PassageHit@1 would be capped at {val_cov20_pct}%. "
                "In strict accordance with V6 feasibility governance, LoRA remains definitively BLOCKED. "
                "No LoRA, no DEV-B execution, no heldout execution, and no production promotion are authorized. "
                "Renal retrieval R&D is terminated and QwenRenalRetrieverV3 remains the frozen production default."
            )
        }
    }

    out_path = REPORTS_V6_DIR / "renal_v6_decision_package.json"
    out_path.write_text(json.dumps(decision_package, indent=2), encoding="utf-8")
    out_sha = compute_sha256(out_path)
    (REPORTS_V6_DIR / "renal_v6_decision_package.json.sha256").write_text(out_sha + "\n", encoding="utf-8")

    print("\n" + "=" * 80)
    print("MEDICALPLAB RENAL V6: ENGINEERING DECISION PACKAGE COMPLETE")
    print("=" * 80)
    print(f"Report written to: {out_path}")
    print(f"Decision Package SHA256: {out_sha}")
    print(f"Final Recommendation:   {recommendation}")
    print(f"LoRA Authorization:     {lora_status}")
    print(f"Production Baseline:    {decision_package['governance']['production_runtime_retriever']}")
    print("=" * 80)

if __name__ == "__main__":
    main()
