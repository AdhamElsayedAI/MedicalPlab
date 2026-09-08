"""Runtime-mode guardrails for Stage-G.

The project intentionally supports a demo mode for hackathon presentation data,
but pilot and production measurements must never fall back to fabricated AI,
clinical content, users, or telemetry.
"""

from __future__ import annotations

from enum import Enum
import os


class RuntimeMode(str, Enum):
    DEMO = "demo"
    TEST = "test"
    PILOT = "pilot"
    PRODUCTION = "production"


_ENV_NAME = "MEDICALPLAB_RUNTIME_MODE"
_DEMO_FALLBACK_MODES = {RuntimeMode.DEMO, RuntimeMode.TEST}
_STRICT_MODES = {RuntimeMode.PILOT, RuntimeMode.PRODUCTION}


def get_runtime_mode(value: str | RuntimeMode | None = None) -> RuntimeMode:
    """Resolve the active runtime mode.

    Defaults to ``demo`` for backwards compatibility with the existing
    hackathon UI. Pilot/production must be selected explicitly by environment.
    """
    if isinstance(value, RuntimeMode):
        return value

    raw = value if value is not None else os.environ.get(_ENV_NAME, RuntimeMode.DEMO.value)
    normalized = str(raw).strip().lower()

    try:
        return RuntimeMode(normalized)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in RuntimeMode)
        raise ValueError(
            f"Invalid {_ENV_NAME}={raw!r}. Expected one of: {allowed}."
        ) from exc


def demo_fallbacks_allowed(value: str | RuntimeMode | None = None) -> bool:
    """Return whether hard-coded/demo fallback behavior may be used."""
    return get_runtime_mode(value) in _DEMO_FALLBACK_MODES


def strict_runtime_enabled(value: str | RuntimeMode | None = None) -> bool:
    """Return True for pilot/production modes that must fail closed."""
    return get_runtime_mode(value) in _STRICT_MODES


def runtime_metadata(value: str | RuntimeMode | None = None) -> dict[str, object]:
    """Expose a small, safe runtime-status payload for health/version APIs."""
    mode = get_runtime_mode(value)
    return {
        "runtime_mode": mode.value,
        "demo_fallbacks_enabled": mode in _DEMO_FALLBACK_MODES,
        "strict_runtime": mode in _STRICT_MODES,
    }
