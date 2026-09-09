"""Select a balanced renal v1 candidate set from Europe PMC discovery data."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "Data" / "metadata" / "renal_source_candidates_raw.json"
OUTPUT = ROOT / "Data" / "metadata" / "renal_source_registry_v1.json"

# Manual coverage judgement is intentionally explicit and reviewable. Selection
# does not imply license acceptance; the JATS gate runs during acquisition.
SELECTED = {
    "PMC3997861": ("DOC-PMC-RENAL-0001", ["RAAS", "aldosterone", "renal endocrine function"], "foundational", 18, 18, 15),
    "PMC6692336": ("DOC-PMC-RENAL-0002", ["glomerulus", "filtration barrier", "GFR"], "foundational", 17, 18, 18),
    "PMC9395506": ("DOC-PMC-RENAL-0003", ["potassium handling", "tubular transport", "hyperkalaemia"], "foundational_clinical", 20, 19, 19),
    "PMC4058521": ("DOC-PMC-RENAL-0004", ["proximal tubule", "tubular reabsorption", "acid-base"], "foundational", 17, 19, 19),
    "PMC11064853": ("DOC-PMC-RENAL-0005", ["acid-base physiology", "tubular secretion", "functional nephron units"], "foundational", 17, 19, 18),
    "PMC6154171": ("DOC-PMC-RENAL-0006", ["AKI", "diagnosis", "management principles"], "clinical", 22, 18, 18),
    "PMC11116248": ("DOC-PMC-RENAL-0007", ["CKD", "evaluation", "management principles"], "clinical", 22, 19, 20),
    "PMC7316686": ("DOC-PMC-RENAL-0008", ["nephrotic syndrome", "glomerular disease", "proteinuria"], "clinical", 22, 18, 17),
    "PMC6892421": ("DOC-PMC-RENAL-0009", ["hyperkalaemia", "electrolyte disturbance", "potassium"], "clinical", 19, 19, 18),
    "PMC6588653": ("DOC-PMC-RENAL-0010", ["hyperkalaemia", "kidney disease", "management"], "clinical_high_risk", 22, 18, 17),
    "PMC8188986": ("DOC-PMC-RENAL-0011", ["UTI", "recurrent UTI", "urinary tract"], "clinical", 17, 18, 18),
    "PMC10889283": ("DOC-PMC-RENAL-0012", ["nephrolithiasis", "renal colic", "urinary obstruction"], "clinical", 20, 19, 20),
    "PMC9492590": ("DOC-PMC-RENAL-0013", ["kidney stones", "recurrent UTI", "infected obstruction"], "clinical", 18, 18, 17),
    "PMC7481370": ("DOC-PMC-RENAL-0014", ["hydronephrosis", "urinary obstruction", "grading"], "clinical", 16, 16, 17),
    "PMC4056317": ("DOC-PMC-RENAL-0015", ["renal replacement therapy", "dialysis basics", "AKI"], "clinical_high_risk", 19, 17, 16),
    "PMC4056314": ("DOC-PMC-RENAL-0016", ["GFR", "creatinine clearance", "AKI assessment"], "foundational_clinical", 18, 18, 17),
}


def main() -> int:
    candidates = json.loads(INPUT.read_text(encoding="utf-8"))
    by_id = {item["pmcid"]: item for item in candidates}
    missing = sorted(set(SELECTED) - set(by_id))
    if missing:
        raise RuntimeError(f"Selected PMCIDs missing from discovery output: {missing}")
    documents = []
    for pmcid, (document_id, topics, domain, authority, education, coverage) in SELECTED.items():
        item = by_id[pmcid]
        freshness = 5 if int(item.get("publication_year") or 0) >= 2021 else 3
        provenance = 5
        structure = 9
        quality = authority + education + 20 + coverage + structure + freshness + provenance
        documents.append({
            "document_id": document_id,
            "title": item["title"],
            "authors": item["authors"],
            "journal": item["journal"],
            "publisher": item["publisher"],
            "publication_year": item["publication_year"],
            "doi": item["doi"],
            "pmcid": pmcid,
            "official_source_url": item["official_source_url"],
            "license_name": item["reported_license"],
            "license_url": None,
            "commercial_reuse_status": "PENDING_JATS_VERIFICATION",
            "rag_ingestion_status": "candidate",
            "medical_domain": domain,
            "topic_tags": topics,
            "evidence_type": item["evidence_type"] or "journal_article",
            "authority_score": authority,
            "education_score": education,
            "coverage_score": coverage,
            "source_quality_score": quality,
            "retrieved_at": None,
            "download_format": None,
            "sha256": None,
            "status": "selected_pending_license",
            "exclusion_reason": None,
        })
    rejected = [{
        "pmcid": item["pmcid"], "title": item["title"], "doi": item["doi"],
        "status": "not_selected_v1", "exclusion_reason": "Lower marginal coverage/authority score or redundant for the 16-document v1 target.",
    } for item in candidates if item["pmcid"] not in SELECTED]
    payload = {"registry_id": "RENAL-SOURCE-REGISTRY-v1", "selection_policy": "balanced_coverage_weighted_v1", "candidate_count": len(candidates), "documents": documents, "rejected_candidates": rejected}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Selected {len(documents)} of {len(candidates)} candidates; recorded {len(rejected)} not-selected candidates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
