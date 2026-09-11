"""
MedicalPlab Renal V5 — Freeze P3 Candidate Specification
=========================================================
Freezes the exact architecture, feature set, preprocessing, regularization,
weights, thresholds, B=500, R=20, and SHA for P3 before any evaluation
on SELECT_VAL_CLEAN_V1.
"""

import json
import hashlib
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
reports_dir = _ROOT / "reports/renal_v5"
spec_file = reports_dir / "renal_v5_p3_model_specification.json"
sha_file = reports_dir / "renal_v5_p3_model_specification.json.sha256"

# Exact frozen parameters of P3-A (Regularized Logistic Relevance Scorer)
# Feature indices:
# 0: dense_combined (Dense + 0.18*Doc)
# 1: bm25_score (Okapi BM25 k1=1.5, b=0.75)
# 2: section_centroid_score (cosine with section chunk centroid)
# 3: lexical_jaccard (token Jaccard similarity)
# 4: lexical_containment (query token containment in chunk)

frozen_p3_spec = {
    "model_name": "SELECTOR_V5_P3_REGULARIZED_LOGISTIC_SCORER",
    "model_class": "REGULARIZED_LOW_CAPACITY_QUERY_GROUPED_LOGISTIC_RANKER",
    "status": "FROZEN_PRE_EVALUATION",
    "b_input_budget": 500,
    "r_output_budget": 20,
    "features": [
        {
            "index": 0,
            "name": "dense_combined",
            "description": "Baseline first-stage dense similarity score + 0.18 * document prior score",
            "runtime_available": True,
            "gold_leakage": False
        },
        {
            "index": 1,
            "name": "bm25_sparse",
            "description": "Okapi BM25 score (k1=1.5, b=0.75) over chunk text tokens",
            "runtime_available": True,
            "gold_leakage": False
        },
        {
            "index": 2,
            "name": "section_centroid",
            "description": "Cosine similarity of query embedding with precomputed section chunk centroid embedding",
            "runtime_available": True,
            "gold_leakage": False
        },
        {
            "index": 3,
            "name": "lexical_jaccard",
            "description": "Token Jaccard overlap between query tokens and chunk text tokens",
            "runtime_available": True,
            "gold_leakage": False
        },
        {
            "index": 4,
            "name": "lexical_containment",
            "description": "Fraction of query tokens present in chunk text",
            "runtime_available": True,
            "gold_leakage": False
        }
    ],
    "preprocessing": {
        "method": "QUERY_GROUPED_Z_SCORE",
        "description": "Per-query standardization across candidate pool: z = (x - mean_q) / (std_q + 1e-9)"
    },
    "regularization": {
        "penalty": "L2",
        "C": 0.1,
        "solver": "lbfgs",
        "class_weight": {
            "0": 1.0,
            "1": 50.0
        },
        "max_iter": 500
    },
    "frozen_coefficients": {
        "dense_combined": 2.20920223,
        "bm25_sparse": 0.97126733,
        "section_centroid": -1.17596765,
        "lexical_jaccard": -0.12850108,
        "lexical_containment": 0.13216377
    },
    "frozen_intercept": -5.670422908091894,
    "train_core_cross_validation_results": {
        "cv_folds": 5,
        "grouping_unit": "QUERY_FAMILY_ATOM",
        "candidate_row_splitting": False,
        "n_query_families": 60,
        "out_of_fold_output_coverage_at_20": "56/60 (93.3%)",
        "out_of_fold_output_coverage_at_50": "59/60 (98.3%)",
        "naive_top20_preservation": "45/47 (95.7%)",
        "genuine_rescues_count": 11,
        "relevant_lost_count": 2,
        "mrr": 0.6610,
        "median_best_relevant_rank": 1.0,
        "p75_best_relevant_rank": 6.0,
        "p90_best_relevant_rank": 18.0
    },
    "predeclared_evaluation_gate": {
        "target_split": "SELECT_VAL_CLEAN_V1 (N=20)",
        "primary_metric": "OutputCoverage@20 >= 17/20 (85.0%)",
        "naive_top20_preservation_threshold": ">= 95.0% (at most 0 lost on N=20)",
        "genuine_rescues_requirement": ">= 2 rank 21+ rescues",
        "candidate_output_budget": "R exactly 20",
        "max_latency_ms": 50.0,
        "gpu_paging": False,
        "hard_leakage": 0
    }
}

spec_file.write_text(json.dumps(frozen_p3_spec, indent=2), encoding="utf-8")
file_sha = hashlib.sha256(spec_file.read_bytes()).hexdigest()
sha_file.write_text(f"{file_sha}  {spec_file.name}\n", encoding="utf-8")

print(f"P3 Model Specification frozen at: {spec_file}")
print(f"SHA-256: {file_sha}")
print(f"SHA-256 sidecar written to: {sha_file}")
