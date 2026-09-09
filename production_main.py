"""MedicalPlab pilot/production FastAPI entrypoint.

Unlike the legacy demo entrypoint, this module does not import seeded demo
platform data or hard-coded clinical answers. Unwired AI services fail closed.

Run with:
    MEDICALPLAB_RUNTIME_MODE=pilot uvicorn production_main:app --host 0.0.0.0 --port 8000
or:
    MEDICALPLAB_RUNTIME_MODE=production uvicorn production_main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from medicalplab.plab.pilot import PLABPilotService
from medicalplab.stage_g.product_api import configure_plab_service, router as product_router
from medicalplab.stage_g.runtime import get_runtime_mode, runtime_metadata, strict_runtime_enabled


RUNTIME_MODE = get_runtime_mode()
if not strict_runtime_enabled(RUNTIME_MODE):
    raise RuntimeError(
        "production_main.py requires MEDICALPLAB_RUNTIME_MODE=pilot or production. "
        "Use main.py for the backwards-compatible demo runtime."
    )

APP_START_TIME = time.time()


@asynccontextmanager
async def lifespan(_: FastAPI):
    preview = os.environ.get("MEDICALPLAB_PLAB_PREVIEW_QA", "").strip().lower() in {"1", "true", "yes"}
    try:
        configure_plab_service(PLABPilotService.load_default(preview_qa=preview))
    except PLABProductError:
        configure_plab_service(None)
    try:
        yield
    finally:
        configure_plab_service(None)

app = FastAPI(
    title="MedicalPlab Product API",
    description="Fail-closed MedicalPlab API for pilot and production clients",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
allowed_origins = [
    origin.strip()
    for origin in allowed_origins_env.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-User-Id", "X-Tenant-Id", "X-Request-Id"],
)

app.include_router(product_router)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "healthy",
        "service": "MedicalPlab Product API",
        "version": "1.1.0",
        "uptime_seconds": round(time.time() - APP_START_TIME, 2),
        **runtime_metadata(RUNTIME_MODE),
    }


@app.get("/")
def root() -> dict[str, object]:
    return {
        "service": "MedicalPlab Product API",
        "status": "healthy",
        "docs": "/docs",
        "health": "/health",
        "version_endpoint": "/api/v1/version",
        **runtime_metadata(RUNTIME_MODE),
    }
