import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


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
        while True:
            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def download_pdf(
    url: str,
    destination: Path,
) -> None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/152.0 Safari/537.36"
        ),
        "Accept": "application/pdf,*/*",
    }

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = destination.with_suffix(
        ".download"
    )

    try:
        with requests.get(
            url,
            headers=headers,
            timeout=60,
            stream=True,
            allow_redirects=True,
        ) as response:

            response.raise_for_status()

            with temporary_path.open("wb") as file:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if chunk:
                        file.write(chunk)

        if temporary_path.stat().st_size < 10_000:
            raise ValueError(
                "Downloaded file is unexpectedly small."
            )

        with temporary_path.open("rb") as file:
            signature = file.read(5)

        if signature != b"%PDF-":
            raise ValueError(
                "Downloaded content is not a valid PDF."
            )

        temporary_path.replace(destination)

    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()

        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download a governed MedicalPlab document."
    )

    parser.add_argument(
        "document_id",
        help="Document ID from the real document manifest.",
    )

    args = parser.parse_args()

    manifest = load_manifest()

    document = find_document(
        manifest,
        args.document_id,
    )

    download_url = document.get("download_url")

    if not download_url:
        raise ValueError(
            f"{args.document_id} has no download_url."
        )

    if document.get("license_status") == "blocked":
        raise ValueError(
            f"{args.document_id} has a blocked licence."
        )

    if document.get("ingestion_status") == "blocked":
        raise ValueError(
            f"{args.document_id} is blocked from ingestion."
        )

    specialty = normalize_folder_name(
        document["medical_specialty"]
    )

    destination = (
        RAW_DIR
        / specialty
        / f"{args.document_id}.pdf"
    )

    if destination.exists():
        raise FileExistsError(
            f"File already exists: {destination}"
        )

    print("\nMedicalPlab Corpus Downloader")
    print("=" * 34)
    print(f"Document : {args.document_id}")
    print(f"Specialty: {document['medical_specialty']}")
    print("Status    : downloading...")

    download_pdf(
        download_url,
        destination,
    )

    file_hash = calculate_sha256(
        destination
    )

    retrieved_at = datetime.now(
        timezone.utc
    ).isoformat()

    document["sha256"] = file_hash
    document["retrieved_at"] = retrieved_at
    document["ingestion_status"] = "downloaded"

    save_manifest(manifest)

    print("\nDOWNLOAD COMPLETE ✅")
    print(f"File   : {destination}")
    print(f"SHA256 : {file_hash}")
    print(f"UTC    : {retrieved_at}")


if __name__ == "__main__":
    main()