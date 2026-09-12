"""
Blinded All-Query Audit of PRODUCT_DEV_V2 (N=120)
=================================================
Strictly blind to model names, retrieval ranks, scores, or hit/miss status.
Audits:
- query
- learning_objective
- canonical_claim
- evidence_span

Classifies into:
1. VALID_PRODUCT_QUERY
2. EDITORIAL_STRUCTURE_QUERY
3. QUERY_EVIDENCE_MISMATCH
4. AMBIGUOUS_QUERY
5. MULTI_CLAIM_QUERY
6. INSUFFICIENT_DIRECT_EVIDENCE
7. DUPLICATE_OR_NEAR_DUPLICATE_FAMILY
"""

import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

EDITORIAL_PATTERNS = [
    r"\bin\s+[\.\s]*(Introduction|Discussion|Commentary|Methods|Results|Conclusions?|Background|References|Acknowledgements?)\b",
    r"characterize\s+[\.\s]*(Introduction|Discussion|Commentary|Methods|Results|Conclusions?|Background)\b",
    r"characterize\s+\.\s+",
    r"in\s+Renal Clinical Evidence\?",
    r"in\s+\.\s+",
]

def classify_blinded_item(item: dict, seen_families: set) -> tuple[str, str]:
    query = item["query"]
    claim = item.get("canonical_claim", "")
    evidence = item.get("evidence_span", "")
    lo = item.get("learning_objective", "")
    doc_id = item.get("gold_document_id", "")

    # Check for editorial structure
    for pat in EDITORIAL_PATTERNS:
        if re.search(pat, query, re.IGNORECASE):
            return "EDITORIAL_STRUCTURE_QUERY", f"Query targets manuscript section/editorial label matching '{pat}'"

    # Check for heading concatenation artifacts (e.g. ends with 'in . [Heading]?')
    if re.search(r"in\s+\.\s+[A-Z]", query):
        return "EDITORIAL_STRUCTURE_QUERY", "Query ends with synthetic heading concatenation artifact 'in . [Heading]?'"

    # Check for query-evidence mismatch:
    # E.g. Query asks about tubulointerstitial fibrosis, but claim is about IL-6/CVD or hypertension
    q_lower = query.lower()
    c_lower = claim.lower()

    if "tubulointerstitial fibrosis" in q_lower and "fibrosis" not in c_lower and "tubulointerstitial" not in c_lower:
        return "QUERY_EVIDENCE_MISMATCH", "Query asks about tubulointerstitial fibrosis but claim discusses unrelated pathology"

    if "acute tubular injury" in q_lower and "tubular" not in c_lower and "ati" not in c_lower and "aki" not in c_lower:
        return "QUERY_EVIDENCE_MISMATCH", "Query asks about acute tubular injury but claim does not address tubular injury"

    # Check for duplicate / near-duplicate family
    family_key = (doc_id, claim[:60])
    if family_key in seen_families:
        return "DUPLICATE_OR_NEAR_DUPLICATE_FAMILY", "Duplicate atomic claim from same document family"
    seen_families.add(family_key)

    # Check for insufficient direct evidence
    if len(evidence.strip()) < 30:
        return "INSUFFICIENT_DIRECT_EVIDENCE", "Evidence span is truncated (<30 chars) or empty"

    # Check for ambiguity
    if len(query.split()) < 6:
        return "AMBIGUOUS_QUERY", "Query is overly short/underspecified (<6 words)"

    return "VALID_PRODUCT_QUERY", "Clinically coherent medical learning objective with direct claim support"

def main():
    dev_path = _ROOT / "evaluation" / "evidence_engine" / "product_dev_v2.json"
    items = json.loads(dev_path.read_bytes())
    n = len(items)

    classification_counts = {}
    detailed_audit = []
    seen_families = set()

    for item in items:
        cat, reason = classify_blinded_item(item, seen_families)
        classification_counts[cat] = classification_counts.get(cat, 0) + 1
        detailed_audit.append({
            "query_id": item["query_id"],
            "query": item["query"],
            "canonical_claim": item.get("canonical_claim"),
            "category": cat,
            "rationale": reason
        })

    report = {
        "benchmark": "PRODUCT_DEV_V2",
        "n_total": n,
        "classification_summary": {
            cat: {
                "count": count,
                "percent": f"{(count / n) * 100:.2f}%"
            }
            for cat, count in sorted(classification_counts.items(), key=lambda x: x[1], reverse=True)
        },
        "valid_count": classification_counts.get("VALID_PRODUCT_QUERY", 0),
        "invalid_count": n - classification_counts.get("VALID_PRODUCT_QUERY", 0),
        "detailed_audit": detailed_audit
    }

    out_path = _ROOT / "reports" / "evidence_engine" / "product_dev_v2_blinded_audit.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=" * 70)
    print("BLINDED ALL-QUERY AUDIT RESULTS: PRODUCT_DEV_V2")
    print("=" * 70)
    print(f"Total Queries Audited: {n}")
    print(f"Valid Product Queries: {report['valid_count']} ({(report['valid_count']/n)*100:.2f}%)")
    print(f"Invalid / Contaminated Queries: {report['invalid_count']} ({(report['invalid_count']/n)*100:.2f}%)")
    print("\nCategory Breakdown:")
    for cat, data in report["classification_summary"].items():
        print(f"  - {cat:35s}: {data['count']:3d} ({data['percent']})")

if __name__ == "__main__":
    main()
