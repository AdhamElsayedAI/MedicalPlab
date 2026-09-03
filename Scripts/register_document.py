import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MANIFEST_PATH = (
    PROJECT_ROOT
    / "Data"
    / "metadata"
    / "document_manifest.json"
)

RAW_DIR = PROJECT_ROOT / "Data" / "raw"


def load_manifest() -> list[dict[str, Any]]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Document manifest must be a JSON array.")

    return data


def save_manifest(
    manifest: list[dict[str, Any]],
) -> None:
    with MANIFEST_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            manifest,
            file,
            indent=2,
            ensure_ascii=False,
        )


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
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def validate_pdf(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"PDF not found: {path}"
        )

    if path.stat().st_size < 10_000:
        raise ValueError(
            "PDF is unexpectedly small."
        )

    with path.open("rb") as file:
        signature = file.read(5)

    if signature != b"%PDF-":
        raise ValueError(
            "File does not have a valid PDF signature."
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Register a manually acquired MedicalPlab document."
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

    if document.get("license_status") == "blocked":
        raise ValueError(
            "Document licence is blocked."
        )

    specialty = normalize_folder_name(
        document["medical_specialty"]
    )

    file_path = (
        RAW_DIR
        / specialty
        / f"{args.document_id}.pdf"
    )

    print("\nMedicalPlab Document Registrar")
    print("=" * 34)
    print(f"Document : {args.document_id}")
    print(f"File     : {file_path}")
    print("Checking file...")

    validate_pdf(file_path)

    sha256 = calculate_sha256(file_path)

    retrieved_at = datetime.now(
        timezone.utc
    ).isoformat()

    document["sha256"] = sha256
    document["retrieved_at"] = retrieved_at
    document["ingestion_status"] = "downloaded"

    save_manifest(manifest)

    print("\nDOCUMENT REGISTERED ✅")
    print(f"Size   : {file_path.stat().st_size:,} bytes")
    print(f"SHA256 : {sha256}")
    print(f"UTC    : {retrieved_at}")


if __name__ == "__main__":
    main()