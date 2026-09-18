#!/usr/bin/env python3
"""MedicalPlab Staging Warm-Up Utility.

Pre-warms the zero-cost Render Free staging instance (which spins down after inactivity)
before demonstrations, reviews, or mobile testing sessions (T-5 to T-10 min).

Sequence:
1. Public GET /health (unauthenticated probe to trigger spin-up wake)
2. Authenticated GET /ready (manifest and service readiness)
3. Authenticated GET /api/v1/version (API and contract verification)
4. Authenticated GET /api/v1/university/subjects (University curriculum)
5. Authenticated GET /api/v1/adaptive/state (synthetic learner check)

Usage:
    python Scripts/warm_staging.py --url https://medicalplab-staging.onrender.com --staging-key YOUR_KEY
    python Scripts/warm_staging.py --url http://localhost:8000 --staging-key dev-key
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any

try:
    import httpx
except ImportError:
    print("ERROR: httpx is required for warm_staging.py. Install via 'pip install httpx'.", file=sys.stderr)
    sys.exit(1)


def warm_staging(staging_url: str, staging_key: str, timeout: float = 90.0) -> bool:
    staging_url = staging_url.rstrip("/")
    is_local = staging_url.startswith(("http://localhost", "http://127.0.0.1"))
    if not is_local and not staging_url.startswith("https://"):
        print(f"ERROR: Non-local staging URL must use HTTPS for transport security: {staging_url}", file=sys.stderr)
        return False

    auth_headers = {
        "X-Staging-Key": staging_key,
        "X-User-Id": "synthetic-warmup-learner-001",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Step 1 does NOT send X-Staging-Key (mirrors Render platform probe & tests public health)
    steps: list[tuple[str, str, str, dict[str, str] | None, dict[str, Any] | None]] = [
        ("Step 1: Public Health Probe (Wake Trigger)", "GET", "/health", None, None),
        ("Step 2: Authenticated Service Ready", "GET", "/ready", auth_headers, None),
        ("Step 3: Contract Version Verification", "GET", "/api/v1/version", auth_headers, None),
        ("Step 4: University Subjects Catalog", "GET", "/api/v1/university/subjects", auth_headers, None),
        (
            "Step 5: Synthetic Learner Adaptive State",
            "GET",
            "/api/v1/adaptive/state?learner_id=synthetic-warmup-learner-001",
            auth_headers,
            None,
        ),
    ]

    print(f"=== MedicalPlab Render Staging Warm-Up Sequence ===")
    print(f"Staging URL: {staging_url}")
    print(f"Timeout: {timeout}s (allowing for spin-down cold starts)")
    print("-" * 60)

    all_passed = True
    cold_start_time = 0.0

    with httpx.Client(timeout=timeout) as client:
        for idx, (name, method, path, headers, payload) in enumerate(steps):
            target_endpoint = f"{staging_url}{path}"
            t0 = time.time()
            try:
                if method == "GET":
                    resp = client.get(target_endpoint, headers=headers)
                elif method == "POST":
                    resp = client.post(target_endpoint, headers=headers, json=payload)
                else:
                    raise ValueError(f"Unsupported method {method}")

                elapsed = time.time() - t0
                elapsed_ms = elapsed * 1000.0

                if idx == 0:
                    cold_start_time = elapsed

                if resp.status_code in (200, 201):
                    print(f"[{resp.status_code} OK] {name} ({elapsed:.2f}s) -> {path}")
                else:
                    print(
                        f"[{resp.status_code} FAIL] {name} ({elapsed:.2f}s) -> {path}: {resp.text[:120]}",
                        file=sys.stderr,
                    )
                    all_passed = False
            except Exception as exc:
                elapsed = time.time() - t0
                print(f"[ERR] {name} ({elapsed:.2f}s) -> {path}: {exc}", file=sys.stderr)
                all_passed = False

    print("-" * 60)
    print(f"RENDER_COLD_START_SECONDS = {cold_start_time:.2f}")

    if all_passed:
        print("Warm-up sequence completed SUCCESSFULLY. Staging service is warm and responsive.")
    else:
        print("Warm-up sequence encountered ERRORS. Review logs above.", file=sys.stderr)

    return all_passed


def main() -> None:
    parser = argparse.ArgumentParser(description="MedicalPlab Staging Warm-Up Script")
    parser.add_argument(
        "--url",
        "--staging-url",
        "--bff-url",
        dest="staging_url",
        default=(
            os.environ.get("MEDICALPLAB_STAGING_BASE_URL")
            or os.environ.get("RENDER_BASE_URL")
            or os.environ.get("BFF_BASE_URL")
            or "http://localhost:8000"
        ),
        help="Base URL of the MedicalPlab Render Staging Service",
    )
    parser.add_argument(
        "--staging-key",
        default=os.environ.get("STAGING_ACCESS_KEY", ""),
        help="X-Staging-Key value for staging authentication",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=90.0,
        help="HTTP request timeout in seconds (default: 90.0 to account for cold-start wake)",
    )

    args = parser.parse_args()

    if not args.staging_key:
        print("ERROR: --staging-key or STAGING_ACCESS_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)

    success = warm_staging(args.staging_url, args.staging_key, args.timeout)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
