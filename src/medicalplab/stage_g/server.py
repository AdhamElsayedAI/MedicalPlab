"""High-performance HTTP REST Server for Stage-G.

Provides a zero-dependency HTTP server wrapping PlatformAPIRouter,
enabling direct connection from Next.js / React frontends.
Includes CORS handling and initial seed data for startup demos.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
import sys
import time
from typing import Any
import urllib.parse

from medicalplab.stage_g.analytics import PlatformAnalyticsService
from medicalplab.stage_g.api import PlatformAPIRouter
from medicalplab.stage_g.audit import AuditService
from medicalplab.stage_g.database import DatabaseService
from medicalplab.stage_g.gateway import AIGateway
from medicalplab.stage_g.knowledge_management import MedicalKnowledgeManager
from medicalplab.stage_g.models import (
    APIRequest,
    DocumentStage,
    SubscriptionTier,
    Tenant,
    UserRecord,
    UserRole,
)
from medicalplab.stage_g.multitenancy import MultiTenancyService
from medicalplab.stage_g.security import SecurityService
from medicalplab.stage_g.usage import AIUsageTracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("stage_g_server")


def create_demo_platform() -> PlatformAPIRouter:
    """Instantiate a fully configured Stage-G platform router seeded with demo data."""
    db = DatabaseService()
    security = SecurityService()
    multitenancy = MultiTenancyService(db)
    audit = AuditService(db)
    usage = AIUsageTracker(db)
    knowledge = MedicalKnowledgeManager(db, audit)
    analytics = PlatformAnalyticsService(db)
    gateway = AIGateway(db, security, usage, audit)

    # 1. Seed Tenants
    nhs_tenant = multitenancy.create_tenant(
        name="NHS Imperial College Healthcare Trust",
        tenant_id="tenant_nhs_demo",
        tier=SubscriptionTier.INSTITUTION,
    )

    # 2. Seed Organizations
    cardio_org = multitenancy.create_organization(
        tenant_id=nhs_tenant.tenant_id,
        name="Cardiothoracic Medicine & Intensive Care",
        org_id="org_cardio",
    )

    # 3. Seed Users
    student_alice = UserRecord(
        user_id="user_alice",
        tenant_id=nhs_tenant.tenant_id,
        email="alice.vance@nhs.net",
        name="Dr. Alice Vance (PLAB 1 Candidate)",
        role=UserRole.STUDENT,
        tier=SubscriptionTier.PREMIUM,
        created_at=time.time(),
    )
    db.users.create(student_alice)
    multitenancy.assign_membership(
        user_id=student_alice.user_id,
        org_id=cardio_org.org_id,
        tenant_id=nhs_tenant.tenant_id,
        role="TRAINEE",
    )

    doctor_chen = UserRecord(
        user_id="user_chen",
        tenant_id=nhs_tenant.tenant_id,
        email="robert.chen@nhs.net",
        name="Dr. Robert Chen (Consultant Cardiologist)",
        role=UserRole.DOCTOR,
        tier=SubscriptionTier.PREMIUM,
        created_at=time.time(),
    )
    db.users.create(doctor_chen)

    admin_bennett = UserRecord(
        user_id="user_bennett",
        tenant_id=nhs_tenant.tenant_id,
        email="elizabeth.bennett@imperial.nhs.uk",
        name="Prof. Elizabeth Bennett (Dean of Academic Training)",
        role=UserRole.INSTITUTION_ADMIN,
        tier=SubscriptionTier.INSTITUTION,
        created_at=time.time(),
    )
    db.users.create(admin_bennett)

    # 4. Seed Clinical Guidelines in Knowledge Base
    doc1 = knowledge.upload_document(
        tenant_id=nhs_tenant.tenant_id,
        owner_id=admin_bennett.user_id,
        title="NICE Guideline NG185: Acute Coronary Syndromes Management",
        file_path="/storage/nice_ng185.pdf",
        file_size_bytes=2457600,
        mime_type="application/pdf",
        source="NICE UK",
    )
    # Advance to AVAILABLE state
    knowledge.advance_stage(doc1.doc_id, nhs_tenant.tenant_id, DocumentStage.VALIDATION)
    knowledge.advance_stage(doc1.doc_id, nhs_tenant.tenant_id, DocumentStage.EXTRACTION)
    knowledge.advance_stage(doc1.doc_id, nhs_tenant.tenant_id, DocumentStage.CLEANING)
    knowledge.advance_stage(doc1.doc_id, nhs_tenant.tenant_id, DocumentStage.INDEXING)
    knowledge.advance_stage(doc1.doc_id, nhs_tenant.tenant_id, DocumentStage.AVAILABLE)

    # 5. Seed Initial Student Diagnostic Attempts
    topics_seed = [
        ("Cardiology", True),
        ("Cardiology", True),
        ("Cardiology", False),
        ("Neurology", True),
        ("Pharmacology", False),
        ("Pharmacology", False),
        ("Emergency Medicine", True),
    ]
    for topic, correct in topics_seed:
        db.attempts.record({
            "attempt_id": f"att_seed_{time.time()}",
            "student_id": student_alice.user_id,
            "tenant_id": nhs_tenant.tenant_id,
            "topic": topic,
            "is_correct": correct,
            "time_spent_seconds": 32.5,
        })

    return PlatformAPIRouter(
        db=db,
        security=security,
        multitenancy=multitenancy,
        knowledge=knowledge,
        analytics=analytics,
        gateway=gateway,
        audit=audit,
    )


class PlatformHTTPHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler wrapping the Stage-G PlatformAPIRouter."""

    router: PlatformAPIRouter | None = None

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Tenant-Id, X-User-Id")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PUT(self):
        self._dispatch("PUT")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def _dispatch(self, method: str):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else ""

        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        headers_list = [(k, v) for k, v in self.headers.items()]
        user_id = self.headers.get("X-User-Id")
        tenant_id = self.headers.get("X-Tenant-Id")

        # Fallback to demo user if not supplied
        if not user_id:
            user_id = "user_alice"
        if not tenant_id:
            tenant_id = "tenant_nhs_demo"

        req = APIRequest(
            path=path,
            method=method,
            headers=tuple(headers_list),
            body=body,
            user_id=user_id,
            tenant_id=tenant_id,
        )

        try:
            assert self.router is not None
            resp = self.router.handle(req)

            self.send_response(resp.status_code)
            self._set_cors_headers()
            for k, v in resp.headers:
                self.send_header(k, v)
            if not any(k.lower() == "content-type" for k, _ in resp.headers):
                self.send_header("Content-Type", "application/json")
            self.end_headers()

            self.wfile.write(resp.body.encode("utf-8"))
        except Exception as ex:
            logger.error("HTTP dispatch error: %s", ex, exc_info=True)
            self.send_response(500)
            self._set_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            err_json = json.dumps({"error": f"Internal Server Error: {type(ex).__name__} - {str(ex)}"})
            self.wfile.write(err_json.encode("utf-8"))


def run_server(port: int = 8000):
    """Run HTTP server on specified port."""
    router = create_demo_platform()
    PlatformHTTPHandler.router = router
    server_address = ("", port)
    httpd = HTTPServer(server_address, PlatformHTTPHandler)
    logger.info("MedicalPlab Stage-G Server listening on port %d...", port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server terminated.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
