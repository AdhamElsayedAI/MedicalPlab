"""
MedicalPlab Shared Evidence Engine V2 — Stage 15: PubMedQA External Benchmark Harness
=====================================================================================
Evaluates the Central Claim Verifier on official PubMedQA benchmark items (ori_pqal, N=1000):
- Preserves original PubMed IDs and contexts
- Strictly separate from internal MedicalPlab frozen benchmarks
- Computes macro accuracy, Wilson 95% confidence intervals, and decision-level breakdown
- Saves full audit report to reports/evidence_engine/pubmedqa_evaluation_report.json
"""

import hashlib
import json
import logging
import math
import sys
import time
from pathlib import Path
from typing import Any

# Ensure root in sys.path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from medicalplab.evidence_engine.claim_verifier import CentralClaimVerifier
from medicalplab.evidence_engine.models import RetrievedCandidate, VerificationState

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluate_pubmedqa")

BENCHMARK_PATH = _ROOT / "evaluation" / "evidence_engine" / "pubmedqa_external_benchmark.json"
REPORT_DIR = _ROOT / "reports" / "evidence_engine"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = REPORT_DIR / "pubmedqa_evaluation_report.json"


def wilson_score_interval(successes: int, total: int, z: float = 1.95996) -> tuple[float, float]:
    """Compute Wilson score interval (95% confidence)."""
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1.0 + (z**2) / total
    centre = (p + (z**2) / (2.0 * total)) / denom
    half_width = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z**2) / (4.0 * (total**2))))
    return max(0.0, centre - half_width), min(1.0, centre + half_width)


def run_pubmedqa_evaluation(max_items: int | None = None):
    logger.info(f"Loading official PubMedQA benchmark from {BENCHMARK_PATH}...")
    data = json.loads(BENCHMARK_PATH.read_bytes())
    items = data.get("items", [])
    if max_items is not None:
        items = items[:max_items]

    n_items = len(items)
    logger.info(f"Evaluating {n_items} official PubMedQA items...")

    verifier = CentralClaimVerifier()

    correct_predictions = 0
    decision_counts = {"yes": 0, "no": 0, "maybe": 0}
    predicted_counts = {"SUPPORTED": 0, "CONTRADICTED": 0, "PARTIALLY_SUPPORTED": 0, "NOT_SUPPORTED": 0}
    confusion = {
        "yes": {"SUPPORTED": 0, "CONTRADICTED": 0, "PARTIALLY_SUPPORTED": 0, "NOT_SUPPORTED": 0},
        "no": {"SUPPORTED": 0, "CONTRADICTED": 0, "PARTIALLY_SUPPORTED": 0, "NOT_SUPPORTED": 0},
        "maybe": {"SUPPORTED": 0, "CONTRADICTED": 0, "PARTIALLY_SUPPORTED": 0, "NOT_SUPPORTED": 0},
    }

    per_item_results = []
    t0 = time.perf_counter()

    for idx, item in enumerate(items, start=1):
        pmid = item["pmid"]
        q = item["question"]
        gold_decision = item["gold_decision"]  # 'yes', 'no', 'maybe'
        context_text = item["full_context"]
        long_ans = item.get("long_answer", "")

        decision_counts[gold_decision] = decision_counts.get(gold_decision, 0) + 1

        # Synthesize affirmative candidate claim from question + long answer
        cand = RetrievedCandidate(
            chunk_id=f"PUBMED-{pmid}",
            document_id=f"PMID-{pmid}",
            section_path=["PubMedQA Official Abstract"],
            heading="Abstract Context",
            text=context_text,
            doc_title=f"PubMed ID {pmid}",
            fused_score=1.0,
        )

        # Claim to test: question converted into assertion with long answer
        test_claim = long_ans if long_ans else q
        v_res = verifier.verify_claim(
            claim_id=f"PUBMEDQA-{pmid}",
            claim_text=test_claim,
            evidence_text=cand.text,
            cited_chunk_id=cand.chunk_id,
            cited_document_id=cand.document_id
        )
        pred_state = v_res.state.value

        predicted_counts[pred_state] = predicted_counts.get(pred_state, 0) + 1
        if gold_decision in confusion:
            confusion[gold_decision][pred_state] = confusion[gold_decision].get(pred_state, 0) + 1

        # Match logic:
        # 'yes' aligns with SUPPORTED or PARTIALLY_SUPPORTED
        # 'no' aligns with CONTRADICTED
        # 'maybe' aligns with PARTIALLY_SUPPORTED or NOT_SUPPORTED
        is_correct = False
        if gold_decision == "yes" and v_res.state in (VerificationState.SUPPORTED, VerificationState.PARTIALLY_SUPPORTED):
            is_correct = True
        elif gold_decision == "no" and v_res.state == VerificationState.CONTRADICTED:
            is_correct = True
        elif gold_decision == "maybe" and v_res.state in (VerificationState.PARTIALLY_SUPPORTED, VerificationState.NOT_SUPPORTED):
            is_correct = True

        if is_correct:
            correct_predictions += 1

        per_item_results.append({
            "pmid": pmid,
            "question": q,
            "gold_decision": gold_decision,
            "predicted_state": pred_state,
            "is_aligned": is_correct,
            "confidence": v_res.confidence,
            "veto_flags": v_res.veto_flags,
        })

        if idx % 100 == 0 or idx == n_items:
            logger.info(f"[{idx}/{n_items}] Accuracy: {correct_predictions/idx:.1%}")

    elapsed = time.perf_counter() - t0
    acc = correct_predictions / n_items if n_items > 0 else 0.0
    low_ci, high_ci = wilson_score_interval(correct_predictions, n_items)

    summary = {
        "benchmark": "PubMedQA (Official pqa_labeled)",
        "provenance": data.get("provenance_url"),
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_items_evaluated": n_items,
        "elapsed_seconds": round(elapsed, 2),
        "overall_alignment_accuracy": {
            "correct": correct_predictions,
            "total": n_items,
            "rate": round(acc, 4),
            "pct": f"{acc * 100:.2f}%",
            "ci_95_wilson": [round(low_ci, 4), round(high_ci, 4)],
        },
        "gold_distribution": decision_counts,
        "predicted_distribution": predicted_counts,
        "confusion_matrix": confusion,
        "per_item_results": per_item_results,
    }

    REPORT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    sha = hashlib.sha256(REPORT_PATH.read_bytes()).hexdigest()
    (REPORT_PATH.with_suffix(".json.sha256")).write_text(f"{sha}  {REPORT_PATH.name}\n", encoding="utf-8")

    logger.info("================================================================")
    logger.info(f"PubMedQA EVALUATION COMPLETE: {acc * 100:.2f}% (95% CI: [{low_ci:.4f}, {high_ci:.4f}])")
    logger.info(f"Report saved to: {REPORT_PATH.name} (SHA-256: {sha})")
    logger.info("================================================================")
    return summary


if __name__ == "__main__":
    run_pubmedqa_evaluation()
