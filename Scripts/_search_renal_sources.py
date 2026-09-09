"""Discover renal JATS candidates through the official Europe PMC API.

Discovery is broader than acceptance. A candidate is not safe for ingestion
until ``verify_source_license.py`` verifies its article-level JATS license.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = PROJECT_ROOT / "Data" / "metadata" / "renal_source_candidates_raw.json"
SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

TOPIC_QUERIES = {
    "anatomy": '((TITLE:"kidney anatomy" OR TITLE:"renal anatomy" OR TITLE:"urinary tract anatomy" OR TITLE:"nephron anatomy") AND OPEN_ACCESS:Y)',
    "filtration": '((TITLE:"glomerular filtration" OR TITLE:"filtration barrier" OR TITLE:"GFR") AND OPEN_ACCESS:Y)',
    "tubular_transport": '((TITLE:"renal tubular transport" OR TITLE:"proximal tubule transport" OR TITLE:"sodium handling" OR TITLE:"potassium and the kidney") AND OPEN_ACCESS:Y)',
    "water_balance": '((TITLE:"countercurrent" OR TITLE:"vasopressin kidney" OR TITLE:"ADH kidney" OR TITLE:"water balance kidney") AND OPEN_ACCESS:Y)',
    "acid_base": '((TITLE:"kidney acid-base" OR TITLE:"renal acid-base" OR TITLE:"acid-base exchange") AND OPEN_ACCESS:Y)',
    "raas": '((TITLE:"renin angiotensin aldosterone" OR TITLE:"renin-angiotensin system") AND OPEN_ACCESS:Y)',
    "aki_ckd": '((TITLE:"acute kidney injury" OR TITLE:"chronic kidney disease") AND (REVIEW:Y OR PUB_TYPE:"guideline") AND OPEN_ACCESS:Y)',
    "glomerular": '((TITLE:"nephrotic syndrome" OR TITLE:"glomerulonephritis" OR TITLE:"nephritic syndrome") AND OPEN_ACCESS:Y)',
    "electrolytes": '((TITLE:"hyperkalemia" OR TITLE:"hyperkalaemia" OR TITLE:"electrolyte disorders") AND OPEN_ACCESS:Y)',
    "infection": '((TITLE:"urinary tract infection" OR TITLE:"pyelonephritis") AND OPEN_ACCESS:Y)',
    "stones_obstruction": '((TITLE:"kidney stones" OR TITLE:"nephrolithiasis" OR TITLE:"urinary obstruction" OR TITLE:"hydronephrosis") AND OPEN_ACCESS:Y)',
    "dialysis": '((TITLE:hemodialysis OR TITLE:"peritoneal dialysis" OR TITLE:"renal replacement therapy") AND OPEN_ACCESS:Y)',
    "core_physiology": '(("renal physiology" OR "kidney physiology" OR "nephron physiology" OR "renal blood flow") AND REVIEW:Y AND OPEN_ACCESS:Y)',
    "concentration_adh": '(((vasopressin OR "antidiuretic hormone" OR "urine concentration" OR "countercurrent mechanism") AND (kidney OR renal OR nephron)) AND REVIEW:Y AND OPEN_ACCESS:Y)',
    "urinary_anatomy": '(((kidney OR ureter OR bladder OR urinary) AND (anatomy OR histology)) AND REVIEW:Y AND OPEN_ACCESS:Y)',
}


def discover(session: requests.Session, page_size: int = 50) -> list[dict[str, object]]:
    by_pmcid: dict[str, dict[str, object]] = {}
    for topic, query in TOPIC_QUERIES.items():
        response = session.get(
            SEARCH_URL,
            params={"query": query, "format": "json", "pageSize": page_size, "sort": "CITED desc", "resultType": "core"},
            timeout=30,
        )
        response.raise_for_status()
        for article in response.json().get("resultList", {}).get("result", []):
            pmcid = str(article.get("pmcid") or "")
            if not pmcid:
                continue
            record = by_pmcid.setdefault(
                pmcid,
                {
                    "pmcid": pmcid,
                    "title": article.get("title", ""),
                    "authors": article.get("authorString", ""),
                    "journal": article.get("journalTitle", ""),
                    "publisher": article.get("publisher", ""),
                    "publication_year": article.get("pubYear", ""),
                    "doi": article.get("doi", ""),
                    "reported_license": article.get("license", "unknown"),
                    "cited_by_count": int(article.get("citedByCount") or 0),
                    "evidence_type": article.get("pubType", ""),
                    "discovery_topics": [],
                    "official_source_url": f"https://europepmc.org/article/PMC/{pmcid}",
                },
            )
            record["discovery_topics"].append(topic)
    return sorted(by_pmcid.values(), key=lambda item: (-int(item["cited_by_count"]), str(item["pmcid"])))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    with requests.Session() as session:
        session.headers["User-Agent"] = "MedicalPlab-source-research/1.0"
        candidates = discover(session, args.page_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(candidates, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Discovered {len(candidates)} unique renal candidates across {len(TOPIC_QUERIES)} topic searches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
