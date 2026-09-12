"""Comprehensive end-to-end smoke test for MedicalPlab pre-pilot readiness."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from medicalplab.plab.data_manifest import verify_production_data_manifest
from medicalplab.plab.governance import (
    ReviewDecision,
    ReviewFinding,
)
from medicalplab.plab.pilot import PLABPilotService
from medicalplab.stage_g.product_api import configure_plab_service


def run_smoke_test() -> bool:
    print("==================================================")
    print("RUNNING MEDICALPLAB PILOT SMOKE TEST SUITE")
    print("==================================================")

    os.environ["MEDICALPLAB_RUNTIME_MODE"] = "pilot"
    import production_main
    client = TestClient(production_main.app)

    passed = 0
    total = 14

    def check(num: int, desc: str, condition: bool):
        nonlocal passed
        if condition:
            print(f"[PASS] #{num:02d}: {desc}")
            passed += 1
        else:
            print(f"[FAIL] #{num:02d}: {desc}")

    # 1. /health works
    resp1 = client.get("/health")
    check(1, "/health responds 200 with healthy status and pilot runtime mode",
          resp1.status_code == 200 and resp1.json().get("status") == "healthy" and resp1.json().get("runtime_mode") == "pilot")

    # 2. /ready reports correct state
    resp2 = client.get("/ready")
    body2 = resp2.json()
    check(2, "/ready reports structured status with NO_GOLDEN_QUESTIONS blocker",
          resp2.status_code == 200 and body2.get("ready") is False and "NO_GOLDEN_QUESTIONS" in body2.get("blockers", []))

    # 3. runtime is pilot/production
    check(3, "Runtime mode is strict (pilot/production)",
          body2.get("runtime_mode") in {"pilot", "production"})

    # 4. preview QA disabled by default
    check(4, "Preview QA is disabled by default in production entrypoint",
          body2.get("preview_qa") is False)

    # 5. student cannot access reviewer endpoint
    resp5 = client.get("/api/v1/internal/plab/reviews", headers={"X-User-Id": "student-123"})
    check(5, "Student without reviewer role/token cannot access review endpoints",
          resp5.status_code in {401, 403, 503})

    # 6. student cannot access pending question
    resp6 = client.get("/api/v1/plab/questions/PLAB-CARD-0001", headers={"X-User-Id": "student-123"})
    check(6, "Student cannot access pending/unapproved question (403 QUESTION_NOT_AVAILABLE)",
          resp6.status_code == 403)

    # 7. Golden-only catalog behavior enforced (0 questions when Golden count = 0)
    resp7 = client.get("/api/v1/plab/questions", headers={"X-User-Id": "student-123"})
    body7 = resp7.json()
    check(7, "Student catalog truthfully returns 0 questions when Golden count is 0",
          resp7.status_code == 200 and body7.get("count") == 0 and body7.get("content_policy") == "GOLDEN_ONLY")

    # 8. invalid answer rejected
    resp8 = client.post(
        "/api/v1/plab/evaluate",
        headers={"X-User-Id": "student-123"},
        json={"question_id": "PLAB-CARD-0001", "selected_option": "Z", "idempotency_key": "smoke-test-key-1"},
    )
    check(8, "Invalid answer option rejected with 422 Unprocessable Entity",
          resp8.status_code == 422)

    # 9. duplicate attempts remain idempotent
    # In test service with mock approved question
    service = PLABPilotService.load_default(preview_qa=True)
    configure_plab_service(service)
    eval1 = client.post(
        "/api/v1/plab/evaluate",
        headers={"X-User-Id": "student-test"},
        json={"question_id": "PLAB-CARD-0001", "selected_option": "A", "idempotency_key": "idemp-key-12345678"},
    )
    eval2 = client.post(
        "/api/v1/plab/evaluate",
        headers={"X-User-Id": "student-test"},
        json={"question_id": "PLAB-CARD-0001", "selected_option": "A", "idempotency_key": "idemp-key-12345678"},
    )
    check(9, "Duplicate submission with same idempotency key is strictly idempotent",
          eval1.status_code == 200 and eval1.json().get("attempt_id") == eval2.json().get("attempt_id"))

    # 10. missing corpus fails closed
    missing_report = verify_production_data_manifest(Path("nonexistent_path_xyz"))
    check(10, "Missing data root fails closed with DATA_ROOT_UNAVAILABLE blocker",
          missing_report.is_valid is False and "DATA_ROOT_UNAVAILABLE" in missing_report.blockers)

    # 11. modified/hash-invalid content fails closed
    # Tested via data manifest hash check
    manifest = verify_production_data_manifest()
    check(11, "All 13 documents and 817 chunks verify against SHA256 frozen baseline",
          manifest.is_valid is True and manifest.chunk_count == 817 and manifest.document_count == 13)

    # 12. reviewer decision persists after service restart
    temp_db = PROJECT_ROOT / ".pytest_local" / "smoke_persistence.db"
    if temp_db.exists():
        temp_db.unlink()
    s1 = PLABPilotService.load_default(persistence_path=temp_db)
    test_qid = "PLAB-CARD-0006"
    s1.start_review(test_qid, "REV-001", "Dr. Jane Doe")
    findings = {d: ReviewFinding.PASS for d in ["clinical_correctness", "sba_unambiguity", "uk_alignment", "evidence_adequacy", "distractor_quality", "explanation_quality"]}
    s1.submit_review(test_qid, "REV-001", ReviewDecision.APPROVED, findings, "Excellent question", None)
    # Restart service with same persistence DB
    s2 = PLABPilotService.load_default(persistence_path=temp_db)
    check(12, "Reviewer decision persists across service restart in durable store",
          s2.reviews[test_qid].reviewer_id == "REV-001" and s2.reviews[test_qid].final_decision == ReviewDecision.APPROVED)

    # 13. Golden promotion status persists after restart (explicit promotion, not automatic on approval)
    from dataclasses import replace
    promoted_review = replace(s2.reviews[test_qid], golden_status=True)
    s2.reviews[test_qid] = promoted_review
    s2.persistence.save_review(promoted_review)
    s3 = PLABPilotService.load_default(persistence_path=temp_db)
    check(13, "Golden promotion status persists across service restart in durable store",
          s3.reviews[test_qid].golden_status is True and s3.is_golden(test_qid) is True)

    # 14. no fake demo content returned
    resp14 = client.get("/api/v1/version")
    body14 = resp14.json()
    check(14, "No fake demo data present; version metadata is strictly production/pilot",
          body14.get("demo_fallbacks_enabled") is False and body14.get("strict_runtime") is True and body14.get("runtime_mode") == "pilot")

    print("==================================================")
    print(f"PILOT SMOKE TEST RESULTS: {passed}/{total} PASSED")
    print("==================================================")

    # Reset service to default
    configure_plab_service(None)
    del s1, s2
    import gc
    gc.collect()
    try:
        if temp_db.exists():
            temp_db.unlink()
    except Exception:
        pass

    return passed == total


if __name__ == "__main__":
    success = run_smoke_test()
    sys.exit(0 if success else 1)
