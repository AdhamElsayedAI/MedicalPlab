"""Operational tool to inspect promotion eligibility and promote clinically approved questions to Golden."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from medicalplab.plab.pilot import PLABPilotService, PLABProductError


def main() -> int:
    parser = argparse.ArgumentParser(description="MedicalPlab Golden Promotion CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    subparsers.add_parser("status", help="Print governance and Golden counts")

    # check
    check_p = subparsers.add_parser("check", help="Check Golden promotion eligibility for a question")
    check_p.add_argument("question_id", help="e.g. PLAB-CARD-0001")

    # check-all
    subparsers.add_parser("check-all", help="Evaluate promotion eligibility for all questions")

    # promote
    promote_p = subparsers.add_parser("promote", help="Promote an approved question through the Golden gate")
    promote_p.add_argument("question_id", help="e.g. PLAB-CARD-0001")

    args = parser.parse_args()

    service = PLABPilotService.load_default()

    if args.command == "status":
        counts = service.governance_counts()
        print("=== MedicalPlab Governance Status ===")
        print(f"Total Questions: {len(service.questions)}")
        print(f"Golden:          {counts['golden']}")
        print(f"Approved:        {counts['approved']}")
        print(f"In Review:       {counts['in_review']}")
        print(f"Revised:         {counts['revised']}")
        print(f"Pending Review:  {counts['pending']}")
        print(f"Rejected:        {counts['rejected']}")
        return 0

    elif args.command == "check":
        try:
            result = service.check_promotion_eligibility(args.question_id)
            print(json.dumps(result, indent=2))
            return 0 if result["eligible"] else 1
        except PLABProductError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

    elif args.command == "check-all":
        print(f"Checking promotion eligibility for {len(service.questions)} questions...")
        eligible_count = 0
        golden_count = 0
        for qid in sorted(service.questions.keys()):
            res = service.check_promotion_eligibility(qid)
            if res["golden_status"]:
                golden_count += 1
                status_str = "ALREADY_GOLDEN"
            elif res["eligible"]:
                eligible_count += 1
                status_str = "ELIGIBLE"
            else:
                status_str = f"BLOCKED: {','.join(res['error_codes'])}"
            print(f"{qid:16} | {res['review_status']:12} | {status_str}")

        print("\nSummary:")
        print(f"Total:    {len(service.questions)}")
        print(f"Golden:   {golden_count}")
        print(f"Eligible: {eligible_count}")
        print(f"Blocked:  {len(service.questions) - golden_count - eligible_count}")
        return 0

    elif args.command == "promote":
        try:
            res = service.check_promotion_eligibility(args.question_id)
            if not res["eligible"]:
                print(f"Cannot promote {args.question_id}: not eligible.", file=sys.stderr)
                print(f"Error codes: {','.join(res['error_codes'])}", file=sys.stderr)
                return 1
            # Perform promotion
            review = service.reviews[args.question_id]
            from dataclasses import replace
            promoted_review = replace(review, golden_status=True)
            service.reviews[args.question_id] = promoted_review
            if service.persistence:
                service.persistence.save_review(promoted_review)
            print(f"Successfully promoted {args.question_id} to Golden!")
            return 0
        except PLABProductError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
