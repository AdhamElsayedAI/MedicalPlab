"""Explicit denominators; failures stay in end-to-end metrics."""

from collections import Counter, defaultdict
from itertools import combinations
import math

LABELS = ["unsupported", "partial", "supported"]


def fraction(k, n):
    result = {"count": k, "denominator": n, "rate": k / n if n else None}
    if n:
        z = 1.959963984540054
        p = k / n
        center = (p + z * z / (2 * n)) / (1 + z * z / n)
        width = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
        result["wilson95"] = [max(0, center - width), min(1, center + width)]
    else:
        result["wilson95"] = None
    return result


def core(rows):
    valid = [r for r in rows if r["status"] == "ok"]
    confusion = {a: {b: 0 for b in LABELS} for a in LABELS}
    for r in valid:
        confusion[r["gold_label"]][r["prediction"]] += 1
    per_class = {}
    for label in LABELS:
        tp = confusion[label][label]
        actual = sum(confusion[label].values())
        pred = sum(confusion[a][label] for a in LABELS)
        per_class[label] = {
            "precision": fraction(tp, pred),
            "recall": fraction(tp, actual),
            "f1": 2 * tp / (actual + pred) if actual + pred else 0,
        }
    supported = sum(r["gold_label"] == "supported" for r in valid)
    accepts = sum(r["prediction"] == "supported" for r in valid)
    tp = confusion["supported"]["supported"]
    correct = sum(confusion[a][a] for a in LABELS)
    statuses = Counter(r["status"] for r in rows)
    return {
        "total_cases": len(rows),
        "valid_predictions": len(valid),
        "contract_failures": statuses["contract_failure"],
        "model_failures": statuses["model_failure"],
        "contract_pass": fraction(len(valid), len(rows)),
        "strict_end_to_end_correctness": fraction(correct, len(rows)),
        "three_way_accuracy": fraction(correct, len(valid)),
        "macro_f1": sum(p["f1"] for p in per_class.values()) / 3 if valid else None,
        "per_class": per_class,
        "confusion_matrix": confusion,
        "unsafe_accept": fraction(accepts - tp, len(valid) - supported),
        "false_refusal": fraction(supported - tp, supported),
        "supported_accept_precision": fraction(tp, accepts),
        "supported_recall": fraction(tp, supported),
        "coverage": fraction(accepts, len(valid)),
        "end_to_end_coverage": fraction(accepts, len(rows)),
        "end_to_end_supported_recall": fraction(
            tp, sum(r["gold_label"] == "supported" for r in rows)
        ),
        "policy_downgrade_cases": sum(
            bool(r.get("result", {}).get("policy_downgrades")) for r in rows
        ),
    }


def metrics(rows):
    out = core(rows)
    out["denominators"] = (
        "Classification and safety rates use valid predictions; failures remain in strict end-to-end metrics. False refusal includes partial on supported gold."
    )
    for field in ["language", "claim_type", "negative_type"]:
        groups = defaultdict(list)
        for row in rows:
            groups[str(row[field])].append(row)
        out[field] = {k: core(v) for k, v in sorted(groups.items())}
    groups = defaultdict(list)
    for r in rows:
        if r.get("contrast_group_id"):
            groups[r["contrast_group_id"]].append(r)
    out["contrastive_group_exact"] = fraction(
        sum(
            all(r["status"] == "ok" and r["prediction"] == r["gold_label"] for r in g)
            for g in groups.values()
        ),
        len(groups),
    )
    pairs = [
        (a, b)
        for g in groups.values()
        for a, b in combinations(g, 2)
        if a["gold_label"] != b["gold_label"] and a["status"] == b["status"] == "ok"
    ]
    rank = {v: i for i, v in enumerate(LABELS)}
    out["pairwise_reversals"] = fraction(
        sum(
            (rank[a["gold_label"]] - rank[b["gold_label"]])
            * (rank[a["prediction"]] - rank[b["prediction"]])
            < 0
            for a, b in pairs
        ),
        len(pairs),
    )
    out["pairwise_ties"] = sum(a["prediction"] == b["prediction"] for a, b in pairs)
    times = sorted(r["latency_seconds"] for r in rows)
    out["latency"] = {
        "total_seconds": sum(times),
        "mean_seconds": sum(times) / len(times) if times else None,
        "p95_seconds": times[math.ceil(0.95 * len(times)) - 1] if times else None,
    }
    out["tokens"] = {
        key: sum(
            t.get("raw", {}).get(key, 0)
            for r in rows
            for t in r.get("trace", [])
        )
        for key in ["input_tokens", "output_tokens"]
    }
    out["failure_taxonomy"] = dict(
        Counter(r.get("error_type", "unknown") for r in rows if r["status"] != "ok")
    )
    out["unsafe_accept_case_ids"] = [
        r["case_id"]
        for r in rows
        if r["status"] == "ok"
        and r["prediction"] == "supported"
        and r["gold_label"] != "supported"
    ]
    return out
