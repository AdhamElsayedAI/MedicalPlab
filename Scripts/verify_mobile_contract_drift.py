#!/usr/bin/env python3
"""Automated OpenAPI contract drift verification for MedicalPlab.

Compares the live runtime OpenAPI specification generated from production_main.py
against the frozen reference specification in docs/mobile-handoff/openapi.json.

Exits with code 0 on perfect alignment; exits with code 1 if contract drift is detected.
This script does not mutate the repository.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def normalize_json(obj: Any) -> Any:
    """Recursively sort dict keys and lists of primitives for non-semantic comparison."""
    if isinstance(obj, dict):
        return {k: normalize_json(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        # Only sort lists of basic primitive scalars (strings/ints) where ordering is non-semantic
        if all(isinstance(item, (str, int, float, bool)) for item in obj):
            try:
                return sorted([normalize_json(item) for item in obj])
            except TypeError:
                pass
        return [normalize_json(item) for item in obj]
    return obj


def deep_diff(d1: Any, d2: Any, path: str = "") -> list[str]:
    """Identify semantic differences between two normalized data structures."""
    diffs: list[str] = []
    if type(d1) != type(d2):
        return [f"{path}: type mismatch ({type(d1).__name__} vs {type(d2).__name__})"]
    if isinstance(d1, dict):
        all_keys = sorted(set(d1.keys()) | set(d2.keys()))
        for k in all_keys:
            current_path = f"{path}.{k}" if path else k
            if k not in d1:
                diffs.append(f"{current_path}: missing in runtime specification")
            elif k not in d2:
                diffs.append(f"{current_path}: missing in saved reference specification")
            else:
                diffs.extend(deep_diff(d1[k], d2[k], current_path))
    elif isinstance(d1, list):
        if len(d1) != len(d2):
            diffs.append(f"{path}: list length mismatch ({len(d1)} in runtime vs {len(d2)} in saved)")
        else:
            for idx, (item1, item2) in enumerate(zip(d1, d2)):
                diffs.extend(deep_diff(item1, item2, f"{path}[{idx}]"))
    else:
        if d1 != d2:
            diffs.append(f"{path}: value mismatch ({d1!r} vs {d2!r})")
    return diffs


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)

    # Ensure python path includes src/ and repo root
    src_path = str(repo_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    # Enforce pilot runtime mode for inspection
    if not os.environ.get("MEDICALPLAB_RUNTIME_MODE"):
        os.environ["MEDICALPLAB_RUNTIME_MODE"] = "pilot"

    # Load frozen reference contract
    ref_path = repo_root / "docs" / "mobile-handoff" / "openapi.json"
    if not ref_path.exists():
        print(f"ERROR: Reference contract not found at {ref_path}", file=sys.stderr)
        return 1

    try:
        with open(ref_path, "r", encoding="utf-8") as f:
            saved_spec = json.load(f)
    except Exception as exc:
        print(f"ERROR: Failed to parse saved OpenAPI JSON: {exc}", file=sys.stderr)
        return 1

    # Generate live runtime specification from production FastAPI application
    try:
        from production_main import app
        runtime_spec = app.openapi()
    except Exception as exc:
        print(f"ERROR: Failed to import production_main or generate runtime OpenAPI: {exc}", file=sys.stderr)
        return 1

    runtime_norm = normalize_json(runtime_spec)
    saved_norm = normalize_json(saved_spec)

    diffs = deep_diff(runtime_norm, saved_norm)

    runtime_paths = len(runtime_spec.get("paths", {}))
    runtime_ops = sum(len(methods) for methods in runtime_spec.get("paths", {}).values())

    print("============================================================")
    print("      MEDICALPLAB OPENAPI CONTRACT DRIFT AUDIT")
    print("============================================================")
    print(f"  Reference Specification: {ref_path.relative_to(repo_root)}")
    print(f"  Runtime OpenAPI Version: {runtime_spec.get('openapi', 'unknown')}")
    print(f"  API Title & Version:     {runtime_spec.get('info', {}).get('title')} v{runtime_spec.get('info', {}).get('version')}")
    print(f"  Total API Endpoints:     {runtime_paths}")
    print(f"  Total Operations:        {runtime_ops}")
    print("------------------------------------------------------------")

    if diffs:
        print(f"FAILED: Detected {len(diffs)} meaningful contract drift issue(s):", file=sys.stderr)
        for diff in diffs[:25]:
            print(f"  - {diff}", file=sys.stderr)
        if len(diffs) > 25:
            print(f"  ... and {len(diffs) - 25} more differences.", file=sys.stderr)
        print("Contract verification failed. Update docs/mobile-handoff/openapi.json or revert runtime changes.", file=sys.stderr)
        return 1

    print("  RESULT: PERFECT CONTRACT ALIGNMENT (0 drift detected)")
    print("  RUNTIME_OPENAPI_MATCH = YES")
    print("============================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
