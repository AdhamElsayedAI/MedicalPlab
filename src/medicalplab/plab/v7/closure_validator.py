"""Fail-closed validators for the final PLAB automated closure checkpoint.

V7 deliberately validates the low-level closure records rather than reusing V6's
stored summary booleans.  In particular, it rejects unsupported non-key claims,
uncovered explanation text, unbound option rationales, arbitrary in-memory source
text, and trust states above clinician review.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Iterable, List, Mapping


ALLOWED_DISPOSITIONS = {
    "PRESERVE_AFTER_REVALIDATION",
    "REPAIR",
    "REWRITE",
    "REPLACE",
    "QUARANTINE",
    "DEFER",
    "REJECT",
}

ALLOWED_BLOCKER_CLASSES = {
    "A_ENGINEERING_FIXABLE",
    "B_EVIDENCE_FIXABLE",
    "C_CONTENT_REPAIRABLE",
    "D_CONTENT_REWRITE_REQUIRED",
    "E_AUTHORITATIVE_SOURCE_CONFLICT",
    "F_HUMAN_CLINICAL_JUDGMENT_REQUIRED",
    "G_LICENSING_BLOCKER",
    "H_NO_AUTHORITATIVE_EVIDENCE",
    "I_UNSAFE_OR_INVALID_QUESTION",
}

FINAL_NON_ENGINEERING_BLOCKERS = {
    "E_AUTHORITATIVE_SOURCE_CONFLICT",
    "F_HUMAN_CLINICAL_JUDGMENT_REQUIRED",
    "G_LICENSING_BLOCKER",
    "H_NO_AUTHORITATIVE_EVIDENCE",
    "I_UNSAFE_OR_INVALID_QUESTION",
}

TRUST_STATES = {"CLINICIAN_REVIEW_REQUIRED", "QUARANTINED", "DEFERRED", "REJECTED"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
OFFICIAL_HOSTS = {
    "www.nice.org.uk",
    "www.resus.org.uk",
    "www.brit-thoracic.org.uk",
    "ics.ac.uk",
}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require(condition: bool, message: str, errors: List[str]) -> None:
    if not condition:
        errors.append(message)


def _host(url: str) -> str:
    match = re.match(r"^https://([^/]+)/", url)
    return match.group(1).lower() if match else ""


def validate_source_packet(packet: Mapping[str, Any]) -> List[str]:
    """Validate provenance, representation integrity, and exact evidence spans."""
    errors: List[str] = []
    sid = str(packet.get("source_id", "<missing>"))
    representation = str(packet.get("representation_text", ""))

    _require(packet.get("identity_status") == "IDENTITY_VERIFIED", f"{sid}: identity is not verified", errors)
    _require(packet.get("edition_verification_status") == "EDITION_VERIFIED", f"{sid}: wrong or unverified edition", errors)
    _require(packet.get("currentness_status") == "CURRENT_VERIFIED", f"{sid}: currentness is not verified", errors)
    _require(packet.get("http_status") == 200, f"{sid}: official retrieval did not return HTTP 200", errors)
    _require(_host(str(packet.get("canonical_url", ""))) in OFFICIAL_HOSTS, f"{sid}: source is not on an approved official host", errors)
    _require(packet.get("representation_origin") == "EXTERNALLY_RETRIEVED_PRIMARY_SOURCE_EXCERPT", f"{sid}: arbitrary or synthetic representation origin", errors)
    _require(packet.get("retrieval_method") == "LIVE_PRIMARY_SOURCE_HTTP_AND_TEXT_EXTRACTION", f"{sid}: unverified retrieval method", errors)
    _require(bool(representation.strip()), f"{sid}: empty representation", errors)
    _require(HEX64.match(str(packet.get("raw_response_sha256", ""))) is not None, f"{sid}: invalid raw response SHA256", errors)
    _require(packet.get("representation_sha256") == sha256_text(representation), f"{sid}: representation hash mismatch", errors)

    span_ids = set()
    for span in packet.get("evidence_spans", []):
        span_id = str(span.get("span_id", ""))
        exact_text = str(span.get("exact_text", ""))
        _require(bool(span_id) and span_id not in span_ids, f"{sid}: missing or duplicate evidence span id", errors)
        span_ids.add(span_id)
        _require(bool(exact_text.strip()), f"{sid}/{span_id}: empty evidence span", errors)
        _require(exact_text in representation, f"{sid}/{span_id}: quote not present in verified representation", errors)
        _require(span.get("exact_text_sha256") == sha256_text(exact_text), f"{sid}/{span_id}: evidence span hash mismatch", errors)
    _require(bool(span_ids), f"{sid}: no evidence spans", errors)
    return errors


def _validate_bound_option_reviews(question: Mapping[str, Any], errors: List[str]) -> None:
    qid = str(question.get("question_id", "<missing>"))
    version = str(question.get("question_version", ""))
    stem = str(question.get("stem", ""))
    stem_hash = sha256_text(stem)
    choices = question.get("choices", [])
    expected = {str(choice.get("id")): str(choice.get("text", "")) for choice in choices}
    reviews = question.get("option_reviews", [])
    review_ids = [str(review.get("option_id", "")) for review in reviews]

    _require(set(review_ids) == set(expected), f"{qid}: option reviews are incomplete or reference unknown options", errors)
    _require(len(review_ids) == len(set(review_ids)), f"{qid}: duplicate option review", errors)
    defensible = []
    rationale_hashes = set()
    for review in reviews:
        option_id = str(review.get("option_id", ""))
        option_text = expected.get(option_id, "")
        rationale = str(review.get("rationale", ""))
        _require(review.get("question_id") == qid, f"{qid}/{option_id}: cross-question rationale binding", errors)
        _require(review.get("question_version") == version, f"{qid}/{option_id}: stale question-version rationale", errors)
        _require(review.get("stem_sha256") == stem_hash, f"{qid}/{option_id}: stem hash mismatch", errors)
        _require(review.get("option_text") == option_text, f"{qid}/{option_id}: option text mismatch", errors)
        _require(review.get("option_text_sha256") == sha256_text(option_text), f"{qid}/{option_id}: option hash mismatch", errors)
        _require(len(rationale.split()) >= 6, f"{qid}/{option_id}: boilerplate or missing rationale", errors)
        rationale_hash = sha256_text(rationale)
        _require(rationale_hash not in rationale_hashes, f"{qid}/{option_id}: duplicate rationale", errors)
        rationale_hashes.add(rationale_hash)
        if review.get("is_defensible") is True:
            defensible.append(option_id)
    _require(defensible == [question.get("correct_answer")], f"{qid}: one-best-answer adjudication failed ({defensible})", errors)


def validate_question_record(question: Mapping[str, Any], source_packets: Mapping[str, Mapping[str, Any]]) -> List[str]:
    """Recompute a question's eligibility from its low-level evidence and coverage records."""
    errors: List[str] = []
    qid = str(question.get("question_id", "<missing>"))
    grounded = question.get("source_grounded") is True
    disposition = str(question.get("disposition", ""))
    trust_state = str(question.get("trust_state", ""))

    _require(disposition in ALLOWED_DISPOSITIONS, f"{qid}: invalid disposition {disposition}", errors)
    _require(trust_state in TRUST_STATES, f"{qid}: unauthorized trust state {trust_state}", errors)
    _require(question.get("clinician_approved") is not True, f"{qid}: fabricated clinician approval", errors)
    _require(question.get("golden") is not True, f"{qid}: automatic Golden promotion", errors)
    _require(question.get("golden_eligible") is not True, f"{qid}: automatic Golden eligibility", errors)

    if not grounded:
        _require(trust_state in {"QUARANTINED", "DEFERRED", "REJECTED"}, f"{qid}: non-grounded item has review-ready trust", errors)
        blocker_class = str(question.get("blocker_class", ""))
        _require(blocker_class in FINAL_NON_ENGINEERING_BLOCKERS, f"{qid}: unresolved engineering/content blocker {blocker_class}", errors)
        _require(bool(str(question.get("blocking_reason", "")).strip()), f"{qid}: missing substantive blocking reason", errors)
        _require(question.get("remaining_engineering_blocker") is False, f"{qid}: hidden engineering blocker", errors)
        return errors

    _require(trust_state == "CLINICIAN_REVIEW_REQUIRED", f"{qid}: grounded item is not bounded at clinician review", errors)
    _require(disposition not in {"QUARANTINE", "DEFER", "REJECT"}, f"{qid}: grounded item has blocked disposition", errors)
    _require(question.get("clinician_review_ready") is True, f"{qid}: grounded item is not review ready", errors)

    claims = question.get("atomic_claims", [])
    _require(bool(claims), f"{qid}: no atomic claims", errors)
    claim_ids = {str(claim.get("claim_id", "")) for claim in claims}
    _require("" not in claim_ids and len(claim_ids) == len(claims), f"{qid}: missing or duplicate claim id", errors)
    decisive = [claim for claim in claims if claim.get("is_decisive") is True]
    _require(bool(decisive), f"{qid}: no decisive claim", errors)

    packet_spans: Dict[str, Dict[str, str]] = {
        sid: {str(span.get("span_id")): str(span.get("exact_text", "")) for span in packet.get("evidence_spans", [])}
        for sid, packet in source_packets.items()
    }
    for claim in claims:
        cid = str(claim.get("claim_id", ""))
        sid = str(claim.get("source_id", ""))
        span_id = str(claim.get("evidence_span_id", ""))
        _require(sid in source_packets, f"{qid}/{cid}: unknown source identity", errors)
        evidence_text = packet_spans.get(sid, {}).get(span_id, "")
        _require(bool(evidence_text), f"{qid}/{cid}: unverified evidence span", errors)
        _require(claim.get("evidence_quote") == evidence_text, f"{qid}/{cid}: quote/source span mismatch", errors)
        binding = sha256_text(f"{qid}|{question.get('question_version')}|{claim.get('claim_text')}|{sid}|{span_id}|{evidence_text}")
        _require(claim.get("evidence_binding_sha256") == binding, f"{qid}/{cid}: wrong-source or stale evidence binding", errors)
        _require(claim.get("support_status") == "DIRECT_SUPPORT", f"{qid}/{cid}: unsupported clinical claim", errors)
        _require(claim.get("source_identity_pass") is True, f"{qid}/{cid}: source identity failed", errors)
        _require(claim.get("source_currentness_pass") is True, f"{qid}/{cid}: source currentness failed", errors)
        _require(claim.get("span_verification_pass") is True, f"{qid}/{cid}: span verification failed", errors)
        _require(claim.get("specificity_pass") is True, f"{qid}/{cid}: specificity failed", errors)
        dimensions = claim.get("specificity_dimensions", {})
        for dimension in ("dose", "unit", "operator", "timing", "population", "negation"):
            _require(dimensions.get(dimension) in {"MATCH", "NOT_APPLICABLE"}, f"{qid}/{cid}: {dimension} mismatch", errors)
        _require(claim.get("final_claim_pass") is True, f"{qid}/{cid}: final claim failed", errors)

    coverage = question.get("content_coverage", {})
    fragments = coverage.get("fragments", [])
    _require(bool(fragments), f"{qid}: no content fragments", errors)
    _require(coverage.get("uncovered_decisive_fragments") == 0, f"{qid}: uncovered decisive fragment", errors)
    for fragment in fragments:
        if fragment.get("classification") == "DECISIVE_CLINICAL_CONTENT":
            mapped = set(fragment.get("mapped_claim_ids", []))
            _require(bool(mapped) and mapped <= claim_ids, f"{qid}: decisive fragment lacks a valid claim mapping", errors)
            _require(fragment.get("coverage_status") == "COVERED", f"{qid}: decisive fragment is not covered", errors)

    components = question.get("answer_component_coverage", [])
    _require(bool(components), f"{qid}: keyed answer was not componentized", errors)
    for component in components:
        _require(component.get("status") == "COVERED", f"{qid}: uncovered keyed-answer component {component.get('component')}", errors)
        _require(str(component.get("claim_id", "")) in claim_ids, f"{qid}: answer component has invalid claim mapping", errors)

    _validate_bound_option_reviews(question, errors)
    return errors


def validate_checkpoint(checkpoint: Mapping[str, Any], source_report: Mapping[str, Any]) -> List[str]:
    """Validate and independently recompute final checkpoint summary counts."""
    errors: List[str] = []
    packets = {packet["source_id"]: packet for packet in source_report.get("sources", [])}
    for packet in packets.values():
        errors.extend(validate_source_packet(packet))

    questions = checkpoint.get("questions", [])
    _require(len(questions) == 36, "checkpoint: expected exactly 36 questions", errors)
    ids = [question.get("question_id") for question in questions]
    _require(len(ids) == len(set(ids)), "checkpoint: duplicate question ids", errors)
    for question in questions:
        errors.extend(validate_question_record(question, packets))

    recomputed = {
        "total_questions": len(questions),
        "source_grounded": sum(question.get("source_grounded") is True for question in questions),
        "clinician_review_required": sum(question.get("trust_state") == "CLINICIAN_REVIEW_REQUIRED" for question in questions),
        "quarantined": sum(question.get("trust_state") == "QUARANTINED" for question in questions),
        "deferred": sum(question.get("trust_state") == "DEFERRED" for question in questions),
        "rejected": sum(question.get("trust_state") == "REJECTED" for question in questions),
    }
    _require(checkpoint.get("summary") == recomputed, f"checkpoint: stored summary differs from recomputation {recomputed}", errors)
    return errors


def assert_no_errors(errors: Iterable[str]) -> None:
    collected = list(errors)
    if collected:
        raise ValueError("\n".join(collected))
