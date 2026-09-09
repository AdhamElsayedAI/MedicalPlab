"""Benchmark harness for the Urinary/Renal Course Learning Track."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

URINARY_RAW_DIR = PROJECT_ROOT / "Data" / "raw" / "urinary"
URINARY_PROCESSED_DIR = PROJECT_ROOT / "Data" / "processed" / "urinary"


def run_urinary_benchmark() -> dict[str, object]:
    raw_exists = URINARY_RAW_DIR.exists() and any(URINARY_RAW_DIR.iterdir())
    proc_exists = URINARY_PROCESSED_DIR.exists() and any(URINARY_PROCESSED_DIR.iterdir())

    if not (raw_exists or proc_exists):
        return {
            "status": "SOURCE_DATA_NOT_AVAILABLE",
            "mentor_flag": "URINARY_SOURCE_DATA = NOT AVAILABLE",
            "documents_count": 0,
            "chunks_count": 0,
            "evaluation_queries_count": 0,
            "retrieval_hit_at_1": "NOT MEASURED — SOURCE DATA MISSING",
            "retrieval_hit_at_5": "NOT MEASURED — SOURCE DATA MISSING",
            "retrieval_mrr": "NOT MEASURED — SOURCE DATA MISSING",
            "retrieval_ndcg_at_10": "NOT MEASURED — SOURCE DATA MISSING",
            "evidence_sufficiency": "NOT MEASURED — NO LABELED SUFFICIENCY SET",
            "citation_resolution_rate": "NOT MEASURED — SOURCE DATA MISSING",
            "grounded_response_coverage": "NOT MEASURED — SOURCE DATA MISSING",
            "unsupported_refusal_rate": "NOT MEASURED — SOURCE DATA MISSING",
            "latency_p50_ms": "NOT MEASURED — SOURCE DATA MISSING",
            "latency_p95_ms": "NOT MEASURED — SOURCE DATA MISSING",
            "required_action": "Clinical team must provide authorized urinary/renal course PDFs into Data/raw/urinary/.",
        }

    return {
        "status": "DATA_AVAILABLE",
        "documents_count": len(list(URINARY_RAW_DIR.glob("*.*"))),
        "chunks_count": len(list(URINARY_PROCESSED_DIR.glob("*.chunks.json"))),
    }


def main() -> int:
    report = run_urinary_benchmark()
    print("=" * 60)
    print("URINARY/RENAL COURSE TRACK BENCHMARK")
    print("=" * 60)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
