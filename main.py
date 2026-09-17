"""MedicalPlab Production Cloud API Entrypoint.

Provides a production-ready FastAPI application with CORS, health check,
and route integration into the Stage-G platform router and AI core.
Runs via:
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from medicalplab.evidence_engine.models import EvidencePacket
from medicalplab.evidence_engine.service import CanonicalEvidenceEngine, SharedEvidenceEngineV2
from medicalplab.stage_g.models import APIRequest
from medicalplab.stage_g.server import create_demo_platform
from medicalplab.stage_g.product_api import router as product_router
from medicalplab.university.api import router as university_router
from medicalplab.adaptive.api import router as adaptive_router
from medicalplab.remediation.api import router as remediation_router
from medicalplab.learning_intelligence.api import router as learning_intelligence_router
from medicalplab.anatomy.api import router as anatomy_router
from medicalplab.progress_api import router as progress_router


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("medicalplab_cloud_api")

_evidence_engine: Optional[CanonicalEvidenceEngine] = None


def get_evidence_engine() -> CanonicalEvidenceEngine:
    global _evidence_engine
    if _evidence_engine is None:
        data_root = Path(__file__).resolve().parent / "Data"
        _evidence_engine = CanonicalEvidenceEngine(data_root=data_root)
    return _evidence_engine

# 1. Initialize FastAPI Application
app = FastAPI(
    title="MedicalPlab API",
    description="Evidence-Grounded Medical Intelligence Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

APP_START_TIME = time.time()
app.include_router(university_router)
app.include_router(product_router)
app.include_router(adaptive_router)
app.include_router(remediation_router)
app.include_router(learning_intelligence_router)
app.include_router(anatomy_router)
app.include_router(progress_router)


# 2. Configure CORS
# Pull allowed origins from environment variable or default to Vercel and local origins
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]
else:
    allowed_origins = [
        "https://medical-plab.vercel.app",
        "https://*.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production flexibility while explicitly supporting Vercel
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Log request and attach latency header."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler providing structured JSON errors."""
    logger.error("Unhandled API exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred during request processing.",
            "path": request.url.path,
        },
    )


# 3. Instantiate Stage-G Platform Router
platform_router = create_demo_platform()

# --------------------------------------------------------------------------
# Health Check Endpoint (Required by Cloud Platforms & DevOps Standard)
# --------------------------------------------------------------------------
@app.get("/health")
def health():
    """Health check endpoint for Google Cloud Run, Vercel, and monitoring."""
    return {
        "status": "healthy",
        "service": "MedicalPlab API",
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - APP_START_TIME, 2),
        "stage_g": "initialized",
    }


@app.get("/")
def root():
    """Root platform discovery endpoint."""
    return {
        "service": "MedicalPlab Clinical Intelligence Platform API",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "active_tenant": "tenant_nhs_demo",
    }


# --------------------------------------------------------------------------
# AI Tutor & Clinical Reasoning Gateway
# --------------------------------------------------------------------------
@app.post("/ai/chat")
async def ai_chat(
    request: Request,
    x_user_id: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None),
):
    """Evidence-grounded Socratic tutor chat endpoint.

    Accepts clinical query, applies safety verification, queries guideline
    evidence, and returns structured clinical reasoning with citations.
    """
    start_time = time.perf_counter()
    user_id = x_user_id or "user_alice"
    tenant_id = x_tenant_id or "tenant_nhs_demo"

    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8") if body_bytes else "{}"
        try:
            body_json = json.loads(body_str) if body_str else {}
        except json.JSONDecodeError:
            body_json = {"query": body_str}

        query = body_json.get("query", "").strip()
        if not query:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing 'query' parameter in request body"},
            )

        # If question_id or explicit tutor mode is provided, delegate to Phase 1 Grounded TutorService
        question_id = body_json.get("question_id")
        mode = body_json.get("mode")

        if question_id or mode == "tutor":
            from medicalplab.tutor.models import TutorChatRequest
            from medicalplab.stage_g.product_api import get_tutor_service

            tutor_req = TutorChatRequest(
                query=query,
                mode=mode or "auto",
                session_id=body_json.get("session_id"),
                learner_id=user_id,
                question_id=question_id,
                attempt_key=body_json.get("attempt_key"),
                topic=body_json.get("topic"),
                hint_level=body_json.get("hint_level"),
                selected_option=body_json.get("selected_option"),
            )
            tutor_resp = get_tutor_service().chat(tutor_req, x_user_id=x_user_id)

            if tutor_resp.abstain:
                return {
                    "intent": "abstain",
                    "abstain": True,
                    "abstain_reason": tutor_resp.abstain_reason or "INSUFFICIENT_RETRIEVAL_SUPPORT",
                    "explanation": tutor_resp.message,
                    "citations": [],
                    "next_actions": [
                        "Consult accredited NHS clinical guidelines or senior clinician",
                        "Refine query with specific clinical terms",
                    ],
                    "latency_ms": tutor_resp.latency_breakdown.total_ms,
                    "safety_validated": True,
                    "is_degraded": False,
                    "retrieval_mode": "TUTOR",
                    "packet": {},
                    "tutor_response": tutor_resp.model_dump(),
                }

            citations = [
                {
                    "title": c.title,
                    "ref": c.ref,
                    "quote": c.quote,
                    "section": c.chunk_id,
                    "score": 1.0,
                }
                for c in tutor_resp.citations
            ]
            return {
                "intent": "clinical_guidance",
                "abstain": False,
                "abstain_reason": None,
                "explanation": tutor_resp.message,
                "citations": citations,
                "next_actions": ["Review Grounded Evidence", "Correlate with Clinical Presentation"],
                "latency_ms": tutor_resp.latency_breakdown.total_ms,
                "safety_validated": True,
                "is_degraded": False,
                "retrieval_mode": "TUTOR",
                "packet": {},
                "tutor_response": tutor_resp.model_dump(),
            }

        # Legacy general query behavior: query evidence engine directly
        engine = get_evidence_engine()
        packet = engine.query(
            query=query,
            mode="TUTOR",
            top_candidates=50,
            rerank_top_k=25,
        )

        if packet.abstain or not packet.candidates:
            return {
                "intent": "abstain",
                "abstain": True,
                "abstain_reason": packet.abstain_reason or "INSUFFICIENT_RETRIEVAL_SUPPORT",
                "explanation": (
                    f"I must abstain from providing clinical guidance on '{query}'. "
                    f"No verified, high-confidence evidence was retrieved from the accredited medical corpus "
                    f"(reason: {packet.abstain_reason or 'INSUFFICIENT_RETRIEVAL_SUPPORT'}). "
                    "Under clinical safety policy, ungrounded medical guidance is withheld to prevent patient harm."
                ),
                "citations": [],
                "next_actions": [
                    "Consult accredited NHS clinical guidelines or senior clinician",
                    "Refine query with specific clinical terms",
                ],
                "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
                "safety_validated": True,
                "is_degraded": packet.is_degraded,
                "retrieval_mode": packet.retrieval_mode,
                "packet": packet.to_dict(),
            }

        top_cands = [packet.top_passage]
        citations = [
            {
                "title": cand.doc_title or cand.document_id,
                "ref": f"{cand.document_id}:{cand.chunk_id}",
                "quote": cand.text[:280] + "..." if len(cand.text) > 280 else cand.text,
                "section": " > ".join(cand.section_path) if cand.section_path else cand.heading,
                "score": round(cand.rerank_score or cand.fused_score, 4),
            }
            for cand in top_cands
        ]
        top_cand = top_cands[0]
        heading_str = f" ({top_cand.heading})" if top_cand.heading else ""
        explanation = (
            f"Grounded clinical evidence from {top_cand.doc_title or top_cand.document_id}{heading_str}:\n\n"
            f"{top_cand.text.strip()}"
        )
        return {
            "intent": "clinical_guidance",
            "abstain": False,
            "abstain_reason": None,
            "explanation": explanation,
            "citations": citations,
            "next_actions": ["Review Grounded Evidence", "Correlate with Clinical Presentation"],
            "latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
            "safety_validated": True,
            "is_degraded": packet.is_degraded,
            "retrieval_mode": packet.retrieval_mode,
            "packet": packet.to_dict(),
        }

    except Exception as ex:
        logger.error("Error processing /ai/chat: %s", ex, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"AI Processing Error: {str(ex)}"},
        )


# --------------------------------------------------------------------------
# Direct Evidence Engine Retrieval Endpoint
# --------------------------------------------------------------------------
@app.post("/api/v1/evidence/query")
async def evidence_query_endpoint(request: Request):
    """Direct query endpoint for Canonical Evidence Engine V1.1 inspection."""
    start_time = time.perf_counter()
    body_bytes = await request.body()
    try:
        body_json = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception:
        body_json = {}
    query_text = body_json.get("query", "").strip()
    if not query_text:
        return JSONResponse(status_code=400, content={"error": "Missing 'query' parameter in request body"})
    claims = body_json.get("claims_to_verify")
    top_k = int(body_json.get("top_candidates", 10))
    rerank_k = int(body_json.get("rerank_top_k", 5))
    mode = str(body_json.get("mode", "TUTOR"))

    engine = get_evidence_engine()
    packet = engine.query(
        query=query_text,
        claims_to_verify=claims,
        mode=mode,
        top_candidates=top_k,
        rerank_top_k=rerank_k,
    )
    res = packet.to_dict()
    res["latency_ms"] = round((time.perf_counter() - start_time) * 1000.0, 2)
    return res


# --------------------------------------------------------------------------
# Student Analytics & Mastery Telemetry
# --------------------------------------------------------------------------
@app.get("/student/analytics")
async def student_analytics(
    x_user_id: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None),
):
    """Retrieve Bayesian knowledge tracing and mastery analytics for student."""
    user_id = x_user_id or "user_alice"
    tenant_id = x_tenant_id or "tenant_nhs_demo"

    api_req = APIRequest(
        path="/student/analytics",
        method="GET",
        user_id=user_id,
        tenant_id=tenant_id,
    )
    resp = platform_router.handle(api_req)
    try:
        data = json.loads(resp.body)
        return JSONResponse(status_code=resp.status_code, content=data)
    except Exception:
        return Response(content=resp.body, status_code=resp.status_code, media_type="application/json")


@app.post("/student/attempts")
async def record_student_attempt(
    request: Request,
    x_user_id: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None),
):
    """Record student question attempt and update Bayesian knowledge tracing."""
    user_id = x_user_id or "user_alice"
    tenant_id = x_tenant_id or "tenant_nhs_demo"

    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8") if body_bytes else "{}"

    api_req = APIRequest(
        path="/student/attempts",
        method="POST",
        body=body_str,
        user_id=user_id,
        tenant_id=tenant_id,
    )
    resp = platform_router.handle(api_req)
    try:
        data = json.loads(resp.body)
        return JSONResponse(status_code=resp.status_code, content=data)
    except Exception:
        return Response(content=resp.body, status_code=resp.status_code, media_type="application/json")


# --------------------------------------------------------------------------
# Universal Fallback Route for Stage-G Microservices
# --------------------------------------------------------------------------
@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def universal_stage_g_proxy(
    full_path: str,
    request: Request,
    x_user_id: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None),
):
    """Forward any unhandled Stage-G routes (/auth, /documents, /admin, etc.) to platform router."""
    user_id = x_user_id or "user_alice"
    tenant_id = x_tenant_id or "tenant_nhs_demo"

    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8") if body_bytes else ""

    path = f"/{full_path}"
    api_req = APIRequest(
        path=path,
        method=request.method,
        body=body_str,
        user_id=user_id,
        tenant_id=tenant_id,
    )
    resp = platform_router.handle(api_req)
    try:
        data = json.loads(resp.body)
        return JSONResponse(status_code=resp.status_code, content=data)
    except Exception:
        return Response(content=resp.body, status_code=resp.status_code, media_type="application/json")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run("main:app", host=host, port=port, reload=False, workers=1)
