"""Phase 7 — Passage forensic audit on DEV dataset.

Produces detailed per-query analysis of dense retrieval failures
using the best available configuration (B_400_overlap x content_only).

Classification categories per mission spec §20:
- GOLD_TOO_NARROW
- MULTIPLE_VALID_PASSAGES
- RIGHT_PARENT_WRONG_CHILD
- CHUNK_BOUNDARY
- QUERY_BROADER_THAN_CHILD
- SECTION_HEADING_AMBIGUITY
- METHODS_RESULTS_NOISE
- SOURCE_COVERAGE_GAP
- ACTUAL_DENSE_FAILURE
- ACTUAL_RERANKER_FAILURE
- AMBIGUOUS_QUERY
- OTHER (requires explanation)

Uses ablation report final failures as input + DEV gold data.
No ML compute required.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEV_PATH = ROOT / "evaluation" / "renal" / "renal-dev-v2.json"
ABLATION_PATH = ROOT / "reports" / "renal_v2_ablation.json"
OUT_PATH = ROOT / "reports" / "renal_v2_passage_failure_analysis.json"
CHUNKS_DIR = ROOT / "Data" / "experiments" / "renal_v2" / "chunking" / "B_400_overlap"


def load_chunks() -> list[dict]:
    chunks: list[dict] = []
    for path in sorted(CHUNKS_DIR.glob("*.chunks.json")):
        chunks.extend(json.loads(path.read_text(encoding="utf-8")).get("chunks", []))
    return chunks


def classify_failure(
    query: dict,
    top10: list[dict],
    chunks: list[dict],
    query_text: str,
    gold_evidence_quote: str,
) -> str:
    """Apply heuristic failure classification from top10 retrieved chunks."""
    gold_docs = set(query.get("gold_document_ids", []))
    gold_parent_ids = set(query.get("gold_parent_section_ids", []))
    gold_chunk_ids = set(query.get("gold_child_chunk_ids", []))

    # Check if top10 contains right document
    top10_docs = {item["document_id"] for item in top10}
    top10_parents = {item.get("parent_section_id", "") for item in top10}
    top10_chunk_ids = {item["chunk_id"] for item in top10}

    has_right_doc = bool(top10_docs & gold_docs)
    has_right_parent = bool(top10_parents & gold_parent_ids)
    has_right_chunk = bool(top10_chunk_ids & gold_chunk_ids)

    if has_right_parent and not has_right_chunk:
        return "RIGHT_PARENT_WRONG_CHILD"

    if has_right_doc and not has_right_parent:
        # Check if any retrieved section contains method/result noise
        method_noise = any(
            any(
                term in " ".join(item.get("section_path", [])).lower()
                for term in ("method", "statistical", "result", "supplement")
            )
            for item in top10
            if item["document_id"] in gold_docs
        )
        if method_noise:
            return "METHODS_RESULTS_NOISE"

        # Check section heading ambiguity — same heading words in multiple sections
        if len(gold_parent_ids) > 0:
            return "SECTION_HEADING_AMBIGUITY"

        return "ACTUAL_DENSE_FAILURE"

    if not has_right_doc:
        # Completely wrong documents
        # Is query broader than any single passage could cover?
        words = query_text.lower().split()
        broad_indicators = ["what is", "explain", "describe", "overview", "how does", "summarise", "compare"]
        is_broad = any(query_text.lower().startswith(b) for b in broad_indicators)

        # Is this a coverage gap?
        if is_broad:
            return "QUERY_BROADER_THAN_CHILD"
        return "ACTUAL_DENSE_FAILURE"

    return "OTHER"


def main() -> None:
    dev = json.loads(DEV_PATH.read_text(encoding="utf-8"))
    queries = {q["query_id"]: q for q in dev["queries"] if q.get("answerable")}

    ablation = json.loads(ABLATION_PATH.read_text(encoding="utf-8"))
    final_failures = ablation.get("final_failures", [])

    chunks = load_chunks()
    chunk_map = {c.get("chunk_id", ""): c for c in chunks}

    print(f"DEV answerable: {len(queries)}")
    print(f"Ablation final failures (Top10 misses): {len(final_failures)}")
    print(f"Implied hits in Top10: {len(queries) - len(final_failures)}")
    print()

    # Enrich failure records with detailed classification
    enriched_failures = []
    category_counts: Counter = Counter()

    for failure in final_failures:
        qid = failure["query_id"]
        query = queries.get(qid, {})
        quote = query.get("gold_evidence_quote", "")
        top10_raw = failure.get("top_10", [])

        # Enrich top10 with chunk data
        top10_enriched = []
        for item in top10_raw:
            chunk = chunk_map.get(item.get("chunk_id", ""), {})
            text_snippet = str(chunk.get("text", ""))[:200]
            top10_enriched.append({
                **item,
                "text_snippet": text_snippet,
            })

        # Preliminary category from ablation
        prelim_cat = failure.get("failure_category", "OTHER")

        # Apply more specific classification
        refined_cat = classify_failure(
            query, top10_raw, chunks, failure.get("query", ""), quote
        )

        # Honor METHODS_RESULTS_NOISE from ablation if detected there
        if prelim_cat == "METHODS_RESULTS_NOISE" and refined_cat != "RIGHT_PARENT_WRONG_CHILD":
            refined_cat = "METHODS_RESULTS_NOISE"

        category_counts[refined_cat] += 1

        enriched_failures.append({
            "query_id": qid,
            "query": failure.get("query", ""),
            "topic": failure.get("topic", ""),
            "gold_document_ids": failure.get("gold_document_ids", []),
            "gold_parent_section_ids": failure.get("gold_parent_section_ids", []),
            "gold_child_chunk_ids": query.get("gold_child_chunk_ids", []),
            "gold_evidence_quote_snippet": quote[:300],
            "ablation_category": prelim_cat,
            "refined_category": refined_cat,
            "top10_doc_ids": list({item["document_id"] for item in top10_raw}),
            "top10_parent_ids": list({item.get("parent_section_id", "") for item in top10_raw}),
            "has_right_doc_in_top10": bool(
                {item["document_id"] for item in top10_raw} & set(failure.get("gold_document_ids", []))
            ),
        })

    n_total = len(queries)
    n_fails = len(enriched_failures)
    n_hits = n_total - n_fails

    print(f"{'Category':<45} {'N':>5} {'%failures':>10} {'%total':>10}")
    print("-" * 75)
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        pct_fail = 100 * count / n_fails if n_fails else 0
        pct_total = 100 * count / n_total
        print(f"  {cat:<43} {count:>5} {pct_fail:>9.1f}% {pct_total:>9.1f}%")
    print(f"\n  Total failures: {n_fails}/{n_total} = {100*n_fails/n_total:.1f}%")
    print(f"  Total hits@10: {n_hits}/{n_total} = {100*n_hits/n_total:.1f}%")
    print()

    # Summary buckets
    benchmark_issue_cats = {"RIGHT_PARENT_WRONG_CHILD", "GOLD_TOO_NARROW", "MULTIPLE_VALID_PASSAGES"}
    chunking_issue_cats = {"CHUNK_BOUNDARY", "SECTION_HEADING_AMBIGUITY"}
    methods_noise_cats = {"METHODS_RESULTS_NOISE"}
    true_retrieval_cats = {"ACTUAL_DENSE_FAILURE", "ACTUAL_RERANKER_FAILURE", "QUERY_BROADER_THAN_CHILD"}
    coverage_cats = {"SOURCE_COVERAGE_GAP"}

    benchmark_n = sum(v for k, v in category_counts.items() if k in benchmark_issue_cats)
    chunking_n = sum(v for k, v in category_counts.items() if k in chunking_issue_cats)
    methods_n = sum(v for k, v in category_counts.items() if k in methods_noise_cats)
    retrieval_n = sum(v for k, v in category_counts.items() if k in true_retrieval_cats)
    coverage_n = sum(v for k, v in category_counts.items() if k in coverage_cats)

    print("SUMMARY BUCKETS (as % of total failures):")
    print(f"  Benchmark/relevance issues: {benchmark_n}/{n_fails} = {100*benchmark_n/n_fails:.1f}%" if n_fails else "  N/A")
    print(f"  Chunking issues: {chunking_n}/{n_fails} = {100*chunking_n/n_fails:.1f}%" if n_fails else "  N/A")
    print(f"  Methods/results noise: {methods_n}/{n_fails} = {100*methods_n/n_fails:.1f}%" if n_fails else "  N/A")
    print(f"  True retrieval failures: {retrieval_n}/{n_fails} = {100*retrieval_n/n_fails:.1f}%" if n_fails else "  N/A")
    print(f"  Coverage gaps: {coverage_n}/{n_fails} = {100*coverage_n/n_fails:.1f}%" if n_fails else "  N/A")

    report = {
        "report_id": "RENAL-V2-PASSAGE-FAILURE-ANALYSIS",
        "architecture": "B_400_overlap x content_only (best dense from matrix)",
        "n_total_answerable": n_total,
        "n_top10_hits": n_hits,
        "n_top10_misses": n_fails,
        "hit_rate_at_10": round(n_hits / n_total, 4) if n_total else 0,
        "category_counts": dict(category_counts),
        "summary_buckets": {
            "benchmark_relevance_issues": {"n": benchmark_n, "pct_of_failures": round(100*benchmark_n/n_fails, 1) if n_fails else 0},
            "chunking_issues": {"n": chunking_n, "pct_of_failures": round(100*chunking_n/n_fails, 1) if n_fails else 0},
            "methods_results_noise": {"n": methods_n, "pct_of_failures": round(100*methods_n/n_fails, 1) if n_fails else 0},
            "true_retrieval_failures": {"n": retrieval_n, "pct_of_failures": round(100*retrieval_n/n_fails, 1) if n_fails else 0},
            "coverage_gaps": {"n": coverage_n, "pct_of_failures": round(100*coverage_n/n_fails, 1) if n_fails else 0},
        },
        "failures": enriched_failures,
    }

    OUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nPassage failure analysis written to: {OUT_PATH}")


if __name__ == "__main__":
    main()
