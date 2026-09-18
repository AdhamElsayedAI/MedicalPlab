"""Bootstrap public-safe local runtime assets for clone-and-run execution.

Zero external dependencies, zero unverified clinical corpora.
Uses strictly public CC BY 4.0 validation fixtures.
"""
from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from tests.plab.fixture_helper import build_test_data_root  # noqa: E402
from medicalplab.plab.data_manifest import verify_production_data_manifest  # noqa: E402


def bootstrap_local_data(target_dir: Path | None = None) -> bool:
    target = target_dir or (PROJECT_ROOT / "Data")
    report = verify_production_data_manifest(target)
    if not report.is_valid:
        print(f"Bootstrapping public-safe local data assets into {target}...")
        try:
            build_test_data_root(target)
            report = verify_production_data_manifest(target)
            if not report.is_valid:
                print(f"ERROR: Bootstrapping failed: {report.blockers}")
                return False
            print(f"SUCCESS: Populated {report.chunk_count} CC BY 4.0 validation chunks and taxonomy.")
        except Exception as exc:
            print(f"ERROR: Could not bootstrap local data: {exc}")
            return False
    else:
        print(f"Local data root at {target} already satisfies manifest ({report.chunk_count} chunks).")
    return True


if __name__ == "__main__":
    success = bootstrap_local_data()
    sys.exit(0 if success else 1)
