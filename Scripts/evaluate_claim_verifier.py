"""
MedicalPlab Shared Evidence Engine V2 — Stage-B Semantic Claim-Verifier Evaluation
==================================================================================
Evaluates CentralClaimVerifier on the frozen claim_verifier_benchmark.json (N=60).
Computes:
- Per-class precision, recall, and F1
- Macro-F1 across the 4 discrete classes
- SUPPORTED precision
- CONTRADICTED recall
- False-support rate (predicting SUPPORTED/PARTIALLY_SUPPORTED when ground truth is CONTRADICTED/NOT_SUPPORTED)
- False-rejection rate (predicting NOT_SUPPORTED/CONTRADICTED when ground truth is SUPPORTED)
- Calibration & confidence behavior
- High-risk failure-closed adherence
- 95% Wilson confidence intervals
"""

import hashlib
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from medicalplab.evidence_engine.claim_verifier import CentralClaimVerifier
from medicalplab.evidence_engine.models import VerificationState

BENCHMARK_PATH = _ROOT / "evaluation" / "evidence_engine" / "claim_verifier_benchmark.json"
REPORT_PATH = _ROOT / "reports" / "evidence_engine" / "claim_verifier_evaluation_report.json"
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def wilson_score_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1 + (z**2) / total
    center = (p + (z**2) / (2 * total)) / denom
    spread = (z * math.sqrt((p * (1 - p) / total) + (z**2) / (4 * (total**2)))) / denom
    return max(0.0, center - spread), min(1.0, center + spread)


def make_stat(count: int, n: int) -> dict[str, Any]:
    low, high = wilson_score_interval(count, n)
    return {
        "count": count,
        "total": n,
        "rate": round(count / n, 4) if n > 0 else 0.0,
        "pct": f"{(count / n) * 100:.2f}%" if n > 0 else "0.0%",
        "ci_95_wilson": [round(low, 4), round(high, 4)],
    }


def main():
    print("=" * 70)
    print("STAGE-B CENTRAL CLAIM-VERIFIER EVALUATION")
    print("=" * 70)

    bench_bytes = BENCHMARK_PATH.read_bytes()
    bench_sha = hashlib.sha256(bench_bytes).hexdigest()
    items = json.loads(bench_bytes)
    n = len(items)
    print(f"Loaded {n} items from {BENCHMARK_PATH.name} (SHA-256: {bench_sha[:16]}...)")

    verifier = CentralClaimVerifier()

    classes = [
        VerificationState.SUPPORTED.value,
        VerificationState.PARTIALLY_SUPPORTED.value,
        VerificationState.CONTRADICTED.value,
        VerificationState.NOT_SUPPORTED.value,
    ]

    # Confusion matrix: conf_matrix[true_label][pred_label]
    conf_matrix = {t: {p: 0 for p in classes} for t in classes}
    per_item_records = []

    t0 = time.perf_counter()
    for it in items:
        cid = it["claim_id"]
        c_text = it["claim"]
        premise = it["premise"]
        true_lbl = it["label"]
        doc_id = it.get("source_document")
        sec = it.get("section")

        res = verifier.verify_claim(
            claim_id=cid,
            claim_text=c_text,
            evidence_text=premise,
            cited_document_id=doc_id,
            cited_section=sec,
        )

        pred_lbl = res.state.value
        conf_matrix[true_lbl][pred_lbl] += 1

        per_item_records.append({
            "claim_id": cid,
            "true_label": true_lbl,
            "predicted_label": pred_lbl,
            "confidence": res.confidence,
            "is_high_risk": res.is_high_risk,
            "veto_flags": res.veto_flags,
            "rationale": res.rationale,
            "hard_case_category": it.get("hard_case_category"),
        })

    elapsed = time.perf_counter() - t0

    # Metrics computation
    per_class_metrics = {}
    f1_list = []

    for cls in classes:
        tp = conf_matrix[cls][cls]
        fp = sum(conf_matrix[other][cls] for other in classes if other != cls)
        fn = sum(conf_matrix[cls][other] for other in classes if other != cls)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        f1_list.append(f1)

        per_class_metrics[cls] = {
            "true_count": tp + fn,
            "predicted_count": tp + fp,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": make_stat(tp, tp + fp),
            "recall": make_stat(tp, tp + fn),
            "f1": round(f1, 4),
        }

    macro_f1 = round(sum(f1_list) / len(f1_list), 4)

    # False support: ground truth is CONTRADICTED or NOT_SUPPORTED, but predicted SUPPORTED or PARTIALLY_SUPPORTED
    unsupported_true = [it for it in per_item_records if it["true_label"] in ["CONTRADICTED", "NOT_SUPPORTED"]]
    false_support_count = sum(
        1 for it in unsupported_true if it["predicted_label"] in ["SUPPORTED", "PARTIALLY_SUPPORTED"]
    )
    false_support_stat = make_stat(false_support_count, len(unsupported_true))

    # False rejection: ground truth is SUPPORTED, but predicted NOT_SUPPORTED or CONTRADICTED
    supported_true = [it for it in per_item_records if it["true_label"] == "SUPPORTED"]
    false_rejection_count = sum(
        1 for it in supported_true if it["predicted_label"] in ["NOT_SUPPORTED", "CONTRADICTED"]
    )
    false_rejection_stat = make_stat(false_rejection_count, len(supported_true))

    # High-risk safety check
    high_risk_records = [it for it in per_item_records if it["is_high_risk"]]
    high_risk_unsupported = [it for it in high_risk_records if it["true_label"] in ["CONTRADICTED", "NOT_SUPPORTED"]]
    high_risk_false_support = sum(
        1 for it in high_risk_unsupported if it["predicted_label"] in ["SUPPORTED", "PARTIALLY_SUPPORTED"]
    )

    report = {
        "verifier_name": "CentralClaimVerifier",
        "benchmark_file": str(BENCHMARK_PATH.relative_to(_ROOT)),
        "benchmark_sha256": bench_sha,
        "n_items": n,
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_elapsed_seconds": round(elapsed, 4),
        "confusion_matrix": conf_matrix,
        "macro_f1": macro_f1,
        "per_class_metrics": per_class_metrics,
        "safety_metrics": {
            "supported_precision": per_class_metrics["SUPPORTED"]["precision"],
            "contradicted_recall": per_class_metrics["CONTRADICTED"]["recall"],
            "false_support_rate": false_support_stat,
            "false_rejection_rate": false_rejection_stat,
            "high_risk_total": len(high_risk_records),
            "high_risk_unsupported_total": len(high_risk_unsupported),
            "high_risk_false_support_count": high_risk_false_support,
            "high_risk_unsafe_rate": make_stat(high_risk_false_support, len(high_risk_unsupported)),
        },
        "per_item_records": per_item_records,
    }

    out_bytes = json.dumps(report, indent=2).encode("utf-8")
    REPORT_PATH.write_bytes(out_bytes)
    sha_rep = hashlib.sha256(out_bytes).hexdigest()
    (REPORT_PATH.with_suffix(".json.sha256")).write_text(f"{sha_rep}  {REPORT_PATH.name}\n", encoding="utf-8")

    print("\n" + "=" * 70)
    print("RESULTS: STAGE-B CLAIM-VERIFIER ON BENCHMARK")
    print("=" * 70)
    print(f"Macro-F1: {macro_f1:.4f}")
    for cls in classes:
        p_pct = per_class_metrics[cls]["precision"]["pct"]
        r_pct = per_class_metrics[cls]["recall"]["pct"]
        f1_val = per_class_metrics[cls]["f1"]
        print(f"  {cls:20s}: Precision={p_pct:8s} | Recall={r_pct:8s} | F1={f1_val:.4f}")

    print(f"\nFalse Support Rate (unsafe): {false_support_stat['pct']} ({false_support_stat['count']}/{false_support_stat['total']}) [95% CI: {false_support_stat['ci_95_wilson']}]")
    print(f"False Rejection Rate       : {false_rejection_stat['pct']} ({false_rejection_stat['count']}/{false_rejection_stat['total']}) [95% CI: {false_rejection_stat['ci_95_wilson']}]")
    print(f"High-Risk Unsafe Support   : {high_risk_false_support}/{len(high_risk_unsupported)}")
    print(f"\nSaved report to {REPORT_PATH.name} (SHA-256: {sha_rep})")


if __name__ == "__main__":
    main()
