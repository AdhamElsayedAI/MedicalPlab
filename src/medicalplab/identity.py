"""Canonical learner identity resolution across MedicalPlab modules.

Establishes a single external identity contract:
- Canonical HTTP Header: X-User-Id
- Backward-Compatible Header Alias: X-Learner-Id (used historically in 3D Anatomy)
- Query / Body fallback: learner_id or user_id

Provides a lightweight, zero-bloat resolver dependency for FastAPI routers.
"""
from __future__ import annotations

from typing import Optional
from fastapi import Header, HTTPException


def resolve_learner_id(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_learner_id: Optional[str] = Header(None, alias="X-Learner-Id"),
    fallback_id: Optional[str] = None,
    required: bool = True,
) -> str:
    """Extract and validate the canonical learner identity.

    Accepts X-User-Id as canonical, with X-Learner-Id as backward-compatible fallback.
    Raises HTTP 401 if identity is required but missing or blank.
    """
    candidate = (x_user_id or x_learner_id or fallback_id or "").strip()
    if not candidate:
        if required:
            raise HTTPException(
                status_code=401,
                detail={"code": "USER_ID_REQUIRED", "message": "X-User-Id header is required."},
            )
        return "anonymous_device"
    return candidate
