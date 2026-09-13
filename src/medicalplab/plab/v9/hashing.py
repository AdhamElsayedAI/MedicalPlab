"""Cross-platform deterministic hashing and newline canonicalization for PLAB V9.

Enforces:
1. raw_snapshot_hash_basis = "RAW_BYTES_SHA256"
2. normalized_representation_hash_basis = "UTF8_LF_CANONICAL_TEXT"
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Union


def compute_raw_bytes_sha256(data: bytes) -> str:
    """Compute SHA-256 digest of raw byte sequence without any transformation."""
    return hashlib.sha256(data).hexdigest()


def compute_file_raw_sha256(path: Path) -> str:
    """Compute raw byte SHA-256 digest directly from disk."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonicalize_newlines_to_lf(text: str) -> str:
    """Deterministically normalize CRLF and bare CR to LF."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def compute_canonical_lf_text_sha256(data: Union[bytes, str]) -> str:
    """Compute UTF8_LF_CANONICAL_TEXT SHA-256 digest.

    Algorithm:
    1. Read bytes (or encode input str as UTF-8)
    2. UTF-8 decode fail-closed
    3. Normalize CRLF -> LF
    4. Normalize bare CR -> LF
    5. Encode UTF-8
    6. SHA-256
    """
    if isinstance(data, str):
        text = data
    else:
        text = data.decode("utf-8")  # fail-closed on encoding errors

    canonical_text = canonicalize_newlines_to_lf(text)
    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


def compute_file_canonical_lf_sha256(path: Path) -> str:
    """Read file bytes, decode UTF-8 fail-closed, canonicalize newlines to LF, and hash."""
    raw_bytes = path.read_bytes()
    return compute_canonical_lf_text_sha256(raw_bytes)
