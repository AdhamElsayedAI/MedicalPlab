"""Canonical organization identity and fail-closed source verification for PLAB V9."""

from __future__ import annotations

import re
from typing import Dict, List, Mapping, Optional, Set

from medicalplab.plab.v9.models import OrganizationIdentity, OrganizationRole


CANONICAL_ORGANIZATIONS: Dict[str, OrganizationIdentity] = {
    "ORG-NICE": OrganizationIdentity(
        organization_id="ORG-NICE",
        canonical_name="National Institute for Health and Care Excellence",
        aliases=[
            "NICE",
            "National Institute for Health and Care Excellence",
            "National Institute for Health and Clinical Excellence",
        ],
        roles=[
            OrganizationRole.ISSUING_ORGANIZATION.value,
            OrganizationRole.AUTHORITATIVE_HOST.value,
        ],
        approved_hosts=["www.nice.org.uk", "nice.org.uk"],
    ),
    "ORG-RCUK": OrganizationIdentity(
        organization_id="ORG-RCUK",
        canonical_name="Resuscitation Council UK",
        aliases=[
            "RCUK",
            "Resuscitation Council UK",
            "Resuscitation Council (UK)",
        ],
        roles=[
            OrganizationRole.ISSUING_ORGANIZATION.value,
            OrganizationRole.AUTHORITATIVE_HOST.value,
        ],
        approved_hosts=["www.resus.org.uk", "resus.org.uk"],
    ),
    "ORG-BTS": OrganizationIdentity(
        organization_id="ORG-BTS",
        canonical_name="British Thoracic Society",
        aliases=[
            "BTS",
            "British Thoracic Society",
        ],
        roles=[
            OrganizationRole.ISSUING_ORGANIZATION.value,
            OrganizationRole.AUTHORITATIVE_HOST.value,
        ],
        approved_hosts=["www.brit-thoracic.org.uk", "brit-thoracic.org.uk"],
    ),
    "ORG-ICS": OrganizationIdentity(
        organization_id="ORG-ICS",
        canonical_name="Intensive Care Society",
        aliases=[
            "ICS",
            "Intensive Care Society",
            "The Intensive Care Society",
        ],
        roles=[
            OrganizationRole.ISSUING_ORGANIZATION.value,
            OrganizationRole.AUTHORITATIVE_HOST.value,
        ],
        approved_hosts=["ics.ac.uk", "www.ics.ac.uk"],
    ),
    "ORG-FICM": OrganizationIdentity(
        organization_id="ORG-FICM",
        canonical_name="Faculty of Intensive Care Medicine",
        aliases=[
            "FICM",
            "Faculty of Intensive Care Medicine",
        ],
        roles=[
            OrganizationRole.SUPPORTING_ORGANIZATION.value,
        ],
        approved_hosts=["ficm.ac.uk", "www.ficm.ac.uk"],
    ),
    "ORG-BMJ-THORAX": OrganizationIdentity(
        organization_id="ORG-BMJ-THORAX",
        canonical_name="BMJ Publishing Group / Thorax",
        aliases=[
            "BMJ",
            "Thorax",
            "BMJ Thorax",
            "BMJ Publishing Group",
            "BMJ Publishing Group / Thorax",
            "British Thoracic Society / BMJ Thorax",
        ],
        roles=[
            OrganizationRole.JOURNAL_PUBLISHER.value,
        ],
        approved_hosts=["thorax.bmj.com", "www.bmj.com"],
    ),
    "ORG-SIGN": OrganizationIdentity(
        organization_id="ORG-SIGN",
        canonical_name="Scottish Intercollegiate Guidelines Network",
        aliases=[
            "SIGN",
            "Scottish Intercollegiate Guidelines Network",
        ],
        roles=[
            OrganizationRole.ISSUING_ORGANIZATION.value,
            OrganizationRole.AUTHORITATIVE_HOST.value,
        ],
        approved_hosts=["www.sign.ac.uk", "sign.ac.uk"],
    ),
}

# Approved authoritative clinical hosts
APPROVED_OFFICIAL_HOSTS: Set[str] = {
    host
    for org in CANONICAL_ORGANIZATIONS.values()
    if OrganizationRole.AUTHORITATIVE_HOST.value in org.roles
    for host in org.approved_hosts
}


def extract_host(url: str) -> str:
    """Extract lowercase hostname from a URL."""
    match = re.match(r"^https?://([^/:]+)", url.strip())
    return match.group(1).lower() if match else ""


def resolve_canonical_organization(name_or_alias: str) -> Optional[OrganizationIdentity]:
    """Resolve an organization name or alias to its canonical OrganizationIdentity."""
    cleaned = name_or_alias.strip().lower()
    if not cleaned:
        return None

    # Check by direct ID
    upper_id = name_or_alias.strip().upper()
    if upper_id in CANONICAL_ORGANIZATIONS:
        return CANONICAL_ORGANIZATIONS[upper_id]

    # Check by canonical name or alias
    for org in CANONICAL_ORGANIZATIONS.values():
        if org.canonical_name.lower() == cleaned:
            return org
        for alias in org.aliases:
            if alias.lower() == cleaned:
                return org

    return None


def verify_source_identity(
    source_packet: Mapping[str, Any],
) -> List[str]:
    """Verify source identity against the canonical organization registry with fail-closed checks."""
    errors: List[str] = []
    sid = str(source_packet.get("source_id", "<missing>"))

    issuing_org_id = str(source_packet.get("issuing_organization_id", "")).strip()
    if not issuing_org_id:
        errors.append(f"{sid}: missing issuing_organization_id")
        return errors

    if issuing_org_id not in CANONICAL_ORGANIZATIONS:
        errors.append(f"{sid}: unknown canonical organization ID '{issuing_org_id}'")
        return errors

    canonical_org = CANONICAL_ORGANIZATIONS[issuing_org_id]

    # Check issuing role
    if OrganizationRole.ISSUING_ORGANIZATION.value not in canonical_org.roles:
        errors.append(
            f"{sid}: organization '{issuing_org_id}' does not possess ISSUING_ORGANIZATION role (has roles: {canonical_org.roles})"
        )

    # Check declared canonical organization name
    declared_org = str(source_packet.get("canonical_organization", "")).strip()
    if not declared_org:
        errors.append(f"{sid}: missing canonical_organization declaration")
    else:
        resolved_decl = resolve_canonical_organization(declared_org)
        if resolved_decl is None or resolved_decl.organization_id != issuing_org_id:
            errors.append(
                f"{sid}: declared organization '{declared_org}' does not match issuing organization ID '{issuing_org_id}'"
            )

    # Check canonical URL and official host
    canonical_url = str(source_packet.get("canonical_url", "")).strip()
    if not canonical_url:
        errors.append(f"{sid}: missing canonical_url")
    else:
        host = extract_host(canonical_url)
        if not host:
            errors.append(f"{sid}: malformed canonical_url '{canonical_url}'")
        elif host not in canonical_org.approved_hosts:
            errors.append(
                f"{sid}: canonical URL host '{host}' is not an approved official host for {issuing_org_id} ({canonical_org.approved_hosts})"
            )

    # Verify identity evidence
    id_evidence = source_packet.get("identity_evidence", {})
    if not id_evidence:
        errors.append(f"{sid}: missing identity_evidence metadata")
    else:
        # Check publisher / branding in identity evidence
        ev_publisher = str(id_evidence.get("publisher", id_evidence.get("issuing_organization", ""))).strip()
        if ev_publisher:
            resolved_ev = resolve_canonical_organization(ev_publisher)
            if resolved_ev is None:
                errors.append(f"{sid}: identity evidence mentions unrecognized publisher '{ev_publisher}'")
            elif resolved_ev.organization_id != issuing_org_id:
                # Distinguish journal publisher or supporting organization if explicitly tracked
                supporting_org = id_evidence.get("supporting_organization")
                journal_pub = id_evidence.get("journal_publisher")
                if supporting_org and resolve_canonical_organization(supporting_org) == resolved_ev:
                    pass
                elif journal_pub and resolve_canonical_organization(journal_pub) == resolved_ev:
                    pass
                else:
                    errors.append(
                        f"{sid}: identity evidence publisher '{ev_publisher}' conflicts with issuing organization '{issuing_org_id}'"
                    )

    return errors
