#!/usr/bin/env python3
"""MedicalPlab Staging Warm-Up Utility.

Pre-warms the zero-cost Cloud Run staging instances (min-instances=0)
before demonstrations, reviews, or mobile testing sessions (T-10 min).

Sequence:
1. BFF /health
2. BFF -> backend /ready
3. /api/v1/version
4. University subjects (/api/v1/university/subjects)
5. One synthetic learner request (/api/v1/adaptive/state?learner_id=synthetic-warmup-001)

Usage:
    python Scripts/warm_staging.py --bff-url https://medicalplab-bff-xxx.europe-west1.run.app --staging-key YOUR_KEY
    python Scripts/warm_staging.py --bff-url http://localhost:8080 --staging-key dev-key
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


def warm_staging(bff_url: str, staging_key: str, timeout: float = 30.0) -> bool:
    bff_url = bff_url.rstrip("/")
    is_local = bff_url.startswith(("http://localhost", "http://127.0.0.1"))
    if not is_local and not bff_url.startswith("https://"):
        print(f"ERROR: Non-local BFF URL must use HTTPS for transport security: {bff_url}", file=sys.stderr)
        return False
    headers = {
        "X-Staging-Key": staging_key,
        "X-User-Id": "synthetic-warmup-learner-001",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    steps: list[tuple[str, str, str, dict[str, Any] | None]] = [
        ("Step 1: BFF Health", "GET", "/health", None),
        ("Step 2: Backend Ready", "GET", "/ready", None),
        ("Step 3: Contract Version", "GET", "/api/v1/version", None),
        ("Step 4: University Subjects", "GET", "/api/v1/university/subjects", None),
        (
            "Step 5: Synthetic Learner State",
            "GET",
            "/api/v1/adaptive/state?learner_id=synthetic-warmup-learner-001",
            None,
        ),
    ]

    print(f"=== MedicalPlab Staging Warm-Up Sequence ===")
    print(f"BFF Target URL: {bff_url}")
    print(f"Timeout: {timeout}s")
    print("-" * 50)

    all_passed = True
    with httpx.Client(timeout=timeout) as client:
        for name, method, path, payload in steps:
            target_endpoint = f"{bff_url}{path}"
            t0 = time.time()
            try:
                if method == "GET":
                    resp = client.get(target_endpoint, headers=headers)
                elif method == "POST":
                    resp = client.post(target_endpoint, headers=headers, json=payload)
                else:
                    raise ValueError(f"Unsupported method {method}")

                elapsed_ms = (time.time() - t0) * 1000.0
                if resp.status_code in (200, 201):
                    print(f"[{resp.status_code} OK] {name} ({elapsed_ms:.1f}ms) -> {path}")
                else:
                    print(
                        f"[{resp.status_code} FAIL] {name} ({elapsed_ms:.1f}ms) -> {path}: {resp.text[:120]}",
                        file=sys.stderr,
                    )
                    all_passed = False
            except Exception as exc:
                elapsed_ms = (time.time() - t0) * 1000.0
                print(f"[ERR] {name} ({elapsed_ms:.1f}ms) -> {path}: {exc}", file=sys.stderr)
                all_passed = False

    print("-" * 50)
    if all_passed:
        print("Warm-up sequence completed SUCCESSFULLY. Instances are active.")
    else:
        print("Warm-up sequence encountered ERRORS. Review logs above.", file=sys.stderr)

    return all_passed


def main() -> None:
    parser = argparse.ArgumentParser(description="MedicalPlab Staging Warm-Up Script")
    parser.add_argument(
        "--bff-url",
        default=os.environ.get("BFF_BASE_URL", "http://localhost:8080"),
        help="Base URL of the Staging BFF Gateway",
    )
    parser.add_argument(
        "--staging-key",
        default=os.environ.get("STAGING_ACCESS_KEY", ""),
        help="X-Staging-Key value for gateway authentication",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP request timeout in seconds (default: 30.0)",
    )

    args = parser.parse_args()

    if not args.staging_key:
        print("ERROR: --staging-key or STAGING_ACCESS_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)

    success = warm_staging(args.bff_url, args.staging_key, args.timeout)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
