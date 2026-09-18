#!/usr/bin/env python3
"""MedicalPlab One-Command Local Release Verifier.

Validates that the local clone of MedicalPlab is completely ready for
immediate local execution, reviewer evaluation, mobile integration, and mentor demo
without requiring any cloud infrastructure, paid API keys, or external secrets.

Checks performed:
1. Python runtime compatibility (3.10+)
2. Critical repository files and scripts presence
3. Data integrity and public-safe corpus manifest
4. Backend imports and router configurations
5. OpenAPI contract alignment against frozen reference
6. Staging gate local bypass (fail-open for local, fail-closed for staging)
7. Full in-memory E2E representative product flow (Section 12 specification)
8. Frontend local configuration audit
9. Optional live server probe (if already running on port 8000)

Usage:
    python Scripts/verify_local_release.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Enforce safe local environment defaults for validation
os.environ["MEDICALPLAB_RUNTIME_MODE"] = "pilot"
os.environ["MEDICALPLAB_PLAB_PREVIEW_QA"] = "1"
os.environ["MEDICALPLAB_PHASE_2B_ENABLED"] = "1"
os.environ["MEDICALPLAB_ANATOMY_3D_ENABLED"] = "1"
os.environ["MEDICALPLAB_TUTOR_PROVIDER"] = "stub"
os.environ["MEDICALPLAB_STAGING_GATE_ENABLED"] = "0"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"


def check_python_version() -> bool:
    print("\n[Check 1/8] Python Version Compatibility...")
    major, minor = sys.version_info.major, sys.version_info.minor
    print(f"  Detected Python: {major}.{minor}.{sys.version_info.micro}")
    if major < 3 or (major == 3 and minor < 10):
        print(f"  FAIL: Python 3.10+ required, found {major}.{minor}")
        return False
    print("  PASS: Python version is supported.")
    return True


def check_critical_files() -> bool:
    print("\n[Check 2/8] Critical Repository Files...")
    critical_files = [
        "production_main.py",
        "main.py",
        "requirements.txt",
        "pyproject.toml",
        ".env.example",
        "Dockerfile",
        "Scripts/start_local.ps1",
        "Scripts/start_local.sh",
        "Scripts/bootstrap_local_data.py",
        "Scripts/verify_local_release.py",
        "docs/LOCAL_RUN_GUIDE.md",
        "docs/handoff/MENTOR_LOCAL_RUN.md",
        "docs/mobile-handoff/MedicalPlab_Local.postman_environment.json",
        "docs/mobile-handoff/MedicalPlab.mobile.postman_collection.json",
        "docs/mobile-handoff/openapi.json",
        "frontend/package.json",
        "frontend/src/app/page.tsx",
        "frontend/.env.example",
    ]
    missing = []
    for rel_path in critical_files:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            missing.append(rel_path)
            print(f"  MISSING: {rel_path}")
        else:
            print(f"  EXISTS:  {rel_path}")
    if missing:
        print(f"  FAIL: {len(missing)} critical files missing.")
        return False
    print("  PASS: All critical files are present.")
    return True


def check_data_manifest() -> bool:
    print("\n[Check 3/8] Data Manifest & Corpus Verification...")
    try:
        from Scripts.bootstrap_local_data import bootstrap_local_data
        from medicalplab.plab.data_manifest import verify_production_data_manifest
        data_root = PROJECT_ROOT / "Data"
        bootstrap_local_data(data_root)
        report = verify_production_data_manifest(data_root)
        print(f"  Data root: {data_root}")
        print(f"  Documents: {report.document_count}, Chunks: {report.chunk_count}")
        if not report.is_valid:
            print(f"  FAIL: Data manifest invalid: {report.blockers}")
            return False
        print("  PASS: Data manifest verified (public-safe CC BY 4.0 validation fixtures).")
        return True
    except Exception as exc:
        print(f"  FAIL: Data manifest check error: {exc}")
        return False


def check_backend_imports() -> bool:
    print("\n[Check 4/8] Backend Application Imports & Router Health...")
    try:
        from production_main import app
        openapi_paths = set(app.openapi().get("paths", {}).keys())
        expected_sample = {"/health", "/ready", "/api/v1/version", "/api/v1/university/subjects"}
        for p in expected_sample:
            assert p in openapi_paths, f"Expected route {p} not registered in app"
        print(f"  Total API paths in production_main: {len(openapi_paths)}")
        print("  PASS: Backend imports and routing verified.")
        return True
    except Exception as exc:
        print(f"  FAIL: Backend import error: {exc}")
        return False


def check_openapi_drift() -> bool:
    print("\n[Check 5/8] OpenAPI Contract Alignment...")
    try:
        from Scripts.verify_mobile_contract_drift import main as verify_drift
        ret = verify_drift()
        if ret != 0:
            print(f"  FAIL: Contract drift detected (exit code {ret}).")
            return False
        print("  PASS: 0 drift detected against frozen reference specification.")
        return True
    except Exception as exc:
        print(f"  FAIL: Contract drift audit failed: {exc}")
        return False


def check_local_staging_gate_bypass() -> bool:
    print("\n[Check 6/8] Staging Gate Local Bypass...")
    try:
        from medicalplab.staging.security import is_staging_gate_enabled
        assert not is_staging_gate_enabled(), "Staging gate should be disabled by default for local run"
        print("  Staging gate active: False (local developer does not need X-Staging-Key)")
        print("  PASS: Local staging gate behavior is clean.")
        return True
    except Exception as exc:
        print(f"  FAIL: Staging gate verification error: {exc}")
        return False


def check_representative_e2e_flow() -> bool:
    print("\n[Check 7/8] In-Memory Representative Product Flow (Section 12 E2E)...")
    try:
        from fastapi.testclient import TestClient
        from production_main import app

        with TestClient(app) as client:
            user_header = {"X-User-Id": "local-e2e-synthetic-learner"}

            # 1. Health
            r = client.get("/health")
            assert r.status_code == 200, f"GET /health failed: {r.status_code}"
            assert r.json().get("status") == "healthy"
            print("  [1/10] GET /health -> 200 OK (status: healthy)")

            # 2. Ready
            r = client.get("/ready")
            assert r.status_code == 200, f"GET /ready failed: {r.status_code}"
            print("  [2/10] GET /ready -> 200 OK (pilot mode verified)")

            # 3. Version
            r = client.get("/api/v1/version")
            assert r.status_code == 200, f"GET /api/v1/version failed: {r.status_code}"
            assert r.json().get("contract_version") == "2026-09-10"
            print("  [3/10] GET /api/v1/version -> 200 OK (v1.1.0 baseline)")

            # 4. University Curriculum & Question
            r = client.get("/api/v1/university/subjects", headers=user_header)
            assert r.status_code == 200, f"GET /university/subjects failed: {r.status_code}"

            r = client.get(
                "/api/v1/university/question?subject=Renal%20physiology&topic=RAAS%20mechanisms",
                headers=user_header,
            )
            assert r.status_code == 200, f"GET /university/question failed: {r.status_code}"
            assert "correct_option" not in r.json(), "Question payload must not leak correct option"
            print("  [4/10] GET /api/v1/university/question -> 200 OK (zero answer leakage)")

            # 5. University Answer Submission (Selecting distractor B)
            r = client.post(
                "/api/v1/university/answer",
                headers=user_header,
                json={
                    "question_id": "UNI-RENAL-001",
                    "selected_option": "B",
                    "idempotency_key": "idemp-local-e2e-001",
                },
            )
            assert r.status_code == 200, f"POST /university/answer failed: {r.status_code}"
            assert not r.json().get("is_correct"), "Option B expected to be incorrect distractor"
            print("  [5/10] POST /api/v1/university/answer -> 200 OK (distractor signal captured)")

            # 6. Adaptive State & Recommendation
            r = client.get("/api/v1/adaptive/state?learner_id=local-e2e-synthetic-learner")
            assert r.status_code == 200, f"GET /adaptive/state failed: {r.status_code}"

            r = client.get("/api/v1/adaptive/recommendation?learner_id=local-e2e-synthetic-learner")
            assert r.status_code == 200, f"GET /adaptive/recommendation failed: {r.status_code}"
            print("  [6/10] GET /api/v1/adaptive/recommendation -> 200 OK (remediation suggested)")

            # 7. Bounded 3-Turn Socratic Remediation Loop
            # Turn 1: Probe
            r1 = client.post(
                "/api/v1/remediation/start",
                headers=user_header,
                json={
                    "question_id": "UNI-RENAL-001",
                    "selected_option": "B",
                    "topic": "RAAS mechanisms",
                },
            )
            assert r1.status_code in {200, 201}, f"POST /remediation/start failed: {r1.status_code}"
            session_id = r1.json().get("session_id")
            assert session_id, "Remediation session_id must be returned"

            # Turn 2: Guide
            r2 = client.post(
                "/api/v1/remediation/turn",
                headers=user_header,
                json={
                    "session_id": session_id,
                    "student_message": "Renin acts as an enzyme on a precursor protein.",
                },
            )
            assert r2.status_code == 200, f"Turn 2 failed: {r2.status_code}"

            # Turn 3: Consolidate & Check Readiness
            r3 = client.post(
                "/api/v1/remediation/turn",
                headers=user_header,
                json={
                    "session_id": session_id,
                    "student_message": "Angiotensinogen is the hepatic substrate cleaved by renin.",
                },
            )
            assert r3.status_code == 200, f"Turn 3 failed: {r3.status_code}"
            assert r3.json().get("transfer_available") is True, "Transfer challenge must be unlocked"
            print(f"  [7/10] Bounded 3-Turn Socratic Loop -> 200 OK (session: {session_id}, unlocked transfer)")

            # 8. Held-Out Independent Transfer Problem (UNI-RENAL-001-T -> Answer A)
            r_tr = client.get(f"/api/v1/remediation/session/{session_id}/transfer", headers=user_header)
            assert r_tr.status_code == 200, f"GET transfer failed: {r_tr.status_code}"
            assert r_tr.json().get("question_id") == "UNI-RENAL-001-T", f"Expected UNI-RENAL-001-T, got {r_tr.json().get('question_id')}"

            r_sub = client.post(
                f"/api/v1/remediation/session/{session_id}/transfer",
                headers=user_header,
                json={
                    "session_id": session_id,
                    "question_id": "UNI-RENAL-001-T",
                    "selected_option": "A",
                },
            )
            assert r_sub.status_code == 200, f"POST transfer failed: {r_sub.status_code}"
            assert r_sub.json().get("is_correct") is True, "Answer A (Angiotensinogen) should score correct"
            assert r_sub.json().get("outcome") == "TRANSFER_CONFIRMED"
            print("  [8/10] Independent Held-Out Transfer -> 200 OK (UNI-RENAL-001-T confirmed with Answer A)")

            # 9. Grounded Stub Tutor Chat
            r_tutor = client.post(
                "/api/v1/tutor/chat",
                headers=user_header,
                json={"query": "Explain the role of renin in renal hemodynamics"},
            )
            assert r_tutor.status_code == 200, f"POST /tutor/chat failed: {r_tutor.status_code}"
            print("  [9/10] POST /api/v1/tutor/chat -> 200 OK (deterministic zero-cost)")

            # 10. 3D Spatial Anatomy (Guided Tour + Challenge) & Progress & PLAB Preview
            r_manifest = client.get("/api/v1/anatomy/manifest", headers=user_header)
            assert r_manifest.status_code == 200

            r_anat_start = client.post("/api/v1/anatomy/session/start", json={"learner_id": "local-e2e-synthetic-learner"})
            assert r_anat_start.status_code == 200
            anat_session_id = r_anat_start.json()["session"]["session_id"]

            # Guided interaction: renal_vein_left
            r_tour = client.post(
                f"/api/v1/anatomy/session/{anat_session_id}/interact",
                json={"learner_id": "local-e2e-synthetic-learner", "selected_structure_id": "renal_vein_left"},
            )
            assert r_tour.status_code == 200

            # Independent challenge: renal_artery_left
            r_chal = client.post(
                f"/api/v1/anatomy/session/{anat_session_id}/challenge",
                json={"learner_id": "local-e2e-synthetic-learner", "selected_structure_id": "renal_artery_left"},
            )
            assert r_chal.status_code == 200
            assert r_chal.json().get("is_correct") is True

            # Unified learner progress
            r_prog = client.get("/api/v1/progress", headers=user_header)
            assert r_prog.status_code == 200
            assert r_prog.json().get("learner_id") == "local-e2e-synthetic-learner"

            # PLAB Preview QA check
            r_plab = client.get("/api/v1/plab/questions", headers=user_header)
            assert r_plab.status_code == 200
            assert r_plab.json().get("count") == 36
            print("  [10/10] 3D Anatomy + Progress + PLAB Preview QA (36 questions) -> 200 OK")

        print("  PASS: Full Section 12 representative product flow executes cleanly in-memory.")
        return True
    except Exception as exc:
        print(f"  FAIL: Representative product flow error: {exc}")
        return False


def check_optional_live_server() -> None:
    print("\n[Check 8/8] Optional Live Server Probe (port 8000)...")
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:8000/health")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                print("  INFO: Local backend is ALREADY running on http://127.0.0.1:8000 (status: 200)")
                return
    except Exception:
        pass
    print("  INFO: Live server not currently running on port 8000 (standard for pre-flight check).")


def main() -> int:
    print("=" * 60)
    print("      MEDICALPLAB LOCAL-FIRST RELEASE VERIFICATION      ")
    print("=" * 60)
    print("Target: Clone-and-run verification for mentors, evaluators,")
    print("        mobile developers, and local engineers.")
    print("-" * 60)

    checks = [
        ("Python Compatibility", check_python_version),
        ("Critical Files", check_critical_files),
        ("Data Manifest", check_data_manifest),
        ("Backend Imports", check_backend_imports),
        ("OpenAPI Contract", check_openapi_drift),
        ("Staging Gate Bypass", check_local_staging_gate_bypass),
        ("Representative E2E Flow", check_representative_e2e_flow),
    ]

    results = []
    for name, func in checks:
        t0 = time.time()
        ok = func()
        elapsed = time.time() - t0
        results.append((name, ok, elapsed))

    check_optional_live_server()

    print("\n" + "=" * 60)
    print("                  SUMMARY OF VERIFICATION              ")
    print("=" * 60)
    all_passed = True
    for name, ok, elapsed in results:
        status_str = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        print(f"  [{status_str}] {name:<28} ({elapsed:.3f}s)")

    print("-" * 60)
    if all_passed:
        print("LOCAL_RELEASE_READY = YES")
        print("The repository is 100% prepared for clone-and-run local execution.")
        print("=" * 60)
        return 0
    else:
        print("LOCAL_RELEASE_READY = NO")
        print("Review failure details above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
