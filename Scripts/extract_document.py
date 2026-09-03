import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pdfplumber


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MANIFEST_PATH = (
    PROJECT_ROOT
    / "Data"
    / "metadata"
    / "document_manifest.json"
)

RAW_DIR = PROJECT_ROOT / "Data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "Data" / "processed"


def load_manifest() -> list[dict[str, Any]]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Document manifest must be a JSON array."
        )

    return data


def find_document(
    manifest: list[dict[str, Any]],
    document_id: str,
) -> dict[str, Any]:
    for document in manifest:
        if document.get("document_id") == document_id:
            return document

    raise ValueError(
        f"Unknown document_id: {document_id}"
    )


def normalize_folder_name(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def verify_source_file(
    path: Path,
    expected_sha256: str | None,
) -> str:
    if not path.exists():
        raise FileNotFoundError(
            f"Source PDF not found: {path}"
        )

    if path.stat().st_size < 10_000:
        raise ValueError(
            "Source PDF is unexpectedly small."
        )

    with path.open("rb") as file:
        signature = file.read(5)

    if signature != b"%PDF-":
        raise ValueError(
            "Source file is not a valid PDF."
        )

    actual_sha256 = calculate_sha256(path)

    if expected_sha256:
        if actual_sha256.lower() != expected_sha256.lower():
            raise ValueError(
                "SHA-256 mismatch. "
                "The source PDF may have changed."
            )

    return actual_sha256


def clean_page_text(text: str | None) -> str:
    """
    Conservative cleaning only.

    Medical content must not be rewritten or summarized here.
    """
    if not text:
        return ""

    # Normalize non-breaking spaces.
    text = text.replace("\u00a0", " ")

    # Remove excessive horizontal whitespace.
    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    # Normalize excessive blank lines.
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def extract_pdf(
    path: Path,
) -> tuple[list[dict[str, Any]], int]:
    pages: list[dict[str, Any]] = []

    with pdfplumber.open(path) as pdf:
        page_count = len(pdf.pages)

        for page_number, page in enumerate(
            pdf.pages,
            start=1,
        ):
            raw_text = page.extract_text()

            clean_text = clean_page_text(
                raw_text
            )

            pages.append(
                {
                    "page_number": page_number,
                    "text": clean_text,
                    "character_count": len(clean_text),
                    "has_text": bool(clean_text),
                }
            )

    return pages, page_count


def build_quality_report(
    document_id: str,
    pages: list[dict[str, Any]],
    page_count: int,
) -> dict[str, Any]:
    pages_with_text = sum(
        1
        for page in pages
        if page["has_text"]
    )

    empty_pages = (
        page_count - pages_with_text
    )

    total_characters = sum(
        page["character_count"]
        for page in pages
    )

    text_coverage = (
        pages_with_text / page_count
        if page_count
        else 0.0
    )

    average_characters = (
        total_characters / page_count
        if page_count
        else 0.0
    )

    # Conservative first-pass quality gate.
    passed = (
        page_count > 0
        and text_coverage >= 0.80
        and total_characters >= 5000
    )

    return {
        "document_id": document_id,
        "quality_status": (
            "pass"
            if passed
            else "needs_review"
        ),
        "page_count": page_count,
        "pages_with_text": pages_with_text,
        "empty_pages": empty_pages,
        "text_coverage": round(
            text_coverage,
            4,
        ),
        "total_characters": total_characters,
        "average_characters_per_page": round(
            average_characters,
            2,
        ),
    }


def save_json(
    path: Path,
    data: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extract and quality-check "
            "a governed MedicalPlab PDF."
        )
    )

    parser.add_argument(
        "document_id",
        help="Document ID from the real manifest.",
    )

    args = parser.parse_args()

    manifest = load_manifest()

    document = find_document(
        manifest,
        args.document_id,
    )

    if document.get("ingestion_status") != "downloaded":
        raise ValueError(
            "Document must have "
            "ingestion_status='downloaded' "
            "before extraction."
        )

    specialty = normalize_folder_name(
        document["medical_specialty"]
    )

    source_path = (
        RAW_DIR
        / specialty
        / f"{args.document_id}.pdf"
    )

    print("\nMedicalPlab PDF Extraction")
    print("=" * 34)
    print(f"Document : {args.document_id}")
    print("Step 1   : verifying source integrity...")

    actual_sha256 = verify_source_file(
        source_path,
        document.get("sha256"),
    )

    print("SHA-256  : verified ✅")
    print("Step 2   : extracting page text...")

    pages, page_count = extract_pdf(
        source_path
    )

    print("Step 3   : calculating quality metrics...")

    quality_report = build_quality_report(
        args.document_id,
        pages,
        page_count,
    )

    extracted_at = datetime.now(
        timezone.utc
    ).isoformat()

    output = {
        "document_id": args.document_id,
        "source_id": document["source_id"],
        "title": document["title"],
        "medical_specialty": document[
            "medical_specialty"
        ],
        "topics": document["topics"],
        "source_sha256": actual_sha256,
        "page_count": page_count,
        "extracted_at": extracted_at,
        "extraction": {
            "engine": "pdfplumber",
            "engine_version": pdfplumber.__version__,
            "pipeline_version": "v1",
        },
        "pages": pages,
    }

    output_dir = (
        PROCESSED_DIR
        / specialty
    )

    document_path = (
        output_dir
        / f"{args.document_id}.json"
    )

    quality_path = (
        output_dir
        / f"{args.document_id}.quality.json"
    )

    save_json(
        document_path,
        output,
    )

    save_json(
        quality_path,
        quality_report,
    )

    print("\nEXTRACTION COMPLETE ✅")
    print(f"Pages      : {page_count}")
    print(
        f"Text pages : "
        f"{quality_report['pages_with_text']}"
    )
    print(
        f"Empty pages: "
        f"{quality_report['empty_pages']}"
    )
    print(
        f"Coverage   : "
        f"{quality_report['text_coverage']:.1%}"
    )
    print(
        f"Characters : "
        f"{quality_report['total_characters']:,}"
    )
    print(
        f"Quality    : "
        f"{quality_report['quality_status'].upper()}"
    )
    print(f"Output     : {document_path}")
    print(f"Report     : {quality_path}")


if __name__ == "__main__":
    main()