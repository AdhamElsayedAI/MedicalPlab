"""Configuration and feature flags for Phase 2B Socratic Remediation Engine."""
from __future__ import annotations

import os


def is_remediation_enabled() -> bool:
    """Check if Phase 2B remediation engine is enabled.

    Default is False to protect the frozen Phase 1 / Phase 2A production baseline.
    Can be enabled via environment variable:
        MEDICALPLAB_PHASE_2B_ENABLED=true (or '1', 'yes')
    """
    val = os.environ.get("MEDICALPLAB_PHASE_2B_ENABLED", "false").strip().lower()
    return val in ("1", "true", "yes", "enabled")
