"""Build a separately versioned, undergraduate-oriented Renal v2 corpus."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

import requests

from verify_source_license import decision_dict


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Data"
META = DATA / "metadata"
RAW_V1 = DATA / "raw" / "renal_v1"
RAW_V2 = DATA / "raw" / "renal_v2"
PROCESSED = DATA / "processed" / "renal_v2"
CHUNK_ROOT = DATA / "experiments" / "renal_v2" / "chunking"
FULLTEXT = "https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"

NEW_SOURCES = [
    ("DOC-PMC-RENAL-0017", "PMC6221012", ["salt handling", "water balance", "nephron", "ADH"], "CORE_EDUCATIONAL"),
    ("DOC-PMC-RENAL-0018", "PMC3426247", ["glomerular filtration barrier", "glomerulus"], "CORE_EDUCATIONAL"),
    ("DOC-PMC-RENAL-0019", "PMC8708129", ["glucose handling", "proximal tubule", "SGLT"], "CORE_EDUCATIONAL"),
    ("DOC-PMC-RENAL-0020", "PMC4600925", ["tubular transport", "sodium handling", "potassium handling"], "SUPPORTING"),
    ("DOC-PMC-RENAL-0021", "PMC10220024", ["acid-base physiology", "bicarbonate transport", "renal sensing"], "SUPPORTING"),
    ("DOC-PMC-RENAL-0022", "PMC4203353", ["sodium handling", "phosphate", "blood pressure"], "SUPPORTING"),
    ("DOC-PMC-RENAL-0023", "PMC12904963", ["urine concentration", "countercurrent mechanism", "renal medulla"], "CORE_EDUCATIONAL"),
    ("DOC-PMC-RENAL-0024", "PMC13156944", ["renal endocrine", "erythropoietin", "calcitriol", "vitamin D"], "CORE_EDUCATIONAL"),
    ("DOC-PMC-RENAL-0025", "PMC12411799", ["haematuria", "differential diagnosis", "glomerular vs non-glomerular", "investigation"], "CORE_EDUCATIONAL"),
]

V1_CLASSIFICATION = {
    "DOC-PMC-RENAL-0001": "SUPPORTING", "DOC-PMC-RENAL-0002": "SPECIALIST",
    "DOC-PMC-RENAL-0003": "CORE_EDUCATIONAL", "DOC-PMC-RENAL-0004": "CORE_EDUCATIONAL",
    "DOC-PMC-RENAL-0005": "CORE_EDUCATIONAL", "DOC-PMC-RENAL-0006": "SUPPORTING",
    "DOC-PMC-RENAL-0007": "CORE_EDUCATIONAL", "DOC-PMC-RENAL-0008": "SPECIALIST",
    "DOC-PMC-RENAL-0009": "SUPPORTING", "DOC-PMC-RENAL-0010": "SUPPORTING",
    "DOC-PMC-RENAL-0011": "LOW_MARGINAL_VALUE", "DOC-PMC-RENAL-0012": "CORE_EDUCATIONAL",
    "DOC-PMC-RENAL-0013": "SUPPORTING", "DOC-PMC-RENAL-0014": "SPECIALIST",
    "DOC-PMC-RENAL-0015": "SPECIALIST", "DOC-PMC-RENAL-0016": "SPECIALIST",
}


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def first_text(root: ElementTree.Element, tag: str, attr: tuple[str, str] | None = None) -> str:
    for node in root.iter():
        if local(node.tag) == tag and (attr is None or node.attrib.get(attr[0]) == attr[1]):
            return " ".join("".join(node.itertext()).split())
    return ""


def role_for(chunk: dict) -> str:
    heading = " ".join(chunk.get("section_path", [])).casefold()
    if any(term in heading for term in ("references", "acknowledg", "author contribution", "supplement", "funding", "conflict of interest")):
        return "EXCLUDED_FROM_SEARCH"
    if any(term in heading for term in ("methods", "materials and methods", "statistical analysis", "results")):
        return "LOW_PRIORITY"
    if any(term in heading for term in ("introduction", "discussion", "conclusion", "physiology", "mechanism", "management", "diagnosis", "guideline")):
        return "CORE"
    return "SUPPORTING"


def window(document: dict, size: int, overlap: int, label: str) -> dict:
    chunks = []
    for block in document["sections"]:
        words = re.findall(r"\S+", block["text"])
        p_id = f"{document['document_id']}-P{int(block['block_index']):04d}"
        for start in range(0, len(words), size - overlap):
            part = words[start:start + size]
            if not part:
                continue
            chunks.append({
                "chunk_id": f"{document['document_id']}-{label}-C{len(chunks)+1:04d}",
                "document_id": document["document_id"],
                "parent_section_id": p_id,
                "text": " ".join(part),
                "heading": block.get("heading", ""),
                "section_path": block.get("section_path", []),
                "source_block_index": block["block_index"],
                "retrieval_role": role_for(block),
            })
            if start + size >= len(words):
                break
    return {"document_id": document["document_id"], "configuration": label, "chunks": chunks}


def sentence_window(document: dict, target_words: int = 280, overlap_sentences: int = 1, label: str = "E") -> dict:
    chunks = []
    for block in document["sections"]:
        sentences = re.split(r"(?<=[.!?])\s+", block["text"])
        p_id = f"{document['document_id']}-P{int(block['block_index']):04d}"
        current_sentences = []
        current_words = 0
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            w = len(s.split())
            if current_words + w > target_words and current_sentences:
                chunks.append({
                    "chunk_id": f"{document['document_id']}-{label}-C{len(chunks)+1:04d}",
                    "document_id": document["document_id"],
                    "parent_section_id": p_id,
                    "text": " ".join(current_sentences),
                    "heading": block.get("heading", ""),
                    "section_path": block.get("section_path", []),
                    "source_block_index": block["block_index"],
                    "retrieval_role": role_for(block),
                })
                current_sentences = current_sentences[-overlap_sentences:] if overlap_sentences > 0 else []
                current_words = sum(len(x.split()) for x in current_sentences)
            current_sentences.append(s)
            current_words += w
        if current_sentences:
            chunks.append({
                "chunk_id": f"{document['document_id']}-{label}-C{len(chunks)+1:04d}",
                "document_id": document["document_id"],
                "parent_section_id": p_id,
                "text": " ".join(current_sentences),
                "heading": block.get("heading", ""),
                "section_path": block.get("section_path", []),
                "source_block_index": block["block_index"],
                "retrieval_role": role_for(block),
            })
    return {"document_id": document["document_id"], "configuration": "E_sentence_evidence_300", "chunks": chunks}


def main() -> None:
    v1 = json.loads((META / "renal_source_registry_v1.json").read_text(encoding="utf-8"))
    v1_licenses = json.loads((META / "renal_source_license_manifest_v1.json").read_text(encoding="utf-8"))["entries"]
    RAW_V2.mkdir(parents=True, exist_ok=True)
    for source in RAW_V1.glob("*.xml"):
        shutil.copy2(source, RAW_V2 / source.name)

    documents = []
    rejected_candidates = []
    for item in v1["documents"]:
        copied = dict(item)
        copied["educational_classification"] = V1_CLASSIFICATION[item["document_id"]]
        copied["v2_active"] = True
        documents.append(copied)
    licenses = [dict(item) for item in v1_licenses]

    with requests.Session() as session:
        session.headers["User-Agent"] = "MedicalPlab-governed-renal-v2/1.0"
        for document_id, pmcid, topics, classification in NEW_SOURCES:
            target = RAW_V2 / f"{document_id}.xml"
            response = session.get(FULLTEXT.format(pmcid=pmcid), timeout=60)
            response.raise_for_status()
            target.write_bytes(response.content)
            root = ElementTree.parse(target).getroot()
            actual = first_text(root, "article-id", ("pub-id-type", "pmc")) or first_text(root, "article-id", ("pub-id-type", "pmcid"))
            actual = actual if actual.startswith("PMC") else f"PMC{actual}"
            if actual != pmcid:
                raise RuntimeError(f"PMCID mismatch for {document_id}: {actual}")
            decision = decision_dict(target)
            if not decision["rag_ingestion"]:
                rejected_candidates.append({"document_id": document_id, "pmcid": pmcid, "decision_code": decision["decision_code"]})
                target.unlink()
                print(f"REJECT {document_id} {pmcid} {decision['decision_code']}")
                continue
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            now = datetime.now(timezone.utc).isoformat()
            doi = first_text(root, "article-id", ("pub-id-type", "doi"))
            title = first_text(root, "article-title")
            year = first_text(root, "year")
            document = {
                "document_id": document_id, "pmcid": pmcid, "doi": doi, "title": title,
                "publication_year": year, "official_source_url": f"https://europepmc.org/article/PMC/{pmcid}",
                "topic_tags": topics, "evidence_type": "educational_review", "educational_classification": classification,
                "license_name": decision["license_name"], "license_url": decision["license_url"],
                "commercial_reuse_status": "APPROVED", "rag_ingestion_status": "downloaded", "status": "accepted",
                "retrieved_at": now, "download_format": "pmc_jats_xml", "sha256": digest, "v2_active": True,
            }
            documents.append(document)
            licenses.append({
                "document_id": document_id, "license": decision["license_name"], "license_url": decision["license_url"],
                "license_evidence": decision["license_evidence"], "commercial_use": True,
                "rag_ingestion_decision": True, "decision_code": decision["decision_code"], "doi": doi,
                "pmcid": pmcid, "source_url": document["official_source_url"], "verified_timestamp": now, "sha256": digest,
            })
            print(f"ACCEPT {document_id} {pmcid} {decision['license_name']}")
            time.sleep(0.2)

    registry = {
        "registry_id": "RENAL-SOURCES-v2", "created_from": "RENAL-SOURCES-v1",
        "selection_policy": "Undergraduate coverage repair; article-level CC0/CC BY only",
        "documents": documents, "rejected_candidates": rejected_candidates,
    }
    (META / "renal_source_registry_v2.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    (META / "renal_source_license_manifest_v2.json").write_text(json.dumps({"manifest_id": "RENAL-LICENSE-v2", "entries": licenses}, indent=2) + "\n", encoding="utf-8")

    # Existing extractors resolve documents through document_manifest.json.
    manifest_path = META / "document_manifest.json"
    existing = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = existing["documents"] if isinstance(existing, dict) else existing
    by_id = {item["document_id"]: item for item in manifest}
    for document in documents:
        by_id[document["document_id"]] = {
            "document_id": document["document_id"], "source_id": f"SRC-PMC-{document['pmcid']}", "title": document["title"],
            "medical_specialty": "Renal Medicine", "topics": document["topic_tags"], "document_type": document["evidence_type"],
            "evidence_level": "moderate", "publication_date": str(document["publication_year"]), "version": "2",
            "url": document["official_source_url"], "doi": document["doi"], "license_name": document["license_name"],
            "license_status": "approved", "rag_allowed": True, "question_generation_allowed": True,
            "retrieved_at": document["retrieved_at"], "sha256": document["sha256"], "ingestion_status": "downloaded",
        }
    manifest_path.write_text(json.dumps(list(by_id.values()), indent=2) + "\n", encoding="utf-8")

    for document in documents:
        doc_id = document["document_id"]
        enriched_path = PROCESSED / f"{doc_id}.sections.enriched.json"
        chunk_path = PROCESSED / f"{doc_id}.chunks.json"
        if not (enriched_path.exists() and chunk_path.exists()):
            for script, extra in (("extract_pmc_jats.py", []), ("adapt_pmc_to_canonical.py", []), ("chunk_sections.py", ["--target-chars", "1600", "--max-chars", "2200", "--min-chars", "250"])):
                subprocess.run(
                    [sys.executable, str(ROOT / "Scripts" / script), doc_id, "--specialty", "renal_v2", *extra],
                    cwd=ROOT, env={**os.environ, "PYTHONUTF8": "1"}, check=True,
                )
        enriched = json.loads(enriched_path.read_text(encoding="utf-8"))
        section_chunks = json.loads(chunk_path.read_text(encoding="utf-8"))
        for chunk in section_chunks["chunks"]:
            chunk["retrieval_role"] = role_for(chunk)
        variants = {
            "A_250": window(enriched, 250, 0, "A"),
            "B_400_overlap": window(enriched, 400, 40, "B"),
            "C_section_aware": section_chunks,
            "E_sentence_evidence_300": sentence_window(enriched, 280, 1, "E"),
        }
        for name, payload in variants.items():
            path = CHUNK_ROOT / name / f"{doc_id}.chunks.json"; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        parents = {int(block["block_index"]): {
            "parent_section_id": f"{doc_id}-P{int(block['block_index']):04d}", "document_id": doc_id,
            "heading": block.get("heading", ""), "section_path": block.get("section_path", []), "text": block["text"],
            "retrieval_role": role_for(block),
        } for block in enriched["sections"]}
        children = []
        for chunk in section_chunks["chunks"]:
            child = dict(chunk)
            child["child_chunk_id"] = child["chunk_id"]
            child["parent_section_id"] = parents[int(child["source_block_index"])]["parent_section_id"]
            child["topic_metadata"] = document["topic_tags"]
            children.append(child)
        path = CHUNK_ROOT / "D_parent_child_v2" / f"{doc_id}.json"; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"document_id": doc_id, "parents": list(parents.values()), "children": children}, indent=2) + "\n", encoding="utf-8")

    counts = {}
    for name in ("A_250", "B_400_overlap", "C_section_aware", "E_sentence_evidence_300"):
        counts[name] = sum(len(json.loads(path.read_text(encoding="utf-8"))["chunks"]) for path in (CHUNK_ROOT / name).glob("*.json"))
    counts["D_parent_child_v2"] = sum(len(json.loads(path.read_text(encoding="utf-8"))["children"]) for path in (CHUNK_ROOT / "D_parent_child_v2").glob("*.json"))
    print(json.dumps({"documents": len(documents), "chunk_counts": counts}, indent=2))


if __name__ == "__main__":
    main()
