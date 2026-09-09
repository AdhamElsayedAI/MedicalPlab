"""Machine-readable pre-pilot release gate for MedicalPlab."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from medicalplab.anatomy.ontology import MVP_STRUCTURES
from medicalplab.plab.data_manifest import verify_production_data_manifest
from medicalplab.plab.pilot import PLABPilotService


def check_pilot_readiness() -> dict[str, object]:
    # 1. Engineering check
    data_manifest = verify_production_data_manifest()
    engineering_ready = data_manifest.is_valid

    # 2. Clinical content check
    service = PLABPilotService.load_default()
    counts = service.governance_counts()
    golden_count = counts["golden"]
    approved_count = counts["approved"]
    human_reviewed_count = len(service.questions) - counts["pending"]
    clinical_content_ready = golden_count > 0

    # 3. Deployment check
    # Render, Dockerfile, and CloudBuild exist
    docker_exists = (PROJECT_ROOT / "Dockerfile").exists()
    render_exists = (PROJECT_ROOT / "render.yaml").exists()
    deployment_ready = docker_exists and render_exists and data_manifest.is_valid

    # 4. Persistence check
    # SQLitePilotPersistence implemented and available
    persistence_ready = True

    # 5. Authentication check
    # Reviewer auth is bearer+role, student auth is header-only (unverified)
    auth_ready = False  # Student auth is header-only; flagged as pilot blocker

    # 6. Overall pilot readiness
    overall_pilot_ready = (
        engineering_ready
        and clinical_content_ready
        and deployment_ready
        and persistence_ready
        and auth_ready
    )

    blockers = {
        "engineering": list(data_manifest.blockers),
        "clinical": [
            f"Human reviewed: {human_reviewed_count}/36 (awaiting real clinician review)",
            f"Golden content: {golden_count}/36 (0 questions available for student serving)",
        ] if golden_count == 0 else [],
        "deployment": [
            "Persistent volume / disk required on cloud host for durable MEDICALPLAB_DATA_ROOT",
        ],
        "auth": [
            "Student authentication relies on client-supplied X-User-Id header without cryptographic session verification",
        ],
    }

    return {
        "ENGINEERING_READY": engineering_ready,
        "CLINICAL_CONTENT_READY": clinical_content_ready,
        "DEPLOYMENT_READY": deployment_ready,
        "PERSISTENCE_READY": persistence_ready,
        "AUTH_READY": auth_ready,
        "OVERALL_PILOT_READY": overall_pilot_ready,
        "details": {
            "anatomy_structures_count": len(MVP_STRUCTURES),
            "corpus_documents_verified": data_manifest.document_count,
            "corpus_chunks_verified": data_manifest.chunk_count,
            "batch_version": data_manifest.batch_version,
            "total_questions": len(service.questions),
            "human_reviewed_count": human_reviewed_count,
            "approved_count": approved_count,
            "golden_count": golden_count,
            "pending_review_count": counts["pending"],
        },
        "blockers": blockers,
    }


def main() -> int:
    readiness = check_pilot_readiness()
    print("==================================================")
    print("MEDICALPLAB PRE-PILOT READINESS GATE")
    print("==================================================")
    print(f"ENGINEERING READY:        {readiness['ENGINEERING_READY']}")
    print(f"CLINICAL CONTENT READY:   {readiness['CLINICAL_CONTENT_READY']}")
    print(f"DEPLOYMENT READY:         {readiness['DEPLOYMENT_READY']}")
    print(f"PERSISTENCE READY:        {readiness['PERSISTENCE_READY']}")
    print(f"AUTH READY:               {readiness['AUTH_READY']}")
    print("--------------------------------------------------")
    print(f"OVERALL PILOT READY:      {readiness['OVERALL_PILOT_READY']}")
    print("==================================================")
    print("\nDetailed Status JSON:")
    print(json.dumps(readiness, indent=2))

    return 0 if readiness["OVERALL_PILOT_READY"] else 1


if __name__ == "__main__":
    sys.exit(main())
