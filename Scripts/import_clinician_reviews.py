"""Import real clinician review findings and decisions from CSV or JSON."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from medicalplab.plab.governance import (
    REVIEW_DIMENSIONS,
    ReviewDecision,
    ReviewFinding,
)
from medicalplab.plab.pilot import PLABPilotService, PLABProductError


def import_csv_reviews(service: PLABPilotService, csv_path: Path, dry_run: bool = False) -> list[dict[str, Any]]:
    results = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = row.get("question_id", "").strip()
            if not qid or qid.startswith("#"):
                continue

            reviewer_id = row.get("reviewer_id", "").strip()
            if not reviewer_id:
                raise ValueError(f"Missing reviewer_id for question {qid}")

            decision_str = row.get("final_decision", "").strip().upper()
            if decision_str not in {"APPROVED", "REVISE", "REJECT"}:
                raise ValueError(f"Invalid final_decision '{decision_str}' for question {qid}")
            decision = ReviewDecision(decision_str)

            findings = {}
            for dim in REVIEW_DIMENSIONS:
                val = row.get(dim, "").strip().lower()
                if val not in {"pass", "edit", "fail"}:
                    raise ValueError(f"Invalid finding '{val}' for dimension '{dim}' in question {qid}")
                findings[dim] = ReviewFinding(val)

            comments = row.get("review_comments", "").strip() or None
            revision_notes = row.get("revision_notes", "").strip() or None
            reviewer_name = row.get("reviewer_name", "").strip() or None

            if dry_run:
                # Check eligibility
                rec = service.reviews.get(qid)
                if not rec:
                    raise ValueError(f"Question {qid} not in review queue")
                results.append({"question_id": qid, "decision": decision_str, "status": "validated_dry_run"})
            else:
                # 1. Start review if not started
                if service.reviews[qid].review_status.value in {"pending", "revised", "re_review"}:
                    service.start_review(qid, reviewer_id, reviewer_name)
                # 2. Submit review
                res = service.submit_review(
                    question_id=qid,
                    reviewer_id=reviewer_id,
                    decision=decision,
                    findings=findings,
                    comments=comments,
                    revision_notes=revision_notes,
                )
                results.append({
                    "question_id": qid,
                    "final_decision": res.get("final_decision"),
                    "golden_status": res.get("golden_status"),
                    "review_status": res.get("review_status"),
                })

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Import clinician reviews into MedicalPlab")
    parser.add_argument("--file", required=True, help="Path to CSV or JSON review file")
    parser.add_argument("--dry-run", action="store_true", help="Validate without committing")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: file {file_path} not found.", file=sys.stderr)
        return 1

    service = PLABPilotService.load_default()

    try:
        if file_path.suffix.lower() == ".csv":
            results = import_csv_reviews(service, file_path, dry_run=args.dry_run)
        else:
            print("Only CSV import is supported directly via CLI at this time.", file=sys.stderr)
            return 1

        print(f"Successfully processed {len(results)} reviews (dry_run={args.dry_run}):")
        for r in results:
            print(f"  {r['question_id']}: decision={r.get('final_decision') or r.get('decision')} golden={r.get('golden_status')}")

        gov = service.governance_counts()
        print("\nUpdated Governance Status:")
        print(f"  Golden:   {gov['golden']}")
        print(f"  Approved: {gov['approved']}")
        print(f"  Pending:  {gov['pending']}")
        return 0

    except Exception as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
