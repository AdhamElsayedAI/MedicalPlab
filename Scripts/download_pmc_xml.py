import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MANIFEST_PATH = (
    PROJECT_ROOT
    / "Data"
    / "metadata"
    / "document_manifest.json"
)

RAW_DIR = (
    PROJECT_ROOT
    / "Data"
    / "raw"
)

PMC_OAI_BASE_URL = (
    "https://pmc.ncbi.nlm.nih.gov/api/oai/v1/mh/"
)


def load_manifest() -> list[dict[str, Any]]:
    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if isinstance(data, list):
        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

    if isinstance(data, dict):
        documents = data.get(
            "documents",
            [],
        )

        if isinstance(documents, list):
            return [
                item
                for item in documents
                if isinstance(item, dict)
            ]

    raise ValueError(
        "Unsupported document manifest structure."
    )


def find_document(
    document_id: str,
) -> dict[str, Any]:
    documents = load_manifest()

    for document in documents:
        if (
            document.get("document_id")
            == document_id
        ):
            return document

    raise ValueError(
        f"Document not found: {document_id}"
    )


def extract_pmcid(
    document: dict[str, Any],
) -> str:
    url = str(
        document.get(
            "url",
            "",
        )
    )

    match = re.search(
        r"\bPMC(\d+)\b",
        url,
        flags=re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            "Could not determine PMCID from "
            "the document URL."
        )

    return (
        "PMC"
        + match.group(1)
    )


def specialty_folder(
    value: str,
) -> str:
    return (
        value.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )


def sha256_bytes(
    data: bytes,
) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()


def validate_xml(
    content: bytes,
) -> ElementTree.Element:
    if not content:
        raise ValueError(
            "Downloaded XML is empty."
        )

    try:
        root = ElementTree.fromstring(
            content
        )

    except ElementTree.ParseError as error:
        raise ValueError(
            f"Invalid XML: {error}"
        ) from error

    article_found = False

    for element in root.iter():
        tag = str(
            element.tag
        )

        local_name = (
            tag.split("}")[-1]
        )

        if local_name == "article":
            article_found = True
            break

    if not article_found:
        raise ValueError(
            "OAI response does not contain "
            "a full JATS <article> element."
        )

    return root


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download reusable PMC full-text "
            "JATS XML using the official "
            "PMC OAI-PMH API."
        )
    )

    parser.add_argument(
        "document_id",
    )

    args = parser.parse_args()

    document = find_document(
        args.document_id
    )

    source_id = str(
        document.get(
            "source_id",
            "",
        )
    )

    if not source_id.startswith(
        "SRC-PMC"
    ):
        raise ValueError(
            "Document is not registered as "
            "a PMC source."
        )

    if not document.get(
        "rag_allowed",
        False,
    ):
        raise ValueError(
            "Document is not approved for RAG."
        )

    if (
        document.get(
            "license_status"
        )
        != "approved"
    ):
        raise ValueError(
            "Document license is not approved."
        )

    pmcid = extract_pmcid(
        document
    )

    numeric_pmcid = pmcid[
        3:
    ]

    oai_identifier = (
        "oai:pubmedcentral.nih.gov:"
        + numeric_pmcid
    )

    params = {
        "verb": "GetRecord",
        "identifier": oai_identifier,
        "metadataPrefix": "pmc",
    }

    headers = {
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": (
            "MedicalPlab-RAG/1.0 "
            "(educational research project)"
        ),
    }

    print(
        "\nMedicalPlab PMC XML Acquisition"
    )
    print("=" * 48)

    print(
        f"Document : {args.document_id}"
    )

    print(
        f"PMCID    : {pmcid}"
    )

    print(
        f"OAI ID   : {oai_identifier}"
    )

    print(
        "Step 1   : requesting official "
        "PMC JATS XML..."
    )

    response = requests.get(
        PMC_OAI_BASE_URL,
        params=params,
        headers=headers,
        timeout=60,
    )

    response.raise_for_status()

    content = response.content

    print(
        "Step 2   : validating XML..."
    )

    validate_xml(
        content
    )

    specialty = specialty_folder(
        str(
            document.get(
                "medical_specialty",
                "unknown",
            )
        )
    )

    output_dir = (
        RAW_DIR
        / specialty
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / f"{args.document_id}.xml"
    )

    output_path.write_bytes(
        content
    )

    digest = sha256_bytes(
        content
    )

    print(
        "\nPMC XML ACQUIRED ✅"
    )

    print(
        f"File    : {output_path}"
    )

    print(
        f"Size    : {len(content):,} bytes"
    )

    print(
        f"SHA256  : {digest}"
    )

    print(
        "Format  : JATS XML"
    )

    print(
        "Source  : PMC OAI-PMH"
    )


if __name__ == "__main__":
    main()