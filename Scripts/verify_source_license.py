"""Deterministic article-level license gate for PMC JATS documents."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from xml.etree import ElementTree

ALLOWED = {
    "cc0": ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"),
    "by/4.0": ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/"),
    "by/3.0": ("CC BY 3.0", "https://creativecommons.org/licenses/by/3.0/"),
    "by/2.5": ("CC BY 2.5", "https://creativecommons.org/licenses/by/2.5/"),
    "by/2.0": ("CC BY 2.0", "https://creativecommons.org/licenses/by/2.0/"),
}


@dataclass(frozen=True)
class LicenseDecision:
    license_name: str
    license_url: str | None
    license_evidence: str
    commercial_use: bool
    rag_ingestion: bool
    attribution_required: bool
    decision_code: str


def verify_jats_license(path: Path) -> LicenseDecision:
    root = ElementTree.parse(path).getroot()
    licenses = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "license"]
    evidence = " ".join(" ".join(node.itertext()) for node in licenses).strip()
    hrefs = " ".join(
        value for node in licenses for key, value in node.attrib.items() if key.rsplit("}", 1)[-1] == "href"
    )
    normalized = re.sub(r"\s+", " ", f"{hrefs} {evidence}").casefold()
    blocked = ("noncommercial", "non-commercial", "by-nc", "/by-nc/", "no derivatives", "by-nd", "/by-nd/")
    if any(marker in normalized for marker in blocked):
        return LicenseDecision("PROHIBITED", None, evidence, False, False, False, "PROHIBITED_LICENSE")
    if "sharealike" in normalized or "by-sa" in normalized or "/by-sa/" in normalized:
        return LicenseDecision("CC BY-SA", None, evidence, True, False, True, "SHAREALIKE_REVIEW_REQUIRED")
    for marker, (name, url) in ALLOWED.items():
        if marker in normalized or name.casefold() in normalized:
            return LicenseDecision(name, url, evidence, True, True, name != "CC0 1.0", "AUTO_APPROVED")
    if "creative commons attribution license" in normalized or "(cc by)" in normalized:
        return LicenseDecision(
            "CC BY (version unspecified in JATS)", None, evidence, True, True, True,
            "AUTO_APPROVED_ARTICLE_LEVEL_CC_BY_VERSION_UNSPECIFIED",
        )
    return LicenseDecision("UNKNOWN", None, evidence, False, False, False, "LICENSE_UNVERIFIED")


def decision_dict(path: Path) -> dict[str, object]:
    return asdict(verify_jats_license(path))


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("paths", type=Path, nargs="+")
    args = parser.parse_args()
    rejected = 0
    for path in args.paths:
        decision = decision_dict(path)
        rejected += int(not decision["rag_ingestion"])
        print(json.dumps({"path": str(path), **decision}, ensure_ascii=False))
    return int(rejected > 0)


if __name__ == "__main__":
    raise SystemExit(main())
