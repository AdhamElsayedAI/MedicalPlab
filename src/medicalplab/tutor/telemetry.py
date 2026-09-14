"""Telemetry schemas and logging for Grounded Generative Tutor."""
from __future__ import annotations

import datetime
import logging
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Official vendor pricing rates per 1M tokens (September 2026 baseline)
# Gemini 3.8 Flash introductory rate: $0.75 / 1M in, $3.75 / 1M out
GEMINI_COST_PER_M_IN = 0.75
GEMINI_COST_PER_M_OUT = 3.75
# OpenAI GPT-5.6 Luna: $0.20 / 1M in, $1.20 / 1M out
OPENAI_COST_PER_M_IN = 0.20
OPENAI_COST_PER_M_OUT = 1.20


class TutorTelemetryEvent(BaseModel):
    request_id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    session_id: str
    learner_id: str
    question_id: str | None = None
    topic: str
    pedagogical_state: str  # "PRE_SUBMISSION" | "POST_SUBMISSION" | "GENERAL_STUDY"
    mode: str
    evidence_status: str  # "SUPPORTED" | "ABSTAIN"
    abstain_reason: str | None = None
    provider: str
    model: str
    requested_model: str = ""
    provider_failover_applied: bool = False
    primary_provider_error: str | None = None
    latency_retrieval_ms: float = 0.0
    latency_ttft_ms: float | None = None
    latency_generation_ms: float = 0.0
    latency_post_verify_ms: float = 0.0
    latency_total_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    propositions_total: int = 0
    propositions_supported: int = 0
    propositions_unsupported: int = 0
    fallback_applied: bool = False


class TutorTelemetryLogger:
    """Collects and snapshots runtime telemetry for evaluation and monitoring."""

    def __init__(self) -> None:
        self._events: list[TutorTelemetryEvent] = []

    def calculate_cost(self, provider: str, input_tokens: int, output_tokens: int) -> float:
        if "gemini" in provider.lower():
            cost = (input_tokens / 1_000_000.0) * GEMINI_COST_PER_M_IN + (output_tokens / 1_000_000.0) * GEMINI_COST_PER_M_OUT
        elif "openai" in provider.lower():
            cost = (input_tokens / 1_000_000.0) * OPENAI_COST_PER_M_IN + (output_tokens / 1_000_000.0) * OPENAI_COST_PER_M_OUT
        else:
            cost = 0.0
        return round(cost, 6)

    def log_event(self, event: TutorTelemetryEvent) -> None:
        self._events.append(event)
        logger.info(
            f"TutorTelemetry: req={event.request_id} state={event.pedagogical_state} "
            f"status={event.evidence_status} latency={event.latency_total_ms:.1f}ms "
            f"props={event.propositions_supported}/{event.propositions_total}"
        )

    def get_events(self) -> list[TutorTelemetryEvent]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()
