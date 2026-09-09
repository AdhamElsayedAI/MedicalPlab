"""Wave 2 PMC JATS Ingestion and Validation Batch Runner.

Processes PMC documents through the verified pipeline:
1. download_pmc_xml
2. extract_pmc_jats
3. adapt_pmc_to_canonical
4. chunk_sections
5. validate_chunks
6. validate_chunk_integrity

Records all verification metadata.
"""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "Data" / "metadata" / "document_manifest.json"
PROCESSED_DIR = PROJECT_ROOT / "Data" / "processed"
RAW_DIR = PROJECT_ROOT / "Data" / "raw"


def get_doc_info(doc_id: str) -> dict:
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    for d in manifest:
        if d.get("document_id") == doc_id:
            return d
    raise ValueError(f"Document {doc_id} not found in manifest")


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    res = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return res.returncode, res.stdout, res.stderr


def process_document(doc_id: str) -> dict:
    doc = get_doc_info(doc_id)
    specialty = (
        doc.get("medical_specialty", "Cardiology")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )
    url = doc.get("url", "")
    pmcid = ""
    if "PMC" in url:
        import re
        m = re.search(r"PMC\d+", url)
        if m:
            pmcid = m.group(0)

    print(f"\n========================================================")
    print(f"Ingesting {doc_id} ({pmcid}) - {specialty}")
    print(f"Title: {doc.get('title')}")
    print(f"========================================================")

    # 1. Download
    cmd1 = [sys.executable, "-X", "utf8", "Scripts/download_pmc_xml.py", doc_id]
    code, out, err = run_cmd(cmd1)
    if code != 0:
        print(f"FAILED Step 1 Download: {err or out}")
        return {"document_id": doc_id, "status": "FAILED_DOWNLOAD", "error": err or out}

    xml_path = RAW_DIR / specialty / f"{doc_id}.xml"
    if not xml_path.exists():
        return {"document_id": doc_id, "status": "XML_NOT_FOUND"}
    
    sha256 = hashlib.sha256(xml_path.read_bytes()).hexdigest()
    timestamp = datetime.now(timezone.utc).isoformat()

    # 2. Extract
    cmd2 = [sys.executable, "-X", "utf8", "Scripts/extract_pmc_jats.py", doc_id, "--specialty", specialty]
    code, out, err = run_cmd(cmd2)
    if code != 0:
        print(f"FAILED Step 2 Extract: {err or out}")
        return {"document_id": doc_id, "status": "FAILED_EXTRACT", "error": err or out}

    # 3. Adapt
    cmd3 = [sys.executable, "-X", "utf8", "Scripts/adapt_pmc_to_canonical.py", doc_id, "--specialty", specialty]
    code, out, err = run_cmd(cmd3)
    if code != 0:
        print(f"FAILED Step 3 Adapt: {err or out}")
        return {"document_id": doc_id, "status": "FAILED_ADAPT", "error": err or out}

    # 4. Chunk
    cmd4 = [sys.executable, "-X", "utf8", "Scripts/chunk_sections.py", doc_id, "--specialty", specialty]
    code, out, err = run_cmd(cmd4)
    if code != 0:
        print(f"FAILED Step 4 Chunk: {err or out}")
        return {"document_id": doc_id, "status": "FAILED_CHUNK", "error": err or out}

    # 5. Validate chunks schema
    chunks_path = PROCESSED_DIR / specialty / f"{doc_id}.chunks.json"
    cmd5 = [sys.executable, "-X", "utf8", "Scripts/validate_chunks.py", "--file", str(chunks_path)]
    code, out, err = run_cmd(cmd5)
    schema_ok = (code == 0 and "Validation: PASS" in out)
    if not schema_ok:
        print(f"FAILED Step 5 Validate Chunks: {err or out}")
        return {"document_id": doc_id, "status": "FAILED_SCHEMA_VALIDATE", "error": err or out}

    # 6. Validate chunk integrity
    cmd6 = [sys.executable, "-X", "utf8", "Scripts/validate_chunk_integrity.py", "--specialty", specialty, doc_id]
    code, out, err = run_cmd(cmd6)
    integrity_ok = (code == 0 and "Validation                 : PASS" in out)
    if not integrity_ok:
        print(f"FAILED Step 6 Validate Chunk Integrity: {err or out}")
        return {"document_id": doc_id, "status": "FAILED_INTEGRITY_VALIDATE", "error": err or out}

    # Read quality reports
    jats_quality = json.loads((PROCESSED_DIR / specialty / f"{doc_id}.jats.quality.json").read_text(encoding="utf-8"))
    chunks_quality = json.loads((PROCESSED_DIR / specialty / f"{doc_id}.chunks.quality.json").read_text(encoding="utf-8"))
    
    sections_count = jats_quality.get("checks", {}).get("sections", {}).get("extracted", 0)
    chunk_count = chunks_quality.get("total_chunks", 0)

    res = {
        "document_id": doc_id,
        "pmcid": pmcid,
        "title": doc.get("title"),
        "medical_specialty": specialty,
        "license_name": doc.get("license_name"),
        "license_status": doc.get("license_status"),
        "retrieval_timestamp": timestamp,
        "sha256": sha256,
        "sections_count": sections_count,
        "chunk_count": chunk_count,
        "schema_validation": "PASS",
        "integrity_validation": "PASS",
        "final_status": "VERIFIED",
    }
    print(f"SUCCESS: {doc_id} - {sections_count} sections, {chunk_count} chunks. All checks PASS ✅")
    return res


def main():
    target_docs = sys.argv[1:]
    if not target_docs:
        print("Usage: python Scripts/ingest_wave2_batch.py DOC_ID [DOC_ID ...]")
        sys.exit(1)

    results = []
    for doc_id in target_docs:
        res = process_document(doc_id)
        results.append(res)

    print("\n\n========================================================")
    print("INGESTION BATCH SUMMARY")
    print("========================================================")
    for r in results:
        print(f"{r.get('document_id')}: {r.get('final_status')} | {r.get('chunk_count', 0)} chunks | SHA: {r.get('sha256', '')[:16]}...")
    
    output_log = PROJECT_ROOT / "Data" / "audit" / f"wave2_ingestion_results.json"
    output_log.parent.mkdir(parents=True, exist_ok=True)
    with open(output_log, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {output_log}")


if __name__ == "__main__":
    main()
