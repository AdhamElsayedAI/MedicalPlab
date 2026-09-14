"""
PHASE 1 — Final Live Supported Path Verification (single-shot).

Makes exactly ONE live Gemini request through the full, unmodified
TutorService pipeline (real evidence engine, real Source Rights Gate, real
prompt assembly, real PropositionSegmenter, real TutorPostVerifier /
CentralClaimVerifier, real citation-provenance validation, real
answer-leakage scanner). No preliminary connectivity/model-list calls are
made. The provider/model/key are used exactly as configured by
GeminiGenerativeProvider's own defaults (GEMINI_API_KEY / GEMINI_MODEL env
vars), which are NOT overridden here.

Query is a single synthetic renal-physiology learner query, no PII, no real
learner history (no attempt_key -> PRE_SUBMISSION fail-closed default).
"""
from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from medicalplab.tutor.models import TutorChatRequest
from medicalplab.tutor.provider import GeminiGenerativeProvider
from medicalplab.tutor.service import TutorService


def main() -> None:
    provider = GeminiGenerativeProvider()  # uses GEMINI_API_KEY / GEMINI_MODEL env defaults, unmodified
    service = TutorService(provider=provider)

    session_id = f"synth-live-eval-{uuid.uuid4().hex[:8]}"
    req = TutorChatRequest(
        query=(
            "In the renin-angiotensin pathway, what substrate does active renin "
            "cleave to begin the cascade?"
        ),
        question_id="UNI-RENAL-001",
        mode="socratic_hint",
        session_id=session_id,
    )

    wall_start = time.perf_counter()
    res = service.chat(req, x_user_id="synth-live-eval-learner")
    wall_ms = (time.perf_counter() - wall_start) * 1000.0

    # Real input/output token usage exists internally on TutorTelemetryEvent (sourced from the
    # provider's own usageMetadata), but is NOT exposed on TutorChatResponse. Pull it from the
    # service's in-memory telemetry log immediately, before this process exits and it is lost.
    telemetry_events = service.telemetry.get_events()
    last_event = telemetry_events[-1] if telemetry_events else None

    forensic_records = [r.model_dump() for r in service.forensics.get_records()]

    data = res.model_dump()
    data["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    data["wall_total_ms"] = round(wall_ms, 2)
    data["forensic_records"] = forensic_records

    out_dir = ROOT_DIR / "reports" / "product"
    out_dir.mkdir(parents=True, exist_ok=True)

    call_record_path = out_dir / "live_supported_call_record.json"
    call_record_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    result_path = out_dir / "live_supported_result.json"
    result_summary = {
        "timestamp": data["timestamp"],
        "requested_provider": res.requested_provider,
        "requested_model": res.requested_model,
        "actual_generation_provider": res.actual_generation_provider,
        "actual_generation_model": res.actual_generation_model,
        "provider_failover_applied": res.provider_failover_applied,
        "primary_provider_error": res.primary_provider_error,
        "provider": res.provider,
        "model": res.model,
        "support_status": res.support_status,
        "fallback_applied": res.fallback_applied,
        "abstain": res.abstain,
        "citations_count": len(res.citations),
        "citations": [c.model_dump() for c in res.citations],
        "served_verification": res.verification.model_dump(),
        "draft_verification": res.draft_verification.model_dump() if res.draft_verification else None,
        "message": res.message,
        "latency_breakdown": res.latency_breakdown.model_dump(),
        "input_tokens": last_event.input_tokens if last_event else None,
        "output_tokens": last_event.output_tokens if last_event else None,
        "token_usage_status": "CAPTURED" if last_event and (last_event.input_tokens or last_event.output_tokens) else "NOT_AVAILABLE",
        "forensic_records": forensic_records,
        "wall_total_ms": round(wall_ms, 2),
    }
    result_path.write_text(json.dumps(result_summary, indent=2, default=str), encoding="utf-8")

    print("LIVE_RESULT_JSON=" + json.dumps(result_summary))


if __name__ == "__main__":
    main()
