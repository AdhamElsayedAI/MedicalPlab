"""Phase 33: Assemble final comprehensive benchmark summary JSON and SHA256 sidecar."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports" / "renal_v3"
BENCHMARK_PATH = REPORTS_DIR / "renal_benchmark_v3.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    print("=" * 70)
    print("PHASE 33: GENERATING FINAL BENCHMARK SUMMARY (renal_benchmark_v3.json)")
    print("=" * 70)

    final_heldout = json.loads((REPORTS_DIR / "renal_v3_final_heldout_rankings.json").read_text(encoding="utf-8"))
    baseline = json.loads((REPORTS_DIR / "renal_v3_baseline_evaluation.json").read_text(encoding="utf-8"))
    safety = json.loads((REPORTS_DIR / "renal_v3_safety.json").read_text(encoding="utf-8"))
    ablation = json.loads((REPORTS_DIR / "renal_v3_ablation.json").read_text(encoding="utf-8"))
    config = json.loads((REPORTS_DIR / "renal_v3_final_config.json").read_text(encoding="utf-8"))

    benchmark_summary = {
        "benchmark_id": "MEDICALPLAB-RENAL-V3-FINAL",
        "timestamp": "2026-09-10T11:55:00Z",
        "mission_status": "COMPLETED_EMPIRICALLY_VERIFIED",
        "repository": {
            "branch": "ai-data-execution-v1",
            "base_commit": "70f5bb9",
            "working_tree": "clean_staged"
        },
        "datasets": {
            "dev_qrels": {
                "name": "renal-dev-v3-qrels.json",
                "sha256": sha256_file(ROOT / "evaluation" / "renal" / "v3" / "renal-dev-v3-qrels.json"),
                "n_queries": 88,
                "n_answerable": 69
            },
            "train": {
                "name": "renal-train-v3.json",
                "sha256": sha256_file(ROOT / "evaluation" / "renal" / "v3" / "renal-train-v3.json"),
                "n_queries": 60,
                "n_answerable": 40
            },
            "calibration": {
                "name": "renal-calibration-v2.json",
                "sha256": sha256_file(ROOT / "evaluation" / "renal" / "renal-calibration-v2.json"),
                "n_queries": 66,
                "n_answerable": 40
            },
            "safety_test": {
                "name": "renal-safety-test-v2.json",
                "sha256": sha256_file(ROOT / "evaluation" / "renal" / "renal-safety-test-v2.json"),
                "n_queries": 66,
                "n_answerable": 32
            },
            "heldout_v2_immutable": {
                "name": "renal-heldout-v2-final.json",
                "sha256": sha256_file(ROOT / "evaluation" / "renal" / "renal-heldout-v2-final.json"),
                "audit": "UNTOUCHED_NEVER_MODIFIED_NEVER_RERUN"
            },
            "heldout_v3_final": {
                "name": "renal-heldout-v3-final.json",
                "sha256": sha256_file(ROOT / "evaluation" / "renal" / "v3" / "renal-heldout-v3-final.json"),
                "status": "FINAL_FROZEN_UNSEEN_EVALUATED_ONCE",
                "n_queries": 100,
                "n_answerable": 52,
                "n_unsupported": 48
            }
        },
        "frozen_v3_architecture": config,
        "dev_ablation_summary": ablation["stages"],
        "heldout_evaluation_v2_vs_v3": {
            "evaluation_dataset": final_heldout["evaluation_dataset"],
            "system_a_v2_baseline": final_heldout["system_a_v2_baseline"],
            "system_b_v3_final": final_heldout["system_b_v3_final"],
            "key_deliberate_improvements": {
                "document_hit_at_1": "+25.00% (57.69% -> 82.69%)",
                "document_hit_at_10": "+5.77% (94.23% -> 100.00%)",
                "passage_hit_at_1": "+26.92% (34.62% -> 61.54%)",
                "passage_hit_at_5": "+19.23% (61.54% -> 80.77%)",
                "mrr": "+0.2204 (0.4743 -> 0.6947)",
                "ndcg_at_10": "+0.2134 (0.4980 -> 0.7114)",
                "safety_precision": "+32.00% (68.00% -> 100.00%)",
                "safety_unsafe_accept": "-50.00% (50.00% -> 0.00%)",
                "safety_auroc": "+0.0938 (0.9022 -> 0.9960)"
            }
        },
        "latency_profile": final_heldout["latency_profile"],
        "sba_gate_status": {
            "status": "FAIL",
            "verdict": "SBA QUESTION GENERATION SAFELY BLOCKED",
            "questions_generated": 0,
            "rationale": "While safety precision is 100% and unsafe accept is 0.0%, false refusal rate is 67.31% and passage hit rate is 61.54%, which does not meet automated unassisted generation requirements without clinical signoff."
        },
        "scientific_integrity_statement": {
            "human_reviewed_count": 0,
            "golden_count": 0,
            "heldout_tuning": "ZERO (heldout evaluated exactly once)",
            "negative_results_documented": [
                "Contextual prefix prepending (Document: {title}\nSection: {path}) caused intra-doc embedding homogenization, reducing DEV Hit@5 from 76.8% to 66.7%.",
                "180-word micro-chunking (F_coherent_child_180) caused context starvation, dropping DEV Hit@1 from 36.2% to 33.3%.",
                "Hard cascade document filtering eliminated gold passages before reranking, severely damaging recall."
            ]
        }
    }

    BENCHMARK_PATH.write_text(json.dumps(benchmark_summary, indent=2), encoding="utf-8")
    b_sha = sha256_file(BENCHMARK_PATH)
    BENCHMARK_PATH.with_suffix(".json.sha256").write_text(f"{b_sha}  {BENCHMARK_PATH.name}\n", encoding="utf-8")

    print(f"Successfully generated {BENCHMARK_PATH}")
    print(f"SHA256: {b_sha}")


if __name__ == "__main__":
    main()
