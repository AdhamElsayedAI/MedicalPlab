"""Evidence Sufficiency Gate Calibration across Retrieval Scores.

Evaluates evidence sufficiency on evaluation/evidence_sufficiency_calibration_v1.json.
Sweeps threshold tau and tracks:
- unsafe acceptance rate (FP / Non-Supported)
- false refusal rate (FN / Supported)
- supported-answer coverage (Accepted / Total Cases)
- precision (TP / (TP + FP))
- recall (TP / (TP + FN))
"""

import json
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CALIB_PATH = PROJECT_ROOT / "evaluation" / "evidence_sufficiency_calibration_v1.json"
BASELINE_PATH = PROJECT_ROOT / "evaluation" / "results" / "evidence_sufficiency_retrieval_only_baseline_v1.json"
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"


def main():
    calib = json.load(open(CALIB_PATH, encoding="utf-8"))
    baseline = json.load(open(BASELINE_PATH, encoding="utf-8"))

    cases = calib["cases"]
    n_total = len(cases)
    
    # In baseline, each case has top1_score recorded
    case_map = {c["case_id"]: c for c in cases}
    case_scores = []
    
    for case_data in baseline["cases"]:
        cid = case_data["case_id"]
        c_orig = case_map[cid]
        label = c_orig["support_label"]  # 'supported', 'partial', 'unsupported'
        is_supported = (label == "supported")
        top1 = case_data["retrieval_features"]["top1_score"]
        case_scores.append((cid, top1, is_supported, label))

    scores = np.array([cs[1] for cs in case_scores])
    labels = np.array([cs[2] for cs in case_scores])
    n_pos = np.sum(labels)
    n_neg = len(labels) - n_pos

    # Threshold sweep from min to max score
    thresholds = np.linspace(scores.min(), scores.max(), 50)
    operating_points = []

    for tau in thresholds:
        accepted = scores >= tau
        tp = np.sum(accepted & labels)
        fp = np.sum(accepted & (~labels))
        tn = np.sum((~accepted) & (~labels))
        fn = np.sum((~accepted) & labels)

        cov = np.sum(accepted) / n_total
        prec = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
        rec = (tp / n_pos) if n_pos > 0 else 0.0
        unsafe_accept_rate = (fp / n_neg) if n_neg > 0 else 0.0
        false_refusal_rate = (fn / n_pos) if n_pos > 0 else 0.0

        operating_points.append({
            "threshold": round(float(tau), 4),
            "coverage": round(float(cov), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "unsafe_accept_rate": round(float(unsafe_accept_rate), 4),
            "false_refusal_rate": round(float(false_refusal_rate), 4),
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
        })

    # Select representative points:
    # 1. Conservative (Zero Unsafe Accept)
    zero_unsafe = [p for p in operating_points if p["unsafe_accept_rate"] == 0.0]
    best_zero_unsafe = max(zero_unsafe, key=lambda x: x["coverage"]) if zero_unsafe else operating_points[-1]

    # 2. Balanced (Recall >= 0.70 while minimizing unsafe accept)
    high_recall = [p for p in operating_points if p["recall"] >= 0.70]
    best_balanced = min(high_recall, key=lambda x: x["unsafe_accept_rate"]) if high_recall else operating_points[0]

    # 3. High-Coverage (Coverage >= 0.60)
    high_cov = [p for p in operating_points if p["coverage"] >= 0.60]
    best_high_cov = min(high_cov, key=lambda x: x["unsafe_accept_rate"]) if high_cov else operating_points[0]

    print("=========================================================================================")
    print("EVIDENCE SUFFICIENCY GATE CALIBRATION")
    print("=========================================================================================")
    print(f"Total Cases: {n_total} (Supported: {n_pos}, Non-Supported: {n_neg})")
    print("\nOperating Point Profiles:")
    print("-" * 88)
    print(f"{'Profile':<24} | {'Tau':<6} | {'Coverage':<8} | {'Precision':<9} | {'Recall':<6} | {'UnsafeAcc':<9} | {'FalseRef':<8}")
    print("-" * 88)
    for name, p in [
        ("Zero-Unsafe (Cautious)", best_zero_unsafe),
        ("Balanced Operating Point", best_balanced),
        ("High-Coverage", best_high_cov),
    ]:
        print(f"{name:<24} | {p['threshold']:<6.3f} | {p['coverage']*100:<7.1f}% | {p['precision']*100:<8.1f}% | {p['recall']*100:<5.1f}% | {p['unsafe_accept_rate']*100:<8.1f}% | {p['false_refusal_rate']*100:<7.1f}%")

    out_payload = {
        "calibration_id": "medicalplab-evidence-sufficiency-calibration-v2",
        "dataset": {
            "cases": n_total,
            "supported": int(n_pos),
            "non_supported": int(n_neg),
        },
        "operating_profiles": {
            "zero_unsafe_cautious": best_zero_unsafe,
            "balanced_operating_point": best_balanced,
            "high_coverage": best_high_cov,
        },
        "all_operating_points": operating_points,
    }

    out_file = RESULTS_DIR / "evidence_sufficiency_calibrated_profiles_v1.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"\nSaved calibration profiles to {out_file}")


if __name__ == "__main__":
    main()
