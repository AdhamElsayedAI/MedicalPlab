"""Feature flag configuration for MedicalPlab Generative 3D Anatomy."""
from __future__ import annotations

import os


def is_anatomy_enabled() -> bool:
    """Return True if the 3D Anatomy engine is enabled by feature flag.

    Environment variable: MEDICALPLAB_ANATOMY_3D_ENABLED
    Default: False (fails closed in production unless explicitly enabled)
    """
    flag = os.environ.get("MEDICALPLAB_ANATOMY_3D_ENABLED", "false").strip().lower()
    return flag in ("true", "1", "yes", "enabled", "on")
