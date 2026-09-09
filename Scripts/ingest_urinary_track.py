"""Ingestion harness for the Urinary/Renal Course Learning Track."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

URINARY_RAW_DIR = PROJECT_ROOT / "Data" / "raw" / "urinary"
URINARY_PROCESSED_DIR = PROJECT_ROOT / "Data" / "processed" / "urinary"
SPEC_PATH = PROJECT_ROOT / "Data" / "metadata" / "urinary_track_specification.json"


def main() -> int:
    print("=" * 60)
    print("MEDICALPLAB URINARY/RENAL TRACK INGESTION PIPELINE")
    print("=" * 60)

    if not URINARY_RAW_DIR.exists() or not any(URINARY_RAW_DIR.iterdir()):
        print("\n[BLOCKED] URINARY_SOURCE_DATA = NOT AVAILABLE")
        print(f"Target raw directory '{URINARY_RAW_DIR}' does not contain any clinical PDFs.")
        if SPEC_PATH.exists():
            spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
            print(f"\nRequired Clinical Topics ({len(spec.get('required_clinical_topics', []))} topics):")
            for t in spec.get("required_clinical_topics", []):
                print(f"  - [{t.get('topic_id')}] {t.get('name')}: {t.get('target_guideline')}")
        print("\nPlease upload authorized course PDFs to Data/raw/urinary/ to execute ingestion.")
        return 1

    print("\nProcessing raw urinary PDFs...")
    # Ingestion pipeline logic for when documents are provided
    URINARY_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    raw_files = list(URINARY_RAW_DIR.glob("*.*"))
    print(f"Discovered {len(raw_files)} raw documents in {URINARY_RAW_DIR}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
