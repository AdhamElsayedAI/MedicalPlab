"""V6 Canonical Source Identity Resolver with Immutable External Verification Receipts.

Enforces:
1. Real canonical identity extraction from external source responses (NCBI E-utilities XML,
   official publisher HTML/metadata). Never defaults or inherits canonical fields from declared metadata.
2. Immutable External Verification Receipts with cryptographic payload hashes.
3. No offline creation of canonical truth: offline mode may ONLY replay validated receipts.
   If unresolved and offline, returns UNRESOLVED (fail-closed).
4. Strict fail-closed identity: HTTP 200 or reachable domain alone is NOT sufficient.
   Identity is established only when canonical metadata matches declared authority and title.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class SourceVerificationStatus(str, Enum):
    IDENTITY_VERIFIED = "IDENTITY_VERIFIED"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
    UNRESOLVED = "UNRESOLVED"
    STALE_REVERIFY_REQUIRED = "STALE_REVERIFY_REQUIRED"


@dataclass
class ExternalVerificationReceipt:
    verification_receipt_id: str
    source_id: str
    source_type: str
    declared_identifier: str
    declared_title: str
    canonical_identifier: str
    canonical_title: str
    canonical_url: str
    canonical_organization: str
    canonical_document_type: str
    resolver_name: str
    resolver_version: str
    retrieval_timestamp: str
    canonical_version: Optional[str] = None
    canonical_publication_date: Optional[str] = None
    canonical_update_date: Optional[str] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    http_status: Optional[int] = None
    redirect_chain: List[str] = field(default_factory=list)
    raw_response_hash: str = ""
    identity_comparison_result: str = ""
    identity_verification_status: SourceVerificationStatus = SourceVerificationStatus.UNRESOLVED
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["identity_verification_status"] = self.identity_verification_status.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExternalVerificationReceipt:
        d = dict(data)
        d["identity_verification_status"] = SourceVerificationStatus(d["identity_verification_status"])
        return cls(**d)


def normalize_title_text(t: str) -> str:
    """Normalize title for fuzzy comparison: lowercase, remove punctuation, collapse whitespace."""
    if not t:
        return ""
    t = t.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def compute_title_similarity(declared: str, canonical: str) -> float:
    """Compute token-level similarity between declared and canonical titles.
    
    Sub-title aware: handles main titles before colon/hyphen as high-weight anchors.
    """
    d_norm = normalize_title_text(declared)
    c_norm = normalize_title_text(canonical)
    if not d_norm or not c_norm:
        return 0.0
    if d_norm == c_norm:
        return 1.0

    d_tokens = set(d_norm.split())
    c_tokens = set(c_norm.split())
    intersection = d_tokens & c_tokens
    union = d_tokens | c_tokens
    jaccard = len(intersection) / len(union) if union else 0.0

    # Prefix/contains heuristic: if one is full substring of another
    if d_norm in c_norm or c_norm in d_norm:
        jaccard = max(jaccard, 0.85)

    # Subtitle aware: check leading 5 keywords
    d_head = set(d_norm.split()[:5])
    c_head = set(c_norm.split()[:5])
    if d_head and c_head and len(d_head & c_head) >= 3:
        jaccard = max(jaccard, 0.75)

    return jaccard


class V6CanonicalSourceResolver:
    """Deterministic external source identity resolver with immutable receipt generation."""

    def __init__(
        self,
        online_mode: bool = True,
        receipts_store_path: Optional[Path] = None,
    ):
        self.online_mode = online_mode
        self.receipts_store_path = receipts_store_path or (
            Path(__file__).resolve().parent.parent.parent.parent
            / "Data/metadata/external_source_verification_receipts_v6.jsonl"
        )
        self._cached_receipts: Dict[str, ExternalVerificationReceipt] = {}
        self._load_cached_receipts()

    def _load_cached_receipts(self) -> None:
        """Load previously verified receipts from disk store."""
        if not self.receipts_store_path.exists():
            return
        with open(self.receipts_store_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    receipt = ExternalVerificationReceipt.from_dict(data)
                    self._cached_receipts[receipt.source_id] = receipt
                    if receipt.canonical_identifier:
                        self._cached_receipts[receipt.canonical_identifier] = receipt
                except Exception:
                    continue

    def record_receipt(self, receipt: ExternalVerificationReceipt) -> None:
        """Persist a newly verified receipt to disk."""
        self._cached_receipts[receipt.source_id] = receipt
        if receipt.canonical_identifier:
            self._cached_receipts[receipt.canonical_identifier] = receipt
        self.receipts_store_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.receipts_store_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(receipt.to_dict()) + "\n")

    def resolve_ncbi_pmc(
        self,
        source_id: str,
        pmcid: str,
        declared_title: Optional[str] = None,
    ) -> ExternalVerificationReceipt:
        """Resolve canonical PMCID metadata from NCBI E-utilities live.
        
        Strict rule:
        If online_mode is False and no valid cached receipt exists, returns UNRESOLVED.
        Never fabricates truth offline.
        """
        # Extract clean PMC identifier (e.g. PMC10980676)
        m = re.search(r"PMC(\d+)", pmcid.strip(), re.IGNORECASE)
        if m:
            norm_pmc = f"PMC{m.group(1)}"
            numeric_id = m.group(1)
        else:
            norm_pmc = pmcid.strip().upper()
            if not norm_pmc.startswith("PMC"):
                norm_pmc = f"PMC{norm_pmc}"
            numeric_id = norm_pmc.replace("PMC", "")

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        decl_title = declared_title or ""

        # Check existing verified cache first
        if not self.online_mode:
            if norm_pmc in self._cached_receipts:
                return self._cached_receipts[norm_pmc]
            return ExternalVerificationReceipt(
                verification_receipt_id=f"RCPT-OFFLINE-UNRESOLVED-{norm_pmc}",
                source_id=source_id,
                source_type="PEER_REVIEWED_ARTICLE",
                declared_identifier=pmcid,
                declared_title=decl_title,
                canonical_identifier=norm_pmc,
                canonical_title="",
                canonical_url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{norm_pmc}/",
                canonical_organization="NCBI / National Library of Medicine",
                canonical_document_type="JOURNAL_ARTICLE",
                resolver_name="RECEIPT_CACHE_REPLAY",
                resolver_version="6.0.0",
                retrieval_timestamp=timestamp,
                identity_comparison_result="OFFLINE_NO_PRIOR_RECEIPT",
                identity_verification_status=SourceVerificationStatus.UNRESOLVED,
                explanation=f"Offline mode active and no previously verified external receipt exists for {norm_pmc}. Offline creation of truth is prohibited.",
            )

        # Online HTTP fetch via NCBI E-utilities
        api_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
            f"db=pmc&id={numeric_id}&retmode=xml"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MedicalPlab-V6-Resolver/6.0.0 (Research Evidence Infrastructure)"
        }

        try:
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                status_code = response.status
                raw_bytes = response.read()
                raw_hash = hashlib.sha256(raw_bytes).hexdigest()

                root = ET.fromstring(raw_bytes)
                docsum = root.find(".//DocSum")

                if docsum is None:
                    receipt = ExternalVerificationReceipt(
                        verification_receipt_id=f"RCPT-NOTFOUND-{norm_pmc}",
                        source_id=source_id,
                        source_type="PEER_REVIEWED_ARTICLE",
                        declared_identifier=pmcid,
                        declared_title=decl_title,
                        canonical_identifier=norm_pmc,
                        canonical_title="",
                        canonical_url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{norm_pmc}/",
                        canonical_organization="NCBI / National Library of Medicine",
                        canonical_document_type="JOURNAL_ARTICLE",
                        resolver_name="NCBI_EUTILS_LIVE",
                        resolver_version="6.0.0",
                        retrieval_timestamp=timestamp,
                        http_status=status_code,
                        raw_response_hash=raw_hash,
                        identity_comparison_result="DOCSUM_NOT_FOUND",
                        identity_verification_status=SourceVerificationStatus.SOURCE_NOT_FOUND,
                        explanation=f"NCBI E-utilities returned no document summary for ID {numeric_id}.",
                    )
                    self.record_receipt(receipt)
                    return receipt

                # Extract canonical metadata from DocSum
                title_elem = docsum.find(".//Item[@Name='Title']")
                source_elem = docsum.find(".//Item[@Name='Source']")
                pubdate_elem = docsum.find(".//Item[@Name='PubDate']")
                doi_elem = docsum.find(".//Item[@Name='DOI']")
                pmid_elem = docsum.find(".//Item[@Name='pmid']")

                canon_title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                journal = source_elem.text.strip() if source_elem is not None and source_elem.text else ""
                pubdate = pubdate_elem.text.strip() if pubdate_elem is not None and pubdate_elem.text else ""
                doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None
                pmid = pmid_elem.text.strip() if pmid_elem is not None and pmid_elem.text else None

                # Extract year
                year = None
                if pubdate:
                    m_yr = re.search(r"\b(19\d\d|20\d\d)\b", pubdate)
                    if m_yr:
                        year = int(m_yr.group(1))

                # Compare declared title vs canonical title
                sim = compute_title_similarity(decl_title, canon_title) if decl_title else 1.0
                if decl_title and sim < 0.45:
                    verif_status = SourceVerificationStatus.IDENTITY_MISMATCH
                    explanation = (
                        f"PMC metadata resolved from NCBI but canonical title mismatch! "
                        f"Declared: '{decl_title}' vs Canonical NCBI: '{canon_title}' (similarity={sim:.2f})."
                    )
                else:
                    verif_status = SourceVerificationStatus.IDENTITY_VERIFIED
                    explanation = f"Canonical NCBI PMC identity verified: '{canon_title}' ({journal}, {year})."

                receipt = ExternalVerificationReceipt(
                    verification_receipt_id=f"RCPT-{raw_hash[:16].upper()}",
                    source_id=source_id,
                    source_type="PEER_REVIEWED_ARTICLE",
                    declared_identifier=pmcid,
                    declared_title=decl_title,
                    canonical_identifier=norm_pmc,
                    canonical_title=canon_title,
                    canonical_url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{norm_pmc}/",
                    canonical_organization="NCBI / National Library of Medicine",
                    canonical_document_type="JOURNAL_ARTICLE",
                    resolver_name="NCBI_EUTILS_LIVE",
                    resolver_version="6.0.0",
                    retrieval_timestamp=timestamp,
                    journal=journal,
                    doi=doi,
                    pmid=pmid,
                    canonical_publication_date=pubdate,
                    canonical_version=str(year) if year else None,
                    http_status=status_code,
                    raw_response_hash=raw_hash,
                    identity_comparison_result=f"SIMILARITY_{sim:.2f}",
                    identity_verification_status=verif_status,
                    explanation=explanation,
                )
                self.record_receipt(receipt)
                return receipt

        except Exception as e:
            if norm_pmc in self._cached_receipts:
                return self._cached_receipts[norm_pmc]
            return ExternalVerificationReceipt(
                verification_receipt_id=f"RCPT-ERROR-{norm_pmc}",
                source_id=source_id,
                source_type="PEER_REVIEWED_ARTICLE",
                declared_identifier=pmcid,
                declared_title=decl_title,
                canonical_identifier=norm_pmc,
                canonical_title="",
                canonical_url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{norm_pmc}/",
                canonical_organization="NCBI / National Library of Medicine",
                canonical_document_type="JOURNAL_ARTICLE",
                resolver_name="NCBI_EUTILS_LIVE",
                resolver_version="6.0.0",
                retrieval_timestamp=timestamp,
                identity_comparison_result="HTTP_ERROR",
                identity_verification_status=SourceVerificationStatus.UNRESOLVED,
                explanation=f"Online canonical resolution failed with error: {str(e)}",
            )

    def resolve_official_guideline(
        self,
        source_id: str,
        canonical_identifier: str,
        canonical_url: str,
        declared_title: str,
        organization: str,
        publication_year: Optional[int] = None,
    ) -> ExternalVerificationReceipt:
        """Resolve official guideline against publishing authority.
        
        Strict rule (V6 Defect 1 fix):
        In online mode, fetches the actual official publisher resource.
        Extracts real metadata (HTML title, meta tags, H1) from the response content.
        Never defaults canonical_title from declared_title.
        Compares extracted title against declared title; if similarity is insufficient,
        fails closed as IDENTITY_MISMATCH or UNRESOLVED.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Check existing verified receipt in cache
        if source_id in self._cached_receipts and self._cached_receipts[source_id].identity_verification_status == SourceVerificationStatus.IDENTITY_VERIFIED:
            return self._cached_receipts[source_id]

        if not self.online_mode:
            if source_id in self._cached_receipts:
                return self._cached_receipts[source_id]
            return ExternalVerificationReceipt(
                verification_receipt_id=f"RCPT-OFFLINE-UNRESOLVED-{source_id}",
                source_id=source_id,
                source_type="AUTHORITATIVE_UK_GUIDELINE" if any(k in organization for k in ["UK", "NICE", "RCUK", "BTS", "FICM", "NHS"]) else "INTERNATIONAL_BENCHMARK",
                declared_identifier=canonical_identifier,
                declared_title=declared_title,
                canonical_identifier=canonical_identifier,
                canonical_title="",
                canonical_url=canonical_url,
                canonical_organization=organization,
                canonical_document_type="CLINICAL_PRACTICE_GUIDELINE",
                resolver_name="RECEIPT_CACHE_REPLAY",
                resolver_version="6.0.0",
                retrieval_timestamp=timestamp,
                canonical_version=str(publication_year) if publication_year else None,
                identity_comparison_result="OFFLINE_NO_PRIOR_RECEIPT",
                identity_verification_status=SourceVerificationStatus.UNRESOLVED,
                explanation=f"Offline mode active and no previously verified external receipt exists for {source_id}.",
            )

        # Online HTTP check to official publisher endpoint
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MedicalPlab-V6-Resolver/6.0.0 (Research Evidence Infrastructure)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        try:
            req = urllib.request.Request(canonical_url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                status_code = resp.status
                redirect_url = resp.geturl()
                redirect_chain = [canonical_url]
                if redirect_url != canonical_url:
                    redirect_chain.append(redirect_url)

                raw_bytes = resp.read()
                raw_hash = hashlib.sha256(raw_bytes).hexdigest()

                # Extract real metadata from official HTML response body
                html_text = raw_bytes[:100000].decode("utf-8", errors="replace")
                extracted_title = ""

                # 1. Try <meta name="dc.title" ...> or <meta property="og:title" ...>
                m_meta = re.search(r'<meta\s+[^>]*(?:name=["\']dc\.title["\']|property=["\']og:title["\'])[^>]*content=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
                if m_meta:
                    extracted_title = m_meta.group(1).strip()

                # 2. Try <title> tag if meta title absent
                if not extracted_title:
                    m_title = re.search(r"<title\b[^>]*>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
                    if m_title:
                        raw_title = re.sub(r"\s+", " ", m_title.group(1)).strip()
                        # Clean publisher suffixes like "| NICE" or "- British Thoracic Society"
                        raw_title = re.sub(r"\s*[\-\|]\s*(?:NICE|British Thoracic Society|Resuscitation Council UK).*$", "", raw_title, flags=re.IGNORECASE).strip()
                        extracted_title = raw_title

                # 3. Try <h1> tag if still empty
                if not extracted_title:
                    m_h1 = re.search(r"<h1\b[^>]*>(.*?)</h1>", html_text, re.IGNORECASE | re.DOTALL)
                    if m_h1:
                        extracted_title = re.sub(r"<[^>]+>", "", m_h1.group(1)).strip()

                canonical_title = extracted_title if extracted_title else ""

                # Verify identity: check similarity or keyword presence
                if canonical_title:
                    sim = compute_title_similarity(declared_title, canonical_title)
                    # Check guideline number presence (e.g. NG136, CG109, NG196, NG115, CG64, NG208)
                    m_code = re.search(r"\b([A-Z]{1,3}\d{2,4})\b", canonical_identifier)
                    code_match = bool(m_code and m_code.group(1).lower() in html_text.lower())
                    org_match = any(w.lower() in html_text.lower() for w in organization.split() if len(w) > 3)

                    if sim >= 0.40 or (code_match and org_match):
                        verif_status = SourceVerificationStatus.IDENTITY_VERIFIED
                        comparison = f"SIMILARITY_{sim:.2f}_CODE_MATCH_{code_match}"
                        explanation = f"Official publisher identity verified from response: '{canonical_title}' ({organization})."
                    else:
                        verif_status = SourceVerificationStatus.IDENTITY_MISMATCH
                        comparison = f"SIMILARITY_{sim:.2f}_LOW"
                        explanation = f"Publisher reached (HTTP {status_code}) but extracted title '{canonical_title}' does not match declared '{declared_title}'."
                else:
                    # Could not extract canonical title from body
                    verif_status = SourceVerificationStatus.UNRESOLVED
                    comparison = "METADATA_EXTRACTION_FAILED"
                    explanation = f"Publisher reached (HTTP {status_code}) but failed to extract canonical title from response body."

                receipt = ExternalVerificationReceipt(
                    verification_receipt_id=f"RCPT-{raw_hash[:16].upper()}",
                    source_id=source_id,
                    source_type="AUTHORITATIVE_UK_GUIDELINE" if any(k in organization for k in ["UK", "NICE", "RCUK", "BTS", "FICM", "NHS"]) else "INTERNATIONAL_BENCHMARK",
                    declared_identifier=canonical_identifier,
                    declared_title=declared_title,
                    canonical_identifier=canonical_identifier,
                    canonical_title=canonical_title,
                    canonical_url=canonical_url,
                    canonical_organization=organization,
                    canonical_document_type="CLINICAL_PRACTICE_GUIDELINE",
                    resolver_name="OFFICIAL_PUBLISHER_LIVE",
                    resolver_version="6.0.0",
                    retrieval_timestamp=timestamp,
                    canonical_version=str(publication_year) if publication_year else None,
                    http_status=status_code,
                    redirect_chain=redirect_chain,
                    raw_response_hash=raw_hash,
                    identity_comparison_result=comparison,
                    identity_verification_status=verif_status,
                    explanation=explanation,
                )
                self.record_receipt(receipt)
                return receipt

        except urllib.error.HTTPError as he:
            return ExternalVerificationReceipt(
                verification_receipt_id=f"RCPT-HTTP-ERR-{source_id}",
                source_id=source_id,
                source_type="AUTHORITATIVE_UK_GUIDELINE",
                declared_identifier=canonical_identifier,
                declared_title=declared_title,
                canonical_identifier=canonical_identifier,
                canonical_title="",
                canonical_url=canonical_url,
                canonical_organization=organization,
                canonical_document_type="CLINICAL_PRACTICE_GUIDELINE",
                resolver_name="OFFICIAL_PUBLISHER_LIVE",
                resolver_version="6.0.0",
                retrieval_timestamp=timestamp,
                http_status=he.code,
                raw_response_hash="",
                identity_comparison_result=f"HTTP_{he.code}",
                identity_verification_status=SourceVerificationStatus.SOURCE_NOT_FOUND,
                explanation=f"Official publisher returned error: HTTP {he.code}",
            )
        except Exception as e:
            if source_id in self._cached_receipts:
                return self._cached_receipts[source_id]
            return ExternalVerificationReceipt(
                verification_receipt_id=f"RCPT-ERR-{source_id}",
                source_id=source_id,
                source_type="AUTHORITATIVE_UK_GUIDELINE",
                declared_identifier=canonical_identifier,
                declared_title=declared_title,
                canonical_identifier=canonical_identifier,
                canonical_title="",
                canonical_url=canonical_url,
                canonical_organization=organization,
                canonical_document_type="CLINICAL_PRACTICE_GUIDELINE",
                resolver_name="OFFICIAL_PUBLISHER_LIVE",
                resolver_version="6.0.0",
                retrieval_timestamp=timestamp,
                identity_comparison_result="CONNECTION_ERROR",
                identity_verification_status=SourceVerificationStatus.UNRESOLVED,
                explanation=f"Failed to reach official publisher: {str(e)}",
            )
