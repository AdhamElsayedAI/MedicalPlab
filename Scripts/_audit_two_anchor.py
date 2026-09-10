"""Phase 3 — Two-anchor rule audit on DEV dataset (NO GPU required).

Examines each answerable query's gold_verification_anchors vs
gold_matched_anchors vs gold_evidence_quote to determine whether
the two-anchor filtering rule is producing false negatives or
false positives.

Uses DEV only — never inspects heldout.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEV_PATH = ROOT / "evaluation" / "renal" / "renal-dev-v2.json"
CAL_PATH = ROOT / "evaluation" / "renal" / "renal-calibration-v2.json"
OUT_PATH = ROOT / "reports" / "renal_v2_gold_audit.json"


def audit_dataset(path: Path, dataset_name: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    queries = data.get("queries", [])
    answerable = [q for q in queries if q.get("answerable")]
    print(f"\n{'='*60}")
    print(f"TWO-ANCHOR AUDIT: {dataset_name}  N={len(queries)}  Answerable={len(answerable)}")
    print(f"{'='*60}")

    audit_items = []
    category_counts: Counter = Counter()

    for q in answerable:
        qid = q.get("query_id", "?")
        anchors = q.get("gold_verification_anchors", [])
        matched = q.get("gold_matched_anchors", [])
        quote = q.get("gold_evidence_quote", "")
        min_hits = q.get("gold_minimum_anchor_hits", 2)
        topic = q.get("topic", "?")

        quote_lower = quote.lower()

        # Which declared anchors are actually in the quote?
        anchors_in_quote = [a for a in anchors if a.lower() in quote_lower]
        anchors_not_in_quote = [a for a in anchors if a.lower() not in quote_lower]

        # Which matched anchors are actually in the quote?
        matched_in_quote = [a for a in matched if a.lower() in quote_lower]
        matched_not_in_quote = [a for a in matched if a.lower() not in quote_lower]

        n_matched = len(matched)

        # Classification
        if n_matched >= min_hits:
            if len(matched_not_in_quote) == 0:
                # All matched anchors verifiably in quote text
                category = "CORRECT_SUPPORTED"
            else:
                # Some matched anchors NOT verifiably in quote text
                # Could be: anchor matched in passage not shown in quote,
                # or anchor was matched against incorrect text
                category = "ANCHOR_MATCH_OUTSIDE_QUOTE"
        else:
            # Fewer than min_hits anchors matched
            # Were there anchors in quote that could have matched?
            potential_unmatched = [a for a in anchors_in_quote if a not in matched]
            if len(potential_unmatched) > 0:
                # Quote DOES contain anchors that were not counted as matched
                # Likely false negative in the matching logic
                category = "ANCHOR_FALSE_NEGATIVE"
            else:
                # Quote genuinely doesn't contain enough anchor terms
                # Two-anchor rule correctly flagged this as insufficient
                category = "CORRECT_UNSUPPORTED_OR_PARTIAL"

        category_counts[category] += 1

        item = {
            "query_id": qid,
            "topic": topic,
            "query": q.get("query", ""),
            "gold_document_ids": q.get("gold_document_ids", []),
            "n_anchors": len(anchors),
            "n_matched": n_matched,
            "min_hits": min_hits,
            "anchors": anchors,
            "matched": matched,
            "anchors_in_quote": anchors_in_quote,
            "anchors_not_in_quote": anchors_not_in_quote,
            "matched_in_quote": matched_in_quote,
            "matched_not_in_quote": matched_not_in_quote,
            "category": category,
        }
        audit_items.append(item)

    n = len(answerable)
    print(f"\nCategories (N={n}):")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        pct = 100.0 * count / n if n else 0
        print(f"  {cat:<45} {count:>4} / {n} = {pct:.1f}%")

    # False negative rate
    fn = category_counts.get("ANCHOR_FALSE_NEGATIVE", 0)
    fp = category_counts.get("ANCHOR_MATCH_OUTSIDE_QUOTE", 0)
    print(f"\nFalse Negative Rate (missed valid items): {fn}/{n} = {100*fn/n:.1f}%")
    print(f"Potential False Positive Rate (matched outside quote): {fp}/{n} = {100*fp/n:.1f}%")

    # Print problematic cases
    problems = [item for item in audit_items if item["category"] not in (
        "CORRECT_SUPPORTED", "CORRECT_UNSUPPORTED_OR_PARTIAL"
    )]
    if problems:
        print(f"\nPROBLEMATIC CASES ({len(problems)}):")
        for item in problems[:15]:
            print(f"  [{item['category']}] {item['query_id']}: {item['query'][:70]}")
            print(f"    topic={item['topic']}  n_anchors={item['n_anchors']}  n_matched={item['n_matched']}")
            if item["anchors_not_in_quote"]:
                print(f"    anchors_not_in_quote: {item['anchors_not_in_quote']}")
            if item["matched_not_in_quote"]:
                print(f"    matched_not_in_quote: {item['matched_not_in_quote']}")
            print()
    else:
        print("\nNo problematic cases found — two-anchor rule appears sound for this dataset.")

    return {
        "dataset": dataset_name,
        "n_queries": len(queries),
        "n_answerable": n,
        "category_counts": dict(category_counts),
        "false_negative_count": fn,
        "false_negative_rate": fn / n if n else 0,
        "false_positive_count": fp,
        "false_positive_rate": fp / n if n else 0,
        "items": audit_items,
    }


def main() -> None:
    results = {}
    results["dev"] = audit_dataset(DEV_PATH, "RENAL-DEV-v2")

    # Also audit calibration dataset for supported items
    cal_data = json.loads(CAL_PATH.read_text(encoding="utf-8"))
    cal_queries = cal_data.get("queries", [])
    cal_answerable = [q for q in cal_queries if q.get("answerable")]
    print(f"\n{'='*60}")
    print(f"CALIBRATION SUPPORTED ITEMS: {len(cal_answerable)} / {len(cal_queries)}")
    print(f"{'='*60}")
    cal_support_labels = Counter(q.get("support_label") for q in cal_queries)
    print("Support labels:", dict(cal_support_labels))
    results["calibration_label_summary"] = dict(cal_support_labels)

    # Check calibration anchors similarly
    cal_with_anchors = [q for q in cal_answerable if q.get("gold_verification_anchors")]
    print(f"Calibration answerable with anchors: {len(cal_with_anchors)}")
    if cal_answerable:
        results["calibration"] = audit_dataset(CAL_PATH, "RENAL-CALIBRATION-v2")

    # Write report
    report = {
        "report_id": "RENAL-V2-GOLD-AUDIT",
        "dev": results.get("dev", {}),
        "calibration": results.get("calibration", {}),
        "calibration_label_summary": results.get("calibration_label_summary", {}),
    }
    # Remove verbose item lists from top-level report to keep size manageable
    summary = {
        "report_id": report["report_id"],
        "dev": {k: v for k, v in report["dev"].items() if k != "items"},
        "calibration": {k: v for k, v in report.get("calibration", {}).items() if k != "items"},
        "calibration_label_summary": report["calibration_label_summary"],
        "dev_items": report["dev"].get("items", []),
        "calibration_items": report.get("calibration", {}).get("items", []),
    }
    OUT_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nAudit written to: {OUT_PATH}")


if __name__ == "__main__":
    main()
