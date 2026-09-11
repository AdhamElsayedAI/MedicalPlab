import json
from pathlib import Path

report_path = Path("reports/renal_v7/renal_v7_answerability_safety_report.json")
report = json.loads(report_path.read_text(encoding="utf-8"))

sup_scores = [q["top_rerank_score"] for q in report["query_evaluations"] if q["expected"] == "supported"]
uns_scores = [q["top_rerank_score"] for q in report["query_evaluations"] if q["expected"] == "unsupported"]

sup_sorted = sorted(sup_scores)
uns_sorted = sorted(uns_scores)

print(f"Supported N={len(sup_scores)}: min={min(sup_scores)}, median={sup_sorted[len(sup_sorted)//2]}, max={max(sup_scores)}")
print(f"Unsupported N={len(uns_scores)}: min={min(uns_scores)}, median={uns_sorted[len(uns_sorted)//2]}, max={max(uns_scores)}")

print("\n--- Sweeping Tau from 0.0 to 9.0 ---")
for t in [i * 0.5 for i in range(0, 19)]:
    tp = sum(1 for s in sup_scores if s >= t)
    fp = sum(1 for s in uns_scores if s >= t)
    fn = sum(1 for s in sup_scores if s < t)
    tn = sum(1 for s in uns_scores if s < t)
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / len(sup_scores)
    unsafe = fp / len(uns_scores)
    print(f"Tau {t:4.1f} | Prec: {prec:.4f} | Rec: {rec:.4f} | Unsafe: {unsafe:.4f} (FP={fp}, TP={tp})")
