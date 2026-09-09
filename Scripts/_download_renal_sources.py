"""Acquire selected renal JATS from Europe PMC and enforce the license gate."""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

import requests

from verify_source_license import decision_dict

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "Data" / "metadata"
RAW = ROOT / "Data" / "raw" / "renal_v1"
REGISTRY = META / "renal_source_registry_v1.json"
LICENSE_MANIFEST = META / "renal_source_license_manifest_v1.json"
FULLTEXT = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"


def _article_pmcid(path: Path) -> str | None:
    root = ElementTree.parse(path).getroot()
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] == "article-id" and node.attrib.get("pub-id-type") in {"pmc", "pmcid"}:
            value = "".join(node.itertext()).strip()
            return value if value.startswith("PMC") else f"PMC{value}"
    return None


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = []
    with requests.Session() as session:
        session.headers["User-Agent"] = "MedicalPlab-governed-acquisition/1.0"
        for document in registry["documents"]:
            pmcid = document["pmcid"]
            document_id = document["document_id"]
            target = RAW / f"{document_id}.xml"
            temporary = RAW / f".{document_id}.download"
            try:
                response = session.get(FULLTEXT.format(pmcid=pmcid), timeout=45)
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                if "xml" not in content_type.casefold() or len(response.content) < 1000:
                    raise ValueError(f"Unexpected payload: content-type={content_type!r}, bytes={len(response.content)}")
                temporary.write_bytes(response.content)
                if _article_pmcid(temporary) != pmcid:
                    raise ValueError("Downloaded JATS PMCID does not match the registry.")
                decision = decision_dict(temporary)
                now = datetime.now(timezone.utc).isoformat()
                entry = {
                    "document_id": document_id,
                    "license": decision["license_name"],
                    "license_evidence_url": document["official_source_url"],
                    "license_url": decision["license_url"],
                    "license_evidence": decision["license_evidence"],
                    "commercial_use": decision["commercial_use"],
                    "rag_ingestion_decision": decision["rag_ingestion"],
                    "attribution_requirement": "required" if decision["attribution_required"] else "none_or_unverified",
                    "decision_code": decision["decision_code"],
                    "doi": document["doi"],
                    "pmcid": pmcid,
                    "source_url": document["official_source_url"],
                    "verified_timestamp": now,
                }
                if decision["rag_ingestion"]:
                    temporary.replace(target)
                    digest = hashlib.sha256(target.read_bytes()).hexdigest()
                    entry["sha256"] = digest
                    document.update({
                        "license_name": decision["license_name"], "license_url": decision["license_url"],
                        "commercial_reuse_status": "APPROVED", "rag_ingestion_status": "downloaded",
                        "retrieved_at": now, "download_format": "pmc_jats_xml", "sha256": digest,
                        "status": "accepted", "exclusion_reason": None,
                    })
                    print(f"ACCEPT {document_id} {pmcid} {decision['license_name']} {len(response.content)} bytes")
                else:
                    temporary.unlink(missing_ok=True)
                    document.update({"commercial_reuse_status": "REJECTED", "rag_ingestion_status": "excluded", "status": "rejected", "exclusion_reason": decision["decision_code"]})
                    print(f"REJECT {document_id} {pmcid} {decision['decision_code']}")
                manifest.append(entry)
            except Exception as exc:
                temporary.unlink(missing_ok=True)
                document.update({"rag_ingestion_status": "download_failed", "status": "rejected", "exclusion_reason": f"ACQUISITION_ERROR: {exc}"})
                manifest.append({"document_id": document_id, "pmcid": pmcid, "rag_ingestion_decision": False, "decision_code": "ACQUISITION_ERROR", "error": str(exc)})
                print(f"ERROR {document_id} {pmcid}: {exc}")
            time.sleep(0.2)
    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    LICENSE_MANIFEST.write_text(json.dumps({"manifest_id": "RENAL-LICENSE-v1", "entries": manifest}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    accepted = sum(item.get("rag_ingestion_decision") is True for item in manifest)
    print(f"Accepted {accepted}/{len(manifest)}; rejected {len(manifest)-accepted}/{len(manifest)}.")
    return int(accepted < 12)


if __name__ == "__main__":
    raise SystemExit(main())
